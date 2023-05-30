import numpy as np
from ..rss import rss


def test_rss():
    a = np.array([3, 4])
    rss_a = rss(a)
    assert rss_a.shape == ()
    assert rss_a == 5.0
    a = np.array([[3, 4, 5], [5, 4, 3]])
    rss_a = rss(a)
    assert rss_a.shape == ()
    assert rss_a == 10.0
    rss_a = rss(a, axis=0)
    assert rss_a.shape == (3,)
    assert rss_a[0] == np.sqrt(34)
    assert rss_a[1] == np.sqrt(32)
    assert rss_a[2] == np.sqrt(34)
    rss_a = rss(a, axis=1)
    assert rss_a.shape == (2,)
    assert rss_a[0] == np.sqrt(50)
    assert rss_a[1] == np.sqrt(50)
