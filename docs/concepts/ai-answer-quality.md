---
title: Measuring AI answer quality
summary: "Retrieval quality is a ceiling on answer quality, and when a wider context window stops helping, the failures left are vocabulary rather than ranking."
diataxis: explanation
audience: developer
concept: ai-answer-quality
tags: [meas, core]
---

# Measuring AI answer quality

`core` · difficulty 3 · 5h

!!! quote "Asked for by name"
    NVIDIA: "AI answer quality"

**Prerequisites:** [Output evaluation](output-evaluation.md), [Documentation analytics](docs-analytics.md)

## What it is

Measuring whether an assistant answering from your corpus answers correctly.
NVIDIA lists it as a metric the role owns, which makes documentation partly
responsible for a system it does not control: the model is someone else's, the
prompt is often someone else's, and the only input the documentation team owns
is the corpus.

That constraint is clarifying rather than limiting, because the corpus sets a
ceiling. If the retrieved context does not contain the fact, a correct answer
requires the model to supply it from elsewhere, which is the behaviour you are
trying to prevent. **Retrieval quality is an upper bound on grounded answer
quality**, and the bound is measurable without a model in the loop at all.

## Why the job asks for it

Because readers have stopped arriving at documentation and started arriving at
answers about it.

A corpus is now consumed by assistants more often than many teams realise, and
the failure mode is new: a confident, fluent, wrong answer, delivered without
the reader ever seeing the page that would have corrected it. Link checking,
sample execution and prose linting say nothing about this. The page can be
perfect and unretrieved, and the answer is still wrong.

The second reason is defensive. When an assistant answers wrongly from your
documentation, the question in the room is whether the docs were wrong or the
model was. Without a measurement, that argument is settled by whoever is more
senior. With one, it is settled by the number.

## The golden path

Measure the ceiling, find the point at which more context stops helping, and
fix what is left. About forty minutes, on the companion repository's twenty-case
golden set.

**Step 1: the ceiling, at one chunk**

Each golden case declares the terms a grounded answer must cite. Check whether
the top retrieved chunk contains them:

```python
hay = f"{top.breadcrumb}\n{top.text}".lower()
missing = tuple(t for t in case.must_contain if t.lower() not in hay)
```

```
grounded@1   16/20  (80%)
```

That is not an answer-quality score. It is a statement that for four of twenty
questions, a model answering from the single best chunk would have to invent
the key fact or decline.

**Step 2: the ceiling across the window a model actually sees**

No real system passes one chunk. Measure the same property across the top *k*:

```
  grounded@1    16/20  (80%)
  grounded@3    18/20  (90%)
  grounded@5    18/20  (90%)
  grounded@10   18/20  (90%)
```

Ten points between one chunk and three, then **nothing at all out to ten**.

That plateau is the most useful shape in this measurement. While widening the
window still helps, the failures are ranking failures, and a reranker or a
better embedding model would address them. Once it stops helping, the remaining
failures are not retrieval failures at all, and no amount of model or
infrastructure will touch them.

**Step 3: look at what survived**

```
ungrounded at k=10: 2
   chunk-size      missing ['size']   'how do I make the chunks smaller'
   prose-linting   missing ['vale']   'how do I stop people writing hedge words'
```

Both are vocabulary gaps. In each, the reader's everyday word was absent from
the page that documents the thing, while the page used a precise term the reader
had no reason to know. The golden set had even said so in its own `why` field
for one of them: "the reader knows the symptom and not the tool name".

Neither is a ranking problem, which is why k=10 could not help.

**Step 4: fix the corpus, not the retriever**

One sentence per page, each putting the reader's word beside the corpus's word.
Two sentences in total, no code, no model, no reranker:

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

**Four of five scores moved, and the ceiling reached 100 per cent at three
chunks.** The narrowing headroom is the subtle part: routing headroom measures
accuracy sitting unclaimed behind a query router, and some of that gap turned
out never to have been a routing problem. It was a word the corpus did not use.

A ten-point `hit@1` gap looks like a business case for a reranker. Five points
of it were a synonym.

