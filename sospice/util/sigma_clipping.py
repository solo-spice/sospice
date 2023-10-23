import numpy as np
from scipy.ndimage import generic_filter
from numpy import ma


def _get_numpy_function(image, name):
    if np.isnan(image.data).any():
        name = 'nan' + name
    return getattr(np, name)


def sigma_clip(image, size, center_method='median', low=3, high=3, iterations=1):
    """
     Performs 2D or 3D sigma-clipping of the input array.

     Parameters
     ----------
     image: ndarray-like. input image or image cube
     size: size of the square kernel used to compute the running median (or mean) and standard deviation
     center_method: either 'median' (default) or 'mean'. The method used to estimate the center of the local intensity
     distribution.
     low: low threshold, in units of the standard deviation of the local intensity distribution
     high: high threshold, in units of the standard deviation of the local intensity distribution
     iterations: number of iterations to perform

     Returns
     -------
     Filtered array, with clipped pixels replaced by the estimated value of the center of the local intensity
     distribution (either median or mean).
     """
    output = np.copy(image)

    if type(size) is int:
        size = (size,) * image.ndim

    for iteration in range(iterations):
        center = generic_filter(output, _get_numpy_function(output, center_method), size)
        stddev = generic_filter(output, _get_numpy_function(output, 'std'), size)
        diff = output - center
        output[(diff > high * stddev) | (diff < -low * stddev)] = np.nan

    nan = np.isnan(output)
    output[nan] = center[nan]

    return ma.masked_array(output, mask=nan)
