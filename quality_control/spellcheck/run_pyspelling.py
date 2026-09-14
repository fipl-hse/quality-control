"""
Run PySpelling with project-specific warning handling.
"""

import runpy
import warnings

from bs4 import XMLParsedAsHTMLWarning

warnings.filterwarnings(
    "ignore",
    category=XMLParsedAsHTMLWarning,
)

runpy.run_module("pyspelling", run_name="__main__")
