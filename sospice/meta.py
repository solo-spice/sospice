import textwrap

import astropy.units as u
import numpy as np
from astropy.coordinates import SkyCoord
from astropy.time import Time

from sunraster.meta import Meta, SlitSpectrographMetaABC

__all__ = ["SPICEMeta"]


class SPICEMeta(Meta, metaclass=SlitSpectrographMetaABC):
    # ---------- SPICE-specific convenience methods ----------
    def _get_unit(self, key):
        if comment := self.comments.get(key):
            try:
                return [s.split("]") for s in comment.split("[")[1:]][0][:-1][0]
            except IndexError:
                pass
        return None

    def _construct_quantity(self, key):
        val = self.get(key)
        if val:
            val *= u.Unit(self._get_unit(key))
        return val

    def _construct_time(self, key):
        val = self.get(key)
        scale = self._get_unit(key).lower()
        if val:
            val = Time(val, format="fits", scale=scale)
        return val

    def __str__(self):
        return textwrap.dedent(
            f"""\
                SPICEMeta
                ---------
                Observatory:\t\t\t\t{self.observatory}
                Instrument:\t\t\t\t{self.instrument}
                Detector:\t\t\t\t{self.detector}
                Spectral Window:\t\t\t{self.spectral_window}
                Date:\t\t\t\t\t{self.date_reference}
                OBS_ID (SOC Observation ID):\t\t{self.observing_mode_id_solar_orbiter}
                SPIOBSID (SPICE Observation ID):\t{self.spice_observation_id}
                """
        )

    def __repr__(self):
        return f"{object.__repr__(self)}\n{str(self)}"

    # ---------- Inherited ABC properties ----------
    @property
    def spectral_window(self):
        spectral_window = self.get("EXTNAME")
        # Remove redundant text associated with dumbbells.
        joiner = "_"
        if self.contains_dumbbell:
            dummy_txt = ""
            spectral_window = spectral_window.replace("DUMBBELL", dummy_txt)
            spectral_window = spectral_window.replace("UPPER", dummy_txt)
            spectral_window = spectral_window.replace("LOWER", dummy_txt)
            spectral_window = joiner.join(list(filter((dummy_txt).__ne__, spectral_window.split(joiner))))
        # Remove other redundant text from window name.
        redundant_txt = "WINDOW"
        if redundant_txt in spectral_window:
            spectral_window = joiner.join([comp for comp in spectral_window.split(joiner) if "WINDOW" not in comp])
        return spectral_window

    @property
    def detector(self):
        return self.get("DETECTOR")

    @property
    def instrument(self):
        return self.get("INSTRUME")

    @property
    def observatory(self):
        return self.get("OBSRVTRY")

    @property
    def processing_level(self):
        return self.get("LEVEL")

    @property
    def rsun_meters(self):
        return self._construct_quantity("RSUN_REF")

    @property
    def rsun_angular(self):
        return self._construct_quantity("RSUN_ARC")

    @property
    def spice_observation_id(self):
        return self.get("SPIOBSID")

    @property
    def observer_radial_velocity(self):
        return self._construct_quantity("OBS_VR")

    @property
    def distance_to_sun(self):
        return self._construct_quantity("DSUN_OBS")

    @property
    def date_reference(self):
        return self._construct_time("DATE-OBS")

    @property
    def date_start(self):
        return self._construct_time("DATE-BEG")

    @property
    def date_end(self):
        return self._construct_time("DATE-END")

    @property
    def observer_location(self):
        from sunpy.coordinates import HeliographicStonyhurst

        lon_unit = u.deg
        lat_unit = u.deg
        radius_unit = u.m
        lon_key = "HGLN_OBS"
        lat_key = "HGLT_OBS"
        kwargs = {
            "lon": u.Quantity(self.get(lon_key), unit=self._get_unit(lon_key)).to_value(lon_unit),
            "lat": u.Quantity(self.get(lat_key), unit=self._get_unit(lat_key)).to_value(lat_unit),
            "radius": self.distance_to_sun.to_value(radius_unit),
            "unit": (lon_unit, lat_unit, radius_unit),
            "frame": HeliographicStonyhurst,
        }
        return SkyCoord(obstime=self.date_reference, **kwargs)

    @property
    def version(self):
        return self.get("VERSION")

    # ---------- SPICE-specific metadata properties ----------
    @property
    def observing_mode_id_solar_orbiter(self):
        return self.get("OBS_ID")

    @property
    def darkmap_subtracted_onboard(self):
        return bool(self.get("DARKMAP"))

    @property
    def bias_frame_subtracted_onboard(self):
        return bool(self.get("BLACKLEV"))

    @property
    def window_type(self):
        return self.get("WIN_TYPE")

    @property
    def slit_id(self):
        return self.get("SLIT_ID")

    @property
    def slit_width(self):
        return self._construct_quantity("SLIT_WID")

    @property
    def contains_dumbbell(self):
        return self.get("DUMBBELL") in [1, 2]

    @property
    def dumbbell_type(self):
        dumbbell_types = [None, "lower", "upper"]
        dumbbell_idx = self.get("DUMBBELL")
        return dumbbell_types[dumbbell_idx]

    @property
    def solar_B0(self):
        """
        Tilt angle of solar north toward spacecraft.
        """
        return self._construct_quantity("SOLAR_B0")

    @property
    def solar_P0(self):
        """
        Angle from spacecraft celestial north to solar north.
        """
        return self._construct_quantity("SOLAR_P0")

    @property
    def solar_ep(self):
        """
        Angle from spacecraft ecliptic north to solar north angle.
        """
        return self._construct_quantity("SOLAR_EP")

    @property
    def carrington_rotation(self):
        """
        Carrington Rotation number of observation.
        """
        return self.get("CAR_ROT")

    @property
    def date_start_earth(self):
        """
        Time at which photons reaching SPICE at start time would have reach
        Earth.
        """
        return self._construct_time("DATE_EAR")

    @property
    def date_start_sun(self):
        """
        Time at which photons reaching SPICE at start time would have left Sun.

        The Sun is defined as the center of the Sun assuming photon was
        not impeded.
        """
        return self._construct_time("DATE_SUN")
