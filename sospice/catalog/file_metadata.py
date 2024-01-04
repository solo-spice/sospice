from dataclasses import dataclass
from pathlib import Path
import warnings

import numpy as np
import pandas as pd
import portion

from parfive import Downloader
from astropy.utils.data import download_file
import astropy.units as u
from astropy.wcs import WCS, FITSFixedWarning
from astropy.coordinates import SkyCoord
from sunpy.coordinates import HeliographicStonyhurst, Helioprojective

from sunpy.coordinates.utils import GreatArc  # check whether still needed

from .release import Release

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


@dataclass
class FileMetadata:
    """
    A SPICE file entry in the SPICE catalog

    Parameters
    ----------
    metadata: pandas.Series
        File metadata
    skip_validation: bool
        Do no validate data
    """

    metadata: pd.Series = None
    skip_validation: bool = False

    def __post_init__(self):
        """
        Update object
        """
        if not self.skip_validation:
            self.validate()

    def validate(self):
        """
        Check file metadata
        """
        assert self.metadata is not None
        if type(self.metadata) is pd.DataFrame:
            assert len(self.metadata) == 1
            self.metadata = self.metadata.iloc[0]
        assert not self.metadata.empty
        assert required_columns.issubset(self.metadata.keys())

    def _get_file_url_from_base_url(self, base_url):
        """
        Get URL for a file located under some base URL

        Parameters
        ----------
        base_url: str
            Base URL

        Return
        ------
        str
            File URL

        Notes:

        * There is no guarantee that the URL corresponds to an existing location
        * The base URL can be a path on disk, but paths are built using "/"
        and this might not work on all operating systems.
        """
        if not base_url.endswith("/"):
            base_url += "/"
        return base_url + self.metadata.FILE_PATH + "/" + self.metadata.FILENAME

    def get_file_url(self, base_url=None, release=None):
        """
        Get file URL, from a release, from some other online file tree, or from SOAR if no parameter has been provided

        Parameters
        ----------
        base_url: str
            Base URL for file
        release: Release or str
            Release to download file from. This can be a Release object, or a string for the release tag.

        Return
        ------
        str
            File URL
        """
        if release is not None:
            if type(release) is str:
                release = Release(release)
            url = self._get_file_url_from_base_url(release.url)
        elif base_url is not None:
            url = self._get_file_url_from_base_url(base_url)
        else:
            url = "http://soar.esac.esa.int/soar-sl-tap/data"
            url += "?retrieval_type=ALL_PRODUCTS"
            url += "&QUERY=SELECT+filepath,filename+FROM+soar.v_sc_repository_file"
            url += f"+WHERE+filename='{self.metadata.FILENAME}'"
        return url

    def cache_file(self, base_url=None, release=None, update=False):
        """
        Put file in local disk cache, from a release, from some other online
        file tree, or from SOAR if no parameter has been provided

        Parameters
        ----------
        base_url: str
            Base URL for file
        release: Release or str
            Release to download file from
        update: bool
            Whether to update the cached file

        Return
        ------
        Path
            Cache file location

        The cache is managed by `astropy.utils.data`.
        """
        url = self.get_file_url(base_url=base_url, release=release)
        cache = "update" if update else True
        filename = download_file(url, cache=cache)
        return Path(filename)

    def download_file(
        self, base_dir, base_url=None, release=None, keep_tree=True, downloader=None
    ):
        """
        Download file, from a release, from some other online file tree,
        or from SOAR if no parameter has been provided

        Parameters
        ----------
        base_dir: Path or str
            Base directory to download file to
        base_url: str
            Base URL for file
        release: Release or str
            Release to download file from
        keep_tree: bool
            Keep tree directory structure (by level and date)
        downloader: parfive.Downloader
            If provided, enqueue file for download instead of downloading it.
            To download enqueued files, run `downloader.download()`

        Return
        ------
        parfive.Result
            Download result (or None if file has only been enqueued)
        """
        url = self.get_file_url(base_url=base_url, release=release)
        if keep_tree:
            destination = Path(base_dir) / self.metadata.FILE_PATH
            destination.mkdir(parents=True, exist_ok=True)
        else:
            destination = Path(base_dir)
        do_download = False
        if downloader is None:
            downloader = Downloader(overwrite=False)
            do_download = True
        downloader.enqueue_file(url, destination, self.metadata.FILENAME)
        if do_download:
            result = downloader.download()
            return result
        return None

    def get_wavelengths(self):
        """
        Get wavelength ranges for the observation

        Return
        ------
        portion.Interval
            Wavelength ranges

        Wavelength ranges are determined at the center of the slit,
        from the WAVECOV header (present from data release 3.0). If it does
        not exist, an empty interval is returned.

        The return value is a Union of wavelength intervals, represented as a ``portion`` object.

        Examples
        --------
        The presence of a given wavelength in these intervals can easily be checked, e.g.:
        >>> import astropy.units as u
        >>> from sospice import Catalog, FileMetadata
        >>> catalog = Catalog(release_tag='2.0')
        >>> file_metadata = FileMetadata(cat.iloc[-1])
        >>> 770 * u.angstrom in file_metadata.get_wavelength_ranges()
        True
        """
        if type(self.metadata.WAVECOV) != str or "-" not in self.metadata.WAVECOV:
            return portion.empty()
        ranges = self.metadata.WAVECOV.split(", ")
        ranges = [r.split("-") for r in ranges]
        ranges = [[u.Quantity(r, "nm") for r in rr] for rr in ranges]
        intervals = portion.empty()
        for r in ranges:
            intervals |= portion.closed(*r)
        return intervals

    def get_pc_2d(self):
        """
        Get 2D PC matrix for observation, for x and y axes

        Return
        ------
        dict
            2D PC matrix element values

        Note: a 4D PC matrix (with wavelength and time axes) is included
        in the SPICE FITS files, but the full information cannot be retrieved
        from the catalog.
        """
        cdelt_ratio = self.metadata.CDELT2 / self.metadata.CDELT1
        crota = self.metadata.CROTA * u.deg
        pc = dict()
        pc["PC1_1"] = np.cos(crota).value
        pc["PC1_2"] = -np.sin(crota).value * cdelt_ratio
        pc["PC2_1"] = np.sin(crota).value / cdelt_ratio
        pc["PC2_2"] = np.cos(crota).value
        return pc

    def get_crpix_2d(self):
        """
        Get 2D CRPIX values, for x and y axes (assuming FITS pixel indices convention)

        Return
        ------
        dict:
            CRPIX values
        """
        crpix = dict()
        crpix["CRPIX1"] = self.metadata.NAXIS1 / 2 + 0.5
        crpix["CRPIX2"] = self.metadata.NAXIS2 / 2 + 0.5
        return crpix

    def get_wcs_2d(self):
        """
        Get World Coordinates System object for the observation, for x and y axes

        Return
        ------
        astropy.wcs.WCS
            WCS object for observation

        Note: more dimensions can be retrieved from the SPICE FITS files,
        but not from the catalog.
        """
        useful_columns = [
            "CDELT1",
            "CDELT2",
            "CRVAL1",
            "CRVAL2",
            "CTYPE1",
            "CTYPE2",
            "CUNIT1",
            "CUNIT2",
            "NAXIS1",
            "NAXIS2",
        ]
        header_dict = self.metadata[useful_columns].to_dict()
        header_dict.update(self.get_pc_2d())
        header_dict.update(self.get_crpix_2d())
        with warnings.catch_warnings():
            # Ignore a warning on CROTA
            # There should be an additional condition
            # message="keyword looks very much like CROTAn but isn't.",
            # but this does not work
            warnings.filterwarnings("ignore", category=FITSFixedWarning)
            wcs = WCS(header_dict)
        return wcs

    def get_observer(self):
        """
        Get observer position and time for the observation

        Return
        ------
        atropy.coordinates.SkyCoord
            Observer coordinates (defined in Stonyhurst frame)
        """
        # estimate DATE-AVG from available metadata
        date_avg = self.metadata["DATE-BEG"] + pd.Timedelta(
            self.metadata["TELAPSE"] / 2, "seconds"
        )
        observer = HeliographicStonyhurst(
            self.metadata.HGLN_OBS * u.deg,
            self.metadata.HGLT_OBS * u.deg,
            self.metadata.DSUN_AU * u.au,
            obstime=date_avg,
        )
        return observer

    def get_fov(self, points=None, method=None):
        """
        Get the FOV coordinates (bottom left and top right vertices of rectangle
        in helioprojective coordinates) for an observation

        Parameters
        ----------
        points: int
            Number of points on each FOV boundary edge
        method: str
            Interpolation method for each edge (if points > 2).
            'interp': interpolate the edge segment in helioprojective coordinates;
            'arc': consider the edge as a great arc.
        """
        if points is None:
            points = 10
        if method is None:
            method = "interp"
        wcs = self.get_wcs_2d()
        # Take pixel size into account to get coordinates at the external edges of vertex pixels
        min1 = -0.5
        min2 = -0.5
        max1 = self.metadata.NAXIS1 - 0.5
        max2 = self.metadata.NAXIS2 - 0.5
        vertex_pixels = [
            [min1, min2],
            [max1, min2],
            [max1, max2],
            [min1, max2],
            [min1, min2],  # close to first vertex
        ]
        if (points > 2) and (method == "interp"):
            vertex_all_pixels = list()
            for i in range(4):
                vertex1 = vertex_pixels[i]
                vertex2 = vertex_pixels[i + 1]
                coords = [
                    np.linspace(vertex1[j], vertex2[j], num=points) for j in [0, 1]
                ]
                for k in range(points):
                    vertex_all_pixels.append([coords[j][k] for j in [0, 1]])
            vertex_pixels = vertex_all_pixels
        vertices_world = np.array(wcs.pixel_to_world_values(vertex_pixels))
        observer = self.get_observer()
        frame = Helioprojective(observer=observer, obstime=observer.obstime)
        fov_coords = SkyCoord(vertices_world * u.deg, frame=frame)
        if (points > 2) and (method == "arc"):
            fov_all_coords = list()
            for i in range(4):
                arc = GreatArc(fov_coords[i], fov_coords[i + 1], points=points)
                # This is at the Sun distance of SO!
                # and still in helioprojective coordinates (not clear that this is on the correct sphere)
                fov_all_coords.append(arc.coordinates())
            fov_coords = SkyCoord(fov_all_coords)
        return fov_coords

    def plot_fov(self, ax, **kwargs):
        """
        Plot SPICE FOV on a background map

        Parameters
        ----------
        ax: matplotlib.axes.Axes
            Axes (with relevant projection)
        kwargs: dict
            Keyword arguments.
            'points' and 'method' are passed to FileMetadata.get_fov(),
            other arguments are passed to ax.plot_coords()
        """
        fov_args = dict()
        for k in ["points", "method"]:
            fov_args[k] = kwargs.pop(k, None)
        fov_coords = self.get_fov(**fov_args)
        ax.plot_coord(fov_coords, **kwargs)
