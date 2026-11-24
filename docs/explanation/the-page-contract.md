---
title: The page contract
summary: Seven required sections in a fixed order, enforced in CI, and the reasoning behind each one.
diataxis: explanation
audience: contributor
---

# The page contract

Every concept page in this guide answers the same seven questions in the same
order. `fieldguide check` rejects one that does not, and `fieldguide new`
generates the headings so nobody has to remember them.

1. What it is
2. How this applies to your role
3. The golden path
4. Reference
5. Explaining it to your team
6. Putting it into practice
7. Related

## Why a fixed order rather than a suggested one

A reader working through thirty pages of a reference corpus spends attention on
two separate things: the subject, and figuring out where in this particular
page the thing they want is. The second is pure overhead, and it is paid again
on every page.

A fixed contract pays it once. By the third page a reader knows that the
command they can paste is under "The golden path" and the tradeoff is in the
fifth section, and they can skip directly. That is the entire benefit, and it only
exists if the order is actually reliable, which is why it is a build failure
rather than a style note.

This is [Diátaxis](../concepts/diataxis.md) logic applied inside a page instead of across a tree. Diátaxis
separates the four kinds of documentation into separate documents because
mixing them serves nobody. A concept page in a study guide is a deliberate
exception: the reader wants orientation, a tutorial, reference, and
argumentation about *one narrow subject*, in one sitting. The contract keeps
them separated within the page rather than interleaved, which is the thing
Diátaxis is actually objecting to.

## What each section is for, and how it usually fails

### What it is

Two sentences, for someone who has heard the term in a meeting and did not
admit they were lost. No history, no motivation, no benefits.

**The failure mode is the Wikipedia opening**: a definition so hedged and
complete that it conveys nothing. "Diátaxis is a systematic framework for
technical documentation authoring" is correct and useless. Prefer the sentence
you would say out loud to a colleague.

### How this applies to your role

The line at the top of the page names the work that needs the concept. This
section explains that work: what does someone doing it do on a Tuesday that
requires this, whatever their title?

**The failure mode is restating the line.** If this section can be deleted
without losing information, it was not written.

### The golden path

The shortest real exercise that produces a working result. Commands to paste,
and what the reader should see after each one.

Three rules, and they are rules rather than preferences:

- **It starts from a [clean environment](../concepts/coldstart-testing.md).** The commonest documentation failure
  in existence is a quickstart that works because the author installed
  something months ago and forgot.
- **It ends in something observable.** Not "you now understand chunking", but a
  file on disk, a number printed, a page rendered.
- **The author has run it, in that order, in that environment.** A golden path
  nobody has walked is fiction with good formatting.

### Reference

The facts worth looking up later: vocabulary, options, defaults, gotchas.

**The failure mode is narrative.** Nobody reads this section; they scan it and
leave. Tables, definition lists, and short rows beat paragraphs.

### Explaining it to your team

How you would explain the concept to a colleague, a manager or an engineer
who asks, and what their follow-up question will be.

**Every one of these must include a tradeoff.** Reciting what a thing does is
not useful, because anyone can read the documentation an hour before a
meeting. Knowing what it costs, and when you would not use it, is the part your
team needs from you, and it is the question a good colleague asks second.

### Putting it into practice

The work product the concept produces when it is done well: a repository, a
file, a measured number, a commit. Then three tasks to do next, in order, and
how to tell the result is working.

**It has to be specific enough to act on today.** "Build a [RAG](../concepts/rag.md) pipeline" is not
a task. "Write twenty questions with their expected source pages, score
recall@3, and publish the number including the bad one" is.

## How it is enforced

`fieldguide check` reads every page belonging to a concept whose status is past
`planned` and checks:

- all seven headings are present, matched as `## <exact text>`
- their positions in the file are in contract order
- a page marked `complete` is at least 450 words

The word count is a crude proxy and is meant to be. It does not detect a bad
page; it detects a page marked `complete` that is obviously a stub, which is
the specific dishonesty worth automating against. Judging whether a page is
*good* is a [review](../concepts/docs-review.md) problem, and no linter is going to take it over.

## The honest limitation

**A contract this rigid is wrong for some concepts.** Several of the
domain-context entries, such as [OpenUSD](../concepts/usd-omniverse.md) or [robotics](../concepts/robotics-sim.md) simulation, do not have a
meaningful golden path at this guide's level of detail: the useful content is
orientation and vocabulary so you are not lost in a room full of specialists.
Those pages have a "golden path" section because the contract demands one, and
on the weakest of them it is the least valuable section on the page.

The alternative was a second contract for context-tier concepts, which means
two shapes for a reader to learn and a conditional in the validator. That
seemed worse than a handful of thin sections, but it is a judgment call rather
than an obvious win, and a reader who finds those sections padded is not
wrong.

## Related

- [Why the curriculum is a data file](why-a-registry.md)
- [Provenance](provenance.md)
