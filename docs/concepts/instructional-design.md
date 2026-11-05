---
title: Instructional design for developers
summary: "The structural commitments that make a page teach rather than inform, and why auditing your own corpus for them is harder than writing them."
diataxis: explanation
audience: developer
concept: instructional-design
tags: [edu, core]
---

# Instructional design for developers

`core` · difficulty 2 · 5h

!!! quote "Asked for by name"
    Intel: "Design and maintain golden paths and curriculum that take a developer from a clean environment to a working result"

**Leads to:** [Learning paths and curriculum](learning-paths.md), [Cognitive load in technical content](cognitive-load.md), [Assessment and checks for understanding](assessment.md)

## What it is

The practice of designing content so that a reader can *do* something
afterwards, rather than having read about it. For developer documentation that
reduces to a small number of structural commitments: say what the reader will
be able to do, say what they need first, give them something to practise on,
and give them a way to know it worked.

The reason this is not obvious is that documentation and instruction are
different jobs sharing one medium. A reference page is finished when it is
accurate. A tutorial is finished when a stranger reaches a working result,
which is a claim about the *reader* rather than about the page.

## Why the job asks for it

Intel's bullet is the concept in one line: "from a clean environment to a
working result". That is an instructional objective written in behavioural
terms, with its starting state named. The posting is describing design, not
writing.

It matters on an ordinary Tuesday because most developer documentation is
written by people who already know the thing, and expertise is the enemy of
instruction. An expert cannot see which of their steps are inferential leaps,
having stopped making those leaps years ago. Structural commitments are the
defence: if every page must declare its prerequisites, the author is forced to
notice what they were assuming.

## The golden path

Audit a corpus for four structural commitments, and find out what auditing
your own writing actually costs. About thirty-five minutes.

**Step 1: four commitments, chosen because a script can check them**

| Commitment | In this corpus | Checkable as |
|---|---|---|
| Objective | What the exercise produces | A stated result at its end |
| Entry state | What the reader must already know | A prerequisites line |
| Practice | Something to do, not to read | The golden path itself |
| Verification | How the reader knows it worked | A "how to prove it" section |

These are not the only possible commitments. They are four that a program can
verify, which is what makes them worth adopting over good intentions.

**Step 2: audit the corpus**

```python
for c in [x for x in reg.concepts if x.status == "complete"]:
    t = (docs / c.page).read_text()
    if c.prerequisites and "**Prerequisites:**" in t:   has["prereq"] += 1
    if DURATION.search(t):                              has["dur"] += 1
    if re.search(r"\*\*What you (?:built|learned)", t):  has["result"] += 1
    if "## How to prove it" in t:                       has["proof"] += 1
```

```
complete pages: 82

  prereq stated      55/73   (75%)
  duration stated    75/82   (91%)
  closing result     78/82   (95%)
  proof section      82/82   (100%)
```

(The audit below ran when the corpus was 82 pages. On the finished 106 the
same four commitments stand at 89/89, 106/106, 106/106 and 106/106.)

Two of those four numbers are wrong, and working out which is the real lesson
of this page.

**Step 3: the prerequisite number was counting labels, not commitments**

```
prerequisite markers in use:
  **Prerequisites:**   46
  **Read first:**      28
concepts with no prerequisites at all: 9
```

Coverage was already complete. The corpus was using **two labels for one
structural element**: hand-written pages said "Prerequisites", pages that began
in the scaffold said "Read first", because that is the string the scaffold
emitted.

A real defect, just not the one the number suggested. A reader meeting both
labels does not infer two conventions, they experience inconsistency, and the
entry-state commitment stops being recognisable as a commitment at all. Fixed
by standardising on one label, changing the scaffold, and asserting it in a
test so it cannot drift back.

```
labels in use after the pass: {'Prerequisites:': 74}
prereq coverage: 73/73
```

On the finished corpus: 90 occurrences, 89 of 89 concepts that have
prerequisites. One page states the label twice, which is a cosmetic
inconsistency the check does not care about and a reader would not notice.

