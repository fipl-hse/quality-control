"""
Useful constant variables.
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
PROJECT_CONFIG_PATH = PROJECT_ROOT / "project_config.json"
CORE_UTILS_PACKAGE_PATH = PROJECT_ROOT / "core_utils"
QUALITY_CONTROL_PATH = Path(__file__).parent.parent

USE_VENV = False
