"""
Check black to check the style and quality of Python code.
"""

# pylint: disable=duplicate-code
from pathlib import Path

from .cli_unifier import _run_console_tool, choose_python_exe, handles_console_error
from .console_logging import get_child_logger
from .constants import ABSOLUTE_CWD_PATH, ABSOLUTE_PROJECT_CONFIG_PATH
from .project_config import ProjectConfig

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

    return _run_console_tool(str(choose_python_exe()), black_args, debug=True, cwd=ABSOLUTE_CWD_PATH)


def main() -> None:
    """
    Run black checks for the project.
    """
    project_config = ProjectConfig(ABSOLUTE_PROJECT_CONFIG_PATH)
    labs_list = project_config.get_labs_paths()
    addons = project_config.get_addons_names()
    logger.info(labs_list)

    logger.info(f"Running black on {', '.join(addons)}")

    all_paths = [ABSOLUTE_CWD_PATH / addon for addon in addons]
    all_paths.extend([ABSOLUTE_CWD_PATH / lab_name for lab_name in labs_list])

    check_black_on_paths(all_paths)


if __name__ == "__main__":
    main()