**What this fix got wrong**, which took a while to see. It standardised the
label that had surfaced and asserted that one label in a test, and that is
exactly as far as it went. Three more elements were carrying two wordings each
at the time, in other sections, and the test written here could not have seen
any of them, because it was a test about prerequisites rather than about
labels.

The [assessment](assessment.md) page found the second pair independently,
months later, by measuring something else entirely. All four are standardised
now, against `STRUCTURAL_LABELS` in `registry.py` rather than against a string
written into a test. **A fix applied to the instance is not applied to the
class**, and the way to tell the difference is whether the check you add
afterwards could find a defect you had not already found.

**Step 4: the duration number was the line-wrapping bug**

Seven pages appeared to state no duration. All seven state one:

```
docs/concepts/content-lifecycle.md:  "... falsifiable. About thirty
                                      minutes. This uses this guide's own ..."
```

The number and its unit were separated by a line break, and the pattern's
`[- ]?` does not match a newline. Normalising whitespace before searching:

```
duration stated: 82/82
```

This is the third time in this project that measuring wrapped prose per line
has produced a confident wrong answer, which is worth more than the result.

**Step 5: count the real failures, then fix them**

With both measurements corrected, exactly one commitment was genuinely
incomplete:

```
golden paths with no stated result: 4/82
   diataxis, antora, github-actions, mcp
```

Four exercises that ended without telling the reader what they now had.
Writing those four closings took ten minutes, and each one forced the useful
question: what *did* this exercise produce? On `diataxis` the answer came out
sharper than the page's own introduction.

```
golden paths with no stated result: 0/82
```

**Step 6: the finding worth carrying out of here**

Count the attempts. Across this corpus, eight successive audits of my own
writing returned plausible wrong numbers:

| Attempt | Wrong because |
|---|---|
| Golden path structure | Split sections on `## `, which golden paths write inside heredocs |
| Duration, first try | Matched only "About N minutes" |
| Duration, second try | Matched per line, and prose wraps |
| Duration, third try | Word list omitted the hyphenated numbers |
| Sentence length | Front matter counted as prose |
| Sentence length, again | `."` not treated as a sentence ending |
| Sentence length, third | A naive fence toggle counted shell commands as prose |
| Prerequisites | Two labels for one element |

Every one produced a number a reasonable person would have published. Five of
the eight would have gone into this guide as findings.

The instructional-design point is not "be careful". It is that **the audit is
an artifact with the same defect profile as the corpus it measures**, and it
needs the same treatment: a fixture with a known answer before you believe any
number it gives you about something you care about.

**What you built.** Four structural commitments, measured honestly, four pages
repaired, one label standardised, and a calibrated distrust of your own first
number.

## Reference

### Objectives in behavioural terms

| Weak | Behavioural |
|---|---|
| "Understand authentication" | "Obtain a token and make an authenticated call" |
| "Learn about retries" | "Configure a retry policy and observe a backoff" |
| "Get familiar with the CLI" | "Install the CLI and list your widgets" |
| "Know the architecture" | "Trace one request through all three services" |

The test is whether you could watch someone and tell whether they had done it.
"Understand" fails that test, which is why Intel's "to a working result" is
better written than most objectives in actual curricula.

### Where expertise hurts

| Expert behaviour | Consequence for the reader |
|---|---|
| Omitting a step that is automatic for them | A silent prerequisite |
| Using the internal name for a thing | Unfindable and unsearchable |
| Explaining why before what | The reader has nothing to attach it to |
| Choosing the elegant path over the common one | Correct and not useful |
| Assuming the goal is obvious | The reader does not know what they are building |

[Cold-start testing](coldstart-testing.md) is the mechanical defence against
the first row. The others need a human reader, which is why
[assessment](assessment.md) is a separate concept.

### What instructional design is not

