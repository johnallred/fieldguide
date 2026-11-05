---
title: RAG pipelines
summary: "Retrieve, assemble, generate: the architecture, and which stage is actually failing when the answer is wrong."
diataxis: explanation
audience: developer
concept: rag
tags: [ai, core]
---

# RAG pipelines

`core` · difficulty 3 · 8h

> Ways to stand out: experience building RAG pipelines, AI assistants, MCP servers, or agent skill and context libraries backed by documentation

> Source: nvidia posting, verbatim

**Prerequisites:** [Chunking strategies](chunking.md), [Vector stores and hybrid search](vector-stores.md)

**Leads to:** [Documentation-backed AI assistants](ai-assistants.md), [Grounding and citation](grounding.md), [Retrieval evaluation](retrieval-evaluation.md)

## What it is

Retrieval-augmented generation: look up relevant text, put it in the prompt,
and have a model answer from it. Three stages, and the whole discipline is in
knowing which one is broken when the answer is wrong.

The name oversells the novelty. It is search, with the results handed to a model
instead of to a person.

## Why the job asks for it

NVIDIA names it three times: "structure and package content for RAG", "RAG
pipelines" under ways to stand out, and implicitly in "internal assistants". It
is the single most-repeated technical artifact in either posting.

What makes it `core` and difficulty 3 is not the code, which is a few hundred
lines. It is that **a RAG pipeline has five distinct failure modes that all
present identically to a user**: a wrong answer. Diagnosing which one you have
is the job, and you can only do it if you built the stages separately and can
inspect each.

On a Tuesday this is the ticket. "The assistant told me to use `max_memory_mb`
and that flag does not exist." Five possible causes, in the order worth
checking:

1. The content does not exist. Nothing can fix this but writing.
2. It exists and was not chunked usefully, so no chunk contains the answer.
3. It was chunked and not retrieved, because the query and the page use
   different vocabulary.
4. It was retrieved and outranked by something adjacent.
5. It was retrieved, ranked first, and the model ignored it.

Those have five different fixes and four of them are not prompt changes. A team
that cannot tell them apart ends up tuning prompts against a retrieval problem,
which is the most common wasted quarter in this field.

## The golden path

Build the whole pipeline, dependency-free, then break each stage deliberately
and watch the same symptom appear. Fifty minutes.

**Step 1: the pipeline, with every stage inspectable**

```bash
mkdir -p rag-drill && cd rag-drill
cat > corpus.json <<'EOF'
[
  {"id": "c1", "source": "reference/flags.md", "crumb": "Server flags > batch_size",
   "kind": "reference",
   "text": "batch_size controls how many requests are grouped per forward pass. The default is 32. The maximum is 512."},
  {"id": "c2", "source": "how-to/latency.md", "crumb": "Reduce latency > Lower the batch size",
   "kind": "how-to",
   "text": "If your p99 is too high, set batch_size to 1 or 2. A batch of 32 waits for 32 requests to arrive, which adds roughly 200ms at p99."},
  {"id": "c3", "source": "reference/flags.md", "crumb": "Server flags > max_memory_gb",
   "kind": "reference",
   "text": "max_memory_gb caps the GPU memory the server will allocate. The default is 16. Size for peak load, not startup."},
  {"id": "c4", "source": "reference/legacy.md", "crumb": "Legacy 1.x flags > max_memory_mb",
   "kind": "reference",
   "text": "max_memory_mb was the 1.x equivalent of max_memory_gb. It was removed in 2.0 and is ignored if set."},
  {"id": "c5", "source": "explanation/batching.md", "crumb": "Why batching helps > Throughput",
   "kind": "explanation",
   "text": "A GPU is more efficient per item on a larger batch, so batching raises throughput at the cost of latency."}
]
EOF
python3 -c "import json; print(len(json.load(open('corpus.json'))), 'chunks')"
```

**Step 2: retrieve, assemble, generate, as three separable functions**

