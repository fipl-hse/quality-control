"""
Course projects do not use prohibited modules.
"""

# pylint: disable=invalid-name

import ast
from pathlib import Path
from typing import Any

from logging518.config import fileConfig

from quality_control.console_logging import get_child_logger
from quality_control.project_config import Lab, ProjectConfig
from quality_control.quality_control_parser import QualityControlArgumentsParser
from quality_control.run_tests import check_skip

logger = get_child_logger(__file__)


class ProhibitedModulesFoundError(Exception):
    """
    Found prohibited modules usage in the lab.
    """


class ImportsParser(ast.NodeVisitor):
    """
    Custom import parser class.
    """

    def __init__(self) -> None:
        """
        Initialize ImportsParser.
        """
        super().__init__()

        self.module_imports = set()

    def visit_Import(self, node: Any) -> None:
        """
        Custom visit_Import method implementation.

        Args:
            node (Any): "import" node to parse modules from.
        """
        for name in node.names:
            # import MODULE
            self.module_imports.add(name.name.split(".")[0])

    def visit_ImportFrom(self, node: Any) -> None:
        """
        Custom visit_ImportFrom method implementation.

        Args:
            node (Any): "import from" node to parse modules from.
        """
        if node.module is not None and node.level == 0:
            # from MODULE(.submodule) import name
            self.module_imports.add(node.module.split(".")[0])
        elif node.module is None:
            # from . import MODULE (. is the parent dir to the file)
            self.module_imports.add(node.name.split(".")[0])
        elif node.level > 0:
            # from .(MODULE) import name
            self.module_imports.add(node.module.split(".")[1])


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
        import_collector = ImportsParser()
        lab_path = root_dir / Path(lab_config.name) / Path(stub)
        with open(lab_path, "r", encoding="utf-8") as f:
            import_collector.visit(ast.parse(f.read()))

        if not import_collector.module_imports.isdisjoint(prohibited_modules):
            raise ProhibitedModulesFoundError(
                f"Checked {lab_config.name}/{stub}. "
                "Found prohibited modules: "
                f"{import_collector.module_imports & set(prohibited_modules)}."
            )
        logger.info(f"Checked {lab_config.name}/{stub}. All modules are allowed.")


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

    labs = project_config.get_labs()

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
