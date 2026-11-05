---
title: LLMs in the content lifecycle
summary: Drafting, updating and auditing a corpus with models, with the human placed where judgement is actually required.
diataxis: explanation
audience: operator
concept: llm-content-lifecycle
tags: [ai, core]
---

# LLMs in the content lifecycle

`core` · difficulty 3 · 6h

> Automate the content lifecycle with LLMs and scripting, from drafting and updating to auditing, with checks for freshness, code accuracy, and terminology drift, and human review where judgment matters

> Source: nvidia posting, verbatim

**Prerequisites:** [Prompting for content work](prompting.md), [Content lifecycle and governance](content-lifecycle.md)

## What it is

Using models as one stage in the machinery that keeps a corpus current:
proposing drafts, flagging what has gone stale, auditing for drift. The quote
above is the most specific bullet in either posting, and it names its own
constraint at the end: **human review where judgment matters.**

The work is deciding where that is.

## Why the job asks for it

NVIDIA's bullet is a job description in one sentence. It names three activities
(drafting, updating, auditing), three checks (freshness, code accuracy,
terminology drift), and one constraint (human review where judgement matters).
Every other page in this category is a piece of it.

What makes it `core` and difficulty 3 is that **the lifecycle is where the
economics live.** A single good answer from an assistant saves a reader five
minutes. An audit that correctly flags 40 of 400 stale pages saves a team a
week, every quarter, and it is the only thing in this category that scales with
corpus size rather than with traffic.

On a Tuesday it is a pipeline you babysit. The weekly audit ran overnight and
produced 180 findings on a 400-page corpus. Nobody will review 180 findings, so
by Thursday the queue is untouched and the corpus is no more current than
before. **The pipeline worked and the lifecycle did not**, because the design
target was recall and the binding constraint was reviewer attention.

## The golden path

Build the three stages, with the human placed deliberately, and discover that
the constraint is review capacity rather than model quality. Fifty minutes,
dependency-free.

**Step 1: a corpus in the state corpora are actually in**

```bash
mkdir -p lifecycle-drill/docs && cd lifecycle-drill
cat > docs/install.md <<'EOF'
---
title: Install the CLI
updated: 2024-01-15
owner: platform
---
# Install the CLI

Requires widget 2.2 or newer. Simply run the installer.

    pip install widget==2.2
EOF

cat > docs/retries.md <<'EOF'
---
title: Configure retries
updated: 2026-09-20
owner: platform
---
# Configure retries

Set `retries` on the client. The default is 3.
EOF

cat > docs/batching.md <<'EOF'
---
title: Batch requests
updated: 2023-11-02
owner: inference
---
# Batch requests

Pass a list to infer_batch. The repo has examples.
EOF

cat > docs/legacy-upgrade.md <<'EOF'
---
title: Upgrading from 1.x
updated: 2023-03-01
owner: platform
status: superseded
---
# Upgrading from 1.x

The 1.x client reached end of life in 2024.
EOF

cat > facts.yaml <<'EOF'
# Ground truth the pipeline checks against, generated in CI from the real
# artifacts: --help output, git tags, the glossary. Never hand-maintained.
current_version: "2.6"
supported_versions: ["2.4", "2.6"]
retries_default: 5          # changed from 3 in 2.5 and nobody updated the page
terms:
  repository: [repo, repos]
  pull request: [PR, MR]
EOF
ls docs/
```

**Step 2: the three stages, each proposing and never applying**

