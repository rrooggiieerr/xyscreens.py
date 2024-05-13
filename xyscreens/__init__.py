"""
Implements the XYScreens library for controlling XY Screens projector screens and projector lifts.

Created on 17 Nov 2022

@author: Rogier van Staveren
"""

try:
    from ._version import __version__
except ModuleNotFoundError:
    pass
from .xyscreens import XYScreens, XYScreensConnectionError, XYScreensState
