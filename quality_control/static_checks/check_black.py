"""
Check black to check the style and quality of Python code.
"""

# pylint: disable=duplicate-code
from pathlib import Path

from quality_control.cli_unifier import _run_console_tool, choose_python_exe, handles_console_error
from quality_control.console_logging import get_child_logger
from quality_control.constants import PROJECT_CONFIG_PATH, PROJECT_ROOT
from quality_control.project_config import ProjectConfig

logger = get_child_logger(__file__)


@handles_console_error()
def check_black_on_paths(paths: list[Path]) -> tuple[str, str, int]:
    """
    Run black checks for the project.

    Args:
        paths (list[Path]): Paths to the projects.

    Returns:
        tuple[str, str, int]: stdout, stderr, exit code
    """
    black_args = ["-m", "black", *map(str, filter(lambda x: x.exists(), paths)), "--check"]

    return _run_console_tool(str(choose_python_exe()), black_args, debug=True, cwd=PROJECT_ROOT)


def main() -> None:
    """
    Run black checks for the project.
    """
    project_config = ProjectConfig(PROJECT_CONFIG_PATH)
    labs_list = project_config.get_labs_paths()
    logger.info(labs_list)

    logger.info("Running black on quality_control")
    all_paths = [
        PROJECT_ROOT / "quality_control"
    ]
    all_paths.extend([PROJECT_ROOT / lab_name for lab_name in labs_list])
    check_black_on_paths(all_paths)


if __name__ == "__main__":
    main()
