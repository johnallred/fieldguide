---
title: Assessment and checks for understanding
summary: "A task without a success criterion is practice, not assessment, and a corpus can be excellent at the first while doing almost none of the second."
diataxis: explanation
audience: developer
concept: assessment
tags: [edu, supporting]
---

# Assessment and checks for understanding

`supporting` · difficulty 2 · 3h

!!! quote "Adjacent, not quoted"
    Not named in either posting. The counterpart to cold-start testing: how you find out the curriculum worked.

**Prerequisites:** [Instructional design for developers](instructional-design.md)

## What it is

Any mechanism that tells you whether a reader can now do the thing. The useful
distinction is between a **practice task**, which gives the reader something to
do, and an **assessment**, which also states what counts as having done it.
Almost everything published as assessment in developer documentation is
practice with a quiz attached.

[Cold-start testing](coldstart-testing.md) is the mirror image. It runs the
documentation in a clean environment and tells you whether the *content* works.
Assessment tells you whether the *reader* does. A corpus can pass the first
perfectly and hold no evidence at all about the second, which is the normal
state and worth saying out loud rather than disguising.

## Why the job asks for it

Because every claim a documentation team makes about outcomes is an assessment
claim wearing other clothes.

"A developer reaches a working result in fifteen minutes" is a measurement of
readers. So is "our quickstart reduced support tickets". So is every sentence
in a performance review about improving onboarding. If nothing in the system
observes a reader succeeding or failing, those claims rest on page views and on
the absence of complaints, which is the weakest evidence available and the most
commonly cited.

The practical reason is sharper. Without assessment you cannot distinguish
content that is clear from content that is merely agreeable to read, and those
two fail in opposite directions: the agreeable page collects good feedback and
produces nobody who can do the task.

## The golden path

Assess a corpus's own assessment. This guide ends every page with three things
to do, so there are 318 of them to examine. About thirty minutes, and the
measurement is wrong twice before it is right.

**Step 1: find the instrument**

```python
proof = text.partition("## How to prove it")[2].partition("## Related")[0]
tail  = proof[LABEL.search(proof).end():].partition("**What makes it")[0]
items = [" ".join(m.group(1).split()) for m in ITEM.finditer(tail)]
```

```
pages with a proof section:   47/82
```

Forty-seven, when the page contract makes that section mandatory and a separate
check had already reported 82 of 82. One of the two is wrong.

(Steps 1 to 3 were run when the corpus was 82 pages, and are kept because they
are what exposed the defect. Step 4 onward is the finished 106-page corpus.)

**Step 2: it is two labels again**

```
**Three things to do today:**            46
**Three things to do, in order:**        35
**Three things to do today, in order:**   1
```

On the finished corpus the split was 70, 35 and 1. The inconsistency outlived
the discovery by some months, because standardising the label meant touching
every page and the defect was recorded rather than fixed.

**It is fixed now, and fixing it found three more.** The lesson below says to
sweep every structural element at once, and acting on that rather than on the
one label that surfaced turned up:

| Element | Wordings in use |
|---|---|
| Proof-task label | "today:" on 70, ", in order:" on 35, a splice of the two on 1 |
| Sharper point | "One sharper point." on 47, "A sharper point." on 35 |
| Credibility | "...rather than decorative." on 72, "What makes it credible." on 34 |

Two of the three were decided on accuracy rather than on majority, which is
worth saying because the majority was the easier answer both times. The tasks
genuinely are ordered, with the first always being to run the golden path,
while "today" promises a scope that "compute grounded@k on a corpus you own"
does not have, so the minority wording won. And "rather than decorative" is
the section's whole argument, so the longer form won.

Then a **fourth** variant appeared, which is the part worth remembering: after
the sweep above pronounced the corpus clean, the label
"One sharper point, and the best thing to say here." turned out to be on five
more pages. The hand sweep had filtered to labels used ten or more times, so a
five-page variant was below the threshold that was supposed to find variants.
**A frequency floor is a filter on what you are willing to find.**

So the fix was not the standardisation. It is `STRUCTURAL_LABELS` in
`registry.py`, which declares the wording of every labelled element, and the
part of `fieldguide audit` that reports every repeated bolded opener *not* in
that list. Counting declared labels confirms what you already know; counting
the undeclared ones is what finds the next one.

The section was present on all 82 pages. The parser was looking for one of
three labels, and the corpus had split 47 to 35 on wording, almost exactly
along the line between two sittings of writing.

This is the second independent discovery of the same defect in this corpus.
The [prerequisite label](instructional-design.md) audit found "Prerequisites"
against "Read first" and fixed it; this one was sitting underneath, in a
different section, undetected, because the fix had been applied to the label
that surfaced rather than to the class of defect. **A corpus written by one
author across several sittings contains several of these**, and the lesson is
to sweep every structural element for variants at once.

**Step 3: classify the 246 tasks, and get it wrong**

