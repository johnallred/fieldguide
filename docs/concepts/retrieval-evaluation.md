---
title: Retrieval evaluation
summary: A golden set of questions with expected sources, scored in CI, because every other check asks whether the docs are correct rather than useful.
diataxis: explanation
audience: developer
concept: retrieval-evaluation
tags: [ai, core]
---

# Retrieval evaluation

`core` · difficulty 3 · 6h

> including llms.txt, MCP-accessible sources, agent skills and context kits, and evaluation sets for answer accuracy

> Source: nvidia posting, verbatim

**Prerequisites:** [RAG pipelines](rag.md)

**Leads to:** [Measuring AI answer quality](ai-answer-quality.md), [Output evaluation](output-evaluation.md)

## What it is

A set of real questions paired with the page that should answer each, scored
automatically so a change to the corpus or the retriever moves a number. The
metrics are hit@k, mean reciprocal rank, and whatever else your failure modes
demand.

It is the only check in a documentation pipeline that asks whether the corpus
is **useful** rather than whether it is **correct**.

## Why the job asks for it

NVIDIA names it directly: "evaluation sets for answer accuracy", listed
alongside llms.txt and MCP as a required AI-ready output. It is the rarest of
the four in practice and the most diagnostic of whether a team is serious.

Here is why it matters more than it sounds. Every other gate in this guide,
[link checking](link-checking.md),
[code-sample validation](code-sample-validation.md),
[cold-start testing](coldstart-testing.md), answers a question of the form "is
this broken". A corpus can pass all of them and still fail the only question a
reader has: **I asked this, did I get the right page.** Nothing else measures
that, and without measuring it you cannot tell an improvement from a
coincidence.

On a Tuesday it is the thing that settles arguments. Somebody proposes adding
embeddings. Somebody else proposes a reranker. A third person wants to rewrite
the chunker. All three are plausible, all three cost weeks, and without an eval
set the decision is made by whoever argues hardest. With one, you measure the
lexical baseline, see that routing is the gap rather than ranking, and build the
cheap thing.

## The golden path

Build a golden set, score a retriever on it, and use it to make one real
decision. Fifty minutes, dependency-free.

**Step 1: write the golden set, with the conventions that keep it alive**

