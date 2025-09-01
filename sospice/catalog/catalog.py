from dataclasses import dataclass
from pathlib import Path
from itertools import cycle

import matplotlib.colors as mcolors
import pandas as pd
import numpy as np

from astropy.utils.data import download_file
import astropy.units as u

from .release import Release
from .file_metadata import FileMetadata, required_columns


@dataclass
class Catalog(pd.DataFrame):
    """
    A SPICE catalog, initialized (in that order) either from a filename, a release tag, or a pandas.DataFrame.

    Parameters
    ----------
    filename: str
        A file name (or URL) for the catalog
    release_tag: str
        A release tag. The catalog is fetched online and downloaded to the astropy cache.
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
        Find files with DATE-BEG in some date range.

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
    
    def find_files_by_wavelength(self, wavelength):
        """
        Find files by wavelength included in observed wavelength ranges.

        Parameters
        ----------
        wavelength:
            Wavelength that must be included in the file wavelength's range
            must be defined in a length astropy unit only

        Return
        ------
        Catalog
            Matching files
        """
        if self.empty:
            return self
        df = self
        if wavelength is not None:

            # Check the unit is an length astropy unit
            if isinstance(wavelength, u.Quantity) and wavelength.unit.is_equivalent(u.nm):

                    if wavelength.unit != u.nm:
                        wavelength.to(u.nm)

                    contains_wl = df.apply(lambda row: wavelength in FileMetadata(row).get_wavelengths(), axis=1)
                    df = df[contains_wl]
            else:  
                raise TypeError("Input must be a length astropy Quantity")

        return Catalog(data_frame=df)

    def find_files(
        self, query=None, date_min=None, date_max=None, closest_to_date=None, wavelength=None, **kwargs
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
        if wavelength is not None:
            df = df.find_files_by_wavelength(wavelength)
        if closest_to_date is not None:
            df = (
                df.find_file_closest_to_date(closest_to_date, level=kwargs["LEVEL"])
                .to_frame()
                .T
            )
        
        return df

    def mid_time(self, method=None):
        """
        Find "middle time" for observations in catalog

        Parameters
        ----------
        method: str
            Method for determining middle time. Can be

            * "midrange" (default): middle of time range, from beginning of first observation to end of last observation
            * "mean": mean of observation times (not weighted by observations durations)

        """
        if method is None or method == "midrange":
            begin_min = self["DATE-BEG"].min()
            begin_max = self["DATE-BEG"].max()
            last_telapse = self[self["DATE-BEG"] == begin_max].TELAPSE.max()
            end_max = begin_max + pd.Timedelta(seconds=last_telapse)
            return begin_min + (end_max - begin_min) / 2
        elif method == "mean":
            begin_mean = self["DATE-BEG"].mean()
            telapse_mean = pd.Timedelta(seconds=self.TELAPSE.mean())
            return begin_mean + telapse_mean
        elif method == "barycenter":
            mid_observation = self["DATE-BEG"] + self.apply(
                lambda row: pd.Timedelta(seconds=row.TELAPSE / 2), axis=1
            )
            weight = self.TELAPSE
            t0 = mid_observation.iloc[0]
            return t0 + ((mid_observation - t0) * weight).sum() / weight.sum()
        else:
            raise RuntimeError("Invalid method")

    @classmethod
    def _format_time_range(cls, row, timespec="minutes"):
        """
        Format time range for observation

        Parameters
        ----------
        row: pd.Series
            Catalog row
        timespec: str
            Time terms specification for pandas.Timestamp.isoformat()

        Return
        ------
        str
            Formatted time range

        The end of the time range is known from the single observation in `row`
        thanks to an additional element `last_DATE-BEG' in the Series.
        All dates are DATE-BEG, we don't compute a DATE-END.
        """
        t = [row["DATE-BEG"]]
        is_range = ("last_DATE-BEG" in row.index) and (row["last_DATE-BEG"] != t[0])
        if is_range:
            t.append(row["last_DATE-BEG"])
        t_str = [tt.isoformat(timespec=timespec) for tt in t]
        if is_range and t_str[0][:10] == t_str[1][:10]:
            t_str[1] = t_str[1][10:]
        return " - ".join(t_str)

    def plot_fov(self, ax, **kwargs):
        """
        Plot SPICE FOVs on a background map

        Parameters
        ----------
        ax: matplotlib.axes.Axes
            Axes (with relevant projection)
        color: str or list
            Color(s) cycle for drawing the FOVs
        kwargs: dict
            Keyword arguments, passed to FileMetadata.plot_fov()
        """
        time_range_length = self["DATE-BEG"].max() - self["DATE-BEG"].min()
        if time_range_length > pd.Timedelta(days=60):
            print(
                f"Time range length is {time_range_length}, this is long, and probably not what you want; aborting"
            )
            return
        merge_by_spiobsid = True
        if merge_by_spiobsid:
            groups = self.groupby("SPIOBSID")
            fovs = groups.first()
            fovs_last = groups.last()
            fovs["last_DATE-BEG"] = fovs_last["DATE-BEG"]
            fovs.reset_index(inplace=True)
        else:
            fovs = Catalog(data_frame=self[list(required_columns)])
        # label at the position of the plot
        fovs["fov_text"] = fovs.apply(Catalog._format_time_range, axis=1)
        # label at the level of the plot (will be de-duplicated afterwards)
        fovs["fov_label"] = fovs.apply(
            lambda row: f"{row.STUDY} ({row.MISOSTUD})", axis=1
        )
        # color(s)
        color = kwargs.pop("color", None)
        studies = sorted(list(self.STUDY.unique()))
        colors = (
            mcolors.TABLEAU_COLORS
            if color is None
            else color
            if type(color) is list
            else [color]
        )
        study_color = dict(zip(studies, cycle(colors)))
        fovs["fov_color"] = fovs.apply(lambda row: study_color[row.STUDY], axis=1)
        fovs.apply(
            lambda row: FileMetadata(row).plot_fov(ax, **kwargs),
            axis=1,
        )
        if merge_by_spiobsid:
            # also plot last FOV, with dashes
            fovs_last.reset_index(inplace=True)
            fovs_last["fov_color"] = fovs.fov_color
            fovs_last["fov_linestyle"] = ":"
            fovs_last = fovs_last[fovs_last.RASTERNO != 0]
            fovs_last.apply(
                lambda row: FileMetadata(row).plot_fov(ax, **kwargs),
                axis=1,
            )
        # De-duplicate labels for legend (an alternative would be
        # to provide labels only to the first instance of each study)
        handles, labels = ax.get_legend_handles_labels()
        unique_indices = [labels.index(x) for x in sorted(set(labels))]
        handles = list(np.array(handles)[unique_indices])
        ax.legend(handles=handles)
