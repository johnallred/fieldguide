#!/usr/bin/env python3
"""Gate a lab document, promote lab versions on evidence, and decide rollbacks.

    python3 drills/lab_publish.py                                        # embedded samples
    python3 drills/lab_publish.py candidate.md versions.csv runs.csv     # your files

Three decisions a lab publishing pipeline makes, with no cloud account:

1. Can this document be published at all? The gate parses the lab document the
   way coldlab's harness/extract.py does, from directives written as shell
   comments, and refuses anything that would make the published lab less
   testable or less portable.
2. Which version goes to which channel? A version is immutable and named by a
   hash of its content, and it moves from beta to prod only on passing health
   runs recorded against that exact version.
3. When prod breaks, roll back or fix forward? If failures began when the
   content changed, the previous version is the fix. If the content did not
   change, the world did, usually a service, and rolling back changes nothing.

The labs, versions and runs are invented. The directive syntax is coldlab's.
"""

from __future__ import annotations

import csv
import hashlib
import io
import re
import sys

CANDIDATE = """\
# Retries and dead-letter queues

## Send a message

```bash
# step: send
aws sqs send-message --queue-url "$QUEUE_URL" --message-body '{"file":"invoice-9001.csv"}'
```

## Wait for the redrive

```bash
sleep 120
```

## Confirm the file never landed

```bash
# step: confirm absent
# exits 1:
aws s3 ls "s3://$BUCKET/landed/"
```

## Inspect the worker

```bash
# step: inspect worker
pip install sqs-inspect
aws lambda get-function --function-name arn:aws:lambda:us-east-2:111122223333:function:Worker
```
"""

VERSIONS = """\
lab,version,content,published
sqs-retry,1,a1b2c3,2026-09-30
sqs-retry,2,c3d4e5,2026-11-02
sqs-retry,3,e5f6a7,2026-11-19
s3-events,1,0a0b0c,2026-09-15
s3-events,2,1c1d1e,2026-11-18
ec2-basics,1,9f8e7d,2026-08-01
vpc-basics,1,4d5e6f,2026-10-10
vpc-basics,2,7a8b9c,2026-11-21
"""

RUNS = """\
lab,version,date,channel,passed
sqs-retry,2,2026-11-17,prod,yes
sqs-retry,2,2026-11-18,prod,yes
sqs-retry,2,2026-11-19,prod,yes
sqs-retry,3,2026-11-20,beta,yes
sqs-retry,3,2026-11-21,beta,yes
sqs-retry,3,2026-11-22,beta,yes
s3-events,1,2026-11-16,prod,yes
s3-events,1,2026-11-17,prod,yes
s3-events,2,2026-11-19,prod,no
s3-events,2,2026-11-20,prod,no
s3-events,1,2026-11-20,beta,yes
ec2-basics,1,2026-11-19,prod,yes
ec2-basics,1,2026-11-20,prod,yes
ec2-basics,1,2026-11-21,prod,no
ec2-basics,1,2026-11-22,prod,no
vpc-basics,1,2026-11-20,prod,yes
vpc-basics,1,2026-11-21,prod,yes
vpc-basics,1,2026-11-22,prod,yes
vpc-basics,2,2026-11-22,beta,yes
"""

PROMOTE_AFTER = 3   # consecutive passing beta runs before a version reaches prod
PULL_AFTER = 2      # consecutive prod failures before a lab is acted on

FENCE = re.compile(r"^(`{3,}|~{3,})\s*(\w*)\s*$")
DIRECTIVE = re.compile(r"^#\s*(step|exits\s+\d+|not run by the harness|harness waits for)\s*:\s*(.*?)\s*$")
FETCHES = re.compile(r"\b(pip3? install|npm install|curl|wget|git clone)\b")
PINNED = re.compile(r"\barn:aws:|\b\d{12}\b")


def rows(text: str) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(text)))


def blocks(text: str) -> list[tuple[str, list[str]]]:
    """(heading, lines) for every bash block, as the harness would read them."""
    found, heading, inside, body = [], "(top)", None, []
    for line in text.splitlines():
        fence = FENCE.match(line)
        if inside is None:
            if line.startswith("#") and not line.startswith("#!"):
                heading = line.lstrip("#").strip()
            if fence and fence.group(2) == "bash":
                inside, body = fence.group(1), []
        elif fence and fence.group(1) == inside and not fence.group(2):
            found.append((heading, body))
            inside = None
        else:
            body.append(line)
    return found


