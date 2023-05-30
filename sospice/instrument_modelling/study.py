from dataclasses import dataclass
import astropy.units as u


@dataclass
class Study:
    """
    Study parameters
    """

    slit: u.arcsec = None
    bin_x: int = None  # bin over x or wavelength axis
    bin_y: int = None
    window_width: u.pix = None
    exp_time: u.s = None
    av_wavelength: u.m = None
    radcal: u.ct / (u.W / u.m**2 / u.sr / u.nm) = None
    level: str = None

    def init_from_header(self, header):
        """
        Initialize study parameters from FITS header

        Parameters
        ----------
        header: astropy.io.fits.Header
            FITS header
        """
        # TODO use real slit width, not nominal slit width
        self.slit = header["SLIT_WID"] * u.arcsec
        self.bin_x = header["NBIN3"]  # bin factor in dispersion direction
        self.bin_y = header["NBIN2"]  # bin factor in slit direction
        self.exp_time = header["XPOSURE"] * u.s
        self.window_width = header["NAXIS3"] * u.pix
        self.av_wavelength = (
            (header["WAVEMIN"] + header["WAVEMAX"]) / 2 * 10 ** header["WAVEUNIT"] * u.m
        )
        self.level = header["LEVEL"]
        if self.level == "L2":
            self.radcal = header["RADCAL"] * u.ct / (u.W / u.m**2 / u.sr / u.nm)
        else:
            self.radcal = None  # TODO or need to have a value of 1?

    def __str__(self):
        if self.slit is None:
            return "Non-initialized study"
        else:
            return f"""
Slit: {self.slit}
Bin: ({self.bin_x}, {self.bin_y})
Exposure time: {self.exp_time}
Window width: {self.window_width}
Average wavelength: {self.av_wavelength.to(u.nm)}
RADCAL: {self.radcal}
            """
