#!/usr/bin/env python3
"""Find the pages whose evidence changed after the page last described it.

    python3 scripts/freshness.py             # report
    python3 scripts/freshness.py --issue     # report, and keep one GitHub issue current

The freshness-monitoring page argues that age is not staleness: the useful
check compares a page against the thing it documents. In this guide that
relation is written down already. Every entry in `demonstrations.yaml` names a
concept and the file that demonstrates it, in this repository, `docpack` or
`coldlab`, with a note describing what the file does.

So for each entry this compares two dates. The claim's date is when its note
line was last written, from `git blame`. The evidence's date is when the
artifact last changed, from `git log` for this repository and from the GitHub
API for the other two. Evidence newer than the claim means the note, and the
concept page that relies on it, may no longer describe the code. That is a
candidate for review, not a verdict: the change may not touch what the note
says.

With `--issue` it keeps a single open issue labelled `freshness` in step with
the report: created when there are candidates, updated when they change, closed
when there are none. It runs weekly in `.github/workflows/freshness.yml`.

Needs this repository's full history (`fetch-depth: 0` in Actions).
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from github_api import GitHub  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
OWNER = "johnallred"
LABEL = "freshness"
TITLE = "Pages whose evidence changed since they described it"
ENTRY = re.compile(
    r"^  - concept: (?P<concept>\S+)\n    project: (?P<project>\S+)\n"
    r"    artifact: (?P<artifact>.+)\n    extent: (?P<extent>\S+)\n    note: ", re.M)
#: An optional line after the note: the date someone last read the note
#: against its evidence and found it still true, without needing to reword it.
REVIEWED = re.compile(r"^    note: .*\n    reviewed: (\d{4}-\d{2}-\d{2})$", re.M)


def entries(text: str) -> list[dict]:
    """Each demonstration entry, with the line number its note starts on."""
    out = []
    for match in ENTRY.finditer(text):
        found = match.groupdict()
        found["artifact"] = found["artifact"].strip().strip('"')
        found["line"] = text.count("\n", 0, match.end()) + 1
        reviewed = REVIEWED.match(text, text.rfind("\n", 0, match.end()) + 1)
        found["reviewed"] = reviewed.group(1) if reviewed else None
        out.append(found)
    return out


def git(*args: str, cwd: Path = REPO) -> str:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True,
                          check=True).stdout


def claim_time(line: int) -> datetime:
    porcelain = git("blame", "-L", f"{line},{line}", "--porcelain", "demonstrations.yaml")
    seconds = int(re.search(r"^committer-time (\d+)$", porcelain, re.M).group(1))
    return datetime.fromtimestamp(seconds, timezone.utc)


def local_time(path: str, cwd: Path = REPO) -> datetime | None:
    stamp = git("log", "-1", "--format=%cI", "--", path.rstrip("/"), cwd=cwd).strip()
    return datetime.fromisoformat(stamp) if stamp else None


def remote_time(api: GitHub, project: str, path: str) -> datetime | None:
    commits = api.get(f"/repos/{OWNER}/{project}/commits", path=path.rstrip("/"), per_page=1)
    if not commits:
        return None
    return datetime.fromisoformat(commits[0]["commit"]["committer"]["date"].replace("Z", "+00:00"))


def candidates(api: GitHub, clones: Path | None = None) -> tuple[list[dict], list[str]]:
    """Compare every claim with its evidence.

    `clones`, if given, is a directory holding clones of the other projects,
    read with git instead of the API: the same answer, for local runs that
    should not spend an unauthenticated rate limit of 60 an hour.
    """
    found, unknown = [], []
    cache: dict[tuple[str, str], datetime | None] = {}
    for entry in entries((REPO / "demonstrations.yaml").read_text(encoding="utf-8")):
        key = (entry["project"], entry["artifact"])
        if key not in cache:
            if entry["project"] == "fieldguide":
                cache[key] = local_time(entry["artifact"])
            elif clones is not None:
                cache[key] = local_time(entry["artifact"], cwd=clones / entry["project"])
            else:
                cache[key] = remote_time(api, entry["project"], entry["artifact"])
        changed = cache[key]
        if changed is None:
            unknown.append(f"{entry['project']}/{entry['artifact']} ({entry['concept']})")
            continue
        claimed = claim_time(entry["line"])
        if entry["reviewed"]:
            # The end of the review day, so a change made that day counts as seen.
            reviewed = datetime.fromisoformat(entry["reviewed"] + "T23:59:59+00:00")
            claimed = max(claimed, reviewed)
        if changed > claimed:
            found.append(dict(entry, claimed=claimed, changed=changed,
                              days=(changed - claimed).days))
    found.sort(key=lambda e: e["changed"] - e["claimed"], reverse=True)
    return found, unknown


def render(found: list[dict], unknown: list[str], total: int) -> str:
    lines = [f"{len(found)} of {total} demonstration notes describe a file that has changed "
             "since the note was written.", ""]
    if found:
        lines += ["| Concept | Evidence | Note written | File changed |", "|---|---|---|---|"]
        for e in found:
            lines.append(f"| [{e['concept']}](docs/concepts/{e['concept']}.md) | "
                         f"`{e['project']}/{e['artifact']}` | {e['claimed']:%Y-%m-%d} | "
                         f"{e['changed']:%Y-%m-%d} |")
        lines += ["", "Read each note against its file. If it still holds, add or update a "
                  "`reviewed: YYYY-MM-DD` line under the note; if not, correct the note "
                  "and the concept page."]
    if unknown:
        lines += ["", "No history found for: " + ", ".join(unknown)]
    return "\n".join(lines) + "\n"


def sync_issue(api: GitHub, body: str, has_candidates: bool) -> str:
    repo = f"/repos/{OWNER}/fieldguide"
    open_issues = [i for i in api.paginate(f"{repo}/issues", labels=LABEL, state="open",
                                           per_page=100) if "pull_request" not in i]
    issue = open_issues[0] if open_issues else None
    if not has_candidates:
        if issue:
            api.request("PATCH", f"{repo}/issues/{issue['number']}",
                        body={"state": "closed", "state_reason": "completed"})
            return f"closed #{issue['number']}"
        return "no issue needed"
    if issue is None:
        created, _ = api.request("POST", f"{repo}/issues",
                                 body={"title": TITLE, "body": body, "labels": [LABEL]})
        return f"opened #{created['number']}"
    if issue.get("body") != body:
        api.request("PATCH", f"{repo}/issues/{issue['number']}", body={"body": body})
        return f"updated #{issue['number']}"
    return f"#{issue['number']} already current"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--issue", action="store_true", help="keep the GitHub issue in step")
    parser.add_argument("--clones", type=Path,
                        help="read docpack and coldlab from clones in this directory, not the API")
    args = parser.parse_args(argv)
    api = GitHub()
    total = len(entries((REPO / "demonstrations.yaml").read_text(encoding="utf-8")))
    found, unknown = candidates(api, args.clones)
    body = render(found, unknown, total)
    print(body, end="")
    if args.issue:
        if not os.environ.get("GITHUB_TOKEN"):
            print("--issue needs GITHUB_TOKEN", file=sys.stderr)
            return 2
        print(sync_issue(api, body, bool(found)))
    if api.remaining is not None:
        print(f"GitHub API requests remaining this hour: {api.remaining}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
