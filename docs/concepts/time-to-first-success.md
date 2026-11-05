---
title: Time to first success
summary: "The best metric in this field, and worth exactly as much as the path you instrumented: a cold-start test passed in nine seconds while a real reader never succeeded at all."
diataxis: explanation
audience: developer
concept: time-to-first-success
tags: [meas, core]
---

# Time to first success

`core` · difficulty 2 · 3h

!!! quote "Asked for by name"
    NVIDIA: "measure time-to-first-success, support deflection, repeat questions, and AI answer quality"

**Prerequisites:** [Documentation analytics](docs-analytics.md), [Golden paths](golden-paths.md)

## What it is

The elapsed time between a developer deciding to try something and that
developer having it work. Intel writes the same idea as a design goal, "from a
clean environment to a working result", and NVIDIA writes it as a metric. It is
the same quantity from two sides.

It is the best single number in developer documentation, because it is the only
one that cannot be satisfied by a well-written page. Prose quality, link
health, sample correctness and search ranking are all inputs to it, and none of
them substitutes for it.

Defining it requires two decisions, and both are where the metric usually goes
wrong: when the clock starts, and what counts as success.

## Why the job asks for it

Because every other documentation metric can be green while nobody can get
started.

A corpus can be complete, correct, linked, linted, searchable, fully tested,
and still leave a competent developer with nothing working after twenty
minutes. Time to first success is the metric that refuses to be fooled by that,
which is precisely why it is uncomfortable to adopt: it is the one number that
can make a quarter of good work look insufficient.

NVIDIA lists it first of four, ahead of deflection and answer quality, and that
ordering is defensible. Deflection measures the load you removed from someone
else. First success measures whether the thing works for the person in front of
you.

## The golden path

Measure it on a real repository, discover the measurement passed while a real
reader failed, and work out why. About thirty minutes, and the finding is the
most useful thing in this category.

**Step 1: instrument it properly**

A cold-start test is time to first success, automated. The companion repository
has one: it creates an empty directory, builds a fresh virtual environment,
installs the package the way a reader would, and runs the tutorial's commands
in order, asserting the output the tutorial promises.

```bash
bash scripts/coldstart.sh
```

```
==> Cold environment at /tmp/tmp.7SDBOfrJoQ
==> Tutorial step 1: create a virtual environment and install
==> Tutorial step 1: verify the CLI is on PATH
docpack --help works
==> Tutorial step 3: pack it
packed 2 pages into 4 chunks -> dist
output matches what the tutorial promises
==> Tutorial step 4: inspect the artifacts
dist/llms.txt present
dist/chunks.jsonl present
dist/llms-full.txt present
chunks.jsonl has the documented shape
==> COLD START PASSED: a reader following the tutorial reaches the documented result

EXIT=0  ELAPSED_S=9
```

**Nine seconds, exit zero.** A reader goes from an empty directory to three
artifacts whose shape is asserted. By any reasonable reading, time to first
success is nine seconds and the metric is excellent.

Time the steps individually, though, and the nine seconds turns out to be
almost entirely one step. A second run on a different machine, with each
`==>` banner timestamped:

```
  [+   0.0s  step  0.0s]  Cold environment at /tmp/tmp.XqTcyx6tJH
  [+   0.0s  step  0.0s]  Tutorial step 1: create a venv and install
  [+  11.6s  step 11.6s]  Tutorial step 1: verify the CLI is on PATH
  [+  11.7s  step  0.1s]  Tutorial step 2: create the documentation tree
  [+  11.7s  step  0.0s]  Tutorial step 3: pack it
  [+  11.8s  step  0.1s]  Tutorial step 4: inspect the artifacts
  [+  11.8s  step  0.0s]  Tutorial step 5: break it on purpose
  [+  12.6s  step  0.7s]  COLD START PASSED
TOTAL 12.7s
```

**Of 12.7 seconds, 11.6 are `pip install`: 91 per cent.** Everything the
tutorial actually teaches, creating a tree, packing it, inspecting the
artifacts and breaking it on purpose, takes 0.4 seconds in total.

Two things follow, and the second is the one worth keeping. The headline figure
is machine-dependent, nine seconds here and 12.7 there, so quoting it to two
significant figures is false precision; the composition is stable and the total
is not. And the only lever on this number is the dependency install, because
rewriting every word of the tutorial could not move four tenths of a second.
A metric whose single component you cannot influence by doing your own job well
is a metric about somebody else's work.

