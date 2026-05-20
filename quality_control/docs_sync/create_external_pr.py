"""
Python tool for synchronization between source and target repositories.
"""

import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import git
from logging518.config import fileConfig
from pydantic import BaseModel, Field, ValidationError

from quality_control.cli_unifier import _run_console_tool, handles_console_error
from quality_control.console_logging import get_child_logger
from quality_control.constants import SYNC_CONFIG_PATH
from quality_control.project_config import ProjectConfig
from quality_control.quality_control_parser import QualityControlArgumentsParser

logger = get_child_logger(__file__)


class SyncArgumentParser(QualityControlArgumentsParser):  # type: ignore
    """
    Parser that gets args for sync tool
    """

    repo_name: str
    pr_number: str


class PRData(BaseModel):
    """
    Model for information about PR
    """

    mergedAt: Optional[datetime] = None
    headRefName: str
    baseRefName: str = Field(default="main")


@dataclass(slots=True)
class CommitConfig:
    """
    Storage for commit data
    """

    repo_path: str
    branch_name: str
    repo_name: str
    pr_number: str
    json_changed: bool
    files_to_sync_found: bool


@dataclass(slots=True)
class SyncConfig:
    """
    Storage for final PR data
    """

    target_repo: str
    changed_files: list[str]
    json_content: Optional[dict]
    commit_sha: str


@dataclass(slots=True)
class SyncResult:
    """
    Result of synchronization operation
    """

    has_changes: bool
    files_to_sync_found: bool
    json_changed: bool


@handles_console_error(ok_codes=(0, 1))
def run_gh(args: list[str]) -> Any:
    """
    Run gh command via imported function.

    Args:
        args (list[str]): Arguments for gh command.

    Returns:
        Any: Result of gh command.
    """
    return _run_console_tool("gh", args)


def get_pr_data(repo_name: str, pr_number: str) -> PRData | None:
    """
    Get PR data via gh.

    Args:
        repo_name (str): Name of source repo.
        pr_number (str): Number of needed PR in source repo.

    Returns:
        Optional[PRData]: PR data.
    """
    stdout, stderr, return_code = run_gh(
        [
            "pr",
            "view",
            pr_number,
            "--repo",
            repo_name,
            "--json",
            "mergedAt,headRefName,baseRefName",
        ]
    )

    if return_code != 0 or not stdout:
        logger.warning("Failed to get PR data: %s", stderr)
        return None

    try:
        data = json.loads(stdout)
        return PRData.model_validate(data)
    except json.JSONDecodeError as e:
        logger.error("Invalid JSON from gh: %s", e)
        return None
    except ValidationError as e:
        logger.error("PR data validation failed: %s", e)
        return None


def clone_repo(target_repo: str, gh_token: str) -> git.Repo:
    """
    Clone target repo, removing any existing local copy first.

    Args:
        target_repo (str): Repository name.
        gh_token (str): GitHub token used for authenticated HTTPS clone.

    Returns:
        git.Repo: Cloned repository object.
    """
    target_path = Path(target_repo)
    if target_path.exists():
        import shutil

        shutil.rmtree(target_path)

    url = f"https://{gh_token}@github.com/fipl-hse/{target_repo}.git"
    logger.info("Cloning %s …", url.replace(gh_token, "***"))
    repo = git.Repo.clone_from(url, str(target_path))
    return repo


def setup_git_config(repo: git.Repo) -> None:
    """
    Configure bot identity for commits.

    Args:
        repo (git.Repo): Repository to configure.
    """
    with repo.config_writer() as cfg:
        cfg.set_value("user", "name", "github-actions[bot]")
        cfg.set_value(
            "user",
            "email",
            "41898282+github-actions[bot]@users.noreply.github.com",
        )


