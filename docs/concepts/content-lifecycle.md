---
title: Content lifecycle and governance
summary: "The states a page moves through, and making the state a field something checks rather than a label."
diataxis: explanation
audience: developer
concept: content-lifecycle
tags: [ia, supporting]
---

# Content lifecycle and governance

`supporting` · difficulty 2 · 3h

!!! quote "Asked for by name"
    NVIDIA: "Automate the content lifecycle with LLMs and scripting, from drafting and updating to auditing, with checks for freshness, code accuracy, and terminology drift, and human review where judgment matters"

**Prerequisites:** [Content models](content-model.md)

**Leads to:** [Freshness monitoring](freshness-monitoring.md), [Retiring content](content-retirement.md)

## What it is

The states a page moves through from proposal to retirement, who owns it in
each state, and what has to be true before it moves. Governance is the part
that says who decides.

NVIDIA's phrasing names four activities: drafting, updating, auditing, and
human review where judgment matters. That last clause is the governance
question, and it is the one that determines whether the first three are worth
automating.

## Why the job asks for it

Because a corpus without a lifecycle has exactly one state, which is
"published", and therefore no mechanism for anything. A page cannot be known to
be a draft, cannot be flagged for review, and cannot be retired, so the corpus
only ever grows.

The automation NVIDIA asks for is downstream of the states. You cannot automate
auditing without a definition of what is due for audit, and that definition is
a lifecycle state plus a date. Teams that try to add the automation first end
up with a script producing a list nobody owns.

The sharper version, and the subject of the golden path: a lifecycle state is
only real if something checks it. A `status` field that nothing validates is a
label, and labels drift.

## The golden path

Define a lifecycle, then make each state claim falsifiable. About thirty
minutes. This uses this guide's own registry, where the lifecycle is three
states and every one of them is checked.

**Step 1: the states, as a closed vocabulary**

```python
STATUSES = ("planned", "drafted", "complete")
```

Three states, deliberately few. `planned` means the concept is on the
curriculum with no prose; `drafted` means prose exists and has not been
verified; `complete` means it satisfies the page contract.

**Step 2: decide what each state claims**

This is the design work, and it is the whole concept. For each state, write
down what a reader is entitled to assume:

| State | The claim | Falsifiable by |
|---|---|---|
| `planned` | A placeholder exists, carrying its registry metadata | A generated page exists |
| `drafted` | Prose exists; nothing is promised about it | A file exists |
| `complete` | Six required sections, 450+ words, every golden path executed | Section and length check |

A state whose claim you cannot write down is a state that does nothing.

**Step 3: make each claim fail**

```
  CAUGHT check  complete concept, page deleted
  CAUGHT check  complete page truncated below 450 words
  CAUGHT check  complete page missing a required section
  CAUGHT check  an orphan page with no concept
```

Each of those is a lifecycle lie: a page claiming a state it has not earned.
With the checks in place, `status: complete` is a statement about the file
rather than an opinion.

Note what is **not** checked, and say so out loud: nothing verifies that the
golden path on a `complete` page was actually executed. That part of the claim
rests on the author's discipline, and pretending otherwise would be the sort of
thing this page argues against.

**Step 4: the state that needs a date, not a check**

Three states are enough for authoring and not enough for maintenance, because
a page can be `complete` and wrong. That is the
[freshness](freshness-monitoring.md) problem, and the lifecycle hook for it is
a review date rather than another state:

```yaml
reviewed: 2026-01-10
documents: src/client.py
```

Measured on the freshness page: comparing a page's edit date against its
subject's finds nothing after a bulk commit, and comparing against an explicit
`reviewed:` date finds the real drift. So the lifecycle field that matters for
maintenance is a date somebody sets deliberately, not a timestamp the file
system supplies.

**Step 5: governance, which is the part with no code**

Write down, in the repository, who decides:

```markdown
## Ownership

| Area            | Owner        | Review cadence |
|-----------------|--------------|----------------|
| Install & setup | Platform     | Each release   |
| API reference   | Generated    | Automatic      |
| Concepts        | Docs lead    | Annual         |
| Playbooks       | Service team | Each incident  |
```

Four rows and a cadence beat a governance document nobody reads. The useful
test is whether a page in your corpus can be traced to a person; if it cannot,
the lifecycle has no actor and the states will not move.

**What you built.** Three states whose claims are checkable, a review date for
the one claim a state cannot carry, and a named owner per area.

## Reference

### A lifecycle that is worth having

| State | Means | Entry condition | Who |
|---|---|---|---|
| Proposed | Someone asked for it | A request, or a gap in a coverage matrix | Anyone |
| Planned | It is on the roadmap | Accepted, with a named owner | Docs lead |
| Drafted | Prose exists | A file in the repository | Author |
| In review | Awaiting judgment | Gates green; see [docs review](docs-review.md) | Reviewer |
| Published | Readers can rely on it | Contract satisfied, merged | Author plus reviewer |
| Due for review | Its subject moved, or the clock ran out | [Freshness](freshness-monitoring.md) signal | Owner |
| Deprecated | Still true for old versions | Superseded | Owner |
| Retired | Gone, with a redirect | See [retirement](content-retirement.md) | Docs lead |

