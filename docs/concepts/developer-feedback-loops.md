---
title: Turning developer feedback into changes
summary: "Ten automated gates were green when the first real reader could not tell what the software did; the only signal that catches that arrives once, from a person."
diataxis: explanation
audience: developer
concept: developer-feedback-loops
tags: [meas, supporting]
---

# Turning developer feedback into changes

`supporting` · difficulty 2 · 3h

!!! quote "Asked for by name"
    Intel: "Ability to translate developer feedback into documentation, samples, and product improvements"

**Prerequisites:** [Documentation analytics](docs-analytics.md)

## What it is

The path from something a developer said to something that changed in the
repository. The interesting part is not collection, which every team does, but
the translation: a complaint is evidence about an experience, and turning it
into an edit means deciding what it is evidence *of*, which is usually not what
the complaint names.

Intel's bullet puts "documentation, samples, and product improvements" in one
sentence, which is the right scope. The same report frequently calls for all
three, and routing it only to the documentation queue is how feedback gets
answered without being used.

## Why the job asks for it

Because it is the only measurement in this category that no instrument
produces.

Everything else here, [deflection](support-deflection.md),
[repeat questions](repeat-questions.md),
[answer quality](ai-answer-quality.md) and
[time to first success](time-to-first-success.md), is a number computed from
artifacts. Each of them can be green while the thing is unusable, because each
measures a property somebody thought to measure. A reader saying "I ran all of
this and I do not know what it does" measures the property nobody thought of,
and there is no automated substitute.

The practical problem is that the signal is rare and perishable. The first
reader is only first once, and the confusion they report is the confusion
everyone after them will have and nobody else will mention, because by then the
project looks like something they are supposed to already understand.

## The golden path

Two real feedback events, traced from report to shipped change, with what each
cost and what no gate could have caught. About twenty minutes of reading and
nothing to install.

**Step 1: the report**

The companion repository had been built, tested and packaged. Its first reader
worked through the README's quick start on his own machine, then said:

> I ran all the commands and I have no idea what the result is or what I should
> be looking at. The readme didn't clarify this for me.

Nine commands, all exit zero, no errors.

**Step 2: what the gates said at that moment**

```
Content model                       pass
Links and anchors                   pass
Unit tests and doctests             pass
Code samples in the docs            pass
Retrieval quality above the floor   pass
Generated pages pass validation     pass
Prose linting                       pass
Site builds with no warnings        pass
Per-page SEO is rendered            pass
Cold-start the quickstart           pass
```

**Ten gates, ten passes, and the artifact was incomprehensible to its reader.**

The cold-start gate is the painful one, because it exists precisely to catch "a
quickstart that does not work for a stranger". It runs the *tutorial's*
commands. The reader had followed the *README's* quick start, a different
sequence. The repository had two front doors and one of them was instrumented.

**Step 3: diagnose what the complaint is evidence of**

The report names the README. The README was a symptom. Counting what the quick
start actually offered:

```
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

commands producing something: 4 of 10, the first at position 5
the first four, consecutively, produce nothing but reports
```

The command that makes the library's actual output was ninth. The first
impression of a tool whose purpose is packaging documentation was four
consecutive validators printing "ok".

One thing was missing altogether: the library's whole point is retrieval, and
there was no way to perform a retrieval by hand. `eval` scores a fixed set of
twenty questions, which answers "is retrieval working" rather than "what does
this do".

**Step 4: the three changes, which belong to three different queues**

| Change | Kind | Why this report produced it |
|---|---|---|
| `docpack search` | Product | The capability existed and was unreachable |
| README reordered, making before checking | Documentation | The ordering was the reported symptom |
| Three tests on the new command | Tests | So it cannot silently rot |

Intel's bullet asks for exactly that split, and the product change is the one
that gets missed by treating a README complaint as a README task.

```
report at 11:56, change delivered at 12:01
elapsed: about five minutes
```

The latency is not a boast about speed. The point is the ratio: the diagnosis
took longer than every edit combined, which is normal and is why feedback
handling is a judgment skill rather than a throughput problem.

**Step 5: the second loop, which started from a number**

A different shape, worth contrasting. The retrieval evaluation reported two
cases whose top chunk lacked the terms an answer needs. That is a measurement
rather than a complaint, and it named its own cause: the reader's everyday word
was absent from the page documenting the thing.

```
             before   after
hit@1          60%     65%
MRR          0.742   0.775
routing        70%     75%
grounded@1     80%     90%
grounded@3     90%    100%
```

Two sentences, four of five scores moved, no code at all.

**Step 6: what the two loops say together**

```
loop 1   a person, once        found: nothing was measurable
loop 2   an instrument, daily  found: two words
```

The instrument found a precise, small, actionable defect and would never have
found the first one, because "the artifact does not explain itself" is not a
property anybody encodes as a check. The person found the structural failure and
would never have found the second, because no reader computes vocabulary overlap
across twenty questions.

Neither substitutes for the other, and the asymmetry is in supply. Instruments
run on every commit. The first reader happens once.

**What you built.** Two feedback loops traced to shipped changes, a gate audit
showing ten passes against one unusable artifact, and one report split into a
product change, a documentation change and a test.

## Reference

### What each signal can and cannot see

