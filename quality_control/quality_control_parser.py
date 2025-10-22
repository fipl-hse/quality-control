
import os
from pathlib import Path
from typing import Optional

from tap import Tap

class QualityControlArgumentsParser(Tap):
    toml_config_path: Optional[Path] = None
    root_dir: Optional[Path] = Path(os.getcwd())
    project_config_path: Optional[Path] = None
    ignore_tests: bool = False
