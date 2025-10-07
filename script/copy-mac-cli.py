#!/usr/bin/env python3
"""
Generate a Markdown file with the `--help` output of a set of CLI tools.

- No external dependencies (stdlib only).
- Hardcoded output path and commands list at the top.
- Each section is fenced in ``` for Markdown.
- Safe execution with timeouts and graceful error messages.
"""

import os
import shlex
import subprocess
import sys
from datetime import datetime
from typing import List, Tuple, Optional

# =========================
# Hardcoded configuration
# =========================
DEST_DIR = "./temp/data"
DEST_FILE = os.path.join(DEST_DIR, "mac-os-terminal-cli.md")

# List of commands to document. You may include commands with or without --help.
# If a command already contains -h/--help, the script will use it as-is.
HELP_COMMANDS: List[str] = [
    "fd",
    "clingy",
    "dart",
    "dust",
    "gh",
    "brew",
    "go",
    "jd",
    "jq",
    "keyring",
    "rg",
    "scc",
    "python",
    "tree",
    "trivy",
    "xsv",
    "yq",
    "zig",
    "node",
    "yarn",
    "npm",
    "uv",
    "npx zx"  # example with an argument before --help
]
HELP_COMMANDS.sort()

# Global settings
HELP_FLAG_DEFAULT = "--help"   # what to append if not present
RUN_TIMEOUT_SECONDS = 15       # be conservative; adjust as you like
ENCODING = "utf-8"

# =========================
# Helper functions
# =========================
def normalize_command(cmd: str) -> List[str]:
    """
    Ensure the command includes a help flag. If -h/--help is already present,
    use as-is. Otherwise append the default help flag.
    Returns a list suitable for subprocess.run (no shell).
    """
    parts = shlex.split(cmd)
    if any(tok in ("-h", "--help") for tok in parts):
        return parts
    return parts + [HELP_FLAG_DEFAULT]

def run_help_command(cmd: str, timeout: int = RUN_TIMEOUT_SECONDS) -> Tuple[str, int, Optional[str]]:
    """
    Run a help command (adding --help if needed), capturing stdout/stderr.
    Returns (stdout_text, returncode, resolved_exe_or_none).
    If the command's executable can't be found, returncode will be 127.
    """
    parts = normalize_command(cmd)
    exe = parts[0]

    # Try to locate the executable the cross-platform way by just attempting run()
    try:
        proc = subprocess.run(
            parts,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # capture both in one stream
            timeout=timeout,
            check=False,
            text=True,
            encoding=ENCODING
        )
        return proc.stdout, proc.returncode, exe
    except FileNotFoundError:
        msg = f"Error: '{exe}' not found on PATH."
        return msg, 127, None
    except subprocess.TimeoutExpired as e:
        combined = (e.stdout or "") + (e.stderr or "")
        msg = "Error: command timed out."
        if combined.strip():
            msg += f"\n\nPartial output before timeout:\n{combined}"
        return msg, 124, exe
    except Exception as e:
        return f"Unexpected error: {e!r}", 1, exe

def write_header(f, title: str, commands: List[str]) -> None:
    f.write(f"# {title}\n\n")
    f.write("## Commands covered\n\n")
    for c in commands:
        # Heading is based on the first token (e.g., 'npx' for 'npx zx')
        heading = shlex.split(c)[0] if c.strip() else c
        f.write(f"- `{c}` (section: **{heading}**)\n")
    f.write("\n---\n\n")

def write_help_section(f, section_title: str, command: str, output: str, rc: int) -> None:
    f.write(f"## {section_title}\n\n")
    f.write(f"**Command:** `{command if ('-h' in command or '--help' in command) else command + ' ' + HELP_FLAG_DEFAULT}`\n\n")
    f.write("```text\n")
    f.write(output.rstrip() + "\n")
    f.write("```\n\n")
    f.write("---\n\n")

def main() -> int:
    os.makedirs(DEST_DIR, exist_ok=True)

    with open(DEST_FILE, "w", encoding=ENCODING) as f:
        write_header(f, "MacOS terminal commands", HELP_COMMANDS)

        for raw_cmd in HELP_COMMANDS:
            # Section title uses first token as the "tool" name
            section_title = shlex.split(raw_cmd)[0] if raw_cmd.strip() else raw_cmd
            stdout_text, rc, _exe = run_help_command(raw_cmd)

            # If a tool prints nothing but returns 0, keep the section informative.
            if not stdout_text.strip() and rc == 0:
                stdout_text = "(No output produced by help command.)"

            write_help_section(f, section_title, raw_cmd, stdout_text, rc)

    print(f"Wrote Markdown to: {DEST_FILE}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
