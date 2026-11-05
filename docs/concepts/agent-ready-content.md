---
title: Agent-ready content
summary: Structuring a corpus so machines can find, cite and act on it, which is three different consumers rather than one.
diataxis: explanation
audience: developer
concept: agent-ready-content
tags: [ai, core]
---

# Agent-ready content

`core` · difficulty 2 · 4h

> Make knowledge AI-ready: structure and package content for RAG, internal assistants, and agentic workflows

> Source: nvidia posting, verbatim

**Prerequisites:** [Content models](content-model.md), [Metadata for navigation and retrieval](metadata.md)

**Leads to:** [Agentic workflows](agentic-workflows.md), [Chunking strategies](chunking.md), [Documentation for coding agents](coding-agents.md), [Generative engine optimization](geo.md), [Model Context Protocol](mcp.md), [llms.txt and llms-full.txt](llms-txt.md)

## What it is

Structuring and packaging a corpus so that machines can find the right part,
know what kind of answer it supports, and cite it. The phrase is vague on
purpose in job postings and should not be vague in your head: **"AI-ready" is
three consumers with incompatible needs**, and serving one of them is the usual
way to fail the other two.

## Why the job asks for it

NVIDIA's bullet is the clearest statement of this work anywhere in either
posting: "Make knowledge AI-ready: structure and package content for RAG,
internal assistants, and agentic workflows, including llms.txt, MCP-accessible
sources, agent skills and context kits, and evaluation sets for answer
accuracy."

Read the list of outputs. `llms.txt` is a map. MCP is an interface. Chunks for
RAG are retrieval units. Agent skills are instructions. Those are not four
formats of the same thing; they are four different artifacts for different
consumption patterns, and the posting is asking for all of them because no one
of them covers the others.

Intel's version is the same requirement from the other side: "a crawlable,
agent-ready front door" and "agentready, LLMdigestible content".

On a Tuesday this is a question you answer repeatedly: an assistant gave a
developer a wrong answer about batch sizing. Was the chunk missing, or was the
right chunk retrieved and the wrong one ranked higher, or did the assistant not
know which page could answer the question at all? Those have three different
fixes, and you can only tell them apart if you built the three artifacts
separately and can inspect each.

The reason this concept exists as its own page rather than being absorbed into
[chunking](chunking.md) or [RAG](rag.md): it is the framing that keeps you from
building one thing and claiming all of it.

## The golden path

Produce all three artifacts from one corpus and see why each exists. Forty
minutes, no dependencies beyond Python.

**Step 1: a small corpus with a real content model**

```bash
mkdir -p agentready-drill/docs && cd agentready-drill
cat > docs/install.md <<'EOF'
---
title: Install the widget CLI
summary: Install the CLI and verify it runs.
kind: how-to
audience: new-user
updated: 2026-10-26
---
# Install the widget CLI

Run `pip install widget`. Requires Python 3.10 or newer.

## Verify

Run `widget --version`. It prints the version and exits 0.
EOF

cat > docs/batch-size.md <<'EOF'
---
title: Choose a batch size
summary: Pick a batch size from latency, memory and quantisation.
kind: how-to
audience: developer
updated: 2026-10-26
---
# Choose a batch size

Set `batch_size` on the client. The default is 32.

## If latency matters

Use 1 or 2. Batching at 32 adds roughly 200ms at p99.

## If the model is quantised

The memory arithmetic differs. Start at 64 and watch memory.
EOF

cat > docs/why-at-least-once.md <<'EOF'
---
title: Why delivery is at-least-once
summary: The reasoning behind at-least-once rather than exactly-once delivery.
kind: explanation
audience: developer
updated: 2026-10-26
---
# Why delivery is at-least-once

Exactly-once requires distributed transactions across the queue and the
consumer's datastore.

## What it costs you

Every consumer must tolerate seeing an item twice.
EOF
ls docs/
```

**Step 2: build the three artifacts**

