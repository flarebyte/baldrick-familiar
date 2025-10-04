#!/usr/bin/env python3
"""
Utility to collect specific files from a code checkout.

It searches recursively under "./temp/github/" for each filename listed in
FILENAMES, and copies every match into "./temp/data/" using the pattern
"<sanitized-relative-path>-<filename>". The relative path is taken from the
match's location under "./temp/github/" and sanitized by replacing path
separators with "-".

Logging is printed to stdout.
"""

from __future__ import annotations

import os
from pathlib import Path
import shutil
from typing import Iterable


# === Configuration ===
FILENAMES = [
    "README.md"
]

SRC_ROOT = Path("./temp/github")
DEST_ROOT = Path("./temp/data")


def copy_matches(filename: str, src_root: Path, dest_root: Path) -> int:
    """
    Find every file named `filename` under `src_root` (recursively) and copy
    it into `dest_root` using the name "<sanitized-relative-path>-<filename>".

    The "sanitized-relative-path" is the file's path relative to `src_root`
    with path separators replaced by "-".

    Args:
        filename: Exact file name to match (e.g., "README.md").
        src_root: Root directory to search (e.g., Path("./temp/github")).
        dest_root: Destination directory for copied files
                   (e.g., Path("./temp/data")).

    Returns:
        The number of files copied.
    """
    if not src_root.exists():
        print(f"[WARN] Source root does not exist: {src_root}")
        return 0

    dest_root.mkdir(parents=True, exist_ok=True)

    copied = 0
    print(f"[INFO] Searching for '{filename}' under {src_root.resolve()}")

    # Walk the tree without external deps for speed and portability
    for dirpath, _dirnames, filenames in os.walk(src_root):
        if filename in filenames:
            src_path = Path(dirpath) / filename
            rel_path = src_path.relative_to(src_root)
            # Remove the trailing filename to get its directory relative path
            rel_dir = rel_path.parent
            sanitized = _sanitize(rel_dir)
            out_name = f"{sanitized}-{filename}" if sanitized else f"{filename}"
            dest_path = dest_root / out_name

            try:
                shutil.copy2(src_path, dest_path)
                copied += 1
                print(f"[OK]  Copied: {src_path}  ->  {dest_path.name}")
            except Exception as e:
                print(f"[ERR] Failed to copy {src_path} -> {dest_path}: {e}")

    print(f"[INFO] Done '{filename}': {copied} file(s) copied.")
    return copied


def main(filenames: Iterable[str] = FILENAMES,
         src_root: Path = SRC_ROOT,
         dest_root: Path = DEST_ROOT) -> None:
    """
    Run the collection process over each filename in `filenames`.
    Logs progress and a final summary.
    """
    total = 0
    print(f"[START] Collecting files into: {dest_root.resolve()}")
    for name in filenames:
        total += copy_matches(name, src_root, dest_root)
    print(f"[SUMMARY] Total files copied: {total}")


# --- Internal helpers (no public docs) ---

def _sanitize(rel_dir: Path) -> str:
    s = str(rel_dir).strip()
    if not s or s == ".":
        return ""
    # Normalize both POSIX and Windows separators
    s = s.replace("\\", "/")
    s = s.replace("/", "-")
    # Collapse any duplicate hyphens and strip leading/trailing ones
    while "--" in s:
        s = s.replace("--", "-")
    return s.strip("-")


if __name__ == "__main__":
    main()
