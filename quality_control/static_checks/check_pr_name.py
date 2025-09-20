"""
Module for PR name check.
"""

# pylint: skip-file
import os
import re
import sys
from pathlib import Path
from re import Pattern
from typing import Optional

from logging518.config import fileConfig
from tap import Tap

from quality_control.console_logging import get_child_logger
from quality_control.project_config import ProjectConfig

logger = get_child_logger(__file__)


class CheckPrNameArguments(Tap):
    pr_name: str
    pr_author: str
    toml_config_path: Optional[Path] = None
    root_dir: Optional[Path] = Path(os.getcwd())
    project_config_path: Optional[Path] = None


def convert_raw_pr_name(pr_name_raw: str) -> str:
    """
    Convert raw PR name.

    Args:
        pr_name_raw (str): Raw PR name

    Returns:
        str: Processed PR name
    """
    return pr_name_raw.replace("_", " ")


def is_matching_name(
    pr_name: str, compiled_pattern: Pattern, example_name: str
) -> bool:
    """
    Determine whether name is matching.

    Args:
        pr_name (str): PR name
        compiled_pattern (Pattern): Compiled pattern
        example_name (str): Example name

    Returns:
        bool: Is name matching or not
    """
    if not re.search(compiled_pattern, pr_name):
        logger.error(
            f"Your Pull Request title does not confirm to the template.\n{example_name}\n\n"
        )
        return False

    logger.info("Your Pull Request name confirms to provided template.")
    return True


def is_author_admin(author_login: str, project_config: ProjectConfig) -> bool:
    """
    Determine whether author is admin.

    Args:
        author_login (str): Author login
        project_config (ProjectConfig): Project config

    Returns:
        bool: Is author admin or not
    """
    admins_logins = project_config.get_admins()

    return author_login in admins_logins


def main() -> None:
    args = CheckPrNameArguments().parse_args()
    root_dir = args.root_dir.resolve()
    project_config_path = (
        args.project_config_path or (root_dir / "project_config.json")
    ).resolve()
    toml_config = (args.toml_config_path or (root_dir / "pyproject.toml")).resolve()

    project_config = ProjectConfig(project_config_path)
    fileConfig(toml_config)

    if is_author_admin(args.pr_author, project_config):
        logger.info("Skipping PR name checks due to author.")
        sys.exit(0)

    pr_name = convert_raw_pr_name(args.pr_name)

    compiled_pattern = project_config.get_pr_name_regex()
    example_name = project_config.get_pr_name_example()

    sys.exit(not is_matching_name(pr_name, compiled_pattern, example_name))


if __name__ == "__main__":
    main()
