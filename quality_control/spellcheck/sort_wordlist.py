"""
Module to check if wordlist is properly sorted.
"""

import re
from pathlib import Path

from logging518.config import fileConfig

from quality_control.console_logging import get_child_logger
from quality_control.quality_control_parser import QualityControlArgumentsParser

logger = get_child_logger(__file__)


def check_wordlist(wordlist_path: Path) -> None:
    """
    Check that wordlist is properly sorted.

    Args:
        wordlist_path (Path): Path to wordlist
    """
    with open(wordlist_path, encoding="utf-8") as f:
        original_text = f.read()
        words = [i.strip().lower() for i in original_text.split("\n") if i.strip()]

    russian_letters_pattern = re.compile(r"[а-я]+", re.IGNORECASE)
    russian_words = [i for i in words if russian_letters_pattern.match(i)]
    english_words = list(set(words) - set(russian_words))
    new_content = "\n".join(
        sorted(russian_words)
        + sorted(english_words)
        + [
            "",
        ]
    )

    are_same = original_text == new_content
    logger.info(f"Wordlist {wordlist_path} is sorted well: {are_same}")

    if are_same:
        return

    logger.info(f"Writing new content for {wordlist_path}")
    with open(wordlist_path, "w", encoding="utf-8") as f:
        f.write(new_content)


def main() -> None:
    """
    Call functions.
    """
    args = QualityControlArgumentsParser(underscores_to_dashes=True).parse_args()

    root_dir = args.root_dir.resolve()
    toml_config = (args.toml_config_path or (root_dir / "pyproject.toml")).resolve()
    fileConfig(toml_config)

    main_wordlist_path = root_dir / "admin_utils" / "spellcheck" / ".wordlist.txt"
    secondary_wordlist_path = (
        root_dir / "admin_utils" / "spellcheck" / ".wordlist_en.txt"
    )

    for current_path in (main_wordlist_path, secondary_wordlist_path):
        if current_path.exists():
            check_wordlist(current_path)


if __name__ == "__main__":
    main()
