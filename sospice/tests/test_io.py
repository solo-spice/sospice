import os.path

import numpy as np
import pytest
from astropy.io import fits
from ndcube import NDCollection
from sunraster import RasterSequence, SpectrogramCube, SpectrogramSequence

from sospice.io import read_spice_l2_fits
from sospice.tests import TEST_DATA_PATH

READ_SPICE_L2_FITS_RETURN_TYPE = NDCollection


@pytest.fixture
def spice_rasdb_filename(tmp_path):
    """
    Inserts data into a raster SPICE FITS file with dumbbells and returns new
    filename.

    A new FITS file is saved in a tmp file path.
    """
    rng_gen = np.random.default_rng()
    filename = "solo_L2_spice-n-ras-db_20200602T081733_V01_12583760-000.fits"
    with fits.open(TEST_DATA_PATH / filename) as hdulist:
        new_hdulist = fits.HDUList()
        new_hdulist.append(fits.PrimaryHDU(rng_gen.random((1, 48, 832, 30)), header=hdulist[0].header))
        new_hdulist.append(fits.ImageHDU(rng_gen.random((1, 48, 832, 30)), header=hdulist[1].header))
        new_hdulist.append(fits.ImageHDU(rng_gen.random((1, 56, 64, 30)), header=hdulist[2].header))
        new_hdulist.append(fits.ImageHDU(rng_gen.random((1, 56, 64, 30)), header=hdulist[3].header))
        new_hdulist.append(hdulist[-1])
        tmp_spice_path = tmp_path / "spice"
        if not os.path.exists(tmp_spice_path):
            tmp_spice_path.mkdir()
        new_filename = os.path.join(tmp_spice_path, filename)
        new_hdulist.writeto(new_filename, overwrite=True)
    return new_filename


@pytest.fixture
def spice_sns_filename(tmp_path):
    """
    Inserts data into a sit-and-stare SPICE FITS file and returns new filename.

    A new FITS file is saved in a tmp file path.
    """
    rng_gen = np.random.default_rng()
    filename = "solo_L2_spice-n-sit_20200620T235901_V01_16777431-000.fits"
    with fits.open(TEST_DATA_PATH / filename) as hdulist:
        new_hdulist = fits.HDUList()
        new_hdulist.append(fits.PrimaryHDU(rng_gen.random((32, 48, 1024, 1)), header=hdulist[0].header))
        new_hdulist.append(fits.ImageHDU(rng_gen.random((32, 48, 1024, 1)), header=hdulist[1].header))
        new_hdulist.append(hdulist[-1])
        tmp_spice_path = tmp_path / "spice"
        if not os.path.exists(tmp_spice_path):
            tmp_spice_path.mkdir()
        new_filename = os.path.join(tmp_spice_path, filename)
        new_hdulist.writeto(new_filename, output_verify="fix+ignore", overwrite=True)
    return new_filename


def test_read_spice_l2_fits_single_file_multiple_windows(spice_rasdb_filename):
    filename = spice_rasdb_filename
    result = read_spice_l2_fits(filename)
    assert isinstance(result, READ_SPICE_L2_FITS_RETURN_TYPE)
    assert set(result.aligned_axes.values()) == {(0, 2, 3)}
    assert len(result) == 2
    assert all(isinstance(window, SpectrogramCube) for window in result.values())


def test_read_spice_l2_fits_single_file_window(spice_rasdb_filename):
    filename = spice_rasdb_filename
    result = read_spice_l2_fits(filename, windows=["WINDOW0_70.51"])
    assert isinstance(result, READ_SPICE_L2_FITS_RETURN_TYPE)
    assert result.aligned_axes is None
    assert len(result) == 1
    assert all(isinstance(window, SpectrogramCube) for window in result.values())


def test_read_spice_l2_fits_single_file_dumbbells(spice_rasdb_filename):
    filename = spice_rasdb_filename
    result = read_spice_l2_fits(filename, read_dumbbells=True)
    assert isinstance(result, READ_SPICE_L2_FITS_RETURN_TYPE)
    assert all(window.meta.contains_dumbbell for window in result.values())
    assert set(result.aligned_axes.values()) == {tuple(range(4))}
    assert all(isinstance(window, SpectrogramCube) for window in result.values())


def test_read_spice_l2_fits_multiple_rasters_multiple_windows(spice_rasdb_filename):
    filenames = [spice_rasdb_filename] * 2
    result = read_spice_l2_fits(filenames)
    assert isinstance(result, READ_SPICE_L2_FITS_RETURN_TYPE)
    assert set(result.aligned_axes.values()) == {(0, 2, 3)}
    assert len(result) == 2
    assert all(window.dimensions[0].value == len(filenames) for window in result.values())
    assert all(isinstance(window, RasterSequence) for window in result.values())


def test_read_spice_l2_fits_multiple_rasters_single_window(spice_rasdb_filename):
    filenames = [spice_rasdb_filename] * 2
    result = read_spice_l2_fits(filenames, windows=["WINDOW0_70.51"])
    assert isinstance(result, READ_SPICE_L2_FITS_RETURN_TYPE)
    assert result.aligned_axes is None
    assert len(result) == 1
    assert all(window.dimensions[0].value == len(filenames) for window in result.values())
    assert all(isinstance(window, RasterSequence) for window in result.values())


def test_read_spice_l2_fits_multiple_sns_multiple_windows(spice_sns_filename):
    filenames = [spice_sns_filename] * 2
    result = read_spice_l2_fits(filenames)
    assert isinstance(result, READ_SPICE_L2_FITS_RETURN_TYPE)
    assert set(result.aligned_axes.values()) == {(0, 2, 3)}
    assert len(result) == 2
    assert all(window.dimensions[0].value == len(filenames) for window in result.values())
    assert all(isinstance(window, SpectrogramSequence) for window in result.values())


def test_read_spice_l2_fits_multiple_files_dumbbells(spice_rasdb_filename):
    filenames = [spice_rasdb_filename] * 2
    result = read_spice_l2_fits(filenames, read_dumbbells=True)
    assert isinstance(result, READ_SPICE_L2_FITS_RETURN_TYPE)
    assert all(window[0].meta.contains_dumbbell for window in result.values())
    assert set(result.aligned_axes.values()) == {tuple(range(4))}
    assert all(window.dimensions[0].value == len(filenames) for window in result.values())
    assert all(isinstance(window, SpectrogramSequence) for window in result.values())


def test_read_spice_l2_fits_incompatible_files(spice_rasdb_filename, spice_sns_filename):
    with pytest.raises(ValueError):
        filenames = [spice_rasdb_filename, spice_sns_filename]
        read_spice_l2_fits(filenames)
