---
title: Learning paths and curriculum
summary: "A path is a route through a graph rather than a self-contained course, and the gap between those two things is what the reader pays for."
diataxis: how-to
audience: developer
concept: learning-paths
tags: [edu, core]
---

# Learning paths and curriculum

`core` · difficulty 3 · 5h

!!! quote "Asked for by name"
    Intel: "structured learning paths"

**Prerequisites:** [Diátaxis](diataxis.md), [Instructional design for developers](instructional-design.md)

**Leads to:** [Workshops and hands-on labs](workshops.md)

## What it is

An ordered sequence through existing content, aimed at one audience and one
outcome. A path adds no new material. It makes two claims about material that
already exists: that this is the right subset, and that this is the right
order.

Both claims are checkable, which is what separates a learning path from a
list of links with a heading, and almost all published learning paths are
lists of links with a heading.

## Why the job asks for it

Because [Diátaxis](diataxis.md) organises content by its kind, and a reader
does not arrive with a kind. They arrive with a job.

A corpus sorted into tutorials, how-to guides, reference and explanation is
navigable and gives no answer to "I started on Monday, what do I read first".
The four quadrants are an authoring discipline and a filing system; a path is
the reading order that the filing system deliberately does not encode. Intel
asks for "structured learning paths" next to golden paths and quickstarts
because those are the three shapes of the same obligation at three scales: one
command, one page, one career's first fortnight.

The failure mode is specific and nearly universal: a path that is a table of
contents, ordered by the order someone wrote the pages in, with no claim about
prerequisites that anything verifies.

## The golden path

Validate a real curriculum: nine paths over 106 concepts. Find that the
ordering claim holds, the coverage claim does not, and the promise made at the
top of every path page is false. About thirty-five minutes.

**Step 1: the paths as data, not as pages**

```yaml
paths:
  - id: first-week
    name: The first week
    audience: Someone who has just taken one of these roles and needs to be useful by Friday.
    concepts: [technical-writing, docs-as-product, docs-as-code, markdown,
               git-authoring, diataxis, static-site-generators, mkdocs,
               link-checking, documentation-ci]
```

A path is a list of concept ids. That is the whole structure, and it is the
reason any of what follows is possible: the path page is generated, so a path
cannot link to a concept that does not exist, and the sequence can be checked
against the [prerequisite graph](knowledge-architecture.md).

```
  first-week             10 steps  34h
  content-architect      13 steps  43h
  docs-engineer          18 steps  70h
  knowledgeops           17 steps  83h
  developer-educator     15 steps  60h
  writer-who-builds      10 steps  37h
  prove-it               15 steps  59h
```

**Step 2: check the ordering claim**

Every path page says the order matters. For each step, every prerequisite
appearing in the same path must appear earlier:

```python
for learning_path in reg.paths:
    pos = {c: i for i, c in enumerate(learning_path.concepts)}
    for concept in learning_path.concepts:
        for prerequisite in reg.by_id[concept].prerequisites:
            if prerequisite in pos and pos[prerequisite] > pos[concept]:
                findings.path_order_violations.append(...)
```

```
learning paths that teach a concept before its prerequisite: 0
```

Zero across nine paths and 114 steps, and not because the paths were written
carefully. They were reordered twice to satisfy this check when it was first
added. That is the check paying for itself: a curriculum nobody validates
drifts out of order the first time a concept gains a prerequisite.

**Step 3: check the claim the validator deliberately does not make**

The validator contains this comment:

```python
# A prerequisite outside the path is fine: a path is a route
# through the graph, not a self-contained curriculum.
if prerequisite in learning_path.concepts and prerequisite not in seen:
```

A defensible decision, and an unmeasured one. Count the pairs it permits:

```
  first-week           steps assuming something the path never teaches:  1
  content-architect                                                      1
  docs-engineer                                                          5
  knowledgeops                                                           3
  developer-educator                                                     4
  writer-who-builds                                                      3
  prove-it                                                              10

total step-prerequisite pairs pointing outside their path: 27
```

Ten of `prove-it`'s fifteen steps depend on something the path does not cover.
A reader finishing it has been walked through fifteen concepts and quietly
assumed to know seven more.

**Step 4: what the path page actually promised**

```
**15 concepts, roughly 59 hours.** The order matters:
each step assumes the ones above it.
```