def checkout_or_create_branch(repo: git.Repo, branch_name: str) -> None:
    """
    Checkout an existing remote branch or create a new local one.

    Args:
        repo (git.Repo): Repository object.
        branch_name (str): Branch to checkout / create.
    """
    remote_ref = f"origin/{branch_name}"
    remote_exists = any(ref.name == remote_ref for ref in repo.remotes["origin"].refs)

    if remote_exists:
        repo.git.checkout(branch_name)
        repo.remotes["origin"].pull(branch_name)
        logger.info("Checked out existing branch %s", branch_name)
    else:
        repo.git.checkout("-b", branch_name)
        logger.info("Created new branch %s", branch_name)


def add_remote_and_fetch(repo: git.Repo, remote_name: str, repo_url: str) -> git.Remote:
    """
    Add a remote if it does not exist yet, then fetch it.

    Args:
        repo (git.Repo): Repository object.
        remote_name (str): Short name for the new remote.
        repo_url (str): URL of the remote repository.

    Returns:
        git.Remote: The remote object after fetching.
    """
    existing_names = [r.name for r in repo.remotes]
    if remote_name not in existing_names:
        remote = repo.create_remote(remote_name, repo_url)
        logger.info("Added remote %s", remote_name)
    else:
        remote = repo.remotes[remote_name]

    remote.fetch()
    return remote


def _get_blob_sha(repo: git.Repo, ref_str: str, file_path: str) -> str | None:
    """
    Return the git object SHA for file_path at ref_str, or None if absent.

    Args:
        repo (git.Repo): Repository object.
        ref_str (str): A ref name resolvable by the repo.
        file_path (str): Relative path inside the tree.

    Returns:
        str | None: Object SHA string, or None when the path doesn't exist.
    """
    try:
        commit = repo.commit(ref_str)
        blob = commit.tree[file_path]
        return blob.hexsha
    except (KeyError, git.BadName, git.BadObject):
        return None


def _read_blob(repo: git.Repo, ref_str: str, file_path: str) -> str | None:
    """
    Return decoded text content of file_path at ref_str, or None.

    Args:
        repo (git.Repo): Repository object.
        ref_str (str): Ref name.
        file_path (str): Relative path inside the tree.

    Returns:
        str | None: File contents as text, or None when absent.
    """
    try:
        commit = repo.commit(ref_str)
        blob = commit.tree[file_path]
        return blob.data_stream.read().decode("utf-8")
    except (KeyError, git.BadName, git.BadObject):
        return None


def get_json_from_source(repo: git.Repo, source_ref: str) -> tuple[Any | None, bool]:
    """
    Compare sync-config JSON between source ref and target main; update on disk
    if it changed.

    Args:
        repo (git.Repo): Target repository object.
        source_ref (str): Ref in source repo.

    Returns:
        tuple[Any | None, bool]: (ProjectConfig | None, json_changed).
    """
    repo_root = Path(repo.working_dir)
    json_path = repo_root / SYNC_CONFIG_PATH

    source_sha = _get_blob_sha(repo, source_ref, SYNC_CONFIG_PATH)
    target_sha = _get_blob_sha(repo, "origin/main", SYNC_CONFIG_PATH)

    json_changed = source_sha != target_sha

    if json_changed:
        if source_sha is not None:
            content = _read_blob(repo, source_ref, SYNC_CONFIG_PATH)
            if content is None:
                logger.error("Failed to read JSON from source")
                return None, json_changed
            json_path.parent.mkdir(parents=True, exist_ok=True)
            json_path.write_text(content, encoding="utf-8")
            repo.index.add([SYNC_CONFIG_PATH])
        else:
            if json_path.exists():
                repo.index.remove([SYNC_CONFIG_PATH], working_tree=True)
            return None, json_changed

    config = ProjectConfig(json_path)
    return config, json_changed