```bash
mkdir -p eval-drill && cd eval-drill
cat > corpus.json <<'EOF'
[
  {"id": "c1", "source": "reference/flags.md", "crumb": "Server flags > batch_size", "kind": "reference",
   "text": "batch_size controls how many requests are grouped per forward pass. The default is 32."},
  {"id": "c2", "source": "how-to/latency.md", "crumb": "Reduce latency > Lower the batch size", "kind": "how-to",
   "text": "If your p99 is too high, set batch_size to 1 or 2. A batch of 32 waits for 32 requests, adding roughly 200ms."},
  {"id": "c3", "source": "reference/flags.md", "crumb": "Server flags > max_memory_gb", "kind": "reference",
   "text": "max_memory_gb caps the GPU memory the server will allocate. The default is 16. Size for peak load, not startup."},
  {"id": "c4", "source": "reference/legacy.md", "crumb": "Legacy 1.x flags > max_memory_mb", "kind": "reference",
   "text": "max_memory_mb was the 1.x equivalent of max_memory_gb. Removed in 2.0 and ignored if set."},
  {"id": "c5", "source": "explanation/batching.md", "crumb": "Why batching helps > Throughput", "kind": "explanation",
   "text": "A GPU is more efficient per item on a larger batch, so batching raises throughput at the cost of latency."},
  {"id": "c6", "source": "how-to/oom.md", "crumb": "Fix an out-of-memory error > Size for peak", "kind": "how-to",
   "text": "If the server starts cleanly and dies under traffic, raise max_memory_gb or lower batch_size."}
]
EOF

cat > golden.yaml <<'EOF'
# Rules for adding a case, which exist because an eval set rots faster than
# the corpus it measures:
#
#   1. Phrase the question the way a READER would type it, never the way the
#      page is worded. A case lifted from a page's own heading measures that
#      string matching works, which was never in doubt.
#   2. `expect_kind` is the kind of answer the question's PHRASING calls for,
#      which is not always the kind of the expected page. A mismatch is a
#      finding about the corpus, not a mistake in the case.
#   3. `why` says what the case probes. Without it nobody can tell a
#      deliberately hard case from a stale one, and in six months the whole
#      set is untouchable.

- id: default-batch
  question: what is the default batch size
  expect_source: reference/flags.md
  expect_kind: reference
  why: Pure lookup. If this regresses, something is badly wrong.

- id: latency-symptom
  question: my p99 is too high
  expect_source: how-to/latency.md
  expect_kind: how-to
  why: A symptom, not a topic. The reader does not know the fix is batch size.

- id: cap-memory
  question: how do I limit gpu memory
  expect_source: reference/flags.md
  expect_kind: reference
  why: Competes with the removed 1.x flag, which is the dangerous near-miss.

- id: oom-under-load
  question: server dies under traffic but starts fine
  expect_source: how-to/oom.md
  expect_kind: how-to
  why: Phrased as an incident. Shares little vocabulary with the page.

- id: why-batch
  question: why would I batch requests at all
  expect_source: explanation/batching.md
  expect_kind: explanation
  why: A why question. Should route to explanation, not to the flag reference.

- id: legacy-flag
  question: max_memory_mb
  expect_source: reference/legacy.md
  expect_kind: reference
  why: An exact identifier for a removed flag. Must not return the current one.

- id: throughput-action
  question: how do I raise throughput
  expect_source: how-to/latency.md
  expect_kind: how-to
  why: >
    Deliberate tension. Topically the explanation page is closest; the reader
    asked what to DO. Expected to be hard.
EOF
python3 -c "
import yaml
cases = yaml.safe_load(open('golden.yaml'))
print(len(cases), 'cases')
assert all(c.get('why') for c in cases), 'every case needs a why'
print('every case states what it probes')
"
```

**Step 2: the harness**

