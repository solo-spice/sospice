from dataclasses import dataclass

import pandas as pd
from pathlib import Path
from astropy.utils.data import download_file

from .release import Release


def get_file_relative_path(cat_row):
    """
    Get file relative path for a given catalog entry

    Parameters
    ----------
    cat_row: pandas.Series
        SPICE catalog entry

    Return
    ------
    pathlib.PosixPath
        File path, relative to the "fits" directory of the file archive:
        leveln/yyyy/mm/dd

    Requires a DATE-BEG header (so does not work with L0 files).
    """
    date = cat_row["DATE-BEG"]
    return (
        Path(f"level{cat_row.LEVEL[1]}")
        / f"{date.year}"  # noqa: W503
        / f"{date.month:02}"  # noqa: W503
        / f"{date.day:02}"  # noqa: W503
    )


@dataclass
class Catalog(pd.DataFrame):
    """
    A SPICE catalog, initialized (in that order) either from a filename, a release tag, or a pandas.DataFrame.

    Parameters
    ----------
    filename: str
        A file name (or URL) for the catalog
    release_tag: str
        A release tag. The catalog is fetched online and dowloaded to the astropy cache.
    data_frame: pandas.DataFrame
        A pandas DataFrame to be used as SPICE catalog. Some basic checks are made to ensure
        that is can be used as a SPICE catalog.
    update_cache: bool
        Update cached catalog for the given release tag
    """

    filename: str = None
    release_tag: str = None
    data_frame: str = None
    update_cache: bool = False

    def __post_init__(self):
        """
        Read catalog and update object
        """
        self._normalize_arguments()
        if self.release_tag is not None:
            self._cache_release_catalog()
        if self.filename is not None:
            super().__init__(self.read_catalog())
        else:
            if self.data_frame is None:
                self.data_frame = pd.DataFrame()
            self._validate_data_frame()
            super().__init__(self.data_frame)
            del self.data_frame  # needed for memory usage?
            self.data_frame = None

    def _normalize_arguments(self):
        """
        Prioritize filename then release tag then data frame
        """
        if self.filename is not None:
            self.release_tag = None
            self.data_frame = None
        elif self.release_tag is not None:
            self.data_frame = None

    def _cache_release_catalog(self):
        """
        Used cached catalog or download release catalog to astropy cache
        """
        if self.release_tag is None:
            return
        if self.release_tag == "latest":
            self.release_tag = None
        release = Release(self.release_tag)
        assert release.exists
        self.filename = download_file(release.catalog_url, cache=True)
        self.release_tag = None

    def _validate_data_frame(self):
        """
        Check that the data_frame argument can be considered a valid SPICE catalog (or raise an exception)
        """
        assert self.data_frame is not None
        if self.data_frame.empty:
            return True  # an empty data frame is valid
        required_columns = {
            "NAXIS1",
            "NAXIS2",
            "NAXIS3",
            "NAXIS4",
            "OBT_BEG",
            "LEVEL",
            "FILENAME",
            "DATE-BEG",
            "SPIOBSID",
            "RASTERNO",
            "STUDYTYP",
            "MISOSTUD",
            "XPOSURE",
            "CRVAL1",
            "CDELT1",
            "CRVAL2",
            "CDELT2",
            "STP",
            "DSUN_AU",
            "CROTA",
            "OBS_ID",
            "SOOPNAME",
            "SOOPTYPE",
            "NWIN",
            "DARKMAP",
            "COMPLETE",
            "SLIT_WID",
            "DATE",
            "PARENT",
            "HGLT_OBS",
            "HGLN_OBS",
            "PRSTEP1",
            "PRPROC1",
            "PRPVER1",
            "PRPARA1",
        }
        assert required_columns.issubset(self.data_frame.columns)

    def read_catalog(self):
        """
        Read SPICE FITS files catalog

        Return
        ------
        pandas.DataFrame
            Catalog
        """
        if not Path(self.filename).exists():
            raise RuntimeError(f"File {self.filename} does not exist")
        df = pd.read_csv(
            self.filename,
            low_memory=False,
        )
        date_columns = ["DATE-BEG", "DATE", "TIMAQUTC"]
        for date_column in date_columns:
            df.loc[df[date_column] == "MISSING", date_column] = "NaT"
            df[date_column] = pd.to_datetime(df[date_column], format="ISO8601")
        return df

    def find_file(self, date=None, level="L2"):
        """
        Find closest file to some observation data (DATE-BEG)

        Parameters
        ----------
        date: datetime.datetime, pandas.Timestamp...
            Target date
        level: str
            LEVEL to select (≥L1)

        Return
        ------
        pandas.Series
            File with closest date
        """
        if self.empty or date is None:
            return None
        if type(date) is str:
            date = pd.Timestamp(date)
        df = self[self.LEVEL == level]
        df.set_index("DATE-BEG", inplace=True)
        index = df.index.get_indexer([date], method="nearest")
        df.reset_index(inplace=True)
        return df.iloc[index[0]]
