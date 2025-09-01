import numpy as np
from ..pix_desat import pix_desat
import pytest

from astropy.io import fits

#Build a customized hdul for testing
@pytest.fixture
def hdu_test():
    # Create random image
    image = np.random.random((1, 50, 50, 1))

    # 100 random pixel indices to set as NaN
    flat_indices = np.random.choice(image.size, size=100, replace=False)
    coords = np.unravel_index(flat_indices, image.shape)
    image[coords] = np.nan

    # Build Primary HDU 
    primary_hdu = fits.PrimaryHDU(image)
    primary_hdu.header["PIXLISTS"] = "SATPIX"

    # Build the Table HDU for only 80 NaN pixels
    
    chosen_idx = np.random.choice(len(flat_indices), size=80, replace=False)
    yy = coords[2][chosen_idx]
    xx = coords[1][chosen_idx]

    col0 = np.ones_like(xx)                      
    col1 = yy + 1                   
    col2 = xx + 1                            
    col3 = np.ones_like(xx)                          
    col4 = np.random.random(size=len(xx))        
    col5 = np.ones_like(xx)                     

    cols = fits.ColDefs([
        fits.Column(name="DIM1", format="J", array=col0),
        fits.Column(name="Y", format="J", array=col1),
        fits.Column(name="X",    format="J", array=col2),
        fits.Column(name="DIM2",    format="J", array=col3),
        fits.Column(name="VALUE",format="E", array=col4),
        fits.Column(name="THR",  format="J", array=col5),
    ])

    table_hdu = fits.BinTableHDU.from_columns(cols, name="SATPIX")

    # Create hdu list
    hdul = fits.HDUList([primary_hdu, table_hdu])

    return hdul



def test_desat(hdu_test):

    # hdu list for testing with 100 random nans
    # and a pixel tab with a new value for 80 of them
    hdutest_corr = pix_desat(hdu_test)

    dataTest = hdu_test[0].data
    dataTestC = hdutest_corr[0].data

    assert np.isnan(dataTest[ 0, :, :, 0]).sum() == 100
    assert np.isnan(dataTestC[ 0, :, :, 0]).sum() == 20
