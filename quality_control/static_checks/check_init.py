"""
Check availability of __init__.py in every directory except for excluded ones.
"""

import sys
from pathlib import Path

from tap import Tap

from quality_control.console_logging import get_child_logger

logger = get_child_logger(__file__)


class InitArgumentsParser(Tap):
    """
    CLI arguments for checking __init__.py presence.
    """

    root_dir: Path = Path.cwd()


def find_missing_inits(root_dir: Path, excluded_dirs: list[str]) -> list[Path]:
    """
    Find directories with Python files but missing __init__.py.

    Args:
        root_dir (Path): Root directory to scan.
        excluded_dirs (list[str]): List of directory names to exclude.

    Returns:
        list[Path]: List of directories without __init__.py.
    """
    missing_init = []
    for directory in root_dir.rglob("*"):
        if not directory.is_dir():
            continue
        if any(excluded in directory.parts for excluded in excluded_dirs):
            continue
        python_files = list(directory.glob("*.py"))
        if python_files and not (directory / "__init__.py").exists():
            missing_init.append(directory)
    return missing_init


def main() -> None:
    args = InitArgumentsParser().parse_args()
    root_dir = args.root_dir.resolve()

    excluded_dirs = ["venv", ".git", "__pycache__"]
    missing_init = find_missing_inits(root_dir, excluded_dirs)

    if missing_init:
        logger.error("Error: __init__.py was not found in following directories:")
        for path in missing_init:
            print(f"- {path}")
        sys.exit(1)

    logger.info("All directories with Python-files contain __init__.py.")
    sys.exit(0)


if __name__ == "__main__":
    main()
