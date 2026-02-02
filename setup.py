from pathlib import Path
from typing import List

from setuptools import find_packages, setup


def collect_requirements() -> List[str]:
    requirements_file_path = Path("quality_control") / "requirements.txt"
    with requirements_file_path.open(encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]


setup(
    name="fiplconfig",
    version="0.3",
    packages=find_packages(include=["quality_control", "quality_control.*"]),
    include_package_data=True,
    package_data={
        "quality_control": ["*.txt", "*.json", "*.yaml"],
    },
    install_requires=collect_requirements(),
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "fiplconfig.check_black=quality_control.static_checks.check_black:main",
            "fiplconfig.check_init=quality_control.static_checks.check_init:main",
            "fiplconfig.check_doc8=quality_control.static_checks.check_doc8:main",
            "fiplconfig.check_docstrings=quality_control.static_checks.check_docstrings:main",
            "fiplconfig.check_mypy=quality_control.static_checks.check_mypy:main",
            "fiplconfig.check_flake8=quality_control.static_checks.check_flake8:main",
            "fiplconfig.check_actual_stubs=quality_control.static_checks.check_actual_stubs:main",
            "fiplconfig.check_lint=quality_control.static_checks.check_lint:main",
            "fiplconfig.check_newline=quality_control.static_checks.check_newline:main",
            "fiplconfig.check_pr_name=quality_control.static_checks.check_pr_name:main",
            "fiplconfig.check_requirements=quality_control.static_checks.check_requirements:main",
            "fiplconfig.check_spelling=quality_control.spellcheck.check_spelling:main",
            "fiplconfig.coverage_analyzer=quality_control.collect_coverage.coverage_analyzer:main",
            "fiplconfig.sort_wordlist=quality_control.spellcheck.sort_wordlist:main",
            "fiplconfig.generate_labs_stubs=quality_control.generate_stubs.generate_labs_stubs:main",
            "fiplconfig.run_tests=quality_control.run_tests:main",
            "fiplconfig.run_start=quality_control.run_start:main",
            "fiplconfig.update_forks=quality_control.github.update_forks:main",
        ]
    },
    long_description=(Path(__file__).parent / "README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
)