```bash
cat > lifecycle.py <<'PY'
"""Audit, update and draft stages for a documentation corpus.

Every stage returns PROPOSALS. Nothing writes to the corpus, because the
constraint named in the posting is "human review where judgment matters" and
a stage that applies its own findings has removed the place to put a human.

The three checks NVIDIA names map onto three different mechanisms, and only
one of them should involve a model at all:

  FRESHNESS         a date comparison. No model. Deterministic
  CODE ACCURACY     compare claims to generated ground truth. No model
  TERMINOLOGY DRIFT a substitution list. No model

The model's job is the fourth thing: DRAFTING a proposed replacement for a
finding a deterministic check already located, and ranking what a human
should look at first.
"""
import datetime as dt
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

STALE_DAYS = 365
VERSION = re.compile(r"widget[ =]{1,2}(\d+\.\d+)")
HEDGES = ("simply", "just", "easy")


@dataclass
class Finding:
    """One proposal. `confidence` decides review order, never whether to apply."""

    page: str
    kind: str
    detail: str
    confidence: str          # mechanical | needs-judgement
    owner: str = ""
    proposed: str = ""


@dataclass
class Report:
    findings: list = field(default_factory=list)

    def add(self, **kwargs):
        self.findings.append(Finding(**kwargs))

    def by_confidence(self, level):
        return [f for f in self.findings if f.confidence == level]


def pages(root):
    for path in sorted(root.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        meta = yaml.safe_load(text.split("---")[1]) or {}
        yield path, meta, text


def audit(root, facts):
    """Stage 1: find what is wrong. Entirely deterministic."""
    report = Report()
    today = dt.date.today()

    for path, meta, text in pages(root):
        owner = meta.get("owner", "unassigned")
        updated = meta.get("updated")
        if isinstance(updated, str):
            updated = dt.date.fromisoformat(updated)

        # Freshness: a date comparison.
        if updated and (today - updated).days > STALE_DAYS:
            age = (today - updated).days
            report.add(page=path.name, kind="stale", owner=owner,
                       detail=f"not reviewed in {age} days",
                       confidence="needs-judgement")

        # Code accuracy: claims against generated ground truth.
        # `set()` because findall hits the same version once in prose and once
        # in the install line, and two identical findings is one decision
        # presented as two.
        for version in sorted(set(VERSION.findall(text))):
            if version not in facts["supported_versions"]:
                report.add(page=path.name, kind="unsupported-version", owner=owner,
                           detail=f"references widget {version}, "
                                  f"supported: {facts['supported_versions']}",
                           confidence="mechanical",
                           proposed=f"{version} -> {facts['current_version']}")

        match = re.search(r"default is (\d+)", text)
        if match and int(match.group(1)) != facts["retries_default"]:
            report.add(page=path.name, kind="wrong-default", owner=owner,
                       detail=f"says default is {match.group(1)}, "
                              f"actual is {facts['retries_default']}",
                       confidence="mechanical",
                       proposed=f"default is {match.group(1)} -> "
                                f"default is {facts['retries_default']}")

        # Terminology drift: a substitution list.
        for approved, variants in facts["terms"].items():
            for variant in variants:
                if re.search(rf"\b{re.escape(variant)}\b", text):
                    report.add(page=path.name, kind="terminology", owner=owner,
                               detail=f"{variant!r} should be {approved!r}",
                               confidence="mechanical",
                               proposed=f"{variant} -> {approved}")

        # Prose quality: a hedge list. Mechanical to find, judgement to fix.
        for hedge in HEDGES:
            if re.search(rf"\b{hedge}\b", text, re.I):
                report.add(page=path.name, kind="hedge", owner=owner,
                           detail=f"uses {hedge!r}", confidence="needs-judgement")

    return report


def route(report, capacity):
    """Stage 2: decide what a human sees this week.

    THIS is the stage that determines whether the lifecycle works. A report
    of 180 findings is reviewed by nobody. Mechanical findings batch into one
    approval; judgement findings are rationed to the capacity that exists.
    """
    mechanical = report.by_confidence("mechanical")
    judgement = report.by_confidence("needs-judgement")

    batches = {}
    for finding in mechanical:
        batches.setdefault((finding.kind, finding.proposed), []).append(finding)

    # Judgement items go oldest-first, by owner, capped.
    rationed = judgement[:capacity]
    deferred = judgement[capacity:]
    return batches, rationed, deferred


def draft(finding, text):
    """Stage 3: propose replacement text for a located finding.

    A deterministic substitution stands in for a model call. The important
    property is the INTERFACE: a draft is produced for a finding that a
    deterministic check already located, never from an open instruction to
    improve the page. That bounds what a wrong draft can do.
    """
    if finding.kind in ("unsupported-version", "terminology", "wrong-default"):
        old, _, new = finding.proposed.partition(" -> ")
        if not new:
            # A proposal with no `old -> new` form cannot be applied as a diff.
            # Returning `finding.proposed` here replaced the WHOLE document
            # with the proposal string, which is how the first version of this
            # page produced a diff reading `- ---` / `+ default is 5`.
            raise ValueError(
                f"{finding.kind} proposal {finding.proposed!r} is not in "
                "'old -> new' form, so it cannot be rendered as a diff"
            )
        return text.replace(old, new)
    return ""
PY
echo "lifecycle written"
```