def sync_files_from_source(
    repo: git.Repo,
    source_ref: str,
    sync_list: list[tuple[str, str]],
) -> bool:
    """
    Copy files from source_ref into the working tree according to sync_list.

    Args:
        repo (git.Repo): Target repository object.
        source_ref (str): Source ref to read blobs from.
        sync_list (list[tuple[str, str]]): (source_path, target_path) pairs
            for files whose SHA already differs.

    Returns:
        bool: True if any file was written or removed.
    """
    repo_root = Path(repo.working_dir)
    has_changes = False

    for source_path, target_path in sync_list:
        content = _read_blob(repo, source_ref, source_path)
        full_target = repo_root / target_path

        if content is not None:
            full_target.parent.mkdir(parents=True, exist_ok=True)
            full_target.write_text(content, encoding="utf-8")
            repo.index.add([target_path])
            has_changes = True
        else:
            if full_target.exists():
                repo.index.remove([target_path], working_tree=True)
                has_changes = True
            else:
                logger.info(
                    "File %s not found in source and not present in target — skipping",
                    source_path,
                )

    return has_changes


def run_sync(
    repo: git.Repo,
    source_ref: str,
    config: Any | None,
    json_changed: bool,
) -> SyncResult | None:
    """
    Compute which files need syncing and apply changes.

    Args:
        repo (git.Repo): Target repository object.
        source_ref (str): Ref in source repo.
        config (Any | None): ProjectConfig object.
        json_changed (bool): Whether the JSON config file itself changed.

    Returns:
        SyncResult | None: Result of sync operation, or None when config absent.
    """
    if not config:
        return None

    has_changes = json_changed
    files_to_sync_found = False

    sync_pairs = config.get_doc_sync_config()
    files_to_sync: list[tuple[str, str]] = []

    for pair in sync_pairs:
        source_sha = _get_blob_sha(repo, source_ref, pair.source)
        target_sha = _get_blob_sha(repo, "origin/main", pair.target)

        if source_sha != target_sha:
            files_to_sync.append((pair.source, pair.target))
            files_to_sync_found = True

    if files_to_sync:
        synced = sync_files_from_source(repo, source_ref, files_to_sync)
        has_changes = has_changes or synced

    return SyncResult(
        has_changes=has_changes,
        files_to_sync_found=files_to_sync_found,
        json_changed=json_changed,
    )


def commit_and_push_changes(repo: git.Repo, commit_config: CommitConfig) -> None:
    """
    Create a commit with the staged changes and push the branch.

    Args:
        repo (git.Repo): Target repository object.
        commit_config (CommitConfig): Commit metadata.
    """
    if commit_config.json_changed and not commit_config.files_to_sync_found:
        commit_msg = (
            f"Update sync mapping from {commit_config.repo_name} " f"PR {commit_config.pr_number}"
        )
    else:
        commit_msg = f"Sync changes from {commit_config.repo_name} PR {commit_config.pr_number}"

    repo.index.commit(commit_msg)
    repo.remotes["origin"].push(commit_config.branch_name)
    logger.info("Committed and pushed: %s", commit_msg)


def create_or_update_pr(
    repo: git.Repo,
    target_repo: str,
    branch_name: str,
    repo_name: str,
    pr_number: str,
) -> None:
    """
    Create a new PR in target repo or comment on the existing one.

    Args:
        repo (git.Repo): Target repository object (used to check for commits).
        target_repo (str): Target repo name.
        branch_name (str): Branch with the synced changes.
        repo_name (str): Source repo name.
        pr_number (str): Source PR number.
    """
    stdout, _, return_code = run_gh(
        [
            "pr",
            "list",
            "--repo",
            f"fipl-hse/{target_repo}",
            "--head",
            branch_name,
            "--json",
            "number",
        ]
    )

    target_pr_number = None
    if return_code == 0 and stdout:
        pr_list = json.loads(stdout)
        if pr_list:
            target_pr_number = pr_list[0].get("number")

    ahead_commits = list(repo.iter_commits(f"origin/main..{branch_name}"))
    has_commits = bool(ahead_commits)

    if not has_commits:
        logger.info("No commits in branch %s — skipping PR creation", branch_name)
        return

    if target_pr_number is None:
        stdout, stderr, return_code = run_gh(
            [
                "pr",
                "create",
                "--repo",
                f"fipl-hse/{target_repo}",
                "--head",
                branch_name,
                "--base",
                "main",
                "--title",
                f"[Automated] Sync from {repo_name} PR {pr_number}",
                "--body",
                f"Automated synchronization from {repo_name} PR #{pr_number}",
                "--label",
                "automated pr",
                "--assignee",
                "demid5111",
            ]
        )
        if return_code == 1:
            logger.error("Failed to create PR. stdout: %s  stderr: %s", stdout, stderr)
            sys.exit(1)
        logger.info("Created new PR in target repository")
    else:
        stdout, stderr, return_code = run_gh(
            [
                "pr",
                "comment",
                str(target_pr_number),
                "--repo",
                f"fipl-hse/{target_repo}",
                "--body",
                "Automatically updated",
            ]
        )
        if return_code != 0:
            logger.warning("Failed to update PR %s", target_pr_number)