**Step 2: a real reader arrives**

The same day, the project's first real reader worked through the repository.
Every command he ran exited zero. He then reported that he had no idea what the
library did or what he should be looking at.

```
commands run:        9
commands failing:    0
first success:       never reached
```

Both measurements are correct. The cold-start test is not lying, and neither is
the reader.

**Step 3: find out why the instrument missed it**

The cold-start script runs **the tutorial's** command sequence. The reader
followed **the README's quick start**, which is a different sequence entirely:

```
quick start, in the order a reader meets it:
   1. docpack docs --check                   report
   2. python -m pytest -q                    report
   3. python scripts/check_links.py          report
   4. vale docs/                             report
   5. mkdocs build --strict                  artifact: site/
   6. docpack eval evals/golden.yaml         report
   7. bash scripts/coldstart.sh              report
   8. docpack new how-to --title ...         artifact: a page
   9. docpack docs --out dist                artifact: 3 files
  10. python mcp_server/server.py            artifact: a running server

commands that produce something: 4/10, at positions 5, 8, 9, 10
the first four, consecutively, produce nothing but reports
```

The command that makes the library's actual output is **ninth of ten**. The
first four are validators that print "ok". A reader working down that list in
order spends their entire first impression watching a corpus check itself.

So the repository had two front doors, instrumented one of them, and the metric
was silently absent on the other. Not wrong: absent. There was no number for
the README path at all, and nothing to notice.

**Step 4: instrument the other door**

The README's quick start cannot be executed end to end (one step needs a
separately installed prose linter), but the property that failed is checkable
without running anything:

```python
#: Commands that leave the reader holding something.
PRODUCES_SOMETHING = ("docpack docs --out", "docpack search",
                      "docpack new", "mcp_server/server.py")

first = [c for c in commands if not c.startswith("pip install")][0]
assert any(first.startswith(p) or p in first for p in PRODUCES_SOMETHING), (
    f"the first quick-start command after install is {first!r}, which only "
    "reports. Lead with a command that leaves the reader holding something."
)
```

Run against the README as the reader found it:

```
old README first command: 'docpack docs --check'
would the gate pass? False
```

And against the rewritten one, where the quick start is split into commands
that make something and commands that check something:

```
6 passed
```

A test that would have caught the failure before a human had to. Cheap, and it
exists only because somebody said something.

**Step 5: what the two numbers mean together**

```
instrumented path:    9 seconds
unmeasured path:      never
```

Time to first success is not a property of a product. It is a property of a
**route through** a product, and a product has as many of those as it has entry
points: the README, the tutorial, the package registry page, the `--help`
output, the first search result, whatever an assistant says when asked.

Reporting a single number means having chosen a route, usually the one you
wrote the test for, which is the route you understand best and therefore the
one least likely to fail.

**Step 6: the definitions that decide the number**

Two choices do most of the work, and defaults tend to flatter.

| Decision | Flattering default | Honest version |
|---|---|---|
| Clock starts | First command of the tutorial | Arrival at the front door |
| Success means | The command exits zero | The reader has a result they recognise |

The second row is this whole page. Nine of nine commands exited zero, and the
reader had no result he recognised, because exit codes are a property of
programs and recognition is a property of people.

**What you built.** An automated cold-start measurement at nine seconds, a
documented case of that measurement passing while a real reader never
succeeded, a diagnosis naming the uninstrumented entry point, and a test that
closes it.

## Reference

### Defining the two endpoints

| Clock starts at | Measures | Use when |
|---|---|---|
| Arrival at the docs | The whole funnel, including navigation | The honest default |
| First command of a quickstart | Quickstart quality alone | Comparing quickstarts |
| After install | The API's own learnability | Install is somebody else's problem |
| Account creation | Onboarding including provisioning | There is a signup |

| Success means | Strength | Weakness |
|---|---|---|
| A result the reader recognises | The real thing | Needs a judgment per task |
| An asserted output | Automatable | Can pass with no comprehension |
| Exit code zero | Trivial to measure | See step 2 |
| The reader says they are done | Honest | Needs a reader |
| A telemetry event | Scales | Instruments one surface only |

### How the metric fails

| Failure | What it looks like | Fix |
|---|---|---|
| One route instrumented | A good number and unhappy readers | Instrument every entry point |
| Success defined as exit zero | Green runs, confused people | Define success as a recognised result |
| Measured only on the author's machine | Passes forever | A clean environment per run |
| Measured once | Passes forever | In CI, on every change |
| Averaged across audiences | Nothing actionable | Segment, or pick one |
| Measured and not acted on | A dashboard | Cut steps before first success |