| Signal | Catches | Blind to | Supply |
|---|---|---|---|
| CI gates | Breakage, drift, regressions | Whether any of it makes sense | Every commit |
| Cold-start test | A quickstart that fails for a stranger | The quickstart you did not instrument | Every commit |
| Retrieval evaluation | Unfindable answers, vocabulary gaps | Whether the corpus is worth finding | Every commit |
| Search logs | The words readers use | Why they wanted them | Continuous, with an audience |
| Support tickets | Problems bad enough to report | Everything people gave up on | Continuous, with an audience |
| A person reading it cold | Structural incomprehension | Anything needing aggregation | Once per person |

The bottom row is the only one that catches the top row's blind spot, and the
only one you cannot schedule.

### Translating a report into the right queue

| The reader says | Often means | Goes to |
|---|---|---|
| "The docs are confusing" | The product has no obvious entry point | Product |
| "I don't know what this does" | The artifact is validated but never shown | Docs, and usually product |
| "This didn't work" | An undeclared prerequisite | Docs, then a cold-start test |
| "Where is X?" | X exists and is unfindable | Ranking or vocabulary |
| "Can it do X?" | It can, and nothing says so | Docs |
| "I expected Y" | A real design disagreement | Product, with a decision record |

Taking any of these at face value produces a documentation edit that does not
help, which is the most common way feedback is formally honoured and
practically wasted.

### Why the first reader is worth protecting

| Property | Consequence |
|---|---|
| They have no context | They see what the artifact actually communicates |
| They will not be first twice | The signal is single-use |
| They assume the confusion is their fault | Most of it is never reported |
| They stop at the first wall | You learn where the wall is, not what is behind it |
| They are usually polite about it | The report understates the problem |

The fourth row is the reason to ask what they expected rather than only what
happened. The fifth is the reason to treat a mild report as a severe finding.

### Closing the loop visibly

| Practice | Effect |
|---|---|
| Name the report in the commit or the comment | The reporter sees that it landed |
| Record it in the source, not the ticket | It survives the ticket system |
| Add the check that would have caught it | The class closes, not the instance |
| Say which queue it went to | Product changes get credited as product |
| Say what you did not change, and why | Preserves trust for the next report |

The third row is the one that compounds. One report produced a new command and
a reordered README; the lasting change is a check asserting that the first
quick-start command after install produces something rather than reporting
something.

## How to talk about it

**Lead with the gate audit, because it is the strongest thing here.** "The first
real reader of my repository ran nine commands, all exited zero, and reported
that he had no idea what the software did. Ten CI gates were green at that
moment, including a cold-start test that exists specifically to catch a
quickstart failing for a stranger. It tested the tutorial's command sequence and
he had followed the README's, so the repository had two front doors and I had
instrumented one."

**Then the diagnosis, which is the actual skill.** The report named the README
and the README was a symptom. The first four commands produced nothing but
reports, the command that makes the library's output was ninth of ten, and the
library's whole purpose, retrieval, could not be performed by hand at all. One
report became three changes in three queues: a new command, a reordered README,
and tests. Treating it as a README task would have missed the product change,
which was the real finding.

**Contrast it with the measured loop.** The same day, the retrieval evaluation
found two cases where the reader's word was missing from the page documenting
the thing, and two sentences moved four of five scores. That is a precise, small
defect an instrument finds daily and a person never would, against a structural
failure a person finds and an instrument never will. The difference is supply:
instruments run on every commit, the first reader happens once.

**The tradeoff to volunteer.** Acting on a single report risks building for one
person, and one report cannot tell you whether the confusion generalises. What
made this one safe to act on is that the fix was additive and the diagnosis was
checkable without him: the command ordering and the absent capability are facts
about the repository rather than opinions about his experience. When a report
cannot be grounded in something checkable, the right move is to collect a second
one before building.

**One sharper point.** Mild reports understate. "The readme didn't clarify this
for me" is a polite sentence describing a total failure of an artifact to
communicate its purpose, and the politeness is load-bearing: most readers who
hit that wall conclude they are missing something obvious and say nothing. The
right prior on a gently worded confusion report is that it is severe and
under-reported.

## How to prove it

**The artifact.** A repository where a reader's report is traceable to a commit,
and a check that closes the class rather than the instance.

**Three things to do, in order:**

1. Find the last piece of feedback your team received and ask which queue it
   went to and which queue it should have gone to. If the answer is the same
   queue every time, reports are being filed rather than diagnosed.
2. Count the commands in your own quick start that produce something against
   the ones that only report, and note the position of the first producing one.
   Write both predictions down first.
3. Ask one person who has never seen your project to run its quick start while
   you watch and say nothing. It is the highest-value hour available in this job
   and it works exactly once per person, so spend it on the project you care
   about most.

**What makes it credible rather than decorative.** Both loops are in the
repositories: `docpack search` exists with three tests, the README is reordered
into commands that make something and commands that check something with a line
saying why, the vocabulary edits are in two how-to pages, and the score movement
is recorded in `docs/explanation/evaluating-retrieval.md`. What cannot be
claimed is a process. This is two events, one of them from a single reader, with
no recurring intake, no triage policy and no second data point, and the
[demonstrated](../demonstrated.md) page records developer feedback loops as
having instances rather than a demonstrated practice.

## Related

- [Documentation analytics](docs-analytics.md), the instrumented half of the same question
- [Time to first success](time-to-first-success.md), the metric that was green during loop 1
- [Repeat questions](repeat-questions.md), where loop 2's vocabulary fix is developed
- [Cold-start testing](coldstart-testing.md), the gate that tested the other front door
- [Developer advocacy](developer-advocacy.md), the queue a product-shaped report belongs in
