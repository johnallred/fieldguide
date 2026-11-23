#!/usr/bin/env python3
"""Decide what to teach from what readers do, not from what the expert says.

    python3 drills/task_analysis.py                           # embedded samples
    python3 drills/task_analysis.py tasks.txt tickets.txt survey.txt

Three inputs, each a plain text file a reader can write by hand:

- tasks.txt: a task inventory. Each task lists its steps (`-`) and decision
  points (`?`), each tagged with where it came from: `said` (the expert's
  description) or `observed` (watching someone do it).
- tickets.txt: one support question per line, tagged with the task it is about
  and its cause: `knowledge` (they did not know how) or `environment` (the
  product, console or setup got in the way).
- survey.txt: how much prior experience readers report, as counts.

The output is the analysis that comes before any objective is written: what
the expert left out, which tasks readers actually struggle with, which of
those are not a teaching problem at all, and who the readers are.

The tickets and survey counts in the embedded samples are invented for the
exercise, and the page says so. The arithmetic over them is real.
"""

from __future__ import annotations

import sys
from collections import Counter

TASKS = """\
T1 configure retries | taught | high
  - set retries on the client [said]
  - pick a value for the workload [said]
  ? is a caller waiting on the response [observed]
  ? does the upstream restart during deploys [observed]
T2 diagnose an exhausted retry budget | not taught | high
  - read the status code in RetryExhausted [said]
  ? is it 429 (rejected) or 503 (down) [observed]
  ? is the budget shared across workers [observed]
  - check the upstream status page [observed]
T3 rotate the API key | not taught | medium
  - open the key page in the console [said]
  - create the new key [said]
  ? which key is production using right now [observed]
  - deploy the new key before revoking the old [observed]
T4 install the client | taught | low
  - pip install widget-client [said]
  ? is the Python version supported [observed]
"""

TICKETS = """\
T2 knowledge | gave up after 3 retries, is the service down?
T2 knowledge | RetryExhausted 429, what does that mean
T2 knowledge | retries do nothing when every worker fails at once
T2 knowledge | how do I tell rejected from unavailable
T2 knowledge | job stops at night with RetryExhausted
T2 environment | status page link in the error is broken
T2 knowledge | 429 after raising retries to 10
T2 knowledge | should I raise retries when I see 503
T3 environment | cannot find where to create a key
T3 environment | console shows two keys, which is live?
T3 environment | key page times out
T3 knowledge | revoked old key and production broke
T3 environment | new key not shown after creating it
T3 environment | no way to label keys in the console
T1 knowledge | does retries=3 mean three requests?
T1 knowledge | what retry value for a web request
T1 knowledge | retries make my API endpoint slow
T4 environment | pip install fails on Python 3.8
T4 environment | wheel not available for my platform
"""

SURVEY = """\
never used a client with retries | 11
used retries in another client | 23
used retries in this client | 6
"""


def parse_tasks(text: str) -> list[dict]:
    tasks = []
    for line in text.splitlines():
        if not line.strip():
            continue
        if not line.startswith(" "):
            head, taught, criticality = (part.strip() for part in line.split("|"))
            tid, name = head.split(" ", 1)
            tasks.append({"id": tid, "name": name, "taught": taught == "taught",
                          "criticality": criticality, "items": []})
        else:
            kind = line.strip()[0]
            source = line.rsplit("[", 1)[1].rstrip("]")
            tasks[-1]["items"].append((kind, source))
    return tasks


def parse_tickets(text: str) -> list[tuple[str, str]]:
    rows = []
    for line in text.splitlines():
        if line.strip():
            head = line.split("|", 1)[0].split()
            rows.append((head[0], head[1]))
    return rows


def parse_survey(text: str) -> list[tuple[str, int]]:
    rows = []
    for line in text.splitlines():
        if line.strip():
            label, count = line.rsplit("|", 1)
            rows.append((label.strip(), int(count)))
    return rows


def report(tasks_text: str, tickets_text: str, survey_text: str) -> None:
    tasks = parse_tasks(tasks_text)
    tickets = parse_tickets(tickets_text)
    survey = parse_survey(survey_text)

    print("step 1: what the expert said, against what was observed")
    said_steps = sum(1 for t in tasks for k, s in t["items"] if k == "-" and s == "said")
    steps = sum(1 for t in tasks for k, _ in t["items"] if k == "-")
    said_decisions = sum(1 for t in tasks for k, s in t["items"] if k == "?" and s == "said")
    decisions = sum(1 for t in tasks for k, _ in t["items"] if k == "?")
    print(f"  steps the expert described:     {said_steps}/{steps}")
    print(f"  decisions the expert described: {said_decisions}/{decisions}")
    print()

    print("step 2: which tasks readers struggle with, and why")
    by_task = Counter(tid for tid, _ in tickets)
    knowledge = Counter(tid for tid, cause in tickets if cause == "knowledge")
    print("  task                                    tickets  knowledge  taught  action")
    for t in sorted(tasks, key=lambda t: -by_task[t["id"]]):
        n, k = by_task[t["id"]], knowledge[t["id"]]
        if n and (n - k) > n / 2:
            action = "fix the product, not the page"
        elif not t["taught"]:
            action = "teach it"
        else:
            action = "keep, check it works"
        label = f"{t['id']} {t['name']}"
        taught = "yes" if t["taught"] else "no"
        print(f"  {label:<40}{n:>4}    {k:>3}/{n:<3}    {taught:<6}  {action}")
    print()

    print("step 3: who the readers are")
    total = sum(count for _, count in survey)
    for label, count in survey:
        print(f"  {label:<34} {count:>3}  ({round(100 * count / total)}%)")
    experienced = total - survey[0][1]
    print(f"  already used retries somewhere: {experienced}/{total} "
          f"({round(100 * experienced / total)}%)")


def main() -> int:
    if len(sys.argv) == 4:
        texts = []
        for path in sys.argv[1:]:
            with open(path, encoding="utf-8") as handle:
                texts.append(handle.read())
        report(*texts)
    else:
        report(TASKS, TICKETS, SURVEY)
    return 0


if __name__ == "__main__":
    sys.exit(main())
