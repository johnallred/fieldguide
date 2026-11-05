---
title: Documentation CI
summary: The pipeline that decides what counts as a broken page, and fails a pull request over it.
diataxis: how-to
audience: developer
concept: documentation-ci
tags: [qa, core]
---

# Documentation CI

`core` · difficulty 2 · 4h

!!! quote "Asked for by name"
    Intel: "Build and maintain docsascode pipelines and documentation CI, including link checking and coldstart testing of quickstarts"

    NVIDIA: "Build and run docs-as-code pipelines: Git authoring, CI/CD builds, linting, link and code-sample validation, and publishing"

**Prerequisites:** [Docs-as-code](docs-as-code.md), [Git authoring workflows for writers](git-authoring.md)

## What it is

The set of automated checks that run on every documentation pull request, and
the decision about which of them can block a merge. Both postings name it as a
thing you build and operate, not a thing you configure once.

The useful framing is not "CI for docs" but **a list of ways this corpus can
start lying, each with a gate that catches it**. The pipeline is the artifact;
the list is the thinking.

## Why the job asks for it

A documentation corpus does not decay because people write badly. It decays
because the world moves and nothing tells the page. A flag is renamed, a
default changes from 3 to 5, a heading is reworded, a sample stops running
against the current release. Each of those is a silent, specific defect, and
each needs a specific check.

Both postings ask for the pipeline because it is the only mechanism that scales
past the size where a human can hold the corpus in their head. NVIDIA's phrase
for the philosophy is exact: build systems where the right way is easier than
the wrong way. A gate is how you make the wrong way harder.

The part interviewers probe is **what you chose to block on**. Anyone can add
checks. Deciding that a dead link blocks a merge while a style suggestion does
not, and being able to defend the line, is the judgment the role is actually
hiring for.

## The golden path

Build a two-gate pipeline, then discover why the gates must be separate steps.
About thirty minutes.

**Step 1: a corpus with two different defects**

````bash
mkdir -p ci-demo/docs && cd ci-demo
printf 'site_name: CI demo\n' > mkdocs.yml

cat > docs/index.md <<'EOF'
# Home

A [dead link](nope.md) and a style problem: we will probably maybe fix this.
EOF
````

One broken link and one hedging phrase. Two defect classes, two gates.

**Step 2: a style gate of your own**

```python
# gate_style.py
import re
import sys
from pathlib import Path

BAD = re.compile(r"\b(probably|maybe|should be able to)\b", re.I)

bad = []
for page in sorted(Path("docs").rglob("*.md")):
    for n, line in enumerate(page.read_text().splitlines(), 1):
        if m := BAD.search(line):
            bad.append(f"{page}:{n}: hedging: {m.group(0)!r}")

for b in bad:
    print(f"STYLE {b}")
print(f"{'FAIL' if bad else 'ok'}: {len(bad)} style problem(s)")
raise SystemExit(1 if bad else 0)
```

**Step 3: run them chained, the way people naturally write it first**

```bash
mkdocs build --strict >/dev/null 2>&1 && python3 gate_style.py
echo "chain exit=$?"
```

```
chain exit=1
```

That is the whole output. The build failed, `&&` short-circuited, and the style
gate never ran. You now know about one defect and have no idea the second
exists. Fix the link, push again, and learn about the hedging on the next
round trip.

**Step 4: run them as independent gates**

```bash
mkdocs build --strict >/dev/null 2>&1; BUILD=$?
python3 gate_style.py; STYLE=$?
echo "build gate exit=$BUILD   style gate exit=$STYLE"
```

```
STYLE docs/index.md:3: hedging: 'probably'
FAIL: 1 style problem(s)
build gate exit=1   style gate exit=1
```

Both defects, one run. In a GitHub Actions workflow this is the difference between one `run:` with
`&&` in it and two `run:` steps, and it is worth more than it looks. A
contributor who gets every problem at once fixes them in one commit. A
contributor who gets them one at a time learns that the pipeline wastes their
afternoon.

**Step 5: name the gates after the lie they prevent**

```bash
mkdir -p .github/workflows
cat > .github/workflows/docs.yml <<'EOF'
name: docs
on: [push, pull_request]
jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install mkdocs

      # A page links somewhere that does not exist.
      - name: Site builds with no warnings
        run: mkdocs build --strict

      # A page hedges where it should state a fact.
      - name: Prose is direct
        run: python3 gate_style.py
EOF
cat .github/workflows/docs.yml | head -5
```

Each step name describes the failure mode in the reader's terms, not the
tool's. "Site builds with no warnings" tells a contributor what broke. "Run
mkdocs" tells them nothing.

**What you built.** Two independent gates whose names describe defects. Adding
[link checking](link-checking.md),
[code-sample validation](code-sample-validation.md) and
[cold-start testing](coldstart-testing.md) is another step each.

