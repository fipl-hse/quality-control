"""
Check and validate that the generated lab stubs remain unchanged.
"""

# pylint: disable=too-many-locals
import sys
import tempfile
from pathlib import Path

import git
from logging518.config import fileConfig

from quality_control.console_logging import get_child_logger
from quality_control.generate_stubs.generator import cleanup_code
from quality_control.project_config import ProjectConfig
from quality_control.quality_control_parser import QualityControlArgumentsParser

logger = get_child_logger(__file__)

UPSTREAM_URL = "https://github.com/fipl-hse/2026-2-level-labs-admin"
UPSTREAM_NAME = "upstream"
UPSTREAM_BRANCH = "main"

def main() -> None:
    """
    Check the stubs correctness
    """

    args = QualityControlArgumentsParser(underscores_to_dashes=True).parse_args()

    root_dir = args.root_dir.resolve()

    project_config = ProjectConfig(
        (args.project_config_path or (root_dir / "project_config.json")).resolve()
    )
    toml_config = (args.toml_config_path or (root_dir / "pyproject.toml")).resolve()

    fileConfig(toml_config)

    repo = git.Repo(root_dir)
    if UPSTREAM_NAME not in [remote.name for remote in repo.remotes]:
        upstream = repo.create_remote(UPSTREAM_NAME, UPSTREAM_URL)
    else:
        upstream = repo.remotes[UPSTREAM_NAME]
        upstream.set_url(UPSTREAM_URL)
    upstream.fetch(UPSTREAM_BRANCH)
    commit = upstream.refs[UPSTREAM_BRANCH].commit

    passed_files = []
    failed_files = []

    for lab_path in project_config.get_labs_paths(root_dir=root_dir):
        lab_name = lab_path.name
        lab_config = project_config.get_lab(lab_name)

        for impl_file in lab_config.stubs:
            file_is_correct = True
            impl_path = lab_path / impl_file

            if not impl_path.exists():
                logger.error(f"Missing implementation file: {impl_path.relative_to(root_dir)}")
                file_is_correct = False

            try:
                blob = commit.tree / impl_path.relative_to(root_dir)
            except KeyError:
                logger.error(
                    f"Missing referenece in upstream commit file: {impl_path.relative_to(root_dir)}"
                )
                file_is_correct = False
                failed_files.append(impl_file)
                continue

            with tempfile.TemporaryDirectory() as tmpdirname:
                tmp_path = Path(tmpdirname) / impl_file
                tmp_path.write_text(blob.data_stream.read().decode("utf-8"))
                expected_code = cleanup_code(tmp_path, project_config)
            current_code = cleanup_code(impl_path, project_config)

            if expected_code != current_code:
                # logger.error(
                #     "Mismatch between "
                #     f"{impl_path.relative_to(root_dir)} and "
                #     f"{reference_path.relative_to(root_dir)}"
                # )
                file_is_correct = False

            if file_is_correct:
                passed_files.append(impl_file)
            else:
                failed_files.append(impl_file)

    if failed_files:
        logger.error(f"Failed files: {failed_files}")
        sys.exit(1)

    logger.info("All stubs are relevant")
    sys.exit(0)


if __name__ == "__main__":
    main()
