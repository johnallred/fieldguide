---
title: Agentic workflows
summary: Documentation work done by an agent over several steps, and the checkpoints that keep it reviewable.
diataxis: explanation
audience: developer
concept: agentic-workflows
tags: [ai, core]
---

# Agentic workflows

`core` · difficulty 3 · 6h

> structure and package content for RAG, internal assistants, and agentic workflows

> Source: nvidia posting, verbatim

**Prerequisites:** [Model Context Protocol](mcp.md), [Agent skills and context kits](agent-skills.md)

## What it is

Documentation work carried out by an agent across several steps, where each step
depends on what the previous one found: audit the corpus, pick the stale pages,
check each against the code, propose edits, open a pull request.

The distinguishing feature is **the agent chooses what to do next**. That is
what separates it from a script, and it is the entire source of both the value
and the difficulty.

## Why the job asks for it

NVIDIA names it as the third consumer of AI-ready content, alongside RAG and
internal assistants. Intel's version is "the agentic toolkit" and "coding
agents" as a documentation audience.

What makes it `core` and difficulty 3 is that **the usual review model stops
working.** For a single generated answer you can check the output: grounded,
cited, correct. For a twelve-step run you get a pull request and a summary, and
the summary is written by the thing you are checking. If step 3 picked the wrong
pages, every later step did excellent work on the wrong input, and the pull
request looks fine.

On a Tuesday that failure is concrete. An agent was asked to update version
references after a 2.6 release. It opened a tidy pull request touching nine
pages. Seven were correct. One updated a deliberately pinned example in a
migration guide, and one updated a version string inside a quoted error message,
where the old version is the whole point. The summary said "updated version
references across nine pages", which is true. **Review caught it because
somebody read the diff, not because any check did.**

## The golden path

Build an agentic documentation workflow with checkpoints, then watch a wrong
decision at step 2 propagate into confident work at every later step. Fifty
minutes, dependency-free.

**Step 1: a corpus with traps in it**

```bash
mkdir -p agentic-drill/docs/{how-to,reference,explanation} && cd agentic-drill
cat > docs/how-to/install.md <<'EOF'
---
title: Install the CLI
updated: 2024-01-15
---
# Install the CLI

Requires widget 2.2 or newer.

    pip install widget==2.2
EOF

cat > docs/how-to/migrate-from-2-2.md <<'EOF'
---
title: Migrate from 2.2
updated: 2024-02-01
pinned_versions: true
---
# Migrate from 2.2

This guide is specifically about moving off widget 2.2. Do not update these
version references; they are the subject of the page.

    pip install widget==2.2
EOF

cat > docs/reference/errors.md <<'EOF'
---
title: Error reference
updated: 2024-03-10
---
# Error reference

## E_VERSION_MISMATCH

The server emits this verbatim:

    error: client widget 2.2 is older than server widget 2.4

Match the client to the server.
EOF

cat > docs/explanation/design.md <<'EOF'
---
title: Why batching is opt-in
updated: 2026-09-01
---
# Why batching is opt-in

Batching changes latency characteristics, so it is never enabled by default.
EOF
find docs -name "*.md" | sort
```

Four pages. One genuinely needs updating, one must never be touched, one
contains a version inside quoted output, and one is current and irrelevant.

**Step 2: the workflow, with a checkpoint between every step**

