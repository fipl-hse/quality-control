"""
Check mypy for type checking in Python code.
"""

from os import listdir
from pathlib import Path

# pylint: disable=duplicate-code
from logging518.config import fileConfig

from quality_control.cli_unifier import (
    _run_console_tool,
    choose_python_exe,
    handles_console_error,
)
from quality_control.console_logging import get_child_logger
from quality_control.lab_settings import LabSettings
from quality_control.project_config import ProjectConfig
from quality_control.static_checks.check_black import QualityControlArgumentsParser

logger = get_child_logger(__file__)


@handles_console_error()
def check_mypy_on_paths(
    paths: list[Path], path_to_config: Path, root_dir: Path
) -> tuple[str, str, int]:
    """
    Run mypy checks for the project.

    Args:
        paths (list[Path]): Paths to the projects.
        path_to_config (Path): Path to the config.

    Returns:
        tuple[str, str, int]: stdout, stderr, exit code
    """
    mypy_args = [
        "-m",
        "mypy",
        *map(str, filter(lambda x: x.exists(), paths)),
        "--config-file",
        str(path_to_config),
    ]

    return _run_console_tool(str(choose_python_exe(lab_path=root_dir)), mypy_args, debug=True, cwd=root_dir)


def main() -> None:
    """
    Run mypy checks for the project.
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

    if addons:
        logger.info(f"Running mypy on {' '.join(addons)}")
        check_mypy_on_paths(
            [root_dir / addon for addon in addons],
            toml_config,
            root_dir=root_dir,
        )
    print(f"ROOT DIRI: {root_dir}")
    for lab_name in labs_list:
        lab_path = root_dir / lab_name
        if "settings.json" in listdir(lab_path):
            target_score = LabSettings(
                root_dir / f"{lab_path}/settings.json"
            ).target_score

            if target_score > 7:
                logger.info(f"Running mypy for lab {lab_path}")
                check_mypy_on_paths(
                    [lab_path], toml_config, root_dir=root_dir
                )


if __name__ == "__main__":
    main()
