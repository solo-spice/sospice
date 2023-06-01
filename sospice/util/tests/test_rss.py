import numpy as np
from ..rss import rss


def test_rss():
    a = np.array([3, 4])
    assert np.isclose(rss(a), 5.0)
    a = np.array([[3, 4, 5], [5, 4, 3]])
    assert np.isclose(rss(a), 10.0)
    assert np.allclose(rss(a, axis=0), np.sqrt([34, 32, 34]))
    assert np.allclose(rss(a, axis=1), np.sqrt([50, 50]))
