from dataclasses import dataclass
import requests


@dataclass
class Release:
    tag: str = None
    base_url: str = "https://spice.osups.universite-paris-saclay.fr/spice-data/"
    _latest_tag: str = None

    def __post_init__(self):
        """
        Initialize object to latest release if no release tag set
        """
        if self.tag is None:
            self.tag = self.latest_tag

    @property
    def url(self):
        """
        Return
        ------
        str
            Release URL
        """
        return f"{self.base_url}release-{self.tag}/"

    @property
    def catalog_url(self):
        """
        Return
        ------
        str
            Catalog URL for release
        """
        return self.url + "catalog.csv"

    @property
    def latest_tag(self):
        """
        Return
        ------
        str
            Tag of latest release
        """
        if self._latest_tag is None:
            url = f"{self.base_url}metadata/latest-release.txt"
            result = requests.get(url)
            if not result.ok:
                raise RuntimeError(
                    "Could not access URL for file with latest release tag"
                )
            self._latest_tag = result.text.split("\n")[0]
        return self._latest_tag

    @property
    def is_latest(self):
        """
        Return
        ------
        bool
            True is object corresponds to latest release
        """
        return self.tag == self.latest_tag

    @property
    def exists(self):
        """
        Return
        ------
        bool
            True if release exists (is accessible online)
        """
        result = requests.get(self.url)
        return result.ok


def get_latest_release_tag():
    """
    Return
    ------
    str
        Latest available release tag
    """
    release = Release()
    return release.latest_tag
