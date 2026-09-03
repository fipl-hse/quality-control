"""
Module for CLI for quality control.
"""

import os
from pathlib import Path

from tap import Tap


class QualityControlArgumentsParser(Tap):
    """
    CLI for quality control.
    """

    toml_config_path: Path | None = None
    root_dir: Path | None = Path(os.getcwd())
    project_config_path: Path | None = None
