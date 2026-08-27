"""
Check and validate that the generated lab stubs remain unchanged.
"""

# pylint: disable=too-many-locals
import sys
from pathlib import Path

from quality_control.generate_stubs.generator import cleanup_code
from quality_control.project_config import ProjectConfig
from quality_control.static_checks.check_black import QualityControlArgumentsParser


def main() -> None:
    """
    Check the stubs correctness
    """
    args = QualityControlArgumentsParser()

    root_dir = args.root_dir.resolve()

    project_config = ProjectConfig(
        (args.project_config_path or (root_dir / "project_config.json")).resolve()
    )

    code_is_equal = True

    for lab_path in project_config.get_labs_paths(root_dir=root_dir):
        if not code_is_equal:
            break

        lab_name = lab_path.name
        lab_config = project_config.get_lab(lab_name)

        for impl_file in lab_config.stubs:
            impl_path = lab_path / impl_file

            if not impl_path.exists():
                print(f"Missing implementation file: {impl_path}")
                code_is_equal = False
                continue

            reference_path = lab_path / f"{ Path(impl_file).stem}_stub.py"

            if not reference_path.exists():
                print(f"Missing reference file: {reference_path}")
                code_is_equal = False
                continue

            expected_code = cleanup_code(reference_path, project_config, exclude_imports=True)
            current_code = cleanup_code(impl_path, project_config, exclude_imports=True)

            if expected_code != current_code:
                print(
                    "mismatch",
                    impl_path,
                    reference_path,
                )
                code_is_equal = False

    if code_is_equal:
        print("All stubs are relevant")
    sys.exit(not code_is_equal)


if __name__ == "__main__":
    main()
