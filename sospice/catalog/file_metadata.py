from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from astropy.utils.data import download_file
from parfive import Downloader

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

        Note: there is no guarantee that the URL corresponds to an existing location
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
        release: Release
            Release to download file from

        Return
        ------
        str
            File URL
        """
        if release is not None:
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
        release: Release
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
        base_dir: Path
            Base directory to download file to
        base_url: str
            Base URL for file
        release: Release
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
            destination = base_dir / self.metadata.FILE_PATH
            destination.mkdir(parents=True, exist_ok=True)
        else:
            destination = base_dir
        do_download = False
        if downloader is None:
            downloader = Downloader(overwrite=False)
            do_download = True
        downloader.enqueue_file(url, destination, self.metadata.FILENAME)
        if do_download:
            result = downloader.download()
            return result
        return None