"""
Check black to check the style and quality of Python code.
"""

import os
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
    paths: list[Path], toml_config_path: Optional[Path], root_dir: Optional[Path]
) -> tuple[str, str, int]:
    if toml_config_path:
        config_path = (
            toml_config_path
            if toml_config_path.is_absolute()
            else (root_dir or Path.cwd()) / toml_config_path
        ).resolve()
    else:
        config_path = ((root_dir or Path.cwd()) / "pyproject.toml").resolve()

    black_args = [
        "-m",
        "black",
        *[str(p) for p in paths if p.exists()],
        "--check",
        "--config",
        str(config_path),
    ]

    return _run_console_tool(
        str(choose_python_exe(lab_path=Path(os.getcwd()))),
        black_args,
        debug=True,
        cwd=PROJECT_ROOT,
    )


def main() -> None:
    import quality_control.cli_unifier

    quality_control.cli_unifier.CONFIG_PACKAGE_PATH = (
        quality_control.constants.QUALITY_CONTROL_PATH / "quality_control"
    )

    args = BlackArgumentsParser().parse_args()

    if args.project_config_path is not None:
        quality_control.constants.PROJECT_CONFIG_PATH = args.project_config_path
    if args.root_dir is not None:
        quality_control.constants.PROJECT_ROOT = args.root_dir

    toml_logging_config = args.root_dir / "pyproject.toml"
    if toml_logging_config.exists():
        fileConfig(toml_logging_config)

    project_config = ProjectConfig(args.project_config_path)
    labs_list = project_config.get_labs_paths()
    addons = project_config.get_addons_names()

    logger.info("Labs: %s", labs_list)
    logger.info("Addons: %s", addons)
    logger.info("Running black on: %s", ", ".join(addons))

    all_paths = [args.root_dir / addon for addon in addons]
    all_paths += [args.root_dir / lab for lab in labs_list]

    check_black_on_paths(
        all_paths,
        toml_config_path=args.toml_config_path,
        root_dir=args.root_dir,
    )


if __name__ == "__main__":
    main()
