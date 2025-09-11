
from astropy import wcs
import astropy.units as u
import numpy as np

from astropy.time import Time

from sunpy.coordinates import frames
from sunpy.physics.differential_rotation import diff_rot
from astropy.coordinates import SkyCoord
from astropy.wcs import WCS



"""
Adapted from Grabiel Pelouze's code https://github.com/gpelouze/spice_jitter_correction.git

"""

def _get_spatial_wcs(header):
    """ Get subset WCS for the spatial coordinates of a SPICE HDU.

    Parameters
    ==========
    header : fits.Header
        SPICE L2 FITS header.

    Returns
    =======
    w : wcs.WCS
        Spatial WCSa.
    """
    w = wcs.WCS(header)
    w.wcs.pc[3, 0] = 0  # remove PC4_1 to decouple t from x
    return w.sub(2)  # drop wavelength and time axes


def _assert_hdus_have_the_same_spatial_coordinates(hdul):
    """ Assert that SPICE image HDUs have the same spatial coordinates

    Parameters
    ==========
    hdul : fits.HDUList
        HDU list with images extensions.

    Raises
    ======
    ValueError :
        When the spatial coordinates of the HDUs differ.

    """
    w_ref = _get_spatial_wcs(hdul[0].header)
    for hdu in hdul:
        if hdu.is_image and hdu.name != 'WCSDVARR':
            w = _get_spatial_wcs(hdu.header)
            if w.to_header() != w_ref.to_header():
                print(w_ref)
                print(w)
                raise ValueError('FITS extensions have different spatial '
                                 'coordinates')


def get_coordinates(header):
    """ Get SPICE coordinates (without distortion)
    
    Parameters
    ==========
    header : fits.Header
        Header of the FITS extension for which to compute the coordinates.

    Returns
    =======
    coordinates : np.ndarray
        Array of shape (2, ny, nx), containing the helioprojective coordinates
        `T_x` and `T_y` for each pixel of the field of view.
    """
    w = wcs.WCS(header)
    iy, ix = np.indices((header['NAXIS2'], header['NAXIS1']))
    iD = np.zeros_like(ix)  
    it = np.zeros_like(ix)  
    outputs = w.pixel_to_world(ix, iy, iD, it)
    Tx = outputs[0].Tx.arcsec
    Ty = outputs[0].Ty.arcsec
    
    pi = u.Quantity(np.pi, 'rad').to('arcsec').value
    Tx = (Tx + pi) % (2*pi) - pi
    Ty = (Ty + pi) % (2*pi) - pi
    return np.array([Tx, Ty])


def add_distortion_to_coordinates(coordinates, hdul):
    """ Add distortion to coordinates

    Parameters
    ==========
    coordinates : array_like
        Array of shape (2, ny, nx), containing the helioprojective coordinates
        `T_x` and `T_y` for each pixel of the field of view.
    hdul : fits.HDUList
        HDU list with two extensions images ``WCSDVARR`` (1 and 2) containing
        the pointing distortion correction for `T_x` and `T_y`.

    Returns
    =======
    coordinates : np.ndarray
        Array of shape (2, ny, nx), containing the corrected coordinates.
    """
    Tx, Ty = coordinates
    Tx_corr = hdul['WCSDVARR', 1].data
    Ty_corr = hdul['WCSDVARR', 2].data
    return np.array([Tx - Tx_corr, Ty - Ty_corr])


