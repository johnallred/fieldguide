---
title: Treating docs, setup and samples as one product
summary: The unit a developer experiences is not the page; it is everything between arriving and first success.
diataxis: explanation
audience: developer
concept: docs-as-product
tags: [craft, core]
---

# Treating docs, setup and samples as one product

`core` · difficulty 2 · 3h

> Treats setup, runnable samples, and docs as one product

> Source: intel posting, verbatim

## What it is

Owning the whole route from a developer arriving to a developer succeeding,
rather than owning the pages along it. Setup instructions, the install script,
the sample repository and the tutorial are one deliverable with one success
criterion, even when three different teams maintain them.

## Why the job asks for it

Intel states it in one sentence and the rest of the posting follows from it:
"Treats setup, runnable samples, and docs as one product", and then "so a
developer reaches first success in minutes with zero help".

The failure this prevents is organisational rather than editorial. The page is
correct. The sample repository is correct. The install script is correct. The
developer still fails, because the sample assumes a driver version the install
page does not mention, and no single owner is responsible for the seam. Each
team passes its own tests.

On a Tuesday this is mostly about **who owns the seams**. A developer reports
that the quickstart does not work. Investigating, the cause is that the sample
repo pinned a dependency three weeks ago and the docs page predates the pin. In
a page-ownership model, that is nobody's defect, and the conversation is about
whose ticket it is. In a product-ownership model it is yours, and the fix is
[a cold-start test](coldstart-testing.md) that would have caught it, which you
also own.

The second reason this is `core`: it is what makes
[time to first success](time-to-first-success.md) a meaningful metric. If you
only own pages, the number you can move is small and the number the developer
experiences is somebody else's.

## The golden path

Measure one real route end to end, find the seam, and write the thing that
watches it. About forty minutes.

**Step 1: write the route down as a sequence of artifacts**

Not as a page outline. As the things a developer actually touches.

```bash
mkdir -p product-drill && cd product-drill
cat > route.md <<'EOF'
# Route: zero to first inference result

| # | Artifact                      | Owner        | Can it fail alone? |
|---|-------------------------------|--------------|--------------------|
| 1 | Landing page                  | docs         | no                 |
| 2 | Install page                  | docs         | no                 |
| 3 | pip package                   | release eng  | yes                |
| 4 | Driver / runtime prerequisite | platform     | yes                |
| 5 | Quickstart page               | docs         | no                 |
| 6 | Sample repository             | engineering  | yes                |
| 7 | Model artifact download       | ml infra     | yes                |
| 8 | First result on screen        | nobody       | --                 |
EOF
cat route.md
```

The last two columns are the point. **Four of eight artifacts are owned by
people whose tests do not include this route**, and the final row, which is the
only one the developer cares about, is owned by nobody.

**Step 2: walk it and record where time goes**

```bash
cat > walk.md <<'EOF'
Walk the route on a clean machine. Record elapsed time per step and every
moment you had to leave the documented path.

| # | Step                  | Minutes | Left the path? |
|---|-----------------------|---------|----------------|
| 1 | Found the quickstart  |     2   | no             |
| 2 | Installed the package |     3   | no             |
| 3 | Ran the sample        |     -   | FAILED         |
| 4 | Searched the error    |    14   | yes: GitHub issue |
| 5 | Installed the runtime |     6   | yes: undocumented |
| 6 | Reran the sample      |     1   | no             |

Total: 26 minutes, of which 20 were off-path.
EOF
cat walk.md
```

Two numbers matter and neither is the total. **Minutes off-path** is the real
measure of the product, because off-path time is where developers abandon. And
**which seam produced it**: step 4 was caused by step 5's prerequisite being
owned by a team that does not read the quickstart.

**Step 3: build the thing that watches the seam**

The seam is between the install page's claimed prerequisites and the sample's
actual ones. That is checkable.

