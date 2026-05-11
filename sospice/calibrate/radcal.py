# Rewritten in python from the Spice data analysis tool in IDL (T. Fredvik)
from astropy.io import fits
import re
from astropy.wcs import WCS
import numpy as np


def get_radcal(
    window: int | str,     
    hdul: fits.HDUList | None       = None,
    path_to_l2: str    | None       = None,
    return_base_wavelength: bool    = False,):
    """
    Return the radiometric calibration of a specific spectral window for an SPICE fits file.
    Accepts either an HDUList or the path to a L2 FITS file.

    Parameters
    ----------
    window: int or str
        index or extname of the spectral window in the HDUList 
    hdul: fits.HDUList (optional)
        HDUList of a SPICE FITS file
    path_to_l2: str
        path to a L2 SPICE fits file
    return_base_wavelength: bool
        set to True to return the wavelength array corresponding to the radiometric calibration
    Return
    ------
    ND array radiometric calibration array for the given spectral window, 
    (optional) ND array associated wavelength array

    """
    if ((hdul is None) & (path_to_l2 is None)) or ((hdul is not None) & (path_to_l2 is not None)):
        raise ValueError("Only one parameter (hdul or path_to_l2) must be provided")
    
    if path_to_l2 is not None:
        hdul = fits.open(path_to_l2)
    hdu = hdul[window]
    hdu_binary = hdul["VARIABLE_KEYWORDS"]
    if return_base_wavelength:
        radcal_array, wavelength_array = get_radcal_from_hdus(hdu=hdu,
                                                              hdu_binary=hdu_binary,
                                                              return_base_wavelength=return_base_wavelength)
        if path_to_l2 is not None:
            hdul.close()
        return radcal_array, wavelength_array
    else:
        radcal_array = get_radcal_from_hdus(hdu=hdu,
                                            hdu_binary=hdu_binary,
                                            return_base_wavelength=return_base_wavelength)
        if path_to_l2 is not None:
            hdul.close()        
        return radcal_array 
    
    



def get_radcal_from_hdus(hdu: fits.ImageHDU, hdu_binary: fits.BinTableHDU, return_base_wavelength: bool = False):

    """
    Return the radiometric calibration array for the corresponding spectral window HDU, and binary table. 

    Parameters
    ----------
    hdu: fits.ImageHDU
        HDU of the given spectral window
    binary_table: tuple
        VARIABLE_KEYWORDS of the corresponding HDUList
    return_base_wavelength: bool
        set to True to return the wavelength array corresponding to the radiometric calibration
    Return
    ------
    ND array radiometric calibration array for the given spectral window

    """    

    if (hdu.header["EXTNAME"] == "VARIABLE_KEYWORDS"):
        raise ValueError("The input hdu must correspond to a spectral window")

    radcal_ttype    = _get_radcal_ttype(hdu.header)
    radcal_array    = np.squeeze(hdu_binary.data[radcal_ttype])
    if return_base_wavelength:
        w = WCS(hdu.header)
        w_spec = w.spectral
        x = np.arange(hdu.data.shape[1])
        wavelength_array = w_spec.pixel_to_world(x)
        return radcal_array, wavelength_array
    else:
        return radcal_array





def _get_radcal_ttype(header_l2: fits.header):
    """
    Return the column number of the radiometric calibration in the
    binary table corresponding to the given FITS HDU header. 

    Parameters
    ----------
    header_l2: fits.header
        header of the HDU L2 fits file
    binary_table: tuple
        Range of base-10 logarithm of temperature, in K
  
    Return
    ------
    ttype of the radcal array on the binary table corresponding to the input header

    """    
    var_keys = header_l2["VAR_KEYS"]
    radcal_extname_list = re.findall('.+;', var_keys)
    if len(radcal_extname_list) != 1:
        raise KeyError("radcal extension name could not be found in the VAR_KEYS keyword value.")
    
    radcal_extname = radcal_extname_list[0][:-1]
    radcal_extname_and_ttype_list = re.findall(radcal_extname + '.+', var_keys)
    if len(radcal_extname_and_ttype_list) != 1:
        raise KeyError("radcal extension and ttype could not be found in the VAR_KEYS keyword value.")
    
    radcal_extname_and_ttype = radcal_extname_and_ttype_list[0]
    radcal_ttype_list = re.findall('RADCAL' + '.+', radcal_extname_and_ttype)
    if len(radcal_ttype_list) != 1:
        raise KeyError("radcal ttype could not be found in the VAR_KEYS keyword value.")
    radcal_ttype = radcal_ttype_list[0]
    return radcal_ttype

