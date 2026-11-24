---
title: The lab engineer
summary: Taking a lab from a working draft to one that is tested nightly, published
  on evidence, safe for learners and portable.
diataxis: placeholder
audience: new-user
generated: true
---


# The lab engineer

**Who this is for.** Someone who builds, tests and publishes hands-on labs that run in real cloud accounts.

Taking a lab from a working draft to one that is tested nightly, published on evidence, safe for learners and portable.

**9 concepts, roughly 43 hours.** The order matters:
where a step builds on an earlier one, it says so.

**Assumed before step 1.** This path does not teach [Docs-as-code](../concepts/docs-as-code.md), [Git authoring workflows for writers](../concepts/git-authoring.md), [Golden paths](../concepts/golden-paths.md), [Security guidance as encoded standard](../concepts/security-documentation.md) and [Single-sourcing and content reuse](../concepts/single-sourcing.md). Each step below repeats what it assumes.

**Shared with other paths.** 4 of these steps, roughly 18 hours, also appear in another path. Each is marked below; if you have done it there, skip it here.

## 1. [Code-sample validation](../concepts/code-sample-validation.md)

`core` · build something · 5h

Proving every code sample in the docs still runs and still produces what the page says.

Assumes, from outside this path: [Docs-as-code](../concepts/docs-as-code.md).

Also in: [A working result in a weekend](prove-it.md) and [The documentation engineer](docs-engineer.md).

## 2. [Documentation CI](../concepts/documentation-ci.md)

`core` · practice it · 4h

Running automated checks on every documentation change before it merges.

Assumes, from outside this path: [Docs-as-code](../concepts/docs-as-code.md) and [Git authoring workflows for writers](../concepts/git-authoring.md).

Also in: [The first week](first-week.md), [A working result in a weekend](prove-it.md) and [The documentation engineer](docs-engineer.md).

## 3. [Reproducible environments](../concepts/reproducible-environments.md)

`supporting` · build something · 4h

Making sure every exercise starts from an environment a reader can recreate exactly.

Assumes, from outside this path: [Golden paths](../concepts/golden-paths.md).

## 4. [Cold-start testing](../concepts/coldstart-testing.md)

`core` · build something · 5h

Testing quickstarts from a clean environment, the way a new developer meets them.

Builds on, earlier in this path: Code-sample validation and Reproducible environments.

Also in: [A working result in a weekend](prove-it.md) and [The documentation engineer](docs-engineer.md).

## 5. [Ephemeral lab environments](../concepts/ephemeral-environments.md)

`supporting` · build something · 6h

Standing up a real cloud environment for every lab run, checking the lab against it, and proving the teardown left nothing running.

Builds on, earlier in this path: Reproducible environments and Cold-start testing.

## 6. [Lab publishing pipelines](../concepts/lab-publishing.md)

`supporting` · build something · 5h

Shipping hands-on labs through gates, versions and channels, so a broken lab is stopped before learners meet it and a published one can be pulled or rolled back.

Builds on, earlier in this path: Ephemeral lab environments and Documentation CI.

## 7. [Learner sandbox guardrails](../concepts/learner-sandbox-guardrails.md)

`supporting` · build something · 5h

Letting a learner do everything the lab needs in a real cloud account, and nothing that breaks the account, the bill or the lab.

Builds on, earlier in this path: Ephemeral lab environments.

Assumes, from outside this path: [Security guidance as encoded standard](../concepts/security-documentation.md).

## 8. [Multi-platform parity](../concepts/multi-platform-parity.md)

`supporting` · build something · 4h

Documenting one product that developers reach through a first-party API and several cloud platforms, so each reader learns what is true on their route.

Builds on, earlier in this path: Code-sample validation.

Assumes, from outside this path: [Single-sourcing and content reuse](../concepts/single-sourcing.md).

Also in: [The content architect](content-architect.md).

## 9. [Labs for isolated regions](../concepts/isolated-region-labs.md)

`supporting` · build something · 5h

Making a lab that runs in one AWS partition run in another, including isolated regions with no route to the public internet.

Builds on, earlier in this path: Lab publishing pipelines and Multi-platform parity.
