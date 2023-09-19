import astropy.units as u

from ..instrument_modelling import Spice, Study, Observation


def spice_error(hdu=None, data=None, header=None, verbose=True):
    """
    Return total (measured) signal increase and standard deviation due to noises

    Parameters
    ----------
    hdu: astropy.io.fits.hdu.image.ImageHDU
        SPICE L2 FITS HDU
    data: numpy.ndarray
        SPICE L2 FITS data, assumed to be in W / m2 / sr / nm
    header: astropy.io.fits.header.Header
        SPICE L2 FITS header
    verbose: bool
        If True, displays details

    Return
    ------
    float:
        Average contribution of dark current and background to measured signal
    dict:
        Noise standard deviations for the different components (and total)

    Either hdu, or data and header should be provided.

    Note: see docstring of ``Observation.noise_effects()`` for more details about methods and assumptions.
    """
    if data is None or header is None:
        if hdu is None:
            raise RuntimeError("Either hdu, or data and header should be provided")
        header = hdu.header
        data = hdu.data
    if header["LEVEL"] != "L2":
        raise RuntimeError("Level should be L2")
    data *= u.Unit(header["BUNIT"])
    print(data.unit)
    study = Study()
    study.init_from_header(header)
    if verbose:
        print(f"Getting observation parameters from {header['EXTNAME']}")
        print(study)
    instrument = Spice()
    observation = Observation(instrument, study)
    av_noise_contribution, sigma = observation.noise_effects_from_l2(
        data, study.av_wavelength
    )
    return av_noise_contribution, sigma
