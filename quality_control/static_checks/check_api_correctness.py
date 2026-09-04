"""
Check and validate that the generated lab stubs remain unchanged.
"""

# pylint: disable=too-many-locals
import sys

from logging518.config import fileConfig

from quality_control.console_logging import get_child_logger
from quality_control.generate_stubs.generator import cleanup_code
from quality_control.project_config import ProjectConfig
from quality_control.quality_control_parser import QualityControlArgumentsParser

logger = get_child_logger(__file__)


def main() -> None:
    """
    Check the stubs correctness
    """
    args = QualityControlArgumentsParser(underscores_to_dashes=True).parse_args()

    root_dir = args.root_dir.resolve()
    toml_config = (args.toml_config_path or (root_dir / "pyproject.toml")).resolve()

    project_config = ProjectConfig(
        (args.project_config_path or (root_dir / "project_config.json")).resolve()
    )

    fileConfig(toml_config)

    passed_files = []
    failed_files = []

    for lab_path in project_config.get_labs_paths(root_dir=root_dir):
        lab_name = lab_path.name
        lab_config = project_config.get_lab(lab_name)

        for impl_file in lab_config.stubs:
            file_is_correct = True
            impl_path = lab_path / impl_file

            if not impl_path.exists():
                logger.error(f"Missing implementation file: {impl_path.relative_to(root_dir)}")
                file_is_correct = False

            reference_path = lab_path / f"{impl_path.stem}_stub.py"

            if not reference_path.exists():
                logger.error(f"Missing reference file: {reference_path.relative_to(root_dir)}")
                file_is_correct = False

            expected_code = cleanup_code(reference_path, project_config)
            current_code = cleanup_code(impl_path, project_config)

            if expected_code != current_code:
                logger.error(
                    "Mismatch between "
                    f"{impl_path.relative_to(root_dir)} and "
                    f"{reference_path.relative_to(root_dir)}"
                )
                file_is_correct = False

            if file_is_correct:
                passed_files.append(impl_file)
            else:
                failed_files.append(impl_file)

    if failed_files:
        logger.error(f"Failed files: {failed_files}")
        sys.exit(1)

    logger.info("All stubs are relevant")
    sys.exit(0)


if __name__ == "__main__":
    main()
