import pytest

from ..file import File
from .test_catalog import catalog_df  # noqa: F401


@pytest.fixture
def file_metadata(catalog_df):  # noqa: F811
    metadata = catalog_df.iloc[0]
    return File(metadata)


class TestFile:
    def test_init(self):
        pass

    def test_relative_path(self, file_metadata):
        path = file_metadata.relative_path
        assert path.as_posix() == "level2/2023/02/01"
