---
title: Transforming content as data
summary: "Every transformation drops something; the dangerous ones relocate it instead, so the pipeline is correct and any consumer who forgets the relocation is not."
diataxis: explanation
audience: developer
concept: content-data-transformation
tags: [auto, core]
---

# Transforming content as data

`core` · difficulty 2 · 4h

!!! quote "Asked for by name"
    NVIDIA: "Working proficiency in Python or similar to automate content tasks, transform data, and integrate with APIs"

**Prerequisites:** [Python for content automation](python-for-content.md), [Content models](content-model.md)

## What it is

Converting documentation from the form people write into the forms machines
consume: Markdown into chunk records, front matter into a search index, a tree
of pages into one flat file for a context window. The
[content model](content-model.md) is what makes it possible, because a
transformation can only carry fields that reliably exist.

The whole discipline reduces to one question asked at every stage: **what did
this drop, and who finds out?**

## Why the job asks for it

Because the artifacts a documentation platform ships are mostly derived, and
derived artifacts fail quietly.

A broken page is visible to whoever opens it. A chunk record missing a field is
visible to nobody until a retrieval returns something unhelpful, and then it
looks like a ranking problem. The team spends a quarter evaluating embedding
models for a defect introduced by a transformation that ran correctly.

NVIDIA's sentence puts "transform data" between automating content tasks and
integrating with APIs, which is the right order: transformation is where the
corpus stops being prose and becomes someone else's input, and the handover is
where the accountability gets lost.

## The golden path

Measure a real three-stage pipeline for what each stage drops, then find the
drop that is not a drop. About thirty minutes.

**Step 1: run the pipeline and account for every character**

```bash
docpack docs --out dist
```

```
stage                     files  chars     of source
  docs/*.md                  12   45751      100%
  chunks.jsonl text          85   40767       89%
  llms-full.txt               1   45308       99%
  llms.txt                    1    2246        5%
```

Three outputs with three quite different jobs. `llms-full.txt` keeps 99 per
cent, so it is close to a concatenation. `llms.txt` keeps five, because it is a
map rather than a copy: titles, summaries and links, grouped by type. Neither is
surprising.

`chunks.jsonl` keeping 89 per cent is the one to look at, because it is the
artifact a retriever actually uses.

**Step 2: find out where the eleven per cent went**

Reconstruct each page by concatenating its own chunks and compare with the
source:

```python
joined = "\n\n".join(c["text"] for c in by_source[rel])
frac = len(joined) / len(body_without_front_matter)
```

```
page                                          source  chunks   kept
reference/api.md                                1028     908    88%
how-to/wire-up-ci.md                            1549    1415    91%
how-to/add-a-page.md                            3707    3392    92%
explanation/why-heading-aware-chunking.md       2909    2702    93%

mean kept: 93%
```

Seven per cent, evenly spread, no page catastrophically worse than another.
Even distribution is a clue: a parsing bug would concentrate. Account for it
directly:

```
source body characters:      43285
  in heading lines:           2367   (5%)
  blank lines:                 322
```

Five per cent is heading lines, and the rest is the blank lines between
sections. The transformation is doing exactly what it was designed to do.

**Step 3: the drop that is not a drop**

The headings are not discarded. They are **relocated**:

```
a chunk record:
  breadcrumb: AI-readiness patterns > Why generated and not hand-maintained
  title:      AI-readiness patterns
  text opens: 'A hand-written `llms.txt` is accurate on the day it is written...'

chunks whose text still contains their own heading: 3 of 85
```

Eighty-two of eighty-five chunks have the heading stripped from the body and
promoted to a metadata field. That is the right design: the heading trail is
more useful as a filterable, displayable field than as the first line of a text
blob, and it is how the breadcrumb gets into a search result.

It also means **every consumer that reads `text` alone silently loses every
heading in the corpus.** The information is present in the record and absent
from the field people reach for.

**Step 4: measure what that costs the careless consumer**

The grounding check joins the breadcrumb back on before testing. Run it both
ways:

```
  grounded@1, breadcrumb + text (what the pipeline does)   18/20  (90%)
  grounded@1, text alone (a careless consumer)             17/20  (85%)
```

Five points, one case in twenty, from forgetting a field that is right there in
the record.

Five points is small and the shape of the failure is what matters. The
transformation is correct, the artifact is complete, the schema is documented,
and a reasonable integrator writing `record["text"]` gets a worse system with
no error, no warning and nothing to debug. The defect is not in the pipeline; it
is in the **contract the pipeline does not state**.

**Step 5: state the contract, then assert it**

The fix is not to stop relocating headings, which would make the records worse.
It is to say so where an integrator will see it, and to check that the
statement stays true:

```python
#: Fields a consumer must concatenate to reproduce what a reader sees.
RETRIEVAL_TEXT = ("breadcrumb", "text")
```

A transformation that relocates anything owes its consumers three things: the
relocation documented next to the schema, a named constant or helper that does
the rejoining so nobody has to remember, and a test that fails if the
relocation changes. The third is what stops this from recurring the next time
the chunker is improved.

**What you built.** A character-level account of a three-stage pipeline, a
seven per cent loss resolved into headings and blank lines, and a measurement of
what one unstated contract costs the consumer who follows the obvious path.

## Reference

### The three transformations, and what each is for

