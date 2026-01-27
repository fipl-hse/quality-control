"""
Run tests for each lab using pytest.
"""

from pathlib import Path

from logging518.config import fileConfig

from quality_control.cli_unifier import (
    _run_console_tool,
    choose_python_exe,
    handles_console_error,
)
from quality_control.collect_coverage.run_coverage import get_target_score
from quality_control.console_logging import get_child_logger
from quality_control.project_config import ProjectConfig
from quality_control.quality_control_parser import QualityControlArgumentsParser

logger = get_child_logger(__file__)


class CommandLineInterface(QualityControlArgumentsParser):
    """
    Types for the argument parser.
    """

    pr_name: str
    pr_author: str
    lab_path: str | None = None
    pytest_label: str | None = None


def prepare_pytest_args(
    lab_path: str,
    target_score: int,
    project_config_path: Path,
    pytest_label: str | None = None,
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
    lab_config = project_config.get_lab(lab_path)

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
    return _run_console_tool(
        str(choose_python_exe(lab_path=root_dir)), args, cwd=root_dir, debug=True
    )


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

    project_config_path = (args.project_config_path or (root_dir / "project_config.json")).resolve()

    fileConfig(toml_config)

    if args.lab_path:
        if check_skip(root_dir=root_dir, lab_path=args.lab_path):
            return
        target_score = get_target_score(root_dir / args.lab_path)
        pytest_args = prepare_pytest_args(
            lab_path=args.lab_path,
            target_score=target_score,
            project_config_path=project_config_path,
            pytest_label=args.pytest_label,
        )

        _, _, return_code = run_pytest(root_dir, pytest_args)
        if return_code == 5:
            logger.info(
                f"This combination of mark and label "
                f"doesn't match any tests for {args.lab_path}."
            )

    else:
        project_config = ProjectConfig(project_config_path)

        logger.info(f"Current scope: {project_config.get_labs()}")

        for lab in project_config.get_labs():
            if check_skip(root_dir=root_dir, lab_path=lab.name):
                continue
            logger.info(f"Running tests for lab {lab.name}")

            target_score = get_target_score(root_dir / lab.name)
            pytest_args = prepare_pytest_args(
                lab_path=lab.name,
                target_score=target_score,
                project_config_path=project_config_path,
            )

            _, _, return_code = run_pytest(root_dir, pytest_args)
            if return_code == 5:
                logger.info(
                    f"This combination of mark and label "
                    f"doesn't match any tests for {lab.name}."
                )

        for addon in project_config.get_addons():
            if not addon.run_tests:
                logger.info(f"Addon {addon.name} does not need to run tests")

            logger.info(f"Running tests for addon {addon.name}")

            pytest_args = prepare_pytest_args(
                lab_path=addon.name,
                target_score=10,
                project_config_path=project_config_path,
            )


if __name__ == "__main__":
    main()