| Not | Because |
|---|---|
| Making content friendlier | Tone is not structure |
| Adding more explanation | Usually raises [load](cognitive-load.md) |
| A learning management system | That is delivery |
| Quizzes | One kind of [assessment](assessment.md), often the weakest |
| Writing for beginners | It applies at every level of expertise |

### The commitments, and what each one costs

| Commitment | Costs | Buys |
|---|---|---|
| Every page states its entry state | One line, and a real decision | Silent prerequisites become visible |
| Every exercise states its duration | One phrase | Readers can decide whether to start |
| Every exercise names its result | Two sentences | The author must know what it produced |
| Every page says how to verify | A section | Separates informing from teaching |
| One label per element | A standardisation pass, once | The commitments stay recognisable |

The last row is the one this page learned the hard way, and the one most
corpora get wrong without noticing, because each author is individually
consistent.

## How to talk about it

**Lead with the difference between the two jobs.** "A reference page is done
when it is accurate. A tutorial is done when a stranger finishes with a working
result, which is a claim about the reader rather than the page. So I hold pages
to structural commitments: declare the entry state, state the duration, name
the result, say how to verify. Four things a script can check, which is why I
chose those four."

**The follow-up is usually about expertise.** The honest answer is that authors
cannot see their own inferential leaps, so this needs mechanisms rather than
care. Cold-start testing catches undeclared prerequisites; a required
prerequisites line forces the author to decide what they are assuming; the rest
needs a real reader, which is the limit of what tooling buys you.

**The tradeoff to volunteer.** Structural commitments are a tax on every page
and they can decay into ritual. A prerequisites line reading "none" on forty
pages is noise, and a "what you built" paragraph written to satisfy a checker
is worse than none at all. They work while they force a decision and fail once
they become a form to fill in, and the only way to tell which has happened is
to read what they produced.

**One sharper point.** Auditing your own corpus
is harder than it looks, and the failure is silent. Eight successive measurements of mine returned confident wrong numbers. Front
matter counted as prose. A duration pattern defeated by line wrapping. A fence
parser that counted shell commands as sentences. And two labels for one
structural element, which looked like a quarter of the corpus failing a
commitment it had already met. Five would have been published as findings. An audit script has the same
defect profile as the corpus it measures, so it gets a fixture with a known
answer before any of its numbers are believed.

## How to prove it

**The artifact.** A corpus whose structural commitments are checked in CI,
plus the audit and the fixtures that make the audit trustworthy.

**Three things to do, in order:**

1. Pick one commitment, audit a corpus you own for it, then verify the
   measurement by hand against three pages. The hand-check is the step people
   skip and the only one that catches a wrong number.
2. Rewrite your three weakest learning objectives in behavioural terms. "Could
   I watch someone and tell?" is the entire test. The test is falsifiable or
   the objective is not rewritten: if you cannot name the observation that
   would show a reader had failed, the words changed and the objective did
   not.
3. Find an exercise that never says what it produced, and write that sentence.
   It is the fastest way to discover an exercise that produces nothing.

**What makes it credible rather than decorative.** `fieldguide audit` prints
the four commitments on demand, which is the whole of the claim: a
seven-section page contract enforced in CI, a prerequisite graph with no
cycles, 89 of 89 prerequisite lines, and 106 of 106 golden paths stating a
duration and naming a result. Every figure in this page's golden path comes
from that command rather than from a transcript, and its test fixtures pin the
three measurement bugs described above so they cannot come back.

What that does **not** establish is the thing the concept is actually about.
The commitments are met; whether meeting them teaches anybody is a claim about
readers, and there are none. The [demonstrated](../demonstrated.md) page
records this as `partial` for that reason.

## Related

- [Learning paths and curriculum](learning-paths.md), sequencing across pages
- [Cognitive load in technical content](cognitive-load.md), the mechanism behind first success
- [Assessment and checks for understanding](assessment.md), how you find out it worked
- [Tutorial design](tutorial-design.md), the page-level craft
- [Cold-start testing](coldstart-testing.md), the mechanical half of the entry-state commitment
