---
title: Guided workflows
summary: "A checklist that verifies each item instead of asking, and the sequencing mistake that doubles the round trips."
diataxis: how-to
audience: developer
concept: guided-workflows
tags: [gp, core]
---

# Guided workflows

`core` · difficulty 3 · 5h

!!! quote "Asked for by name"
    NVIDIA: "Encode standards (user stories, release readiness, onboarding, security guidance) into templates, validators, and guided workflows rather than static documents"

**Prerequisites:** [Templates and scaffolding](templates-scaffolding.md)

## What it is

The third thing on NVIDIA's list, and the most ambitious. A
[template](templates-scaffolding.md) gives you a correctly shaped artifact. A
validator tells you whether an artifact is correct. A guided workflow **walks
you through a process**, checking as it goes, so that completing it is the same
act as satisfying the standard.

The concrete form is usually a command rather than a page: `release-check`,
`onboard`, `new-integration`. It replaces a checklist page where a human reads
an item, decides whether it is done, and ticks it.

## Why the job asks for it

Because a checklist asks a question the reader is badly placed to answer.

"Every page has a summary" is an item on a release checklist. The person
reading it has to decide whether that is true, which means either checking 121
pages or guessing. Under deadline they guess, and the checklist records a yes
that means "I did not look". A guided workflow answers the question instead of
asking it, and the difference is not convenience: it is whether the record is
true.

NVIDIA's phrase is again **rather than static documents**. The standard that
exists as a page is a standard whose compliance is self-reported.

## The golden path

Build a release workflow, then discover that the obvious sequencing doubles
the author's round trips. About thirty-five minutes.

**Step 1: steps that verify instead of asking**

```python
class Blocked(Exception): pass

@step("every page has a summary")
def check_summaries(root):
    bad = [p.name for p in (root / "docs").glob("*.md")
           if "summary:" not in p.read_text()]
    if bad:
        raise Blocked(f"missing summary: {', '.join(bad)}")
    return f"{len(list((root / 'docs').glob('*.md')))} pages have a summary"


@step("the changelog mentions this version")
def check_changelog(root):
    version = (root / "VERSION").read_text().strip()
    if version not in (root / "CHANGELOG.md").read_text():
        raise Blocked(f"CHANGELOG.md does not mention {version}")
    return f"changelog covers {version}"
```

Three properties make these workflow steps rather than tests. Each has a
**human-readable name** that reads like a checklist item. Each returns a
**detail on success**, so the output is a record rather than a row of ticks.
And each raises `Blocked` with the specific thing to fix, not an assertion
failure.

**Step 2: run it against a repository with three real problems**

```bash
python3 release.py .
```

```
  [1/3] BLOCKED  every page has a summary
           missing summary: b.md

stopped at step 1. Fix the above and re-run.
exit=1
```

Precise and actionable. It names the file.

**Step 3: count what that costs**

Fix exactly what it reports, re-run, repeat, the way an author would:

```
  [1/3] BLOCKED  every page has a summary
  [2/3] BLOCKED  the changelog mentions this version
  [3/3] BLOCKED  no TODO markers in published pages
  all steps passed; ready to release
  runs needed: 4
```

Four runs for three defects. The workflow stopped at the first failure each
time, so the author learned about one problem per round trip.

This is the `&&` problem from [documentation CI](documentation-ci.md) wearing
different clothes, and it is harder to see here because a *workflow* feels like
it ought to be sequential. It is a workflow; steps come in an order; stopping
at a failure looks like correctness.

**Step 4: ask which steps actually gate**

A step gates when later steps genuinely cannot run without it. Checking the
changelog does not depend on page summaries. Checking for TODO markers does
not depend on either. All three are independent, and the sequence was an
accident of how they were written down.

```python
# A step gates when later steps genuinely cannot run without it.
GATES = set()

for i, fn in enumerate(STEPS, 1):
    try:
        results.append((i, fn.step_name, "ok", fn(root)))
    except Blocked as e:
        results.append((i, fn.step_name, "BLOCKED", str(e)))
        blocked.append(fn)
        if fn in GATES:
            break   # later steps depend on this one; stop here honestly
```

