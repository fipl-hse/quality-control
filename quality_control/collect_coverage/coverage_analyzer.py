"""
Runner for collecting coverage.
"""

import sys
from pathlib import Path
from typing import Iterable, Mapping

from logging518.config import fileConfig

from quality_control.collect_coverage.run_coverage import (
    CoverageCreateReportError,
    CoverageRunError,
    extract_percentage_from_report,
    run_coverage_collection,
)
from quality_control.console_logging import get_child_logger
from quality_control.lab_settings import LabSettings
from quality_control.project_config import ProjectConfig
from quality_control.static_checks.check_black import QualityControlArgumentsParser

logger = get_child_logger(__file__)

CoverageResults = Mapping[
    str,
    tuple[int | None,],
]


def collect_coverage(
    root_dir: Path, all_labs_names: Iterable[Path], artifacts_path: Path
) -> CoverageResults:
    """
    Entrypoint for coverage collection for every required folder.

    Args:
        all_labs_names (Iterable[Path]): Names of all labs
        artifacts_path (Path): Path to artifacts

    Returns:
        CoverageResults: Coverage results
    """
    all_labs_results = {}
    for lab_path in all_labs_names:
        percentage = None
        try:
            check_target = True
            run_coverage_collection(
                lab_path=lab_path,
                artifacts_path=artifacts_path,
                check_target_score=check_target,
                root_dir=root_dir,
            )
            report_path = artifacts_path / f"{lab_path.name}.json"
            percentage = extract_percentage_from_report(report_path)
        except (CoverageRunError, CoverageCreateReportError) as e:
            logger.error(str(e))
        finally:
            all_labs_results[lab_path.name] = (percentage,)
    return all_labs_results


def is_decrease_present(
    all_labs_results: CoverageResults, previous_coverage_results: dict
) -> tuple[bool, bool, dict]:
    """
    Analyze coverage report versus previous runs.

    Args:
        all_labs_results (CoverageResults): Coverage results
        previous_coverage_results (dict): Previous coverage results

    Returns:
        tuple[bool, bool, dict]: Is decrease present or not, and failed tests present or not
    """
    logger.info("\n\n------------------\nREPORT\n------------------")
    any_degradation = False
    any_fallen_tests = False
    labs_with_thresholds = {}
    for lab_name, current_lab_args in all_labs_results.items():
        current_lab_percentage = current_lab_args[0]
        prev_lab_percentage = previous_coverage_results.get(lab_name, 0)
        if current_lab_percentage is None:
            current_lab_percentage = 0
        diff = current_lab_percentage - prev_lab_percentage

        logger.info(
            f'{lab_name:<30}: {current_lab_percentage}% ({"+" if diff >= 0 else ""}{diff})'
        )
        labs_with_thresholds[lab_name] = current_lab_percentage
        if diff < 0:
            any_degradation = True
    logger.info("\n\n------------------\nEND OF REPORT\n------------------")

    return any_degradation, any_fallen_tests, labs_with_thresholds


def main() -> None:
    """
    Entrypoint for coverage collection.
    """
    args = QualityControlArgumentsParser(underscores_to_dashes=True).parse_args()

    root_dir = args.root_dir.resolve()
    toml_config = (args.toml_config_path or (root_dir / "pyproject.toml")).resolve()

    project_config_path = (
        args.project_config_path or (root_dir / "project_config.json")
    ).resolve()

    project_config = ProjectConfig(project_config_path)

    fileConfig(toml_config)

    artifacts_path = root_dir / "build" / "coverage"
    artifacts_path.mkdir(parents=True, exist_ok=True)

    coverage_thresholds = project_config.get_thresholds()
    all_labs_names = project_config.get_labs_paths(
        include_addons=False, root_dir=root_dir
    )

    not_skipped = []
    for lab_path in all_labs_names:
        settings = LabSettings(lab_path / "settings.json")
        if settings.target_score == 0:
            logger.info(f"Skip {lab_path} as target score is 0")
            continue
        not_skipped.append(lab_path)

    all_labs_results = collect_coverage(
        root_dir=root_dir, all_labs_names=not_skipped, artifacts_path=artifacts_path
    )

    any_degradation, any_fallen_tests, labs_with_thresholds = is_decrease_present(
        all_labs_results, coverage_thresholds
    )

    if any_degradation:
        logger.info(
            "Some of labs have worse coverage. We cannot accept this. Write more tests!\n"
            "You can copy-paste the following content to the ./project_config.json "
            "to update thresholds. \n\n"
        )

        project_config.update_thresholds(labs_with_thresholds)

        logger.info(project_config.get_json())
        sys.exit(1)

    if any_fallen_tests:
        logger.info(
            "Some tests failed! We can't accept that.\n"
            "Make sure the tests pass. I wish you good luck! \n\n"
        )
        sys.exit(1)

    logger.info("Nice coverage. Anyway, write more tests!\n\n")


if __name__ == "__main__":
    main()