```
tasks: 246 across 82 pages, exactly 3 each
begin with an imperative action: 133/246 (54%)
```

Fifty-four per cent would be a real finding, if true. The unmatched items:

```
[('**Run', 30), ('**Write', 11), ('**Add', 8), ('**Find', 8), ('**Generate', 7), ...]
```

They begin with `**`. The same 35 pages bold the opening of each task, so the
classifier was measuring Markdown emphasis rather than verbs. Strip the markup
and the inline links:

```
begin with an imperative action: 232/246 (94%)
unmatched: If 3, On 2, For 1, When 1, Redo 1, Use 1, Publish 1, Track 1
```

Four of the fourteen remaining, `Redo`, `Use`, `Publish` and `Track`, are
imperatives the verb list omitted, which is the word-list bug from the duration
audit in miniature. The real figure is about 96 per cent, and the honest
summary is that the corpus is good at telling a reader what to do.

**Step 4: the number that matters**

Two further properties, both about whether a task is assessable at all. The
measurement as it originally stood:

```
tasks: 318 across 106 pages, exactly 3 each
tasks beginning with an imperative:            303/318 (95%)
tasks naming an inspectable artifact:          203/318 (64%)
tasks stating how the learner knows it worked:  53/318 (17%)
```

**Seventeen per cent**, and that number was wrong. It stood on this page for
months as the guide's weakest figure, and it was the classifier that was weak.

The keyword list behind it included `against`. Sixteen of its 53 matches were
the preposition in "run it against a corpus you own", which states no criterion
at all. Meanwhile it recognised none of the forms the corpus actually uses. Not the
conditionals, "if the answer is two, you have the drift". Not the predicted
values, "on a client-rendered site the number is near zero". Not the
comparisons to the author's own result, "mine said 72 tests and there were
119". It was wrong in both directions at once, and the net error ran against
the guide rather than for it.

Sixty tasks hand-labelled against a written definition, in two samples with one
held out, put the real rate at **about forty per cent** of a sample where the
old classifier saw seventeen. The rewritten classifier, scored against those
labels, reports a third of the corpus.

```
tasks: 318 across 106 pages, exactly 3 each
tasks beginning with an imperative:            303/318 (95%)
tasks naming an inspectable artifact:          204/318 (64%)
tasks stating how the learner knows it worked: 128/318 (40%)
```

That last figure is 40 per cent after a pass that added one clause to the
best-suited task on every `core` page that had none, which was 22 of them. The
pass moved the measured rate from 33 to 40; the correction moved it from 17 to
33. **The instrument was worth more than the work**, which is not the lesson
anybody sets out to demonstrate on a page about assessment.

Two of the clauses written during that pass were invisible to the classifier
the moment they were written: "you will know the gate is wired when..." and
"more than roughly one suppression per ten pages means...". Both are criteria,
both are now patterns, and both arrived as misses. A classifier for a quantity
this open-ended is permanently incomplete, which is the argument for scoring it
against labels rather than trusting it.

The labelled set is frozen at `tests/fixtures/criterion_labels.json` with its
definition and method beside it, and `tests/test_criterion.py` scores the
classifier against it on every run. Recall against the labels must be perfect
and precision is allowed to be imperfect, because a missed criterion
understates the corpus and hides work already done, which is exactly how the
seventeen happened.

Take a real one:

> Measure the per-page maximum sentence length on your docs, then read the
> three worst sentences out loud.

A good practice task, and not an assessment, because nothing in it
distinguishes a reader who understood from one who ran a script. Compare one
that does:

> Run the golden path and count the runs in step 3 before reading step 4.

Here there is a number, the reader produces it before being told it, and a
wrong answer is visible to the reader themselves. That is the entire
difference, and it costs one clause.

**Step 5: what a seventeen per cent calls for**

Not quizzes. A quiz over this corpus would test recall of its wording, which is
the thing nobody needs.

The cheap fix is to give the highest-value tasks a **predict-then-check** shape,
which is what the good example does. The reader commits to an expected answer
before running the thing, so feedback is immediate, self-administered and
honest; and the writer has to know the right answer, which is its own quality
check on the task.

The expensive fix is real learners, for which no amount of corpus analysis
substitutes. That limit belongs in the claim: this guide can say its tasks are
well formed and cannot say they teach, and the distance between those two
sentences is the distance between construct and criterion validity.

**What you built.** An assessment of 318 practice tasks, a second instance of
the two-label defect, a classifier corrected twice, and one number worth acting
on.

## Reference

### Practice against assessment

| | Practice task | Assessment |
|---|---|---|
| Says what to do | Yes | Yes |
| Says what counts as done | No | Yes |
| Who judges | Nobody | The criterion, or a reader |
| Tells the writer anything | No | Yes |
| In this corpus | 318 | 128 |

The bottom row is this page in one line. The gap is cheap to close on the tasks
that matter and not worth closing on all of them.

