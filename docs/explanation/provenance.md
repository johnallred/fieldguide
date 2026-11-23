---
title: Provenance
summary: Every concept names the day-to-day work that needs it, and the limits of that judgement are stated rather than implied.
diataxis: explanation
audience: new-user
---

# Provenance

Every concept in this guide prints a line naming the work that needs it. The
line appears on every row of the [coverage matrix](../coverage.md) and at the
top of every concept page, and `fieldguide check` requires one on every
concept.

## Why this is worth the clutter

A curriculum has an obvious failure mode: the author's existing interests
quietly become requirements. The work involves "information architecture", and
forty pages later the guide is teaching a specific taxonomy methodology the
author happens to like, with the work's authority borrowed for all of it.

Printing the line that justifies each concept makes that move visible. A reader
who disagrees with a concept's place on the list can see exactly what it rests
on, rather than taking the curriculum's word for it.

## Where the list comes from

The scope was built from descriptions of this work as several different teams
do it: developer relations, developer education, cloud training labs and
KnowledgeOps. The titles differed and the work overlapped heavily, which is the
premise of the whole guide.

Some concepts are named directly in that work: docs-as-code pipelines, Git
authoring, documentation CI, content modelling, `llms.txt`, evaluation sets.
Others are here because the named work is impossible without them, and their
lines say so in those terms. Diátaxis is one of those, and so is every
embedding concept underneath RAG.

## What a second pass changed

The first version of this registry was built from notes rather than from the
source descriptions, and it is worth recording what happened when the sources
were read again in full, because it is the best available argument for
tracking where a concept came from at all.

**Fifty-one concepts were mislabelled.** Most were understated: docs-as-code
pipelines, Git authoring, Markdown and RST, Sphinx, MkDocs, Docusaurus,
knowledge architecture, Vale, `llms.txt`, documentation analytics, the
sample-app gallery and the AI software stack are all named directly in the
work, and all of those had been recorded as inferences.

**Eight were overstated in the other direction**, which matters more.
Localization, accessibility, versioned documentation, OpenAPI, single-sourcing,
screencasts, workshops and assessment design had been recorded as things the
work explicitly requires. They are here because one person thinks the work
needs them, and their lines now say so.

**Twenty-three concepts were missing entirely**, including three that are
`core`: technical writing as a craft, which everything else rests on; reading
code to verify accuracy; and judging where AI can be trusted.

The curriculum did not get more rigorous, it got more honestly labelled, and
the eight demotions are the part worth dwelling on. An unchecked registry
drifts toward whatever the author already believed.

## How to read a weak claim

A concept resting on an inference is not thereby unimportant. Diátaxis is one
of them, and it is the single most useful thing on this list: few teams name
it, and all of them describe at length the problem it solves. Markdown is
another, and you will not get through a day of this work without it.

What the line tells you is **what the concept is for**. Whether that earns your
time is a decision only you can make, and you can only make it if somebody
tells you.

## Related

- [Why the curriculum is a data file](why-a-registry.md)
- [Coverage](../coverage.md), where the line behind all 115 is printed