```bash
cat > workflow.py <<'PY'
"""An agentic documentation workflow with inspectable checkpoints.

The structure is the whole lesson. Each step takes the previous step's
OUTPUT as explicit input and records what it decided, so a wrong decision
early is visible as a wrong decision rather than as a confusing diff at the
end.

Steps:
  1 SURVEY    what exists, with the metadata that matters
  2 SELECT    which pages are in scope          <- the decision that matters
  3 INSPECT   what in each page would change
  4 PROPOSE   the edits, as a diff, applied to nothing
  5 GATE      refuse to proceed past declared tripwires

The agent's judgement lives in step 2. Everything after it is mechanical,
which means everything after it will be done competently on whatever step 2
chose. That asymmetry is why step 2 gets its own checkpoint.
"""
import datetime as dt
import difflib
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

CURRENT = "2.6"
STALE_DAYS = 365
VERSION = re.compile(r"widget[ =]{1,2}(\d+\.\d+)")


@dataclass
class Checkpoint:
    """One step's decision, recorded so a human can audit the sequence."""

    step: str
    decided: list = field(default_factory=list)
    skipped: list = field(default_factory=list)
    notes: list = field(default_factory=list)

    def show(self):
        print(f"--- {self.step} ---")
        for item in self.decided:
            print(f"    in:   {item}")
        for item in self.skipped:
            print(f"    out:  {item}")
        for note in self.notes:
            print(f"    note: {note}")
        print()


def survey(root: Path):
    """Step 1: what exists. No judgement here."""
    pages = []
    for path in sorted(root.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        meta = yaml.safe_load(text.split("---")[1]) or {}
        pages.append({"path": path, "meta": meta, "text": text})
    cp = Checkpoint("1 survey")
    cp.decided = [f"{p['path']}  updated {p['meta'].get('updated')}" for p in pages]
    return pages, cp


def select(pages, respect_pins=True):
    """Step 2: which pages are in scope. THE decision.

    `respect_pins` exists so the golden path can run this step wrong and show
    what happens downstream. A real agent gets this wrong by not knowing the
    convention exists, which is what a context kit is for.
    """
    cp = Checkpoint("2 select")
    today = dt.date.today()
    chosen = []
    for page in pages:
        path, meta, text = page["path"], page["meta"], page["text"]
        updated = meta.get("updated")
        if isinstance(updated, str):
            updated = dt.date.fromisoformat(updated)

        if respect_pins and meta.get("pinned_versions"):
            cp.skipped.append(f"{path}  (pinned_versions: true)")
            continue
        if not VERSION.search(text):
            cp.skipped.append(f"{path}  (no version reference)")
            continue
        if updated and (today - updated).days <= STALE_DAYS:
            cp.skipped.append(f"{path}  (reviewed within {STALE_DAYS} days)")
            continue
        chosen.append(page)
        cp.decided.append(str(path))
    if not respect_pins:
        cp.notes.append("respect_pins=False: pinned pages were NOT excluded")
    return chosen, cp


def inspect(chosen):
    """Step 3: what in each page would change, and what must not."""
    cp = Checkpoint("3 inspect")
    findings = []
    for page in chosen:
        path, text = page["path"], page["text"]
        in_block = False
        for number, line in enumerate(text.splitlines(), 1):
            # A version inside quoted program output is not ours to change.
            # Detecting that is step 3's job; step 4 only applies decisions.
            quoted = line.startswith("    ") and (
                "error:" in line or "warning:" in line
            )
            for version in VERSION.findall(line):
                if version == CURRENT:
                    continue
                item = {"path": path, "line": number, "version": version,
                        "text": line, "quoted": quoted}
                if quoted:
                    cp.skipped.append(f"{path}:{number}  quoted output, left alone")
                else:
                    findings.append(item)
                    cp.decided.append(f"{path}:{number}  {version} -> {CURRENT}")
    return findings, cp


def propose(findings):
    """Step 4: build diffs. Writes nothing."""
    cp = Checkpoint("4 propose")
    diffs = {}
    by_path = {}
    for finding in findings:
        by_path.setdefault(finding["path"], []).append(finding)

    for path, items in by_path.items():
        original = path.read_text(encoding="utf-8")
        updated = original
        for item in items:
            updated = updated.replace(item["text"],
                                      VERSION.sub(lambda m: m.group(0).replace(
                                          m.group(1), CURRENT), item["text"]))
        diff = list(difflib.unified_diff(
            original.splitlines(), updated.splitlines(),
            fromfile=str(path), tofile=f"{path} (proposed)", lineterm="",
        ))
        diffs[path] = diff
        cp.decided.append(f"{path}  {len(items)} line(s)")
    return diffs, cp


def gate(diffs, pages):
    """Step 5: tripwires. Declared in advance, checked before anything ships.

    These are not quality checks. They are statements about what this
    workflow is NOT allowed to do, which is the only kind of check that
    survives an agent being competent and wrong.
    """
    cp = Checkpoint("5 gate")
    pinned = {p["path"] for p in pages if p["meta"].get("pinned_versions")}
    failures = []

    for path in diffs:
        if path in pinned:
            failures.append(f"{path} is pinned and must never be edited")
    if len(diffs) > 5:
        failures.append(f"{len(diffs)} files exceeds the 5-file limit for one run")
    for path, diff in diffs.items():
        added = [l for l in diff if l.startswith("+") and not l.startswith("+++")]
        if len(added) > 10:
            failures.append(f"{path}: {len(added)} added lines exceeds the limit")

    cp.notes = failures or ["all tripwires clear"]
    return failures, cp
PY
echo "workflow written"
```

