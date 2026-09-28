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
        "pyspelling",
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

    all_missed = set()
    for task in ("ru", "en", "docstrings"):
        logger.info(f"Running spellcheck for {task=}")
        stdout, stderr, return_code = check_spelling_on_paths(task=task, root_dir=root_dir)
        if not stdout and stderr:
            logger.error(
                "Spelling: FAIL due to a problem unrelated to spelling correctness. "
                "Maybe there is a problem in config"
            )
            sys.exit(1)
        pattern = russian_word_p if task == "ru" else english_word_p if task == "en" else None
        missed = set(get_misspelled_from_stdout(stdout, pattern)) if return_code else set()
        if sys.platform == "darwin":
            missed = {i for i in missed if "ё" not in i}
        all_missed |= missed

    if not all_missed:
        logger.info("Spelling: OK")
        sys.exit(0)

    logger.info("List of potentially wrong words:")
    logger.info(f"\n\n{'\n'.join(sorted(all_missed))}\n")
    logger.error("Spelling: FAIL")
    sys.exit(1)


if __name__ == "__main__":
    main()