### Forms, ranked by what they actually measure

| Form | Measures | Costs | Fails by |
|---|---|---|---|
| Predict, then check | Understanding of mechanism | One clause | Needs a crisp expected answer |
| Produce an artifact | Ability | A task design | Nobody inspects it |
| A task with an automated check | Ability, at scale | A test harness | Teaching to the harness |
| Cold-start run | The content, not the reader | A clean machine | Says nothing about people |
| Watching one person | Everything, slowly | An hour | Does not scale, is still the best |
| Multiple choice | Recall of wording | Little | Passed without ability |
| "Was this page helpful?" | Mood | Nothing | Measures agreeableness |

The last row is the most-deployed instrument in documentation and the least
informative, which is not a coincidence: it is the only one that costs nothing
and never produces bad news.

### Predict-then-check, as a pattern

| Weak | With a criterion |
|---|---|
| "Run the link checker" | "Predict how many links break, then run it" |
| "Measure sentence length" | "Guess your longest sentence, then measure" |
| "Try the sample" | "Say what it will print, then run it" |
| "Audit your gallery" | "Name the sample you think is broken, then check" |

In every row the writer has to know the answer, which quietly removes tasks
that sound instructive and have no determinate result.

### Validity, in the two senses that matter

| Question | Name | This guide's evidence |
|---|---|---|
| Is the instrument well formed? | Construct | 318 tasks, 95% imperative, 64% producing an artifact |
| Does it predict real ability? | Criterion | None |

Reporting the first while implying the second is the usual overreach in
education claims, and stating both rows avoids it.

### When not to assess

| Situation | Instead |
|---|---|
| Reference pages | Nobody "learns" a parameter table |
| One-off migration guides | Cold-start test the instructions |
| Content with four readers | Ask all four |
| A number is wanted for a slide | Say what you actually have |

## How to talk about it

**Lead with the pairing.** "Cold-start testing tells me whether the content
works; assessment tells me whether the reader does. Most documentation has the
first and treats page views and the absence of complaints as the second, which
is the weakest evidence available and the most commonly cited."

**The follow-up is what you measured.** My corpus ends every page with three
things to do, 318 tasks in all, and 95 per cent begin with an imperative while
40 per cent state how the reader would know it worked. More practice than
assessment, and the forty is after a deliberate pass. The honest part of that
story is that the first measurement said seventeen and was wrong: the
classifier matched the word "against" and missed every conditional, so the
instrument was worth more than the writing it prompted. The fix on the tasks
themselves is predict-then-check, because it costs one clause and forces the
writer to know the right answer, which removes the tasks that sound
instructive and have no determinate
result.

**Volunteer the limit before being asked.** Corpus analysis establishes that an
instrument is well formed. It says nothing about whether anybody learns, which
needs real readers. Those are construct and criterion validity, and reporting
the first while implying the second is the standard overreach in this area. I
would rather say I have one and not the other.

**One sharper point.** My own measurement was wrong twice inside ten minutes:
it found 47 of 82 proof sections because the corpus used three labels for one
element, and it put the imperative rate at 54 per cent because it was matching
Markdown emphasis rather than verbs. Both produced numbers I would have
published. The label one matters more, because it was the second independent
discovery of that defect here: the earlier fix had been applied to the label
that surfaced instead of to the class, so the right move is to sweep every
structural element for variants in one pass.

## How to prove it

**The artifact.** A classification of your own practice tasks by whether they
state a success criterion, and one task rewritten into predict-then-check.

**Three things to do, in order:**

1. Guess what fraction of your exercises say what the result should look like,
   write the number down, then measure it. The guess is the point, and the gap
   between the two is this page's whole subject.
2. Take your most important exercise and add a prediction step before the
   command. If you cannot state the expected answer, that exercise has no
   determinate result, which is more useful to learn than any percentage.
3. Sit with one person while they follow your quickstart and say nothing for
   ten minutes. It does not scale, it is still the best instrument available,
   and it will contradict at least one thing you believe.

**What makes it credible rather than decorative.** The measurement above runs
against this guide's own 106 pages and is reproducible from the repository;
what it establishes is that 318 tasks are well formed and that 128 of them are
assessable, against a classifier scored on sixty hand-labelled tasks rather
than trusted. What it cannot establish is that any of them teach
anybody anything, because no reader has been observed, and the
[demonstrated](../demonstrated.md) page records assessment as having no
demonstration in either repository rather than claiming this analysis as one.

## Related

- [Cold-start testing](coldstart-testing.md), the same question asked of the content
- [Instructional design for developers](instructional-design.md), where the structural commitments come from
- [Learning paths and curriculum](learning-paths.md), the unit an assessment usually spans
- [Time to first success](time-to-first-success.md), the behavioural proxy used instead
- [Workshops and hands-on labs](workshops.md), the one setting where watching a reader is free
