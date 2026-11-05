---
title: Support deflection
summary: "The deflection a corpus is capable of is measurable without a single ticket; the deflection it achieved is not measurable without a controlled comparison nobody runs."
diataxis: explanation
audience: developer
concept: support-deflection
tags: [meas, core]
---

# Support deflection

`core` · difficulty 2 · 3h

!!! quote "Asked for by name"
    NVIDIA: "Measurable reductions in support load or onboarding time through self-service knowledge systems"

**Prerequisites:** [Documentation analytics](docs-analytics.md)

**Leads to:** [Repeat questions](repeat-questions.md)

## What it is

A question that documentation answered, so nobody had to answer it again. The
claim is a counterfactual: this ticket would have been filed and was not, which
is a statement about an event that did not happen, and that is why the metric is
so often reported badly.

The useful move is to split it in two. **Deflection capability** is whether the
corpus contains the answer and hands it over when asked, which is a property of
the documentation and measurable today with no audience. **Deflection achieved**
is whether support volume actually fell because of it, which is a property of
the world and needs a comparison almost nobody sets up.

## Why the job asks for it

Because it is the one documentation outcome that converts directly into money,
which makes it the number a documentation team is funded by and the number it is
most tempted to overstate.

NVIDIA's phrasing is careful: "measurable reductions in support load". Not
"fewer tickets", which any release can produce by shipping fewer features, and
not "a self-service portal", which is an artifact rather than an outcome. The
word doing the work is *measurable*, and the honest answer in most organisations
is that nobody has the baseline to measure against.

So the professional skill here is less about raising the number than knowing
which half you are reporting, and saying so.

## The golden path

Measure the deflection a corpus is capable of, using no tickets, no analytics
and no audience. About twenty-five minutes. The method is the point: it turns a
counterfactual into two properties you can check.

**Step 1: separate answerable from findable**

A question becomes a support ticket for one of two quite different reasons. The
documentation does not contain the answer, which is a content gap. Or it
contains the answer and did not surface it, which is a retrieval gap. Those need
opposite responses, and the ticket looks identical either way.

Both are checkable against a [golden set](retrieval-evaluation.md):

```python
whole = "\n".join(p.read_text() for p in Path("docs").rglob("*.md")).lower()

for case in cases:
    answerable = all(t.lower() in whole for t in case.must_contain)
    hits = index.search(case.question, limit=1)
    findable = bool(hits) and hits[0].source == case.expect_source
```

**Step 2: run it**

```
  the answer exists somewhere in the corpus:   20/20
  the right page is returned first:            13/20
  answerable but not findable:                  7/20
```

```
  deflection ceiling      100%   every question is answered by the corpus
  deflection achieved      65%   the reader is handed the right page
  avoidable support load   35%   of these questions
```

**Seven of twenty questions have an answer in the documentation that the
documentation will not give you.** Those are the tickets worth caring about,
because each one is a reader who would have been deflected by better ranking or
better wording rather than by more writing.

The content gap is zero here, which is unusual and is an artifact of the golden
set having been written from the corpus. On a real corpus with real queries that
row is the interesting one, and it is the only row that calls for writing.

**Step 3: notice what the number is not**

Thirty-five per cent avoidable load is a statement about twenty questions chosen
by the author of the corpus. It is not a prediction about ticket volume, for
three reasons worth saying out loud:

```
the sample is 20 cases, author-written          one case is five points
no case is weighted by how often it is asked    all twenty count equally
no ticket queue exists for this project         nothing to validate against
```

Real deflection weights each question by frequency, and frequency comes from
[search logs](search-log-analysis.md) or a ticket queue. An unweighted golden
set treats a question asked four hundred times a month and one asked twice as
equally important, which is exactly the error that makes documentation backlogs
look nothing like support backlogs.

**Step 4: the comparison that would measure the other half, and why it is rare**

To claim deflection achieved you need tickets on a topic before a page existed
and after, with everything else held still. In practice everything else moves:

```
release cadence     a quieter quarter lowers tickets with no docs change
traffic             more users raise tickets while deflection improves
support policy      a new triage rule reclassifies tickets out of the category
product changes     the feature that generated the tickets was fixed
seasonality         enterprise support volume is not flat across a year
```

Each of those moves ticket volume by more than a documentation page does. A
before-and-after chart with none of them controlled is the standard artifact in
this area, and it supports no causal claim at all.

What does work, in rough order of rigour:

- A staged rollout, where the page is reachable for some locales or plans
  before others. This is the only option that gives you a control group.
- Tagging tickets with whether the asker had seen the page.
- Reporting the *rate* per thousand active users rather than the count.
- Instrumenting documentation search for the question and reporting that query
  volume moved. Cheapest and most honest, as long as you call it what it is: a
  deflection *proxy*, not a deflection.

**What you built.** A deflection ceiling and an achieved figure from a corpus
with no audience, a content gap separated from a retrieval gap, and an explicit
list of the confounds that make the other half unclaimable.

## Reference

### The two halves

