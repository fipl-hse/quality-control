"""
Runner for generating and auto-formatting stubs.
"""

from pathlib import Path

from quality_control.cli_unifier import (
    _run_console_tool,
    choose_python_exe,
    handles_console_error,
)
from quality_control.console_logging import get_child_logger

logger = get_child_logger(__file__)


@handles_console_error()
def remove_implementation(
    source_code_path: Path,
    res_stub_path: Path,
    root_dir: Path,
    project_config_path: Path,
) -> None:
    """
    Wrapper for implementation removal from a listing.

    Args:
        source_code_path (Path): Path to source code
        res_stub_path (Path): Path to resulting stub
        root_dir (Path): Root directory
        project_config_path (Path): Path to project configuration file
    """
    stub_generator_path = Path(__file__).parent / "generator.py"
    args = [
        str(stub_generator_path),
        "--source_code_path",
        str(source_code_path),
        "--target_code_path",
        str(res_stub_path),
        "--project_config_path",
        str(project_config_path),
    ]
    _run_console_tool(str(choose_python_exe(lab_path=root_dir)), args, debug=False)


@handles_console_error()
def format_stub_file(res_stub_path: Path, root_dir: Path) -> tuple[str, str, int]:
    """
    Autoformat resulting stub.

    Args:
        res_stub_path (Path): Path to resulting path.
        root_dir (Path): Root directory

    Returns:
        tuple[str, str, int]: stdout, stderr, exit code
    """
    args = ["-m", "black", "-l", "100", str(res_stub_path)]

    return _run_console_tool(str(choose_python_exe(lab_path=root_dir)), args, debug=False)


@handles_console_error()
def sort_stub_imports(res_stub_path: Path) -> tuple[str, str, int]:
    """
    Autoformat resulting stub.

    Args:
        res_stub_path (Path): Path to resulting stub.

    Returns:
        tuple[str, str, int]: stdout, stderr, exit code
    """
    args = [str(res_stub_path)]

    return _run_console_tool("isort", args, debug=False)
