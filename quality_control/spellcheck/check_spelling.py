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
from quality_control.quality_control_parser import QualityControlArgumentsParser

logger = get_child_logger(__file__)


@handles_console_error(ok_codes=(0, 1))
def check_spelling_on_paths(task: str, root_dir: Path) -> tuple[str, str, int]:
    """
    Run spelling checks on paths.

    Returns:
        tuple[str, str, int]: stdout, stderr, exit code
    """
    spelling_args = [
        "-m",
        "quality_control.spellcheck.run_pyspelling",
        "-c",
        f"{root_dir}/admin_utils/spellcheck/.spellcheck.yaml",
        "-n",
        task,
    ]

    return _run_console_tool(
        str(choose_python_exe(lab_path=root_dir)),
        spelling_args,
        debug=True,
        cwd=root_dir,
    )


def run_spelling_check(
    task: str,
    root_dir: Path,
    word_pattern: Pattern | None = None,
) -> tuple[set[str], str, int]:
    """
    Run spelling check for a task.

    Returns:
        tuple[set[str], str, int]: missed words, stderr, exit code
    """
    stdout, stderr, return_code = check_spelling_on_paths(
        task=task,
        root_dir=root_dir,
    )

    missed_words = (
        get_misspelled_from_stdout(stdout, word_pattern) if return_code in (0, 1) else set()
    )

    return missed_words, stderr, return_code


def get_misspelled_from_stdout(stdout: str, additional_re_check: Pattern | None = None) -> set[str]:
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


def check_spelling_result(
    task: str,
    result: tuple[set[str], str, int],
) -> set[str]:
    """Validate spelling check result and return missed words."""
    missed_words, stderr, return_code = result

    if return_code not in (0, 1):
        logger.error(
            f"{task.capitalize()} spelling check failed to run. "
            f"Exit code: {return_code}. Error: {stderr}"
        )
        sys.exit(1)

    return missed_words


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

    missed_russian = check_spelling_result(
        "Russian",
        run_spelling_check("ru", root_dir, russian_word_p),
    )

    missed_english = check_spelling_result(
        "English",
        run_spelling_check("en", root_dir, english_word_p),
    )

    missed_docstrings = check_spelling_result(
        "Docstring",
        run_spelling_check("docstrings", root_dir),
    )

    missed_docs = missed_russian & missed_english

    if missed_docs:
        logger.info("List of potentially wrong words in docs:")
        logger.info("\n\n" + "\n".join(sorted(missed_docs)) + "\n")

    if missed_docstrings:
        logger.info("List of potentially wrong words in docstrings:")
        logger.info("\n\n" + "\n".join(sorted(missed_docstrings)) + "\n")

    if not missed_docs and not missed_docstrings:
        logger.info("Spelling: OK")
        sys.exit(0)

    logger.error("Spelling: FAIL")
    sys.exit(1)


if __name__ == "__main__":
    main()
