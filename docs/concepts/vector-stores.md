---
title: Vector stores and hybrid search
summary: Where the vectors live, and why a documentation corpus needs lexical search alongside them rather than instead.
diataxis: explanation
audience: developer
concept: vector-stores
tags: [ai, core]
---

# Vector stores and hybrid search

`core` · difficulty 3 · 5h

!!! note "Not a quotation (derived)"
    The retrieval half of a RAG pipeline, which NVIDIA names as a way to stand out.

**Prerequisites:** [Embeddings](embeddings.md)

**Leads to:** [RAG pipelines](rag.md)

## What it is

A store that holds vectors and answers "which of these is closest to this one"
quickly, plus the metadata needed to filter before ranking. Hybrid search is
running a lexical index alongside it and combining the results, because the two
methods fail on different queries.

For a documentation corpus, **hybrid is the default and vector-only is the
mistake.**

## Why the job asks for it

Neither posting names a vector store, which is why this is `derived`. NVIDIA
asks for RAG pipelines twice and for content "structured and packaged for RAG",
and this is where the packaged content ends up.

What makes it `core` is the decision rather than the database. The database
choice barely matters and people spend all their time on it; **the hybrid
decision matters enormously and people skip it.** The reason is covered in
[embeddings](embeddings.md): a developer's question turns on flag names, version
numbers and negations, and those are precisely what embeddings blur. A
documentation search that cannot reliably find `max_memory_gb` when asked about
`max_memory_gb` is broken in a way no amount of reranking fixes.

On a Tuesday it is a triage question with a clear procedure. A developer
searched an exact error string and got nothing useful. Was the chunk missing
(a [chunking](chunking.md) problem), outranked (a fusion problem), or did the
vector search simply never surface it because the string is rare and
semantically unremarkable? The third is the common one and the fix is a lexical
index, not a better model.

## The golden path

Build a BM25 index, a vector index, and a fused one, then find the queries each
gets wrong. About forty minutes, dependency-free: the "vectors" here are
deterministic and local, so the comparison is reproducible and needs no model
download.

**Step 1: a corpus with the vocabulary that breaks each method**

```bash
mkdir -p store-drill && cd store-drill
cat > chunks.json <<'EOF'
[
  {"id": "c1", "text": "Set batch_size on the client. The default is 32.", "kind": "reference"},
  {"id": "c2", "text": "If your p99 is too high, reduce the batch to 1 or 2. Larger batches wait for the batch to fill before running.", "kind": "how-to"},
  {"id": "c3", "text": "Set max_memory_gb to cap GPU memory. The default is 16.", "kind": "reference"},
  {"id": "c4", "text": "Set max_memory_mb on the legacy 1.x client. Removed in 2.0.", "kind": "reference"},
  {"id": "c5", "text": "Quantised models tolerate much larger batches because the memory arithmetic differs.", "kind": "explanation"},
  {"id": "c6", "text": "The cache is enabled by default. Pass cache=False to turn it off.", "kind": "reference"},
  {"id": "c7", "text": "Exit code 2 means the arguments were invalid.", "kind": "reference"},
  {"id": "c8", "text": "A GPU is more efficient per item on a larger batch, which is why batching raises throughput.", "kind": "explanation"}
]
EOF
python3 -c "import json; print(len(json.load(open('chunks.json'))), 'chunks')"
```

**Step 2: BM25, which is the baseline worth beating**

