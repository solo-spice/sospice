import pytest

import numpy as np
import astropy.units as u

from ..spice import Spice


@pytest.fixture
def spice():
    return Spice()


class TestSpice:
    def test_init(self, spice):
        assert spice.read_noise == 6.9 * u.ct / u.pix
        assert spice.aeff_data is None

    def test_effective_area(self, spice):
        # Expected values in mm² for wavelengths in nm
        expected = {
            20: np.nan,
            77: 4.33579493,  # Ne VIII (SW)
            102.6: 9.57706423,  # H Lyβ (LW)
            52.1: 0.43514445,  # Si XII (LW, 2nd order)
            200: np.nan,
        }
        for wavelength in expected:
            assert u.isclose(
                spice.effective_area(wavelength * u.nm),
                expected[wavelength] * u.mm**2,
                equal_nan=True,
            )
        assert u.allclose(
            spice.effective_area([50, 80, 100] * u.nm),
            [0.28686351, 5.50425673, 9.21953583] * u.mm**2,
        )
        assert spice.aeff_data is not None

    def test_quantum_efficiency(self, spice):
        # Expected values for wavelengths in nm
        # Not sure about the value for 2nd order LW
        expected = {
            77: 0.1,
            102.6: 0.25,
        }
        for wavelength in expected:
            assert u.isclose(
                spice.quantum_efficiency(wavelength * u.nm), expected[wavelength]
            )

    def test_which_detector(self, spice):
        # Expected values for wavelengths in nm
        expected = {
            77: "SW",
            102.6: "LW",
        }
        for wavelength in expected:
            assert spice.which_detector(wavelength * u.nm) == expected[wavelength]
        # Expected None values
        expected_none = [70, 85, 106]
        for wavelength in expected_none:
            assert spice.which_detector(wavelength * u.nm) is None

    def test_gain(self, spice):
        # Expected values in DN/ph for wavelengths in nm
        expected = {
            20: np.nan,
            77: 3.58,
            102.6: 0.57,
            200: np.nan,
        }
        for wavelength in expected:
            assert u.isclose(
                spice.gain(wavelength * u.nm),
                expected[wavelength] * u.ct / u.ph,
                equal_nan=True,
            )

    def test_dark_current(self, spice):
        # Expected values in DN/s/pix for wavelengths in nm
        expected = {
            20: np.nan,
            77: 0.89,
            102.6: 0.54,
            200: np.nan,
        }
        for wavelength in expected:
            assert u.isclose(
                spice.dark_current(wavelength * u.nm),
                expected[wavelength] * u.ct / u.s / u.pix,
                equal_nan=True,
            )

    def test_noise_factor(self, spice):
        # Expected values in DN/s/pix for wavelengths in nm
        expected = {
            20: np.nan,
            77: 1.0,
            102.6: 1.6,
            200: np.nan,
        }
        for wavelength in expected:
            assert u.isclose(
                spice.noise_factor(wavelength * u.nm),
                expected[wavelength],
                equal_nan=True,
            )
