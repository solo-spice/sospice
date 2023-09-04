from dataclasses import dataclass

import pandas as pd
from pathlib import Path
from astropy.utils.data import download_file

from .release import Release
from .file_metadata import required_columns


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
    data_frame: pd.DataFrame = None
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
        cache = "update" if self.update_cache else True
        self.filename = download_file(release.catalog_url, cache=cache)
        self.release_tag = None

    def _validate_data_frame(self):
        """
        Check that the data_frame argument can be considered a valid SPICE catalog (or raise an exception)
        """
        assert self.data_frame is not None
        if self.data_frame.empty:
            return True  # an empty data frame is valid
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

    @classmethod
    def build_query_from_keywords(cls, **kwargs):
        """
        Build a query from the provided parameters: exact keyword matches

        Parameters
        ----------
        kwargs: dict
            Parameters and their values

        Return
        ------
        str
            Query string for `pandas.DataFrame.query()`

        Notes:

        * does not work for dates
        * keywords are converted to upper case (FITS keywords)
        * ignores keywords with value None
        """
        queries = list()
        for key in kwargs:
            value = kwargs[key]
            if value is None:
                continue
            if isinstance(value, str):
                query = f'{key.upper()} == "{kwargs[key]}"'
            else:
                query = f"{key.upper()} == {kwargs[key]}"
            queries.append(query)
        return " and ".join(queries)

    def find_files_by_keywords(self, **kwargs):
        """
        Find files according to criteria on metadata: exact keyword matches

        Parameters
        ----------
        kwargs: dict
            Parameters and their values

        Return
        ------
        Catalog
            Matching files
        """
        if self.empty or not kwargs:
            return self
        query = Catalog.build_query_from_keywords(**kwargs)
        if query != "":
            df = self.query(query)
            return Catalog(data_frame=df)
        else:
            return self

    def find_files_by_date_range(self, date_min=None, date_max=None):
        """
        Find files in some date range.

        Parameters
        ----------
        date_min:
            Minimum date of a date range
        date_max:
            Maximum date of a date range

        Return
        ------
        Catalog
            Matching files
        """
        if self.empty:
            return self
        df = self
        if date_min is not None:
            if type(date_min) is str:
                date_min = pd.Timestamp(date_min)
            df = df[df["DATE-BEG"] >= date_min]
        if date_max is not None:
            if type(date_max) is str:
                date_max = pd.Timestamp(date_max)
            df = df[df["DATE-BEG"] <= date_max]
        return Catalog(data_frame=df)

    def find_file_closest_to_date(self, date, level="L2"):
        """
        Find file closest to some given date

        Parameters
        ----------
        date: datetime.datetime, pandas.Timestamp...
            Date (compared to DATE-BEG)
        level: str
            Data level

        Return
        ------
        pandas.Series
            Matching file
        """
        if date is None:
            return pd.Series()
        if type(date) is str:
            date = pd.Timestamp(date)
        df = self[self.LEVEL == level]
        df.set_index("DATE-BEG", inplace=True)
        index = df.index.get_indexer([date], method="nearest")
        df.reset_index(inplace=True)
        return df.iloc[index[0]]

    def find_files(
        self, query=None, date_min=None, date_max=None, closest_to_date=None, **kwargs
    ):
        """
        Find files according to different criteria on metadata.

        Parameters
        ----------
        query: str
            Generic pandas.DataFrame.query() string
        date_min:
            Minimum date of a date range
        date_max:
            Maximum date of a date range
        closest_to_date: datetime.datetime, pandas.Timestamp...
            Find the file closest to a date.
        kwargs: dict
            Other parameters and their values

        Return
        ------
        pandas.DataFrame
            Matching files

        Notes:

        * Filtering is done by keyword exact match (LEVEL, SOOPNAME, MISOSTDU...),
          then using the generic query string, then by date range, then by closest date.
        * Keywords are converted to upper case (FITS keywords), so they can be passed as lowercase arguments
        * Selects LEVEL="L2" by default; if you want all levels, please specify LEVEL=None
        * Date arguments are compared to DATE-BEG.
        """
        if self.empty:
            return self
        if "LEVEL" not in [k.upper() for k in kwargs.keys()]:
            kwargs["LEVEL"] = "L2"
        df = self.find_files_by_keywords(**kwargs)
        if query is not None:
            df = Catalog(data_frame=df.query(query))
        df = df.find_files_by_date_range(date_min, date_max)
        if closest_to_date is not None:
            df = (
                df.find_file_closest_to_date(closest_to_date, level=kwargs["LEVEL"])
                .to_frame()
                .T
            )
        return df
