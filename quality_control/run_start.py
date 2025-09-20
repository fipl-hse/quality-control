"""
Run start.
"""

from pathlib import Path

from logging518.config import fileConfig

from quality_control.cli_unifier import (_run_console_tool, choose_python_exe,
                                         handles_console_error)
from quality_control.collect_coverage.run_coverage import get_target_score
from quality_control.console_logging import get_child_logger
from quality_control.constants import PROJECT_ROOT
from quality_control.project_config import ProjectConfig
from quality_control.static_checks.check_black import BlackArgumentsParser

logger = get_child_logger(__file__)


@handles_console_error()
def run_start(lab_name: str, root_dir: Path) -> tuple[str, str, int]:
    """
    Run start.py script in the specified lab directory.

    Args:
        lab_name (str): Name of the lab directory.

    Returns:
        tuple[str, str, int]: stdout, stderr, exit code
    """
    return _run_console_tool(
        str(choose_python_exe(lab_path=root_dir)),
        [str("start.py")],
        cwd=root_dir / lab_name,
        debug=True,
    )


@handles_console_error()
def check_start_content(lab_name: str, root_dir: Path) -> tuple[str, str, int]:
    """
    Check the content of start.py script using check_start_content.py script.

    Args:
        lab_name (str): Name of the lab directory.

    Returns:
        tuple[str, str, int]: stdout, stderr, exit code
    """
    start_py_file = root_dir / lab_name / "start.py"
    with start_py_file.open() as f:
        start_py_content = f.read()

    return _run_console_tool(
        str(choose_python_exe(lab_path=root_dir)),
        [
            str(Path(PROJECT_ROOT, "check_start_content.py")),
            "--start_py_content",
            start_py_content,
        ],
        cwd=root_dir,
        debug=True,
    )


def main() -> None:
    """
    Main function to run start.py checks for each lab.
    """
    args = BlackArgumentsParser().parse_args()

    root_dir = args.root_dir.resolve()
    toml_config = (args.toml_config_path or (root_dir / "pyproject.toml")).resolve()

    project_config_path = (
        args.project_config_path or (root_dir / "project_config.json")
    ).resolve()

    project_config = ProjectConfig(project_config_path)

    fileConfig(toml_config)
    labs = project_config.get_labs_names()

    for lab_name in labs:
        logger.info(f"Running start.py checks for lab {lab_name}")

        target_score = get_target_score(root_dir / lab_name)

        if target_score == 0:
            logger.info("Skipping stage. Target score is 0.")
            continue
        run_start(lab_name, root_dir=root_dir)

        logger.info(f"Check calling lab {lab_name} passed")

        check_start_content(lab_name, root_dir)

    logger.info("All start.py checks passed.")


if __name__ == "__main__":
    main()