```bash
cat > evaluate.py <<'PY'
"""Score a retriever against a golden set.

Five metrics, and the last two are the ones worth arguing about.

  hit@1 / hit@3   the expected page is first / in the top three
  MRR             mean reciprocal rank, so second beats ninth
  routing         the top result is the KIND of page the question needs
  headroom        hit@1 if the retriever were told the right kind

ROUTING matters because topical correctness is not enough: a reference page
and an explanation page about one subject can both be relevant while only one
can answer the question asked.

HEADROOM is NOT an achievable score. At query time nobody knows what kind the
question wants. It measures how much accuracy is sitting behind a query
router, which turns "add a reranker or add a classifier" from an argument into
a measurement.
"""
import json
import math
import re
import sys
from collections import Counter

import yaml

K1, B, DEPTH = 1.2, 0.75, 3


def tokenize(text):
    return [t for t in re.findall(r"[a-z0-9_]+", text.lower()) if len(t) > 1]


class Retriever:
    """BM25 over chunks, searching the heading trail as well as the text."""

    def __init__(self, chunks, use_crumb=True):
        self.chunks = chunks
        self.use_crumb = use_crumb
        self.docs = [
            Counter(tokenize(f"{c['crumb']} {c['text']}" if use_crumb else c["text"]))
            for c in chunks
        ]
        self.lengths = [sum(d.values()) for d in self.docs]
        self.avg = sum(self.lengths) / len(self.docs)
        df = Counter()
        for d in self.docs:
            df.update(d.keys())
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - c + 0.5) / (c + 0.5)) for t, c in df.items()}

    def search(self, question, kind=None, limit=DEPTH):
        terms = tokenize(question)
        scored = []
        for chunk, doc, length in zip(self.chunks, self.docs, self.lengths):
            if kind and chunk["kind"] != kind:
                continue
            score = 0.0
            for t in terms:
                f = doc.get(t, 0)
                if not f:
                    continue
                norm = 1 - B + B * (length / self.avg)
                score += self.idf.get(t, 0.0) * (f * (K1 + 1)) / (f + K1 * norm)
            if score > 0:
                scored.append((score, chunk))
        scored.sort(key=lambda s: (-s[0], s[1]["id"]))
        return scored[:limit]


def rank_of(hits, expect_source):
    """1-indexed rank of the first hit from the expected PAGE, or None.

    Page-level, not chunk-level: a corpus has several chunks per page and the
    reader wants the page. Scoring per chunk would punish a corpus for
    splitting a page well.
    """
    for position, (_, chunk) in enumerate(hits, start=1):
        if chunk["source"] == expect_source:
            return position
    return None


def evaluate(retriever, cases):
    rows = []
    for case in cases:
        hits = retriever.search(case["question"])
        filtered = retriever.search(case["question"], kind=case["expect_kind"])
        top = hits[0][1] if hits else None
        rows.append({
            "id": case["id"],
            "rank": rank_of(hits, case["expect_source"]),
            "filtered_rank": rank_of(filtered, case["expect_source"]),
            "top_source": top["source"] if top else "",
            "top_kind": top["kind"] if top else "",
            "routed": bool(top) and top["kind"] == case["expect_kind"],
        })
    return rows


def report(rows, label):
    n = len(rows)
    hit1 = sum(1 for r in rows if r["rank"] == 1) / n
    hit3 = sum(1 for r in rows if r["rank"] is not None) / n
    mrr = sum(1 / r["rank"] if r["rank"] else 0 for r in rows) / n
    routing = sum(1 for r in rows if r["routed"]) / n
    fhit1 = sum(1 for r in rows if r["filtered_rank"] == 1) / n

    print(f"\n{label}: {n} cases, top-{DEPTH}")
    print(f"  hit@1      {hit1:6.1%}")
    print(f"  hit@{DEPTH}      {hit3:6.1%}")
    print(f"  MRR        {mrr:6.3f}")
    print(f"  routing    {routing:6.1%}")
    print(f"  hit@1 with kind filter   {fhit1:6.1%}")
    print(f"  routing headroom         {fhit1 - hit1:+6.1%}  (not achievable; see the page)")

    misses = [r for r in rows if r["rank"] != 1]
    if misses:
        width = max(len(r["id"]) for r in misses)
        print(f"\n  {'case':<{width + 2}} rank  top result")
        print("  " + "-" * (width + 32))
        for r in misses:
            rank = str(r["rank"]) if r["rank"] else "-"
            print(f"  ! {r['id']:<{width}} {rank:>4}  {r['top_source']} ({r['top_kind']})")
    return {"hit@1": hit1, f"hit@{DEPTH}": hit3, "mrr": mrr, "routing": routing}


def main():
    chunks = json.load(open("corpus.json"))
    cases = yaml.safe_load(open("golden.yaml"))

    # Validate the set against the corpus BEFORE scoring. A case pointing at
    # a renamed page keeps running and keeps reporting a lower score, and the
    # obvious reading of a falling score is that the retriever got worse.
    # That misdiagnosis is expensive, so it fails loudly instead.
    sources = {c["source"] for c in chunks}
    kinds = {c["kind"] for c in chunks}
    for case in cases:
        if case["expect_source"] not in sources:
            sys.exit(f"stale golden set: {case['id']} expects {case['expect_source']}, "
                     f"which is not in the corpus")
        if case["expect_kind"] not in kinds:
            sys.exit(f"{case['id']}: unknown expect_kind {case['expect_kind']!r}")
    print(f"ok: {len(cases)} cases resolve against {len(sources)} pages")

    report(evaluate(Retriever(chunks), cases), "BM25 with heading trails")
    return 0


if __name__ == "__main__":
    sys.exit(main())
PY
python3 evaluate.py
```