```
  blocked this run: 3
  blocked this run: 0
  runs needed: 2
```

**Two runs instead of four**, same defects, same fixes. The author saw all
three problems at once and fixed them in one pass.

And `GATES` is empty here, which is the finding. Three steps in a sequence,
and none of them actually gated anything.

**Step 5: when a gate is real**

Gates do exist. A workflow that creates a resource before configuring it
genuinely cannot continue past a failed creation, and pretending otherwise
produces a cascade of confusing secondary failures. The rule is that `GATES`
is an explicit, short, justified list, and everything not in it runs.

The default most people write is the opposite: everything gates, because
`break` on failure is the shortest code.

**What you built.** A workflow whose steps verify rather than ask, and an
explicit distinction between sequence and dependency that halved the round
trips.

## Reference

### The three forms NVIDIA names

| Form | Gives you | Tells you | Walks you |
|---|---|---|---|
| [Template](templates-scaffolding.md) | A correct artifact | No | No |
| Validator | No | Whether it is correct | No |
| Guided workflow | Sometimes | Yes, per step | Yes |

A guided workflow is usually built on the other two: its steps call the
validators, and some of them scaffold.

### Checklist against guided workflow

| | Checklist page | Guided workflow |
|---|---|---|
| Who determines done | The reader | The step |
| Record | Self-reported | Observed |
| Under deadline | Guessed | Unchanged |
| Cost to add an item | A line of prose | A function |
| Catches a regression | No | Yes |
| Teaches the standard | By being read | By blocking |

The bottom row is the sneaky benefit. A workflow that blocks with a specific
message is the most reliably read documentation you will ever write, because
the reader is stuck and motivated.

### What makes a step a good workflow step

| Property | Why |
|---|---|
| A name that reads as a checklist item | The output is a record people trust |
| A detail on success, not just a tick | "121 pages have a summary" beats "ok" |
| The specific thing to fix on failure | A finding you cannot act on is a chore |
| Deterministic | A flaky step destroys the whole workflow's credibility |
| Fast, or explicitly slow | A step that takes four minutes needs saying so |
| Independent unless genuinely gating | See steps 3 and 4 |

### Sequence against dependency

| Situation | Behaviour |
|---|---|
| Later steps read what this one creates | A real gate; stop |
| Later steps need this one's credentials or state | A real gate; stop |
| Steps check unrelated properties | Not a gate; run them all |
| Steps are ordered by convention | Not a gate; run them all |

The third and fourth rows are the common case and the one people get wrong.

### Where guided workflows pay

| Process | Workflow replaces |
|---|---|
| Release readiness | A checklist page |
| Writer onboarding | "Getting started for contributors" |
| New integration or service | A wiki page of steps |
| Incident response | A [playbook](playbooks.md), when the steps are mechanical |
| Content audit | A spreadsheet |

The incident row has a boundary worth respecting. When the steps are
mechanical, automate them; when the next step depends on judgment about
observations, that is a [playbook](playbooks.md), and forcing it into a linear
workflow loses the routing that made it valuable.

### What this is not

It is not a test suite, even though it calls the same checks. A test suite
answers "is the repository correct" for a machine; a guided workflow answers
"what do I do next" for a person, with names, details and a record. The same
function can serve both, and the presentation is the difference.

## How to talk about it

**Lead with the self-report problem.** "A checklist asks the reader to decide
whether an item is done, which means checking 121 pages or guessing, and under
deadline it is a guess. A guided workflow answers the question instead of
asking it, so the record means something. That is why NVIDIA says workflows
rather than static documents."

**The follow-up is sequencing, and it is the measurement worth bringing.** The
obvious implementation stops at the first failure, which looks like
correctness and cost me four runs for three defects. Separating sequence from
dependency, and finding that none of my three steps actually gated anything,
took it to two. Everything not in an explicit `GATES` list runs.