"Each step assumes the ones above it" is false for ten of those fifteen steps.
Each step did disclose its own outside prerequisites further down the page, so
the information was present and arrived after the reader had committed.

This is the entry-state commitment from
[instructional design](instructional-design.md), applied to a path rather than
a page, and it had been applied at step level and skipped at path level. The
fix is to compute the assumed set and state it before step 1:

```python
assumed = []
for concept_id in learning_path.concepts:
    for prerequisite in by_id[concept_id].prerequisites:
        if prerequisite not in learning_path.concepts and prerequisite not in assumed:
            assumed.append(prerequisite)
```

```
**Assumed before step 1.** This path does not teach Information architecture,
Choosing a static site generator, Git authoring workflows for writers, Style
guides and terminology management, Reproducible environments, Agent-ready
content, RAG pipelines. Each step below repeats what it assumes.
```

Seven named concepts, before the hours are committed rather than after. A test
asserts it appears above the first step, because the useful version of this
information is the one the reader sees while deciding.

**Step 5: check the coverage claim, which is the worse number**

A path makes a claim about a subset. Ask what the subsets add up to:

```
concepts reachable through some path: 84/106
concepts in no path at all:           22
   of those, written:                 22
   of those, core tier:                4
```

**Four core-tier concepts are in no path.** Not thin pages: core means the
curriculum asserts you cannot do the job without them, and every one of the
twenty-two is written. They are reachable by search and by the dependency
graph, and no curated route goes through them.

That was eleven of thirty-seven when this measurement was first run, over seven
paths. Two paths were added afterwards, one over measurement and automation and
one over domain context, which is what moved it. The figures here are the
current ones and `fieldguide audit` is where to read them; this page was wrong
about them for a while, which is the hazard of a page whose subject is a
measurement of the thing it lives in.

Then the mirror image:

```
concepts in exactly one path: 62
most reused: diataxis 4, docs-as-product 3, docs-as-code 3, link-checking 3
```

Sixty-two concepts carry one path each. A path that is the sole route to well
over half the corpus is doing navigation work, not curriculum work, and that is
the honest reading of what nine paths over 106 concepts produces.

**Step 6: which of the two gaps to fix**

They want opposite things. Closing the prerequisite gaps means lengthening
paths, and `prove-it` at 59 hours would become unrecommendable. Closing the
coverage gap means adding paths or widening them, which worsens the
prerequisite gaps.

The resolution is to stop treating them as the same defect. Prerequisite gaps
are a **disclosure** problem, fixed in step 4 at the cost of one computed
paragraph. Coverage is a **curriculum** problem, and eleven uncovered core
concepts is a decision about whether every core concept deserves a route, which
is a judgment the numbers inform and do not make.

What is not defensible is the state before this exercise: both gaps present,
neither measured, and a promise at the top of every page that the data
contradicted.

**What you built.** Seven validated paths, an ordering check at zero
violations, an entry state stated before step 1 and asserted by a test, and two
measured gaps that pull in opposite directions.

## Reference

### Path against the alternatives

| | Diátaxis quadrant | Path | Study plan |
|---|---|---|---|
| Ordered by | Kind of content | One audience's job | The dependency graph |
| Covers | Everything, filed | A chosen subset | Everything |
| Written by | The content model | Judgment | A topological sort |
| Claims | This is a how-to | This subset, this order | No cycles |
| Fails by | Miscategorising | Omitting, or over-including | Being 106 steps long |

This guide generates all three from one registry, which is the argument for
keeping a path as data. The study plan is the honest fallback for the 37
concepts no path reaches.

### What a path has to declare

| Field | Why |
|---|---|
| Audience, in one sentence | A path for everyone is a table of contents |
| Outcome | What the reader can do at the end |
| Entry state | See step 4; the one most often skipped |
| Step order | And a check that prerequisites precede their dependents |
| Total time | A reader commits hours, not steps |
| Per-step time | So a path can be paused |

### How paths fail

| Failure | Detected by |
|---|---|
| A step precedes its prerequisite | The ordering check |
| Steps assume material the path omits | The closure count, step 3 |
| The entry state is stated only per step | Reading the top of the page |
| Core concepts in no path | The coverage count, step 5 |
| A path is the sole route to a third of the corpus | The reuse count |
| Links to pages that do not exist | Generating the page from the registry |
| Ordered by authoring date | Nothing; this needs a person |

