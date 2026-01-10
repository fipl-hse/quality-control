"""
Check docstrings for conformance to the Google-style-docstrings.
"""

from pathlib import Path

from logging518.config import fileConfig

from quality_control.cli_unifier import _run_console_tool, handles_console_error
from quality_control.console_logging import get_child_logger
from quality_control.constants import PROJECT_ROOT
from quality_control.static_checks.check_black import QualityControlArgumentsParser

logger = get_child_logger(__file__)


@handles_console_error()
def check_with_pydoctest(path_to_config: Path, root_dir: Path) -> tuple[str, str, int]:
    """
    Check docstrings in files with pydoctest module.

    Args:
        path_to_config (Path): Path to pydoctest config

    Returns:
        tuple[str, str, int]: stdout, stderr, exit code
    """
    pydoctest_args = ["--config", str(path_to_config)]
    return _run_console_tool("pydoctest", pydoctest_args, debug=True, cwd=root_dir)


def main() -> None:
    """
    Check docstrings for labs, config and core_utils packages.
    """
    args = QualityControlArgumentsParser(underscores_to_dashes=True).parse_args()

    root_dir = args.root_dir.resolve()

    pydoctest_path = (
        (root_dir / "pydoctest.json") or (PROJECT_ROOT / "static_checks" / "pydoctest.json")
    ).resolve()
    if args.project_config_path:
        pydoctest_path = args.project_config_path.resolve()

    toml_config = (args.toml_config_path or (root_dir / "pyproject.toml")).resolve()
    fileConfig(toml_config)

    check_with_pydoctest(path_to_config=pydoctest_path, root_dir=root_dir)


if __name__ == "__main__":
    main()
