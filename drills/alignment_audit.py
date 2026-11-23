#!/usr/bin/env python3
"""Audit a tutorial against learning-science principles, before and after.

    python3 drills/alignment_audit.py              # both embedded tutorials
    python3 drills/alignment_audit.py before.md    # any marked-up tutorial

The tutorial marks its own structure in HTML comments, so a script can read
what a reviewer would otherwise have to infer: which of Merrill's phases each
section serves, which objective it serves, and what kind of practice it is.
The audit reports three things the learning-science page argues for:

- problem-centred: is the whole task shown before the parts are taught?
- constructive alignment: is every objective demonstrated, practised and checked?
- fading: does practice move from worked example to completion to independent?

It checks structure only. Nothing here observes a reader learning anything.
"""

from __future__ import annotations

import re
import sys

BEFORE = """\
---
objectives:
  O1: Configure retries on the client
  O2: Choose a retry count for a workload
  O3: Diagnose a retry budget that is exhausted
---
# Retries in the widget client

<!-- phase: demonstration; serves: O1 -->
## How retries work
The client retries failed requests with exponential backoff. Retries are
controlled by the `retries` argument, which counts retries rather than
attempts, so `retries=3` makes up to four requests. Backoff doubles from
200 ms. The maximum is 10. Historically the client did not retry at all.

<!-- phase: demonstration; serves: O2 -->
## Choosing a value
Callers waiting on a response want 1 or 2. Background jobs can use 3 to 5.
Upstreams that restart often justify up to 10, at the cost of blocking.

<!-- phase: application; serves: O1; practice: independent -->
## Exercise
Configure a client that survives a restarting upstream.
"""

AFTER = """\
---
objectives:
  O1: Configure retries on the client
  O2: Choose a retry count for a workload
  O3: Diagnose a retry budget that is exhausted
---
# Retries in the widget client

<!-- phase: task -->
## What you will build
A sync job that keeps running while its upstream restarts, and a log line
that tells you when it gave up and why.

<!-- phase: activation -->
## What you already know
You have seen a request fail and succeed when you ran it again by hand.
Retries are that, done by the client, with a pause that grows each time.

<!-- phase: demonstration; serves: O1; practice: worked -->
## Worked example: a client that retries
    client = WidgetClient(retries=3)   # up to 4 requests
    client.sync()                      # logs: retry 1/3 after 200 ms
`retries` counts retries, not attempts. Backoff doubles from 200 ms.

<!-- phase: demonstration; serves: O2 -->
## Choosing a value
Callers waiting on a response want 1 or 2. Background jobs can use 3 to 5.
Upstreams that restart often justify up to 10, at the cost of blocking.

<!-- phase: application; serves: O1, O2; practice: completion -->
## Your turn, with the start done
    client = WidgetClient(retries=____)   # a nightly background job
Fill the blank and run it. You should see `synced` after at most 3 retries.

<!-- phase: demonstration; serves: O3 -->
## When the budget runs out
The client logs `gave up after 3 retries: 503` and raises `RetryExhausted`.
The status code tells you whether the upstream was down or rejecting you.

<!-- phase: application; serves: O3; practice: independent -->
## On your own
Point the job at the flaky test upstream and read why it gave up.

<!-- phase: integration; serves: O1, O2, O3; check: O1, O2, O3 -->
## Check yourself, then change it
Without scrolling up: what does `retries=3` cost in requests, which value
would you pick for an interactive call, and what does `RetryExhausted: 429`
tell you? Then choose a value for a job in your own codebase.
"""

MARKER = re.compile(r"<!--\s*(.*?)\s*-->")
PHASES = ("task", "activation", "demonstration", "application", "integration")
FADING = ("worked", "completion", "independent")


def parse(text: str) -> tuple[dict[str, str], list[dict]]:
    """Return the objectives and one record per marked section."""
    front, body = text.split("---\n", 2)[1:]
    objectives = dict(
        line.strip().split(": ", 1)
        for line in front.splitlines()
        if re.match(r"\s+O\d+:", line)
    )
    sections = []
    for block in MARKER.split(body)[1:]:
        if not sections or "body" in sections[-1]:
            fields = {}
            for part in block.split(";"):
                key, _, value = part.partition(":")
                fields[key.strip()] = [v.strip() for v in value.split(",") if v.strip()]
            sections.append(fields)
        else:
            sections[-1]["body"] = block
    for section in sections:
        section.setdefault("body", "")
        section["words"] = len(section["body"].split())
    return objectives, sections


def audit(name: str, text: str) -> int:
    objectives, sections = parse(text)
    print(f"== {name}")

    words = {phase: 0 for phase in PHASES}
    for s in sections:
        words[s["phase"][0]] += s["words"]
    print("phase words:  " + "  ".join(f"{p} {words[p]}" for p in PHASES))
    print(f"total words: {sum(words.values())}")

    order = [s["phase"][0] for s in sections]
    first_demo = order.index("demonstration") if "demonstration" in order else len(order)
    centred = "task" in order[:first_demo]
    print(f"task shown before demonstration: {'yes' if centred else 'no'}")

    print("objective                                     demo  practice  check")
    aligned = 0
    for oid, label in objectives.items():
        demo = any(s["phase"][0] == "demonstration" and oid in s.get("serves", []) for s in sections)
        prac = any(s["phase"][0] == "application" and oid in s.get("serves", []) for s in sections)
        chk = any(oid in s.get("check", []) for s in sections)
        aligned += demo and prac and chk
        row = "  ".join(f"{'yes' if v else 'no':<4}" for v in (demo, prac, chk))
        print(f"  {oid} {label:<41} {row}".rstrip())
    print(f"aligned objectives: {aligned}/{len(objectives)}")

    practice = [s["practice"][0] for s in sections if "practice" in s]
    print("practice sequence: " + " -> ".join(practice))
    ranks = [FADING.index(p) for p in practice]
    faded = len(ranks) > 1 and ranks == sorted(ranks) and ranks[0] == 0
    print(f"faded from worked to independent: {'yes' if faded else 'no'}")
    print()
    return aligned


def main() -> int:
    if len(sys.argv) > 1:
        for path in sys.argv[1:]:
            with open(path, encoding="utf-8") as handle:
                audit(path, handle.read())
        return 0
    before = audit("before.md", BEFORE)
    after = audit("after.md", AFTER)
    print(f"aligned objectives: {before}/3 before, {after}/3 after")
    return 0


if __name__ == "__main__":
    sys.exit(main())
