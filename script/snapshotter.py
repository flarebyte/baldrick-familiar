#!/usr/bin/env python3
"""
GitHub repo snapshotter (no external libraries).

Public API:
- clone_and_detach(full_name: str) -> str
    Clone org/name into ./temp/github/<name> (via `gh` if available, else `git clone --depth=1`),
    then remove the 'origin' remote. Saves the snapshot commit to ./temp/github/commit-<name>.txt.
    Returns the snapshot commit SHA.

- remote_has_commit(full_name: str, commit: str) -> bool
    Return True iff the given commit matches the current HEAD commit of the remote's default branch.

- main()
    For each repo in REPOS, clone if we don't have a saved commit or if it differs from the remote.
"""

import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Tuple

# ---------- Configuration ----------
REPOS = [
    "flarebyte/baldrick-broth",
    "flarebyte/baldrick-pest",
    "flarebyte/baldrick-whisker",
    "flarebyte/baldrick-dev-ts",
    "flarebyte/learning",
    "flarebyte/baldrick-reserve",
    "flarebyte/clingy-code-detective",
    "flarebyte/overview"
]
BASE_DIR = Path("./temp/github")  # working root for downloads and commit files
# ----------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
)


def _run(
    cmd: list, cwd: Optional[Path] = None, capture: bool = True
) -> Tuple[int, str, str]:
    """Run a command and return (returncode, stdout, stderr)."""
    proc = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
        text=True,
        check=False,
    )
    out = proc.stdout or ""
    err = proc.stderr or ""
    return proc.returncode, out, err


def _which(exe: str) -> Optional[str]:
    """Return path to executable if found."""
    return shutil.which(exe)


def _ensure_dirs() -> None:
    BASE_DIR.mkdir(parents=True, exist_ok=True)


def _split_full_name(full_name: str) -> Tuple[str, str]:
    if "/" not in full_name:
        raise ValueError(f"Invalid repo '{full_name}'. Use 'org/name'.")
    org, name = full_name.split("/", 1)
    return org, name


def _commit_file_path(repo_name: str) -> Path:
    return BASE_DIR / f"commit-{repo_name}.txt"


def _read_saved_commit(repo_name: str) -> Optional[str]:
    p = _commit_file_path(repo_name)
    if p.exists():
        try:
            return p.read_text(encoding="utf-8").strip()
        except Exception:
            return None
    return None


def _save_commit(repo_name: str, sha: str) -> None:
    _ensure_dirs()
    _commit_file_path(repo_name).write_text(sha.strip() + "\n", encoding="utf-8")


def _remote_url(full_name: str) -> str:
    return f"https://github.com/{full_name}.git"


def _remote_default_branch(full_name: str) -> Optional[str]:
    # Use: git ls-remote --symref <url> HEAD  -> output contains "ref: refs/heads/<branch>\tHEAD"
    url = _remote_url(full_name)
    rc, out, err = _run(["git", "ls-remote", "--symref", url, "HEAD"])
    if rc != 0:
        logging.warning(
            "Failed to detect default branch for %s: %s",
            full_name,
            (err or out).strip(),
        )
        return None
    for line in out.splitlines():
        # Example: "ref: refs/heads/main\tHEAD"
        if line.startswith("ref:"):
            parts = line.split()
            if len(parts) >= 2 and parts[1].startswith("refs/heads/"):
                return parts[1].split("refs/heads/")[-1]
    return None


def _remote_head_commit(full_name: str) -> Optional[str]:
    branch = _remote_default_branch(full_name)
    url = _remote_url(full_name)
    ref = branch if branch else "HEAD"
    # git ls-remote <url> <ref> -> "<sha>\t<ref>"
    rc, out, err = _run(["git", "ls-remote", url, ref])
    if rc != 0 or not out.strip():
        logging.warning(
            "Failed to read remote head for %s: %s", full_name, (err or out).strip()
        )
        return None
    first_line = out.splitlines()[0].strip()
    sha = first_line.split("\t")[0].strip()
    if len(sha) == 40:
        return sha
    return None


