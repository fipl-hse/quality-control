"""
Check spelling in project files.
"""

import re
import sys
from pathlib import Path
from typing import Pattern

from logging518.config import fileConfig

from quality_control.cli_unifier import (
    _run_console_tool,
    choose_python_exe,
    handles_console_error,
)
from quality_control.console_logging import get_child_logger
from quality_control.constants import PROJECT_ROOT
from quality_control.static_checks.check_black import QualityControlArgumentsParser

logger = get_child_logger(__file__)


@handles_console_error(ok_codes=(0, 1))
def check_spelling_on_paths(task: str, root_dir: Path) -> tuple[str, str, int]:
    """
    Run spelling checks on paths.

    Returns:
        tuple[str, str, int]: stdout, stderr, exit code
    """
    spelling_args = ["-m", "pyspelling", "-c", "config/spellcheck/.spellcheck.yaml", "-n", task]

    return _run_console_tool(
        str(choose_python_exe(lab_path=root_dir)),
        spelling_args,
        debug=True,
        cwd=root_dir,
    )


def get_misspelled_from_stdout(
    stdout: str, additional_re_check: Pattern | None = None
) -> set[str]:
    """
    Get words from the blocks of pyspelling output.

    Args:
        stdout (str): stdout log

    Returns:
        set[str]: set of misspelled words
    """
    pattern = re.compile(
        r"Misspelled words:\n<[a-zA-Z_-]+> .*: .*\n-+(?P<wrong>(([а-яА-ЯёЁa-zA-Z\-]{1,})\n?)+)"
    )

    all_misses = set()
    logger.info("Parsing words from the log.")
    for found in pattern.finditer(stdout):
        all_misses.update(
            [
                word.lower()
                for word in found.group("wrong").strip().split("\n")
                if word and len(word) != 80
            ]
        )
    if additional_re_check is None:
        return all_misses

    return {word for word in all_misses if additional_re_check.search(word)}


def main() -> None:
    """
    Run spellchecking for the project.
    """

    russian_word_p = re.compile(r"[а-яА-ЯёЁ]+")
    english_word_p = re.compile(r"[a-zA-Z]+")

    args = QualityControlArgumentsParser(underscores_to_dashes=True).parse_args()

    root_dir = args.root_dir.resolve()
    toml_config = (args.toml_config_path or (root_dir / "pyproject.toml")).resolve()

    fileConfig(toml_config)

    stdout, _, return_code = check_spelling_on_paths(task="ru", root_dir=root_dir)
    missed_russian = (
        set(get_misspelled_from_stdout(stdout, russian_word_p))
        if return_code
        else set()
    )

    stdout, _, return_code = check_spelling_on_paths(task="en", root_dir=root_dir)
    missed_english = (
        set(get_misspelled_from_stdout(stdout, english_word_p))
        if return_code
        else set()
    )

    stdout, _, return_code = check_spelling_on_paths(task="docstrings", root_dir=root_dir)
    missed_docstrings = (
        set(get_misspelled_from_stdout(stdout)) if return_code else set()
    )

    if not missed_docstrings and not missed_russian and not missed_english:
        logger.info("Spelling: OK")
        sys.exit(0)

    if missed_english or missed_russian:
        logger.info("List of potentially wrong words in docs:")
        logger.info("\n\n" + "\n".join(sorted(missed_english | missed_russian)) + "\n")

    if missed_docstrings:
        logger.info("List of potentially wrong words in docstrings:")
        logger.info("\n\n" + "\n".join(sorted(missed_docstrings)) + "\n")

    logger.error("Spelling: FAIL")
    sys.exit(1)


if __name__ == "__main__":
    main()