```bash
cat > pack.py <<'PY'
"""Produce three artifacts for three consumers from one corpus.

The point of this script is the comment above each function. Each artifact
answers a question the others cannot, and the reason "AI-ready" is slippery as
a phrase is that it gets used for whichever one somebody built.
"""
import json
import re
from pathlib import Path

import yaml

HEADING = re.compile(r"^(#{1,3}) +(.*)$")


def pages(docs: Path):
    for path in sorted(docs.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        front, _, body = text.partition("---\n")[2].partition("\n---\n")
        yield path, yaml.safe_load(front), body


def chunks(body: str, title: str):
    """Split on headings, keeping the heading trail with each piece.

    CONSUMER 1: a retriever. It wants small units, each carrying enough
    context to be understood alone, with metadata it can filter on before
    ranking. It never sees your navigation.

    The trail starts empty and the H1 becomes its first element, which is
    why the slice is `depth - 1`. Seeding it with the title instead produces
    "Choose a batch size > Choose a batch size" on every top-level chunk.
    """
    trail, buffer, out = [], [], []
    for line in body.splitlines():
        match = HEADING.match(line)
        if match:
            if buffer:
                out.append((" > ".join(trail), "\n".join(buffer).strip()))
                buffer = []
            depth = len(match.group(1))
            trail = trail[: depth - 1] + [match.group(2)]
        else:
            buffer.append(line)
    if buffer:
        out.append((" > ".join(trail), "\n".join(buffer).strip()))
    return [(crumb, text) for crumb, text in out if text]


def main() -> None:
    docs = Path("docs")
    out = Path("dist")
    out.mkdir(exist_ok=True)

    # ---- artifact 1: retrieval records -------------------------------
    records = []
    for path, meta, body in pages(docs):
        for crumb, text in chunks(body, meta["title"]):
            records.append({
                "id": f"{path.stem}::{crumb}",
                "source": path.name,
                "breadcrumb": crumb,
                "text": text,
                "kind": meta["kind"],
                "audience": meta["audience"],
                "summary": meta["summary"],
            })
    (out / "chunks.jsonl").write_text(
        "\n".join(json.dumps(r, sort_keys=True) for r in records) + "\n"
    )

    # ---- artifact 2: a map -------------------------------------------
    # CONSUMER 2: an assistant deciding WHERE TO LOOK. It has not read
    # anything yet. It needs the shape of the corpus and one line per page,
    # grouped so it can tell which pages can answer which kind of question.
    lines = ["# Widget docs", "", "> Documentation for the widget platform.", ""]
    for kind, label in [("how-to", "How-to guides"), ("explanation", "Explanation")]:
        group = [(p, m) for p, m, _ in pages(docs) if m["kind"] == kind]
        if not group:
            continue
        lines += [f"## {label}", ""]
        for path, meta in group:
            lines.append(f"- [{meta['title']}](docs/{path.name}): {meta['summary']}")
        lines.append("")
    (out / "llms.txt").write_text("\n".join(lines))

    # ---- artifact 3: everything, once --------------------------------
    # CONSUMER 3: an assistant that would rather make one request than
    # thirty. Cheap to serve, and it keeps each page's type visible so the
    # model can still tell a recipe from an argument.
    full = ["# Widget docs: complete", ""]
    for path, meta, body in pages(docs):
        full += [
            "---", "", f"# {meta['title']}", "",
            f"*{meta['kind']} for {meta['audience']}*", "",
            meta["summary"], "", body.strip(), "",
        ]
    (out / "llms-full.txt").write_text("\n".join(full))

    print(f"{len(records)} chunks, {len(list(pages(docs)))} pages -> dist/")
    for name in ("chunks.jsonl", "llms.txt", "llms-full.txt"):
        size = (out / name).stat().st_size
        print(f"  {name:<16} {size:>6} bytes")


if __name__ == "__main__":
    main()
PY
python3 pack.py
```

**Step 3: see why one artifact cannot do the others' job**

```bash
echo "=== The heading trail is not decoration. Search text only: ==="
python3 - <<'PY'
import json
rows = [json.loads(l) for l in open("dist/chunks.jsonl")]
print("  chunks whose TEXT contains 'latency':",
      sum(1 for r in rows if "latency" in r["text"].lower()))
print("  chunks whose BREADCRUMB + TEXT contains it:",
      sum(1 for r in rows if "latency" in f"{r['breadcrumb']} {r['text']}".lower()))
PY
```