**Step 3: run the audit and look at the shape of the problem**

```bash
cat > run.py <<'PY'
from collections import Counter
from pathlib import Path

import yaml

from lifecycle import audit, route

facts = yaml.safe_load(open("facts.yaml"))
report = audit(Path("docs"), facts)

print(f"=== audit: {len(report.findings)} findings on 4 pages ===")
for finding in report.findings:
    print(f"  [{finding.confidence:<16}] {finding.page:<20} {finding.kind:<20} "
          f"{finding.detail}")

print()
print("by kind:      ", dict(Counter(f.kind for f in report.findings)))
print("by confidence:", dict(Counter(f.confidence for f in report.findings)))
print("by owner:     ", dict(Counter(f.owner for f in report.findings)))

CAPACITY = 2   # judgement items one person will actually review this week
batches, rationed, deferred = route(report, CAPACITY)

print(f"\n=== routed, with review capacity {CAPACITY} ===")
print(f"  {len(batches)} batched approval(s) covering "
      f"{sum(len(v) for v in batches.values())} mechanical findings:")
for (kind, proposed), items in batches.items():
    pages_affected = ", ".join(sorted(f.page for f in items))
    print(f"    {kind}: {proposed}   ({pages_affected})")
print(f"  {len(rationed)} judgement item(s) for review this week:")
for finding in rationed:
    print(f"    {finding.page}  {finding.kind}  {finding.detail}")
print(f"  {len(deferred)} deferred")
PY
python3 run.py
```

**Step 4: show the drafting stage, and what bounds it**

```bash
python3 - <<'PY'
from pathlib import Path

import yaml

from lifecycle import audit, draft

facts = yaml.safe_load(open("facts.yaml"))
report = audit(Path("docs"), facts)

print("=== drafts for mechanical findings, applied to nothing ===")
for finding in report.by_confidence("mechanical"):
    original = (Path("docs") / finding.page).read_text()
    proposed = draft(finding, original)
    changed = [
        (a, b) for a, b in zip(original.splitlines(), proposed.splitlines()) if a != b
    ]
    print(f"\n  {finding.page}  ({finding.kind})")
    for before, after in changed:
        print(f"    - {before.strip()}")
        print(f"    + {after.strip()}")

print()
print("=== what the drafting stage is NOT asked to do ===")
for finding in report.by_confidence("needs-judgement"):
    print(f"  {finding.page:<20} {finding.kind:<12} {finding.detail}")
print("  No draft is generated for these. 'This page is 1030 days old' has no")
print("  mechanical fix, and a model asked to refresh it would rewrite content")
print("  it cannot verify.")
PY
```

**What you built.** Three stages, a routing step that respects review capacity,
and a drafting stage that only ever proposes a fix for a finding a
deterministic check already located.

### What the audit found, and how routing changed its shape

Seven findings on four pages: three stale, one terminology, one unsupported
version, one hedge, one wrong default. Split 4 judgement and 3 mechanical.

Routing turns that into:

```
3 batched approval(s) covering 3 mechanical findings:
  terminology: repo -> repository              (batching.md)
  unsupported-version: 2.2 -> 2.6              (install.md)
  wrong-default: default is 3 -> default is 5  (retries.md)
2 judgement item(s) for review this week
2 deferred
```

**Three glances and two decisions**, instead of seven items in a list. At four
pages the difference is cosmetic. At four hundred it is the difference between a
queue that gets cleared and one that does not, which is the whole argument.

The `wrong-default` finding is the one worth noticing: the page says the retries
default is 3 and the ground truth says 5, because it changed in 2.5 and nobody
updated the page. **No model was involved in finding that.** It is a regex
against a value generated in CI.

### Two bugs the first run exposed

**A duplicate finding.** `install.md` mentions `widget 2.2` twice, in prose and
in the install command, so `findall` produced two identical findings and the
batch read `(install.md, install.md)`. One decision presented as two is exactly
the thing routing exists to prevent, so the fix is to deduplicate per page and
version.

**A draft that replaced the whole document.** The `wrong-default` proposal was
`"default is 5"`, with no `old -> new` form, and `draft()` fell back to
returning the proposal as the entire proposed text. The rendered diff read
`- ---` / `+ default is 5`, which is a page being deleted and replaced by a
sentence. The fix puts the proposal in `old -> new` form, and the fallback now
raises instead of returning something nonsensical: **a drafting stage that
cannot express a change as a diff must fail loudly, because the alternative is
a diff a reviewer might approve.**

