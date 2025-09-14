"""
Check spelling in project files.
"""

from importlib.resources import files
import os
from pathlib import Path
import re
import sys

from quality_control.cli_unifier import _run_console_tool, choose_python_exe, handles_console_error
from quality_control.console_logging import get_child_logger

from logging518.config import fileConfig
from quality_control import spellcheck
from quality_control.constants import PROJECT_ROOT
from quality_control.static_checks.check_black import BlackArgumentsParser

logger = get_child_logger(__file__)


@handles_console_error(ok_codes=(0, 1))
def check_spelling_on_paths(root_dir: Path) -> tuple[str, str, int]:
    """
    Run spelling checks on paths.

    Returns:
        tuple[str, str, int]: stdout, stderr, exit code
    """
    spelling_args = ["-m", "pyspelling", "-c", f"{PROJECT_ROOT}/spellcheck/.spellcheck.yaml", "-v"]

    return _run_console_tool(str(choose_python_exe(lab_path=root_dir)), spelling_args, debug=True, cwd=root_dir)


def main() -> None:
    """
    Run spellchecking for the project.
    """

    SPELLCHECK_DIR = files(spellcheck)
    os.environ["SPELLCHECK_DIR"] = str(SPELLCHECK_DIR)
    args = BlackArgumentsParser().parse_args()

    root_dir = args.root_dir.resolve()
    toml_config = (args.toml_config_path or (root_dir / "pyproject.toml")).resolve()

    fileConfig(toml_config)

    stdout, _, return_code = check_spelling_on_paths(root_dir=root_dir)
    if return_code == 0:
        logger.info("Spelling check is passed.")
        sys.exit(0)

    pattern = re.compile(
        r"Misspelled words:\n<htmlcontent>[ a-zA-Z_\/\.0-9]+:\s([a-zA-Z\.0-9]+>?)+\n-+\n"
        r"(?P<wrong>(([а-яА-ЯёЁa-zA-Z\-]{1,})\n?)+)"
    )

    final = []
    for found in pattern.finditer(stdout):
        final.extend(
            [
                word.lower()
                for word in found.group("wrong").strip().split("\n")
                if word and len(word) != 80
            ]
        )
    missed = sorted(set(final))

    if missed:
        logger.info("List of potentially wrong words:")
        logger.info("\n\n" + "\n".join(missed))

    logger.error("Spellcheck is not passed.")
    sys.exit(1)


if __name__ == "__main__":
    main()