### Reducing it, in order of effect

| Change | Why it works |
|---|---|
| Delete a step before first success | The only reliable lever |
| Remove a choice before first success | A decision costs more than a command |
| Show expected output after each command | Removes "did that work?" |
| Lead with the command that produces something | See step 4 |
| Defer configuration until after first success | Most of it is not needed yet |
| Supply a working default | A placeholder the reader must replace is a step |
| Shorten the install | Usually the largest single block |

The first two are the whole list in practice. Prose improvements move this
number much less than people expect, which is unwelcome news for a writing
team and the reason the metric belongs next to the tooling.

### What it does not tell you

| Not measured | Needs |
|---|---|
| Whether they understood it | [Assessment](assessment.md) |
| Whether they came back | Retention |
| Whether the second task was easy | A second measurement |
| Whether they needed help | [Support deflection](support-deflection.md) |
| Why they gave up | A person, or a session recording |

A fast first success followed by a wall is a real pattern, and this metric
reports the good half of it.

## How to talk about it

**Lead with why it is the best metric and what it costs.** "It is the only
documentation number that cannot be satisfied by a well-written page. Prose
quality, link health, sample correctness and search ranking are all inputs; none
substitutes. Which is also why it is uncomfortable: it can make a quarter of
good work look insufficient."

**Then the story, because it is the strongest thing I have in measurement.** I
automated it as a cold-start test: empty directory, fresh environment, install
the way a reader would, run the tutorial's commands, assert the promised
output. Nine seconds, exit zero. The same day, the first real reader ran nine
commands, had every one exit zero, and told me he could not tell what the
library did. Both measurements were correct.

**The diagnosis is the part worth remembering.** The cold-start test ran the
tutorial's sequence; he followed the README's quick start, where the first four
commands are validators that print "ok" and the command producing the library's
actual output is ninth of ten. The repository had two front doors and I had
instrumented one, so on the other the metric was not wrong, it was absent. An
uninstrumented entry point is where this number silently does not exist, and
that is the general lesson: time to first success is a property of a route
through a product, not of the product, and a product has as many routes as
entry points.

**The fix, and the tradeoff.** I added a test that reads the README's quick
start and fails unless the first command after install produces something; it
fails on the old README and passes on the rewritten one. The tradeoff is that
this is a proxy. It checks the ordering of a list, not whether a human
recognises the result, and the only instrument that checks the second one is a
human. So the proxy goes in CI and the human channel stays open, because the
proxy exists only because a person spoke up first.

## How to prove it

**The artifact.** A cold-start script in CI that runs from an empty
environment and asserts a promised output, plus a check on whichever entry
point it does not cover.

**Three things to do, in order:**

1. Run your quickstart in a fresh container, timing it, and write the number
   down. Predict it first. The gap between your prediction and the measurement
   is the finding, not the measurement.
2. List your entry points: README, tutorial, registry page, `--help`, first
   search result. Mark which ones have ever been tested. One of five is the
   usual answer, and the untested four are where the metric is absent rather
   than bad.
3. Count how many commands a reader runs before anything they can look at
   appears. If the answer is more than one, reorder the list; it is the cheapest
   improvement available in this entire category.

**What makes it credible rather than decorative.** `scripts/coldstart.sh` is in
the companion repository, runs in CI, and passed in nine seconds with exit zero
on the run quoted above. The reader failure is equally real, reported by the
first person to follow the README, and the test added in step 4 is in
`tests/test_doc_samples.py` and verified to fail against the previous README.
What is missing is any measurement over more than one reader: n is one, so
nothing here supports a claim about distributions, medians or trends, and the
[demonstrated](../demonstrated.md) page records the cold-start half as
demonstrated and the reader-side half as not.

## Related

- [Documentation analytics](docs-analytics.md), where this metric sits among the others
- [Golden paths](golden-paths.md), the route being measured
- [Cold-start testing](coldstart-testing.md), the automated form of this measurement
- [Turning developer feedback into changes](developer-feedback-loops.md), the channel that caught what the metric missed
- [Cognitive load in technical content](cognitive-load.md), the mechanism behind a slow first success
- [Assessment and checks for understanding](assessment.md), the question this metric cannot answer