```bash
cat > rag.py <<'PY'
"""A RAG pipeline with every stage inspectable.

The structure is the lesson. `retrieve`, `assemble` and `generate` are
separate functions returning separate values, because the only way to debug a
wrong answer is to look at what each stage produced. A pipeline written as one
function that takes a question and returns a string cannot be debugged at all,
and that is how most of them are written.
"""
import json
import math
import re
from collections import Counter
from dataclasses import dataclass, field

K1, B = 1.2, 0.75
CONTEXT_BUDGET = 600  # characters, standing in for a token budget


def tokenize(text):
    # Underscores are kept so `max_memory_gb` survives as one term. Splitting
    # on them turns a flag name into three common words.
    return [t for t in re.findall(r"[a-z0-9_]+", text.lower()) if len(t) > 1]


@dataclass
class Trace:
    """What each stage did. The reason this class exists is diagnosis."""

    question: str
    retrieved: list = field(default_factory=list)
    assembled: str = ""
    dropped_for_budget: list = field(default_factory=list)
    answer: str = ""
    cited: list = field(default_factory=list)


class Retriever:
    def __init__(self, chunks):
        self.chunks = chunks
        self.docs = [Counter(tokenize(f"{c['crumb']} {c['text']}")) for c in chunks]
        self.lengths = [sum(d.values()) for d in self.docs]
        self.avg = sum(self.lengths) / len(self.docs)
        df = Counter()
        for d in self.docs:
            df.update(d.keys())
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - c + 0.5) / (c + 0.5)) for t, c in df.items()}

    def __call__(self, question, kind=None, limit=3):
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
        scored.sort(key=lambda s: -s[0])
        return scored[:limit]


def assemble(hits, budget=CONTEXT_BUDGET):
    """Build the context block, and record what did not fit.

    Two decisions matter here and both are usually invisible.

    The CITATION LABEL is attached per chunk, so the model can cite and a
    reader can verify. Without it, grounding is unenforceable.

    The BUDGET drops the lowest-ranked chunks, and `dropped` is returned
    rather than discarded, because "the answer was retrieved at rank 3 and
    then truncated away" is a real failure that looks like a retrieval
    failure.
    """
    blocks, dropped, used = [], [], 0
    for rank, (score, chunk) in enumerate(hits, start=1):
        block = (
            f"[{chunk['id']}] {chunk['crumb']}  (source: {chunk['source']})\n"
            f"{chunk['text']}"
        )
        if used + len(block) > budget and blocks:
            dropped.append((rank, chunk["id"]))
            continue
        blocks.append(block)
        used += len(block)
    return "\n\n".join(blocks), dropped


def generate(question, context):
    """Stand-in for a model, extractive and deterministic.

    It answers ONLY from the context and cites the chunk it used, which is
    the behaviour a real pipeline has to get a real model to approximate
    through prompting and then verify. Using a deterministic stand-in keeps
    this golden path reproducible and keeps the lesson on the pipeline.
    """
    if not context.strip():
        return "I could not find this in the documentation.", []

    terms = set(tokenize(question))
    best, best_score, best_id = None, 0, None
    for block in context.split("\n\n"):
        label = re.match(r"\[(\w+)\]", block)
        body = block.split("\n", 1)[-1]
        overlap = len(terms & set(tokenize(block)))
        if overlap > best_score:
            best, best_score, best_id = body, overlap, label.group(1) if label else None

    if not best:
        return "I could not find this in the documentation.", []
    sentence = best.split(". ")[0].strip().rstrip(".") + "."
    return f"{sentence} [{best_id}]", [best_id]


def ask(question, retriever, kind=None, budget=CONTEXT_BUDGET):
    trace = Trace(question=question)
    hits = retriever(question, kind=kind)
    trace.retrieved = [(round(s, 2), c["id"], c["crumb"]) for s, c in hits]
    trace.assembled, trace.dropped_for_budget = assemble(hits, budget)
    trace.answer, trace.cited = generate(question, trace.assembled)
    return trace


def show(trace):
    print(f"Q: {trace.question}")
    print("  retrieved:")
    for score, cid, crumb in trace.retrieved or [("-", "none", "")]:
        print(f"    {score:>5}  {cid}  {crumb}")
    if trace.dropped_for_budget:
        print(f"  dropped for budget: {trace.dropped_for_budget}")
    print(f"  answer: {trace.answer}")
    print(f"  cited:  {trace.cited}")
    print()


if __name__ == "__main__":
    retriever = Retriever(json.load(open("corpus.json")))
    for question in [
        "what is the default batch_size",
        "my p99 latency is too high",
        "what does max_memory_mb do",
    ]:
        show(ask(question, retriever))
PY
python3 rag.py
```

