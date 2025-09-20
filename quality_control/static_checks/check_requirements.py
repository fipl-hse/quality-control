# pylint: disable=implicit-str-concat
"""
Check dependencies.
"""

import re
import sys
from pathlib import Path

from logging518.config import fileConfig

from quality_control.console_logging import get_child_logger
from quality_control.constants import PROJECT_ROOT
from quality_control.static_checks.check_black import BlackArgumentsParser

logger = get_child_logger(__file__)


def get_paths(root_dir: Path) -> list[Path]:
    """
    Get paths to non-python files.

    Returns:
        list[Path]: Paths to non-python files
    """
    return [
        path for path in root_dir.rglob("requirements*.txt") if "venv" not in str(path)
    ]


def get_requirements(path: Path) -> list:
    """
    Get dependencies.

    Args:
        path (Path): Path to non-python file

    Returns:
        list: Dependencies
    """
    with path.open(encoding="utf-8") as f:
        lines = f.readlines()
    return [line.strip() for line in lines if line.strip()]


def compile_pattern() -> re.Pattern:
    """
    Compile pattern.

    Returns:
        re.Pattern: Compiled pattern
    """
    return re.compile(
        r"((\w+(-\w+|\[\w+\])*==\d+(\.\d+)+)"
        r"|((-r|--extra-index-url)\s.*)"
        r"|(git\+https://github\.com/.*\.git))",
        re.MULTILINE,
    )


def check_dependencies(lines: list, compiled_pattern: re.Pattern, path: Path) -> bool:
    """
    Check that dependencies confirm to the template.

    Args:
        lines (list): Dependencies
        compiled_pattern (re.Pattern): Compiled pattern
        path (Path): Path to file with dependencies

    Returns:
        bool: Do dependencies confirm to the template or not
    """
    expected = [
        i
        for i in sorted(map(str.lower, lines))
        if i.split()[0] not in ("--extra-index-url",)
    ]
    actual = [
        i for i in map(str.lower, lines) if i.split()[0] not in ("--extra-index-url",)
    ]
    if expected != actual:
        expected_str = "\n".join(expected)
        logger.error(
            f"Dependencies in {path.relative_to(PROJECT_ROOT)} do not follow sorting rule."
            f"\nExpected\n{expected_str}"
        )
        return False
    for line in lines:
        if not re.search(compiled_pattern, line):
            logger.error(
                f"Specific dependency in {path.relative_to(PROJECT_ROOT)} "
                f"do not conform to the template.\n{line}"
            )
            return False
    return True


def main() -> None:
    """
    Call functions.
    """
    args = BlackArgumentsParser().parse_args()

    root_dir = args.root_dir.resolve()
    toml_config = (args.toml_config_path or (root_dir / "pyproject.toml")).resolve()
    fileConfig(toml_config)
    paths = get_paths(root_dir=root_dir)
    compiled_pattern = compile_pattern()
    for path in paths:
        lines = get_requirements(path)
        if not check_dependencies(lines, compiled_pattern, path):
            logger.error(f"{path.relative_to(root_dir)} : FAIL")
            sys.exit(1)
        else:
            logger.info(f"{path.relative_to(root_dir)} : OK")


if __name__ == "__main__":
    main()