```bash
mkdir -p docs sample
cat > docs/install.md <<'EOF'
---
title: Install
requires:
  - python>=3.10
  - widget-runtime>=2.0
---
# Install

    pip install widget
EOF

cat > sample/requirements.txt <<'EOF'
widget>=1.4
widget-runtime>=2.4
numpy>=1.26
EOF

cat > check_prereqs.py <<'PY'
"""Fail when the sample needs something the install page does not promise.

The seam this watches is organisational: the sample's requirements file is
owned by engineering and the install page is owned by docs, and nothing
otherwise connects them. A developer finds the gap by failing.
"""
import re
import sys
from pathlib import Path

import yaml

NAME = re.compile(r"^([A-Za-z0-9_.-]+)")


def declared(page: Path) -> dict[str, str]:
    front = page.read_text(encoding="utf-8").split("---")[1]
    out = {}
    for item in yaml.safe_load(front).get("requires", []) or []:
        match = NAME.match(item)
        if match:
            out[match.group(1).lower()] = item
    return out


def required(reqs: Path) -> dict[str, str]:
    out = {}
    for line in reqs.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = NAME.match(line)
        if match:
            out[match.group(1).lower()] = line
    return out


def main() -> int:
    promised = declared(Path("docs/install.md"))
    needed = required(Path("sample/requirements.txt"))

    missing = sorted(set(needed) - set(promised))
    mismatched = [
        (name, promised[name], needed[name])
        for name in sorted(set(needed) & set(promised))
        if promised[name] != needed[name]
    ]

    for name in missing:
        print(f"UNDOCUMENTED  the sample needs {needed[name]!r}, "
              f"the install page never mentions it", file=sys.stderr)
    for name, page, sample in mismatched:
        print(f"VERSION SKEW  install page promises {page!r}, "
              f"the sample needs {sample!r}", file=sys.stderr)

    failures = len(missing) + len(mismatched)
    print(f"{'FAIL' if failures else 'ok'}: {failures} seam problem(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
PY
python3 check_prereqs.py
```

**Step 4: close it and confirm the gate turns green**

```bash
python3 - <<'PY'
import pathlib
p = pathlib.Path("docs/install.md")
p.write_text(p.read_text()
             .replace("widget-runtime>=2.0", "widget-runtime>=2.4")
             .replace("  - python>=3.10",
                      "  - python>=3.10\n  - widget>=1.4\n  - numpy>=1.26"))
PY
python3 check_prereqs.py
```

Three findings came out of one check, and the third is the one worth noticing.
`widget-runtime` was a version skew, `numpy` was undocumented, and **`widget`
itself was undeclared**: the install page said `pip install widget` without ever
stating which version the sample needs. That is invisible until something
compares the two files, and it is the most common form of this defect. A page
that tells you to install a thing is not the same as a page that tells you which
version of it works.

**What you built.** A check that fails when two teams' artifacts disagree, and
a written route that shows which of the eight steps nobody owns. The check is
small; the route document is the thing that changes conversations, because it
turns "whose bug is this" into "this seam has no owner and here is the gate I
put on it".

## Reference

### The shift in the unit of ownership

| Page ownership | Product ownership |
|---|---|
| Is the page accurate? | Does the developer succeed? |
| My tests pass | The route works on a clean machine |
| The sample repo is engineering's | The seam is mine |
| Measured in pages shipped | Measured in [time to first success](time-to-first-success.md) |
| A broken route is a routing problem | A broken route is a defect with my name on it |

### The seams, and what watches each

| Seam | Typical failure | Gate |
|---|---|---|
| Install page to package | Version drift | Prerequisite check, as above |
| Docs to sample repository | Sample moved or pinned | [Code-sample validation](code-sample-validation.md) |
| Docs to runtime prerequisite | Undocumented dependency | [Cold-start testing](coldstart-testing.md) |
| Sample to model or data artifact | Download moved, auth added | A smoke test that fetches it |
| Release to documentation | Capability ships undocumented | [Release readiness](release-readiness.md) |
| Page to page | Dead cross-reference | [Link checking](link-checking.md) |

### What to measure

| Metric | Why it is better than it looks |
|---|---|
| Minutes off-path | Where developers actually abandon. Total time hides this |
| Number of artifacts on the route | A proxy for how many ways it can break |
| Artifacts owned by teams whose CI excludes the route | The real risk register |
| First-attempt success rate on a clean machine | The only number that matches the posting's promise |

### The limits of this framing

| Claim | Honest version |
|---|---|
| "I own the route" | You own the gates. You do not own engineering's priorities |
| "One product, one owner" | Four teams still ship four artifacts on their own schedules |
| "Cold-start testing proves it works" | It proves it works on the CI runner's clean machine, not on the developer's |

## How to talk about it