**Step 3: break each stage and watch the symptom stay the same**

This is the exercise. Five sabotages, one symptom.

```bash
cat > failures.py <<'PY'
"""Five failure modes, one symptom: a wrong or useless answer.

Each block below breaks exactly one stage, so the trace shows where the
pipeline lost the answer. In production you get only the last line of the
trace, which is why the trace has to exist.
"""
import json

from rag import Retriever, ask, show

corpus = json.load(open("corpus.json"))


def banner(text):
    print("=" * 72)
    print(text)
    print("=" * 72)


banner("0. BASELINE: the whole pipeline working")
show(ask("how do I cap GPU memory", Retriever(corpus)))

banner("1. CONTENT MISSING: the max_memory_gb chunk does not exist")
# Nothing downstream can recover from this. The answer is about batch_size.
show(ask("how do I cap GPU memory", Retriever([c for c in corpus if c["id"] != "c3"])))

banner("2. CHUNKING: the heading trail was discarded at split time")
# The word "latency" appears in c2's CRUMB, not in its text, which says "p99".
# Discard the crumb and the only chunk that answers the question becomes
# invisible to the query that asks it.
stripped = [dict(c, crumb="") for c in corpus]
print("  with the heading trail kept:")
show(ask("reduce latency", Retriever(corpus)))
print("  with the heading trail discarded:")
show(ask("reduce latency", Retriever(stripped)))

banner("3. RETRIEVAL VOCABULARY: the question says GPU, the page says VRAM")
reworded = [
    dict(c, text=c["text"].replace("GPU memory", "VRAM")) if c["id"] == "c3" else c
    for c in corpus
]
show(ask("how do I cap GPU memory", Retriever(reworded)))

banner("4. RANKING: a removed legacy flag outranks the current one")
# The dangerous one. Both chunks are retrieved; the wrong one is first.
show(ask("cap memory in mb", Retriever(corpus)))

banner("5. ASSEMBLY BUDGET: the correcting chunk is truncated away")
# Same query as 4. With a full budget the context contains BOTH the legacy
# flag and the current one, so a reranker, a better model or a reader could
# notice. With a tight budget the current flag is dropped and that chance is
# gone, while the answer looks identical.
for budget in (600, 190):
    print(f"  budget={budget}:")
    trace = ask("cap memory in mb", Retriever(corpus), budget=budget)
    show(trace)
    # Check for the CHUNK, not the string: c4's own text mentions
    # max_memory_gb in passing, so a substring test on the context passes
    # even when the current flag's documentation was dropped.
    print(f"    c3 (the current flag's page) in context: {'[c3]' in trace.assembled}")
    print()
PY
python3 failures.py
```

**Step 4: the one filter that fixes a whole class**

```bash
python3 - <<'PY'
import json

from rag import Retriever, ask, show

retriever = Retriever(json.load(open("corpus.json")))
# The question asks what to DO. Topically, the explanation page about
# throughput is the closest match, and it cannot answer that question.
question = "how do I handle throughput and latency"

print("--- unfiltered ---")
show(ask(question, retriever))

print("--- filtered to how-to, because the question asks what to DO ---")
show(ask(question, retriever, kind="how-to"))
PY
```

Unfiltered, the top result is the **explanation** chunk: "A GPU is more
efficient per item on a larger batch, so batching raises throughput at the cost
of latency." True, relevant, and not an answer to "how do I".

Filtered to `how-to`, the same corpus returns "If your p99 is too high, set
`batch_size` to 1 or 2."

**One metadata field turned a correct non-answer into an answer**, with no
change to the retriever, the corpus, or the prompt. That is the payoff for the
[content model](content-model.md), and it is failure mode 4 fixed structurally
rather than by reranking.

**What you built.** A pipeline whose every stage is inspectable, and a
demonstration that five different defects produce the same user-visible
symptom.