def validate_and_process_inputs() -> tuple[str, ...]:
    """
    Validate input args and derive basic parameters for the script.

    Returns:
        tuple[str, ...]: (repo_name, pr_number, target_repo, branch_name, gh_token)
    """
    parser = SyncArgumentParser(underscores_to_dashes=True)
    args = parser.parse_args()

    repo_name = args.repo_name
    pr_number = args.pr_number
    target_repo = "fipl-hse.github.io"
    branch_name = f"auto-update-from-{repo_name}-pr-{pr_number}"
    root_dir = args.root_dir.resolve()
    toml_config = (args.toml_config_path or (root_dir / "pyproject.toml")).resolve()
    fileConfig(toml_config)

    gh_token = os.environ.get("GH_TOKEN")
    if not gh_token:
        logger.error("GH_TOKEN environment variable is not set")
        sys.exit(1)

    return repo_name, pr_number, target_repo, branch_name, gh_token


def prepare_target_repo(target_repo: str, branch_name: str, gh_token: str) -> git.Repo:
    """
    Clone target repo, configure git identity, and checkout the working branch.

    Args:
        target_repo (str): Name of target repo.
        branch_name (str): Branch to work on.
        gh_token (str): GitHub token.

    Returns:
        git.Repo: Fully prepared repository object.
    """
    repo = clone_repo(target_repo, gh_token)
    setup_git_config(repo)
    checkout_or_create_branch(repo, branch_name)
    return repo


def main() -> None:
    """
    Entry point: sync files from source PR into the target repository
    """
    repo_name, pr_number, target_repo, branch_name, gh_token = validate_and_process_inputs()

    repo = prepare_target_repo(target_repo, branch_name, gh_token)

    pr_data = get_pr_data(repo_name, pr_number)
    if not pr_data:
        logger.error("PR data in source repo not found")
        sys.exit(0)

    head_ref = pr_data.headRefName
    base_ref = pr_data.baseRefName

    if not head_ref:
        logger.error("Could not get head branch name from PR")
        sys.exit(0)

    if pr_data.mergedAt:
        source_ref = f"parent-repo/{base_ref}"
        logger.info("PR is merged — comparing %s with target main", source_ref)
    else:
        source_ref = f"parent-repo/{head_ref}"
        logger.info("PR is open — comparing %s with target main", source_ref)

    repo.remotes["origin"].fetch("main")

    config, json_changed = get_json_from_source(repo, source_ref)

    sync_result = run_sync(repo, source_ref, config, json_changed)

    if sync_result is None or not sync_result.has_changes:
        logger.info("No changes to commit")
        sys.exit(0)

    commit_config = CommitConfig(
        repo_path=str(repo.working_dir),
        branch_name=branch_name,
        repo_name=repo_name,
        pr_number=pr_number,
        json_changed=sync_result.json_changed,
        files_to_sync_found=sync_result.files_to_sync_found,
    )
    commit_and_push_changes(repo, commit_config)
    create_or_update_pr(repo, target_repo, branch_name, repo_name, pr_number)


if __name__ == "__main__":
    main()
