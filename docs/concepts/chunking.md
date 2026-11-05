---
title: Chunking strategies
summary: Splitting a corpus into retrieval units without destroying the context that makes them findable.
diataxis: explanation
audience: developer
concept: chunking
tags: [ai, core]
---

# Chunking strategies

`core` · difficulty 3 · 5h

> structure and package content for RAG, internal assistants, and agentic workflows

> Source: nvidia posting, verbatim

**Prerequisites:** [Agent-ready content](agent-ready-content.md)

**Leads to:** [Embeddings](embeddings.md)

## What it is

Splitting documents into the units a retrieval system stores and returns. The
unit is what gets embedded, ranked, and handed to a model, so the chunk boundary
decides what an assistant can possibly know in one answer.

The entire difficulty is that **splitting destroys context**, and the context it
destroys is usually the thing that made the text findable.

## Why the job asks for it

NVIDIA asks you to "structure and package content for RAG", which is this. It
is the lowest-level decision in the whole AI-ready stack and the one that
constrains everything above it: no reranker recovers information the chunker
threw away.

On a Tuesday it is a debugging question with three possible answers. An
assistant gave a developer the wrong batch-size advice. Either the right chunk
was never retrieved, or it was retrieved and outranked, or **it was retrieved
and did not contain enough to answer**. The third case is a chunking failure and
it is the most common one, because it looks like a model problem.

The reason it is `core` and difficulty 3: the naive implementation is four lines
and is wrong in ways that are invisible until you measure. Fixed-size windows
over Markdown produce chunks that split a table from its header, a command from
its explanation, and a heading from the text it introduces. Each of those
degrades retrieval quietly.

## The golden path

Build a fixed-size chunker and a heading-aware one, then measure the difference
on the same queries. Forty-five minutes.

**Step 1: a document with the structures that break naive chunking**

````bash
mkdir -p chunk-drill && cd chunk-drill
cat > page.md <<'EOF'
# Configure the inference server

The server reads configuration from `server.toml` at startup.

## Batch size

Set `batch_size`. The default is 32.

If latency matters, use 1 or 2. Batching at 32 adds roughly 200ms at p99.

## Memory limits

| Flag | Default | Description |
|---|---|---|
| `max_memory_gb` | 16 | Hard ceiling before the server refuses to load |
| `reserve_gb` | 2 | Held back for the runtime itself |

Size for peak, not for startup. The common failure is an out-of-memory error
under load, which passes a smoke test and fails in production.

## Starting the server

Run this:

```bash
# start the server in the foreground
widget-server --config server.toml
```

The server prints its listening address and blocks.
EOF
wc -c page.md
````

That document contains all four hazards: a table, a fenced code block with a
`#` comment inside it, headings that state what is below them, and prose that
depends on the heading for meaning.

**Step 2: the naive chunker, which is what most people ship**

```bash
cat > naive.py <<'PY'
"""Fixed-size chunking with overlap. Four lines of logic, widely deployed."""
import json
import sys
from pathlib import Path

SIZE = 200
OVERLAP = 40


def main(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start:start + SIZE])
        start += SIZE - OVERLAP

    records = [{"id": f"naive-{i}", "text": c} for i, c in enumerate(chunks)]
    Path("naive.jsonl").write_text(
        "\n".join(json.dumps(r) for r in records) + "\n"
    )
    print(f"{len(records)} chunks of {SIZE} chars with {OVERLAP} overlap")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
PY
python3 naive.py page.md
```

**Step 3: look at what it did, which is the whole argument**

```bash
cat > damage.py <<'PY'
"""Report what the window broke, rather than asserting that it broke things."""
import json
import re

rows = [json.loads(line) for line in open("naive.jsonl")]
print("=== damage report ===")
for r in rows:
    text = r["text"]
    problems = []
    if text.count("```") % 2 == 1:
        problems.append("unbalanced code fence")
    if "|---|" in text and "| Flag" not in text:
        problems.append("table header separated from its rows")
    elif re.search(r"^\| `", text, re.M) and "| Flag" not in text:
        problems.append("table rows with no header")
    if not re.match(r"^\s*(#|\||```|[A-Z])", text):
        problems.append("starts mid-sentence")
    if not re.search(r"^#{1,6} ", text, re.M):
        problems.append("no heading anywhere in the chunk")
    print(f"  {r['id']}: {', '.join(problems) if problems else 'intact'}")
