#!/usr/bin/env python3
"""Check a single-sourced page against what each platform actually supports.

    python3 drills/parity_check.py                                   # embedded samples
    python3 drills/parity_check.py matrix.csv page.md results.csv    # check a page
    python3 drills/parity_check.py --render matrix.csv page.md       # per-platform sizes

One capability, several front doors: a first-party API and two cloud
marketplaces. Three inputs:

- matrix.csv: for each feature, what each platform supports. `yes`, `no`, or a
  value (an auth method, a model name) where platforms differ.
- page.md: one page for every platform. Front matter names the platforms, the
  features the page covers, and which platforms each sample claims to run on.
  Platform-specific text sits in `<!-- delta PLATFORM: FEATURE -->` blocks.
- results.csv: what happened when each sample ran against each platform.

The check: wherever a platform differs from the first-party API on a feature
the page covers, the page needs a delta for it; and every platform a sample
claims must have a passing run. The platforms and results are invented.
"""

from __future__ import annotations

import csv
import io
import re
import sys

MATRIX = """\
feature,direct,cloud-a,cloud-b
streaming,yes,yes,yes
batch,yes,yes,no
auth,API key,IAM role,service account
model name,widget-2,widget.widget-2-v1,widget-2@2026
"""

PAGE = """\
---
platforms: direct, cloud-a, cloud-b
features: batch, auth, model name
samples: batch_example.py = direct, cloud-a, cloud-b
---
# Send a batch of requests

Create a client, then submit up to 1,000 requests in one batch with
`client.batches.create()`. Results arrive within 24 hours.

<!-- delta cloud-a: auth -->
On Cloud A, the client authenticates with an IAM role instead of an API key.
<!-- end -->
"""

RESULTS = """\
sample,platform,result
batch_example.py,direct,pass
batch_example.py,cloud-b,fail
"""

PAGE_FIXED = """\
---
platforms: direct, cloud-a, cloud-b
features: batch, auth, model name
samples: batch_example.py = direct, cloud-a
---
# Send a batch of requests

Create a client, then submit up to 1,000 requests in one batch with
`client.batches.create()`. Results arrive within 24 hours.

<!-- delta cloud-a: auth -->
On Cloud A, the client authenticates with an IAM role instead of an API key.
<!-- end -->
<!-- delta cloud-a: model name -->
On Cloud A, the model is `widget.widget-2-v1`.
<!-- end -->
<!-- delta cloud-b: auth -->
On Cloud B, the client authenticates with a service account.
<!-- end -->
<!-- delta cloud-b: model name -->
On Cloud B, the model is `widget-2@2026`.
<!-- end -->
<!-- delta cloud-b: batch -->
Cloud B has no batch endpoint. Send the requests one at a time and handle
rate limits yourself; the sample on this page does not run there.
<!-- end -->
"""

RESULTS_FIXED = """\
sample,platform,result
batch_example.py,direct,pass
batch_example.py,cloud-a,pass
batch_example.py,cloud-b,fail
"""

DELTA = re.compile(r"<!-- delta ([\w-]+): ([\w ]+) -->\n(.*?)<!-- end -->\n", re.S)


def front(page: str) -> dict[str, str]:
    head = page.split("---\n")[1]
    return dict(line.split(": ", 1) for line in head.splitlines())


def listed(value: str) -> list[str]:
    return [v.strip() for v in value.split(",")]


def check(matrix_text: str, page: str, results_text: str) -> int:
    matrix = {row["feature"]: row for row in csv.DictReader(io.StringIO(matrix_text))}
    meta = front(page)
    deltas = {(p, f) for p, f, _ in DELTA.findall(page)}
    found = []
    for feature in listed(meta["features"]):
        row = matrix[feature]
        for platform in listed(meta["platforms"])[1:]:
            if row[platform] != row["direct"] and (platform, feature) not in deltas:
                what = "not available" if row[platform] == "no" else f"'{row[platform]}'"
                found.append(f"DELTA    {platform}: {feature} is {what}, and the page does not say so")
    runs = {(r["sample"], r["platform"]): r["result"]
            for r in csv.DictReader(io.StringIO(results_text))}
    sample, platforms = meta["samples"].split(" = ")
    for platform in listed(platforms):
        result = runs.get((sample, platform))
        if result is None:
            found.append(f"UNTESTED {sample} claims {platform} and was never run there")
        elif result != "pass":
            found.append(f"FAILS    {sample} claims {platform} and fails there")
    for line in found:
        print(line)
    print(f"{len(found)} finding(s)")
    return len(found)


def render(page: str) -> None:
    meta = front(page)
    body = page.split("---\n", 2)[2]
    shared = len(DELTA.sub("", body).split())
    for platform in listed(meta["platforms"]):
        own = sum(len(text.split()) for p, _, text in DELTA.findall(body) if p == platform)
        print(f"  {platform:<8} {shared + own:>3} words: {shared} shared + {own} for this platform")


def main() -> int:
    args = sys.argv[1:]
    if args[:1] == ["--render"]:
        texts = [open(path, encoding="utf-8").read() for path in args[1:]]
        render(texts[1])
        return 0
    if len(args) == 3:
        texts = [open(path, encoding="utf-8").read() for path in args]
        return 1 if check(*texts) else 0
    print("== draft")
    check(MATRIX, PAGE, RESULTS)
    print("\n== revised")
    remaining = check(MATRIX, PAGE_FIXED, RESULTS_FIXED)
    print("\n== what each reader sees")
    render(PAGE_FIXED)
    return 1 if remaining else 0


if __name__ == "__main__":
    sys.exit(main())
