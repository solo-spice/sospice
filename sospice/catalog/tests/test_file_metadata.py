import pytest
from pathlib import Path

import pandas as pd
from parfive import Downloader
import shutil

import astropy.units as u

from ..file_metadata import FileMetadata
from .test_catalog import catalog2, catalog3  # noqa: F401
from .test_release import release2  # noqa: F401


@pytest.fixture
def filename():  # noqa: F811
    return "solo_L2_spice-n-exp_20220305T072522_V01_100663707-014.fits"


@pytest.fixture
def filename3():  # noqa: F811
    return "solo_L2_spice-n-exp_20220305T072522_V02_100663707-014.fits"


@pytest.fixture
def file_metadata(catalog2, filename):  # noqa: F811
    metadata = catalog2[catalog2.FILENAME == filename]
    return FileMetadata(metadata)


@pytest.fixture
def file_metadata3(catalog3, filename3):  # noqa: F811
    metadata = catalog3[catalog3.FILENAME == filename3]
    return FileMetadata(metadata)


class TestFileMetadata:
    def test_get_file_url(self, file_metadata, release2, filename):  # noqa: F811
        expected = "https://foobar/level2/2022/03/05/" + filename
        assert file_metadata.get_file_url(base_url="https://foobar/") == expected
        assert file_metadata.get_file_url(base_url="https://foobar") == expected
        expected = (
            "https://spice.osups.universite-paris-saclay.fr/spice-data/release-2.0/level2/2022/03/05/"
            + filename  # noqa: W503
        )
        assert file_metadata.get_file_url(release=release2) == expected
        assert file_metadata.get_file_url(release="2.0") == expected
        expected = "http://soar.esac.esa.int/soar-sl-tap/data?retrieval_type=ALL_PRODUCTS&QUERY="
        expected += f"SELECT+filepath,filename+FROM+soar.v_sc_repository_file+WHERE+filename='{filename}'"
        assert file_metadata.get_file_url() == expected

    def test_cache_file(self, file_metadata, release2):  # noqa: F811
        file_path = file_metadata.cache_file(release=release2)
        assert file_path.exists()
        now = pd.Timestamp("now", tz="UTC")
        file_path = file_metadata.cache_file(release=release2, update=True)
        assert file_path.exists()
        mtime = pd.Timestamp(file_path.stat().st_mtime, unit="s", tz="UTC")
        assert pd.Timestamp(mtime) >= now

    def test_download_file(self, file_metadata, release2, filename):  # noqa: F811
        base_dir = Path("./local/test_download_file")
        if base_dir.exists():
            shutil.rmtree(base_dir)
        result = file_metadata.download_file(
            base_dir, release=release2, keep_tree=False
        )
        assert len(result) == 1
        assert result[0] == (base_dir / filename).as_posix()
        result = file_metadata.download_file(base_dir, release=release2)
        expected = (base_dir / file_metadata.metadata.FILE_PATH / filename).as_posix()
        assert len(result) == 1
        assert result[0] == expected
        downloader = Downloader(overwrite=False)
        result = file_metadata.download_file(  # noqa: F841
            base_dir, release=release2, downloader=downloader
        )
        assert result is None
        assert downloader.queued_downloads == 1

    def test_get_wavelengths(self, file_metadata, file_metadata3):
        wavelengths = file_metadata.get_wavelengths()
        assert wavelengths.empty
        wavelengths = file_metadata3.get_wavelengths()
        assert 770 * u.angstrom in wavelengths
