"""
Check lint for code style and formatting in Python code using Ruff.
"""

# pylint: disable=duplicate-code
import sys
from os import listdir
from pathlib import Path
from typing import Optional

from logging518.config import fileConfig

from quality_control.cli_unifier import (
    _run_console_tool,
    choose_python_exe,
    handles_console_error,
)
from quality_control.console_logging import get_child_logger
from quality_control.lab_settings import LabSettings
from quality_control.project_config import ProjectConfig
from quality_control.quality_control_parser import QualityControlArgumentsParser

logger = get_child_logger(__file__)


class QualityControlRuffArgumentsParser(QualityControlArgumentsParser):
    """
    CLI for Ruff checks.
    """

    repository_type: Optional[str] = None


@handles_console_error()
def run_ruff_on_paths(
    paths: list[Path],
    path_to_config: Path,
    root_dir: Path,
    ignore_tests: bool = False,
) -> tuple[str, str, int]:
    """
    Run Ruff checks for the given paths.

    Args:
        paths (list[Path]): Paths to the projects/labs.
        path_to_config (Path): Path to the pyproject.toml config.
        root_dir (Path): Root directory of the repository.
        ignore_tests (bool): If True, excludes tests directory from check.

    Returns:
        tuple[str, str, int]: stdout, stderr, exit code
    ```"""
    existing_paths = [str(p) for p in paths if p.exists()]

    if not existing_paths:
        return "", "", 0

    ruff_args = [
        "-m",
        "ruff",
        "check",
        *existing_paths,
        "--config",
        str(path_to_config),
    ]

    if ignore_tests:
        ruff_args.extend(["--exclude", "**/tests/**"])

    return _run_console_tool(str(choose_python_exe(lab_path=root_dir)), ruff_args, debug=True)


def main() -> None:
    """
    Run Ruff checks for the project.
    """
    args = QualityControlRuffArgumentsParser(underscores_to_dashes=True).parse_args()

    root_dir = args.root_dir.resolve()
    toml_config = (args.toml_config_path or (root_dir / "pyproject.toml")).resolve()
    project_config_path = (args.project_config_path or (root_dir / "project_config.json")).resolve()

    project_config = ProjectConfig(project_config_path)

    fileConfig(toml_config)

    check_is_failed = False

    addons_paths = project_config.get_addons_paths(root_dir=root_dir)
    if addons_paths:
        logger.info("Running Ruff for addons...")
        _, stderr, exit_code = run_ruff_on_paths(
            addons_paths,
            toml_config,
            root_dir=root_dir,
        )
        if exit_code != 0:
            msg = ", ".join(str(i) for i in addons_paths)
            logger.error(f"Ruff check on {msg} failed! Code: {exit_code}. Errors: {stderr}")
            check_is_failed = True
        else:
            logger.info("Ruff check for addons passed!")

    labs_list = project_config.get_labs_paths(root_dir=root_dir)
    for lab_path in labs_list:

        if "settings.json" in listdir(lab_path):
            target_score = LabSettings(root_dir / f"{lab_path}/settings.json").target_score

            if target_score == 0:
                logger.info(f"Skipping Ruff check for {lab_path}")
                continue

            logger.info(f"Running Ruff for lab {lab_path}")
            _, stderr, exit_code = run_ruff_on_paths(
                [lab_path],
                toml_config,
                ignore_tests=args.repository_type == "public",
                root_dir=root_dir,
            )

            if exit_code != 0:
                logger.error(f"Ruff check for lab {lab_path} failed!")
                check_is_failed = True
            else:
                logger.info(f"Ruff check for lab {lab_path} passed!")

    if check_is_failed:
        logger.error("\nSome of Ruff checks failed. Fix listed issues.")
        sys.exit(1)
    logger.info("\nAll Ruff checks passed successfully!")


if __name__ == "__main__":
    main()
