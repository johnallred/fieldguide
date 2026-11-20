# 01 Ephemeral environment provisioning

Status: ready-for-agent

Category: `gp` (golden paths) or `qa`. Asked for by both postings.

Standing up a disposable environment per learner or per demo, proving the
exercise still works in it, tearing it down, and knowing what a run costs.

## Why it is not `reproducible-environments`

That concept is about which isolation level catches which defect and the
pinning decision, for testing documentation. This is infrastructure with a
lifecycle and a bill.

## What the page has to cover

- The lifecycle: provision, seed, run, assert, tear down, verify nothing survived
- Teardown as an assertion, not an assumption. An orphaned resource is a silent
  recurring cost
- Flake rate rather than pass/fail. A lab that fails one run in twenty is worse
  than one that fails every time, because the second gets fixed and the first
  gets blamed on the learner
- Cost per run, and the arithmetic of a nightly catalog
- Where the real version differs: account vending through an organization

## Demonstration

`coldlab`. Blocked until it exists, so that the `demonstrations.yaml` row is
real rather than aspirational.
