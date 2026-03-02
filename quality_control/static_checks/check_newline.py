"""
Check newline at the end of a file.
"""

import sys
from pathlib import Path

from logging518.config import fileConfig

from quality_control.console_logging import get_child_logger
from quality_control.project_config import ProjectConfig
from quality_control.static_checks.check_black import QualityControlArgumentsParser

logger = get_child_logger(__file__)


def get_paths(root_dir: Path, exclude_dirs: set[str]) -> list[Path]:
    """
    Get paths excluding configured directories.

    Returns:
        list[Path]: Paths to excluded directories
    """
    only_sources = [
        file for file in root_dir.iterdir()
        if file.name not in exclude_dirs
    ]

    list_with_paths: list[Path] = []

    for source_file in only_sources:
        if not source_file.is_dir():
            list_with_paths.append(source_file)
            continue

        list_with_paths.extend(
            [
                file
                for file in source_file.rglob("*")
                if not set(parent.name for parent in file.parents) & exclude_dirs
            ]
        )
    return list_with_paths


def check_paths(
    list_with_paths: list[Path],
    exclude_files: set[str],
    exclude_extensions: set[str],
) -> list[Path]:
    """
    Check valid files for newline check.

    Args:
        exclude_extensions: Extensions to exclude
        exclude_files: Files to exclude
        list_with_paths (list): Paths to non-python files

    Returns:
        list: Appropriate paths
    """
    paths: list[Path] = []

    for path in sorted(list_with_paths):
        is_file = path.is_file() and path.stat().st_size != 0
        is_ok_file = (
            path.name not in exclude_files
            and path.suffix not in exclude_extensions
            and "__pycache__" not in str(path)
        )
        if is_file and is_ok_file:
            paths.append(path)
    return paths


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
    for path in paths:
        logger.info(f"Analyzing {path}")
        with open(path, encoding="utf-8") as file:
            lines = file.readlines()
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
    newline_config = project_config.get_newline_config()

    exclude_dirs = set(newline_config.exclude_dirs)
    exclude_files = set(newline_config.exclude_files)
    exclude_extensions = set(newline_config.exclude_extensions)

    list_with_paths = get_paths(root_dir, exclude_dirs)
    paths = check_paths(list_with_paths, exclude_files, exclude_extensions)
    result = has_newline(paths)
    sys.exit(not result)


if __name__ == "__main__":
    main()
