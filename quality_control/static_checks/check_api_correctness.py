from pathlib import Path

from quality_control.generate_stubs.generate_labs_stubs import generate_all_stubs
from quality_control.project_config import ProjectConfig
from quality_control.static_checks.check_black import QualityControlArgumentsParser


def main() -> None:
    args = QualityControlArgumentsParser()

    root_dir = args.root_dir.resolve()
    project_config = ProjectConfig(
        (args.project_config_path or (root_dir / "project_config.json")).resolve()
    )

    generate_all_stubs(project_config, root_dir, exclude_imports=True)

    labs_list = project_config.get_labs_paths(root_dir=root_dir)
    for lab_path in labs_list:
        lab_name = lab_path.name
        lab_config = project_config.get_lab(lab_name)

        for impl_file in lab_config.stubs:
            print(impl_file)

            base_name = Path(impl_file).stem
            stub_path = lab_path / f"{base_name}_stub.py"
            validate_stub_path = lab_path / f"actual_{base_name}_stub.py"

            if not (stub_path.exists() and validate_stub_path.exists()):
                continue

            with open(stub_path, "r", encoding="utf-8") as f:
                stub_code = f.read()
            with open(validate_stub_path, "r", encoding="utf-8") as f:
                validate_stub_code = f.read()

            if validate_stub_code == stub_code:
                print(f"{impl_file}: Stubs weren't changed")
            else:
                print(f"{impl_file}: [WARNING] Stubs were changed")

            stub_path.unlink()


if __name__ == "__main__":
    main()