PY
python3 damage.py
```

One chunk in five survives. Two have no heading at all, which means nothing in
them says what they are about. One carries table rows with no column names, so
a model reading it sees `16` and `2` with no idea what they measure. One ends
having opened a code fence it never closes.

**None of that is visible in a retrieval score.** It shows up as an assistant
that is vaguely unreliable.

**Step 4: the heading-aware chunker**

Two things make it different: it tracks fence state, and it keeps the heading
trail with every chunk.

```bash
cat > aware.py <<'PY'
"""Heading-aware chunking that survives Markdown.

Two decisions carry all the value.

FENCE STATE. A `#` inside a fenced code block is a shell comment, not a
heading. Without tracking fences, `# start the server in the foreground`
becomes an H1 and the document structure collapses from that point on. This
is the bug every naive implementation has.

THE HEADING TRAIL travels with the chunk. A heading is an author's explicit
statement of what the text below is about, which makes it the single most
valuable retrieval signal in the document, and a splitter that drops it
throws away the best thing it had.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

HEADING = re.compile(r"^(#{1,6}) +(.*?)\s*$")
FENCE = re.compile(r"^\s*(```|~~~)")
MAX_CHARS = 1200


def stable_id(source: str, trail: tuple[str, ...], ordinal: int) -> str:
    """Identify a chunk by where it is in the document, not by byte offset.

    Position-based ids change for every chunk after an edit, which forces a
    full re-index for a one-word fix. Deriving from the heading trail means
    editing the introduction leaves every other chunk's id alone.
    """
    basis = f"{source}::{'/'.join(trail)}::{ordinal}"
    return hashlib.sha256(basis.encode()).hexdigest()[:16]


def chunk(text: str, source: str):
    trail: list[str] = []
    buffer: list[str] = []
    in_fence = False
    out = []

    def flush():
        body = "\n".join(buffer).strip()
        if not body:
            return
        # Oversized sections split on blank lines, keeping the same trail, so
        # a long section degrades to several chunks that still know where
        # they came from.
        parts, current = [], []
        length = 0
        for para in body.split("\n\n"):
            if length + len(para) > MAX_CHARS and current:
                parts.append("\n\n".join(current))
                current, length = [], 0
            current.append(para)
            length += len(para)
        if current:
            parts.append("\n\n".join(current))
        for ordinal, part in enumerate(parts):
            crumb = tuple(trail)
            out.append({
                "id": stable_id(source, crumb, ordinal),
                "source": source,
                "breadcrumb": " > ".join(crumb),
                "text": part,
            })

    for line in text.splitlines():
        if FENCE.match(line):
            in_fence = not in_fence
            buffer.append(line)
            continue
        match = None if in_fence else HEADING.match(line)
        if match:
            flush()
            buffer = []
            depth = len(match.group(1))
            trail = trail[: depth - 1] + [match.group(2)]
        else:
            buffer.append(line)
    flush()
    return out


def main(path: Path) -> None:
    rows = chunk(path.read_text(encoding="utf-8"), path.name)
    Path("aware.jsonl").write_text(
        "\n".join(json.dumps(r, sort_keys=True) for r in rows) + "\n"
    )
    print(f"{len(rows)} chunks")
    for r in rows:
        print(f"  [{len(r['text']):>4}] {r['breadcrumb']}")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
PY
python3 aware.py page.md
```

**Step 5: measure, do not assert**

```bash
cat > compare.py <<'PY'
"""Score both chunkers on the same queries.