**Step 3: use it to make a decision**

This is the whole point. Three candidate changes, measured instead of argued.

```bash
cat > decide.py <<'PY'
"""Measure three proposed changes instead of arguing about them."""
import json

import yaml

from evaluate import Retriever, evaluate, report

chunks = json.load(open("corpus.json"))
cases = yaml.safe_load(open("golden.yaml"))

baseline = report(evaluate(Retriever(chunks), cases), "A. baseline")

# Proposal 1: stop indexing the heading trail, to save index size.
no_crumb = report(
    evaluate(Retriever(chunks, use_crumb=False), cases),
    "B. without heading trails (someone proposed dropping them)",
)

# Proposal 2: retire the legacy flags page, which nobody should be using.
without_legacy = report(
    evaluate(Retriever([c for c in chunks if c["source"] != "reference/legacy.md"]),
             [c for c in cases if c["expect_source"] != "reference/legacy.md"]),
    "C. with the legacy page retired",
)

print("\n" + "=" * 64)
print(f"{'metric':<12} {'A base':>8} {'B no crumb':>12} {'C no legacy':>12}")
print("-" * 64)
for key in baseline:
    print(f"{key:<12} {baseline[key]:>8.1%}" if key != "mrr"
          else f"{key:<12} {baseline[key]:>8.3f}", end="")
    for other in (no_crumb, without_legacy):
        print(f" {other[key]:>12.1%}" if key != "mrr" else f" {other[key]:>12.3f}", end="")
    print()
PY
python3 decide.py
```

**Step 4: set a floor, not a target**

```bash
cat > gate.py <<'PY'
"""Fail the build when retrieval regresses.

The floor sits BELOW the current score on purpose. It is a regression gate,
not a target: set to the current number, ordinary content edits trip it and
people learn to skip CI. The real scores belong on a published page where a
change to them shows up in a diff and has to be explained.
"""
import json
import sys

import yaml

from evaluate import Retriever, evaluate

MRR_FLOOR = 0.60
HIT3_FLOOR = 0.70

rows = evaluate(Retriever(json.load(open("corpus.json"))),
                yaml.safe_load(open("golden.yaml")))
n = len(rows)
mrr = sum(1 / r["rank"] if r["rank"] else 0 for r in rows) / n
hit3 = sum(1 for r in rows if r["rank"] is not None) / n

failures = []
if mrr < MRR_FLOOR:
    failures.append(f"MRR {mrr:.3f} below floor {MRR_FLOOR}")
if hit3 < HIT3_FLOOR:
    failures.append(f"hit@3 {hit3:.1%} below floor {HIT3_FLOOR:.0%}")

for failure in failures:
    print(f"RETRIEVAL REGRESSION  {failure}", file=sys.stderr)
print(f"{'FAIL' if failures else 'ok'}: MRR {mrr:.3f}, hit@3 {hit3:.1%}")
sys.exit(1 if failures else 0)
PY
python3 gate.py; echo "exit=$?"
```

**What you built.** A validated golden set, five metrics, a measured comparison
of three proposals, and a CI gate with a floor below the current score.

### What the measurement actually said, which was not what was expected

Baseline: **hit@1 71.4%, hit@3 85.7%, MRR 0.786, routing 71.4%, headroom
+14.3%.** Two cases miss. `default-batch` lands at rank 2, and
`throughput-action` is not in the top three at all, which is the case the
golden set marked as deliberately hard.

Then the comparison:

| metric | A baseline | B without heading trails | C with legacy retired |
|---|---|---|---|
| hit@1 | 71.4% | **85.7%** | 66.7% |
| hit@3 | 85.7% | 85.7% | 83.3% |
| MRR | 0.786 | **0.857** | 0.750 |
| routing | 71.4% | **85.7%** | 66.7% |

