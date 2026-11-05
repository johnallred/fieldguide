---
title: Embeddings
summary: Turning text into vectors so similar meaning lands nearby, and knowing what that buys and costs.
diataxis: explanation
audience: developer
concept: embeddings
tags: [ai, core]
---

# Embeddings

`core` · difficulty 2 · 4h

!!! note "Not a quotation (derived)"
    Required by any RAG pipeline, and NVIDIA names RAG pipelines twice.

**Prerequisites:** [Chunking strategies](chunking.md)

**Leads to:** [Vector stores and hybrid search](vector-stores.md)

## What it is

A function from text to a fixed-length list of numbers, trained so that text
with similar meaning produces vectors that are close together. Closeness is
usually cosine similarity, which is the angle between two vectors.

That is the whole idea. Everything interesting is in what "similar meaning"
turns out to mean in practice, which is not always what you want.

## Why the job asks for it

Neither posting says "embeddings", which is why this is tagged `derived`.
NVIDIA asks for RAG pipelines twice, and there is no RAG pipeline without an
embedding step, so the inference is safe.

What makes this `core` rather than a detail is that embeddings are where
**documentation people usually stop understanding their own system.** The
chunker is readable code. The vector store is a database. The embedding model is
a black box that turns text into 1,536 numbers, and the temptation is to treat
it as magic and move on. That is how you end up unable to explain why your
assistant returned the wrong page.

On a Tuesday it is a diagnosis. An assistant answered a question about
*deprecating* a flag using the page about *adding* one. Lexical search would
never have made that mistake, because the words differ. The embedding made it
because the two pages are semantically adjacent: same subject, same vocabulary,
opposite instruction. **Embeddings capture topic much better than they capture
polarity**, and knowing that is the difference between fixing it and blaming the
model.

## The golden path

Embed a small corpus with a real model, see where similarity helps, and find a
case where it fails. Forty minutes.

!!! warning "This one needs network access"
    Steps 2 to 4 download model weights from `huggingface.co` on first run,
    roughly 90 MB. Unlike every other golden path in this guide, it will not
    run in an environment that blocks that host, and the author verified the
    arithmetic in step 0 rather than the model steps for exactly that reason.
    If you are behind a restrictive proxy, do step 0 here and steps 2 to 4 on
    a machine with access.

**Step 0: confirm the one piece of arithmetic that matters**

Everything in this page rests on cosine similarity equalling a dot product once
vectors are normalised. That is checkable with no model and no network, and it
is worth seeing once so the rest stops being magic.

```bash
mkdir -p embed-drill && cd embed-drill
python3 - <<'PY'
import math

def dot(a, b):
    return sum(x * y for x, y in zip(a, b))

def norm(v):
    return math.sqrt(dot(v, v))

def cosine(a, b):
    return dot(a, b) / (norm(a) * norm(b))

def unit(v):
    n = norm(v)
    return [x / n for x in v]

a = [3.0, 1.0, 0.0, -2.0]
b = [1.5, 0.5, 1.0, -1.0]

print(f"cosine(a, b)            = {cosine(a, b):.6f}")
print(f"dot(unit(a), unit(b))   = {dot(unit(a), unit(b)):.6f}")
print(f"identical?                {abs(cosine(a, b) - dot(unit(a), unit(b))) < 1e-12}")
print()
print(f"norm of a unit vector   = {norm(unit(a)):.6f}")
print(f"cosine(a, a)            = {cosine(a, a):.6f}   (a vector is identical to itself)")
print(f"cosine(a, [-x for x in a]) = {cosine(a, [-x for x in a]):.6f}   (opposite direction)")
PY
```

That is why every vector store normalises at write time: it turns similarity
into one multiply-add per dimension, with no division and no square roots at
query time.

**Step 1: install a local embedding model**

```bash
mkdir -p embed-drill && cd embed-drill
python3 -m venv .venv && source .venv/bin/activate
pip install --quiet "sentence-transformers>=3.0"
python -c "import sentence_transformers; print(sentence_transformers.__version__)"
```

`all-MiniLM-L6-v2` is 384 dimensions, runs on a CPU in milliseconds, and needs
no API key. Good enough to learn on and good enough for a lot of production
documentation search.

**Step 2: embed the chunks and look at the actual numbers**

