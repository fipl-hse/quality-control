"""
Install GitHub CLI using the script shipped with quality_control.
"""

from pathlib import Path

from quality_control.cli_unifier import _run_console_tool, handles_console_error

SETUP_CLI_SCRIPT = Path(__file__).parent / "setup_cli.sh"


@handles_console_error()
def run_setup_cli() -> tuple[str, str, int]:
    """
    Run setup_cli.sh bundled with quality_control.

    Returns:
        tuple[str, str, int]: stdout, stderr, exit code
    """
    return _run_console_tool("bash", [str(SETUP_CLI_SCRIPT)])


def main() -> None:
    """
    Entry point: install GitHub CLI
    """
    run_setup_cli()


if __name__ == "__main__":
    main()