**Proposal B scored better.** Dropping the heading trail from the index
improved hit@1 by 14 points, which directly contradicts the argument made on
[the chunking page](chunking.md) and the argument made earlier in this guide.

That is the result, and the honest response is not to bury it or to accept it.

**It is one case.** Seven cases means one case is 14.3 percentage points, so
this entire difference is `default-batch` changing places. With the crumb
indexed, "what is the default batch size" matches `Reduce latency > Lower the
batch size` and returns the how-to page; without it, the reference page wins.
By the sample-size table below, **a 14-point difference on a seven-case set is
one case and is inside the noise floor.** The correct conclusion is "this set
cannot answer that question", not "drop the heading trails".

**And it points at a real defect that is not about crumbs at all.** The
reference page's chunk says `batch_size` with an underscore; the question says
"batch size" with a space. The tokenizer keeps underscores so flag names
survive, which means the two never match. That is a genuine finding the eval
set surfaced, and the fix is a tokenizer that indexes both forms, not a change
to chunking.

**Proposal C is not a like-for-like comparison**, and this is a methodological
trap worth naming. Retiring the legacy page also removes the `legacy-flag`
case, so C is scored over six cases instead of seven. Its lower score is partly
arithmetic. Any change that alters the corpus *and* the question set cannot be
compared on a single number, and an eval harness will happily let you do it
anyway.

Three findings from one measurement, and none of them was the one being looked
for. That is what an eval set is for.

## Reference

### The metrics, and what each is for

| Metric | Question it answers | Watch out for |
|---|---|---|
| hit@1 | Is the top result right? | Harsh; a near-miss at rank 2 scores zero |
| hit@3 | Is it in the top three? | Generous; says nothing about ordering |
| MRR | Weighted by position | One number, hard to interpret alone |
| Routing accuracy | Is it the right *kind* of page? | Needs a type field on every page |
| Grounded@1 | Does the top chunk contain the fact? | See [grounding](grounding.md) |
| Headroom | What a perfect router would gain | **Not a score.** Explained below |

### Why routing accuracy is worth the extra column

Topical relevance is not enough. "How do I raise throughput" and "why would I
batch requests" are about the same subject, and only one of them can be
answered by an explanation page. A retriever returning the right subject in the
wrong genre produces an assistant that confidently answers a different question
than the one asked, and hit@1 cannot see it.

### The headroom number, and why it is not a score

The harness runs every question twice: once normally, once with the retriever
told which page kind to search.

That second figure is **not achievable**. At query time nobody knows what kind
a question wants; the harness knows only because the golden set declares it.

What the gap measures is how much accuracy is sitting unclaimed behind a query
router. A large gap says your [content model](content-model.md) carries
information the retriever is throwing away, and the cheapest next move is
classifying the question rather than embedding the corpus better. A gap near
zero says the opposite. Either way it is a measurement rather than an argument.

### Sample size, stated honestly

| Cases | One case is worth | Smallest meaningful difference |
|---|---|---|
| 7 | 14 percentage points | enormous |
| 20 | 5 points | about 10 points |
| 50 | 2 points | about 5 points |
| 200 | 0.5 points | a few points |

**A seven-case set cannot distinguish two retrievers that score within 15
points of each other.** It can tell you a page became unreachable, which is
most of what a regression gate needs. Any decision closer than that needs more
cases, and pretending otherwise is how teams make choices out of noise.

### Where the questions come from

| Source | Quality | Cost |
|---|---|---|
| Search queries with no click | **best**: gaps in the reader's words | an export |
| Support ticket subject lines | real failures, biased to people who ask | an export |
| Repeat questions in channels | real, biased to the loudest | a search |
| Assistant conversation logs | exactly your traffic | needs the assistant running |
| Hand-written by the author | available today, reflects author assumptions | an afternoon |