Run step 3 and read the traces rather than the answers. Here is what each
sabotage produced:

| # | Sabotage | What the user sees | What the trace shows |
|---|---|---|---|
| 1 | `max_memory_gb` chunk removed | An answer about `batch_size` | The right chunk is not in the ranked list because it does not exist |
| 2 | Heading trail discarded | An answer about GPU efficiency | `c2` vanishes from the list entirely: "latency" was only in its crumb |
| 3 | Page says VRAM, question says GPU | An answer about `batch_size` | `c3` scores zero; nothing relevant retrieved |
| 4 | None; ranking as it is | **"`max_memory_mb` was the 1.x equivalent"** | `c4` at 1.52 beats `c3` at 1.41. Both retrieved, wrong one first |
| 5 | Context budget 190 instead of 600 | Byte-identical answer to #4 | `c3` dropped for budget; the correcting chunk is gone |

Four observations worth taking from that table.

**Sabotage 2 is the sharpest.** The word "latency" appears in `c2`'s heading
trail and nowhere in its text, which says "p99". Discard the crumb at split
time and the only chunk that answers "reduce latency" becomes invisible to the
query that asks it. That is [chunking](chunking.md) deciding retrieval.

**Sabotage 4 is the dangerous one**, and nothing was sabotaged to produce it.
The pipeline, working as designed, tells a developer to use a flag that was
removed in 2.0. Both chunks were retrieved; the wrong one ranked first by 0.11.

**Sabotage 5 is invisible.** The answer is identical to #4's, and the trace
shows `c3` was retrieved and then truncated. With the full budget the context
contained both flags, so a reranker, a better model or a reader could have
noticed. At the tighter budget that chance is gone, and **nothing in the output
indicates anything was dropped.**

And: **the answer line alone cannot distinguish any of these.** The trace can.
That is the argument for building the stages separately, and it is most of what
separates a pipeline you can operate from one you can only restart.

## Reference

### The three stages and what each owns

| Stage | Input | Output | Owns |
|---|---|---|---|
| **Retrieve** | question, filters | ranked chunks | Recall. If the answer is not here, nothing downstream helps |
| **Assemble** | ranked chunks | a context block | Budget, ordering, citation labels, deduplication |
| **Generate** | question, context | answer, citations | Faithfulness to the context |

The middle stage is the one people skip and it causes the subtlest bugs:
truncation, duplicate chunks from one page crowding out variety, and lost
citation labels that make [grounding](grounding.md) unenforceable.

### The five failure modes, and what actually fixes each

| # | Failure | Symptom | Fix |
|---|---|---|---|
| 1 | Content does not exist | Confident wrong answer, or a refusal | Write the page. Nothing else |
| 2 | Chunked badly | Retrieval finds the page, answer is incomplete | [Heading-aware chunking](chunking.md) |
| 3 | Vocabulary mismatch | Nothing relevant retrieved | [Hybrid search](vector-stores.md), or write the reader's words |
| 4 | Outranked | Plausible neighbour returned instead | Fusion, reranking, [metadata filters](metadata.md) |
| 5 | Model ignored the context | Answer contradicts a retrieved chunk | Prompting, then [output evaluation](output-evaluation.md) |

**Four of the five are not prompt problems.** The instinct when a RAG answer is
wrong is to edit the prompt, and it is the right move about twenty percent of
the time.

### Diagnosing in order

| Question | How to answer it |
|---|---|
| Does the content exist at all? | Grep the corpus. Do this first; it is free |
| Is it in a chunk, whole? | Search your chunk store for the fact, not the page |
| Was the chunk retrieved? | Log the ranked list for every query. Non-negotiable |
| At what rank? | Rank 4 with a top-3 cutoff looks identical to not retrieved |
| Did it survive assembly? | Log the dropped-for-budget list |
| Did the answer use it? | Require citations and check them mechanically |

**Log the ranked list.** A RAG system without retrieval logs cannot be debugged,
and adding them later means losing the traffic you needed.

### Things that matter more than they look

