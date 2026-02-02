
from astropy import wcs
import astropy.units as u
import numpy as np

from astropy.time import Time

from sunpy.coordinates import frames
from sunpy.physics.differential_rotation import diff_rot
from astropy.coordinates import SkyCoord
from astropy.wcs import WCS
from sunpy.sun.models import differential_rotation
from astropy.constants import R_sun


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




def spice_diff_rot_coord(coordinates, header, hpc, observer, target_header = None):
    """
    Apply solar differential rotation to helioprojective coordinates

    Parameters
    ----------
    coordinates : np.ndarray
        Shape (2, ny, nx), array of [Tx, Ty] in arcsec (helioprojective)
    header : fits.Header
        Header defining the WCS (HPC + time axis). Should contain DATEREF or DATE-OBS
    target_header : fits.Header, optional
        If given, final coordinates are converted into this WCS/time.

    Returns
    -------
    np.ndarray
        Shape (2, ny, nx), corrected [Tx, Ty] in arcsec at the target time/WCS.
    """

    Tx = coordinates.Tx.to(u.arcsec).value
    Ty = coordinates.Ty.to(u.arcsec).value
    ny, nx = Tx.shape


    # Reference date
    #dateref = header.get('DATEREF', header.get('DATE-OBS'))
    dateref = header.get('DATE-BEG')
    if dateref is None:
        raise ValueError("Header must contain DATEREF or DATE-OBS")

    # average/target time default
    #date_avg = header.get('DATE-AVG', header.get('DATE-OBS'))
    date_avg = header.get('DATE-BEG')
    if date_avg is None:
        raise ValueError("Header must contain DATE-AVG or DATE-OBS")
    t_avg = Time(date_avg)

    # build WCS 
    w_in = WCS(header)
    iy, ix = np.indices((ny, nx))
    iD = np.zeros_like(ix)   #  wavelength 
    it = np.zeros_like(ix)   #  time 

    # Build Nx4 pixel array and map to world
    pix_stack = np.stack([ix, iy, iD, it], axis=-1).reshape(-1, 4)
    # wcs_pix2world returns an (N,4) array of world values 
    world = w_in.wcs_pix2world(pix_stack, 0)  
    t_ref = Time(dateref)
    seconds_from_ref = world[:, -1] 
    times_flat = t_ref + seconds_from_ref * u.s
    times = times_flat.reshape(ny, nx)

    # target time for rotation
    if target_header is None:
        target_time = t_avg
    else:
        target_time = Time(target_header.get('DATE-AVG', target_header.get('DATE-OBS', date_avg)))


    dd_days = (target_time - times).to(u.day).value
    if np.all(dd_days == 0):
        return np.array([Tx, Ty])

    # Convert HPC -> HelioCarrington (lon,lat)
    Tx_q = (Tx * u.arcsec).reshape(ny, nx)
    Ty_q = (Ty * u.arcsec).reshape(ny, nx)


    times_flat = times_flat.ravel() 

    # radius 
    rad = R_sun * 1.005

    
    # Transform to Carrington
    hgcrs = hpc.transform_to(frames.HeliographicCarrington())


    lon_deg = hgcrs.lon.to(u.deg).value.reshape(ny, nx)
    lat_deg = hgcrs.lat.to(u.deg).value.reshape(ny, nx)

    # Apply differential rotation 
    drot_deg = differential_rotation(dd_days * u.day,lat_deg * u.deg).to(u.deg).value
    lon_deg = lon_deg + drot_deg 

    # Correct any latitudes that go beyond -90 to +90
    w_over = lat_deg > 90.0
    if np.any(w_over):
        lat_deg[w_over] = 180.0 - lat_deg[w_over]
        lon_deg[w_over] = lon_deg[w_over] + 180.0

    w_under = lat_deg < -90.0
    if np.any(w_under):
        lat_deg[w_under] = -180.0 - lat_deg[w_under]
        lon_deg[w_under] = lon_deg[w_under] + 180.0

    # Convert back to HPC at target_time
    hgcrs_new = SkyCoord(lon=lon_deg * u.deg,
                        lat=lat_deg * u.deg,
                        radius=rad,
                        frame=frames.HeliographicCarrington,
                        observer=observer)

    hpc_out = hgcrs_new.transform_to(frames.Helioprojective(observer=observer))



    Tx_new = hpc_out.Tx.to(u.arcsec).value.reshape(ny, nx)
    Ty_new = hpc_out.Ty.to(u.arcsec).value.reshape(ny, nx)

    finite = np.isfinite(Tx_new) & np.isfinite(Ty_new)
    Tx_corr = Tx.copy()
    Ty_corr = Ty.copy()
    Tx_corr[finite] = Tx_new[finite]
    Ty_corr[finite] = Ty_new[finite]

    return np.array([Tx_corr, Ty_corr])