## Reference

### Where the model goes, and where it does not

| Activity | Mechanism | Model? |
|---|---|---|
| Freshness check | A date comparison | **No** |
| Code accuracy | Claims against [generated ground truth](reading-code-to-verify.md) | **No** |
| Terminology drift | A substitution list | **No** |
| Finding hedges and style issues | A [linter](prose-linting.md) | **No** |
| **Drafting a replacement for a located finding** | Prompt plus validation | **Yes** |
| **Ranking a review queue** | Classification | **Yes** |
| Summarising a changelog into release notes | Prompt plus review | Yes |
| Deciding what to retire | Judgement | **Never** |
| Confirming a page is accurate | Needs the implementation | **Never** |

Three of the four checks NVIDIA names involve no model at all. That is the most
useful thing on this page: **"automate the content lifecycle with LLMs" is
mostly automation, with an LLM at two specific points.** A pipeline that uses a
model for the freshness check is slower, more expensive and less reliable than
`date.today() - updated`.

### The constraint is review capacity

The failure that kills these pipelines is not a bad model. It is a queue nobody
works:

| Design target | Result |
|---|---|
| Maximise recall | 180 findings, zero reviewed, corpus unchanged |
| Respect capacity | 12 findings, all reviewed, corpus improves weekly |

Three mechanisms make a queue reviewable:

| Mechanism | Effect |
|---|---|
| **Batch identical mechanical findings** | One approval covers "2.2 to 2.6" on nine pages |
| **Separate mechanical from judgement** | Mechanical needs a glance; judgement needs thought |
| **Ration judgement items to real capacity** | The remainder is deferred visibly, not hidden |

Batching is the big one. Nine pages with the same wrong version is one decision,
not nine, and presenting it as nine is what makes a queue look impossible.

### Freshness is a signal, not a defect

A date is not evidence of anything. A page about a stable interface is fine at
three years old; a page about a weekly-changing API is suspect at three months.

| Better signal | Why |
|---|---|
| Last change to the code it documents | Actual drift risk |
| Views since last review | A stale page nobody reads is not urgent |
| Support tickets referencing it | Evidence of real harm |
| An assistant's [failed answers](ai-assistants.md) citing it | Evidence it misleads |

Age alone over-reports, which is exactly how a queue reaches 180 items. This is
why the golden path tags staleness `needs-judgement` rather than `mechanical`.

### What drafting must be bounded by

| Bound | Why |
|---|---|
| A deterministic check located the finding first | An open "improve this page" instruction has no failure bound |
| The proposed change is a diff | Reviewable; an applied change is not |
| Validate the draft before a human sees it | [Grounding](grounding.md) and [vocabulary](hallucination-guardrails.md) checks |
| Never draft for a judgement finding | "This is 1030 days old" has no mechanical fix |
| Never widen a constraint to pass | See [agent skills](agent-skills.md) |

The last two are the ones that go wrong. A model asked to refresh a stale page
rewrites content it cannot verify, fluently, and the diff looks like an
improvement.

### Measuring whether the lifecycle works

| Metric | Healthy |
|---|---|
| Review queue depth | Flat or falling. Growing means it is theatre |
| Proposals accepted | 80% or more. Below that the precision is wrong |
| Median page age | Falling |
| Findings per page per quarter | Falling, as classes of defect get fixed at the source |
| Time from finding to merge | Days, not months |

**Queue depth is the one to watch.** A growing queue with a good acceptance rate
means you built a pipeline that generates work faster than the team absorbs it,
which is a worse outcome than not having one, because the corpus now also looks
audited.

## How to talk about it

**What a competent answer sounds like.** Lead with how little of it needs a
model, then with the capacity constraint. "Three of the four checks in that
bullet are not model work: freshness is a date comparison, code accuracy is
claims against ground truth generated in CI, terminology drift is a
substitution list. The model does two things, drafting a replacement for a
finding something else already located, and ranking the queue. And the thing
that decides whether any of it works is review capacity: our first audit
produced 180 findings on 400 pages and nobody reviewed any of them, so I batched
identical mechanical findings into single approvals and rationed judgement items
to what one person actually reads in a week."

