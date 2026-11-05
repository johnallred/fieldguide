---
title: Repeat-question analysis
summary: "A question repeats because the corpus answers it in the corpus's words; two words missing from a 1,159-term vocabulary moved four of five retrieval scores."
diataxis: explanation
audience: developer
concept: repeat-questions
tags: [meas, core]
---

# Repeat-question analysis

`core` · difficulty 2 · 3h

!!! quote "Asked for by name"
    NVIDIA: "repeat questions"

**Prerequisites:** [Support deflection](support-deflection.md)

**Leads to:** [Prioritising documentation work](docs-prioritization.md)

## What it is

The practice of treating a question asked many times as a defect report about
the documentation rather than as a support workload. One person asking is a
person; forty people asking the same thing is a measurement, and the thing it
measures is a specific, locatable failure in the corpus.

The reason it earns a concept of its own, next to
[deflection](support-deflection.md), is that the repeat is diagnostic in a way
the volume is not. Deflection tells you how much load the documentation could
carry. A repeat tells you **which sentence to write**.

## Why the job asks for it

Because a repeat question is the cheapest high-quality signal in this entire
field, and almost nobody acts on it.

NVIDIA lists it among the things to measure, alongside deflection and answer
quality, and it is the one that most directly converts into an edit. The
failure mode is organisational rather than technical: repeats are visible to
support, the fix belongs to documentation, and the two have separate queues. So
the same question is answered individually four hundred times by people who are
measured on response time, and nobody is measured on making it stop.

The second reason is subtler and is what this page is mostly about. The usual
assumption is that a repeat means the answer is missing. More often the answer
is present, correct, well written, and phrased in vocabulary the asker does not
have.

## The golden path

Find out why two questions kept failing on a corpus that contained both
answers, then fix them and measure what the fix was worth. About thirty
minutes.

**Step 1: the questions that fail when the answer exists**

From the [deflection ceiling](support-deflection.md): every one of twenty
questions is answered somewhere in the corpus, and the right page comes back
first for thirteen. Two of the failures were not ranking failures at all. They
survived widening the retrieved window from one chunk to ten:

```
  grounded@1    16/20  (80%)
  grounded@3    18/20  (90%)
  grounded@5    18/20  (90%)
  grounded@10   18/20  (90%)
```

A plateau. More context stops helping, so no reranker and no embedding model
would touch the remaining two. Something else is wrong with them.

**Step 2: measure the corpus's vocabulary against the questions'**

For each question, what proportion of its terms appear anywhere in the corpus
at all:

```python
corpus = Counter()
for p in Path("docs").rglob("*.md"):
    corpus.update(tokenize(p.read_text()))

terms = tokenize(case.question)
coverage = sum(1 for t in terms if corpus[t]) / len(terms)
```

```
corpus vocabulary: 1159 distinct terms

  chunk-size        5/6   83%   term absent from the corpus: ['smaller']
  prose-linting     6/7   86%   term absent from the corpus: ['hedge']
  ...the other 18 cases: 100%

  mean question-vocabulary coverage: 95%
  questions fully covered: 13 of 20
```

**Two words.** `smaller` and `hedge`, absent from a corpus of 1,159 distinct
terms. The page about chunk sizing said "token ceiling". The page about prose
rules named the tool but never the symptom. Both pages were correct, complete
and useless to the person asking.

**Step 3: fix the vocabulary, not the retriever**

One sentence per page, each placing the reader's word beside the corpus's. No
code, no model, no reranker:

```
             before   after
hit@1          60%     65%
hit@3          95%     95%
MRR          0.742   0.775
routing        70%     75%
grounded@1     80%     90%
grounded@3     90%    100%
headroom      +15%    +10%
```

Four of five scores moved, and the ceiling reached 100 per cent at three
chunks. Two sentences.

**Step 4: confirm the mechanism rather than the coincidence**

Scores moving after an edit is not proof that the edit caused it. Re-measure
the vocabulary coverage itself, against the corpus as it was and as it is:

```
corpus vocabulary: 1159 distinct terms before, 1194 after

  chunk-size         83% -> 100%
  prose-linting      86% -> 100%

  mean coverage:      95% -> 97%
  fully covered:    13/20 -> 15/20
```

The two cases that moved on the retrieval metrics are exactly the two whose
vocabulary coverage moved, and no others. Thirty-five new terms entered the
corpus and two of them were the ones being tested, which is as close to a
mechanism as a twenty-case sample can get.

**Step 5: the generalisation, and its trap**

A repeat question is usually a vocabulary gap, and the fix is usually one
sentence putting the reader's word next to yours. That is the cheapest
documentation work there is.

The trap is where to put the sentence. It belongs on the page that answers the
question, and nowhere else. Writing the synonym pair into an explanation page *about* vocabulary gaps
makes that page compete for the query it describes. That happened here. An
earlier draft of the companion repository's own explanation page set both
pairs out in a table and gave back five points of `hit@1`, because the
explanation outranked the two how-to pages for their own questions. Name the case, not its wording.

**What you built.** Two repeat failures diagnosed as vocabulary rather than
ranking, a two-sentence fix worth four of five scores, and a before-and-after
on the vocabulary metric itself that ties the fix to the movement.

## Reference

### Why a question repeats

| Cause | Looks like | Fix | Cost |
|---|---|---|---|
| The answer is absent | Nothing matches | Write the page | High |
| The reader's word is absent | Right page, never surfaced | One sentence | Trivial |
| The answer is buried mid-page | Right page, wrong section | A heading | Low |
| The answer is split across pages | Partial answers, repeated asks | Consolidate | Medium |
| The answer is wrong or stale | The reader followed it and came back | Fix and test it | Medium |
| The question is a product defect | Documentation cannot fix it | File the bug | Not yours |

