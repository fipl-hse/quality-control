"""
Config class implementation: stores the configuration information.
"""

import json
import re
from dataclasses import field
from pathlib import Path
from re import Pattern

from pydantic import TypeAdapter
from pydantic.dataclasses import dataclass

from quality_control.constants import PROJECT_ROOT


@dataclass
class LabSettings:
    """
    BaseModel for labs settings
    """

    ignore: list[str] | None = field(default_factory=list)


@dataclass
class Lab:
    """
    BaseModel for labs.
    """

    name: str = field(default_factory=str)
    coverage: int = field(default_factory=int)
    settings: LabSettings | None = field(default_factory=LabSettings)
    stubs: list[str] | None = None


@dataclass
class Addon:
    """
    BaseModel for addons.
    """

    name: str = field(default_factory=str)
    coverage: int = field(default_factory=int)
    need_uml: bool = field(default_factory=False)
    run_tests: bool = False


@dataclass
class Repository:
    """
    BaseModel for repository.
    """

    admins: list = field(default_factory=list)
    pr_name_regex: str = field(default_factory=str)
    pr_name_example: str = field(default_factory=str)


@dataclass
class Stub:
    """
    BaseModel for stubs configuration.
    """

    accepted_modules: dict[str, list[str]] = field(default_factory=dict)
    specific_file_rules: dict[str, dict] = field(default_factory=dict)


@dataclass
class ProjectConfigDTO:
    """
    BaseModel for ProjectConfig.
    """

    labs: list[Lab] = field(default_factory=list[Lab])
    addons: list[Addon] = field(default_factory=list[Addon])
    repository: Repository = field(default_factory=Repository)
    stubs_config: Stub = field(default_factory=Stub)


class ProjectConfig(ProjectConfigDTO):
    """
    Project Config implementation.
    """

    _dto: ProjectConfigDTO

    def __init__(self, config_path: Path) -> None:
        """
        Initialize ProjectConfig.

        Args:
             config_path (Path): Path to config
        """
        super().__init__()
        with config_path.open(encoding="utf-8", mode="r") as config_file:
            json_content = json.load(config_file)
        self._dto = TypeAdapter(ProjectConfigDTO).validate_python(json_content)

    def get_thresholds(self) -> dict:
        """
        Get labs thresholds.

        Returns:
            dict: Labs thresholds
        """
        all_thresholds = {}
        labs_thresholds = {lab.name: lab.coverage for lab in self.get_labs()}
        addons_thresholds = {addon.name: addon.coverage for addon in self.get_addons()}
        all_thresholds.update(labs_thresholds)
        all_thresholds.update(addons_thresholds)
        return all_thresholds

    def get_admins(self) -> list[str]:
        """
        Get admins names.

        Returns:
            list[str]: Admins
        """
        return list(self._dto.repository.admins)

    def get_pr_name_regex(self) -> Pattern:
        """
        Get pull request name regex example.

        Returns:
            Pattern: Compiled pattern
        """
        return re.compile(self._dto.repository.pr_name_regex)

    def get_pr_name_example(self) -> str:
        """
        Get pull request name example.

        Returns:
            str: PR name example
        """
        return str(self._dto.repository.pr_name_example)

    def update_thresholds(self, new_thresholds: dict[str, int]) -> None:
        """
        Get json content from project_config.json with updated thresholds.

        Args:
            new_thresholds (dict[str, int]): Updated thresholds
        """
        for index, lab in enumerate(self.get_labs()):
            self._dto.labs[index] = Lab(
                name=lab.name,
                coverage=new_thresholds.get(lab.name, lab.coverage),
                stubs=lab.stubs,
            )
        for index, addon in enumerate(self.get_addons()):
            self._dto.addons[index] = Addon(
                name=addon.name, coverage=new_thresholds.get(addon.name, addon.coverage)
            )

    def __str__(self) -> str:
        """
        Get a string with fields.

        Returns:
            str: A string with fields
        """
        return f"{self._dto}"

    def get_json(self) -> str:
        """
        Get a json view of ProjectConfig.

        Returns:
            str: A json view of ProjectConfig
        """
        return str(self._dto.model_dump_json(indent=4))  # type: ignore

    def get_labs(self) -> list[Lab]:
        """
        Get the list of Lab objects from the configuration.

        Returns:
            list[Lab]: List of configured labs.
        """
        return sorted(self._dto.labs, key=lambda x: x.name)

    def get_lab(self, lab_name: str) -> Lab | None:
        """
        Returns configuration of the lab.

        Args:
            lab_name (str): Name of lab

        Returns:
            Lab | None: Configuration of lab
        """
        return next((lab for lab in self.get_labs() if lab.name == lab_name), None)

    def get_labs_paths(self, root_dir: Path = PROJECT_ROOT) -> list:
        """
        Get labs paths.

        Args:
            include_addons (bool): Include addons or not
            root_dir (Path): Root path

        Returns:
            list: Paths to labs
        """
        return [root_dir / lab.name for lab in self.get_labs()]

    def get_addons(self) -> list:
        """
        Get addons names.

        Returns:
            list: Addons names
        """
        return sorted(self._dto.addons, key=lambda x: x.name)

    def get_addons_paths(self, root_dir: Path = PROJECT_ROOT) -> list:
        """
        Get addons paths.

        Args:
            root_dir (Path): Root path

        Returns:
            list: Paths to addons
        """
        return [root_dir / lab.name for lab in self.get_addons()]

    def get_stubs_names(self) -> Stub:
        """
        Returns the configuration for stubs.

        Returns:
            StubsConfig: The stubs configuration object.
        """
        return self._dto.stubs_config