**The follow-up is "how do you stop a model rewriting things it should not",**
and the answer is the interface rather than the prompt. A draft is only ever
produced for a finding a deterministic check located, with the specific change
named, as a diff, applied to nothing. An open instruction to improve a page has
no bound on what it can change, and that is a design choice rather than a
prompting problem.

**The tradeoff to volunteer.** This pipeline makes the corpus more consistent and
can make it blander. Batched terminology fixes are genuinely good; batched
anything-else starts flattening the voice of pages that had one, and the
reviewer approving a batch of nine is not reading nine pages. There is also a
real risk of false confidence: a corpus with a green audit looks maintained, and
the audit only checks what you taught it to check. The things it cannot see,
omissions and subtly wrong explanations, are the expensive defects, and nothing
here touches them.

**One sharper point.** The strongest observation is that **the lifecycle pipeline's
real output is a list of defect classes to fix at the source.** If the audit
reports forty wrong version references every quarter, the answer is not a better
audit, it is a single source of truth for the version plus a
[gate](release-readiness.md), after which that finding never appears again.
Findings-per-page should fall over time, and if it is flat you are paying for a
treadmill. That is [the systems mindset](systems-mindset.md) applied to your own
automation, and it is the thing that distinguishes an operator from someone who
set up a cron job.

## How to prove it

**The artifact.** A pipeline that proposes and never applies, with a routing
step that batches and rations, and queue-depth numbers over a few weeks.

**Three things to do, in order:**

1. **Run the golden path.** The routing step is the demonstration: it turns a
   raw finding list into a queue a person will actually clear.
2. **Generate your ground truth in CI.** Parse `--help`, read git tags, export
   the glossary. The audit is only as good as the facts, and hand-maintained
   facts are the first thing to rot.
3. **Track queue depth and acceptance rate for a month.** Two numbers. If depth
   grows while acceptance is high, you have the capacity problem rather than a
   precision problem, and that diagnosis is the whole value.

**What makes it credible rather than decorative.** "We use AI to maintain our docs" is a slogan. A
pipeline where three of four checks are deterministic, drafting is bounded to
located findings, mechanical findings batch into one approval, and queue depth
is a tracked metric demonstrates that you have run one long enough for the
review bottleneck to bite.

### How this would be demonstrated elsewhere

No model ran here, so the drafting, review and migration uses this page
describes were reasoned about rather than measured. The demonstration is
organisational as much as technical: the interesting figures are about review
cost, not model quality.

**What you need.** A model you can call, a corpus with a validator, and,
crucially, a human reviewer's time logged honestly. Two afternoons: one to run
the model over real work, one to review the output while recording how long
each piece took.

**What you would run.** Pick the three lifecycle stages where a model is
plausibly useful and treat each as a separate experiment: drafting a page from
an outline plus source material, reviewing an existing page against a style
guide, and migrating a page between formats. Score each against the check that
already exists for that stage, then record reviewer minutes per page.

**What you would see.**

| Stage | Rough outcome | What it tells you |
|---|---|---|
| Drafting from sources | structurally correct, factually thin | The scaffold is the value, not the prose |
| Drafting without sources | fluent and wrong in ways review misses | The failure this page warns about |
| Style review against a written guide | high agreement with a linter | Cheapest real win |
| Style review against taste | confident and unusable | Guides have to be written down first |
| Format migration | high accuracy, with a long tail | The tail is where the time goes |
| Reviewer minutes, drafted page | often *higher* than writing fresh | The number that decides adoption |

The last row is the measurement that matters and the one nobody records.
Reviewing a plausible wrong draft is slower than writing a page, because
verification requires reading the source material you would have read anyway
plus the draft's claims about it. A pipeline that reduces authoring time and
increases review time has not saved anything.

**How you would know it had failed.** If review time per page is not recorded,
the experiment has measured nothing, whatever the quality scores say. If the
model's drafts pass your validator at a higher rate than your humans' do,
suspect that the validator checks structure and the humans are writing content.
And if migration accuracy is 100%, the sample did not include the awkward cases,
which are the only ones that cost anything.

## Related

- [Freshness monitoring](freshness-monitoring.md), the first check in detail
- [Detecting terminology drift](terminology-drift.md), the third
- [Judging where AI can be trusted](ai-trust-judgment.md), the decision procedure behind the table
- [Prioritizing documentation work](docs-prioritization.md), what to do with the findings
