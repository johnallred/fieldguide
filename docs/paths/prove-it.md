---
title: Prove it in a weekend
summary: The shortest path through the concepts that produce something reviewable.
diataxis: placeholder
audience: new-user
generated: true
---


# Prove it in a weekend

**Who this is for.** Someone who needs a portfolio artifact before Monday.

The shortest path through the concepts that produce something reviewable.

**15 concepts, roughly 59 hours.** The order matters:
each step assumes the ones above it.

**Assumed before step 1.** This path does not teach [Information architecture](../concepts/information-architecture.md), [Choosing a static site generator](../concepts/static-site-generators.md), [Git authoring workflows for writers](../concepts/git-authoring.md), [Style guides and terminology management](../concepts/style-guide.md), [Reproducible environments](../concepts/reproducible-environments.md), [Agent-ready content](../concepts/agent-ready-content.md), [RAG pipelines](../concepts/rag.md). Each step below repeats what it assumes.

## 1. [Docs-as-code](../concepts/docs-as-code.md)

`core` · read it · 2h

Build and run docs-as-code pipelines: Git authoring, CI/CD builds, linting, link and code-sample validation, and publishing

## 2. [Diátaxis](../concepts/diataxis.md)

`core` · read it · 2h

The dominant framework for documentation structure. Neither posting names it; both describe the problem it solves.

Assumes, from outside this path: [Information architecture](../concepts/information-architecture.md).

## 3. [Content models](../concepts/content-model.md)

`core` · practise it · 4h

content modeling, taxonomy, and metadata

Assumes, from outside this path: [Information architecture](../concepts/information-architecture.md).

## 4. [MkDocs and Material](../concepts/mkdocs.md)

`core` · practise it · 4h

static site generators (Sphinx, MkDocs, Docusaurus, or similar)

Assumes, from outside this path: [Choosing a static site generator](../concepts/static-site-generators.md).

## 5. [Documentation CI](../concepts/documentation-ci.md)

`core` · practise it · 4h

documentation CI

Builds on, earlier in this path: Docs-as-code.

Assumes, from outside this path: [Git authoring workflows for writers](../concepts/git-authoring.md).

## 6. [Link checking](../concepts/link-checking.md)

`core` · read it · 2h

link checking

Builds on, earlier in this path: Docs-as-code.

## 7. [Prose linting with Vale](../concepts/prose-linting.md)

`core` · practise it · 3h

Content quality automation you've built, such as Vale or custom linters, doc test harnesses, or freshness monitoring

Assumes, from outside this path: [Style guides and terminology management](../concepts/style-guide.md).

## 8. [Code-sample validation](../concepts/code-sample-validation.md)

`core` · build something · 5h

link and code-sample validation

Builds on, earlier in this path: Docs-as-code.

## 9. [Building a doc test harness](../concepts/doc-test-harness.md)

`core` · build something · 6h

Content quality automation you've built, such as Vale or custom linters, doc test harnesses, or freshness monitoring

Builds on, earlier in this path: Code-sample validation.

## 10. [Cold-start testing](../concepts/coldstart-testing.md)

`core` · build something · 5h

coldstart testing of quickstarts

Builds on, earlier in this path: Code-sample validation.

Assumes, from outside this path: [Reproducible environments](../concepts/reproducible-environments.md).

## 11. [llms.txt and llms-full.txt](../concepts/llms-txt.md)

`core` · read it · 2h

including llms.txt, MCP-accessible sources, agent skills and context kits, and evaluation sets for answer accuracy

Assumes, from outside this path: [Agent-ready content](../concepts/agent-ready-content.md).

## 12. [Chunking strategies](../concepts/chunking.md)

`core` · build something · 5h

structure and package content for RAG, internal assistants, and agentic workflows

Assumes, from outside this path: [Agent-ready content](../concepts/agent-ready-content.md).

## 13. [Model Context Protocol](../concepts/mcp.md)

`core` · build something · 5h

Ways to stand out: experience building RAG pipelines, AI assistants, MCP servers

Assumes, from outside this path: [Agent-ready content](../concepts/agent-ready-content.md).

## 14. [Evaluating retrieval](../concepts/retrieval-evaluation.md)

`core` · build something · 6h

evaluation sets for answer accuracy

Assumes, from outside this path: [RAG pipelines](../concepts/rag.md).

## 15. [Publishing in public](../concepts/publishing-in-public.md)

`supporting` · read it · 4h

Open source contributions or published work on docs-as-code, AI-assisted documentation, or knowledge engineering