**What a competent answer sounds like.** Lead with the seam, not the philosophy.
"The quickstart was accurate and the sample repository was accurate and the
route failed, because the sample had pinned a runtime version three weeks
earlier. I added a check that compares the sample's requirements against the
prerequisites the install page declares, and it fails the build when they
diverge. Before that, the gap was nobody's defect."

**The follow-up is about authority**, and it is the real question: how do you own
a product made of other teams' artifacts when you cannot direct those teams? The
answer is that you own the *detection*, not the artifacts. A gate that fails
loudly when engineering's pin drifts is available to you without anyone's
permission, and it converts an invisible seam into a red build with a named
cause. That is usually enough, because the argument changes from "please care
about documentation" to "this check is red and here is the commit".

Where it is not enough, the escalation is
[release readiness](release-readiness.md): getting documentation into the
definition of done, which is a political project rather than a technical one.

**The tradeoff to volunteer.** Claiming the whole route means owning failures
you cannot fix. You will be the person who reports that the model download
started requiring authentication, and you will not be the person who can change
it back. That is genuinely uncomfortable and it is the job: the alternative is a
documentation team that passes all its own tests while developers fail.

**One sharper point.** The strongest version of this is that **the route is the
product's actual API for new users**, and it is the only part of a platform that
every single user touches in the same order. Teams instrument their services
heavily and instrument that route not at all. Pointing out that the
highest-traffic, least-monitored path in the product is the first ten minutes is
a good way to get resources, and it is exactly the argument Intel's posting is
making with "setup, runnable samples, and docs as one product".

## How to prove it

**The artifact.** A route document and one gate on one seam. The route document
is unusual enough to be memorable and takes an hour.

**Three things to do, in order:**

1. **Walk a route on a clean machine and record minutes off-path.** Any
   product, including one you do not work on. The off-path number is the
   finding, and almost nobody has it. Predict the off-path minutes first. On a
   route you own the guess is usually low by a factor, and that factor is the
   number worth reporting.
2. **Build one seam check.** The golden path above is a working one. Point it at
   two real files in a project you know.
3. **Name the artifacts on the route whose owners' CI excludes the route.** That
   list is a risk register nobody has written, and presenting it is a stronger
   demonstration of product ownership than any page.

**What makes it credible rather than decorative.** "I think of docs as a product" is a slogan. A table
of eight artifacts, four owners, and a measured twenty minutes off-path is not.

### How this would be demonstrated elsewhere

A repository can show that setup, samples and documentation are built and
tested together, and this one does. What it cannot show is the organisational
half: that they are *owned* together, planned together and released together,
which is what the concept actually asserts.

**Where the skill is exercised.** In a release meeting, when someone asks
whether the docs are ready and the honest answer is a gate rather than an
opinion. In the decision to hold a launch for a broken quickstart. In whose
backlog a sample lives.

**What a learner would do.** Take the last three features your team shipped and
reconstruct, from records rather than memory, when the documentation work
started relative to the code. Then ask who decided it was done. Those two facts
describe whether docs are a product or a deliverable, and neither is a matter of
opinion once you look.

Then run the cheaper experiment: pick one feature and treat its quickstart as a
release blocker for a single release. The interesting output is not the
quickstart, it is the conversation that happens when it blocks something.

**What competence looks like.**

| Evidence | Why it carries weight |
|---|---|
| A release that waited for documentation | Someone had the authority and used it |
| A sample owned by the team that owns the feature | The authorship question, answered |
| A definition of done naming documentation | It survives a deadline |
| A quickstart in the same CI run as the code | The mechanisable half |
| A feature shipped without docs, and the record of why | Honest exceptions beat a perfect claim |

**What this guide and its companion can point at.** `docpack` builds its
samples, its site, its `llms.txt` and its chunk artifacts from one command and
gates all of them on one CI run, and its tutorial is executed from an empty
virtual environment on every change. That is the product half made real.

**Why it is not the demonstration the page needs.** One person wrote all of it,
so nothing was negotiated, nobody had to be persuaded, and no release was ever
held. The hard part of this concept is entirely social and a single-author
repository removes it by construction. That is why the entry here is not
upgraded past the mechanical half.

## Related

- [Golden paths](golden-paths.md), the route done deliberately
- [Cold-start testing](coldstart-testing.md), the gate on the biggest seam
- [Time to first success](time-to-first-success.md), the number this makes measurable
- [Release readiness](release-readiness.md), the political escalation