| Decision | Why |
|---|---|
| Citation labels per chunk | Enables [grounding](grounding.md) checks and lets a reader verify |
| Deduplicate by source page | Three chunks from one page is less useful than three pages |
| Context ordering | Models weight the start and end of a long context more heavily |
| A refusal path | "Not in the documentation" must be an available answer |
| Filter before ranking | A hard constraint, not a hope. See [vector stores](vector-stores.md) |
| Return the source path | The reader needs somewhere to go, and you need to spot bad pages |

### What RAG does not fix

| Claim | Reality |
|---|---|
| "It stops hallucination" | It reduces it. A model can still contradict its context |
| "It keeps answers current" | Only if the index is rebuilt. A stale index is a confident liar |
| "It replaces writing" | Failure mode 1 is unfixable by any amount of engineering |
| "It replaces search" | It *is* search, with the results read aloud |
| "More chunks is better" | Past a point, relevant content gets diluted |

The second row is the one that causes incidents: an index built in March
answering questions in September, with nothing in the answer indicating its
age. A freshness field in the chunk metadata is cheap insurance.

## How to talk about it

**What a competent answer sounds like.** Lead with diagnosis, not architecture.
Everyone can draw the three boxes. "When a RAG answer is wrong there are five
candidates, and they look identical to the user: the content does not exist, it
was chunked badly, it was not retrieved, it was retrieved and outranked, or the
model ignored it. Four of those are not prompt problems. So I log the ranked
retrieval list and what got dropped for context budget on every query, because
without those two logs the only available debugging move is guessing."

**The follow-up is "how do you know it is working",** which is
[retrieval evaluation](retrieval-evaluation.md) and is where most teams have
nothing. The honest answer: a golden set of questions with their expected source
pages, scored on whether the right page came back and at what rank, run in CI.
And the number you must have next to it is the lexical baseline, because a dense
pipeline that scores worse than BM25 is a quarter spent going backwards.

**The tradeoff to volunteer.** RAG converts a search problem you could inspect
into a generation problem you cannot. A search results page is honest: the
reader sees five results and judges them. A generated answer hides the ranking,
so a confidently wrong synthesis of two half-relevant chunks reads exactly like
a correct answer. You have improved the experience and removed the user's
ability to notice you were wrong, which is why citations are not a nicety and
why a refusal path has to exist.

**One sharper point.** The strongest framing for a documentation role is that
**RAG makes your content quality legible for the first time.** Failure mode 1 is
unfixable by engineering, and a RAG system is an excellent detector for it: the
questions it answers badly are the pages you have not written or have written in
the wrong vocabulary. Teams treat a bad RAG answer as a model problem; it is
usually a content report, delivered in the reader's own words, for free. Pointing
that out reframes the whole project from an AI initiative into a documentation
gap analysis, which is a much better pitch to a documentation lead and happens
to be true.

## How to prove it

**The artifact.** A pipeline with a trace object, plus the five-failure
demonstration. The trace is what makes it look like something you operate rather
than something you assembled.

**Three things to do, in order:**

1. **Run the golden path, especially step 3.** Five sabotages producing one
   symptom is the most persuasive five minutes available on this topic.
2. **Add retrieval logging to anything you build.** The ranked list and the
   dropped-for-budget list, per query. Ten lines, and it is the difference
   between operating the system and restarting it.
3. **Use the pipeline as a content audit.** Ask it thirty real questions and
   sort the failures by the five modes. The count in mode 1 is a documentation
   backlog in the reader's words, and presenting it as such is the move that
   makes this work visible to people who do not care about retrieval. Predict
   the distribution first. If mode 1 is not the largest, your corpus is in
   better shape than most and the retrieval configuration is where to look.

**What makes it credible rather than decorative.** A working RAG demo is now a weekend project and
proves little. A trace object, a five-mode taxonomy with a worked example of
each, and a lexical baseline next to your retrieval numbers demonstrates that
you have debugged one rather than built one.

## Related

- [Grounding and citation](grounding.md), making the answer checkable
- [Retrieval evaluation](retrieval-evaluation.md), how you know it works
- [Documentation-backed AI assistants](ai-assistants.md), this wrapped in a product
- [Chunking strategies](chunking.md), where failure mode 2 lives
