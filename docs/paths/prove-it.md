---
title: A working result in a weekend
summary: The shortest path through the concepts that produce something reviewable.
diataxis: placeholder
audience: new-user
generated: true
---


# A working result in a weekend

**Who this is for.** Someone who needs to ship something their team can review by Monday.

The shortest path through the concepts that produce something reviewable.

**15 concepts, roughly 59 hours.** The order matters:
each step assumes the ones above it.

**Assumed before step 1.** This path does not teach [Information architecture](../concepts/information-architecture.md), [Choosing a static site generator](../concepts/static-site-generators.md), [Git authoring workflows for writers](../concepts/git-authoring.md), [Style guides and terminology management](../concepts/style-guide.md), [Reproducible environments](../concepts/reproducible-environments.md), [Agent-ready content](../concepts/agent-ready-content.md), [RAG pipelines](../concepts/rag.md). Each step below repeats what it assumes.

## 1. [Docs-as-code](../concepts/docs-as-code.md)

`core` · read it · 2h

Running documentation through Git, CI builds, linting, link and sample checks, and automated publishing.

## 2. [Diátaxis](../concepts/diataxis.md)

`core` · read it · 2h

Deciding whether a page is a tutorial, a how-to, reference or explanation, and keeping it to one of them.

Assumes, from outside this path: [Information architecture](../concepts/information-architecture.md).

## 3. [Content models](../concepts/content-model.md)

`core` · practise it · 4h

Defining the types of content your team writes and the fields each one must carry.

Assumes, from outside this path: [Information architecture](../concepts/information-architecture.md).

## 4. [MkDocs and Material](../concepts/mkdocs.md)

`core` · practise it · 4h

Building and maintaining a documentation site on MkDocs with the Material theme.

Assumes, from outside this path: [Choosing a static site generator](../concepts/static-site-generators.md).

## 5. [Documentation CI](../concepts/documentation-ci.md)

`core` · practise it · 4h

Running automated checks on every documentation change before it merges.

Builds on, earlier in this path: Docs-as-code.

Assumes, from outside this path: [Git authoring workflows for writers](../concepts/git-authoring.md).

## 6. [Link checking](../concepts/link-checking.md)

`core` · read it · 2h

Catching broken links before readers do, in CI and on the published site.

Builds on, earlier in this path: Docs-as-code.

## 7. [Prose linting with Vale](../concepts/prose-linting.md)

`core` · practise it · 3h

Enforcing your style guide automatically with Vale, so reviews argue with a rule rather than a person.

Assumes, from outside this path: [Style guides and terminology management](../concepts/style-guide.md).

## 8. [Code-sample validation](../concepts/code-sample-validation.md)

`core` · build something · 5h

Proving every code sample in the docs still runs and still produces what the page says.

Builds on, earlier in this path: Docs-as-code.

## 9. [Building a doc test harness](../concepts/doc-test-harness.md)

`core` · build something · 6h

Building a harness that runs documentation as tests, so broken pages fail the build.

Builds on, earlier in this path: Code-sample validation.

## 10. [Cold-start testing](../concepts/coldstart-testing.md)

`core` · build something · 5h

Testing quickstarts from a clean environment, the way a new developer meets them.

Builds on, earlier in this path: Code-sample validation.

Assumes, from outside this path: [Reproducible environments](../concepts/reproducible-environments.md).

## 11. [llms.txt and llms-full.txt](../concepts/llms-txt.md)

`core` · read it · 2h

Publishing machine-readable entry points to your docs, such as llms.txt, for AI tools to consume.

Assumes, from outside this path: [Agent-ready content](../concepts/agent-ready-content.md).

## 12. [Chunking strategies](../concepts/chunking.md)

`core` · build something · 5h

Splitting content into pieces a RAG system, internal assistant or agent can retrieve on their own.

Assumes, from outside this path: [Agent-ready content](../concepts/agent-ready-content.md).

## 13. [Model Context Protocol](../concepts/mcp.md)

`core` · build something · 5h

Exposing documentation and tools to AI assistants through Model Context Protocol servers.

Assumes, from outside this path: [Agent-ready content](../concepts/agent-ready-content.md).

## 14. [Evaluating retrieval](../concepts/retrieval-evaluation.md)

`core` · build something · 6h

Building question sets that measure whether retrieval finds the right content.

Assumes, from outside this path: [RAG pipelines](../concepts/rag.md).

## 15. [Publishing in public](../concepts/publishing-in-public.md)

`supporting` · read it · 4h

Publishing your documentation tooling and work openly, and doing it safely.