The last row is the common case in the wild, and no check catches it, because
authoring order is a valid order. It is just never the right one.

### Sizing

| Length | Reads as | Risk |
|---|---|---|
| Under 5 steps | A reading list | Not worth the page |
| 8 to 15 steps | A path | Right for most audiences |
| Over 18 steps | A syllabus | Abandoned partway, invisibly |
| Over 60 hours | A qualification | Needs checkpoints and a reason |

This guide's longest is 18 steps and 83 hours, which is over the line, and the
mitigation is that every step is independently useful. That is a weaker answer
than splitting it.

### Keeping it honest

| Rule | Because |
|---|---|
| Paths live in the registry, not in prose | Pages generated from data cannot link to nothing |
| Ordering is checked in CI | A new prerequisite silently invalidates an order |
| The entry state is computed, not written | Hand-written assumptions go stale |
| Coverage is reported | Orphaned core concepts are invisible otherwise |
| Reuse is reported | A concept in four paths is load-bearing |

## How to talk about it

**Lead with why Diátaxis is not enough.** "Diátaxis sorts content by kind, and
a reader does not arrive with a kind, they arrive with a job. The four
quadrants are an authoring discipline; a path is the reading order the filing
system deliberately does not encode. So I keep paths as data in the registry
and generate the pages, which means a path cannot point at a concept that does
not exist, and the order can be checked against the prerequisite graph."

**The follow-up is what the check actually caught, and here the numbers are
worth stating precisely.** Ordering came out at zero violations across nine
paths and 114 steps, and only because two paths were reordered when the check
was added. The interesting number is the one the validator deliberately does
not check: 32 step-prerequisite pairs point outside their path, and on
`prove-it` ten of fifteen steps depend on something it never teaches.

**Then the finding that changed the generator.** Every path page promised that
each step assumes the ones above it, which was false for those ten steps. The
information existed, disclosed per step, further down the page, after the
reader had already committed to 59 hours. So the generator now computes the
assumed set and states it before step 1, and a test asserts it appears above
the first heading, because the useful version of that information is the one
visible while deciding whether to start.

**The tradeoff to volunteer.** The two gaps pull in opposite directions.
Closing the prerequisite gaps lengthens paths past the point anyone finishes
them; closing the coverage gap, four core concepts currently in no path, means
more or wider paths, which worsens the prerequisite gaps. I do not think there
is a clean answer. What I would not defend is where this started, with both
gaps unmeasured and a promise on every page that the data contradicted.

**One sharper point.** Sixty-two of the 106 concepts sit in exactly one path.
A path that is the sole route to a third of a corpus is doing navigation work
rather than curriculum work, and calling it curriculum obscures that the real
need was [findability](findability.md).

## How to prove it

**The artifact.** Paths held as data, pages generated from them, an ordering
check and a coverage report in CI, and an entry state computed per path.

**Three things to do, in order:**

1. Take your longest learning path and count how many steps depend on
   something it never teaches. If that number is not zero, the page's promise
   about ordering is false, and the fix is one computed paragraph.
2. Count the concepts your paths do not reach, split by whether you consider
   them essential. The essential ones in no path are your real finding.
3. Count how many paths each item appears in. Anything appearing once is
   navigation, not curriculum, and should probably be solved by search instead.

**What makes it credible rather than decorative.** This guide holds nine paths
over 106 concepts in `concepts.yaml`, generates every path page from them, and
fails CI on an ordering violation; the entry-state paragraph and its test were
added by the exercise above. The honest limits: no reader has completed any of
these paths, so there is no evidence the orders are *good*, only that they are
consistent with the prerequisite graph, and the
[demonstrated](../demonstrated.md) page records that distinction.

## Related

- [Instructional design for developers](instructional-design.md), where the entry-state commitment comes from
- [Diátaxis](diataxis.md), the filing system a path deliberately cuts across
- [Knowledge architecture](knowledge-architecture.md), the prerequisite graph underneath
- [Cognitive load in technical content](cognitive-load.md), the cross-reference census over these paths
- [Workshops and hands-on labs](workshops.md), a path compressed into a room
- [Findability and search](findability.md), what a single-path concept actually needed
