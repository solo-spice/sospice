import itertools

from tqdm import tqdm
import numpy as np
import scipy.interpolate as si




def get_interpolation_points(coord_grid,coord_real):
    """ Get the origin and target points for the interpolation

    Parameters
    ==========
    hdul : fits.HDUList
        HDU list with the image extensions for which to compute the
        coordinates, plus two image extensions ``WCSDVARR`` (1 and 2)
        containing the pointing distortion correction for `T_x` and `T_y`.

    Returns
    =======
    points : array_like
        Array of shape (ny*nx, 2) containing the coordinates of the data
        points.
    new_points : array_like
        Array of shape (ny*nx, 2) containing the points at which to interpolate
        the data.
    """
   

    # Interpolation initial and target points
    points = coord_real.reshape(2, -1).T
    new_points = np.moveaxis(coord_grid, 0, -1)
    return points, new_points


def remap_spice_hdu(hdu, points, new_points, sum_wvl=False):
    """ Remap a SPICE spectral cube to corrected coordinates

    Parameters
    ==========
    hdu : fits.PrimaryHDU, fits.ImageHDU, fits.BinTableHDU
        SPICE L2 FITS HDU to remap. (If the HDU is not of 'image' type, return
        it without modification.)
    points : array_like or sspatial.Delaunay
        Array of shape (ny*nx, 2) containing the coordinates of the data
        points, or precomputed Delaunay triangulation.
    new_points : array_like
        Array of shape (ny*nx, 2) containing the points at which to interpolate
        the data.
    new_points : array_like
    sum_wvl : bool
        If True, sum along wavelength axis to generate a quicklook image.

    Returns
    =======
    hdu : fits.PrimaryHDU, fits.ImageHDU, fits.BinTableHDU
        Aligned SPICE 'L2r' HDU, matching the type of the input HDU.
    """
    if not hdu.is_image or hdu.name == 'WCSDVARR':
        return hdu

    new_hdu = hdu.copy()
    if sum_wvl:
        # Integrated intensity
        img = np.nansum(hdu.data, axis=1)  # Sum over wavelengths
        img = np.squeeze(img)  # Collapse 1-depth axis (t or X)
        interp = si.LinearNDInterpolator(points, img.flatten())
        new_img = interp(new_points)
        new_hdu.data = new_img.reshape(1, 1, *new_img.shape)
    else:
        # Remap to new coordinates within time and/or wvl slices
        nt, nD, _, _ = hdu.data.shape
        itD = itertools.product(range(nt), range(nD))
        for it, iD in tqdm(itD, desc=f'Remapping {hdu.name}', total=nt * nD):
            img = hdu.data[it, iD]
            interp = si.LinearNDInterpolator(points, img.flatten())
            new_img = interp(new_points)
            new_hdu.data[it, iD] = new_img

    new_hdu.update_header()
    new_hdu.add_datasum()
    new_hdu.add_checksum()
    return new_hdu


