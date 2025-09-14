"""
Run tests for each lab using pytest.
"""

import os
from pathlib import Path
from typing import Optional
from tap import Tap

from quality_control.cli_unifier import _run_console_tool, choose_python_exe, handles_console_error
from quality_control.collect_coverage.run_coverage import get_target_score
from quality_control.console_logging import get_child_logger
from quality_control.constants import PROJECT_CONFIG_PATH, PROJECT_ROOT
from quality_control.project_config import ProjectConfig
from logging518.config import fileConfig

logger = get_child_logger(__file__)


class CommandLineInterface(Tap):
    """
    Types for the argument parser.
    """

    pr_name: str
    pr_author: str
    lab_path: str | None = None
    pytest_label: str | None = None
    toml_config_path: Optional[Path] = None
    root_dir: Optional[Path] = Path(os.getcwd())
    project_config_path: Optional[Path] = None


def prepare_pytest_args(
    lab_path: str, target_score: int, project_config_path: Path, pytest_label: str | None = None, 
) -> list[str]:
    """
    Build the arguments for running pytest.

    Args:
        lab_path (str): Path to the lab.
        target_score (int): Target score for the lab.
        pytest_label (str | None): Label for pytest.

    Returns:
        list[str]: List of arguments for pytest.
    """
    if pytest_label is None:
        pytest_label = lab_path

    project_config = ProjectConfig(project_config_path)
    lab_config = project_config.get_lab_config(lab_path)

    pytest_args = [
        "-m",
        f"mark{target_score} and {pytest_label}" if lab_path else pytest_label,
        "--capture=no",
    ]
    if lab_config and lab_config.settings:
        if ignored_folders := lab_config.settings.ignore:
            pytest_args.extend(f"--ignore={folder}" for folder in ignored_folders)

    logger.info(pytest_args)
    return pytest_args


@handles_console_error(ok_codes=(0, 5))
def run_pytest(root_dir: Path, pytest_args: list[str]) -> tuple[str, str, int]:
    """
    Run pytest with the given arguments.

    Args:
        pytest_args (list[str]): Arguments for pytest.

    Returns:
        tuple[str, str, int]: stdout, stderr, exit code
    """
    args = ["-m", "pytest", *pytest_args]
    return _run_console_tool(str(choose_python_exe(lab_path=root_dir)), args, cwd=root_dir, debug=True)


def check_skip(root_dir: Path, lab_path: str) -> bool:
    """
    Exit if skip conditions are met.

    Args:
        lab_path (str): Path to the lab.

    Returns:
        bool: True if should be skipped
    """
    if lab_path:
        score_path = root_dir / lab_path
        score = get_target_score(lab_path=score_path)
        if score == 0:
            logger.info(f"Skipping check due to no mark for lab {lab_path}.")
            return True

    logger.info(f"No special reasons for skipping {lab_path}!")
    return False


def main() -> None:
    """
    Main function to run tests for only one lab or for one by one.
    """
    args = CommandLineInterface(underscores_to_dashes=True).parse_args()

    root_dir = args.root_dir.resolve()
    toml_config = (args.toml_config_path or (root_dir / "pyproject.toml")).resolve()

    project_config_path = (
        args.project_config_path or (root_dir / "project_config.json")
    ).resolve()

    fileConfig(toml_config)

    if args.lab_path:
        if check_skip(root_dir=root_dir, lab_path=args.lab_path):
            return
        target_score = get_target_score(root_dir / args.lab_path)
        pytest_args = prepare_pytest_args(lab_path=args.lab_path, target_score=target_score, project_config_path=project_config_path, pytest_label=args.pytest_label)

        _, _, return_code = run_pytest(root_dir, pytest_args)
        if return_code == 5:
            logger.info(
                f"This combination of mark and label "
                f"doesn't match any tests for {args.lab_path}."
            )

    else:
        project_config = ProjectConfig(project_config_path)
        labs = project_config.get_labs_names()

        logger.info(f"Current scope: {labs}")

        for lab_name in labs:
            if check_skip(root_dir=root_dir, lab_path=lab_name):
                continue
            logger.info(f"Running tests for lab {lab_name}")

            target_score = get_target_score(root_dir / lab_name)
            pytest_args = prepare_pytest_args(lab_path=lab_name, target_score=target_score, project_config_path=project_config_path)

            _, _, return_code = run_pytest(root_dir, pytest_args)
            if return_code == 5:
                logger.info(
                    f"This combination of mark and label "
                    f"doesn't match any tests for {lab_name}."
                )


if __name__ == "__main__":
    main()