| Output | Keeps | Job | Breaks when |
|---|---|---|---|
| `chunks.jsonl` | 89% | Retrieval, with filters | A field is missing or renamed |
| `llms-full.txt` | 99% | One context window | The corpus outgrows the window |
| `llms.txt` | 5% | A map for an agent to navigate | Summaries go stale |
| A search index | Varies | In-site search | Titles collide |
| An offline bundle | 100% | Air-gapped reading | Links assume a server |

Keeping less is not worse. Each figure should match the job, and a number that
does not match its job is the actual finding: a map at 89 per cent is a copy, and
a chunk set at 5 per cent has lost the content.

### How a transformation loses something

| Mode | Example | Who notices |
|---|---|---|
| Discarded | Comments stripped from output | Nobody, correctly |
| Relocated | A heading becomes a `breadcrumb` field | The consumer who reads one field |
| Flattened | Nested lists become one paragraph | A reader, eventually |
| Truncated | A chunk cut at a token ceiling mid-sentence | A retriever, as poor grounding |
| Reordered | Dict iteration changing record order | A diff, as noise |
| Silently empty | A page that parsed to zero chunks | Nobody, which is the worst case |

The second row is this page's subject and the most common real defect, because
it looks like success at every point in the pipeline.

### What a derived artifact owes its consumers

| Obligation | Why |
|---|---|
| A documented schema | Otherwise every integrator guesses |
| The relocations stated explicitly | See step 4 |
| A helper that does the obvious rejoining | Cheaper than documentation nobody reads |
| Stable identifiers | So a consumer can diff two runs |
| A record count asserted in CI | Catches the silently-empty mode |
| A version or generation timestamp | So staleness is detectable downstream |

### Stable identifiers, and why they are hard

A chunk id must change when the chunk's content changes and must not change
when something unrelated moves. Hashing the content plus the heading trail gets
both; hashing the position gets neither.

| Scheme | Survives an edit elsewhere | Changes on a real edit |
|---|---|---|
| Position index | No | Yes |
| Hash of text | Yes | Yes |
| Hash of text and breadcrumb | Yes | Yes, and on a retitle |
| `hash()` builtin | No; salted per process | Unusable |

The third is usually right, and the fourth is a real mistake people make once.

### Round-tripping as a test

You will rarely need to reconstruct the source, and attempting it is still the
cheapest audit available: concatenate the chunks of each page, compare lengths,
and look at the distribution. An even seven per cent is a design decision. One
page at forty per cent is a bug, and nothing else in the pipeline would have
told you.

## How to talk about it

**Lead with the question.** "Every transformation drops something, so the only
question that matters at each stage is what it dropped and who finds out. The
dangerous answer is that it did not drop the thing, it moved it, because then
the pipeline is correct and the consumer is wrong, and nothing errors."

**The worked example, which is short.** My chunk records keep 89 per cent of
the source. Reconstructing each page from its own chunks put the loss at seven
per cent, evenly spread, and even distribution rules out a parsing bug. It
resolved into five per cent heading lines and the blank lines between sections.
Eighty-two of eighty-five chunks have their heading stripped from the body and
promoted to a `breadcrumb` field, which is the right design and means any
consumer reading `text` alone loses every heading in the corpus.

**Then the cost, measured.** Grounding at rank one is 90 per cent when the
breadcrumb is rejoined and 85 when it is not. One case in twenty, from
forgetting a field sitting in the same record. Small, and the shape is the
point: correct pipeline, complete artifact, documented schema, and a reasonable
integrator writing `record["text"]` gets a quietly worse system. The defect is
in the contract the pipeline never stated.

**The tradeoff to volunteer.** I would not fix that by stopping the relocation,
because the records are better with the heading as a field. The fix is a stated
contract, a helper that does the rejoining so nobody has to remember, and a test
that fails if the relocation changes. That is three small obligations on the
producer to save every consumer from the same discovery, and producers resist it
because from the inside the artifact looks complete.

**One sharper point.** Round-tripping is worth doing even when you never need
the source back. Concatenating each page's chunks and comparing lengths took ten
minutes and converted "89 per cent, presumably fine" into an itemised account. If
one page had come back at forty per cent I would have had a bug, and no other
check in the pipeline would have mentioned it.

## How to prove it

**The artifact.** A transformation of yours with a character-level account of
each stage, and a stated contract for any field it relocates.

**Three things to do, in order:**

1. Reconstruct one page from its own derived records and compare the lengths.
   Predict the percentage first, then explain the gap down to the character
   class; "probably whitespace" is not an explanation.
2. Find a field your pipeline relocates and check whether the obvious consumer
   path picks it up. If there is no helper, write the helper rather than the
   documentation.
3. Assert a record count in CI. The silently-empty failure is the only one on
   this page that nobody notices at all, and one assertion closes it.

**What makes it credible rather than decorative.** `docpack`'s pipeline is real and every figure above is reproducible from it.
Three outputs at 89, 99 and 5 per cent of source. A seven per cent round-trip
gap resolved into headings and blank lines. 82 of 85 chunks with relocated
headings, and the five-point grounding difference between rejoining the
breadcrumb and not. What is absent is
a consumer other than this project: nobody has integrated against these records,
so the contract problem in step 4 is demonstrated by measurement rather than by
a real integrator getting it wrong.

## Related

- [Python for content automation](python-for-content.md), the parsing this depends on
- [Content models](content-model.md), what makes a field safe to transform
- [API integration](api-integration.md), where derived artifacts get handed over
- [Chunking strategies](chunking.md), the transformation measured here
- [Single-sourcing and content reuse](single-sourcing.md), transformation used for publishing
