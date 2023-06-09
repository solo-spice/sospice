import pytest
from datetime import datetime
import pandas as pd


from ..catalog import Catalog, get_file_relative_path


@pytest.fixture
def catalog2():
    return Catalog(release_tag="2.0")


@pytest.fixture
def catalog_latest():
    return Catalog(release_tag="latest")


@pytest.fixture
def catalog_empty():
    return Catalog()


@pytest.fixture
def catalog_df():
    df = pd.DataFrame(
        {
            "NAXIS1": [12, 15, 20],
            "NAXIS2": [100, 101, 102],
            "NAXIS3": [41, 44, 47],
            "NAXIS4": [1, 1, 1],
            "OBT_BEG": [0, 0, 0],
            "LEVEL": ["L2", 0, 0],
            "FILENAME": [0, 0, 0],
            "DATE-BEG": [pd.Timestamp("2023-02-01T12:34"), 0, 0],
            "SPIOBSID": [0, 0, 0],
            "RASTERNO": [0, 0, 0],
            "STUDYTYP": [0, 0, 0],
            "MISOSTUD": [0, 0, 0],
            "XPOSURE": [0, 0, 0],
            "CRVAL1": [0, 0, 0],
            "CDELT1": [0, 0, 0],
            "CRVAL2": [0, 0, 0],
            "CDELT2": [0, 0, 0],
            "STP": [0, 0, 0],
            "DSUN_AU": [0, 0, 0],
            "CROTA": [0, 0, 0],
            "OBS_ID": [0, 0, 0],
            "SOOPNAME": [0, 0, 0],
            "SOOPTYPE": [0, 0, 0],
            "NWIN": [0, 0, 0],
            "DARKMAP": [0, 0, 0],
            "COMPLETE": [0, 0, 0],
            "SLIT_WID": [0, 0, 0],
            "DATE": [0, 0, 0],
            "PARENT": [0, 0, 0],
            "HGLT_OBS": [0, 0, 0],
            "HGLN_OBS": [0, 0, 0],
            "PRSTEP1": [0, 0, 0],
            "PRPROC1": [0, 0, 0],
            "PRPVER1": [0, 0, 0],
            "PRPARA1": [0, 0, 0],
            "proc_steps": [
                '[{"PRPROC": "JPEG Compression (On-board)"},'
                ' {"PRPROC": "spice_prep_dark_offset_correction.pro",'
                ' "PRPVER": "1.3", "PRPARA": "dark_spiobsid=117440828"}]',
                0,
                0,
            ],
        }
    )
    return Catalog(data_frame=df)


def test_get_file_relative_path(catalog_df):
    path = get_file_relative_path(catalog_df.iloc[0])
    assert path.as_posix() == "level2/2023/02/01"


class TestCatalog:
    def test_init_filename(self):
        filename = "wepocmwkx.fts"
        with pytest.raises(RuntimeError, match="does not exist"):
            catalog = Catalog(filename)  # noqa: F841

    def test_init_release(self, catalog2, catalog_latest):
        columns = {
            "NAXIS1",
            "NAXIS2",
            "NAXIS3",
            "NAXIS4",
            "OBT_BEG",
            "LEVEL",
        }
        assert columns.issubset(catalog2.columns)
        assert len(catalog2) > 10000
        assert columns.issubset(catalog_latest.columns)
        assert len(catalog_latest) > 10000
        assert catalog_latest._cache_release_catalog() is None

    def test_init_empty(self, catalog_empty):
        assert len(catalog_empty) == 0
        assert len(catalog_empty.columns) == 0

    def test_init_dataframe(self, catalog_df):
        assert len(catalog_df) == 3
        assert len(catalog_df.columns) == 36
        assert catalog_df.iloc[1].NAXIS2 == 101

    def test_find_file(self, catalog2):
        expected_filename = "solo_L2_spice-n-exp_20211204T120022_V02_83886365-000.fits"
        result = catalog2.find_file(pd.Timestamp("2021-10-10"))
        assert result.FILENAME == expected_filename
        result = catalog2.find_file(datetime(2021, 10, 10))
        assert result.FILENAME == expected_filename
        result = catalog2.find_file("2021-10-10")
        assert result.FILENAME == expected_filename
        result = catalog2.find_file(None)
        assert result is None
