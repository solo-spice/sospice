import numpy as np
from scipy.ndimage import generic_filter
from numpy import ma


def _stddev_loc(image, size):
    if type(size) is int:
        size = (size,) * image.ndim
    mean2 = _blur(image, size) ** 2
    vari = _blur(image ** 2, size)
    vari -= mean2
    vari[vari <= 0] = 1e-20
    return np.sqrt(vari)


def _blur(image, size, output=None):

    if type(size) is int:
        size = (size,)*image.ndim

    if output is None:
        output = np.empty_like(image)

    if image.ndim == 2:
        generic_filter(image, np.nanmean, mode='reflect', output=output, size=size)
    elif image.ndim == 3:
        for i in range(image.shape[0]):
            if size[1] > 1 or size[2] > 1:
                generic_filter(image[i], np.nanmean, mode='reflect', output=output[i], size=size[2:0:-1])
            else:
                output[i] = np.copy(image[i])
        for i in range(image.shape[2]):
            if size[0] > 1:
                dum = np.empty_like(output[:, :, i])
                generic_filter(np.copy(output[:, :, i]), np.nanmean, mode='reflect', output=dum, size=(1, size[0]))
                output[:, :, i] = dum
    else:
        raise ValueError('Unsupported number of dimensions')

    return output


def _get_center_function(image, center):
    if center not in ['mean', 'median']:
        raise ValueError('Center must be mean of median')
    if np.sum(image.mask) > 0:
        if center == 'mean':
            return np.nanmean
        elif center == 'median':
            return np.nanmedian
    else:
        if center == 'mean':
            return np.mean
        elif center == 'median':
            return np.median


def sigma_clip(image, size, center_method='median', low=3, high=3, iterations=1):
    """
    Performs 2D or 3D sigma-clipping of the input array.

    Parameters
    ----------
    image: ndarry-like. input image or image cube
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

    output = ma.masked_array(np.copy(image), mask=np.isnan(image))

    if type(size) is int:
        size = (size,) * image.ndim

    for iteration in range(iterations):
        center = generic_filter(output, _get_center_function(output, center_method), size)
        stddev = _stddev_loc(output, size)
        diff = output - center
        output.mask[(diff > high * stddev) | (diff < -low * stddev)] = True

    output.data[output.mask] = center[output.mask]

    return output