**Step 3: run it correctly**

```bash
cat > run.py <<'PY'
import sys
from pathlib import Path

from workflow import gate, inspect, propose, select, survey

respect_pins = "--ignore-pins" not in sys.argv

pages, cp1 = survey(Path("docs"))
cp1.show()
chosen, cp2 = select(pages, respect_pins=respect_pins)
cp2.show()
findings, cp3 = inspect(chosen)
cp3.show()
diffs, cp4 = propose(findings)
cp4.show()
failures, cp5 = gate(diffs, pages)
cp5.show()

print("=== what a reviewer would see at the end ===")
print(f"summary: updated version references across {len(diffs)} page(s)")
for path, diff in diffs.items():
    for line in diff:
        if line.startswith(("+++", "---", "@@")) or line.startswith(("+", "-")):
            print(f"  {line}")
print()
print(f"VERDICT: {'BLOCKED' if failures else 'ready for review'}")
sys.exit(1 if failures else 0)
PY
python3 run.py; echo "exit=$?"
```

**Step 4: run it with one wrong decision at step 2**

```bash
echo "############ step 2 does not know about pinned_versions ############"
python3 run.py --ignore-pins; echo "exit=$?"
```

**What you built.** A five-step workflow where every step records its decision,
and a tripwire that catches a wrong early decision after four later steps did
competent work on top of it.

### The correct run

Step 2 selects two pages and records why it rejected the other two: one has no
version reference, one is `pinned_versions: true`. Step 3 then finds two
updatable lines in `install.md` and **excludes two lines in `errors.md` as
quoted program output**. Step 5 passes, and the diff is two lines.

Note that step 3's exclusion is as important as its inclusions. The version
inside `error: client widget 2.2 is older than server widget 2.4` is the
subject of the error reference, not a stale fact.

### The run with one wrong decision at step 2

`--ignore-pins` makes step 2 unaware of the pinning convention. Everything
downstream then works perfectly on the wrong input:

```diff
--- docs/how-to/migrate-from-2-2.md
+++ docs/how-to/migrate-from-2-2.md (proposed)
-This guide is specifically about moving off widget 2.2. Do not update these
+This guide is specifically about moving off widget 2.6. Do not update these
-    pip install widget==2.2
+    pip install widget==2.6
```

Read that diff. The agent edited a sentence that **says not to make this
edit**, turning a migration guide about moving off 2.2 into a guide about
moving off 2.6, which is incoherent. It also left `errors.md` alone correctly,
which is the tell: steps 3 and 4 were working well the entire time.

The summary line reads "updated version references across 2 page(s)", which is
accurate. Nothing in the output is self-evidently wrong except the content of
one diff hunk.

**It was blocked by the tripwire, not by any quality check**, and that is the
point of the whole page: a run can be competent at every step after the one
that mattered.

