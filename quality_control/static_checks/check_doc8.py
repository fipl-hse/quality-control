"""
Check doc8 for style checking of rst files.
"""

from pathlib import Path

from logging518.config import fileConfig

from quality_control.cli_unifier import (_run_console_tool, choose_python_exe,
                                         handles_console_error)
from quality_control.console_logging import get_child_logger
from quality_control.project_config import ProjectConfig
from quality_control.static_checks.check_black import BlackArgumentsParser

logger = get_child_logger(__file__)


@handles_console_error()
def check_doc8_on_paths(
    paths: list[Path], path_to_config: Path, python_exe: Path, root_dir: Path
) -> tuple[str, str, int]:
    """
    Run doc8 checks for the project.

    Args:
        paths (list[Path]): List of RST files.
        path_to_config (Path): Path to the config file.
        python_exe (Path): Python executable to run Doc8.
        root_dir (Path): Root directory for running doc8.

    Returns:
        tuple[str, str, int]: stdout, stderr, exit code.
    """
    if not paths:
        logger.info("No .rst files found, skipping doc8.")
        return "", "", 0

    doc8_args = [
        "-m",
        "doc8",
        *map(str, filter(lambda x: x.exists(), paths)),
        "--config",
        str(path_to_config),
    ]
    return _run_console_tool(str(python_exe), doc8_args, debug=True, cwd=root_dir)


def main() -> None:
    args = BlackArgumentsParser().parse_args()

    root_dir = args.root_dir.resolve()
    toml_config = (args.toml_config_path or (root_dir / "pyproject.toml")).resolve()
    project_config_path = (
        args.project_config_path or (root_dir / "project_config.json")
    ).resolve()

    project_config = ProjectConfig(project_config_path)
    fileConfig(toml_config)

    python_exe = choose_python_exe(lab_path=root_dir)
    labs_list = project_config.get_labs_paths(root_dir=root_dir)

    logger.info("Running doc8 for main docs")
    rst_main_files = list(root_dir.glob("*rst"))
    check_doc8_on_paths(
        paths=rst_main_files,
        path_to_config=toml_config,
        python_exe=python_exe,
        root_dir=root_dir,
    )

    logger.info("Running doc8 for other docs")
    docs_path = root_dir / "docs"
    rst_files = list(docs_path.rglob("*.rst"))

    check_doc8_on_paths(
        paths=rst_files,
        path_to_config=toml_config,
        python_exe=python_exe,
        root_dir=root_dir,
    )

    for lab_name in labs_list:
        lab_path = root_dir / lab_name
        rst_labs_files = list(lab_path.rglob("*.rst"))
        logger.info(f"Running doc8 for lab {lab_path}")
        check_doc8_on_paths(
            paths=rst_labs_files,
            path_to_config=toml_config,
            python_exe=python_exe,
            root_dir=root_dir,
        )


if __name__ == "__main__":
    main()
