"""
Useful constant variables.
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
PROJECT_CONFIG_PATH = PROJECT_ROOT / "project_config.json"
CONFIG_PACKAGE_PATH = PROJECT_ROOT / "config"
CORE_UTILS_PACKAGE_PATH = PROJECT_ROOT / "core_utils"
ABSOLUTE_CWD_PATH = Path.cwd()