import numpy as np
from scipy.ndimage import generic_filter
from numpy import ma


def _get_numpy_function(image, name):
    """
    Get NaN-aware version of numpy array function if there are any NaNs in image

    Parameters
    ----------
    image: numpy.array
        Image
    name: str
        Numpy function name, in its not NaN-aware version

    Return
    ------
    function
        Numpy function
    """
    if np.isnan(image.data).any():
        name = "nan" + name
    return getattr(np, name)


def sigma_clip(image, size, center_method="median", low=3, high=3, iterations=1):
    """
     Performs sigma-clipping of the input array.

     Parameters
     ----------
    image: numpy.ndarray
        Input image or image cube
    size: int or tuple[int]
        Size of the kernel used to compute the running median (or mean) and standard deviation
    center_method: str
        Method used to estimate the center of the local intensity distribution ("median" (default) or "mean")
    low: float
        Low threshold, in units of the standard deviation of the local intensity distribution
    high: float
        High threshold, in units of the standard deviation of the local intensity distribution
    iterations: int
        Number of iterations to perform

    Returns
    -------
    numpy.ndarray
        Filtered array, with clipped pixels replaced by the estimated value of the center of the
        local intensity distribution (either median or mean).
    """
    output = np.copy(image)
    if type(size) is int:
        size = (size,) * image.ndim
    for iteration in range(iterations):
        center = generic_filter(
            output, _get_numpy_function(output, center_method), size
        )
        stddev = generic_filter(output, _get_numpy_function(output, "std"), size)
        diff = output - center
        output[(diff > high * stddev) | (diff < -low * stddev)] = np.nan
    nan = np.isnan(output)
    output[nan] = center[nan]
    return ma.masked_array(output, mask=nan)