## Reference

### A gate per failure mode

This is the real deliverable. The pipeline is downstream of this table.

| The lie | The gate | Blocking? |
|---|---|---|
| A link goes nowhere | [Link checking](link-checking.md) | Yes |
| A sample no longer runs | [Code-sample validation](code-sample-validation.md) | Yes |
| The quickstart fails from scratch | [Cold-start testing](coldstart-testing.md) | Yes, in its own job |
| A required metadata field is missing | Content model validation | Yes |
| A term drifted from the glossary | [Terminology drift](terminology-drift.md) | Yes |
| The prose hedges or is passive | [Prose linting](prose-linting.md) | Warn only |
| A page is older than its subject | [Freshness monitoring](freshness-monitoring.md) | Warn, or a scheduled report |
| An external URL died | Scheduled check, never a merge gate | No |

### What to block on

| Block the merge | Warn only |
|---|---|
| Deterministic | Depends on a third party or the clock |
| About correctness | About taste |
| Fixable by the author of this diff | Fixable only by someone else |
| Fails for one clear reason | Produces a list to triage |

A gate that is non-deterministic trains people to re-run CI until it passes,
and once that habit exists it applies to the trustworthy gates too. That is the
reason external link checking stays out of the merge path even though it finds
real problems.

### Where the fast feedback goes

| Job | Contents | Runs in |
|---|---|---|
| `quality` | Build, links, linters, unit tests, content model | Under two minutes |
| `samples` | Executing every code block | A few minutes |
| `coldstart` | Fresh environment, install, follow the quickstart | Ten minutes or more |

Keep them as separate jobs so the slow one does not gate the fast feedback.
A writer fixing a typo should not wait on a virtual environment build.

## How to talk about it

**Lead with the list, not the pipeline.** "I start from the ways the corpus can
start lying, and then there is one gate per way. Dead link, sample that no
longer runs, quickstart that fails from an empty environment, term that drifted
from the glossary. The workflow file is just that list in YAML."

**The question you will be asked is what you block on**, and the answer has to
include something you deliberately chose *not* to block on, with a reason.
Prose style is the usual example: failing a build because a sentence is passive
teaches contributors that the pipeline is an obstacle rather than a safety net,
so style warns and correctness blocks.

**The tradeoff to volunteer.** Every gate is a tax on contribution, paid by the
next person who wants to fix a typo. A pipeline with fifteen required checks on
a corpus nobody contributes to has optimised the wrong thing. The honest
version is that you add gates in response to defects that actually shipped, not
in anticipation of all possible defects.

**One sharper point, and it is the best thing to say here.** A gate suite is
only as good as its coverage of failure *modes*, and the count tells you
nothing about that coverage. This guide had a fully green pipeline, a
hundred-odd tests and a passing strict build while seven of its pages were
silently rendering code samples as prose, because a heredoc inside a bash
sample contained a fence of its own and closed the outer block early. Nothing
in the suite was looking at whether a code block was still a code block on the
published page. The fix was one more gate, comparing fenced source against the
`<pre>` content of the built HTML, and it found 127 defects the day it was
written.

That sentence used to give the gate count and the new gate's ordinal, which is
a figure with no way to stay right: gates have been added since and the
arithmetic quietly stopped working. `.github/workflows/docs.yml` is the count,
and this paragraph is a story about a blind spot. The lesson is not
"add more gates". It is that every green pipeline has blind spots, and the
useful question in a review is which failure mode nothing here would catch.

## How to prove it

**The artifact.** A workflow file with more than one independent check, step
names that describe failure modes, and a commit history that shows a gate
catching something real.

**Three things to do, in order:**

1. Run the golden path, including the `&&` step. Seeing the chain hide the
   second failure is the part that changes how you write workflows.
2. Write the failure-mode table for a corpus you already own. Three columns:
   the lie, the gate, whether it blocks. The gaps in that table are your
   backlog. Expect the blocking column to be mostly empty. This guide ran a
   fully green pipeline while seven of its pages were shipping code samples as
   prose.
3. Pick the one failure mode in your table with no gate and build it. That is
   the one worth talking about, because it came from your corpus rather than
   from a blog post.

**What makes it credible rather than decorative.** A reviewer can tell the
difference between a pipeline assembled from a tutorial and one grown in
response to real breakage. The tell is specificity: a gate that exists because
a particular page misled a particular reader, with the commit to prove it. Keep
the red build in the history.

## Related

- [GitHub Actions for docs](github-actions.md), the implementation
- [Link checking](link-checking.md), the cheapest gate and the first to add
- [Writing custom linters](custom-linters.md), for the failure modes no tool covers
- [Release readiness](release-readiness.md), the human checklist this automates part of
