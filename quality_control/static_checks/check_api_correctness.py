"""
Check and validate that the generated lab stubs remain unchanged.
"""

# pylint: disable=too-many-locals
import sys
from pathlib import Path
from typing import Optional

from quality_control.generate_stubs.generator import cleanup_code
from quality_control.project_config import ProjectConfig
from quality_control.static_checks.check_black import QualityControlArgumentsParser


class ApiCorrectnessArgumentsParser(QualityControlArgumentsParser):
    """
    CLI arguments parser.
    """

    reference_dir: Optional[Path] = None


def main() -> None:
    """
    Check the stubs correctness
    """
    args = ApiCorrectnessArgumentsParser()

    root_dir = args.root_dir.resolve()
    if args.reference_dir is None:
        reference_dir = root_dir / "reference_dir"
        reference_dir.mkdir(exist_ok=True)
    else:
        reference_dir = args.reference_dir.resolve()

    root_config = ProjectConfig(
        (args.project_config_path or (root_dir / "project_config.json")).resolve()
    )
    reference_config = ProjectConfig((reference_dir / "project_config.json").resolve())

    root_lab_list = root_config.get_labs_paths(root_dir=root_dir)
    reference_lab_list = reference_config.get_labs_paths(root_dir=reference_dir)
    code_is_equal = True

    if len(root_lab_list) != len(reference_lab_list):
        print("different lengths of root and reference lab lists")
        code_is_equal = False

    for lab_path, reference_lab_path in zip(root_lab_list, reference_lab_list):
        if not code_is_equal:
            break

        lab_name = lab_path.name
        lab_config = root_config.get_lab(lab_name)

        for impl_file in lab_config.stubs:
            impl_path = lab_path / impl_file
            impl_path_reference = reference_lab_path / impl_file

            clean_code = cleanup_code(impl_path, root_config, exclude_imports=True)
            clean_code_reference = cleanup_code(
                impl_path_reference, root_config, exclude_imports=True
            )

            if clean_code != clean_code_reference:
                base_name = Path(impl_file).stem
                print(
                    "mismatch",
                    lab_path / f"{base_name}_stub.py",
                    reference_lab_path / f"{base_name}_stub.py",
                )
                code_is_equal = False

    if code_is_equal:
        print("All stubs are relevant")
    sys.exit(not code_is_equal)


if __name__ == "__main__":
    main()
