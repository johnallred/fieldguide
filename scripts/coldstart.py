#!/usr/bin/env python3
"""Run the README quick start in a fresh virtual environment.

A quick start is a promise that someone who has just cloned the repository can
paste these lines and have them work. Nothing checked that. The block was
executable-looking prose, and two lines in it were wrong:

  - `fieldguide render site` read a built site, with no build before it. It
    only worked because `site/` was committed, so the promise held for the
    author and would have failed for the first reader.
  - `fieldguide new diataxis` cannot succeed in this repository at all. Every
    registered concept already has a page, and an unregistered one is refused,
    so the command exits 2 either way.

Neither is visible from reading. Both are obvious the first time the block is
run somewhere clean, which is the whole argument for this script.

The lines are read out of README.md rather than copied here. A list of commands
maintained next to the list of commands is a second place to update, and the
second place is the one that rots. This is the same contract `tests/
test_drills.py` holds for the drills: the thing that runs and the thing the
reader reads are one text.

Two directives are honoured, both written as ordinary trailing comments so the
block stays readable:

    <command>    # exits 2: <why>                 expect that code, not zero
    <command>    # ... not run by the cold start  skip it, and say why

An expected non-zero exit is a claim like any other, so a line marked `exits 2`
that starts succeeding fails this script too.

Usage:
    python3 scripts/coldstart.py            # from the repository root
    python3 scripts/coldstart.py --keep     # leave the sandbox for inspection
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import venv
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Build output and caches. Copying them would mean the "fresh" environment
# started with the previous run's artifacts, which is the opposite of the point.
IGNORE = shutil.ignore_patterns(
    ".git", "site", "__pycache__", ".pytest_cache", ".venv", "venv",
    "*.egg-info", ".DS_Store",
)

SKIP = re.compile(r"not run by the cold start", re.I)
EXPECT = re.compile(r"\bexits (\d+)\b", re.I)
# A command and its optional trailing comment. Two spaces or more, so a `#`
# inside a command is not mistaken for one.
LINE = re.compile(r"^(?P<cmd>.*?)(?:\s{2,}#\s*(?P<comment>.*))?$")


@dataclass
class Step:
    command: str
    expected: int = 0
    skip: str = ""


def quick_start(readme: str) -> list[Step]:
    """The commands in the first fenced block under '## Quick start'."""
    section = readme.split("## Quick start", 1)
    if len(section) != 2:
        raise SystemExit("README has no '## Quick start' heading")
    block = re.search(r"```bash\n(.*?)```", section[1], re.S)
    if not block:
        raise SystemExit("the Quick start section has no bash block")

    steps: list[Step] = []
    for raw in block.group(1).splitlines():
        if not raw.strip():
            continue
        parts = LINE.match(raw)
        command = parts.group("cmd").strip()
        comment = parts.group("comment") or ""
        if not command:
            continue
        if SKIP.search(comment):
            steps.append(Step(command, skip=comment.strip()))
            continue
        expected = EXPECT.search(comment)
        steps.append(Step(command, expected=int(expected.group(1)) if expected else 0))
    return steps


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--keep", action="store_true",
                        help="leave the sandbox in place for inspection")
    args = parser.parse_args()

    steps = quick_start((REPO / "README.md").read_text(encoding="utf-8"))
    print(f"{len(steps)} line(s) in the quick start\n")

    sandbox = Path(tempfile.mkdtemp(prefix="coldstart-"))
    checkout, env = sandbox / "repo", sandbox / "venv"
    try:
        shutil.copytree(REPO, checkout, ignore=IGNORE)
        venv.EnvBuilder(with_pip=True, clear=True).create(env)

        bin_dir = env / ("Scripts" if sys.platform == "win32" else "bin")
        # Inherit the real environment and override only what has to change.
        # The first version of this built a minimal env from scratch and pip
        # could not reach an index, because proxy and certificate variables
        # live there; eleven lines then "failed" for reasons that had nothing
        # to do with the repository. A harness that fakes the environment
        # tests the harness.
        shell_env = dict(os.environ)
        shell_env["PATH"] = os.pathsep.join(
            [str(bin_dir), shell_env.get("PATH", "")]
        )
        shell_env["VIRTUAL_ENV"] = str(env)
        # These would let the sandbox import the package from somewhere other
        # than its own install, which is the one thing a cold start must not
        # allow.
        shell_env.pop("PYTHONPATH", None)
        shell_env.pop("PYTHONHOME", None)

        failures: list[str] = []
        for step in steps:
            if step.skip:
                print(f"  skip   {step.command}\n           {step.skip}")
                continue
            result = subprocess.run(
                step.command, shell=True, cwd=checkout, env=shell_env,
                capture_output=True, text=True, timeout=900,
            )
            ok = result.returncode == step.expected
            want = "" if step.expected == 0 else f" (expected {step.expected})"
            print(f"  {'ok  ' if ok else 'FAIL'}   {step.command}{want}")
            if not ok:
                failures.append(step.command)
                tail = (result.stdout + result.stderr).strip().splitlines()[-8:]
                for line in tail:
                    print(f"           {line}")

        print()
        if failures:
            print(f"{len(failures)} of {len(steps)} quick start line(s) failed:")
            for command in failures:
                print(f"  {command}")
            return 1
        print(f"the quick start runs clean from an empty environment")
        return 0
    finally:
        if args.keep:
            print(f"\nsandbox kept at {sandbox}")
        else:
            shutil.rmtree(sandbox, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