```bash
cat > embed.py <<'PY'
"""Embed a handful of documentation chunks and inspect the result."""
import json

from sentence_transformers import SentenceTransformer

CHUNKS = [
    "Set batch_size on the client. The default is 32.",
    "If latency matters, use a batch size of 1 or 2.",
    "Size memory for peak load, not for startup.",
    "Run pip install widget to install the CLI.",
    "Exit code 2 means the arguments were invalid.",
    "Exactly-once delivery requires distributed transactions.",
]

model = SentenceTransformer("all-MiniLM-L6-v2")
vectors = model.encode(CHUNKS, normalize_embeddings=True)

print(f"model dimensions: {vectors.shape[1]}")
print(f"one vector, first 8 of {vectors.shape[1]}:")
print(f"  {[round(float(x), 4) for x in vectors[0][:8]]}")
print(f"norm after normalisation: {float((vectors[0] ** 2).sum()) ** 0.5:.4f}")

with open("vectors.json", "w") as f:
    json.dump({"chunks": CHUNKS, "vectors": vectors.tolist()}, f)
print(f"\nwrote {len(CHUNKS)} vectors")
PY
python3 embed.py
```

Normalising at encode time is worth understanding: once every vector has length
1, cosine similarity is just the dot product, which is one multiply-add per
dimension and no division. Every vector store does this.

**Step 3: see what similarity actually ranks**

```bash
cat > search.py <<'PY'
"""Rank chunks against queries by cosine similarity."""
import json

from sentence_transformers import SentenceTransformer

data = json.load(open("vectors.json"))
chunks, vectors = data["chunks"], data["vectors"]

model = SentenceTransformer("all-MiniLM-L6-v2")

QUERIES = [
    "my p99 latency is too high",          # no shared words with the answer
    "how do I install it",
    "it ran out of memory in production",
    "what does the argument error mean",
]


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


for query in QUERIES:
    q = model.encode([query], normalize_embeddings=True)[0].tolist()
    scored = sorted(
        ((dot(q, v), c) for v, c in zip(vectors, chunks)), reverse=True
    )
    print(f"\nQ: {query}")
    for score, chunk in scored[:2]:
        print(f"   {score:.3f}  {chunk}")
PY
python3 search.py
```

Look at the first query. "my p99 latency is too high" shares **no words** with
"If latency matters, use a batch size of 1 or 2" except "latency", and it ranks
first on meaning rather than overlap. That is what embeddings buy, and lexical
search cannot do it.

**Step 4: find where it fails, which is the part worth your time**

```bash
cat > failure.py <<'PY'
"""Two failure modes that matter for documentation.

Neither is a bug. Both are consequences of what the training objective
rewards, and both are invisible unless you look for them.
"""
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")


def similarity(a, b):
    v = model.encode([a, b], normalize_embeddings=True)
    return float(sum(x * y for x, y in zip(v[0], v[1])))


print("=== 1. negation and polarity ===")
pairs = [
    ("Enable the cache with cache=True.",
     "Disable the cache with cache=False."),
    ("This flag is supported in version 2.",
     "This flag is deprecated in version 2."),
    ("Retries are safe because writes are idempotent.",
     "Retries are unsafe because writes are not idempotent."),
]
for a, b in pairs:
    print(f"  {similarity(a, b):.3f}  opposite instructions")
    print(f"         {a}")
    print(f"         {b}")

print("\n=== 2. exact identifiers ===")
checks = [
    ("max_memory_gb", "max_memory_mb"),
    ("widget-server", "widget-client"),
    ("error code 2", "error code 3"),
]
for a, b in checks:
    print(f"  {similarity(a, b):.3f}  {a!r} vs {b!r}")

print("\nHigh scores in both sections are the problem, not the reassurance.")
PY
python3 failure.py
```

**What you built.** A working embedding search, a demonstration of the thing it
does that lexical search cannot, and two measured failure modes.

Run step 4 and read the numbers before continuing, and do not take this page's
word for the result. The expected finding is that opposite instructions score
high, often above 0.8, and that `max_memory_gb` against `max_memory_mb` scores
very high. **Those similarities are the reason
[hybrid search](vector-stores.md) exists**, and the reason a documentation
corpus should never rely on embeddings alone: a version number, a flag name and
a negation are exactly the things a developer's question turns on, and exactly
the things embeddings blur.

The numbers are not quoted here on purpose. They vary by model, and a page that
printed them would be asserting a result the reader should measure on their own
vocabulary. Step 4 of "how to prove it" below is where that matters.

