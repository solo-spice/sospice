import pytest
import numpy as np

import astropy.units as u

from ..sigma_clipping import _get_numpy_function, sigma_clip


@pytest.fixture
def image_1d():
    return np.array([2, 3, 2, 4, 25, 5, 1, 2, 3, 2], dtype=float)


@pytest.fixture
def image_2d(image_1d):
    image_2d = np.ones((10, 10))
    image_2d[3, 4] = 100
    return image_2d


@pytest.fixture
def image_3d(image_2d):
    return np.stack(image_2d, 2 * image_2d, axis=0)


class TestSigmaClip:
    def test_get_numpy_function(self, image_1d):
        assert _get_numpy_function(image_1d, "mean") == np.mean
        image_1d[0] = np.nan
        assert _get_numpy_function(image_1d, "mean") == np.nanmean

    def test_sigma_clip_1d(self, image_1d):
        result = sigma_clip(image_1d, size=3, sigma=2, maxiters=1)
        expected_values = np.array([2, 2, 2, 4, 5, 5, 1, 2, 2, 2], dtype=float)
        expected_mask = np.array([0, 1, 0, 0, 1, 0, 0, 0, 1, 0], dtype=bool)
        assert u.isclose(result.data, expected_values).all()
        assert (result.mask == expected_mask).all()

    def test_sigma_clip_2d(self, image_2d):
        result = sigma_clip(image_2d, size=5, sigma=2, maxiters=1)
        expected_values = np.ones_like(image_2d)
        expected_mask = np.zeros_like(image_2d, dtype=bool)
        expected_mask[3, 4] = True
        assert u.isclose(result.data, expected_values).all()
        assert (result.mask == expected_mask).all()
        result = sigma_clip(image_2d, size=5, sigma=2, maxiters=1, masked=False)
        assert u.isclose(result, expected_values).all()
