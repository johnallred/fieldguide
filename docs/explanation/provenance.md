---
title: Provenance
summary: Every concept prints the posting line that put it on the list, and the limits of that evidence are stated rather than implied.
diataxis: explanation
audience: new-user
---

# Provenance

Every concept in this guide prints the posting language that put it on the
list. The line appears on every row of the [coverage matrix](../coverage.md)
and at the top of every concept page, and `fieldguide check` requires one on
every concept.

## Why this is worth the clutter

A curriculum assembled from job postings has an obvious failure mode: the
author's existing interests quietly become requirements. The posting says
"information architecture", and forty pages later the guide is teaching a
specific taxonomy methodology the author happens to like, with the posting's
authority borrowed for all of it.

Printing the line that justifies each concept makes that move visible. A reader
who disagrees with a concept's place on the list can see exactly what it rests
on, rather than taking the curriculum's word for it.

## The limitation, stated plainly

**The postings themselves are not reproduced here and are no longer on hand.**
The lines recorded against each concept are phrases taken down while reading
them, so treat them as near-verbatim rather than certified. Where a concept is
here because the work named in a posting is impossible without it, the line
says so in those terms rather than pretending to be a quotation.

That distinction used to be carried by a tag on every entry. It is now carried
by the wording of the line itself, which is less rigorous and worth knowing
about: a reader can no longer filter the list down to only what an employer
literally asked for.

## What a second pass against the source text changed

The first version of this registry was built from notes rather than from the
postings themselves, and it is worth recording what happened when the postings
were read again in full, because it is the best available argument for tracking
where a concept came from at all.

**Fifty-one concepts were mislabelled.** Most were understated: the postings
name docs-as-code pipelines, Git authoring, Markdown and RST, Sphinx, MkDocs,
Docusaurus, knowledge architecture, Vale, llms.txt, documentation analytics,
the sample-app gallery and the AI software stack in so many words, and all of
those had been recorded as inferences.

**Eight were overstated in the other direction**, which matters more.
Localization, accessibility, versioned documentation, OpenAPI, single-sourcing,
screencasts, workshops and assessment design had been recorded as things a
posting required. No posting mentions any of them. They are here because one
person thinks the work needs them, and no employer said so.

**Twenty-three concepts were missing entirely**, including three that are
`core`: technical writing as a craft, which the postings list as a minimum
qualification; reading code to verify accuracy; and judging where AI can be
trusted.

The curriculum did not get more rigorous, it got more honestly labelled, and
the eight demotions are the part worth dwelling on. An unchecked registry
drifts toward whatever the author already believed, with a posting's authority
attached.

## How to read a weak claim

A concept resting on an inference rather than a quotation is not thereby
unimportant. Diátaxis is one of them, and it is the single most useful thing on
this list: no posting names it, and they describe at length the problem it
solves. Markdown is another, and you will not get through a day in any of these
roles without it.

What the line tells you is **where the authority comes from**: an employer's
words, or one person's judgement about what the work requires. Decide how much
that is worth to you, which is a decision you can only make if somebody tells
you which it is.

## Related

- [Why the curriculum is a data file](why-a-registry.md)
- [Coverage](../coverage.md), where the line behind all 106 is printed