```bash
cat > bm25.py <<'PY'
"""BM25 in about thirty lines, with no dependencies.

Worth implementing once rather than importing, because the two corrections it
makes are the two that matter and both are invisible in a library call:

  idf    a term appearing in every chunk carries almost no signal
  length normalisation, so the longest chunk does not win every query
"""
import json
import math
import re
from collections import Counter

K1, B = 1.2, 0.75


def tokenize(text):
    """Lowercase alphanumeric runs, keeping underscores so flag names survive.

    Splitting on underscore would turn `max_memory_gb` into three common
    words and destroy the one thing lexical search is good at.
    """
    return [t for t in re.findall(r"[a-z0-9_]+", text.lower()) if len(t) > 1]


class BM25:
    def __init__(self, chunks):
        self.chunks = chunks
        self.docs = [Counter(tokenize(c["text"])) for c in chunks]
        self.lengths = [sum(d.values()) for d in self.docs]
        self.avg = sum(self.lengths) / len(self.docs)
        df = Counter()
        for d in self.docs:
            df.update(d.keys())
        n = len(self.docs)
        self.idf = {
            t: math.log(1 + (n - c + 0.5) / (c + 0.5)) for t, c in df.items()
        }

    def search(self, query, limit=3):
        terms = tokenize(query)
        scored = []
        for chunk, doc, length in zip(self.chunks, self.docs, self.lengths):
            score = 0.0
            for t in terms:
                f = doc.get(t, 0)
                if not f:
                    continue
                norm = 1 - B + B * (length / self.avg)
                score += self.idf.get(t, 0.0) * (f * (K1 + 1)) / (f + K1 * norm)
            if score > 0:
                scored.append((score, chunk))
        scored.sort(key=lambda s: -s[0])
        return scored[:limit]


if __name__ == "__main__":
    index = BM25(json.load(open("chunks.json")))
    for query in ["max_memory_gb default", "my p99 is too high", "exit code 2"]:
        print(f"\nQ: {query}")
        for score, chunk in index.search(query):
            print(f"   {score:5.2f}  {chunk['id']}  {chunk['text'][:58]}")
PY
python3 bm25.py
```

**Step 3: a deterministic stand-in for vector search**

!!! warning "What this toy can and cannot show"
    A real embedding model is far better than what follows, and this page is
    careful about which conclusions the toy can support.

    **It can show the token-blur failure**, because that failure comes from
    representing text as a point in a topic space, which the toy also does.
    That is the result step 4 measures.

    **It cannot win a quality comparison against BM25.** Its vocabulary is a
    hand-written cue list, so on anything outside that list it returns
    nothing, and a horse race between the two here would be measuring the
    author's cue list rather than dense retrieval. The author's attempt to run
    one produced BM25 winning 6 of 7, which is a fact about the toy and not
    about embeddings.

    For a real quality comparison, run
    [the embeddings golden path](embeddings.md) with an actual model on your
    own vocabulary.

```bash
cat > vectorish.py <<'PY'
"""A deterministic, dependency-free stand-in for dense retrieval.

Each chunk becomes a vector over TOPICS rather than over words, by counting
cue words per topic. That reproduces the two properties of a real embedding
model that this page is about:

  it matches on MEANING    "p99 too high" finds a chunk about latency even
                           with almost no shared words
  it blurs EXACT TOKENS    max_memory_gb and max_memory_mb land in the same
                           place, because both are about memory limits

A real model does this far better and for the same structural reason. Using a
toy keeps the comparison reproducible and keeps the lesson about retrieval
design rather than about model choice.
"""
import json
import math
import re

TOPICS = {
    "latency": ["p99", "latency", "wait", "high", "fast", "slow", "responsive"],
    "batching": ["batch", "batch_size", "batches", "batching", "throughput", "32"],
    "memory": ["memory", "gpu", "cap", "max_memory_gb", "max_memory_mb", "gb", "mb", "16"],
    "config": ["set", "default", "pass", "client", "flag", "option"],
    "errors": ["exit", "code", "invalid", "arguments", "error", "removed"],
    "caching": ["cache", "enabled", "disable", "off"],
}


def embed(text):
    words = set(re.findall(r"[a-z0-9_]+", text.lower()))
    vec = [
        float(sum(1 for cue in cues if cue in words)) for cues in TOPICS.values()
    ]
    n = math.sqrt(sum(x * x for x in vec))
    return [x / n for x in vec] if n else vec


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


class VectorIsh:
    def __init__(self, chunks):
        self.chunks = chunks
        self.vectors = [embed(c["text"]) for c in chunks]

    def search(self, query, limit=3):
        q = embed(query)
        scored = [
            (dot(q, v), c) for v, c in zip(self.vectors, self.chunks) if dot(q, v) > 0
        ]
        scored.sort(key=lambda s: -s[0])
        return scored[:limit]


if __name__ == "__main__":
    index = VectorIsh(json.load(open("chunks.json")))
    for query in ["max_memory_gb default", "my p99 is too high", "exit code 2"]:
        print(f"\nQ: {query}")
        for score, chunk in index.search(query):
            print(f"   {score:5.3f}  {chunk['id']}  {chunk['text'][:58]}")
PY
python3 vectorish.py
```

**Step 4: fuse them, and measure all three**

Reciprocal rank fusion is the default worth starting from: it combines rankings
rather than scores, so it does not care that BM25 returns 7.4 and cosine returns
0.83.

