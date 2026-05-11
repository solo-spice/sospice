import matplotlib as mpl
import numpy as np
import skimage


def get_cmap(logt: float, logt_range=(4.0, 6.0), saturation=0.5, hue_factor=0.9):
    """
    Return a colormap depending on the line temperature

    Parameters
    ----------
    logt: float
        Base-10 logarithm of temperature in K
    logt_range: tuple
        Range of base-10 logarithm of temperature, in K
    saturation: float
        Main color saturation (0 to 1)
    hue_factor: float
        Factor to apply to main color hue, so that not all the hue axis is used (avoid cycling back to red after purple)

    Return
    ------
    mpl.colors.LinearSegmentedColormap
    """
    main_color = _get_main_color(
        logt=logt,
        logt_range=logt_range,
        saturation=saturation,
        hue_factor=hue_factor,
    )
    _, a, b = skimage.color.rgb2lab(main_color)
    L = np.linspace(0, 100, 256)
    a = np.repeat(a, L.size)
    b = np.repeat(b, L.size)
    colors = np.stack([L, a, b]).T
    rgb = skimage.color.lab2rgb(colors)

    # mix with grayscale (with significant weight only close to boundaries)
    ones = np.ones(3)
    grays = np.linspace(np.zeros(3), ones, num=256)
    alpha = np.linspace(-ones, ones, num=256) ** 4
    rgb = (1 - alpha) * rgb + alpha * grays

    # convert to mpl colormap
    rgb_names = ("red", "green", "blue")
    x = np.linspace(0, 1, len(rgb))
    cdict = {k: list(zip(x, v, v)) for k, v in zip(rgb_names, rgb.T)}
    cmap = mpl.colors.LinearSegmentedColormap(f"spice_logt_{logt:.1f}", cdict)
    return cmap


def _get_main_color(logt: float, *, logt_range, saturation, hue_factor):
    """
    Choose main color, according to temperature

    Parameters
    ----------
    logt: float
        Base-10 logarithm of temperature in K
    logt_range: tuple
        Range of base-10 logarithm of temperature, in K
    saturation: float
        Color saturation (0 to 1)
    hue_factor: float
        Factor to apply to hue, so that not all the hue axis is used (avoid cycling back to red after purple)

    Return
    ------
    numpy.ndarray
        RGB values (between 0 and 1) for main color
    """
    logt_fraction = (logt - logt_range[0]) / (logt_range[1] - logt_range[0])
    logt_fraction = np.clip(logt_fraction, a_min=0, a_max=1)
    lab = skimage.color.lch2lab(
        [50, 100 * saturation, logt_fraction * 2 * np.pi * hue_factor]
    )
    rgb = skimage.color.lab2rgb(lab)
    return rgb