**Step 5: the limit, stated plainly**

Everything above measures retrieval. **No model answered a single question.**

So the honest claim is a bound: at three chunks of context, every question in
this set can be answered from material that contains the required facts. Which
is not the same as saying the answers would be right. A model can misread a
correct chunk, blend two chunks into a claim neither makes, or answer correctly
from its own pre-training while the retrieved context is irrelevant, and that
last case scores as success on every metric here.

Measuring the rest needs a model in the loop and a grader, which is
[output evaluation](output-evaluation.md), and it costs per run in a way this
does not. The division worth keeping is that retrieval grounding is cheap,
deterministic and a hard ceiling, so it is where to start and where most of the
early wins are.

**What you built.** A grounding ceiling measured across the context window, a
plateau that distinguishes ranking failures from vocabulary failures, a
two-sentence corpus fix that moved four metrics, and an explicit statement of
what the measurement does not cover.

## Reference

### The three layers, and who owns each

| Layer | Measures | Owned by | Cost per run |
|---|---|---|---|
| Retrieval grounding | Could a correct answer be built | Documentation | Near zero |
| Answer correctness | Was it built correctly | The system | A model call per case |
| Answer usefulness | Did it help the reader | The product | A human per case |

NVIDIA's bullet names the second and a documentation role can only move the
first, which is a reasonable division: the first is a ceiling on the second.

### Metrics worth running, in order of cost

| Metric | Needs a model | Catches |
|---|---|---|
| `grounded@1` | No | The best chunk lacks the fact |
| `grounded@k` | No | Whether more context would help |
| `hit@k`, MRR | No | Ranking quality |
| Routing accuracy | No | The right page of the wrong kind |
| Citation validity | No | A cited chunk that does not support the claim |
| Faithfulness grading | Yes | Fluent answers the context does not support |
| Refusal rate on absent content | Yes | Inventing what the corpus lacks |
| Human preference | A person | Everything, slowly |

The first four are free and deterministic. Teams routinely start at the bottom
of this table because that is what the tooling advertises, and leave the free
ceiling unmeasured.

### Why grounding and ranking have to be read together

Neither metric contains the other. Cross them over the twenty cases:

```
                 grounded   ungrounded
  hit@1             13          0
  miss               5          2

  the two metrics agree on 15 of 20 cases (75%)
```

`grounded@1` is 90 per cent and `hit@1` is 65, so grounding looks like the
healthier number, and the top-right cell explains why that is misleading.
**Five cases are grounded while retrieving the wrong page**: a chunk from a
page the question was not about still happened to contain every term the answer
must cite. An answer built on it could be correct and cite the wrong source.

The empty cell is the one to watch over time. "Right page, wrong section" was
occupied before the vocabulary fix in step 4, by the case whose top chunk came
from the correct page's filtering section rather than its sizing section. A
reader of `hit@1` alone would have scored that case a success.

| Cell | Means | Visible to |
|---|---|---|
| hit, grounded | Working | Either metric |
| hit, ungrounded | Right page, wrong section | `grounded@1` only |
| miss, grounded | Right terms, wrong source | `hit@1` only |
| miss, ungrounded | Nothing useful retrieved | Either metric |

Two of those four failures are invisible to one of the two metrics, which is
the argument for reporting both and the reason a single headline retrieval
number is not worth having.

### Reading the grounded@k curve

| Shape | Means | Do |
|---|---|---|
| Rises steadily with k | Ranking is the bottleneck | Rerank, or improve the index |
| Jumps then plateaus | A few ranking wins, then content gaps | Fix the content |
| Flat and low from k=1 | The corpus lacks the material | Write it |
| 100% at k=1 | The set is too easy | Write harder cases |

The second row is the common case and the one people misdiagnose, because the
early jump suggests retrieval work is paying off right up to the point where it
stops.

### What inflates these numbers

| Hazard | Effect |
|---|---|
| A golden question quoted in the corpus | That page wins its own test case |
| Terms chosen after seeing the retrieval | Grounding checks for what you know is there |
| `must_contain` terms that are too generic | Any chunk satisfies them |
| A set tuned until it goes green | Measures nothing |
| A model's own knowledge of the subject | Scores as retrieval success |

