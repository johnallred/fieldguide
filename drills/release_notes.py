#!/usr/bin/env python3
"""Check human-written release notes against the commits they summarise.

    python3 drills/release_notes.py                          # embedded samples
    python3 drills/release_notes.py --raw commits.txt        # the commit log, grouped
    python3 drills/release_notes.py commits.txt notes.md     # check a draft

commits.txt is a Conventional Commits log since the last release, one subject
per line, with the previous version on a `# since` line. notes.md is the draft
release section in Keep a Changelog form. The check enforces five rules:

- the version bump matches the commits under Semantic Versioning: any breaking
  change (`!`) needs a major bump, any feat a minor one, otherwise a patch;
- every section heading is a Keep a Changelog category;
- every user-facing commit (feat, fix, perf) appears in the notes;
- no internal commit (refactor, ci, docs, chore, test, build, style) does;
- every breaking change tells the reader how to upgrade.

The release date must be ISO 8601. The commits are invented for the exercise.
"""

from __future__ import annotations

import re
import sys

COMMITS = """\
# since 2.5.3
feat!: rename retries to max_attempts (#412)
feat(cli): add --dry-run to sync (#415)
fix: include the HTTP status in RetryExhausted (#418)
fix(auth): refresh tokens before expiry (#420)
refactor: extract backoff calculation (#421)
ci: cache pip downloads (#423)
docs: fix typo in quickstart (#424)
chore: bump requests to 2.32.3 (#425)
"""

NOTES = """\
## [2.6.0] - 11/20/2026

### Improvements
- The retry argument is now `max_attempts`. (#412)
- `sync --dry-run` shows what would change. (#415)

### Fixed
- Tokens are refreshed before they expire. (#420)
- Extracted the backoff calculation into its own module. (#421)
"""

NOTES_FIXED = """\
## [3.0.0] - 2026-11-20

### Changed
- **Breaking:** `retries` is now `max_attempts`, and it counts attempts, not retries. To upgrade: rename the argument and add one, so `retries=3` becomes `max_attempts=4`. (#412)

### Added
- `sync --dry-run` shows what a sync would change without changing it. (#415)

### Fixed
- `RetryExhausted` now includes the HTTP status, so you can tell a rejection (429) from an outage (503). (#418)
- Tokens are refreshed before they expire, so long syncs no longer fail at the one-hour mark. (#420)
"""

CATEGORIES = ("Added", "Changed", "Deprecated", "Removed", "Fixed", "Security")
USER = ("feat", "fix", "perf")
SUBJECT = re.compile(r"^(\w+)(?:\([\w-]+\))?(!)?: (.*) \(#(\d+)\)$")


def parse_commits(text: str) -> tuple[str, list[dict]]:
    previous, commits = "", []
    for line in text.splitlines():
        if line.startswith("# since "):
            previous = line.split()[-1]
        elif line.strip():
            kind, bang, subject, pr = SUBJECT.match(line).groups()
            commits.append({"type": kind, "breaking": bool(bang), "subject": subject, "pr": pr})
    return previous, commits


def raw(commits_text: str) -> None:
    _, commits = parse_commits(commits_text)
    for kind in dict.fromkeys(c["type"] for c in commits):
        print(kind)
        for c in commits:
            if c["type"] == kind:
                print(f"  {c['subject']} (#{c['pr']})")


def bump(old: str, new: str) -> str:
    a, b = [list(map(int, v.split("."))) for v in (old, new)]
    if b[0] > a[0]:
        return "major"
    return "minor" if b[1] > a[1] else "patch"


def check(commits_text: str, notes_text: str) -> int:
    previous, commits = parse_commits(commits_text)
    head = re.search(r"^## \[(\d+\.\d+\.\d+)\] - (\S+)", notes_text, re.M)
    version, date = head.groups()
    found = []

    needed = ("major" if any(c["breaking"] for c in commits)
              else "minor" if any(c["type"] == "feat" for c in commits) else "patch")
    if bump(previous, version) != needed:
        found.append(f"VERSION  {previous} -> {version} is a {bump(previous, version)} bump; "
                     f"the commits need {needed}")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
        found.append(f"DATE     {date} is not ISO 8601 (YYYY-MM-DD)")
    for heading in re.findall(r"^### (.+)$", notes_text, re.M):
        if heading not in CATEGORIES:
            found.append(f"HEADING  '{heading}' is not a Keep a Changelog category")

    entries = {pr: line for line in notes_text.splitlines()
               for pr in re.findall(r"\(#(\d+)\)", line)}
    for c in commits:
        listed = c["pr"] in entries
        if c["type"] in USER and not listed:
            found.append(f"MISSING  #{c['pr']} ({c['type']}: {c['subject']}) is not in the notes")
        if c["type"] not in USER and listed:
            found.append(f"INTERNAL #{c['pr']} ({c['type']}) is in the notes")
        if c["breaking"] and listed and "To upgrade" not in entries[c["pr"]]:
            found.append(f"BREAKING #{c['pr']} says what changed but not how to upgrade")
    for line in found:
        print(line)
    print(f"{len(found)} finding(s)")
    return len(found)


def main() -> int:
    args = sys.argv[1:]
    if args[:1] == ["--raw"]:
        with open(args[1], encoding="utf-8") as handle:
            raw(handle.read())
        return 0
    if len(args) == 2:
        texts = []
        for path in args:
            with open(path, encoding="utf-8") as handle:
                texts.append(handle.read())
        return 1 if check(*texts) else 0
    raw(COMMITS)
    print("\n== draft")
    check(COMMITS, NOTES)
    print("\n== revised")
    return 1 if check(COMMITS, NOTES_FIXED) else 0


if __name__ == "__main__":
    sys.exit(main())
