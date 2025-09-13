"""
Check black to check the style and quality of Python code.
"""

import os
import sys
from pathlib import Path
from typing import Optional

# pylint: disable=duplicate-code
from logging518.config import fileConfig
from tap import Tap

from quality_control.cli_unifier import (
    _run_console_tool,
    choose_python_exe,
    handles_console_error,
)
from quality_control.console_logging import get_child_logger
from quality_control.constants import PROJECT_ROOT
from quality_control.project_config import ProjectConfig

logger = get_child_logger(__file__)


class BlackArgumentsParser(Tap):
    toml_config_path: Optional[Path] = None
    root_dir: Optional[Path] = Path(os.getcwd())
    project_config_path: Optional[Path] = None


@handles_console_error()
def check_black_on_paths(
    paths: list[Path],
    toml_config_path: Path,
    python_exe: Path,
    root_dir: Path,
) -> tuple[str, str, int]:
    """
    Run Black in --check mode on the given paths.

    Args:
        paths (list[Path]): List of paths to check.
        toml_config_path (Path): Path to pyproject.toml (Black config).
        python_exe (Path): Python executable to run Black.
        root_dir (Path): Root directory for running Black.

    Returns:
        tuple[str, str, int]: stdout, stderr, and return code.
    """
    black_args = [
        "-m",
        "black",
        "--check",
        "--config",
        str(toml_config_path),
        *[str(p) for p in paths if p.exists()],
    ]
    return _run_console_tool(str(python_exe), black_args, debug=True, cwd=root_dir)


def main() -> None:
    args = BlackArgumentsParser().parse_args()

    root_dir = args.root_dir.resolve()
    toml_config = (args.toml_config_path or (root_dir / "pyproject.toml")).resolve()

    project_config_path = (
        args.project_config_path or (root_dir / "project_config.json")
    ).resolve()

    project_config = ProjectConfig(project_config_path)

    fileConfig(toml_config)

    labs_list = project_config.get_labs_paths()
    addons = project_config.get_addons_names()
    logger.info(f"Labs to check with black: {labs_list}")
    logger.info(f"Addons to check with black: {addons}")

    all_paths = [root_dir / addon for addon in addons] + [
        root_dir / lab for lab in labs_list
    ]

    python_exe = choose_python_exe(lab_path=root_dir)

    check_black_on_paths(
        all_paths,
        toml_config_path=toml_config,
        python_exe=python_exe,
        root_dir=root_dir,
    )


if __name__ == "__main__":
    main()
