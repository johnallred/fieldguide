#!/usr/bin/env python3
"""What is still wrong with this repository five minutes before publishing it.

Run it from the repository root:

    python3 scripts/prepublication.py .

Deliberately NOT part of the CI workflow. CI answers "is this repository
correct"; this answers "is this repository ready to be seen", and those differ:
a placeholder `repo_url` is not a defect until the day you publish, and a check
that fails every build until publication day is a check people learn to ignore.

The patterns below are the ones worth checking. The exclusions are the more
interesting half: a naive version of this script reported 22 hits across both
repositories, of which 4 were real. Every exclusion here is a class of hit that
was false, with the reason, because an audit whose output is 82 per cent noise
gets switched off exactly like a bad docs gate.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

SKIP_DIRS = {".git", "site", ".venv", "__pycache__", ".pytest_cache", ".mypy_cache"}
TEXT_SUFFIXES = {".md", ".py", ".yaml", ".yml", ".toml", ".cfg", ".txt", ".sh", ""}

# Each check: a pattern, and the paths where a hit is legitimate.
#
# scaffold.py and cli.py WRITE "TODO" placeholders into generated pages; that
# is their job. why-a-registry.md and templates-scaffolding.md discuss TODO
# markers as a subject. The tests assert on the placeholder's presence. None of
# those are unfinished work.
#
# example.com is reserved by RFC 2606 precisely for documentation, so a sample
# command using it is correct and a sample command using a real domain is not.
# The placeholder that matters is example.github.io / github.com/example, which
# is a published site pointing its "edit this page" links at nothing.
#
# The URL check is scoped by file ROLE rather than by an allowlist, which is
# the correction that mattered. An allowlist of three files still produced
# seven false hits, because golden paths legitimately show `site_url:` lines
# for a fictional `widget` project. A placeholder URL is a defect when it is
# this repository's own published identity and illustrative anywhere else, so
# the check reads only the files that carry that identity.
# `demonstrations.yaml` is here because it was missed. Its `projects` block
# carries each repository's own URL and those URLs are published on the
# generated `demonstrated` page, so they are this repository's identity by
# every test that matters. The check read only the obvious config files and
# reported "ready to publish" while two placeholder repository links sat on a
# published page. Role-scoping was the right correction; the roster of files
# that carry the role was incomplete, which is a different mistake and an
# easier one to make twice.
OWN_CONFIG = (
    "mkdocs.yml",
    "pyproject.toml",
    "setup.cfg",
    "README.md",
    "LICENSE",
    "demonstrations.yaml",
)

CHECKS: tuple[tuple[str, re.Pattern[str], tuple[str, ...]], ...] = (
    # A TODO check used to live here and has been removed, which is the most
    # useful thing this script has to say.
    #
    # It cannot be scoped by role, because TODO is simultaneously a marker and
    # a word. In this repository the scaffold deliberately writes TODO
    # placeholders, the tests assert on them, and several pages discuss them as
    # a subject. An allowlist reached four files and still produced eleven
    # false hits the moment a new page mentioned the word, and it would need
    # extending every time anyone wrote about placeholders again.
    #
    # The three checks that remain have no false positives on either
    # repository, because each asks about a file's role rather than its
    # vocabulary. A TODO marker is better caught on the diff, by review, where
    # the question "is this line new unfinished work" is answerable.
    (
        "unfilled licence field",
        re.compile(r"Copyright \[|\[year\]|\[fullname\]"),
        (),
    ),
    (
        "container or local path",
        re.compile(r"/mnt/user-data|/home/claude|/tmp/claude"),
        (),
    ),
)


def text_files(root: Path) -> list[Path]:
    return [
        p
        for p in sorted(root.rglob("*"))
        if p.is_file()
        and not SKIP_DIRS & set(p.relative_to(root).parts)
        and p.suffix in TEXT_SUFFIXES
    ]


def main(argv: list[str]) -> int:
    root = Path(argv[1] if len(argv) > 1 else ".").resolve()
    files = text_files(root)
    findings: list[str] = []

    for label, pattern, allowed in CHECKS:
        for path in files:
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            relative = path.relative_to(root).as_posix()
            if relative in allowed or relative == "scripts/prepublication.py":
                continue
            for number, line in enumerate(text.splitlines(), 1):
                # A line that DEFINES a pattern is not a line that leaks what
                # the pattern matches. The first run after the page describing
                # this script was written flagged that page, for quoting the
                # container-path pattern: a seventh false positive of exactly
                # the class the page is about. Scoped by role, like the URL
                # check above, rather than by naming the file.
                if "re.compile(" in line or "re.search(" in line:
                    continue
                if pattern.search(line):
                    findings.append(f"  {relative}:{number}  {label}\n      {line.strip()[:88]}")

    placeholder_url = re.compile(r"github\.com/example/|example\.github\.io")
    for name in OWN_CONFIG:
        path = root / name
        if not path.exists():
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if placeholder_url.search(line):
                findings.append(
                    f"  {name}:{number}  placeholder URL in this repository's own identity"
                    f"\n      {line.strip()[:88]}"
                )

    licence = root / "LICENSE"
    if not licence.exists():
        findings.append("  LICENSE  missing entirely")
    elif not re.search(r"Copyright \(c\) \d{4} \S+ \S+", licence.read_text(encoding="utf-8")):
        findings.append("  LICENSE  has no real copyright holder")

    print(f"examined {len(files)} files under {root.name}")
    if findings:
        print(f"\nnot ready to publish, {len(findings)} finding(s):\n")
        print("\n".join(findings))
        return 1
    print("ready to publish")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