The last row is where every eval set starts and is the weakest. **Hand-written
cases measure whether the corpus answers the questions its author imagined**,
which correlates with real traffic less than you would hope. The first thing to
do with real logs is replace them.

### Keeping the set alive

| Rule | Why |
|---|---|
| Validate `expect_source` against the corpus | A renamed page makes the score drop for no reason |
| Require a `why` on every case | Otherwise nobody dares delete a stale case |
| Phrase questions as readers do | A case quoting the page's heading measures nothing |
| Score at page level, not chunk level | Readers want pages; chunk-level punishes good splitting |
| Publish the scores, gate on a lower floor | The floor survives edits; the published number gets explained |
| Add a case with every reported failure | The set grows from real traffic rather than imagination |

## How to talk about it

**What a competent answer sounds like.** Lead with what it decides, not with the
metrics. "Every other documentation check asks whether something is broken.
This is the only one that asks whether asking a question returns the right
page. I keep twenty-odd cases phrased the way readers actually type, validated
against the corpus so a renamed page fails loudly instead of quietly lowering
the score, scored on hit@k, MRR and routing accuracy, with a floor in CI set
below the current number so content edits do not trip it. The number I insist on
having is the lexical baseline, because a dense pipeline scoring worse than BM25
is a quarter spent going backwards."

**The follow-up is "how many cases do you need",** and the answer that shows
judgement is about resolution rather than a number. Twenty cases means one case
is five points, so anything under about ten points is noise and should not drive
a decision. That is enough to catch a page becoming unreachable, which is what a
gate is for, and not enough to choose between two close retrievers. Say that
before someone asks, because a candidate quoting a precise improvement from a
twelve-case set has told you they do not understand the instrument.

**The tradeoff to volunteer, and it is the real one.** A golden set becomes a
target. Once the number is visible, every change gets evaluated against those
questions, and the corpus starts getting optimised for them rather than for
readers. The symptom is a rising score and flat support load. Two mitigations,
both partial: never tune parameters by sweeping them against the eval set, which
turns it into training data; and refresh the cases from real logs regularly so
the target moves with the traffic. Neither fully solves it. Goodhart's law is
not avoidable, only managed.

**One sharper point.** The strongest observation is that **an eval set is a content
report, not a retrieval report.** A case that fails because the corpus has no
page on the subject is a documentation gap stated in a reader's own words, and
that is the most valuable output of the whole exercise. Sorting your failures by
[the five RAG failure modes](rag.md) tells you how much of your problem is
engineering and how much is writing, and in most documentation corpora the
answer is mostly writing. That reframes an AI project into a documentation gap
analysis, which is both true and a much better pitch to a documentation lead.

## How to prove it

**The artifact.** A golden set in version control, a harness, published scores
including the bad ones, and a CI floor.

**Three things to do, in order:**

1. **Run the golden path, including step 3.** The three-proposal comparison is
   the demonstration: it shows the set earning its keep by settling a decision
   rather than by producing a number.
2. **Publish the unflattering score.** A page with your real hit@1, the cases
   you lose, and why each is hard is far more credible than a good number with
   no failures listed. Nobody believes a retrieval system that works.
3. **Replace your hand-written cases with real queries.** Export zero-click
   searches or ticket subjects and rebuild the set from them. Then report how
   much the score changed, because that delta is the measure of how wrong your
   assumptions about your readers were, and it is usually a large number.

**What makes it credible rather than decorative.** Describing hit@k and MRR is reading a blog post. A
committed golden set with a `why` on every case, a validator that fails on a
renamed page, a lexical baseline next to every other number, and a published
score you are not proud of demonstrates that you ran it rather than built it.

## Related

- [RAG pipelines](rag.md), the five failure modes to sort your misses into
- [Grounding and citation](grounding.md), the per-answer check this complements
- [Output evaluation](output-evaluation.md), the same discipline on generated text
- [Search and query log analysis](search-log-analysis.md), where the real questions come from