def spice_diff_rot_coord(coordinates, header,
                         tracking=False,
                         target_header=None):
    """
    Apply solar differential rotation to helioprojective coordinates (arcsec),
    from $SSW/so/spice/idl/quicklook/utils/spice_diff_rot_coord.pro

    Parameters
    ----------
    coordinates : np.ndarray
        Shape (2, ny, nx), array of [Tx, Ty] in arcsec
    header : fits.Header
        Header defining the WCS (HPC + time axis).
        Should contain DATE-OBS (and ideally DATE-AVG or DATEREF/EXPTIME).
    tracking : bool, optional
        If True, use the average time only (equivalent to IDL /TRACKING branch).
    target_header : fits.Header, optional
        If given, final coordinates are converted into this WCS/time (like TARGET_WCS).
        Otherwise stays in the same WCS as `header`.

    Returns
    -------
    np.ndarray
        Shape (2, ny, nx), corrected [Tx, Ty] in arcsec at the target time/WCS.
    """
    Tx, Ty = coordinates
    ny, nx = Tx.shape

    # Times (IDL: dateref vs observ_avg)
    # Reference date (DATEREF if present, else DATE-OBS)
    dateref = header.get('DATEREF', header.get('DATE-OBS'))
    if dateref is None:
        raise ValueError("Header must contain DATEREF or DATE-OBS")

    # Average/target time: DATE-AVG preferred, else DATE-OBS
    date_avg = header.get('DATE-AVG', header.get('DATE-OBS'))
    if date_avg is None:
        raise ValueError("Header must contain DATE-AVG or DATE-OBS")

    t_avg = Time(date_avg)

    w_in = WCS(header)
    iy, ix = np.indices((ny, nx))
    # dummy indices for the other axes (D and t index)
    iD = np.zeros_like(ix)
    it = np.zeros_like(ix)

    # Get time component
    pix_stack = np.stack([ix, iy, iD, it], axis=-1).reshape(-1, 4)
    world = w_in.wcs_pix2world(pix_stack, 0)  # shape (N, 4): [Tx, Ty, ?, time]
    t_ref = Time(dateref)
    # Interpret the 4th world component as seconds from DATEREF:
    seconds_from_ref = world[:, -1]
    times_flat = t_ref + seconds_from_ref * u.s
    times = times_flat.reshape(ny, nx)

    # IDL: tracking => tai = tai0 (single time), else use full per-pixel time array.
    if tracking:
        tai = np.full((ny, nx), t_avg)
    else:
        tai = times 


    # Time difference in days (IDL: dd)
    target_time = t_avg if target_header is None else Time(target_header.get('DATE-AVG',
                                        target_header.get('DATE-OBS', date_avg)))
    dd_days = (target_time - tai).to(u.day).value
    # If dd==0 everywhere, nothing to do
    if np.all(dd_days == 0):
        return np.array([Tx, Ty])

    # Convert HPC -> Heliographic Carrington (lon, lat in degrees) 
    # Build HPC SkyCoord for each pixel at *its own time* (tai) with proper observer.
    Tx_q = (Tx * u.arcsec).reshape(ny, nx)
    Ty_q = (Ty * u.arcsec).reshape(ny, nx)

    # Get Solar Orbiter location 
    observer = observer_from_header(header)

    Tx_flat = Tx_q.ravel()
    Ty_flat = Ty_q.ravel()
    times_flat = times_flat.ravel()  

    # Create SkyCoord with array obstime
    hpc = SkyCoord(
        Tx_flat, Ty_flat,
        frame=frames.Helioprojective,
        obstime=times_flat,
        observer=observer
    )

    # Transform to Carrington
    hgcrs = hpc.transform_to(frames.HeliographicCarrington(obstime=times_flat))

    # Reshape back to 2D
    lon_deg = hgcrs.lon.to(u.deg).value.reshape(ny, nx)
    lat_deg = hgcrs.lat.to(u.deg).value.reshape(ny, nx)


    # Apply differential rotation 
    # sunpy.diff_rot expects dd in days and lat in degrees; returns degrees.
    
    drot_deg = diff_rot(dd_days*u.day, lat_deg*u.deg,
                        frame_time='carrington',  # matches /carrington
                        ).to(u.deg).value

    lon_deg = lon_deg + drot_deg

    # Fix latitudes beyond [-90, 90]
    w_over = lat_deg > 90.0
    if np.any(w_over):
        lat_deg[w_over] = 180.0 - lat_deg[w_over]
        lon_deg[w_over] = lon_deg[w_over] + 180.0

    w_under = lat_deg < -90.0
    if np.any(w_under):
        lat_deg[w_under] = -180.0 - lat_deg[w_under]
        lon_deg[w_under] = lon_deg[w_under] + 180.0

    # Convert back to HPC at target time/WCS 
    w_out = WCS(header if target_header is None else target_header)
    # Build HG Carrington SkyCoord at target_time
    hgcrs_new = SkyCoord(
        lon=lon_deg*u.deg,
        lat=lat_deg*u.deg,
        frame=frames.HeliographicCarrington,
        obstime=target_time,
        observer=observer  
    )
    
    # Convert to HPC at target_time with the output WCS's observer if available
    hpc_out = hgcrs_new.transform_to(frames.Helioprojective(observer=observer, obstime=target_time))
    Tx_new = hpc_out.Tx.to(u.arcsec).value
    Ty_new = hpc_out.Ty.to(u.arcsec).value

    # Only update finite (on-disk) values
    finite = np.isfinite(Tx_new) & np.isfinite(Ty_new)
    Tx_corr = Tx.copy()
    Ty_corr = Ty.copy()
    Tx_corr[finite] = Tx_new[finite]
    Ty_corr[finite] = Ty_new[finite]

    return np.array([Tx_corr, Ty_corr])





def get_earth_observer(header):
    obstime = Time(header['DATE-OBS'])

    return SkyCoord(
        lon=0*u.deg, lat=0*u.deg, radius=1*u.AU,
        frame=frames.HeliographicStonyhurst,
        obstime=Time(obstime)
    )

def observer_from_header(header):
    """
    Build a SkyCoord observer location from FITS WCS keywords.
    """
    dsun = header.get("DSUN_OBS") * u.m     # Sun-observer distance
    lon  = header.get("CRLN_OBS") * u.deg   # Carrington longitude
    lat  = header.get("CRLT_OBS") * u.deg   # Carrington latitude
    obstime = Time(header.get("DATE-OBS"))

    observer_hgs = SkyCoord(lon, lat, dsun,
                        frame=frames.HeliographicStonyhurst,
                        obstime=obstime)

    return observer_hgs


