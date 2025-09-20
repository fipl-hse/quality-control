"""
Check lint for code style in Python code.
"""

# pylint: disable=duplicate-code
import argparse
import os
import re
import sys
from os import listdir
from pathlib import Path
from typing import Optional

from logging518.config import fileConfig
from quality_control.quality_control_parser import QualityControlArgumentsParser
from tap import Tap

from quality_control.cli_unifier import (
    _run_console_tool,
    choose_python_exe,
    handles_console_error,
)
from quality_control.console_logging import get_child_logger
from quality_control.lab_settings import LabSettings
from quality_control.project_config import ProjectConfig

logger = get_child_logger(__file__)


class QualityControlLintArgumentsParser(QualityControlArgumentsParser):
    repository_type: Optional[str] = None


def transform_score_into_lint(target_score: int) -> int:
    """
    Transform target s into lint.

    Args:
         target_score (int): Desired score

    Returns:
        int: Lint score
    """
    target_score_to_lint_score = {10: 10, 8: 10, 6: 7, 4: 5}
    return target_score_to_lint_score.get(target_score, 0)


def is_passed(lint_output: str, target_lint_level: int) -> bool:
    """
    Determine whether lint level is passed.

    Args:
        lint_output (str): Lint output
        target_lint_level (int): Lint score

    Returns:
        bool: Lint check passed or not
    """
    if not lint_output:
        return True

    lint_level = re.search(r"Your code has been rated at \d+\.\d+", lint_output).group(
        0
    )
    lint_score = int(re.search(r"\d+", lint_level).group(0))

    if lint_score < target_lint_level:
        logger.error(
            "\nLint check is not passed!\nFix the listed issues and try again.\n"
        )
        return False
    if lint_score != 10:
        logger.info("\nLint check passed but there are things to improve.")
        return True
    logger.info("\nLint check passed!\n")
    return True


@handles_console_error()
def check_lint_on_paths(
    paths: list[Path],
    path_to_config: Path,
    root_dir: Path,
    exit_zero: bool = False,
    ignore_tests: bool = False,
) -> tuple[str, str, int]:
    """
    Run lint checks for the project.

    Args:
        paths (list[Path]): Paths to the projects.
        path_to_config (Path): Path to the config.
        exit_zero (bool): Exit-zero lint argument.
        ignore_tests (bool): Ignore lint argument.

    Returns:
        tuple[str, str, int]: stdout, stderr, exit code
    """
    lint_args = [
        "-m",
        "pylint",
        *map(str, filter(lambda x: x.exists(), paths)),
        "--rcfile",
        str(path_to_config),
    ]
    if ignore_tests:
        lint_args.extend(["--ignore", "tests"])
    if exit_zero:
        lint_args.append("--exit-zero")
    return _run_console_tool(
        str(choose_python_exe(lab_path=root_dir)), lint_args, debug=True
    )


def check_lint_level(lint_output: str, target_score: int) -> bool:
    """
    Run lint level check for the project.

    Args:
        lint_output (str): Pylint check output.
        target_score (int): Target score.

    Returns:
        bool: True if target score corresponding lint score, False otherwise
    """
    score = int(target_score)
    target_lint_level = transform_score_into_lint(score)

    if not target_lint_level:
        logger.error("\nInvalid value for target score: accepted are 4, 6, 8, 10.\n")
        return False
    return is_passed(lint_output, target_lint_level)


def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="Run check_lint.py checks for each lab."
    )
    parser.add_argument(
        "--repository_type", help="Type of the repository (public/admin)"
    )
    return parser.parse_args()


def main() -> None:
    """
    Run lint checks for the project.
    """
    args = QualityControlArgumentsParser(underscores_to_dashes=True).parse_args()

    root_dir = args.root_dir.resolve()
    toml_config = (args.toml_config_path or (root_dir / "pyproject.toml")).resolve()

    project_config_path = (
        args.project_config_path or (root_dir / "project_config.json")
    ).resolve()

    project_config = ProjectConfig(project_config_path)

    fileConfig(toml_config)

    labs_list = project_config.get_labs_paths(root_dir=root_dir)
    addons = project_config.get_addons_names()

    check_is_failed = False

    if addons:
        stdout, _, _ = check_lint_on_paths(
            [root_dir / addon for addon in addons],
            toml_config,
            exit_zero=True,
            root_dir=root_dir,
        )
        if not check_lint_level(stdout, 10):
            logger.info(f"Running lint on {', '.join(addons)}")
            check_is_failed = True

    for lab_name in labs_list:
        lab_path = root_dir / lab_name

        if "settings.json" in listdir(lab_path):
            target_score = LabSettings(
                root_dir / f"{lab_path}/settings.json"
            ).target_score
            if target_score == 0:
                logger.info("Skipping check")
                continue

            logger.info(f"Running lint for lab {lab_path}")
            stdout, _, _ = check_lint_on_paths(
                [lab_path],
                toml_config,
                ignore_tests=args.repository_type == "public",
                exit_zero=True,
                root_dir=root_dir,
            )
            if not check_lint_level(stdout, target_score):
                check_is_failed = True

    if check_is_failed:
        logger.error("\nSome of checks were failed. Fix it.")
        sys.exit(1)


if __name__ == "__main__":
    main()