The first is not hypothetical: adding a documentation example that quoted one
golden question verbatim cost five points of `hit@1`, and the note explaining
the mistake quoted it again and cost the same five points.

### What this cannot tell you

| Question | Needs |
|---|---|
| Was the answer correct | A model and a grader |
| Did it hedge when it should have refused | A model and absent-content cases |
| Did it cite the chunk it actually used | Instrumentation in the answering system |
| Would a reader have been satisfied | A reader |
| Is the assistant better than the search box | Both, measured side by side |

## How to talk about it

**Lead with the ceiling, because it reframes the whole problem.** "The model and
the prompt usually are not mine, and the corpus is. If the retrieved context
does not contain the fact, a correct answer means the model supplied it from
somewhere else, which is the thing I am trying to prevent. So retrieval
grounding is an upper bound on grounded answer quality, and I can measure that
bound with no model in the loop and no cost per run."

**The measurement worth describing is the curve, not the number.** Grounding at
one chunk was 80 per cent, at three 90, and then flat all the way to ten. That
plateau is diagnostic: while widening the window still helps, the failures are
ranking failures and a reranker would address them; once it stops helping, the
failures are not retrieval failures and no model or infrastructure will touch
them.

**Then the finding, which is the part I would want to be asked about.** Both
surviving failures were vocabulary gaps: the reader's everyday word was missing
from the page that documents the thing, while the page used a precise term the
reader had no reason to know. The fix was one sentence per page. It moved
`hit@1` five points, MRR from 0.742 to 0.775, routing five points, grounding at
one chunk from 80 to 90 per cent and at three chunks to 100, and it narrowed the
routing headroom, which means part of what looked like a routing opportunity was
never a routing problem. A ten-point gap looked like a case for a reranker and
five points of it was a synonym.

**Volunteer the limit before anyone has to ask for it.** No model answered a
single question in any of this. I can say that at three chunks every question
in the set can be answered from material containing the required facts. I
cannot say the answers would be right: a model can misread a correct chunk,
blend two into a claim neither makes, or answer correctly from pre-training
while the retrieved context is irrelevant, and that last case scores as success
on every metric I have. Closing that needs a model and a grader, which is
output evaluation and costs per run.

## How to prove it

**The artifact.** A golden set with `must_contain` terms, a grounded@k curve
over your real retriever, and a commit where fixing the corpus moved the
numbers.

**Three things to do, in order:**

1. Compute grounded@k for k of 1, 3, 5 and 10 on a corpus you own. Predict
   where it plateaus. The plateau tells you whether to buy a reranker or write
   two sentences, and that is a budget decision.
2. Take the cases still failing at k=10 and look for the reader's word on the
   page. In mine, both were synonyms the corpus never used.
3. Check whether any documentation page quotes one of your evaluation
   questions. If it does, that page is winning its own test case.

**What makes it credible rather than decorative.** The grounded@k curve, the
plateau, the two-sentence fix and the before-and-after table are all from
`docpack`'s twenty-case golden set and reproducible with
`docpack eval evals/golden.yaml`; the recorded scores on its
[evaluating retrieval](https://johnallred.github.io/docpack/explanation/evaluating-retrieval/)
page were updated in the same commit, which is how the change shows up in a
diff. What does not exist is any measurement with a model in the loop: nothing
here grades an answer, there is no faithfulness scoring and no refusal testing,
so the whole second layer of the table above is unmeasured and the
[demonstrated](../demonstrated.md) page records the concept as partial on that
basis.

## Related

- [Output evaluation](output-evaluation.md), the layer that needs a model and a grader
- [Retrieval evaluation](retrieval-evaluation.md), the harness these metrics come from
- [Grounding and citation](grounding.md), what a grounded answer owes its source
- [Documentation analytics](docs-analytics.md), where this sits among the measurements
- [Search and query log analysis](search-log-analysis.md), what makes a golden set representative
- [Style guides and terminology management](style-guide.md), where a synonym gap gets fixed
