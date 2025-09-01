import pytest
from datetime import datetime
import pandas as pd
import astropy.units as u

from ..catalog import Catalog
from ..file_metadata import FileMetadata



@pytest.fixture
def catalog2():
    return Catalog(release_tag="2.0")


@pytest.fixture
def catalog3():
    return Catalog(release_tag="3.0")


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
            "TELAPSE": [60, 1, 1],
            "LEVEL": ["L2", 0, 0],
            "FILENAME": [0, 0, 0],
            "DATE-BEG": [pd.Timestamp("2023-02-01T12:34"), 0, 0],
            "SPIOBSID": [0, 0, 0],
            "RASTERNO": [0, 0, 0],
            "STUDYTYP": [0, 0, 0],
            "STUDY": ["Compo", "Dynamics", "Whatever"],
            "MISOSTUD": [0, 0, 0],
            "XPOSURE": [0, 0, 0],
            "CRVAL1": [0, 0, 0],
            "CDELT1": [0, 0, 0],
            "CTYPE1": ["HPLN-TAN"] * 3,
            "CUNIT1": ["arcsec"] * 3,
            "CRVAL2": [0, 0, 0],
            "CDELT2": [0, 0, 0],
            "CTYPE2": ["HPLT-TAN"] * 3,
            "CUNIT2": ["arcsec"] * 3,
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
        assert len(catalog_df.columns) == 42
        assert catalog_df.iloc[1].NAXIS2 == 101

    def test_find_files_by_keywords(self, catalog2):
        result = catalog2.find_files_by_keywords()
        assert len(result) == 15643
        result = catalog2.find_files_by_keywords(level=None)
        assert len(result) == 15643
        result = catalog2.find_files_by_keywords(level="L2")
        assert len(result) == 7756
        result = catalog2.find_files_by_keywords(level="L2", nbin3=2)
        assert len(result) == 201

    def test_find_files_by_date_range(self, catalog2):
        result = Catalog().find_files_by_date_range()
        assert result.empty
        result = catalog2.find_files_by_date_range()
        assert len(result) == 15643
        result = catalog2.find_files_by_date_range(date_min="2022-01-01")
        assert len(result) == 14039
        assert result["DATE-BEG"].min() > pd.Timestamp("2022-01-01")
        result = catalog2.find_files_by_date_range(
            date_min="2022-01-01", date_max="2022-03-01"
        )
        assert len(result) == 1711
        assert result["DATE-BEG"].max() < pd.Timestamp("2022-03-01")

    def test_find_file_closest_to_date(self, catalog2):
        expected_filename = "solo_L2_spice-n-exp_20211204T120022_V02_83886365-000.fits"
        result = catalog2.find_file_closest_to_date(pd.Timestamp("2021-10-10"))
        assert result.FILENAME == expected_filename
        result = catalog2.find_file_closest_to_date(datetime(2021, 10, 10))
        assert result.FILENAME == expected_filename
        result = catalog2.find_file_closest_to_date("2021-10-10")
        assert result.FILENAME == expected_filename
        result = catalog2.find_file_closest_to_date(None)
        assert result.empty

    def test_find_file_by_wavelength(self, catalog3):
        expected_filename = "solo_L2_spice-n-exp_20211010T000110_V03_83886152-000.fits"
        wl = 70.8 * u.nm
        wl2 = 10 * u.nm
        wlA = wl.to(u.AA)
        result = catalog3.find_files_by_wavelength(wavelength=wl)
        assert len(result) == 23371
        result = catalog3.find_files_by_wavelength(wl)
        assert len(result) == 23371
        result = catalog3.find_files_by_wavelength(wl2)
        assert result.empty
        result = catalog3.find_files_by_wavelength(wlA)
        assert len(result) == 23371

        #closest to date
        result = catalog3.find_files_by_wavelength(wl)
        result = result.find_file_closest_to_date("2021-10-10")
        assert result.FILENAME == expected_filename

        assert wl in FileMetadata(result).get_wavelengths()


    def test_find_files(self, catalog2):
        result = Catalog().find_files()
        assert result.empty
        result = catalog2.find_files()
        assert len(result) == 7756
        result = catalog2.find_files(level=None)
        assert len(result) == 15643
        result = catalog2.find_files(query="NBIN3==2")
        assert len(result) == 201
        expected_filename = "solo_L2_spice-n-exp_20211204T120022_V02_83886365-000.fits"
        result = catalog2.find_files(closest_to_date="2021-10-10")
        assert len(result) == 1
        assert result.iloc[0].FILENAME == expected_filename

    def test__format_time_range(self, catalog2):
        cat = catalog2.find_files(level="L2", spiobsid=117440593)
        row = cat.iloc[0].copy()
        assert Catalog._format_time_range(row) == "2022-04-12T08:00"
        row["last_DATE-BEG"] = cat.iloc[-1]["DATE-BEG"]
        assert Catalog._format_time_range(row) == "2022-04-12T08:00 - T08:51"
        row["last_DATE-BEG"] = pd.Timestamp("2022-04-13T12:00")
        assert Catalog._format_time_range(row) == "2022-04-12T08:00 - 2022-04-13T12:00"

    def test_mid_time(self, catalog2):
        cat = catalog2.find_files(level="L2", spiobsid=117440593)
        assert (
            abs(cat.mid_time() - pd.Timestamp("2022-04-12 08:26:46")).total_seconds()
            < 1  # noqa: W503
        )
        assert (
            abs(
                cat.mid_time(method="mean") - pd.Timestamp("2022-04-12 08:27:16")
            ).total_seconds()
            < 1  # noqa: W503
        )
        assert (
            abs(
                cat.mid_time(method="barycenter") - pd.Timestamp("2022-04-12 08:26:47")
            ).total_seconds()
            < 1  # noqa: W503
        )
