import numpy as np
from ..compute_coordinates import _assert_hdus_have_the_same_spatial_coordinates, spice_diff_rot_coord
from astropy.io import fits
from ...catalog import Catalog
import pytest
import pandas as pd

import astropy.units as u
from astropy.time import Time
from astropy.coordinates import SkyCoord
from astropy.wcs import WCS
from sunpy.coordinates import frames


@pytest.fixture
def catalog2():
    return Catalog(release_tag="2.0")

# def test_coordinates():
#     result = catalog2.find_file_closest_to_date(pd.Timestamp("2021-10-10"))
#     # open file from catalog = data
#     hdulist = fits.open(data)
#     _assert_hdus_have_the_same_spatial_coordinates(hdulist)

@pytest.fixture
def header():
    w = WCS(naxis=4)
    w.wcs.ctype = ['HPLN-TAN', 'HPLT-TAN', 'WAVE', 'TIME']
    w.wcs.cunit = ['arcsec', 'arcsec', 'Angstrom', 's']
    w.wcs.crpix = [1, 1, 1, 1]
    w.wcs.cdelt = [1, 1, 1, 1]
    w.wcs.crval = [0, 0, 0, 0]

    hdr = w.to_header()
    hdr["DATE-BEG"] = "2024-01-01T00:00:00"
    hdr["DATE-AVG"] = "2024-01-01T00:00:00"

    return hdr


@pytest.fixture
def target_header(header):
    hdr = header.copy()
    hdr["DATE-AVG"] = "2024-01-02T00:00:00"
    return hdr


@pytest.fixture
def observer():
    return SkyCoord(
        0*u.deg, 0*u.deg, 1*u.AU,
        frame=frames.HeliographicStonyhurst,
        obstime=Time("2024-01-01T00:00:00")
    )


@pytest.fixture
def hpc(observer):
    ny, nx = 4, 5

    tx = np.zeros((ny, nx)) * u.arcsec
    ty = np.zeros((ny, nx)) * u.arcsec

    return SkyCoord(
        Tx=tx,
        Ty=ty,
        frame=frames.Helioprojective,
        observer=observer,
        obstime=Time("2024-01-01T00:00:00")
    )

def test_spice_diff_rot_no_time_shift(hpc, header, observer):
    out = spice_diff_rot_coord(header, hpc, observer)

    assert u.allclose(out.Tx, hpc.Tx)
    assert u.allclose(out.Ty, hpc.Ty)

def test_spice_diff_rot_shape(hpc, header, observer, target_header):
    out = spice_diff_rot_coord(
        header, hpc, observer, target_header=target_header
    )

    assert out.Tx.shape == hpc.Tx.shape
    assert out.Ty.shape == hpc.Ty.shape

def test_spice_diff_rot_changes_coordinates(hpc, header, observer, target_header):
    out = spice_diff_rot_coord(
        header, hpc, observer, target_header=target_header
    )

    assert not u.allclose(out.Tx, hpc.Tx)