Read that result carefully, because it is the single most useful thing on this
page. The chunk that answers a latency question says:

> Use 1 or 2. Batching at 32 adds roughly 200ms at p99.

**The word "latency" does not appear in it.** It appears in the heading above
it, `If latency matters`. A chunker that discards the heading produces a chunk
that is the correct answer and is unfindable by the obvious query.

```bash
echo "=== Consumer 1 asks: which chunk answers 'latency' for a developer? ==="
python3 - <<'PY'
import json
rows = [json.loads(l) for l in open("dist/chunks.jsonl")]
hits = [r for r in rows
        if r["audience"] == "developer"
        and r["kind"] == "how-to"
        and "latency" in f"{r['breadcrumb']} {r['text']}".lower()]
for r in hits:
    print(f"  {r['breadcrumb']}")
    print(f"    {r['text']}")
print(f"  ({len(rows)} chunks in the corpus, {len(hits)} match after filtering)")
PY

echo
echo "=== Consumer 2 asks: what kind of questions can this corpus answer? ==="
cat dist/llms.txt

echo "=== Consumer 3: one fetch, whole corpus ==="
wc -c dist/llms-full.txt
```

**Step 4: break each one and watch a different failure**

```bash
python3 - <<'PY'
import json

rows = [json.loads(l) for l in open("dist/chunks.jsonl")]
def haystack(r):
    return f"{r['breadcrumb']} {r['text']}".lower()

# Failure A: no type metadata. Retrieval still "works" and can no longer
# filter, so an explanation chunk competes for a "how do I" question.
print("A) a query about what batching costs you, with no kind filter:")
for r in rows:
    if "cost" in haystack(r) or "200ms" in haystack(r):
        print(f"     [{r['kind']:<11}] {r['breadcrumb']}")
print("   two chunks, two different kinds of answer. Only the how-to one")
print("   can tell a developer what to do.")

# Failure B: a map with no grouping. The assistant cannot tell which page
# supports which kind of answer, so it guesses.
print("\nB) an ungrouped map gives the model three indistinguishable links:")
for source in sorted({r["source"] for r in rows}):
    print(f"     - {source}")

# Failure C: only llms-full.txt. Fine at three pages, impossible at 3,000.
total = sum(len(r["text"]) for r in rows)
print(f"\nC) whole-corpus fetch is {total} chars here;")
print(f"   at 1,000x the corpus that is {total * 1000:,} chars, which no")
print( "   context window makes sense of. The map exists for this reason.")
PY
```

**What you built.** Three artifacts and three distinct failure modes.

Failure A is the one worth dwelling on. Both chunks are topically relevant to a
question about batching cost. One is a how-to guide telling a developer to use
1 or 2; the other is an explanation page saying every consumer must tolerate
duplicate delivery. **Only one of them can answer "what should I do", and
nothing about better embeddings distinguishes them.** The `kind` field does.

## Reference

### The three consumers

| Consumer | Wants | Artifact | Fails without it |
|---|---|---|---|
| A retriever | Small filterable units with context | `chunks.jsonl` | Returns whole pages, or fragments with no heading |
| An assistant choosing where to look | A map with one line per page, grouped | [`llms.txt`](llms-txt.md) | Guesses which page is relevant |
| An assistant reading everything | The whole corpus in one fetch | `llms-full.txt` | Makes thirty requests, or gives up |

A fourth consumer, an agent that needs to *act* rather than read, is served by
[MCP](mcp.md) and [agent skills](agent-skills.md) instead.

### What makes content agent-ready, in order of value

| Property | Why | Covered by |
|---|---|---|
| Every page declares its type | Lets a retriever filter by the kind of answer needed | [Content model](content-model.md), [Diátaxis](diataxis.md) |
| Chunks carry their heading trail | The heading is the strongest statement of what the text is about | [Chunking](chunking.md) |
| Every page has a one-sentence summary | Serves the map, the snippet and the meta description | [Metadata](metadata.md) |
| Stable chunk identifiers | Editing an intro does not force a whole re-index | [Chunking](chunking.md) |
| A freshness signal | Lets a consumer discount stale content | [Freshness monitoring](freshness-monitoring.md) |
| Machine-readable page type in the HTML | A crawler learns what the page can answer | [Structured data](structured-data.md), [GEO](geo.md) |