Rows two and three are the majority on a mature corpus and the cheapest to
close, which is the opposite of how most documentation backlogs are ordered.

### Detecting repeats without a ticket queue

| Signal | Shows | Available without an audience |
|---|---|---|
| Vocabulary coverage per question | Terms the corpus lacks | Yes |
| `grounded@k` plateau | Failures ranking cannot fix | Yes |
| Answerable against findable | Load that is avoidable | Yes |
| Zero-result search queries | Words readers use and you do not | No, needs logs |
| Clustered support tickets | Frequency, which weights everything | No, needs a queue |
| The same question in two channels | A genuinely load-bearing gap | No |

The first three are free and this page is built on them. They identify
candidates; only the bottom three tell you which candidate is asked four
hundred times a month, which is why [search logs](search-log-analysis.md) are
the missing input rather than a nicety.

### The vocabulary sentence, as a pattern

| Corpus says | Reader says | The sentence |
|---|---|---|
| "token ceiling" | "smaller" | "To make chunks smaller, change the token ceiling." |
| "Vale" | "hedge words" | "Vale fails hedge words here rather than in review." |
| "idempotent" | "safe to run twice" | Name both, in that order |
| "deprecated" | "is this still supported" | Answer the question the reader asked |

The shape is always the same: the reader's word first or immediately adjacent,
the precise term kept, on the page that answers the question. Replacing your
term with theirs loses precision; putting them side by side loses nothing.

### What not to do about repeats

| Tempting | Why it fails |
|---|---|
| A FAQ page | Becomes an unmaintained parallel corpus |
| A glossary | Readers do not search glossaries, retrievers do not weight them |
| A synonym list in the search config | Invisible to every consumer but one |
| Rewriting the page in plain language | Loses the precise term, which experts search for |
| A chatbot over the same corpus | Inherits the vocabulary gap exactly |

The last row is the current version of this mistake and worth saying out loud:
a retrieval-augmented assistant over a corpus that lacks the reader's word
fails the same query the same way, with more confidence.

### Repeats against deflection

| | Deflection | Repeat analysis |
|---|---|---|
| Unit | The corpus | One question |
| Answers | How much load is avoidable | Which sentence to write |
| Needs weighting | Yes, badly | Less: a repeat is self-weighting |
| Output | A percentage | An edit |

## How to talk about it

**Lead with the reframing.** "A question asked forty times is a defect report
about the documentation, not a support workload. Deflection tells me how much
load the corpus could carry; a repeat tells me which sentence to write, which is
the more actionable of the two."

**The follow-up is the diagnosis, and this is where the measurement lands.** The
assumption is that a repeat means a missing answer. On my corpus both residual
failures had the answer present and correct: the words `smaller` and `hedge`
were absent from 1,159 distinct terms. One sentence per page putting the
reader's word beside the corpus's moved four of five retrieval scores, and took
grounding to 100 per cent at three chunks.

**How you know it was the vocabulary and not luck.** I re-measured vocabulary
coverage against the old and new corpus. Thirty-five new terms entered, and the
only two cases whose coverage moved were exactly the two whose retrieval scores
moved. On a twenty-case sample that is as close to a mechanism as you get, and
I would say so rather than claim causation.

**The diagnostic worth bringing.** The `grounded@k` plateau tells you when to
stop reaching for ranking. Mine went 80 per cent at one chunk, 90 at three, and
then flat out to ten. Once widening the window stops helping, the remaining
failures are not ranking failures, and no reranker or embedding upgrade will
touch them. That is a ten-point gap that looks like a business case for a
reranker, and half of it was a synonym.

**The tradeoff to volunteer.** Repeat analysis without frequency data finds
candidates and cannot rank them. My twenty cases are unweighted, so a question
asked four hundred times counts the same as one asked twice, and the fix order
I would derive is therefore arbitrary. Search logs or a ticket queue supply the
weights, and until they exist this is a method rather than a prioritisation.

## How to prove it

**The artifact.** A vocabulary-coverage measurement over your own golden set or
query log, and one page edited to carry a reader's word beside your own.

**Three things to do, in order:**

1. Take the five questions your support channel repeats most, and check whether
   each one's own words appear anywhere in the page that answers it. Predict how
   many fail before you look.
2. Compute `grounded@k` for k of 1, 3 and 10 on your corpus. Where the curve
   flattens is where ranking work stops paying, and that boundary is usually
   argued about rather than measured.
3. Add one sentence to one page putting a reader's word beside your precise
   term, then re-run your retrieval scores. It is the highest return per
   keystroke available in this job.

**What makes it credible rather than decorative.** Every figure above was
executed against `docpack`: the plateau, the 1,159-term vocabulary, the two
absent words, the two-sentence fix, and the before-and-after on both the
retrieval scores and the vocabulary metric, all reproducible from the
repository. What is missing is frequency: there is no ticket queue and no query
log, so these are candidates rather than a ranked backlog, and the
[demonstrated](../demonstrated.md) page records that limit rather than implying
the method was validated against real repeat volume.

## Related

- [Support deflection](support-deflection.md), the aggregate this breaks down
- [Search and query log analysis](search-log-analysis.md), the frequency data this lacks
- [AI answer quality](ai-answer-quality.md), where the grounded@k plateau is developed
- [Prioritising documentation work](docs-prioritization.md), what to do with a list of candidates
- [Style guides and terminology management](style-guide.md), the discipline that creates the gap
