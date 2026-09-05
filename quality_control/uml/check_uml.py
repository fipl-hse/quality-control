"""
UML Diagram Check for Labs

Check that all labs have up-to-date UML diagrams by comparing SHA256 hashes
of the DOT representation (not PNG).

DOT is generated deterministically from AST (cross-platform identical).

Workflow.
1. For each lab in project_config.json:
   - generate DOT from the committed main.py;
   - copy lab to a temporary directory;
   - generate DOT from the copy;
   - compare SHA256 hashes of DOT strings.
2. Exit with code 0 if all match, 1 otherwise.
"""

import hashlib
import shutil
import sys
import tempfile
from pathlib import Path

from logging518.config import fileConfig

from quality_control.console_logging import get_child_logger
from quality_control.project_config import Lab, ProjectConfig
from quality_control.quality_control_parser import QualityControlArgumentsParser
from quality_control.uml.uml_builder import (
    generate_class_diagram_dot_from_main,
    generate_function_diagram_dot_from_main,
    has_classes_in_main,
)

logger = get_child_logger(__file__)


def compute_dot_hash(dot_content: str) -> str:
    """
    Compute SHA256 hash from DOT string.

    Args:
        dot_content (str): DOT content as string.

    Returns:
        str: SHA256 hex digest.
    """
    return hashlib.sha256(dot_content.encode("utf-8")).hexdigest()


def get_dot_for_lab(lab_path: Path) -> str | None:
    """
    Generate DOT content for a lab based on its main.py.

    Args:
        lab_path (Path): Path to the lab directory.

    Returns:
        str | None: DOT content, or None if main.py is missing/invalid.
    """
    if has_classes_in_main(lab_path):
        return generate_class_diagram_dot_from_main(lab_path)
    return generate_function_diagram_dot_from_main(lab_path)


def check_lab_diagram(lab_info: Lab, root_dir: Path) -> bool:
    """
    Check a single lab's diagram by comparing DOT hashes.

    1. Locates the lab directory based on config info.
    2. Generates DOT from the committed main.py.
    3. Copies lab to a temporary location.
    4. Generates DOT from the copy.
    5. Compares SHA256 hashes.

    Args:
        lab_info (Lab): Lab entry from project_config.json.
        root_dir (Path): Root directory of the project.

    Returns:
        bool: True if hashes match, False if DOT is missing or differs.
    """
    lab_name = lab_info.name
    lab_path = root_dir / lab_name

    main_py = lab_path / "main.py"
    if not main_py.exists():
        logger.error(f"Missing main.py: {main_py}")
        return False

    # Generate DOT from committed code
    committed_dot = get_dot_for_lab(lab_path)
    if committed_dot is None:
        logger.error(f"Failed to generate DOT for committed {lab_name}")
        return False

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_lab = Path(tmp_dir) / lab_name
        shutil.copytree(lab_path, tmp_lab, dirs_exist_ok=True)

        # Generate DOT from temporary copy
        generated_dot = get_dot_for_lab(tmp_lab)
        if generated_dot is None:
            logger.error(f"Failed to generate DOT for temporary {lab_name}")
            return False

        # Compare hashes
        committed_hash = compute_dot_hash(committed_dot)
        generated_hash = compute_dot_hash(generated_dot)

        if committed_hash != generated_hash:
            logger.info(f"Diagram structure differs: {lab_name}")
            logger.info(f"  Committed DOT hash: {committed_hash}")
            logger.info(f"  Generated DOT hash: {generated_hash}")
            return False

        logger.info(f"Diagram structure is up-to-date: {lab_name}")
        return True


def main() -> None:
    """
    Entry point for the UML diagram consistency checker.

    Reads the project configuration from project_config.json,
    iterates over all registered labs, and verifies that each lab's
    UML diagram structure (represented by DOT) is up-to-date.

    Exits with code:
        0 — if all diagrams are present and up-to-date,
        1 — if any diagram is missing, invalid, or outdated.
    """
    args = QualityControlArgumentsParser().parse_args()

    root_dir = args.root_dir.resolve()

    project_config_path = args.project_config_path or (root_dir / "project_config.json")
    project_config_path = project_config_path.resolve()

    toml_config = (args.toml_config_path or (root_dir / "pyproject.toml")).resolve()
    fileConfig(toml_config)

    project_config = ProjectConfig(project_config_path)

    # pylint: disable=protected-access
    all_ok = not any(not check_lab_diagram(lab, root_dir) for lab in project_config._dto.labs)
    # pylint: enable=protected-access

    if not all_ok:
        logger.error("\nTip: Run the UML generator locally"
                     " and commit the updated assets/description.png")
        logger.error("Run: fiplconfig.build_uml")
        sys.exit(1)

    logger.info("\nAll diagrams are present and up-to-date")
    sys.exit(0)


if __name__ == "__main__":
    main()
