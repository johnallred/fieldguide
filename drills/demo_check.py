#!/usr/bin/env python3
"""Check a demo script and its last rehearsal before anyone performs it.

    python3 drills/demo_check.py                              # embedded samples
    python3 drills/demo_check.py demo.txt rehearsal.csv       # your demo

A demo is performed, not cloned, so its failure modes differ from a sample's:
it runs over its slot, it buries the result under setup, it works only on the
author's laptop, and when a live step breaks there is nothing to show instead.

demo.txt declares the slot, the setup every presenter gets, and the beats in
order: `N | kind | minutes | command | fallback`. `kind` is payoff, context,
detail or close. `fallback` is what to show if the live step fails, or `-`.
Persona variants replace named beats and share the rest.

rehearsal.csv records the last dry run by someone other than the author: each
beat's seconds and whether it worked.

The demo and rehearsal are invented for the exercise.
"""

from __future__ import annotations

import csv
import io
import re
import sys

DEMO = """\
title: Retries that survive a restarting upstream
slot: 10
setup: WIDGET_TOKEN
1 | context | 3 | open slides/architecture.pdf | -
2 | detail | 3 | widget config set retries 3 | -
3 | detail | 2 | widget sync --source /Users/jallred/demo-data | -
4 | payoff | 3 | widget sync --watch --upstream $FLAKY_UPSTREAM | -
5 | close | 1 | open slides/next-steps.pdf | -
variant data-engineer: 3 | detail | 2 | widget sync --source warehouse://demo | -
"""

REHEARSAL = """\
beat,seconds,worked
1,210,yes
2,150,yes
3,95,no
4,240,no
5,50,yes
"""

DEMO_FIXED = """\
title: Retries that survive a restarting upstream
slot: 10
setup: WIDGET_TOKEN, FLAKY_UPSTREAM
1 | payoff | 2 | widget sync --watch --upstream $FLAKY_UPSTREAM | recordings/survives-restart.mp4
2 | detail | 2 | widget config set retries 3 | screenshots/config.png
3 | detail | 2 | widget sync --source ./demo-data | recordings/sync.mp4
4 | context | 1 | open slides/architecture.pdf | -
5 | close | 1 | open slides/next-steps.pdf | -
variant data-engineer: 3 | detail | 2 | widget sync --source warehouse://demo | recordings/warehouse.mp4
"""

REHEARSAL_FIXED = """\
beat,seconds,worked
1,130,yes
2,110,yes
3,100,yes
4,55,yes
5,45,yes
"""

BEAT = re.compile(r"^(?:variant ([\w-]+): )?(\d+) \| (\w+) \| (\d+) \| (.+?) \| (.+)$")
AUTHOR_ONLY = re.compile(r"/Users/\w+|/home/\w+|~/|localhost")
LIVE = ("payoff", "detail")


def parse(text: str) -> tuple[dict, list[dict], dict[str, list[dict]]]:
    meta, beats, variants = {}, [], {}
    for line in text.splitlines():
        match = BEAT.match(line)
        if match:
            variant, n, kind, minutes, command, fallback = match.groups()
            beat = {"n": int(n), "kind": kind, "minutes": int(minutes),
                    "command": command, "fallback": fallback,
                    "name": f"{variant} beat {n}" if variant else f"beat {n}"}
            (variants.setdefault(variant, []) if variant else beats).append(beat)
        elif ": " in line:
            key, value = line.split(": ", 1)
            meta[key] = value
    return meta, beats, variants


def check(demo_text: str, rehearsal_text: str) -> int:
    meta, beats, variants = parse(demo_text)
    slot = int(meta["slot"])
    setup = {v.strip() for v in meta["setup"].split(",")}
    found = []

    if beats[0]["kind"] != "payoff":
        payoff = next(b["n"] for b in beats if b["kind"] == "payoff")
        found.append(f"ORDER     the result is beat {payoff}; show it first")
    planned = sum(b["minutes"] for b in beats)
    if planned > slot:
        found.append(f"TIME      planned {planned} minutes for a {slot}-minute slot")
    for beat in beats + [b for vs in variants.values() for b in vs]:
        if AUTHOR_ONLY.search(beat["command"]):
            found.append(f"AUTHOR    {beat['name']} uses a path on the author's machine")
        for var in re.findall(r"\$(\w+)", beat["command"]):
            if var not in setup:
                found.append(f"AUTHOR    {beat['name']} needs ${var}, which setup does not provide")
        if beat["kind"] in LIVE and beat["fallback"] == "-":
            found.append(f"FALLBACK  live {beat['name']} has nothing to show if it fails")

    runs = list(csv.DictReader(io.StringIO(rehearsal_text)))
    for run in runs:
        if run["worked"] != "yes":
            found.append(f"REHEARSAL beat {run['beat']} failed in the last dry run")
    actual = sum(int(r["seconds"]) for r in runs) / 60
    if actual > slot:
        found.append(f"REHEARSAL the dry run took {actual:.1f} minutes")

    for line in found:
        print(line)
    print(f"{len(found)} finding(s)")
    shared = {b["n"] for b in beats} - {b["n"] for vs in variants.values() for b in vs}
    for name in variants:
        print(f"variant {name}: shares {len(shared)} of {len(beats)} beats")
    return len(found)


def main() -> int:
    args = sys.argv[1:]
    if len(args) == 2:
        texts = [open(path, encoding="utf-8").read() for path in args]
        return 1 if check(*texts) else 0
    print("== first draft")
    check(DEMO, REHEARSAL)
    print("\n== revised")
    return 1 if check(DEMO_FIXED, REHEARSAL_FIXED) else 0


if __name__ == "__main__":
    sys.exit(main())
