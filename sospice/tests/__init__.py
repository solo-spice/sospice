"""
This module contains package tests.
"""

from pathlib import Path

import sospice

__all__ = ["TEST_DATA_PATH"]


TEST_DATA_PATH = Path(sospice.__file__).parent / "tests" / "data"
