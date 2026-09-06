"""
Check that all labs have up-to-date UML diagrams by comparing SHA256 hashes
of the committed PNG file and a freshly generated PNG in isolation.

This ensures binary identity of diagram images — any difference in rendering,
Graphviz version, or layout will cause the check to fail.

Workflow.
1. For each lab in project_config.json:
   - copy lab to a temporary directory;
   - generate a fresh description.png using the current code;
   - compute SHA256 hash of both the committed and generated PNG;
   - compare the hashes.
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
from quality_control.uml.uml_builder import generate_uml_diagrams

logger = get_child_logger(__file__)


def compute_png_hash(png_path: Path) -> str:
    """
    Compute a deterministic SHA256 hash from PNG.

    Args:
        png_path (Path): Path to the PNG file.

    Returns:
        str: SHA256 hex digest from PNG.
    """
    return hashlib.sha256(png_path.read_bytes()).hexdigest()


def check_lab_diagram(lab_info: Lab, root_dir: Path) -> bool:
    """
    Check a single lab's diagram by comparing PNG hashes.

    1. Locates the lab directory based on config info.
    2. Copies it to a temporary location to avoid side effects.
    3. Generates a fresh description.png from current code.
    4. Compares SHA256 hash of the committed PNG with the generated one.

    Args:
        lab_info (Lab): Lab entry from project_config.json.
        root_dir (Path): Root directory of the project (parent of lab folders).

    Returns:
        bool: True if hashes match, False if PNG is missing, generation fails,
            or hashes differ.
    """
    lab_name = lab_info.name
    lab_path = root_dir / lab_name

    committed_png = lab_path / "assets" / "description.png"
    if not committed_png.is_file():
        logger.error(f"Missing committed diagram: {committed_png}")
        return False

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_lab = Path(tmp_dir) / lab_name
        shutil.copytree(lab_path, tmp_lab, dirs_exist_ok=True)

        # Generate fresh PNG in tmp_lab/assets/
        if not generate_uml_diagrams(tmp_lab):
            logger.error(f"Failed to generate diagram for {lab_name}")
            return False

        generated_png = tmp_lab / "assets" / "description.png"
        if not generated_png.exists():
            logger.error(f"Generated PNG not found: {generated_png}")
            return False

        # Compare hashes of the two PNG files
        committed_hash = compute_png_hash(committed_png)
        generated_hash = compute_png_hash(generated_png)

        if committed_hash != generated_hash:
            logger.info(f"Diagram image differs: {committed_png}")

            logger.info(f"  Committed PNG size: {committed_png.stat().st_size} bytes")
            logger.info(f"  Generated PNG size: {generated_png.stat().st_size} bytes")
            committed_hash = compute_png_hash(committed_png)
            generated_hash = compute_png_hash(generated_png)
            logger.info(f"  Committed hash: {committed_hash}")
            logger.info(f"  Generated hash: {generated_hash}")

            return False

        logger.info(f"Diagram image is up-to-date: {lab_name}")
        return True


def main() -> None:
    """
    Entry point for the UML diagram consistency checker.

    Reads the project configuration from project_config.json,
    iterates over all registered labs, and verifies that each lab's
    UML diagram (represented by assets/diagram.hash) is up-to-date
    with the current source code.

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
        logger.error(
            "\nTip: Run the UML generator locally and commit the updated assets/description.png"
        )
        logger.error("Run: fiplconfig.build_uml")
        sys.exit(1)

    logger.info("\nAll diagrams are present and up-to-date")
    sys.exit(0)


if __name__ == "__main__":
    main()