## Reference

### Vocabulary

| Term | Meaning |
|---|---|
| Embedding | The vector produced from a piece of text |
| Dimensions | Length of the vector. 384 to 3,072 typical |
| Cosine similarity | Angle between vectors, in [-1, 1]. The usual metric |
| Dot product | Equals cosine similarity when both vectors are normalised |
| Normalisation | Scaling a vector to length 1, so similarity is one dot product |
| Bi-encoder | Query and document embedded independently. Fast, indexable |
| Cross-encoder | Query and document scored together. Accurate, cannot be pre-indexed |
| Reranker | Usually a cross-encoder, applied to the top k from a fast search |
| Context window | Maximum tokens the model embeds. Text beyond it is truncated silently |

### Choosing a model

| Consideration | What to look at |
|---|---|
| Dimensions | More is not better. 384 is often enough and is four times cheaper to store |
| Context window | Must exceed your largest chunk, or the tail is silently dropped |
| Asymmetric support | Some models embed queries and documents differently; use the prefixes they ask for |
| Local or hosted | Local means no key, no per-call cost, and no data leaving. Hosted means less to run |
| Reproducibility | Pin the version. A model update silently changes every vector you have stored |

That last row causes real incidents. A hosted model updated under you makes new
vectors incomparable with stored ones, and the symptom is retrieval quality
degrading for no visible reason.

### What embeddings are good and bad at

| Good at | Bad at |
|---|---|
| Paraphrase: "latency too high" finding "use 1 or 2" | Negation: supported against deprecated |
| Synonyms: "repo" finding "repository" | Exact identifiers: `max_memory_gb` against `max_memory_mb` |
| Vocabulary mismatch between reader and author | Numbers and versions: "2.4" against "2.3" |
| Topic similarity | Polarity: enable against disable |
| Short queries with no keyword overlap | Rare terms that appear once in the corpus |

**The right column is most of what a developer question is made of.** This table
is the single most useful thing on this page.

### The practical consequences

| Consequence | What to do |
|---|---|
| Embeddings alone will confuse opposites | [Hybrid search](vector-stores.md): combine with BM25 |
| Identifiers need exact matching | Keep a lexical index; never go vector-only |
| Chunks longer than the context window are truncated | Cap chunk size below it, deliberately |
| A model change invalidates your index | Pin the version; re-embed on purpose, never by surprise |
| Similarity scores are not comparable across queries | Never threshold on an absolute score |

### Cost, concretely

For a 5,000-page corpus at roughly 8 chunks per page:

| Item | Scale |
|---|---|
| Chunks | ~40,000 |
| Storage at 384 dimensions, float32 | ~60 MB |
| Storage at 1,536 dimensions, float32 | ~245 MB |
| Local embedding on a CPU | minutes, free |
| Hosted embedding | cents to a few dollars, once |
| Re-embedding on every commit | the thing [stable chunk ids](chunking.md) prevent |

Embedding is cheap. **Re-embedding carelessly is what costs**, which is why
chunk identity is a design decision rather than an implementation detail.

## How to talk about it

**What a competent answer sounds like.** Lead with the failure modes, because
everyone can describe what embeddings do and far fewer can say where they break.
"They buy you paraphrase matching, so a question about high p99 latency finds a
chunk that never uses the word 'performance'. What they do not buy is polarity
or exact identifiers: 'supported in version 2' and 'deprecated in version 2'
embed close together, and `max_memory_gb` and `max_memory_mb` are nearly
identical vectors. Since developer questions turn on exactly those things, I
would not ship vector-only search over a documentation corpus."

**The follow-up is "so which model and how many dimensions",** and the useful
answer resists the premise. Start with a small local model, because it is free
and fast enough to iterate with, and let an
[evaluation set](retrieval-evaluation.md) tell you whether a bigger one helps.
More dimensions cost storage and latency on every query forever; the gain is
usually small on a documentation corpus and is sometimes zero. The point is that
this is a measurable question and should not be answered from a blog post.

**The tradeoff to volunteer.** Adding embeddings makes retrieval better at the
queries you cannot anticipate and worse at being debuggable. A BM25 result is
explainable: these terms matched, with these weights. A vector result is a number
with no account of itself, and when it is wrong the only available fix is
changing the inputs and hoping. That loss of debuggability is a real cost in a
documentation system, where you will be asked *why* the assistant said something.

