"""
Check docstrings for conformance to the Google-style-docstrings.
"""

from pathlib import Path

from quality_control.cli_unifier import _run_console_tool, choose_python_exe, handles_console_error
from quality_control.console_logging import get_child_logger
from quality_control.static_checks.check_black import BlackArgumentsParser

logger = get_child_logger(__file__)


@handles_console_error()
def check_with_pydoctest(path_to_config: Path, python_exe: Path, root_dir: Path) -> tuple[str, str, int]:
    """
    Check docstrings in files with pydoctest module.

    Args:
        path_to_config (Path): Path to pydoctest config

    Returns:
        tuple[str, str, int]: stdout, stderr, exit code
    """
    pydoctest_args = ["-m", "pydoctest", "--config", str(path_to_config), "--verbosity", "2"]
    return _run_console_tool(str(python_exe), pydoctest_args, debug=True, cwd=root_dir)



def main() -> None:
    """
    Check docstrings for labs, config and core_utils packages.
    """
    args = BlackArgumentsParser().parse_args()

    root_dir = args.root_dir.resolve()
    project_config_path = (
        args.project_config_path or (root_dir / "project_config.json")
    ).resolve()

    python_exe = choose_python_exe(lab_path=root_dir)

    check_with_pydoctest(
        path_to_config=project_config_path,
        python_exe=python_exe,
        root_dir=root_dir)


if __name__ == "__main__":
    main()