```bash
cat > hybrid.py <<'PY'
"""Compare BM25, dense, and reciprocal rank fusion on the same queries.

RRF scores a document as the sum over retrievers of 1 / (k + rank). Combining
RANKS rather than SCORES is the whole trick: BM25 scores are unbounded and
cosine scores sit in [-1, 1], so any weighted sum of the raw numbers is
arbitrary and needs retuning whenever either side changes.
"""
import json

from bm25 import BM25
from vectorish import VectorIsh

RRF_K = 60

QUERIES = [
    ("max_memory_gb default", "c3", "exact flag name"),
    ("max_memory_mb", "c4", "NEAR-IDENTICAL legacy flag"),
    ("exit code 2", "c7", "exact error code"),
    ("my p99 is too high", "c2", "rare token, shared"),
    ("switch off the cache", "c6", "paraphrase"),
    ("why does batching help throughput", "c8", "a why question"),
]


def ranked_ids(hits):
    return [c["id"] for _, c in hits]


def rrf(*rankings):
    scores = {}
    for ranking in rankings:
        for rank, cid in enumerate(ranking, start=1):
            scores[cid] = scores.get(cid, 0.0) + 1.0 / (RRF_K + rank)
    return sorted(scores, key=lambda c: -scores[c])


chunks = json.load(open("chunks.json"))
lexical, dense = BM25(chunks), VectorIsh(chunks)

totals = {"bm25": 0, "dense": 0, "hybrid": 0}
print(f"{'query':<34} {'want':<5} {'bm25':<6} {'dense':<6} {'hybrid':<6} note")
print("-" * 92)

for query, expected, note in QUERIES:
    l = ranked_ids(lexical.search(query, limit=5))
    d = ranked_ids(dense.search(query, limit=5))
    h = rrf(l, d)

    results = {}
    for name, ranking in (("bm25", l), ("dense", d), ("hybrid", h)):
        top = ranking[0] if ranking else None
        results[name] = "OK" if top == expected else (top or "none")
        if top == expected:
            totals[name] += 1

    print(f"{query:<34} {expected:<5} {results['bm25']:<6} "
          f"{results['dense']:<6} {results['hybrid']:<6} {note}")

print("-" * 92)
n = len(QUERIES)
print(f"{'totals':<34} {'':<5} {totals['bm25']}/{n}    "
      f"{totals['dense']}/{n}    {totals['hybrid']}/{n}")
PY
python3 hybrid.py
```

**Step 5: look closely at the one case dense loses**

```bash
python3 - <<'PY'
import json

from bm25 import BM25
from vectorish import VectorIsh

chunks = json.load(open("chunks.json"))
lexical, dense = BM25(chunks), VectorIsh(chunks)

query = "max_memory_mb"
print(f"Q: {query}\n")
print("  dense ranking:")
for score, chunk in dense.search(query, limit=3):
    print(f"    {score:.3f}  {chunk['id']}  {chunk['text'][:52]}")
print("  lexical ranking:")
for score, chunk in lexical.search(query, limit=3):
    print(f"    {score:.2f}   {chunk['id']}  {chunk['text'][:52]}")
PY
```

**What you built.** Three retrievers, and one measured failure that is the whole
argument for hybrid search.

The totals are **6/6 lexical, 5/6 dense, 6/6 hybrid**, and the totals are not
the finding. Step 5 is. Asked for `max_memory_mb`, the dense retriever returns:

| Rank | Chunk | Score | Text |
|---|---|---|---|
| 1 | `c3` | 0.928 | Set **`max_memory_gb`** to cap GPU memory |
| 2 | `c5` | 0.707 | Quantised models tolerate larger batches |
| 3 | `c4` | 0.408 | Set **`max_memory_mb`** on the legacy 1.x client |

**The correct answer is third, behind a chunk about a different flag and a
chunk about quantisation.** Lexical search puts it first, alone, at 2.06, and
fusion recovers it.

That is a developer asking about a flag and being told about a different flag,
confidently. It is the single most common serious failure of vector-only
documentation search, and it is why "which vector database" is a far less
interesting question than "is there a lexical index at all".

Note also that lexical scores 6 of 6 here. **BM25 is a strong baseline on a
documentation corpus** and is frequently better than the dense-only system a
team spends a quarter building. Any claim that embeddings improved retrieval
needs the BM25 number next to it, which is what
[retrieval evaluation](retrieval-evaluation.md) is for.