**One sharper point.** The strongest observation is that **embeddings fix a problem
documentation teams can also fix with writing.** The gap embeddings close is
between the reader's vocabulary and the author's. You can also close it by
writing summaries and headings in the reader's words, which is free, improves
the page for humans, helps lexical search too, and does not degrade when a model
is updated. Embeddings are the right tool when you cannot anticipate the
vocabulary; they are an expensive substitute for writing when you can. Saying
that in an interview for a documentation role lands well, because it is the
documentation-specific insight rather than the generic ML one.

## How to prove it

**The artifact.** A working local embedding search and a measured table of its
failure modes on your own corpus's vocabulary.

**Three things to do, in order:**

1. **Run the golden path, especially step 4.** Then redo step 4 with
   **identifiers from your own product**: your flag names, your version numbers,
   your enable/disable pairs. The numbers are usually worse than the generic
   examples and far more persuasive.
2. **Find a real confusion.** Embed your corpus, query it with ten real
   questions, and find one case where a semantically adjacent chunk beats the
   correct one. That single example is the whole argument for hybrid search.
3. **Pin the model version and write down why.** One line in a README about a
   model update invalidating a stored index demonstrates operational
   understanding that most candidates lack.

**What makes it credible rather than decorative.** Describing cosine similarity proves nothing. A
measured table showing that your product's own flag names embed nearly
identically, and a stated conclusion that you would not ship vector-only search
because of it, demonstrates that you tested the tool rather than adopted it.

### How this would be demonstrated elsewhere

Nothing on this page was run. This environment has no model access and the
package network allows registries only, so no weights can be fetched. What
follows is what the demonstration needs, what you would run, and what you would
see, so that the gap is a specification rather than an absence.

**What you need.** A machine with roughly 2 GB free and any sentence-embedding
model small enough to run on CPU; a 384-dimension MiniLM-class model is the
usual choice and takes a few hundred megabytes. No GPU. No API key, if the model
is local. The whole demonstration is about one afternoon.

**What you would run.** Embed every heading-bounded chunk of a corpus you own,
then embed a set of real reader questions, then score each question against
every chunk by cosine similarity and record where the correct chunk ranked.

```python
vectors = model.encode([chunk.text for chunk in chunks], normalize_embeddings=True)
query = model.encode([question], normalize_embeddings=True)
scores = vectors @ query.T          # cosine, because both are normalised
```

**What you would see, and what each number means.**

| Observation | Rough magnitude | What it tells you |
|---|---|---|
| Cosine between a chunk and a paraphrase of it | 0.75 to 0.9 | The model is doing its job |
| Cosine between two unrelated chunks | 0.1 to 0.4, rarely near 0 | Why a raw similarity threshold is a bad filter |
| Cosine between `--dry-run` and `--no-commit` | 0.8 or higher | The failure this page is really about |
| Cosine between a question and its answer chunk | Often *lower* than between two chunks | Questions and statements are different registers |
| `hit@1` against a lexical baseline | Better on paraphrases, worse on exact names | Why hybrid search exists |

The fourth row is the one that surprises people and the reason an evaluation
set matters more than a model choice: a question is phrased unlike its answer,
so the nearest neighbour of a question is often another question.

**The measurement that justifies the page's claim.** Take fifteen of your own
product's flag, field or endpoint names, embed them, and print the pairwise
similarity matrix. On most corpora you will find several pairs above 0.85 whose
meanings are opposites, because they share surrounding vocabulary and differ by
one token the tokeniser barely registers. That table is the artifact. The
conclusion that follows, that you would not ship vector-only retrieval over a
corpus whose distinguishing terms are near-identical, is the judgment the table
buys you.

**How you would know it had failed rather than surprised you.** Three
signatures. Unnormalised vectors make every cosine implausibly high, usually
above 0.9 for everything, so check that the norms are 1.0 before believing any
score. A model loaded with the wrong pooling returns near-identical vectors for
every input, which shows up as a similarity matrix that is uniform rather than
merely high. And if `hit@1` is at chance level, the chunk order and the vector
order have come apart, which is an indexing bug rather than a model result.

## Related

- [Chunking strategies](chunking.md), what gets embedded
- [Vector stores and hybrid search](vector-stores.md), where the vectors live and how to fix the gaps
- [RAG pipelines](rag.md), the assembly this is one stage of
- [Retrieval evaluation](retrieval-evaluation.md), how to settle the model question with data
