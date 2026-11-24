---
title: The content architect
summary: From a folder of Markdown to a modeled, governed, machine-readable corpus.
diataxis: placeholder
audience: new-user
generated: true
---


# The content architect

**Who this is for.** A writer or engineer who owns structure across a growing corpus.

From a folder of Markdown to a modeled, governed, machine-readable corpus.

**17 concepts, roughly 60 hours.** The order matters:
where a step builds on an earlier one, it says so.

**Assumed before step 1.** This path does not teach [Prose linting with Vale](../concepts/prose-linting.md), [Code-sample validation](../concepts/code-sample-validation.md), [Docs-as-code](../concepts/docs-as-code.md) and [Extracting tribal knowledge](../concepts/sme-interviews.md). Each step below repeats what it assumes.

**Shared with other paths.** 5 of these steps, roughly 16 hours, also appear in another path. Each is marked below; if you have done it there, skip it here.

## 1. [Information architecture](../concepts/information-architecture.md)

`core` · practice it · 4h

Deciding how content is modeled, classified and tagged so people can navigate it and machines can retrieve it.

## 2. [Diátaxis](../concepts/diataxis.md)

`core` · read it · 2h

Deciding whether a page is a tutorial, a how-to, reference or explanation, and keeping it to one of them.

Builds on, earlier in this path: Information architecture.

Also in: [The first week](first-week.md), [A working result in a weekend](prove-it.md) and [The developer educator](developer-educator.md).

## 3. [Content models](../concepts/content-model.md)

`core` · practice it · 4h

Defining the types of content your team writes and the fields each one must carry.

Builds on, earlier in this path: Information architecture.

Also in: [A working result in a weekend](prove-it.md) and [The KnowledgeOps path](knowledgeops.md).

## 4. [Taxonomy and controlled vocabularies](../concepts/taxonomy.md)

`core` · practice it · 3h

Agreeing the terms content is classified by, and keeping that vocabulary closed and consistent.

Builds on, earlier in this path: Content models.

## 5. [Metadata for navigation and retrieval](../concepts/metadata.md)

`core` · practice it · 3h

Tagging content so navigation, search and AI retrieval can all find the right page.

Builds on, earlier in this path: Content models.

Also in: [The KnowledgeOps path](knowledgeops.md) and [Found by search and answer engines](answer-engines.md).

## 6. [Style guides and terminology management](../concepts/style-guide.md)

`supporting` · read it · 2h

Keeping voice and terminology consistent across many authors, and enforcing it in the same tools as code.

Builds on, earlier in this path: Taxonomy and controlled vocabularies.

## 7. [Detecting terminology drift](../concepts/terminology-drift.md)

`supporting` · practice it · 3h

Detecting when the words in your docs drift away from the words in the product.

Builds on, earlier in this path: Taxonomy and controlled vocabularies.

Assumes, from outside this path: [Prose linting with Vale](../concepts/prose-linting.md).

## 8. [Security guidance as encoded standard](../concepts/security-documentation.md)

`supporting` · practice it · 3h

Encoding security guidance into templates, validators and workflows rather than static pages.

Builds on, earlier in this path: Style guides and terminology management.

## 9. [Single-sourcing and content reuse](../concepts/single-sourcing.md)

`supporting` · practice it · 3h

Writing a fact once and reusing it wherever it appears, so documentation scales across products.

Builds on, earlier in this path: Content models.

## 10. [Localization and translation pipelines](../concepts/localization.md)

`supporting` · build something · 4h

Getting content translated and keeping translations in step with the source as it changes.

Builds on, earlier in this path: Content models and Single-sourcing and content reuse.

## 11. [Multi-platform parity](../concepts/multi-platform-parity.md)

`supporting` · build something · 4h

Documenting one product that developers reach through a first-party API and several cloud platforms, so each reader learns what is true on their route.

Builds on, earlier in this path: Single-sourcing and content reuse.

Assumes, from outside this path: [Code-sample validation](../concepts/code-sample-validation.md).

Also in: [The lab engineer](lab-engineer.md).

## 12. [Content lifecycle and governance](../concepts/content-lifecycle.md)

`supporting` · practice it · 3h

Running content from draft to update to audit to retirement, increasingly with LLM help at each stage.

Builds on, earlier in this path: Content models.

## 13. [Retiring content](../concepts/content-retirement.md)

`supporting` · practice it · 3h

Deciding what to retire, and removing it without breaking what links to it.

Builds on, earlier in this path: Content lifecycle and governance.

## 14. [Content migration](../concepts/content-migration.md)

`supporting` · build something · 6h

Moving a documentation corpus from a wiki or CMS into docs-as-code, deciding page by page what moves, merges or goes, and keeping every old link working.

Builds on, earlier in this path: Retiring content.

Assumes, from outside this path: [Docs-as-code](../concepts/docs-as-code.md).

## 15. [Findability and search design](../concepts/findability.md)

`supporting` · practice it · 3h

Making sure developers and AI assistants can both find and use the page they need.

Builds on, earlier in this path: Metadata for navigation and retrieval.

Also in: [Found by search and answer engines](answer-engines.md).

## 16. [Playbooks and decision guides](../concepts/playbooks.md)

`core` · practice it · 4h

Turning tribal knowledge from engineering, product and operations into playbooks and decision guides.

Assumes, from outside this path: [Extracting tribal knowledge](../concepts/sme-interviews.md).

## 17. [Knowledge architecture](../concepts/knowledge-architecture.md)

`core` · build something · 6h

Working with documentation leads on how knowledge is organized across products, teams and sources.

Builds on, earlier in this path: Information architecture.
