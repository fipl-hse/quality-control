"""
Check the relevance of stubs.
"""

# pylint: disable=too-many-locals, too-many-statements, duplicate-code
import sys
from pathlib import Path

from logging518.config import fileConfig

from quality_control.generate_stubs.generator import cleanup_code
from quality_control.generate_stubs.run_generator import (
    format_stub_file,
    sort_stub_imports,
)
from quality_control.project_config import ProjectConfig
from quality_control.static_checks.check_black import QualityControlArgumentsParser


def get_code(code_path: Path) -> str:
    """
    Get clear code from file.

    Args:
        code_path (Path): Path to file with code

    Returns:
        str: Clear code
    """
    with code_path.open(encoding="utf-8") as file:
        code_text = file.read()
    return code_text


def main() -> None:
    """
    Check the relevance of stubs.
    """
    args = QualityControlArgumentsParser(underscores_to_dashes=True).parse_args()

    root_dir = args.root_dir.resolve()
    toml_config = (args.toml_config_path or (root_dir / "pyproject.toml")).resolve()

    project_config_path = (args.project_config_path or (root_dir / "project_config.json")).resolve()

    project_config = ProjectConfig(project_config_path)

    fileConfig(toml_config)

    labs_list = project_config.get_labs_paths(root_dir=root_dir, include_addons=False)
    code_is_equal = True

    for lab_path in labs_list:
        lab_name = lab_path.name
        lab_config = project_config.get_lab_config(lab_name)

        if not lab_config:
            print(f"No config found for '{lab_name}'")
            continue

        if not lab_config.stubs:
            print(f"No stubs defined for '{lab_name}', skipping")
            continue

        for impl_file in lab_config.stubs:
            impl_path = lab_path / impl_file

            if not impl_path.exists():
                print(f"Missing implementation file: {impl_path}")
                code_is_equal = False
                continue

            base_name = impl_file[:-3]
            stub_path = lab_path / f"{base_name}_stub.py"

            if not stub_path.exists():
                print(f"Missing stub file: {stub_path}")
                code_is_equal = False
                continue

            clean_code = cleanup_code(impl_path, project_config)
            example_stub_path = lab_path / f"example_{base_name}_stub.py"
            with example_stub_path.open(mode="w", encoding="utf-8") as f:
                f.write(clean_code)

            format_stub_file(example_stub_path, root_dir=root_dir)
            sort_stub_imports(example_stub_path)
            expected_code = get_code(example_stub_path)
            example_stub_path.unlink()

            current_code = get_code(stub_path)

            if expected_code != current_code:
                print(f"Stub mismatch: {impl_file} content differs from {stub_path.name}")
                code_is_equal = False

    if code_is_equal:
        print("All stubs are relevant")
    sys.exit(not code_is_equal)


if __name__ == "__main__":
    main()
