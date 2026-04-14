"""
Check newline at the end of a file.
"""

import re
import sys
from pathlib import Path

from logging518.config import fileConfig

from quality_control.console_logging import get_child_logger
from quality_control.project_config import ProjectConfig
from quality_control.static_checks.check_black import QualityControlArgumentsParser

logger = get_child_logger(__file__)


def get_all_files(root_dir: Path) -> list[Path]:
    """
    Collect all non-empty files.

    Args:
        root_dir[Path]: Root directory of the project

    Returns:
        list[Path]: List of all non-empty files collected
    """
    return [path for path in root_dir.rglob("*") if path.is_file() and path.stat().st_size != 0]


def compile_patterns(patterns: list[str]) -> list[re.Pattern]:
    """
    Compile regex patterns with validation.

    Args:
        patterns(list[str]): List of patterns to exclude

    Returns:
        list[re.Pattern]: Compiled patterns
    """
    compiled_patterns = []
    for pattern in patterns:
        try:
            compiled_patterns.append(re.compile(pattern))
        except re.error as error:
            raise ValueError(f"Invalid regex pattern: {pattern}") from error
    return compiled_patterns


def is_excluded(path: Path, patterns: list[re.Pattern]) -> bool:
    """
    Check if path matches any exclude pattern.

    Args:
        path[Path]: File path
        patterns(list[re.Pattern]): Patterns to exclude

    Returns:
        bool: Matches pattern or not
    """
    path_str = str(path)
    return any(pattern.search(path_str) for pattern in patterns)


def filter_paths(paths: list[Path], patterns: list[re.Pattern]) -> list[Path]:
    """
    Filter paths using regex.

    Args:
        patterns(list[re.Pattern]): List of patterns to exclude
        paths(list[Path]): List of files to check

    Returns:
        list[Path]: List of filtered files to check
    """
    return [path for path in paths if not is_excluded(path, patterns)]


def has_newline(paths: list[Path]) -> bool:
    """
    Check for a newline at the end.

    Args:
        paths (list[Path]): Appropriate paths

    Returns:
        bool: Has newline or not
    """
    bad_paths = []
    check_is_good = True

    for path in sorted(paths):
        logger.info(f"Analyzing {path}")

        try:
            with open(path, encoding="utf-8") as file:
                lines = file.readlines()
        except UnicodeDecodeError:
            logger.info(f"Skipping non-text file: {path}")
            continue

        if lines and not lines[-1].endswith("\n"):
            bad_paths.append(path)
            check_is_good = False

    if check_is_good:
        logger.info("All files conform to the template.")
    else:
        for bad_path in bad_paths:
            logger.info(f"No newline at the end of the {bad_path}")

    return check_is_good


def main() -> None:
    """
    Entrypoint for module.
    """
    args = QualityControlArgumentsParser(underscores_to_dashes=True).parse_args()
    root_dir = args.root_dir.resolve()
    toml_config = (args.toml_config_path or (root_dir / "pyproject.toml")).resolve()

    fileConfig(toml_config)

    config_path = root_dir / "project_config.json"
    project_config = ProjectConfig(config_path)

    raw_patterns = project_config.get_newline_config()
    patterns = compile_patterns(raw_patterns)

    all_files = get_all_files(root_dir)
    filtered_files = filter_paths(all_files, patterns)

    result = has_newline(filtered_files)
    sys.exit(not result)


if __name__ == "__main__":
    main()
