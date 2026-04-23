"""
Course projects do not use prohibited modules.
"""

import ast
from pathlib import Path
from typing import Any

from logging518.config import fileConfig

from quality_control.console_logging import get_child_logger
from quality_control.project_config import Lab, ProjectConfig
from quality_control.quality_control_parser import QualityControlArgumentsParser
from quality_control.run_tests import check_skip

logger = get_child_logger(__file__)


MODULE_IMPORTS = set()


class CommandLineInterface(QualityControlArgumentsParser):
    """
    Types for the argument parser.
    """

    lab_path: str | None = None


class ProhibitedModulesFoundError(Exception):
    """
    Found prohibited modules usage in the lab.
    """


def custom_visit_import(node: Any) -> None:
    """
    Custom Visit_Import method for ast.NodeVisitor.

    Args:
        node (Any): ast node object.
    """
    for name in node.names:
        # import MODULE
        MODULE_IMPORTS.add(name.name.split(".")[0])


def custom_visit_import_from(node: Any) -> None:
    """
    Custom Visit_ImportFrom method for ast.NodeVisitor.

    Args:
        node (Any): ast node object.
    """
    if node.module is not None and node.level == 0:
        # from MODULE(.submodule) import name
        MODULE_IMPORTS.add(node.module.split(".")[0])
    elif node.module is None:
        # from . import MODULE (. is the parent dir to the file)
        MODULE_IMPORTS.add(node.name.split(".")[0])
    elif node.level > 0:
        # from .(MODULE) import name
        MODULE_IMPORTS.add(node.module.split(".")[1])


def test_no_prohibited_modules(
    root_dir: Path, lab_config: Lab, prohibited_modules: list[str]
) -> None:
    """
    Checks if lab only has allowed modules.

    Args:
        root_dir (Path): Root directory.
        lab_config (Lab): Lab to check.
        prohibited_modules (list[str]): Prohibited modules from project config.
    """
    for stub in lab_config.stubs:
        import_collector = ast.NodeVisitor()
        import_collector.visit_Import = custom_visit_import
        import_collector.visit_ImportFrom = custom_visit_import_from

        lab_path = root_dir / Path(lab_config.name) / Path(stub)
        with open(lab_path, "r", encoding="utf-8") as f:
            import_collector.visit(ast.parse(f.read()))

        if not MODULE_IMPORTS.isdisjoint(prohibited_modules):
            raise ProhibitedModulesFoundError(
                f"Checked {lab_config.name}/{stub}."
                f"Found prohibited modules: {MODULE_IMPORTS & set(prohibited_modules)}."
            )
        logger.info(f"Checked {lab_config.name}/{stub}." " All modules are allowed.")
        MODULE_IMPORTS.clear()


def main() -> None:
    """
    Running check for active labs.
    """
    args = QualityControlArgumentsParser(underscores_to_dashes=True).parse_args()

    root_dir = args.root_dir.resolve()
    toml_config = (args.toml_config_path or (root_dir / "pyproject.toml")).resolve()

    project_config_path = (args.project_config_path or (root_dir / "project_config.json")).resolve()

    fileConfig(toml_config)

    project_config = ProjectConfig(project_config_path)

    if args.lab_path:
        labs = [project_config.get_lab(args.lab_path)]
    else:
        labs = project_config.get_labs()
    logger.info(f"Current scope: {labs}")

    for lab in labs:
        if check_skip(root_dir, lab.name):
            continue

        test_no_prohibited_modules(
            root_dir=root_dir,
            lab_config=lab,
            prohibited_modules=project_config.get_prohibited_modules(),
        )


if __name__ == "__main__":
    main()