### The other half: exact against approximate

Everything above is about ranking. A vector store exists for a different
reason, which the eight-chunk corpus is too small to show: it does not compare
the query to every vector. `drills/vector_store.py` measures what that costs,
over 4000 chunks in 64 dimensions with an IVF index, clustering the vectors and
probing only some clusters.

The vectors there are **hashed, not learned**: each chunk's tokens are feature
hashed into 64 dimensions with a signed hash and L2-normalised. No model, no
weights, nothing downloaded.

```
  IVF: 64 clusters, smallest 32, largest 102, mean 62 vectors
  exact: 0.15 ms per query, recall@10 1.000 by definition

  nprobe  scanned  recall@10  ms/query  speedup
       1       67     0.548      0.02    7.6x
       2      133     0.772      0.03    4.9x
       4      263     0.888      0.02    6.3x
       8      521     0.988      0.04    4.1x
      16     1017     1.000      0.09    1.7x
      32     1995     1.000      0.20    0.8x
      64     4000     1.000      0.44    0.4x
```

The table is one run's output. Its exact measurements can vary across
numerical environments; the stable result is the shape of the curve and the
full-probe recall. Milliseconds and speedup also vary by machine.

Three things in that table are worth more than the headline.

**The knee.** Recall climbs steeply and then flattens: probing 8 of 64
clusters scans 13 per cent of the corpus and recovers 98.8 per cent of the
exact answer. That ratio, not the absolute numbers, is what makes an
approximate index worth operating, and it is why `nprobe` is the first dial to
look at when retrieval quality is disappointing.

**Past the knee it is slower than brute force.** At `nprobe` 32 and 64 the
speedup is 0.8x and 0.4x: the index is doing *more* work than scanning
everything, because gathering candidates from clusters costs more than the
comparisons it saves. A vector store tuned to its maximum recall is a slower
exact search with extra steps, and that configuration is easy to arrive at by
raising `nprobe` until quality complaints stop.

**Probing every cluster returns exactly the exact answer**, which sounds like a
truism and is the reason this drill found a bug in its own measurement rather
than in the index. The first version reported 0.924 recall at full probe. An
index cannot lose recall against itself, so the number was measuring the
measurement: `len(set(found) & set(truth)) / k` is wrong whenever scores tie,
and this corpus ties constantly, so the identity of the top ten was arbitrary
among equals while the tenth-best *score* was not. Scoring against the k-th
best score fixes it, because an answer tied with a true answer is a true
answer. Any recall@k figure quoted without saying how ties were handled should
be read with that in mind.

### What the hashed stand-in does and does not preserve

The drill's second half tried to show hybrid search beating either half, and
could not. That failure is the clearest statement of where this substitution
stops.

```
  retriever  identifier     paraphrase     both
  lexical    1.000          0.135          0.568
  dense      0.880          0.000          0.440
  hybrid     0.935          0.065          0.500
```

| | Preserved by hashed vectors | Why |
|---|---|---|
| Exact search | **yes** | Exhaustive comparison is exhaustive for any vectors |
| Approximate recall loss | **yes** | It comes from partitioning a set of points, not from their origin |
| The recall-latency curve | **yes** | Same reason |
| Token blur | **partly** | Hash collisions blur unrelated tokens; a model blurs *related* ones, which is a different cause with a similar effect |
| Semantic matching | **no** | A hash has learned nothing. `cache` and `invalidate` are as far apart as `cache` and `banana` |
| Any quality comparison | **no** | It depends entirely on the above |

The paraphrase column shows the consequence: lexical scores 0.135, dense
scores zero, and fusing two retrievers that both fail produces a third that
also fails. Hybrid search wins when the two halves fail on *different*
queries, and the dense half earns its share by knowing that "too much ram" and
`memory` are related. This one cannot know that.

The identifier column is the sharper result. Dense scores 0.880, nearly as
well as BM25, and a dense retriever is not supposed to be good at exact
identifiers; that failure is most of what this page is about. It scores well
because feature hashing sends one token to one dimension, so a one-identifier
query is a near-one-hot vector and the search is a lexical lookup wearing
vector clothes. **A stand-in that accidentally reproduces the opposite of the
behaviour you are demonstrating is worse than no stand-in**, which is why the
hybrid argument above uses the cue-based toy, which at least has a topic space,
and why any real quality claim needs a real model.

## Reference