### The thing most "AI-ready" claims mean

| Claim | Usually means | Actually needed |
|---|---|---|
| "Our docs are AI-ready" | There is an `llms.txt` | All three artifacts, plus a measurement |
| "We chunked our docs" | Fixed-size windows | [Heading-aware chunks with metadata](chunking.md) |
| "We built a RAG pipeline" | Embeddings over a scrape | A corpus with a content model under it |
| "The assistant works" | Somebody tried five questions | [An evaluation set](retrieval-evaluation.md) |

The last row is the gap that matters most and the one NVIDIA asks about by
name.

### What agent-ready does not mean

- **Not writing for machines instead of people.** Every property above also
  helps a human: a declared page type improves navigation, a summary improves
  search results, a heading trail improves scanning.
- **Not a separate corpus.** A machine-readable copy maintained alongside the
  human one drifts within a quarter. These are generated views.
- **Not a formatting convention.** No amount of cleaner Markdown substitutes
  for the page declaring what it is.

## How to talk about it

**What a competent answer sounds like.** Lead with the three consumers, because
it immediately distinguishes you from the common answer. "AI-ready is three
consumers rather than one. A retriever wants small filterable units. An
assistant choosing where to look wants a map, which is what llms.txt is. An
assistant doing a one-shot read wants everything in one fetch. Serving only one
of those fails the other two, and most sites that claim to be AI-ready have
published an llms.txt and nothing else."

**The follow-up is usually "what is the single highest-value thing to do first",**
and the answer is not any of the three artifacts. It is **the type field on
every page**, because it is what lets a retriever filter by the kind of answer
the question needs, and that is the failure that no ranking improvement fixes.
A corpus with a content model can produce all three artifacts later; a corpus
without one produces three artifacts over mush.

**The tradeoff to volunteer.** Every one of these artifacts is a derived view
that has to be regenerated, and a stale derived view is worse than none because
it looks authoritative. An `llms.txt` committed by hand six months ago is now
actively misleading a model about what your corpus contains. So the real cost of
agent-ready content is a build step and a CI gate that fails when a view is
stale, and a team that is not ready to own that should publish nothing rather
than publish something that will rot.

**One sharper point.** The strongest version is that **the properties that make a
corpus agent-ready are mostly the properties that would have made it good
anyway**, and the arrival of retrieval made them finally worth paying for. A
declared page type, a real one-sentence summary, headings that state what is
below them: all of this was recommended practice for twenty years and routinely
skipped because the cost was visible and the benefit was not. What changed is
that the benefit is now measurable with an
[evaluation set](retrieval-evaluation.md). That framing is both true and
reassuring to a documentation lead who fears this is a new discipline.

## How to prove it

**The artifact.** All three outputs, generated from one corpus by a script in
CI, plus a measurement showing the type filter helps.

**Three things to do, in order:**

1. **Run the golden path** against a real corpus. Twenty pages is enough. The
   failure-A demonstration, where an explanation chunk answers a how-to query,
   is the single most convincing two minutes you can show.
2. **Generate the artifacts in CI, never by hand.** The gate that matters is one
   that fails when a committed view is stale. That is the difference between
   agent-ready and agent-ready-once.
3. **Measure the type filter.** Twenty questions, scored with and without
   filtering on the expected page type. The gap is the value of your content
   model, in a number. See [retrieval evaluation](retrieval-evaluation.md).

**What makes it credible rather than decorative.** An `llms.txt` file proves you read a blog post. Three
generated artifacts, a CI gate against staleness, and a measured difference from
the metadata filter proves you understand why they are three things.

## Related

- [Chunking strategies](chunking.md), the retrieval unit
- [llms.txt and llms-full.txt](llms-txt.md), the map and the one-shot read
- [Model Context Protocol](mcp.md), the interface for agents that act
- [Retrieval evaluation](retrieval-evaluation.md), how you know any of it worked
