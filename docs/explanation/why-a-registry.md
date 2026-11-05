---
title: Why the curriculum is a data file
summary: A checklist nobody can verify reports completion it has not earned, so this one is validated in CI.
diataxis: explanation
audience: contributor
---

# Why the curriculum is a data file

The obvious way to build this guide is a Markdown page with 106
checkboxes on it. Someone ticks one when they write a page.

That version is worse than having no checklist, and it is worth being precise
about why, because the same failure runs through most documentation projects.

## What a hand-maintained checklist actually reports

A checkbox records an intention at the moment someone typed it. It does not
record the state of the repository. Within a month the two have diverged in
every direction at once:

- A page was written and nobody ticked the box.
- A box was ticked and the page is three paragraphs of `TODO`.
- A page was renamed and the link under its ticked box is dead.
- A concept turned out to be two concepts and the single box still says done.
- Someone added a page for a concept that was never on the list.

None of these are visible. The index page *looks* authoritative, which is
precisely the problem: it is the page a reader trusts most and the page most
likely to be wrong. A reader who follows a tick to a stub learns not to trust
the index, and after that the index is decoration.

## What the registry does instead

`concepts.yaml` holds the curriculum as structured data: 106 concepts
with a category, a tier, a difficulty, a time estimate, prerequisites, the job
posting line that justifies the concept, and a status.

`fieldguide check` then refuses to let the registry and the repository disagree:

| The claim | What catches a false one |
|---|---|
| This concept is covered | The page must exist, unless status is `planned` |
| This page belongs here | Every page must have a concept in the registry |
| This concept is complete | A `complete` page under 450 words is rejected |
| This page follows the contract | All seven required sections, in order |
| This path is teachable | No concept before a prerequisite the path also teaches |
| This graph is followable | No cycles, no dangling prerequisites |
| A posting asks for this | Every concept needs a source, provenance, and a quote |

The [coverage matrix](../coverage.md), the [learning paths](../paths/index.md),
and [the full ordering](../study-plan.md) are all generated from the registry.
They are views, not copies, so there is no state in them that can drift. CI
runs the generator with `--check` and fails if a committed view is stale, which
closes the last gap: changing the registry without regenerating.

## It caught four real mistakes immediately

This is the part that justifies the machinery rather than merely describing it.

**Two learning paths taught a prerequisite too late.** The first-week path
taught link checking before documentation CI, and the educator path taught
reproducible environments before cold-start testing. Both were flagged on the
first run.

**Both turned out to be wrong dependencies, not wrong orders.** Thinking about
it, you run a link checker on a tree long before you own a pipeline, so link
checking depending on documentation CI was backwards. And a reproducible
environment is how you make cold-start testing meaningful, so that edge pointed
the wrong way too. The validator reported a symptom in the paths; the bug was
in the model. That is the ordinary experience of working with a validated
schema, and it is the argument for having one: the error surfaced somewhere
cheap.

**The page-contract check and the stub check both found what they were built
for** while the first pages were being drafted.

## What it costs

Honesty requires the other column.

**Adding a concept is now a two-step operation**: edit the registry, then run
the generator. A contributor who edits a generated page by hand loses the work.
The banner on every generated page exists because of that, and a banner is a
weaker guard than a lock.

**The schema has opinions, and some of them will be wrong.** `tier` has three
values and `difficulty` has three levels, which is a forced simplification of
something continuous. A concept that is genuinely between `core` and
`supporting` gets rounded, and the rounding is invisible to a reader.

**Eighty-three concepts in one flat namespace is near the limit of what this
model carries well.** There is no sub-categorisation and no notion of a concept
that is a special case of another. At two hundred concepts this file would need
to become a directory, and the generator would need to grow a notion of
hierarchy it currently does not have.

**And a validated curriculum is still only one person's curriculum.** Nothing
here checks whether these are the right 106 concepts. The registry
makes the list *consistent and honest about its sources*. It cannot make it
*correct*, and no amount of schema will.

## Related

- [The page contract](the-page-contract.md), the part of the model that governs prose.
- [Provenance](provenance.md), on why every concept prints its evidence.