## Reference

### Why review breaks down

| Single generated answer | A multi-step run |
|---|---|
| One output to check | A diff plus a summary written by the agent |
| Wrong is visible | Wrong looks like competent work on the wrong input |
| [Grounding](grounding.md) applies | Nothing to ground against; it is an action, not a claim |
| Cheap to re-run | Expensive, and the state has changed |
| Failure is one bad answer | Failure is nine correct edits and two harmful ones |

**The asymmetry is the problem.** The agent's judgement is concentrated in one
or two early steps, and everything after is executed well regardless. So the
review has to target the decisions, not the output.

### Checkpoints: what to record at each step

| Step | Record | Why |
|---|---|---|
| Survey | What was found | So scope is auditable |
| **Select** | **What was included AND excluded, with reasons** | **The decision that matters** |
| Inspect | What would change, and what was deliberately left | Surfaces the quoted-output case |
| Propose | Diffs, applied to nothing | A diff is reviewable; an applied change is not |
| Gate | Which tripwires were checked | Proves the limits ran |

The exclusions in step 2 are the single most valuable thing in the log. An agent
that skipped a page for a stated reason can be checked; an agent that silently
did not consider it cannot.

### Tripwires, and why they are not quality checks

A tripwire is a statement about what this workflow may never do, declared
before the run:

| Tripwire | Catches |
|---|---|
| Never edit a page with `pinned_versions` | The failure in step 4 above |
| No more than N files per run | Runaway scope |
| No more than N added lines per file | A rewrite disguised as an edit |
| Never edit CI config, lint rules or validators | [Widening a constraint](agent-skills.md) to pass |
| Never delete a file | Irreversible, and rarely the intent |
| Diff only; a human applies | The strongest version, and the slowest |

They work precisely because they do not depend on judging the work. A competent,
confidently wrong run passes every quality check and still trips a limit.

### Where to put a human

| Placement | Cost | Catches |
|---|---|---|
| Review the final pull request | low | What a reader notices in a diff |
| **Approve the step 2 selection** | **low** | **The decision that determines everything else** |
| Approve each proposed edit | high | Everything, slowly |
| Sample runs after trusting it | low | Drift, eventually |

Approving the selection is the best value by a wide margin: it is a short list,
it is cheap to read, and it is where the agent's judgement actually was.

### What makes a task suitable

| Suitable | Unsuitable |
|---|---|
| Mechanical change, many files | A change needing product judgement |
| Reversible | Deletion, publication, anything irreversible |
| Verifiable by a gate | "Make the docs better" |
| Scoped by a declared rule | Scoped by vibes |
| Proposes, does not apply | Direct commits to a default branch |

Mapped onto [judging where AI can be trusted](ai-trust-judgment.md): an agentic
workflow belongs in the *proposes-for-review* cell, and the tripwires are what
keep it there when a run goes wrong.

## How to talk about it

**What a competent answer sounds like.** Lead with the review problem, because
that is the thing that distinguishes this from "we ran a script". "The usual
check does not work on a multi-step run. You get a diff and a summary written by
the thing you are reviewing, and if the selection step picked the wrong pages
then every later step did competent work on the wrong input and the summary is
accurate. So I record what each step decided, including what it excluded and
why, put the human approval on the selection rather than on the final diff, and
declare tripwires in advance: never touch a page marked pinned, never more than
five files, never edit the validators."

**The follow-up is "how do you stop it going off the rails",** and the answer that
lands is that you do not rely on the agent for that. Tripwires work because they
do not judge the work: a run that is competent and wrong passes every quality
check and still fails a file-count limit. Pair that with proposing diffs rather
than applying them, so the worst outcome is a rejected pull request.

