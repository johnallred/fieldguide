#!/usr/bin/env python3
"""Read an ephemeral lab's health record, size a nightly catalogue, verify teardown.

    python3 drills/lab_lifecycle.py                                  # embedded samples
    python3 drills/lab_lifecycle.py runs.csv checks.csv teardown.csv # your files

The real lifecycle (provision, run the lab's own steps, assert, tear down,
verify) runs in the companion repository `coldlab` against a real AWS account.
This drill does the parts that need no account, on that project's data:

- RUNS and CHECKS are coldlab's `health/health.jsonl` as of 2026-11-24T00:01Z,
  reshaped into two small tables. Durations are rounded to the second, error
  text is summarised, and account identifiers are removed. The live record
  grows with every run, so these figures are a dated reading.
- TEARDOWN is what a tag query returned after a teardown, with the exit code of
  the command that asks the owning service whether each resource still exists.
  The event source mapping is the case coldlab met on its first real
  teardown; the other three rows are illustrative, and the account number is
  the documentation example, 111122223333.

Teardown is verified three ways, as coldlab's harness/checks.py does: the stack
is gone, no tagged resource survives, and every tagged ARN was resolved against
its owning service. A tag index is eventually consistent, and a leak detector
that reports leaks which are not there gets ignored.
"""

from __future__ import annotations

import csv
import io
import math
import statistics
import sys

RUNS = """\
run,seconds,passed,stopped_by
2026-11-19T23:00Z,19,no,deploy refused by an organisation policy
2026-11-23T21:22Z,398,no,lab step exited 1 (aws s3 ls on an empty prefix)
2026-11-23T21:31Z,492,yes,-
2026-11-23T21:49Z,453,yes,-
2026-11-23T23:53Z,478,yes,-
"""

CHECKS = """\
check,gating,r1,r2,r3,r4,r5
run.completed,yes,-,F,P,P,P
dlq.depth,yes,-,-,P,P,P
dlq.receive_count_at_least_max_plus_one,yes,-,-,P,P,P
dlq.receive_count_exact,no,-,-,F,-,-
dlq.receive_count_in_observed_set,no,-,-,-,P,P
dlq.sent_timestamp_preserved,yes,-,-,P,P,P
bucket.failing_file_absent,yes,-,-,P,P,P
bucket.success_file_present,yes,-,-,P,P,P
timing.redrive_within_tolerance,no,-,-,P,P,P
teardown.stack_deleted,yes,P,P,P,P,P
teardown.no_leaks,yes,P,P,P,P,P
teardown.all_tagged_resolved,yes,P,P,P,P,P
"""

TEARDOWN = """\
arn,describe_exit
arn:aws:cloudformation:us-east-2:111122223333:stack/ColdlabSqsRetry/1a2b3c,254
arn:aws:lambda:us-east-2:111122223333:event-source-mapping:6f1e2a9c,254
arn:aws:logs:us-east-2:111122223333:log-group:/aws/lambda/ColdlabWorker,0
arn:aws:states:us-east-2:111122223333:stateMachine:ColdlabRetry,-
"""

CATALOG = 200       # labs in a nightly catalogue
WINDOW_HOURS = 4    # the overnight window they must all finish in


def rows(text: str) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(text)))


def resolver(arn: str) -> str | None:
    """The command that asks the owning service, or None if nothing here can."""
    _, _, service, _, _, resource = arn.split(":", 5)
    kind, _, name = resource.replace("/", ":", 1).partition(":")
    if service == "cloudformation" and kind == "stack":
        return f"aws cloudformation describe-stacks --stack-name {name.split('/')[0]}"
    if service == "lambda" and kind == "event-source-mapping":
        return f"aws lambda get-event-source-mapping --uuid {name}"
    if service == "lambda" and kind == "function":
        return f"aws lambda get-function --function-name {name}"
    if service == "logs" and kind == "log-group":
        return f"aws logs describe-log-groups --log-group-name-prefix {name}"
    if service == "sqs":
        return f"aws sqs get-queue-url --queue-name {resource}"
    return None


def health(runs_text: str, checks_text: str) -> float:
    runs = rows(runs_text)
    passed = [r for r in runs if r["passed"] == "yes"]
    print("step 1: what the record says")
    print(f"  runs {len(runs)}, passed {len(passed)} ({100 * len(passed) // len(runs)}%)")
    for r in runs:
        if r["passed"] != "yes":
            print(f"  failed {r['run']} after {r['seconds']}s: {r['stopped_by']}")
    for c in rows(checks_text):
        results = [c[f"r{i}"] for i in range(1, len(runs) + 1)]
        ran = [x for x in results if x != "-"]
        fails = ran.count("F")
        if fails and fails < len(ran):
            print(f"  flaky: {c['check']} ({fails} of {len(ran)} runs failed)")
        elif fails and c["gating"] == "no":
            print(f"  advisory, failed every time it ran, never decided a run: {c['check']}")
    median_all = statistics.median(int(r["seconds"]) for r in runs)
    median_full = statistics.median(int(r["seconds"]) for r in passed)
    print(f"  median duration: {median_all:.0f}s over all runs, {median_full:.0f}s over full lifecycles")
    print()
    return median_full


def catalog(seconds: float) -> None:
    hours = CATALOG * seconds / 3600
    lanes = math.ceil(hours / WINDOW_HOURS)
    print("step 2: what a nightly catalogue costs in time")
    print(f"  {CATALOG} labs x {seconds:.0f}s = {hours:.1f} hours, one after another")
    print(f"  to finish in {WINDOW_HOURS} hours: {lanes} labs running at once")
    print()


def teardown(text: str) -> int:
    print("step 3: is anything left?")
    stack_gone, leaks, unresolved = True, [], []
    tagged = rows(text)
    for row in tagged:
        arn, code = row["arn"], row["describe_exit"]
        short = arn.split(":", 5)[5]
        if resolver(arn) is None or code == "-":
            status = "unresolved: nothing here can ask its service"
            unresolved.append(short)
        elif code == "0":
            status = "LEAK: its service still describes it"
            leaks.append(short)
            stack_gone = stack_gone and not short.startswith("stack/")
        else:
            status = "gone: its service says so, the index was stale"
        print(f"  {short:<45} {status}")
    print()
    print(f"  tag query alone would report: {len(tagged)} leftover resource(s)")
    checks = [
        ("teardown.stack_deleted", stack_gone, ""),
        ("teardown.no_leaks", not leaks, ", ".join(leaks)),
        ("teardown.all_tagged_resolved", not unresolved, ", ".join(unresolved)),
    ]
    for name, ok, detail in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail else ""))
    return sum(not ok for _, ok, _ in checks)


def main() -> int:
    if len(sys.argv) == 4:
        runs_text, checks_text, teardown_text = (
            open(p, encoding="utf-8").read() for p in sys.argv[1:]
        )
    else:
        runs_text, checks_text, teardown_text = RUNS, CHECKS, TEARDOWN
    catalog(health(runs_text, checks_text))
    return 1 if teardown(teardown_text) else 0


if __name__ == "__main__":
    sys.exit(main())
