import pytest

from astropy.io import fits
import astropy.units as u

from ..uncertainties import spice_error


specrad_unit = u.mW / u.m**2 / u.sr / u.nm


@pytest.fixture
def hdus():
    # all expected values in specrad_unit
    hdus = [
        {
            "url": "https://spice.osups.universite-paris-saclay.fr/spice-data/release-3.0/level2/2022/04/02/solo_L2_spice-n-ras_20220402T111537_V06_100664002-000.fits",
            "hdu_index": 2,  # Ne VIII window
            "expected_constant": 42.9513921,
            "pixel_index": (0, 25, 415, 80),
            "expected": {
                "Dark": 20.36091256,
                "Background": 0.0,
                "Read": 66.59878776,
                "Signal": 168.60160232,
                "Total": 182.41837621,
            },
        },
        {  # File used for comparison with MPS' IDL code
            "url": "https://spice.osups.universite-paris-saclay.fr/spice-data/release-3.0/level2/2021/02/23/solo_L2_spice-n-ras_20210223T154400_V10_50331754-000.fits",
            "hdu_index": 2,  # Lyγ - C III
            "expected_constant": 87.80646,
            "pixel_index": (0, 25, 415, 80),
            "expected": {
                "Dark": 26.718655,
                "Background": 0.0,
                "Read": 56.098571,
                "Signal": 61.990004,
                "Total": 87.7707,
            },
        },
    ]
    for item in hdus:
        item["hdu_list"] = fits.open(item["url"])
    yield hdus
    for item in hdus:
        item["hdu_list"].close()


class TestUncertainties:
    def test_spice_error(self, hdus):
        for item in hdus:
            av_constant_noise_level, sigma = spice_error(
                item["hdu_list"][item["hdu_index"]]
            )
        assert u.isclose(
            av_constant_noise_level, item["expected_constant"] * specrad_unit
        )
        for component in item["expected"]:
            pixel_index = (
                () if len(sigma[component].shape) == 0 else item["pixel_index"]
            )
            print(f"{sigma[component][pixel_index]=}")
            assert u.isclose(
                sigma[component][pixel_index],
                item["expected"][component] * specrad_unit,
            )
