from numpy.testing import assert_allclose
import matplotlib as mpl

from ..cmap import get_cmap


def test_cmap():
    logt = 4.5
    cmap = get_cmap(logt=logt)
    assert isinstance(cmap, mpl.colors.LinearSegmentedColormap)

    assert cmap.name == "spice_logt_4.5"
    assert cmap.N == 256
    assert_allclose(cmap(0), [0, 0, 0, 1])
    assert_allclose(cmap(cmap.N - 1), [1, 1, 1, 1])