**The tradeoff to volunteer.** Checkpoints and tripwires cost most of the
speedup. A run that proposes a diff for human approval, with a five-file limit,
is not much faster than doing the work yourself for anything small, and the
honest payoff only arrives at volume: a hundred pages, a mechanical change, a
rule you can state. Below that it is overhead. There is also a trap in trusting
it over time: tripwires get raised because they keep blocking legitimate runs,
and a limit raised three times is a limit that no longer limits.

**One sharper point.** The strongest observation is that **an agentic workflow is a
forcing function for writing your conventions down.** The step 4 failure happens
because `pinned_versions` was a convention in somebody's head; once it is a
front-matter field, both the agent and the tripwire can see it. Every failure of
this kind turns into a piece of machine-readable
[metadata](metadata.md) that also makes the corpus better for humans. So the
real output of adopting agentic workflows is usually a better
[content model](content-model.md), which is a much more interesting claim than
a productivity one and happens to be the one that survives contact with a
documentation lead.

## How to prove it

**The artifact.** A workflow with per-step checkpoints and declared tripwires,
plus the run where an early wrong decision produces competent downstream work.

**Three things to do, in order:**

1. **Run the golden path both ways.** The `--ignore-pins` run is the
   demonstration: identical-looking output, correct-looking diffs, blocked only
   by a tripwire.
2. **Write the tripwires for a task you would actually automate.** Five lines.
   Doing this before building anything is the habit worth demonstrating. Write
   the tripwires before you look at the task's failure modes, then compare.
   The ones you missed are the ones that will fire in production.
3. **Find a convention that only exists in someone's head** and turn it into a
   front-matter field, so a gate can see it. That is the durable output, and it
   improves the corpus whether or not the agent ever runs.

**What makes it credible rather than decorative.** Describing agent workflows is cheap. Per-step
checkpoints that record exclusions, tripwires declared in advance, and a
demonstrated run where everything downstream of a bad decision looked right
shows that you have thought about how these fail rather than how they help.

### How this would be demonstrated elsewhere

The checkpointing structure this page describes was demonstrated here with a
scripted stand-in; the part that needs a real agent, where a wrong decision at
step two propagates into confident work at every later step, was reasoned about
rather than observed.

**What you need.** An agent runtime that can take multi-step actions on a
repository, and a corpus with deliberately planted traps: a stale page, a
contradictory pair of statements, a sample that does not run. The traps are the
experiment. An agentic workflow on a clean corpus demonstrates nothing, because
nothing requires judgment.

**What you would run.** Give the agent a multi-step task over the trapped
corpus, such as "find pages contradicting the reference and fix them", with
checkpoints after each step, and record not just the outcome but *where the
first wrong decision happened* and what the agent did afterwards.

**What you would see.**

| Observation | Rough behaviour | What it tells you |
|---|---|---|
| Tasks completed with no wrong step | some fraction, never all | The baseline |
| What happens after one wrong step | later steps build on it confidently | The failure this page is about |
| Whether the agent reports uncertainty | rarely, unprompted | Why checkpoints are external, not asked for |
| Cost of a checkpoint that a human reads | the whole saving | The real economics |
| Behaviour when a trap is unflagged | the trap propagates silently | Why the corpus needs its own checks |

The second row is the point. A wrong step does not produce an error, it produces
a premise, and every later step is executed competently against it. That is why
this page argues for checkpoints at decision boundaries rather than at the end:
a review of the final output cannot tell which premise it rested on.

**How you would know it had failed.** If the agent completes every trapped task
correctly, the traps are too obvious and need to be subtler than a wrong word.
If it fails at step one every time, the task is underspecified and you are
measuring instruction quality. And if checkpoint review takes as long as doing
the task, the workflow is theatre, which is a legitimate finding and worth
publishing.

## Related

- [Agent skills and context kits](agent-skills.md), how the agent learns the conventions
- [Model Context Protocol](mcp.md), how it reads the corpus
- [Judging where AI can be trusted](ai-trust-judgment.md), whether to automate at all
- [LLMs in the content lifecycle](llm-content-lifecycle.md), the tasks worth running this way
