import pytest
from astropy.io import fits
import numpy as np
from numpy.testing import assert_allclose
from ..radcal import get_radcal, get_radcal_from_hdus, _get_radcal_ttype


@pytest.fixture
def path_to_l2():
    url = ("https://spice.osups.universite-paris-saclay.fr/spice-data/"
    "release-5.0/level2/2022/04/02/solo_L2_spice-n-ras_20220402T111537_V22_100664002-000.fits")    
    return url


@pytest.fixture
def hdul():
    url = ("https://spice.osups.universite-paris-saclay.fr/spice-data/"
    "release-5.0/level2/2022/04/02/solo_L2_spice-n-ras_20220402T111537_V22_100664002-000.fits")
    hdul = fits.open(url)
    return hdul

@pytest.fixture
def results_radcal():
    return np.array([34.05953336, 34.02043985, 33.98132717, 33.94220939, 33.90304904,
        33.86389997, 33.82474689, 33.78557652, 33.74639605, 33.70720547,
        33.66796729, 33.62875244, 33.58952249, 33.55028136, 33.51102715,
        33.47176472, 33.43245371, 33.39315909, 33.3538633 , 33.31454938,
        33.27522236, 33.23585362, 33.19650528, 33.15714186, 33.11776728,
        33.07837563, 33.03897877, 32.9995372 , 32.96011114, 32.92068181,
        32.8812364 , 32.84177198, 32.80230035, 32.76278595, 32.72329296,
        32.68378298, 32.64425986, 32.60472563, 32.56518705, 32.52559685,
        32.48603011, 32.44644929, 32.40685532, 32.36725025, 32.32760231,
        32.28796808, 32.24833239, 32.2086739 , 32.169012  , 32.12933414],
        dtype='>f8')

def test_get_radcal(path_to_l2, hdul, results_radcal):


    radcal1 = get_radcal(window=0, path_to_l2=path_to_l2)
    assert_allclose(radcal1, results_radcal)

    radcal2 = get_radcal(window=0, hdul=hdul)
    assert_allclose(radcal2, results_radcal)

