import pytest

import astropy.units as u

from ..study import Study


@pytest.fixture
def empty_study():
    return Study()


@pytest.fixture
def header():
    return {
        "SLIT_WID": 4.0,
        "NBIN3": 1,
        "NBIN2": 2,
        "XPOSURE": 10.0,
        "NAXIS3": 48,
        "WAVEMIN": 769,
        "WAVEMAX": 771,
        "WAVEUNIT": -10,
        "LEVEL": "L2",
        "RADCAL": 1000.0,
    }


@pytest.fixture
def study(header):
    s = Study()
    s.init_from_header(header)
    return s


class TestStudy:
    def test_init(self, empty_study):
        attributes = [
            "slit",
            "bin_x",
            "bin_y",
            "window_width",
            "exp_time",
            "av_wavelength",
            "radcal",
        ]
        for attribute in attributes:
            assert getattr(empty_study, attribute) is None

    def test_init_from_header(self, study):
        expected_values = {
            "slit": 4 * u.arcsec,
            "bin_x": 1,
            "bin_y": 2,
            "window_width": 48 * u.pix,
            "exp_time": 10 * u.s,
            "av_wavelength": 77 * u.nm,
            "radcal": 1000 * u.ct * u.m**2 * u.nm * u.sr / u.W,
        }
        for attribute in expected_values:
            assert u.isclose(getattr(study, attribute), expected_values[attribute])

    def test___str__(self, empty_study, study):
        assert str(empty_study) == "Non-initialized study"
        assert type(str(study)) is str