### Why hybrid, in one table

| Query type | Lexical | Dense | Example |
|---|---|---|---|
| Exact identifier | **strong** | weak | `max_memory_gb` |
| Exact error string | **strong** | weak | `exit code 2` |
| Version number | **strong** | weak | "2.4 vs 2.3" |
| Rare term | **strong** | weak | a one-off API name |
| Paraphrase | weak | **strong** | "turn the cache off" vs `cache=False` |
| Symptom with no shared words | weak | **strong** | "my p99 is too high" |
| Synonym | weak | **strong** | "repo" vs "repository" |
| Negation and polarity | weak | **weak** | "supported" vs "deprecated" |

The last row is the honest one: **neither method handles polarity**, so the fix
there is writing and [metadata](metadata.md), not retrieval. Anyone claiming
hybrid search solves negation has not tested it.

### Fusion methods

| Method | How | When |
|---|---|---|
| Reciprocal rank fusion | Sum of `1/(k+rank)` per retriever | The default. No score calibration needed |
| Weighted score sum | `a * bm25 + b * cosine` | Only after normalising; needs retuning constantly |
| Cascade | Lexical to shortlist, dense to rerank | Large corpora, latency budget |
| Rerank the union | Cross-encoder over the top k of both | Highest quality, slowest, most expensive |

RRF with `k = 60` is the standard starting point and is usually good enough that
tuning it is not where your time should go.

### Store options, which matter less than people think

| Option | Good for | Watch out for |
|---|---|---|
| In-process (`numpy`, `faiss`, `sqlite-vec`) | Under ~1M chunks, which is most docs | No built-in metadata filtering in some |
| Postgres with `pgvector` | You already run Postgres; real SQL filters | Index tuning on large tables |
| Dedicated (Qdrant, Weaviate, Milvus) | Large corpora, hybrid built in | A service to operate |
| Hosted (Pinecone, Turbopuffer) | Not wanting to operate one | Cost per query, data leaving |
| Search engines (Elasticsearch, OpenSearch, Typesense) | **Hybrid in one system** | Heavier to run |

For a documentation corpus of a few hundred thousand chunks, the honest answer
is that an in-process index plus a lexical index in the same process is
sufficient, fast, and much easier to debug than a service.

### Filtering before ranking

The most important feature after hybrid search, and the reason the
[content model](content-model.md) exists:

```python
# docpack: skip
results = store.search(
    query_vector,
    filter={"kind": "how-to", "audience": "developer", "visibility": "public"},
    limit=5,
)
```

A filter is a hard constraint. Hoping the ranking noticed the page genre is not,
and for [restricted content](partner-documentation.md) the difference is an
access-control boundary rather than a quality preference.

**Check that your store filters before it searches, not after.** A store that
retrieves the top 100 and then filters can return fewer than you asked for, or
nothing, while the right answer sat at rank 150.

### Operational things that cause incidents

| Thing | Consequence |
|---|---|
| Changing the embedding model | Every stored vector is incomparable; full re-embed |
| Changing the chunker | Same, plus every id changes unless ids are content-derived |
| Thresholding on absolute score | Scores are not comparable across queries |
| No `updated` in the metadata | Cannot discount stale content at query time |
| Re-indexing on every commit | Avoidable with [stable chunk ids](chunking.md) |

## How to talk about it

**What a competent answer sounds like.** Lead with hybrid and with the specific
failure. "For documentation I would not ship vector-only search. A developer
asking about `max_memory_gb` has to get the page about `max_memory_gb`, and
dense retrieval puts that nearly on top of `max_memory_mb`. So BM25 plus dense,
fused with reciprocal rank fusion, which combines ranks rather than scores so
nothing needs calibrating. The store choice is almost incidental: an in-process
index is enough for a few hundred thousand chunks, and what I care about is
whether it filters on metadata before ranking rather than after."

**The follow-up is "which vector database",** and the interesting move is to
decline the premise politely and name the two things that actually matter:
hybrid support and filter-before-rank. Then give a real answer anyway, because
refusing to choose reads as evasion: Postgres with `pgvector` if they already
run Postgres, an in-process index if the corpus is small, a search engine like
OpenSearch if they want hybrid in one system.