Most corpora need fewer than this. The test for each state is whether
something different happens because a page is in it.

### What to automate and what not to

NVIDIA's list, with the honest division:

| Activity | Automatable | What stays human |
|---|---|---|
| Drafting | Partly; an LLM can produce a first pass against a template | Whether the page should exist |
| Updating | Partly; a mechanical change can be proposed | Whether the change is correct |
| Auditing | Yes; freshness, drift, code accuracy are all measurable | Which findings matter |
| Review | No | All of it |
| Retiring | The mechanics | The decision |

The pattern across every row: **measurement automates, judgment does not.**
That is also NVIDIA's own framing, "human review where judgment matters", and
echoing it back with this division is a strong answer.

### Making a state real

| Requirement | Without it |
|---|---|
| Closed vocabulary | States accumulate: "mostly done", "needs a look" |
| A written claim per state | Nobody knows what the label asserts |
| A check per claim | The label drifts from the file |
| An owner per area | No actor, so nothing moves between states |
| A trigger out of each state | Pages enter "published" and never leave |

The last row is the one that produces 4,000-page corpora where a third is
wrong. Entry conditions are usually defined and exit conditions almost never
are.

### Governance artifacts that actually get used

| Artifact | Why it works |
|---|---|
| An owner table in the repository | Short, versioned, reviewable |
| A review cadence per area, not per page | Per-page dates are never maintained |
| A coverage matrix with states | Makes the gaps visible, which is what drives work |
| A standing queue of audit findings | Converts measurement into a work item |
| A retirement policy | Permits deletion, which otherwise never happens |

## How to talk about it

**Lead with falsifiability.** "A lifecycle state is only real if something
checks it. In my own registry, `complete` claims seven required sections and a
minimum length, and all of those fail a build if they are not true. Before the
checks existed, `complete` was an opinion."

**The follow-up is NVIDIA's own clause**, human review where judgment matters,
and the division to offer is that measurement automates and judgment does not.
Freshness, terminology drift and code accuracy are all measurable; whether a
page should exist, and whether a proposed correction is right, are not.

**The tradeoff to volunteer.** Every state is overhead, and a lifecycle with
eight states on a corpus of two hundred pages means authors spend their time
in a workflow instead of writing. Three states that are checked beat eight that
are aspirational. Add a state when something different will actually happen
because a page is in it.

**One sharper point, and the honest one.** Not every claim a state makes is
checkable. My `complete` state asserts that the page's golden path was
executed, and nothing verifies that. I can check the section headings and the
word count; I cannot check that I ran the code. Being able to say which part of
your own claim rests on discipline rather than on a gate is worth more than
claiming the gate covers everything.

## How to prove it

**The artifact.** A closed state vocabulary, a written claim per state, a check
per claim, and an owner table.

**Three things to do, in order:**

1. Write down what each of your current states asserts. Any state you cannot
   write a claim for should be deleted.
2. Pick the most load-bearing claim and make it fail a build. One check.
3. Write the owner table. Four rows is enough, and a page that cannot be traced
   to a person has no lifecycle.

**What makes it credible rather than decorative.** Neither of this guide's
repositories implements a governance process, which the
[demonstrated](../demonstrated.md) page records, because process needs an
organisation. What does exist is the falsifiable half: three states, a written
claim each, and twelve defect classes that fail a build, plus an explicit note
about the one part of the `complete` claim that no check covers.

### How this would be demonstrated elsewhere

The mechanism is here and the process is not. This repository has three
lifecycle states, a written claim behind each, and a validator that checks
them, which is the falsifiable half. What it cannot have is a year of the
states actually being applied by people with other priorities.

**What you need.** An organisation, a corpus with more than one owner, and
twelve months. Nothing technical.

**What a learner would do.** Pick the state transition your team already gets
wrong, usually "current" to "needs review", and instrument only that one.
Record, for three months, how many pages entered it, how many left, and how
many were still there at the end. Those three numbers are the whole
demonstration.

**What you would see.**

| Observation | Typical | What it tells you |
|---|---|---|
| Pages entering review | Steady, driven by a date | The trigger works |
| Pages leaving review | Far fewer | The usual finding |
| Pages stuck past a quarter | The majority | Review is a state, not a process |
| Pages retired | Almost none | Nobody is rewarded for deleting |

The gap between rows one and two is the measurement. A lifecycle that moves
pages in and not out is a backlog with a vocabulary, and the number makes that
arguable rather than a matter of opinion.

**Why it does not commit.** The states commit; the transitions are events in
people's weeks. A reader of this repository sees three states correctly
enforced and cannot tell whether anything ever moved between them, because with
one author and no readers nothing has.

## Related

- [Content models](content-model.md), where the state vocabulary lives
- [Freshness monitoring](freshness-monitoring.md), the signal that moves a page out of published
- [Retiring content](content-retirement.md), the exit nobody builds
- [Reviewing documentation](docs-review.md), the human stage this schedules