def clone_and_detach(full_name: str) -> str:
    """Clone repo into ./temp/github/<name>, record the snapshot commit, and remove the remote."""
    _ensure_dirs()
    org, name = _split_full_name(full_name)
    target_dir = BASE_DIR / name
    if target_dir.exists():
        logging.info("Removing existing folder: %s", target_dir)
        shutil.rmtree(target_dir)

    logging.info("Cloning %s into %s ...", full_name, target_dir)
    gh_path = _which("gh")
    if gh_path:
        # Prefer GitHub CLI; pass git flags after --
        rc, out, err = _run(
            ["gh", "repo", "clone", full_name, str(target_dir), "--", "--depth=1"]
        )
        if rc != 0:
            logging.warning(
                "gh clone failed (%s). Falling back to git clone.", (err or out).strip()
            )
            gh_path = None

    if not gh_path:
        url = _remote_url(full_name)
        rc, out, err = _run(["git", "clone", "--depth=1", url, str(target_dir)])
        if rc != 0:
            raise RuntimeError(
                f"git clone failed for {full_name}: {(err or out).strip()}"
            )

    # Determine snapshot commit (HEAD of cloned checkout)
    rc, out, err = _run(["git", "rev-parse", "HEAD"], cwd=target_dir)
    if rc != 0:
        raise RuntimeError(
            f"Failed to determine HEAD for {full_name}: {(err or out).strip()}"
        )
    snapshot_sha = out.strip()
    logging.info("Snapshot commit for %s: %s", full_name, snapshot_sha)

    # Detach by removing origin
    rc, out, err = _run(["git", "remote", "remove", "origin"], cwd=target_dir)
    if rc != 0:
        # If remove failed, try setting url to empty (best-effort)
        _run(
            ["git", "remote", "set-url", "--delete", "origin", _remote_url(full_name)],
            cwd=target_dir,
        )
    else:
        logging.info("Removed 'origin' remote for %s.", full_name)

    # Save commit file at ./temp/github/commit-<name>.txt
    _save_commit(name, snapshot_sha)
    logging.info("Saved snapshot commit to %s.", _commit_file_path(name))

    return snapshot_sha


def remote_has_commit(full_name: str, commit: str) -> bool:
    """Return True if 'commit' equals the current HEAD commit of the remote default branch."""
    if not commit:
        return False
    remote_head = _remote_head_commit(full_name)
    if not remote_head:
        return False
    return remote_head == commit.strip()


def _needs_clone(full_name: str) -> bool:
    org, name = _split_full_name(full_name)
    saved = _read_saved_commit(name)
    if not saved:
        logging.info("[%s] No saved commit. Will clone.", full_name)
        return True
    remote_head = _remote_head_commit(full_name)
    if not remote_head:
        logging.info("[%s] Could not determine remote head. Will clone.", full_name)
        return True
    if remote_head != saved:
        logging.info(
            "[%s] Saved commit differs.\n  saved:  %s\n  remote: %s\nWill clone.",
            full_name,
            saved,
            remote_head,
        )
        return True
    logging.info("[%s] Up to date (commit %s).", full_name, saved)
    return False


def main() -> None:
    _ensure_dirs()
    if not REPOS:
        logging.info(
            "No repositories configured in REPOS. Add entries like 'org/name'."
        )
        return
    for full_name in REPOS:
        try:
            logging.info("Processing %s ...", full_name)
            if _needs_clone(full_name):
                sha = clone_and_detach(full_name)
                logging.info("Cloned %s at %s.", full_name, sha)
            else:
                logging.info("Skipping clone for %s (already current).", full_name)
        except Exception as e:
            logging.error("Error processing %s: %s", full_name, e)


if __name__ == "__main__":
    main()
