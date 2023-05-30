import numpy as np


def rss(a, axis=None):
    """
    Root sum square of array elements

    Parameters
    ----------
    a: numpy.array
        Input values
    axis: None or int or tuple of ints
        Axis or axes along which the root-sum-square is performed.
    Return
    ------
    float
        Root sum square of input values over a given axis
    """
    return np.linalg.norm(a, axis=axis)
