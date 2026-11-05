#!/usr/bin/env python3
"""A sample gallery verified against its manifest, then against what readers ask.

    python3 drills/gallery_audit.py

Reproduces both measurements the `sample-apps` page quotes: four manifest
entries of which two verify, and a coverage table showing that the topics the
gallery teaches are not the topics people have questions about.

This drill exists because that page was the one golden path on the list that a
reader could not actually follow. It shows the manifest in full, then two
fragments of the checker, and quotes the output of a `check_gallery.py` whose
source it never prints. The three sample programs it verifies are not in the
page either: step 1 creates their directories and nothing fills them. So the
output block was unreachable, and nothing said so.

The manifest below is the page's, verbatim, and a test asserts it stays that
way. The sample programs are written here, because they have to live somewhere
and the page's argument does not depend on what they contain: `stale` must
drift from its expectation and `missing` must not exist, and that is the whole
specification.

The ticket counts are invented, as the page says at length. They are a stand-in
for the one input this measurement cannot run without. The arithmetic over them
is real; the distribution is not.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

#: The page's step-1 heredoc, verbatim. A test asserts this still matches.
MANIFEST = """\
samples:
  - id: hello
    title: Hello widget
    teaches: [install, first-call]
    entrypoint: samples/hello/main.py
    expect: "widgets: 3"
  - id: batch
    title: Batch requests
    teaches: [batching]
    entrypoint: samples/batch/main.py
    expect: "sent 2 batches"
  - id: stale
    title: Streaming responses
    teaches: [streaming]
    entrypoint: samples/stale/main.py
    expect: "streamed 10 chunks"
  - id: missing
    title: Webhooks
    teaches: [webhooks]
    entrypoint: samples/missing/main.py
    expect: "received 1 webhook"
"""

#: The sample programs the page's manifest promises. Two satisfy their
#: expectation, `stale` has drifted, and `missing` is deliberately absent.
PROGRAMS = {
    "samples/hello/main.py": 'print("widgets: 3")\n',
    "samples/batch/main.py": 'print("sent 2 batches")\n',
    "samples/stale/main.py": 'print("streamed 8 chunks")\n',
}

#: Stand-in for a real support queue. Replace with yours before concluding
#: anything from the numbers; the page says this twice and means it.
ASKED_ABOUT = {
    "retries": 41,
    "auth": 33,
    "error-handling": 28,
    "pagination": 12,
    "batching": 6,
    "streaming": 3,
}


def verify(gallery: dict, root: Path) -> tuple[int, list[str]]:
    """Run every entrypoint and compare its output to the manifest's claim.

    This is the page's step-2 fragment, completed. The two defect classes it
    separates are the reason the manifest carries an `expect` field at all: a
    sample that fails to run is loud, and a sample that runs and lies is not.
    """
    problems: list[str] = []
    verified = 0
    for sample in gallery["samples"]:
        entry = root / sample["entrypoint"]
        if not entry.exists():
            problems.append(f"{sample['id']}: entrypoint {sample['entrypoint']} does not exist")
            continue
        result = subprocess.run(
            [sys.executable, str(entry)], capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            problems.append(f"{sample['id']}: exited {result.returncode}")
        elif sample["expect"] not in result.stdout:
            problems.append(
                f"{sample['id']}: expected {sample['expect']!r}, "
                f"got {result.stdout.strip()!r}"
            )
        else:
            verified += 1
    return verified, problems


def coverage(gallery: dict) -> tuple[int, int]:
    """Cross what the gallery teaches against what readers ask about."""
    # First-appearance order in the manifest, not a set's iteration order.
    # The page's original table was ordered by the latter, which is why its
    # three zero-ticket rows came out in an order nothing could reproduce.
    covered = []
    for sample in gallery["samples"]:
        for topic in sample["teaches"]:
            if topic not in covered:
                covered.append(topic)
    topics = list(ASKED_ABOUT) + [t for t in covered if t not in ASKED_ABOUT]

    print("topic             in gallery  tickets")
    for topic in topics:
        mark = "yes" if topic in covered else "-"
        print("%-18s%10s%9d" % (topic, mark, ASKED_ABOUT.get(topic, 0)))

    total = sum(ASKED_ABOUT.values())
    uncovered = sum(n for t, n in ASKED_ABOUT.items() if t not in covered)
    print()
    print(f"tickets about uncovered topics: {uncovered} of {total}")
    return uncovered, total


def main() -> int:
    gallery = yaml.safe_load(MANIFEST)

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for name, body in PROGRAMS.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body, encoding="utf-8")

        print("step 2: verify every entry\n")
        verified, problems = verify(gallery, root)
        for problem in problems:
            print(f"GALLERY  {problem}")
        total_samples = len(gallery["samples"])
        print(f"{'FAIL' if problems else 'ok'}: {verified}/{total_samples} samples verified")
        print(f"exit={1 if problems else 0}")

    print("\nstep 3: ask what the gallery covers\n")
    uncovered, tickets = coverage(gallery)

    print("\nstep 4: what the two measurements tell you to do\n")
    print(f"verified: {verified}/{total_samples}")
    print(f"demand coverage: {tickets - uncovered} of {tickets} tickets")

    ok = verified == 2 and len(problems) == 2 and uncovered == 114
    if not ok:
        print(
            "\nunexpected: the gallery no longer fails in the two ways the page "
            "describes",
            file=sys.stderr,
        )
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
