from pathlib import Path
from typing import List

from setuptools import setup, find_packages


def collect_requirements() -> List[str]:
    requirements_file_path = Path("quality_control") / "requirements.txt"
    with requirements_file_path.open(encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]


setup(
    name='fiplconfig',
    version='0.3',
    packages=find_packages(include=["quality_control", "quality_control.*"]),
    install_requires=collect_requirements(),
    python_requires=">=3.10",
    entry_points={
        'console_scripts': [
            'fiplconfig.check_black=quality_control.check_black:main'
        ]
    }
)
