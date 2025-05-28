"""
Check black to check the style and quality of Python code.
"""

import os
# pylint: disable=duplicate-code
from pathlib import Path
from typing import Optional

from logging518.config import fileConfig
from tap import Tap

import quality_control.constants
from quality_control.cli_unifier import (_run_console_tool, choose_python_exe,
                                         handles_console_error)
from quality_control.console_logging import get_child_logger
from quality_control.constants import PROJECT_ROOT
from quality_control.project_config import ProjectConfig

logger = get_child_logger(__file__)


class BlackArgumentsParser(Tap):
    toml_config_path: Optional[Path] = None
    root_dir: Optional[Path] = Path(os.getcwd())
    project_config_path: Optional[Path] = None



@handles_console_error()
def check_black_on_paths(paths: list[Path]) -> tuple[str, str, int]:
    """
    Run black checks for the project.

    Args:
        paths (list[Path]): Paths to the projects.

    Returns:
        tuple[str, str, int]: stdout, stderr, exit code
    """
    black_args = [
        "-m",
        "black",
        *map(str, filter(lambda x: x.exists(), paths)),
        "--check",
    ]

    return _run_console_tool(
        str(choose_python_exe(lab_path=os.getcwd())),
        black_args,
        debug=True,
        cwd=PROJECT_ROOT,
    )


def main() -> None:
    """
    Run black checks for the project.
    """
    import quality_control.cli_unifier

    quality_control.cli_unifier.CONFIG_PACKAGE_PATH = (
        quality_control.constants.QUALITY_CONTROL_PATH / "quality_control"
    )

    args = BlackArgumentsParser().parse_args()
    if args.project_config_path is not None:
        quality_control.constants.PROJECT_CONFIG_PATH = args.project_config_path
    if args.root_dir is not None:
        quality_control.constants.PROJECT_ROOT = args.root_dir
    fileConfig(args.root_dir / "pyproject.toml")

    project_config = ProjectConfig(args.project_config_path)
    labs_list = project_config.get_labs_paths()
    addons = project_config.get_addons_names()
    logger.info(labs_list)

    logger.info(f"Running black on {', '.join(addons)}")

    all_paths = [args.root_dir / addon for addon in addons]
    all_paths.extend([args.root_dir / lab_name for lab_name in labs_list])

    check_black_on_paths(all_paths)


if __name__ == "__main__":
    main()
