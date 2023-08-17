from dataclasses import dataclass

import pandas as pd
from pathlib import Path


required_columns = {
    "NAXIS1",
    "NAXIS2",
    "NAXIS3",
    "NAXIS4",
    "OBT_BEG",
    "LEVEL",
    "FILENAME",
    "DATE-BEG",
    "SPIOBSID",
    "RASTERNO",
    "STUDYTYP",
    "MISOSTUD",
    "XPOSURE",
    "CRVAL1",
    "CDELT1",
    "CRVAL2",
    "CDELT2",
    "STP",
    "DSUN_AU",
    "CROTA",
    "OBS_ID",
    "SOOPNAME",
    "SOOPTYPE",
    "NWIN",
    "DARKMAP",
    "COMPLETE",
    "SLIT_WID",
    "DATE",
    "PARENT",
    "HGLT_OBS",
    "HGLN_OBS",
    "PRSTEP1",
    "PRPROC1",
    "PRPVER1",
    "PRPARA1",
}


@dataclass
class File:
    """
    A SPICE file entry in the SPICE catalog

    Parameters
    ----------
    metadata: pandas.Series
        File metadata
    skip_validation: bool
        Do no validate data
    """

    metadata: pd.Series = None
    skip_validation: bool = False

    def __post_init__(self):
        """
        Update object
        """
        if not self.skip_validation:
            self.validate()

    def validate(self):
        """
        Check file metadata
        """
        assert self.metadata is not None
        assert not self.metadata.empty
        assert required_columns.issubset(self.metadata.keys())

    @property
    def relative_path(self):
        """
        Get file relative path

        Return
        ------
        pathlib.PosixPath
            File path, relative to the "fits" directory of the file archive:
            leveln/yyyy/mm/dd

        Requires a DATE-BEG header (so does not work with L0 files).
        """
        date = self.metadata["DATE-BEG"]
        return (
            Path(f"level{self.metadata.LEVEL[1]}")  # noqa: W503
            / f"{date.year}"  # noqa: W503
            / f"{date.month:02}"  # noqa: W503
            / f"{date.day:02}"  # noqa: W503
        )
