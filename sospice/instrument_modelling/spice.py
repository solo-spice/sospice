from dataclasses import dataclass
from pathlib import Path
import numpy as np
from scipy.io import readsav
import astropy.units as u


@dataclass
class Spice:
    # These values (Huang et al. 2023, doi:10.1051/0004-6361/202345988)
    # are supposed to be the latest values presented by RAL.
    # `astropy.units.ct` (counts) is used for DNs
    read_noise = 6.9 * u.ct / u.pix
    background = 0.0 * u.ph / u.s / u.pix  # 1.0 in SPICE-RAL-RP-0002
    pix_x = 1.0 * u.arcsec / u.pix  # not used
    pix_y = 1.0 * u.arcsec / u.pix  # not used except for PSF
    pix_w = 0.0095 * u.nm / u.pix  # not used except for PSF
    aeff_data = None  # Will be read from file when needed

    @u.quantity_input
    def effective_area(self, wvl: u.nm):
        """
        Get the SPICE effective area for some wavelength

        Parameters
        ----------
        wvl: Quantity
            Wavelength (or array of wavelengths)

        Return
        ------
        Quantity:
            Effective area(s)
        """
        wvl = wvl.to(u.nm).value
        if self.aeff_data is None:
            code_path = (Path(__file__) / ".." / "..").resolve()
            aeff_file = code_path / "data" / "calibration" / "effective_area.sav"
            self.aeff_data = readsav(aeff_file.as_posix())
        # try interpolating for both second (1) and first (2) order
        left_right = {"left": np.nan, "right": np.nan}
        aeff1 = np.interp(
            wvl, self.aeff_data["lam_1"], self.aeff_data["net_resp_1"], **left_right
        )
        aeff2 = np.interp(
            wvl, self.aeff_data["lam_2"], self.aeff_data["net_resp_2"], **left_right
        )
        # choose where interpolation was done for the correct order
        return np.where(np.isfinite(aeff2), aeff2, aeff1) * u.mm**2

    @u.quantity_input
    def quantum_efficiency(self, wvl: u.Angstrom):
        """
        Get the SPICE detector quantum efficiency for some wavelength

        Parameters
        ----------
        wvl: Quantity
            Wavelength (or array of wavelengths)

        Return
        ------
        Quantity:
            Quantum efficiency(ies): number of detected photons / number of
            incident photons

        Not sure about the values for LW 2nd order, and on what wavelength
        ranges the output should be NaN.
        """
        wvl = wvl.to(u.Angstrom).value
        # Source: Table 8.25 of SPICE-RAL-RP-0002 v10.0
        qe_sw = np.interp(
            wvl,
            [703, 706, 770, 790],  # angstrom
            [0.12, 0.12, 0.1, 0.1],  # electron/photon
            left=np.nan,
            right=np.nan,
        )
        qe_lw = 0.25  # electron/photon
        return np.where((wvl > 703) & (wvl < 791), qe_sw, qe_lw)

    @u.quantity_input
    def which_detector(self, wvl: u.Angstrom):
        """
        Determine which detector corresponds to some wavelength

        Parameters
        ----------
        wvl: Quantity
            Wavelength

        Return
        ------
        str
            Detector name (None if not on a detector)
        """
        wvl = wvl.to(u.Angstrom).value
        if 703 < wvl < 791:
            return "SW"
        elif 970 < wvl < 1053:
            return "LW"
        else:
            return None

    @u.quantity_input
    def gain(self, wvl: u.Angstrom):
        """
        Detector gain as a function of wavelength

        Parameters
        ----------
        wvl: Quantity
            Wavelength

        Return
        ------
        float
            Detector gain
        """
        detector = self.which_detector(wvl)
        if detector is None:
            return np.nan * u.ct / u.ph
        else:
            return {"SW": 3.58, "LW": 0.57}[detector] * u.ct / u.ph

    @u.quantity_input
    def dark_current(self, wvl: u.Angstrom):
        """
        Detector dark current as a function of wavelength

        Parameters
        ----------
        wvl: Quantity
            Wavelength

        Return
        ------
        float
            Detector dark current
        """
        detector = self.which_detector(wvl)
        if detector is None:
            return np.nan * u.ct / u.s / u.pix
        else:
            return {"SW": 0.89, "LW": 0.54}[detector] * u.ct / u.s / u.pix

    @u.quantity_input
    def noise_factor(self, wvl: u.Angstrom):
        """
        Detector noise multiplication factor as a function of wavelength

        Parameters
        ----------
        wvl: Quantity
            Wavelength

        Return
        ------
        float
            Noise multiplication factor
        """
        detector = self.which_detector(wvl)
        if detector is None:
            return np.nan
        else:
            return {"SW": 1.0, "LW": 1.6}[detector]