**The tradeoff to volunteer.** Hybrid search is two indexes to build, two to
keep in sync, and two to debug, and it roughly doubles your retrieval
infrastructure for a gain that is invisible on the queries you tested with.
There is also a subtler cost: fusion makes results harder to explain. With BM25
alone you can say which terms matched; with RRF over two retrievers the answer
is "it was third in one list and first in the other", which satisfies nobody
when a stakeholder asks why the assistant said something wrong.

**One sharper point.** The strongest framing is that **a vector store is a cache of
a decision you made earlier.** Every vector in it is downstream of a chunking
choice and a model choice, and neither is visible once the vectors are stored.
So the operational discipline that matters is not tuning the store, it is making
the inputs reproducible: pinned model, content-derived chunk ids, and a
re-embed that is a deliberate migration rather than a surprise. Teams that treat
the store as the system discover this when a model update quietly degrades
retrieval and nothing in their dashboards explains why.

## How to prove it

**The artifact.** A scored comparison of lexical, dense and fused retrieval on
your own corpus, with the per-query losses visible.

**Three things to do, in order:**

1. **Run the golden path.** The six-query table is the deliverable: it shows the
   two methods failing on disjoint sets, which is the argument.
2. **Redo it with your product's identifiers.** Your flag names, your error
   codes, your version strings. The dense column gets worse and the case for
   hybrid gets stronger.
3. **Check filter-before-rank in whatever store you use.** Query with a filter
   that matches only a handful of chunks and ask for twenty results. If you get
   fewer than exist, it filters after. Writing that test down is a small,
   specific thing most people never check.

**What makes it credible rather than decorative.** Naming vector databases proves you read a comparison
post. A per-query table showing exactly which queries dense retrieval loses on
your own vocabulary, and a stated conclusion about hybrid, demonstrates you
measured it.

### How this would be demonstrated elsewhere

The mechanics of this page turned out to be demonstrable without a model, and
`drills/vector_store.py` now does it: the exact-against-approximate measurement
above is a real index over real vectors, because recall and latency depend on
the geometry of the points rather than on where they came from.

What remains blocked is the half where *learned* geometry matters, which is
every quality comparison. The drill's second half measures the boundary rather
than asserting it, and the table above records which properties survive the
substitution. What follows is how to run the part that does not.

**What you need.** The embedding setup from [embeddings](embeddings.md), plus
any vector store with an approximate index: FAISS or `hnswlib` locally, or a
hosted store if you want to measure network latency too. A corpus of at least a
few thousand chunks, since approximate indexes behave like exact ones on small
collections and the whole point is what happens when they stop.

**What you would run.** Index the same vectors twice, exactly and
approximately, then measure the agreement between them and the cost of each.

```python
exact  = numpy_bruteforce(vectors)            # ground truth, O(n) per query
approx = hnswlib.Index(space="cosine", dim=384)
approx.set_ef(ef)                             # the recall/latency dial
```

**What you would see.**

| Observation | Rough magnitude | What it tells you |
|---|---|---|
| Exact search, 10k chunks | single-digit milliseconds | Below ~100k chunks, exact is often fine |
| Approximate search | under a millisecond | The gain, which arrives later than people expect |
| Recall at `ef=10` against exact | 0.85 to 0.95 | Approximate means *wrong sometimes*, by design |
| Recall at `ef=200` | 0.99 or better | The dial, and what it costs in latency |
| Build time for the index | seconds to minutes | Why reindexing is an operational event |
| Hybrid lexical-plus-vector `hit@1` | better than either alone | The result this page exists to argue for |

The third row is the one to internalise: an approximate index returns the wrong
neighbour a measurable fraction of the time, and no amount of evaluation of your
*model* will reveal it, because the defect is in the index.

**The measurement that matters most.** Run a query whose answer depends on an
exact token, a flag name or an error code, and compare the three rankings:
lexical only, vector only, hybrid. Vector-only will often miss it entirely while
scoring something topically adjacent highly, which is the failure mode that
makes a demo look good and production look broken.

**How you would know it had failed.** A recall of exactly 1.0 at a low `ef`
means the corpus is too small for the approximate index to matter, so the
measurement is not testing anything. Identical results from lexical and vector
search mean one of the two is not actually running. And a latency figure that
does not change with `ef` means the dial is not wired to the query path.

## Related

- [Embeddings](embeddings.md), where the vectors come from and why they blur tokens
- [RAG pipelines](rag.md), the assembly this sits inside
- [Retrieval evaluation](retrieval-evaluation.md), how to decide fusion weights with data
- [Metadata for navigation and retrieval](metadata.md), what you filter on