The queries are phrased the way a reader would ask, which is the only fair
test: a query lifted from the document's own headings proves nothing except
that string matching works.
"""
import json
import re

QUERIES = [
    ("how do I reduce latency", "Batch size"),
    ("what is the memory ceiling", "Memory limits"),
    ("how do I start the server", "Starting the server"),
    ("what is the default batch size", "Batch size"),
    ("why did it run out of memory under load", "Memory limits"),
]


def load(path):
    return [json.loads(line) for line in open(path)]


def score(rows, query, expect, use_breadcrumb):
    terms = [t for t in re.findall(r"[a-z]+", query.lower()) if len(t) > 2]
    best, best_hit = 0, None
    for row in rows:
        hay = row["text"].lower()
        if use_breadcrumb:
            hay = f"{row.get('breadcrumb', '')} {hay}".lower()
        hits = sum(1 for t in terms if t in hay)
        if hits > best:
            best, best_hit = hits, row
    if not best_hit:
        return False, "no match"
    where = best_hit.get("breadcrumb") or best_hit["text"][:40].replace("\n", " ")
    return expect.lower() in where.lower(), where


for label, path, use_crumb in [
    ("naive (fixed 320c)", "naive.jsonl", False),
    ("heading-aware", "aware.jsonl", True),
]:
    rows = load(path)
    correct = 0
    print(f"\n{label}: {len(rows)} chunks")
    for query, expect in QUERIES:
        ok, where = score(rows, query, expect, use_crumb)
        correct += ok
        print(f"  {'OK ' if ok else '   '} {query:<42} -> {where[:46]}")
    print(f"  {correct}/{len(QUERIES)} correct")
PY
python3 compare.py
```

**What you built.** Two chunkers and a score. On this page, with these five
reader-phrased queries, the result is **0 of 5 for the fixed-size chunker and 4
of 5 for the heading-aware one.**

Two honest notes about that comparison, because an unqualified 0 against 4
would be overselling it.

**The scoring is asymmetric, and that asymmetry is the finding.** The
heading-aware chunks are judged by their breadcrumb; the naive ones have no
breadcrumb, so they are judged by their opening characters. That is not a rigged
test, it is the actual situation: **a fixed-size chunk cannot tell you which
section it came from, because that information was discarded at split time.**
There is nothing to be fair to.

**The heading-aware chunker misses one.** "How do I start the server" routes to
the page introduction rather than to the `Starting the server` section, because
the word "server" appears heavily in the intro and crude term overlap rewards
that. A real retriever with inverse document frequency would weight "server"
down across this document and probably get it right. The miss is worth keeping
in the output: a method that scores 5 of 5 on its author's own five queries has
usually been tuned to them.

## Reference

### What fixed-size chunking destroys

| Destroyed | Consequence |
|---|---|
| The heading above the text | The strongest statement of what the text is about |
| A table's header row | Rows of numbers with no column names |
| A code fence's opening | A chunk ending mid-block, and a model that invents the rest |
| The sentence boundary | A chunk starting with "If latency matters, use" |
| Document position | Nothing tells the model where in the corpus this came from |

Overlap mitigates the sentence boundary and nothing else. It is widely treated
as the fix for all five.

### The fence bug

Every naive Markdown chunker has it. A `#` at the start of a line inside a
fenced block is a shell comment:

````markdown
```bash
# start the server in the foreground
widget-server --config server.toml
```
````

A splitter that matches `^#` without tracking fence state treats that comment as
an H1, and every chunk after it inherits a wrong heading trail. The symptom is
bizarre breadcrumbs appearing in retrieval results, and it is often misdiagnosed
as an embedding problem.

### Strategies, and when each is right

| Strategy | Use when | Cost |
|---|---|---|
| Fixed-size with overlap | The corpus is unstructured prose | Destroys structure; the baseline to beat |
| Heading-aware | Markdown, RST, HTML with real headings | Sections vary wildly in size |
| Heading-aware with a size cap | Documentation. This is the default worth starting from | Slightly more code |
| Semantic or embedding-based splitting | Prose with no structural markers | Expensive, non-deterministic, hard to debug |
| One chunk per page | Short pages, or a small corpus | Poor precision; the model gets a lot of irrelevance |
| Sentence-window | Precise fact lookup | Loses the surrounding argument |

For a documentation corpus, heading-aware with a size cap is correct nearly
always, and the interesting decisions are the cap and what carries with each
chunk.

### What should travel with every chunk

| Field | Why |
|---|---|
| The heading trail | Context, and often the only place the query's vocabulary appears |
| Source path | Citation, and the reader needs somewhere to go |
| Page type ([Diátaxis](diataxis.md)) | So a retriever can filter by the kind of answer required |
| Audience | Same, for [multi-audience corpora](partner-documentation.md) |
| The page summary | Often the closest text in the corpus to how a reader phrases things |
| A freshness date | So a consumer can discount stale content |
| A stable id | So an edit does not force a full re-index |

### Stable identifiers

An id derived from byte offset changes for every chunk after an edited
paragraph. An id derived from the heading trail plus an ordinal within the
section changes only for the section you edited.

On a corpus of a few hundred pages that is the difference between re-embedding
everything on each commit and re-embedding three chunks.

## How to talk about it

**What a competent answer sounds like.** Lead with the thing the window destroys
and the measured result. "Fixed-size windows split tables from their headers and
drop the heading that said what the text was about. On a five-query test against
one configuration page, the heading-aware chunker routed every query to the
right section and the fixed-size one got most of them wrong, because the words a
reader uses often appear only in the heading. I keep the heading trail, the page
type and the summary on every chunk, and derive the chunk id from the heading
trail so an edit does not force a full re-index."

**The follow-up is almost always "what chunk size do you use",** which is a
trap in the sense that any specific number is the wrong answer. The honest reply:
the question presumes fixed sizes. For documentation I split on structure and
cap the result, so the size is whatever the section is, usually a few hundred to
about 1,200 characters. The cap matters more than a target, because the failure
you are preventing is one enormous section rather than a few short ones.

**The tradeoffs to volunteer, and there are two real ones.**

Heading-aware chunking **depends on the corpus having real headings**. Pointed at
a corpus where every page is one H1 and 2,000 words of prose, it produces one
chunk per page and is worse than a window. That dependency is why
[content models](content-model.md) and chunking belong in the same discussion.

And **section sizes vary enormously**, which means your chunks do too. A
retrieval system tuned for uniform chunks will behave oddly: a 90-character
chunk and a 1,200-character chunk do not compete fairly under most scoring
functions, which is part of why BM25 length normalisation and similar corrections
exist.

**One sharper point.** The strongest framing is that **chunking is an information
architecture decision wearing an engineering costume.** The question "what is a
retrievable unit of meaning" is the same question as "what is a page", asked at a
finer grain, and a corpus with good page boundaries chunks well almost for free.
Teams that treat chunking as a tuning parameter are usually compensating for an
information architecture problem one layer up, which is why
[Diátaxis](diataxis.md) turned out to be the most useful metadata field anyone
had.

## How to prove it

**The artifact.** Two chunkers and a scored comparison. The comparison is what
makes it an argument rather than an opinion.

**Three things to do, in order:**

1. **Run the golden path**, then point both chunkers at a real page from a
   project you know. The damage report in step 3 is the demonstration; it takes
   two minutes and it is visceral.
2. **Add the fence test.** Put a `#` comment inside a code block and confirm your
   chunker does not treat it as a heading. If you only write one test for a
   chunker, write that one.
3. **Measure, with the queries phrased as a reader would.** Five queries is
   enough to be informative. Publish the number including the cases you lose;
   see [retrieval evaluation](retrieval-evaluation.md).

**What makes it credible rather than decorative.** Everyone in this field can describe heading-aware
chunking. A repository with both implementations, a fence-bug test, and a scored
comparison on reader-phrased queries demonstrates that you measured rather than
adopted the consensus.

## Related

- [Agent-ready content](agent-ready-content.md), the framing above this
- [Embeddings](embeddings.md), what happens to a chunk next
- [Retrieval evaluation](retrieval-evaluation.md), how you know a change helped
- [Content models](content-model.md), the structure chunking depends on
