---
title: Reference and releases
summary: Reference generated from the source, checked against it, and versioned with
  each release.
diataxis: placeholder
audience: new-user
generated: true
---


# Reference and releases

**Who this is for.** Someone who owns the API reference and the versioned docs for a product that ships releases.

Reference generated from the source, checked against it, and versioned with each release.

**8 concepts, roughly 29 hours.** The order matters:
where a step builds on an earlier one, it says so.

**Assumed before step 1.** This path does not teach [Markdown and its dialects](../concepts/markdown.md), [Choosing a static site generator](../concepts/static-site-generators.md), [Docs-as-code](../concepts/docs-as-code.md), [Code-sample validation](../concepts/code-sample-validation.md), [Documentation CI](../concepts/documentation-ci.md) and [Technical writing as a craft](../concepts/technical-writing.md). Each step below repeats what it assumes.

**Shared with other paths.** 1 of these steps, roughly 4 hours, also appears in another path. Each is marked below; if you have done it there, skip it here.

## 1. [reStructuredText](../concepts/restructuredtext.md)

`supporting` · practice it · 3h

Maintaining docs written in reStructuredText, usually alongside a Sphinx build.

Assumes, from outside this path: [Markdown and its dialects](../concepts/markdown.md).

## 2. [Sphinx](../concepts/sphinx.md)

`core` · build something · 6h

Building and maintaining documentation with Sphinx, especially for Python projects.

Builds on, earlier in this path: reStructuredText.

Assumes, from outside this path: [Choosing a static site generator](../concepts/static-site-generators.md).

## 3. [Generated API reference](../concepts/api-reference-generation.md)

`core` · practice it · 4h

Producing reference documentation from the code itself, so it assumes no prior context and stays current.

Assumes, from outside this path: [Docs-as-code](../concepts/docs-as-code.md).

## 4. [OpenAPI and REST reference](../concepts/openapi.md)

`supporting` · practice it · 4h

Documenting any HTTP API from its contract, and keeping that contract and the reference in step.

Builds on, earlier in this path: Generated API reference.

## 5. [Doctests and executable docstrings](../concepts/doctests.md)

`supporting` · practice it · 2h

Keeping examples in docstrings executable, so they fail when the code changes.

Assumes, from outside this path: [Code-sample validation](../concepts/code-sample-validation.md).

## 6. [Versioned documentation](../concepts/versioning.md)

`supporting` · practice it · 3h

Publishing documentation for more than one release at once, and keeping readers on the right version.

Assumes, from outside this path: [Choosing a static site generator](../concepts/static-site-generators.md).

## 7. [Release readiness for documentation](../concepts/release-readiness.md)

`core` · practice it · 4h

Making documentation part of what "ready to release" means, enforced rather than remembered.

Assumes, from outside this path: [Documentation CI](../concepts/documentation-ci.md).

Also in: [The writer who builds](writer-who-builds.md).

## 8. [Release notes and changelogs](../concepts/release-notes.md)

`supporting` · practice it · 3h

Writing what changed in each release for the people who have to act on it, and making sure the version number tells them how much.

Builds on, earlier in this path: Release readiness for documentation.

Assumes, from outside this path: [Technical writing as a craft](../concepts/technical-writing.md).
