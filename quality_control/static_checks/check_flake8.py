"""
Check flake8 to check the style and quality of Python code.
"""

# pylint: disable=duplicate-code
from os import listdir
from pathlib import Path

from logging518.config import fileConfig

from quality_control.cli_unifier import (
    _run_console_tool,
    choose_python_exe,
    handles_console_error,
)
from quality_control.console_logging import get_child_logger
from quality_control.constants import PROJECT_ROOT
from quality_control.lab_settings import LabSettings
from quality_control.project_config import ProjectConfig
from quality_control.static_checks.check_black import QualityControlArgumentsParser

logger = get_child_logger(__file__)


@handles_console_error()
def check_flake8_on_paths(
    paths: list[Path],
    root_dir: Path,
) -> tuple[str, str, int]:
    """
    Run flake8 checks for the project.

    Args:
        paths (list[Path]): Paths to the projects.

    Returns:
        tuple[str, str, int]: stdout, stderr, exit code
    """
    flake_args = ["-m", "flake8", *map(str, filter(lambda x: x.exists(), paths))]

    return _run_console_tool(str(choose_python_exe(lab_path=root_dir)), flake_args, debug=True, cwd=root_dir)


def main() -> None:
    """
    Run flake8 checks for the project.
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

    logger.info(f"Running flake8 on {' '.join(addons)}")
    check_flake8_on_paths(
        [root_dir / addon for addon in addons], root_dir=root_dir
    )

    if (root_dir / "core_utils").exists():
        logger.info("core_utils exist")
        check_flake8_on_paths(
            [root_dir / "core_utils"], root_dir=root_dir
        )

    for lab_name in labs_list:
        lab_path = root_dir / lab_name
        if "settings.json" in listdir(lab_path):
            target_score = LabSettings(
                PROJECT_ROOT / f"{lab_path}/settings.json"
            ).target_score

            if target_score > 5:
                logger.info(f"Running flake8 for lab {lab_path}")
                check_flake8_on_paths(
                    [lab_path], root_dir=root_dir
                )


if __name__ == "__main__":
    main()