def gate(text: str) -> list[str]:
    problems, names = [], []
    for heading, body in blocks(text):
        directives = [DIRECTIVE.match(line) for line in body]
        commands = [line for line in body if line.strip() and not line.startswith("#")]
        name = next((d.group(2) for d in directives if d and d.group(1) == "step"), None)
        if any(d and d.group(1) == "not run by the harness" for d in directives):
            continue
        where = name or heading
        if name is None:
            problems.append(f"{where}: no '# step:' name, so a failure cannot say which step broke")
        names.append(where)
        for d in directives:
            if d and d.group(1) != "step" and not d.group(2):
                problems.append(f"{where}: '# {d.group(1)}:' gives no reason, so the exception becomes permanent")
        for command in commands:
            if re.search(r"\bsleep\b", command):
                problems.append(f"{where}: bare sleep; declare what the harness waits for instead")
            if FETCHES.search(command):
                problems.append(f"{where}: downloads at lab time, which fails wherever there is no route out")
            if PINNED.search(command):
                problems.append(f"{where}: hardcodes a partition or account, which fails in any other")
    duplicates = {n for n in names if names.count(n) > 1}
    problems += [f"{n}: step name used twice" for n in sorted(duplicates)]
    return problems


def step1(text: str) -> bool:
    content = hashlib.sha256(text.encode("utf-8")).hexdigest()[:6]
    problems = gate(text)
    print("step 1: can this document be published?")
    print(f"  candidate content {content}, {len(blocks(text))} runnable blocks")
    for problem in problems:
        print(f"  BLOCKED  {problem}")
    if not problems:
        print("  ok: publishable as a new immutable version")
    print()
    return not problems


def latest(runs: list[dict[str, str]], lab: str, version: str, channel: str) -> list[bool]:
    picked = [r for r in runs if (r["lab"], r["version"], r["channel"]) == (lab, version, channel)]
    return [r["passed"] == "yes" for r in sorted(picked, key=lambda r: r["date"])]


def streak(results: list[bool], value: bool) -> int:
    count = 0
    for result in reversed(results):
        if result != value:
            break
        count += 1
    return count


def step2_and_3(versions_text: str, runs_text: str) -> int:
    versions, runs = rows(versions_text), rows(runs_text)
    labs = sorted({v["lab"] for v in versions}, key=[v["lab"] for v in versions].index)
    acted = 0
    print("step 2: what moves to prod")
    for lab in labs:
        mine = [v for v in versions if v["lab"] == lab]
        prod = max((r for r in runs if r["lab"] == lab and r["channel"] == "prod"), key=lambda r: r["date"])["version"]
        newest = mine[-1]["version"]
        if newest == prod:
            print(f"  {lab:<11} v{prod} in prod; nothing newer")
            continue
        passes = streak(latest(runs, lab, newest, "beta"), True)
        if passes >= PROMOTE_AFTER:
            print(f"  {lab:<11} v{newest} PROMOTE: {passes} passing beta runs on this exact content")
        else:
            print(f"  {lab:<11} v{newest} stays in beta: {passes} of {PROMOTE_AFTER} passing runs on its content")
    print()
    print("step 3: prod is failing; roll back or fix forward?")
    for lab in labs:
        mine = {v["version"]: v for v in versions if v["lab"] == lab}
        prod = max((r for r in runs if r["lab"] == lab and r["channel"] == "prod"), key=lambda r: r["date"])["version"]
        results = latest(runs, lab, prod, "prod")
        failing = streak(results, False)
        if failing < PULL_AFTER:
            continue
        acted += 1
        if True in results:
            print(f"  {lab:<11} v{prod} passed in prod, then failed {failing} times with unchanged content")
            print(f"  {'':<11} the environment changed, not the lab: rolling back cannot help;")
            print(f"  {'':<11} pull it from the catalog, tell instructors, fix forward")
        else:
            earlier = [v for v in mine if int(v) < int(prod)]
            previous = earlier[-1]
            print(f"  {lab:<11} v{prod} failed {failing} times since content {mine[prod]['content']} was published")
            if streak(latest(runs, lab, previous, "beta"), True) or streak(latest(runs, lab, previous, "prod"), True):
                print(f"  {'':<11} v{previous} still passes: ROLL BACK prod to v{previous}, then fix v{prod}")
            else:
                print(f"  {'':<11} v{previous} has no recent pass: pull it, do not roll back blind")
    return acted


def main() -> int:
    if len(sys.argv) == 4:
        candidate, versions, runs = (open(p, encoding="utf-8").read() for p in sys.argv[1:])
    else:
        candidate, versions, runs = CANDIDATE, VERSIONS, RUNS
    publishable = step1(candidate)
    step2_and_3(versions, runs)
    return 0 if publishable else 1


if __name__ == "__main__":
    sys.exit(main())
