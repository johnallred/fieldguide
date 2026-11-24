---
title: The documentation engineer
summary: Every automated gate that stops documentation rotting, in the order worth
  adding them.
diataxis: placeholder
audience: new-user
generated: true
---


# The documentation engineer

**Who this is for.** Someone building the pipeline rather than writing the pages.

Every automated gate that stops documentation rotting, in the order worth adding them.

**18 concepts, roughly 69 hours.** The order matters:
each step assumes the ones above it.

**Assumed before step 1.** This path does not teach [Style guides and terminology management](../concepts/style-guide.md), [Diátaxis](../concepts/diataxis.md), [Reproducible environments](../concepts/reproducible-environments.md), [Content lifecycle and governance](../concepts/content-lifecycle.md), [Content models](../concepts/content-model.md). Each step below repeats what it assumes.

**Shared with other paths.** 10 of these steps, roughly 39 hours, also appear in another path. Each is marked below; if you have done it there, skip it here.

## 1. [Docs-as-code](../concepts/docs-as-code.md)

`core` · read it · 2h

Running documentation through Git, CI builds, linting, link and sample checks, and automated publishing.

Also in: [The first week](first-week.md), [A working result in a weekend](prove-it.md).

## 2. [Git authoring workflows for writers](../concepts/git-authoring.md)

`core` · practise it · 4h

Writing in Git: branches, pull requests and review, in Markdown or RST, built by a static site generator.

Builds on, earlier in this path: Docs-as-code.

Also in: [The first week](first-week.md).

## 3. [Documentation CI](../concepts/documentation-ci.md)

`core` · practise it · 4h

Running automated checks on every documentation change before it merges.

Builds on, earlier in this path: Docs-as-code, Git authoring workflows for writers.

Also in: [The first week](first-week.md), [A working result in a weekend](prove-it.md), [The lab engineer](lab-engineer.md).

## 4. [GitHub Actions for docs](../concepts/github-actions.md)

`core` · practise it · 4h

Writing and maintaining the CI workflows that build, check and publish your documentation.

Builds on, earlier in this path: Documentation CI.

## 5. [Link checking](../concepts/link-checking.md)

`core` · read it · 2h

Catching broken links before readers do, in CI and on the published site.

Builds on, earlier in this path: Docs-as-code.

Also in: [The first week](first-week.md), [A working result in a weekend](prove-it.md).

## 6. [Prose linting with Vale](../concepts/prose-linting.md)

`core` · practise it · 3h

Enforcing your style guide automatically with Vale, so reviews argue with a rule rather than a person.

Assumes, from outside this path: [Style guides and terminology management](../concepts/style-guide.md).

Also in: [A working result in a weekend](prove-it.md).

## 7. [Writing custom linters](../concepts/custom-linters.md)

`supporting` · build something · 5h

Writing your own content checks when an off-the-shelf linter cannot express the rule.

Builds on, earlier in this path: Prose linting with Vale.

## 8. [Accessibility checks](../concepts/accessibility.md)

`supporting` · practise it · 3h

Making sure published content is usable by everyone, which applies to every page you ship.

Builds on, earlier in this path: Documentation CI.

## 9. [Code-sample validation](../concepts/code-sample-validation.md)

`core` · build something · 5h

Proving every code sample in the docs still runs and still produces what the page says.

Builds on, earlier in this path: Docs-as-code.

Also in: [A working result in a weekend](prove-it.md), [The lab engineer](lab-engineer.md).

## 10. [Diagrams as code](../concepts/diagrams-as-code.md)

`supporting` · practise it · 3h

Keeping architecture and pipeline diagrams in the repository as text, reviewed like code and checked against the system they describe.

Builds on, earlier in this path: Docs-as-code.

## 11. [Building a doc test harness](../concepts/doc-test-harness.md)

`core` · build something · 6h

Building a harness that runs documentation as tests, so broken pages fail the build.

Builds on, earlier in this path: Code-sample validation.

Also in: [A working result in a weekend](prove-it.md).

## 12. [Golden paths](../concepts/golden-paths.md)

`core` · build something · 5h

Designing and maintaining the routes that take a developer from a clean environment to a working result.

Assumes, from outside this path: [Diátaxis](../concepts/diataxis.md).

Also in: [The developer educator](developer-educator.md).

## 13. [Cold-start testing](../concepts/coldstart-testing.md)

`core` · build something · 5h

Testing quickstarts from a clean environment, the way a new developer meets them.

Builds on, earlier in this path: Code-sample validation.

Assumes, from outside this path: [Reproducible environments](../concepts/reproducible-environments.md).

Also in: [A working result in a weekend](prove-it.md), [The lab engineer](lab-engineer.md).

## 14. [Freshness monitoring](../concepts/freshness-monitoring.md)

`core` · practise it · 4h

Checking automatically that content is still current, and routing what is not to a human.

Builds on, earlier in this path: Documentation CI.

Assumes, from outside this path: [Content lifecycle and governance](../concepts/content-lifecycle.md).

## 15. [Preview deployments and publishing](../concepts/preview-deployments.md)

`supporting` · practise it · 3h

Previewing every documentation change as a built site, and publishing it when it merges.

Builds on, earlier in this path: GitHub Actions for docs.

## 16. [Reviewing documentation](../concepts/docs-review.md)

`supporting` · practise it · 3h

Reviewing documentation pull requests for accuracy, structure and style.

Builds on, earlier in this path: Git authoring workflows for writers.

Assumes, from outside this path: [Style guides and terminology management](../concepts/style-guide.md).

Also in: [The writer who builds](writer-who-builds.md).

## 17. [Templates and scaffolding](../concepts/templates-scaffolding.md)

`core` · practise it · 3h

Encoding team standards into templates and scaffolds, so the right shape is the default.

Assumes, from outside this path: [Content models](../concepts/content-model.md).

## 18. [Guided workflows](../concepts/guided-workflows.md)

`core` · build something · 5h

Replacing static instructions with workflows that guide a person through a standard.

Builds on, earlier in this path: Templates and scaffolding.
