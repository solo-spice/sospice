from dataclasses import dataclass
import numpy as np
import astropy.units as u

from .spice import Spice
from .study import Study
from ..util import rss


@dataclass
class Observation:
    instrument: Spice()
    study: Study()

    @classmethod
    def observation_from_spice_hdu(cls, hdu, verbose=True):
        """
        Generate an Observation object from a SPICE L2 file HDU
        """
        study = Study()
        study.init_from_header(hdu.header)
        if verbose:
            print(f"Getting observation parameters from {hdu.name}")
            print(study)
        instrument = Spice()
        observation = Observation(instrument, study)
        return observation

    @u.quantity_input
    def av_dark_current(self, wvl: u.Angstrom = None):
        """
        Average dark current in DN per macro-pixel over exposure time

        Parameters
        ----------
        wvl: Quantity
            Wavelength (or array of wavelengths)

        Return
        ------
        float
            Average dark current

        TODO:
        * Should depend on detector temperature.
        * Actually non-Poissonian (need to look at real darks).
        * Would depend on position (dark or hot pixels) in L1
        """
        if wvl is None:
            wvl = self.study.av_wavelength
        return (
            self.instrument.dark_current(wvl)
            * self.study.exp_time  # noqa: W503
            * self.study.bin_x  # noqa: W503
            * self.study.bin_y  # noqa: W503
        ).to(u.ct / u.pix)

    @u.quantity_input
    def av_background(self, wvl: u.Angstrom = None):
        """
        Average background signal in DN per macro-pixel over exposure time

        Parameters
        ----------
        wvl: Quantity
            Wavelength (or array of wavelengths)

        Return
        ------
        float
            Average background
        """
        if wvl is None:
            wvl = self.study.av_wavelength
        return (
            self.instrument.background
            * self.instrument.quantum_efficiency(wvl)  # noqa: W503
            * self.study.exp_time  # noqa: W503
            * self.study.bin_x  # noqa: W503
            * self.study.bin_y  # noqa: W503
            * self.instrument.gain(wvl)  # noqa: W503
        ).to(u.ct / u.pix)

    @property
    def read_noise_width(self):
        """
        Read noise distribution width in DN per macro-pixel
        TODO make sure that this is a standard deviation and not a FWHM
        """
        return self.instrument.read_noise * np.sqrt(self.study.bin_x * self.study.bin_y)

    @u.quantity_input
    def noise_effects(self, signal_mean: u.ct / u.pix, wvl: u.Angstrom = None):
        """
        Return total (measured) signal increase and standard deviation due to noises

        Parameters
        ----------
        signal_mean: Quantity
            Measured signal mean, in DN/pix, excluding expected signal increase
            due to average dark current and background (so this is not exactly
            the measured signal).
        wvl: Quantity
            Wavelength (or array of wavelengths)

        Return
        ------
        float:
            Average contribution of dark current and background to measured signal
        dict:
            Noise standard deviations for the different components (and total
            uncertainty resulting from them). The components include noise from
            dark current, noise from the background signal, read noise, shot noise
            from the signal.

        Negative values of the signal are considered to be 0 for the purpose of
        computing the noise on the signal. However, the total uncertainty is
        then set to |signal_mean| + RSS (other noises), to ensure that the
        error bars are still compatible with expected fitted functions.
        We suggest users to replace large negative values of the signal
        (e.g. < -3 * RSS(other noises)) by NaNs.

        Note: the dark and read noise are currently multiplied by √2 to take the
        effect of dark map (currently: a single dark frame) subtraction, this is
        **not** consistent with the MPS spice_error IDL routine.
        """
        if wvl is None:
            wvl = self.study.av_wavelength
        av_dark_current = self.av_dark_current()
        av_background = self.av_background()
        av_noise_contribution = av_dark_current + av_background
        sigma = dict()
        gain = self.instrument.gain(wvl)
        sigma["Dark"] = np.sqrt(av_dark_current.value) * np.sqrt(2) * u.ct / u.pix
        sigma["Background"] = np.sqrt(av_background * gain).value * u.ct / u.pix
        sigma["Read"] = self.read_noise_width * np.sqrt(2)
        signal_mean_nonneg = np.maximum(signal_mean, 0)
        sigma["Signal"] = np.sqrt(signal_mean_nonneg * gain).value * u.ct / u.pix
        sigma["Signal"] *= self.instrument.noise_factor(wvl)
        constant_noises = rss(
            np.array(
                [sigma["Dark"].value, sigma["Background"].value, sigma["Read"].value]
            )
        )
        sigma["Total"] = (
            rss(
                np.array(
                    [
                        constant_noises * np.ones_like(signal_mean.value),
                        sigma["Signal"].value,
                    ]
                ),
                axis=0,
            )  # noqa: W503
            * sigma["Signal"].unit  # noqa: W503
        )
        where_neg = signal_mean < 0
        sigma["Total"][where_neg] = (
            -signal_mean[where_neg] + constant_noises * signal_mean.unit
        )
        return av_noise_contribution, sigma

    @u.quantity_input
    def noise_effects_from_l2(
        self, data: u.W / u.m**2 / u.sr / u.nm, wvl: u.Angstrom
    ):
        """
        Return total (measured) signal increase and standard deviation due to noises

        Parameters
        ----------
        data: Quantity
            L2 data, in W / m2 / sr / nm
        wvl: Quantity
            Wavelength
        Return
        ------
        float:
            Average contribution of noise to measured signal
        dict:
            Noise standard deviations for the different components (and total)
        """
        data_dn = data * self.study.radcal / u.pix
        av_noise_contribution, sigma = self.noise_effects(data_dn, wvl)
        av_noise_contribution /= self.study.radcal / u.pix
        for component in sigma:
            sigma[component] /= self.study.radcal / u.pix
        return av_noise_contribution, sigma
