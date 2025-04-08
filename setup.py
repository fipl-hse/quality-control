from pathlib import Path
from typing import List

from setuptools import setup, find_packages, find_namespace_packages


def collect_requirements() -> List[str]:
    quality_control_dir = Path("quality_control")
    requirements_file_path = quality_control_dir / "requirements.txt"
    with requirements_file_path.open(encoding='utf-8') as requirements_file:
        requirements = requirements_file.readlines()
    return [line.strip() for line in requirements]


def main() -> None:
    setup(
        name='fiplconfig',
        version='0.3',
        packages=find_packages(),
        install_requires=find_namespace_packages(
            where=".", include=["quality_control.*"], exclude=[""]
        ),
        instal_requires=collect_requirements(),
        python_requires=">=3.10",
        entry_points={
            'console_scripts': ['fiplconfig.check_black=quality_control.check_black:main']
        }
    )


if __name__ == '__main__':
    main()
