#!/usr/bin/env python3
"""Compare a course in the repository with the course the LMS is serving.

    python3 drills/lms_admin.py                                  # embedded samples
    python3 drills/lms_admin.py course.txt modules.json progress.csv

Three inputs:

- course.txt: the course as the repository defines it, one module per line,
  in order, with whether it should be published.
- modules.json: the modules the LMS reports, in the shape a Canvas
  `GET /api/v1/courses/:course_id/modules` call returns (name, position,
  published).
- progress.csv: one row per enrolled learner, with their section and the last
  module they completed (0 for none).

The report answers three questions an administrator is asked every week: does
the live course match its source, where do learners stop, and who never
started. The learners and their progress are invented for the exercise.
"""

from __future__ import annotations

import csv
import io
import json
import sys
from collections import Counter

COURSE = """\
1 | What you will build | published
2 | Configure retries | published
3 | Choosing a value | published
4 | Diagnose an exhausted budget | published
5 | Check yourself | published
"""

MODULES = """\
[
  {"name": "What you will build", "position": 1, "published": true},
  {"name": "Configure retries", "position": 2, "published": true},
  {"name": "Diagnose an exhausted budget", "position": 3, "published": true},
  {"name": "Choosing a value", "position": 4, "published": false},
  {"name": "Retries FAQ (old)", "position": 5, "published": true}
]
"""

PROGRESS = """\
learner,section,completed
l01,spring,5
l02,spring,5
l03,spring,4
l04,spring,2
l05,spring,2
l06,spring,2
l07,spring,1
l08,spring,0
l09,spring,5
l10,spring,2
l11,spring,3
l12,spring,2
l13,partners,0
l14,partners,0
l15,partners,1
l16,partners,0
l17,partners,2
l18,partners,0
l19,partners,0
l20,partners,2
"""


def parse_course(text: str) -> list[tuple[str, bool]]:
    rows = []
    for line in text.splitlines():
        if line.strip():
            _, name, state = (part.strip() for part in line.split("|"))
            rows.append((name, state == "published"))
    return rows


def report(course_text: str, modules_text: str, progress_text: str) -> None:
    course = parse_course(course_text)
    modules = sorted(json.loads(modules_text), key=lambda m: m["position"])
    live = {m["name"]: m for m in modules}
    wanted = dict(course)

    print("step 1: does the live course match its source?")
    drift = 0
    for name, published in course:
        if name not in live:
            print(f"  {'missing from the LMS:':<26}{name}")
            drift += 1
        elif live[name]["published"] != published:
            state = "published" if live[name]["published"] else "unpublished"
            print(f"  {state + ' in the LMS:':<26}{name}")
            drift += 1
    for m in modules:
        if m["name"] not in wanted:
            print(f"  {'only in the LMS:':<26}{m['name']}")
            drift += 1
    source_order = [n for n, _ in course if n in live]
    live_order = [m["name"] for m in modules if m["name"] in wanted]
    if source_order != live_order:
        print(f"  {'order differs:':<26}{' > '.join(live_order)}")
        drift += 1
    print(f"  {drift} difference(s)")
    print()

    rows = list(csv.DictReader(io.StringIO(progress_text)))
    enrolled = len(rows)
    print("step 2: where do learners stop?")
    previous = enrolled
    worst = (0, "")
    for position, (name, _) in enumerate(course, 1):
        done = sum(1 for r in rows if int(r["completed"]) >= position)
        lost = previous - done
        if lost > worst[0]:
            worst = (lost, name)
        print(f"  {position} {name:<30} {done:>3}/{enrolled}  (-{lost})")
        previous = done
    print(f"  largest drop: {worst[1]} (-{worst[0]})")
    print()

    print("step 3: who never started?")
    by_section = Counter(r["section"] for r in rows)
    idle = Counter(r["section"] for r in rows if r["completed"] == "0")
    for section in by_section:
        print(f"  {section:<10} {idle[section]:>2}/{by_section[section]} never started")


def main() -> int:
    if len(sys.argv) == 4:
        texts = []
        for path in sys.argv[1:]:
            with open(path, encoding="utf-8") as handle:
                texts.append(handle.read())
        report(*texts)
    else:
        report(COURSE, MODULES, PROGRESS)
    return 0


if __name__ == "__main__":
    sys.exit(main())