| | Deflection capability | Deflection achieved |
|---|---|---|
| Property of | The corpus | The world |
| Needs | A golden set | A controlled comparison |
| Measurable today | Yes | Almost never |
| Moves when | You write or rank better | Anything at all happens |
| Honest claim | "35% of these questions are avoidable" | "We do not have the baseline" |

Reporting the left column in the right column's language is the overstatement to
avoid, and it is close to universal.

### Why a ticket arrived, and what each cause needs

| Cause | Detected by | Fixed by |
|---|---|---|
| The corpus lacks the answer | The answerable check fails | Writing |
| The answer exists, ranked badly | The findable check fails | [Ranking or vocabulary](repeat-questions.md) |
| The answer exists, phrased in house terms | Grounding fails on the right page | One sentence, usually |
| The reader never searched | Nothing in the corpus | Support workflow, not docs |
| The reader did not trust it | Nothing in the corpus | Freshness signals, examples |
| The answer is wrong | A reader complaining | [Code-sample validation](code-sample-validation.md) |

The first three are a documentation role's work and are separable by
measurement. The last three are the ones usually blamed and mostly are not
documentation problems, which is worth having evidence about before that
conversation rather than during it.

### Proxies, and how much to trust them

| Proxy | Trust | Why |
|---|---|---|
| Deflection ceiling from a golden set | High, for capability | Deterministic and reproducible |
| Zero-result searches | High, for gaps | A reader looking for something absent |
| Search query volume for a topic | Medium | Directional, confounded by traffic |
| Ticket rate per active user | Medium | Controls the biggest confound cheaply |
| Page views on the answer page | Low | A view is not a resolution |
| "Was this helpful?" | Very low | Measures mood |
| Ticket count, uncontrolled | None | Moves for a dozen unrelated reasons |

### What to say when asked for the number

| Asked | Answer |
|---|---|
| "How much did docs reduce support?" | The capability figure, and that achieved needs a baseline |
| "Can we get that baseline?" | Yes: tag tickets, or stage the rollout |
| "Just give me a percentage" | The capability figure, labelled as capability |
| "Our competitor claims 40%" | Ask what they controlled for |

## How to talk about it

**Lead with the split, because it is the part most people have not separated.**
"Deflection capability is whether the corpus contains the answer and surfaces it
when asked. That is a property of the documentation and I can measure it today
with no audience. Deflection achieved is whether support volume fell, which is a
property of the world and needs a controlled comparison. I report the first and
say plainly that I do not have the second."

**The follow-up is how you measure the first.** Against a golden set, separate
answerable from findable. On mine every question is answered somewhere in the
corpus and the right page comes back first for thirteen of twenty, so seven
questions have an answer the documentation will not hand over. Those seven are
the deflectable load, and they need better ranking or better wording rather than
more writing, which is a different backlog from the one people expect.

**Volunteer the weakness of your own number.** Twenty author-written cases,
unweighted, so a question asked four hundred times a month counts the same as
one asked twice. Real deflection weights by frequency, and frequency needs
search logs or a ticket queue. Without them the figure is a ceiling rather than
a forecast, and I would rather say that than quote it as one.

**The point to make about the uncontrolled chart.** A before-and-after ticket
graph is the standard artifact here and it supports no causal claim, because
release cadence, traffic, triage policy and seasonality each move ticket volume
further than a documentation page does. The cheapest real improvement is
reporting the rate per thousand active users instead of the count, which
controls the largest confound for no extra instrumentation.

**One sharper point.** The difference between a content gap and a retrieval gap
is invisible in the ticket and decisive for what you do next, and almost no
support taxonomy records it. A corpus that answers everything and surfaces
nothing looks exactly like a corpus with holes in it, and the two call for
opposite work: one needs a writer, the other needs a synonym.

## How to prove it

**The artifact.** A deflection ceiling computed from your own golden set, with
the answerable and findable columns kept separate.

**Three things to do, in order:**

1. Predict the ratio between answerable and findable for your corpus, write the
   two numbers down, then compute them. Mine were 20 of 20 against 13 of 20, and
   the second is the one that funds work.
2. Take your last ten support tickets and label each as content gap, retrieval
   gap, or not a documentation problem. Ten is enough to discover which of the
   three you have been assuming.
3. Convert any deflection figure you currently report into a rate per active
   user. If the trend reverses, the previous chart was measuring growth.

**What makes it credible rather than decorative.** The measurement above runs
against `docpack`'s twenty-case golden set and its twelve pages and is
reproducible from the repository: a ceiling of 100 per cent, an achieved figure
of 65 per cent, and a gap of seven named cases. What does not exist is a ticket
queue, an audience, or any baseline, so nothing here is a claim about support
volume, and the [demonstrated](../demonstrated.md) page records the achieved
half as having no demonstration in either repository.

## Related

- [Documentation analytics](docs-analytics.md), the instrumentation this depends on
- [Repeat questions](repeat-questions.md), the step 2 gap examined question by question
- [Retrieval evaluation](retrieval-evaluation.md), where the golden set comes from
- [Search and query log analysis](search-log-analysis.md), what supplies the missing weights
- [AI answer quality](ai-answer-quality.md), the same corpus measured for a different consumer
