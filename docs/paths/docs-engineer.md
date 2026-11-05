---
title: The documentation engineer
summary: Every automated gate that stops documentation rotting, in the order worth
  adding them.
diataxis: placeholder
audience: new-user
generated: true
---


# The documentation engineer

!!! warning "Generated page"
    This page is generated from `concepts.yaml` by `fieldguide build`.
    Edits here are overwritten. Change the registry instead.


**Who this is for.** Someone building the pipeline rather than writing the pages.

Every automated gate that stops documentation rotting, in the order worth adding them.

**18 concepts, roughly 70 hours.** The order matters:
each step assumes the ones above it.

**Assumed before step 1.** This path does not teach [Style guides and terminology management](../concepts/style-guide.md), [Diátaxis](../concepts/diataxis.md), [Reproducible environments](../concepts/reproducible-environments.md), [Content lifecycle and governance](../concepts/content-lifecycle.md), [Content models](../concepts/content-model.md). Each step below repeats what it assumes.

## 1. [Docs-as-code](../concepts/docs-as-code.md)

`core` · read it · 2h

Build and run docs-as-code pipelines: Git authoring, CI/CD builds, linting, link and code-sample validation, and publishing

## 2. [Git authoring workflows for writers](../concepts/git-authoring.md)

`core` · practise it · 4h

Hands-on docs-as-code experience: Git, pull request review, Markdown/RST, static site generators

Builds on, earlier in this path: Docs-as-code.

## 3. [Documentation CI](../concepts/documentation-ci.md)

`core` · practise it · 4h

documentation CI

Builds on, earlier in this path: Docs-as-code, Git authoring workflows for writers.

## 4. [GitHub Actions for docs](../concepts/github-actions.md)

`core` · practise it · 4h

CI/CD is named by both; GitHub Actions is the most common implementation of it.

Builds on, earlier in this path: Documentation CI.

## 5. [Link checking](../concepts/link-checking.md)

`core` · read it · 2h

link checking

Builds on, earlier in this path: Docs-as-code.

## 6. [Prose linting with Vale](../concepts/prose-linting.md)

`core` · practise it · 3h

Content quality automation you've built, such as Vale or custom linters, doc test harnesses, or freshness monitoring

Assumes, from outside this path: [Style guides and terminology management](../concepts/style-guide.md).

## 7. [Writing custom linters](../concepts/custom-linters.md)

`supporting` · build something · 5h

Content quality automation you've built, such as Vale or custom linters

Builds on, earlier in this path: Prose linting with Vale.

## 8. [Code-sample validation](../concepts/code-sample-validation.md)

`core` · build something · 5h

link and code-sample validation

Builds on, earlier in this path: Docs-as-code.

## 9. [Doctests and executable docstrings](../concepts/doctests.md)

`supporting` · practise it · 2h

doc test harnesses

Builds on, earlier in this path: Code-sample validation.

## 10. [Building a doc test harness](../concepts/doc-test-harness.md)

`core` · build something · 6h

Content quality automation you've built, such as Vale or custom linters, doc test harnesses, or freshness monitoring

Builds on, earlier in this path: Code-sample validation.

## 11. [Generated API reference](../concepts/api-reference-generation.md)

`core` · practise it · 4h

Write and maintain reference documentation, tutorials, and sample walkthroughs that assume no prior context

Builds on, earlier in this path: Docs-as-code.

## 12. [Golden paths](../concepts/golden-paths.md)

`core` · build something · 5h

Design and maintain golden paths and curriculum that take a developer from a clean environment to a working result

Assumes, from outside this path: [Diátaxis](../concepts/diataxis.md).

## 13. [Cold-start testing](../concepts/coldstart-testing.md)

`core` · build something · 5h

coldstart testing of quickstarts

Builds on, earlier in this path: Code-sample validation.

Assumes, from outside this path: [Reproducible environments](../concepts/reproducible-environments.md).

## 14. [Freshness monitoring](../concepts/freshness-monitoring.md)

`core` · practise it · 4h

with checks for freshness, code accuracy, and terminology drift, and human review where judgment matters

Builds on, earlier in this path: Documentation CI.

Assumes, from outside this path: [Content lifecycle and governance](../concepts/content-lifecycle.md).

## 15. [Preview deployments and publishing](../concepts/preview-deployments.md)

`supporting` · practise it · 3h

and publishing

Builds on, earlier in this path: GitHub Actions for docs.

## 16. [Templates and scaffolding](../concepts/templates-scaffolding.md)

`core` · practise it · 3h

encode standards into templates, validators, and guided workflows

Assumes, from outside this path: [Content models](../concepts/content-model.md).

## 17. [Guided workflows](../concepts/guided-workflows.md)

`core` · build something · 5h

into templates, validators, and guided workflows rather than static documents

Builds on, earlier in this path: Templates and scaffolding.

## 18. [Release readiness for documentation](../concepts/release-readiness.md)

`core` · practise it · 4h

Encode standards (user stories, release readiness, onboarding, security guidance) into templates, validators, and guided workflows rather than static documents

Builds on, earlier in this path: Documentation CI.
