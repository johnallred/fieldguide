---
title: Provenance
summary: Every concept prints whether a posting asked for it in those words, and why that distinction is not averaged away.
diataxis: explanation
audience: new-user
---

# Provenance

Every concept in this guide carries a tag saying how strong its claim on your
time is.

| Tag | Meaning | Count |
|---|---|---|
| `quoted` | A verbatim phrase from one of the two job postings | 90 |
| `derived` | The posting requires this, but these are not its words | 4 |
| `adjacent` | Neither posting mentions it; the named work is impossible without it | 12 |

The tag is printed on every row of the [coverage matrix](../coverage.md) and at
the top of every concept page. `fieldguide check` requires one, along with a
quote, on every concept.

## Why this is worth the clutter

A curriculum assembled from job postings has an obvious failure mode: the
author's existing interests quietly become requirements. The posting says
"information architecture", and forty pages later the guide is teaching a
specific taxonomy methodology the author happens to like, with the posting's
authority borrowed for all of it.

Printing the provenance makes that move visible. When a page says `adjacent`,
it is saying: no employer asked for this, I am asserting that you need it, and
you may disagree. Twelve of the 106 concepts are in that position, and
a reader who wants only what the postings demand can skip them and know exactly
what they skipped.

The same logic applies to `derived`, which is the larger and more interesting
category. 4 concepts are here because a posting requires the capability
without naming the concept. NVIDIA asks for RAG pipelines, so embeddings and
vector stores are `derived`: you cannot build the first without the second two,
but NVIDIA never wrote the word "embeddings". That inference is almost certainly
correct and it is still an inference.

## What a second pass against the source text changed

The first version of this registry was built from notes rather than from the
postings themselves, and it is worth recording what happened when both postings
were read again in full, because the result is the best available argument for
tracking provenance at all.

**Fifty-one concepts had the wrong tag.** Most were understated: the postings
name docs-as-code pipelines, Git authoring, Markdown/RST, Sphinx, MkDocs,
Docusaurus, knowledge architecture, Vale, llms.txt, documentation analytics,
the sample-app gallery and the AI software stack in so many words, and all of
those had been filed as `derived`.

**Eight were overstated in the other direction**, which matters more.
Localization, accessibility, versioned documentation, OpenAPI, single-sourcing,
screencasts, workshops and assessment design had been filed as things a posting
required. Neither posting mentions any of them. They are now `adjacent`, which
means: one person thinks you need this, and no employer said so.

**Twenty-three concepts were missing entirely**, including three that are
`core`: technical writing as a craft, which both postings list as a minimum
qualification; reading code to verify accuracy; and judging where AI can be
trusted.

The ratio moved from 41 quoted out of 83 to 90 out of 106. The curriculum did
not get more rigorous, it got more honestly labelled, and the eight demotions
are the part worth dwelling on. An unchecked registry drifts toward whatever
the author already believed, with the posting's authority attached.

A guide that quietly presented all three tags as "what the job requires" would
be more persuasive and less true. The cost of the distinction is a cluttered
table and a reader who has to think about which claims to accept. That seems
like the right trade for a document whose entire subject is how to make
knowledge trustworthy.

## How to read a weak claim

An `adjacent` tag is not a warning that the concept is unimportant. Diátaxis is
tagged `adjacent`, and it is the single most useful thing on this list: neither
posting names it, and both describe at length the problem it solves. Markdown
is `adjacent` too, and you will not get through a day in either role without it.

What the tag tells you is **where the authority comes from**. For `quoted`, an
employer. For `adjacent`, one person's judgement about what the work requires.
Decide how much that is worth to you, which is a decision you can only make if
somebody tells you which it is.

## Related

- [Why the curriculum is a data file](why-a-registry.md)
- [Coverage](../coverage.md), where the provenance of all 106 is printed
