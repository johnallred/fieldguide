---
title: Learning paths
summary: Ordered routes through the concepts, for readers who want a curriculum rather
  than a reference.
diataxis: placeholder
audience: new-user
generated: true
---


# Learning paths

The [coverage matrix](../coverage.md) is a reference: it lists everything and
assumes you know what you need. A path is the other thing a learner wants, which
is somebody else's opinion about the order.

Paths overlap on purpose. A concept that appears in four of them is load-bearing,
and that is worth knowing before you pick where to start.

## Where to start

### [The first week](first-week.md)

*Someone who has just started in this kind of work and needs to be useful by Friday.*

The shortest route to shipping a documentation change with confidence.

10 concepts, roughly 34 hours.

### [A working result in a weekend](prove-it.md)

*Someone who needs to ship something their team can review by Monday.*

The shortest path through the concepts that produce something reviewable.

15 concepts, roughly 59 hours.

## Paths by role

### [The content architect](content-architect.md)

*A writer or engineer who owns structure across a growing corpus.*

From a folder of Markdown to a modelled, governed, machine-readable corpus.

17 concepts, roughly 60 hours.

### [The documentation engineer](docs-engineer.md)

*Someone building the pipeline rather than writing the pages.*

Every automated gate that stops documentation rotting, in the order worth adding them.

18 concepts, roughly 69 hours.

### [Reference and releases](reference-and-releases.md)

*Someone who owns the API reference and the versioned docs for a product that ships releases.*

Reference generated from the source, checked against it, and versioned with each release.

8 concepts, roughly 29 hours.

### [The KnowledgeOps path](knowledgeops.md)

*Someone responsible for making a knowledge base usable by AI assistants and agents.*

Making a corpus answerable by machines, and knowing whether it worked.

18 concepts, roughly 87 hours.

### [Found by search and answer engines](answer-engines.md)

*Someone responsible for whether people, search engines and AI answer engines can find the documentation at all.*

From metadata to being cited, making a public corpus discoverable and quotable.

8 concepts, roughly 24 hours.

### [The developer educator](developer-educator.md)

*Someone who owns developer onboarding, tutorials and curriculum.*

Taking a developer from a clean environment to a working result, repeatably.

19 concepts, roughly 77 hours.

### [The lab engineer](lab-engineer.md)

*Someone who builds, tests and publishes hands-on labs that run in real cloud accounts.*

Taking a lab from a working draft to one that is tested nightly, published on evidence, safe for learners and portable.

9 concepts, roughly 43 hours.

### [The writer who builds](writer-who-builds.md)

*A writer who also builds tooling, and needs the half of the work that is judgement and collaboration rather than tooling.*

The craft and the working relationships, which no pipeline substitutes for.

15 concepts, roughly 55 hours.

## Once the work is real

### [Prove the outcomes](prove-the-outcomes.md)

*Someone whose documentation work is real and who has been asked, probably in a review, to show what it achieved.*

Write the programs that measure a corpus, then measure the four outcomes that matter most.

11 concepts, roughly 40 hours.

## Background, at any time

### [Enough domain to not be lost](domain-context.md)

*Someone doing documentation work at a company whose product is graphics, simulation, robotics or AI infrastructure.*

Six technical domains, at the depth where you can follow an engineer and know which questions are not yours to answer.

6 concepts, roughly 24 hours.

## What every path shares

Concepts that appear in three or more paths. If you only have a weekend,
this is the list.

| Concept | Paths |
|---|---|
| [Documentation CI](../concepts/documentation-ci.md) | 4 |
| [Diátaxis](../concepts/diataxis.md) | 4 |
| [llms.txt and llms-full.txt](../concepts/llms-txt.md) | 3 |
| [Treating docs, setup and samples as one product](../concepts/docs-as-product.md) | 3 |
| [Metadata for navigation and retrieval](../concepts/metadata.md) | 3 |
| [Link checking](../concepts/link-checking.md) | 3 |
| [Docs-as-code](../concepts/docs-as-code.md) | 3 |
| [Content models](../concepts/content-model.md) | 3 |
| [Cold-start testing](../concepts/coldstart-testing.md) | 3 |
| [Code-sample validation](../concepts/code-sample-validation.md) | 3 |

## Not on any path

These concepts are on no path, on purpose, and each says when you would
want it anyway. Every other concept is on at least one path.

| Concept | When to read it |
|---|---|
| [MDX](../concepts/mdx.md) | An alternative to the Markdown the paths teach, met when a site is built on Docusaurus or another React-based generator. |
| [Docusaurus](../concepts/docusaurus.md) | An alternative generator. The paths teach MkDocs; read this when the site you inherit is built on Docusaurus. |
| [Antora and AsciiDoc](../concepts/antora.md) | An alternative generator for multi-repository AsciiDoc sites. Read it when the site you inherit is built on Antora. |
