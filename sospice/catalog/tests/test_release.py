import pytest

from ..release import Release, get_latest_release_tag


@pytest.fixture
def release2():
    return Release("2.0")


class TestRelease:
    def test_init(self, release2):
        assert release2.tag == "2.0"
        assert release2.base_url.startswith(
            "https://spice.osups.universite-paris-saclay.fr"
        )
        assert release2.url.endswith("2.0/")
        assert release2.catalog_url.endswith("/catalog.csv")
        assert release2.exists  # online access
        assert not release2.is_latest  # online access

    def test_latest(self):  # online access
        release = Release()
        assert release.tag != "2.0"
        assert release.base_url.startswith(
            "https://spice.osups.universite-paris-saclay.fr"
        )
        assert release.catalog_url.endswith("/catalog.csv")
        assert release.exists
        assert release.is_latest

    def test_get_latest(self):
        assert get_latest_release_tag() != "2.0"