**The tradeoff to volunteer.** A guided workflow is a program with a user
interface, and that is a bigger commitment than a checklist page. It needs
maintaining, its failure messages are documentation that will go stale, and a
flaky step poisons trust in the whole thing. On a process run twice a year by
one person, the page is the right answer; it starts paying when the process is
frequent, or when the cost of a skipped step is high.

**One sharper point.** The failure messages are the most-read documentation you
will ever write. A reader hitting a blocked step is stuck and motivated, which
is a state no documentation page ever gets its audience into. Treat those
strings as prose, name the specific file, and say what to do, because that is
the sentence that actually teaches the standard.

## How to prove it

**The artifact.** A workflow command in a repository of yours, with named
steps, details on success, specific failures, and an explicit `GATES` list.

**Three things to do, in order:**

1. Run the golden path and count the runs in step 3 before reading step 4.
2. Take your most-used checklist and convert the two items most often
   self-reported as done. Those are the two that are least true.
3. Audit any multi-step script you own for the sequence-versus-dependency
   distinction. Most `break`-on-failure loops are not gating anything. Expect
   most of them to be gating nothing. In this guide's own release workflow
   exactly one step of seven genuinely gates the rest, and the other six were
   sequential by accident.

### The same measurement, on a real command

`fieldguide release-check` is this design built for this repository: seven
named steps, each returning a detail on success and a specific remedy on
failure, with an explicit `GATES` set in `src/fieldguide/release.py`.

```
  [1/7] ok       the registry parses
           106 concepts and 9 paths loaded from concepts.yaml
  [4/7] ok       every generated page is up to date
           13 generated pages match the registry
  [7/7] ok       every committed drill still prints what its page quotes
           26 page-and-drill contract(s) hold

all 7 steps passed; ready to release
```

`drills/release_rounds.py` runs the round-trip experiment against it, by the
method above: copy the repository, plant three independent defects (a
hand-edited generated page, an unclosed fence, unparseable front matter), then
fix exactly what each run reports and count the runs.

```
everything gates, which is what break-on-failure does:
  run 1: blocked 1 of 6
  run 2: blocked 1 of 6
  run 3: blocked 1 of 6
  run 4: blocked 0 of 6
  runs needed: 4

one real gate, which is what fieldguide release-check does:
  run 1: blocked 3 of 6
  run 2: blocked 0 of 6
  runs needed: 2
```

**Four against two, on the real command, for the same reason.** The toy
workflow above and a seven-step command over a hundred-page corpus produce the
same ratio, because the ratio is a property of the gating decision rather than
of the workflow's size.

One thing came out differently, and it is the more useful result. `GATES` is
not empty here. Exactly one step gates: every other step calls
`load_registry`, so a registry that will not parse turns the remaining six
into six secondary failures about a file none of them could read. Gates are
real. They are just far rarer than sequential code implies, and the honest
number for this workflow is one in seven rather than zero in three.

Writing that step also produced a small lesson in naming. The step is called
"the registry parses" and its first version caught the registry's own
validation error and not `yaml.YAMLError`, so the commonest way a registry
fails to parse walked straight past the step named after it. A test caught it.
A step's name is a claim about what it checks, and the two drift apart as
quietly as anything else on a page.

**What makes it credible rather than decorative.** The command exists, runs in
CI, and its steps check real properties of a real corpus; the
[demonstrated](../demonstrated.md) page records it. The distinction from
`fieldguide check` is the point: that is a validator, which reports everything
at once and says nothing about what to do next, and both are worth having for
different readers. What travels beyond this repository is the measurement, four
runs against two for the same three defects, and the finding that six of seven
steps in an apparently sequential process do not gate the next one.

## Related

- [Templates and scaffolding](templates-scaffolding.md), the step below this one
- [Documentation CI](documentation-ci.md), where the independence lesson first appears
- [Playbooks and decision guides](playbooks.md), the branching alternative
- [Release readiness](release-readiness.md), the checklist this most often replaces
