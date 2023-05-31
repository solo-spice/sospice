import pytest

from astropy.io import fits
import astropy.units as u

from ..uncertainties import spice_error


@pytest.fixture
def hdu():
    url = "https://spice.osups.universite-paris-saclay.fr/spice-data/release-3.0/level2/2022/04/02/solo_L2_spice-n-ras_20220402T111537_V06_100664002-000.fits"
    # with fits.open(url) as hdu_list:
    hdu_list = fits.open(url)
    hdu = hdu_list[2]  # Ne VIII window
    yield hdu
    hdu_list.close()


class TestUncertainties:
    def test_spice_error(self, hdu):
        specrad_unit = u.mW / u.m**2 / u.sr / u.nm
        av_constant_noise_level, sigma = spice_error(hdu)
        assert u.isclose(av_constant_noise_level, 42.9513921 * specrad_unit)
        expected = {
            "Dark": 20.36091256,
            "Background": 0.0,
            "Read": 66.59878776,
            "Signal": 168.60160232,
            "Total": 182.41837621,
        }
        for component in expected:
            if len(sigma[component].shape) == 0:
                index = ()
            else:
                index = (0, 25, 415, 80)
            assert u.isclose(
                sigma[component][index], expected[component] * specrad_unit
            )
