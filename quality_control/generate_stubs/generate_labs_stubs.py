"""
Generator of all labs.
"""

# pylint: disable=duplicate-code

from pathlib import Path

from logging518.config import fileConfig

from quality_control.console_logging import get_child_logger
from quality_control.generate_stubs.generator import cleanup_code
from quality_control.generate_stubs.run_generator import (
    format_stub_file,
    sort_stub_imports,
)
from quality_control.project_config import ProjectConfig
from quality_control.quality_control_parser import QualityControlArgumentsParser

logger = get_child_logger(__file__)


def _generate_stubs_single_module(
    module_path: Path, root_dir: Path, project_config: ProjectConfig
) -> None:
    """
    Process single module.

    Args:
        module_path (Path): Path to module
        root_dir (Path): Root directory
        project_config (ProjectConfig): Project configuration
    """
    stub_path = module_path.parent / f"{module_path.stem}_stub{module_path.suffix}"

    source_code = cleanup_code(module_path, project_config)
    with stub_path.open(mode="w", encoding="utf-8") as f:
        f.write(source_code)
    format_stub_file(stub_path, root_dir=root_dir)
    sort_stub_imports(stub_path)


def generate_all_stubs(project_config: ProjectConfig, root_dir: Path) -> None:
    """
    Generate stubs for all labs.

    Args:
        project_config (ProjectConfig): Project config
    """
    labs_config = project_config.get_labs_config()

    for lab_conf in labs_config:
        lab_name = lab_conf.name
        stubs_list = lab_conf.stubs

        if not stubs_list:
            logger.info(f"Skipping stub generation for {lab_name} - no special configuration.")
            continue

        logger.info(f"Generating stubs for {lab_name}.")

        for filename in stubs_list:
            module_path = root_dir / lab_name / filename
            logger.info(f"Processing file {filename} -> {module_path}")
            _generate_stubs_single_module(module_path, root_dir, project_config)


def main() -> None:
    """
    Entrypoint for stub generation.
    """
    args = QualityControlArgumentsParser(underscores_to_dashes=True).parse_args()

    root_dir = args.root_dir.resolve()
    toml_config = (args.toml_config_path or (root_dir / "pyproject.toml")).resolve()

    project_config_path = (args.project_config_path or (root_dir / "project_config.json")).resolve()

    project_config = ProjectConfig(project_config_path)

    fileConfig(toml_config)
    generate_all_stubs(project_config, root_dir)


if __name__ == "__main__":
    main()
