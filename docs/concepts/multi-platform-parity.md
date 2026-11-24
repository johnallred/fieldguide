---
title: Multi-platform parity
summary: Documenting one capability reached through several front doors, a first-party API and cloud marketplaces, where authentication, names, limits and features differ by route.
diataxis: explanation
audience: developer
concept: multi-platform-parity
tags: [craft, supporting]
---

# Multi-platform parity

`supporting` · difficulty 3 · 4h

> Documenting one product that developers reach through a first-party API and several cloud platforms, so each reader learns what is true on their route.

**Prerequisites:** [Single-sourcing and content reuse](single-sourcing.md), [Code-sample validation](code-sample-validation.md)

**Leads to:** [Labs for isolated regions](isolated-region-labs.md)

## What it is

Keeping documentation true for a product that is reached several ways: its
own API and, commonly, one or more cloud marketplaces that resell or host it.
The capability is the same; authentication, model or resource names, regions,
limits and the set of supported features differ from route to route.

The question this concept answers is what to write once and what to write per
platform, and how to know that every claim about a platform has been checked
on that platform.

## How this applies to your role

This matters because the reader on a cloud platform reads the same page as everyone else
and follows it exactly, and the page was written and tested against the
first-party API.

On a Tuesday it looks like this. A developer on a cloud marketplace follows
the batch tutorial, gets a 404 on the batch endpoint, and opens a ticket saying
the documentation is wrong. It is not wrong; it is incomplete. Batches do not
exist on that platform, the sample was only ever run against the first-party
API, and the page's single note about platforms covered authentication on a
different one. Nobody decided to leave that reader out. The page simply had no
way to say what differs, and no test that ran the sample where it claimed to
work.

The same problem exists at much larger scale in real documentation. Anthropic,
for example, keeps separate pages for using Claude on Amazon Bedrock and on
Google Cloud, and those pages cover authentication through each cloud's
identity system, different model identifiers, region and endpoint choices,
lists of features that are not available, request-format differences, and
separate limits and billing. Every one of those is a place where a
single page written for the first-party API would be wrong for someone.

## The golden path

Check a single-sourced page against a capability matrix and against the
results of running its sample on every platform it claims, fix the six gaps,
then measure how much of each reader's page is shared. About thirty minutes.

The check is committed as `drills/parity_check.py`, which holds every file
below and a test that keeps them identical to this page. The platforms and
results are invented.

**Step 1: what each platform supports**

```bash
mkdir -p parity-drill && cd parity-drill
cat > matrix.csv <<'DATA'
feature,direct,cloud-a,cloud-b
streaming,yes,yes,yes
batch,yes,yes,no
auth,API key,IAM role,service account
model name,widget-2,widget.widget-2-v1,widget-2@2026
DATA
```

**Step 2: the page, and what happened when its sample ran**

Platform-specific text goes in `delta` blocks, which a build would show only
to readers of that platform.

```bash
cat > page.md <<'DATA'
---
platforms: direct, cloud-a, cloud-b
features: batch, auth, model name
samples: batch_example.py = direct, cloud-a, cloud-b
---
# Send a batch of requests

Create a client, then submit up to 1,000 requests in one batch with
`client.batches.create()`. Results arrive within 24 hours.

<!-- delta cloud-a: auth -->
On Cloud A, the client authenticates with an IAM role instead of an API key.
<!-- end -->
DATA
cat > results.csv <<'DATA'
sample,platform,result
batch_example.py,direct,pass
batch_example.py,cloud-b,fail
DATA
curl -sO https://raw.githubusercontent.com/johnallred/fieldguide/main/drills/parity_check.py
```

**Step 3: check the page against the platforms**

```bash
python3 parity_check.py matrix.csv page.md results.csv
```

```
DELTA    cloud-b: batch is not available, and the page does not say so
DELTA    cloud-b: auth is 'service account', and the page does not say so
DELTA    cloud-a: model name is 'widget.widget-2-v1', and the page does not say so
DELTA    cloud-b: model name is 'widget-2@2026', and the page does not say so
UNTESTED batch_example.py claims cloud-a and was never run there
FAILS    batch_example.py claims cloud-b and fails there
6 finding(s)
```

Four places where a platform differs and the page is silent, and two claims
about the sample that nobody checked or that are false. The last one is the
404 ticket: the page says the sample runs on Cloud B, the run says it fails,
and the matrix says why.

**Step 4: add the deltas, and claim only what passed**

```bash
cat > page.md <<'DATA'
---
platforms: direct, cloud-a, cloud-b
features: batch, auth, model name
samples: batch_example.py = direct, cloud-a
---
# Send a batch of requests

Create a client, then submit up to 1,000 requests in one batch with
`client.batches.create()`. Results arrive within 24 hours.

<!-- delta cloud-a: auth -->
On Cloud A, the client authenticates with an IAM role instead of an API key.
<!-- end -->
<!-- delta cloud-a: model name -->
On Cloud A, the model is `widget.widget-2-v1`.
<!-- end -->
<!-- delta cloud-b: auth -->
On Cloud B, the client authenticates with a service account.
<!-- end -->
<!-- delta cloud-b: model name -->
On Cloud B, the model is `widget-2@2026`.
<!-- end -->
<!-- delta cloud-b: batch -->
Cloud B has no batch endpoint. Send the requests one at a time and handle
rate limits yourself; the sample on this page does not run there.
<!-- end -->
DATA
cat > results.csv <<'DATA'
sample,platform,result
batch_example.py,direct,pass
batch_example.py,cloud-a,pass
batch_example.py,cloud-b,fail
DATA
python3 parity_check.py matrix.csv page.md results.csv
```

```
0 finding(s)
```

The sample now claims two platforms, both with a passing run, and Cloud B's
readers are told what to do instead. The failing run stays in the results: it
is the evidence for the delta.

**Step 5: how much of each reader's page is shared?**

```bash
python3 parity_check.py --render matrix.csv page.md
```

```
  direct    25 words: 25 shared + 0 for this platform
  cloud-a   47 words: 25 shared + 22 for this platform
  cloud-b   69 words: 25 shared + 44 for this platform
```

The first-party reader sees only shared text. The Cloud B reader sees more text
written for their platform than shared with everyone, which is the signal that
this page has stopped being one page. When per-platform text outweighs shared
text, a separate page per platform, linking back to a shared concept page, is
easier to read and easier to keep true, and that is the shape the Bedrock and
Google Cloud pages take.

**What you built.** A capability matrix as the source of truth for what
differs, a single-sourced page with a delta for every difference it touches,
sample claims backed by a run on every platform, and a measurement that says
when to stop single-sourcing.

## Reference

### What usually differs between routes

| Difference | Why it bites |
|---|---|
| Authentication | Each cloud uses its own identity system, not the product's API keys |
| Resource or model names | The same thing has a different identifier on each platform |
| Regions and endpoints | Availability, pricing and data residency vary by region and endpoint type |
| Supported features | Some features are missing on some routes, or arrive later |
| Request format | Versions, headers or body fields move or change |
| Limits and quotas | Payload sizes, rate limits and quotas are set by the platform |
| Billing and data terms | The platform invoices and its terms govern the data |

### Mechanisms for per-platform content

| Mechanism | How | Good for |
|---|---|---|
| Build-time conditions | Sphinx `only` with tags set by `--tag` or `conf.py`; one build per platform | Separate sites per platform |
| Linked tabs | Material for MkDocs content tabs with `content.tabs.link`, so a reader's platform choice applies across the site | Short deltas inside one page |
| Separate pages | One page per platform, linking to shared concept pages | Deltas that outweigh the shared text |
| A capability matrix | One table, generated from the same data the checks read | Readers comparing platforms before choosing |

Sphinx's `only` directive controls only the content of a document, not its
sections or labels, so whole sections that differ per platform belong in
separate pages, not inside conditions.

### Rules worth enforcing

| Rule | Catches |
|---|---|
| Every platform difference on a covered feature has a delta | Silent gaps like the batch endpoint |
| Every platform a sample claims has a passing run | Samples only ever run on the first-party API |
| The matrix is the single source for what differs | Pages and tables disagreeing |
| Per-platform text is measured | Pages that should have been split |

### Sources

Opened and checked on 2026-11-23:
[Claude on Amazon Bedrock](https://platform.claude.com/docs/en/build-with-claude/claude-on-amazon-bedrock-legacy) and
[Claude models on Google Cloud](https://platform.claude.com/docs/en/build-with-claude/claude-models-on-google-cloud/google-managed), Claude Platform Docs, as a real example of per-platform documentation;
[Sphinx directives: `only`](https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html);
[Material for MkDocs: content tabs](https://squidfunk.github.io/mkdocs-material/reference/content-tabs/).

## Explaining it to your team

**How to explain it.** Lead with the reader who follows the page exactly. "A
developer on Cloud B reads our batch tutorial, does what it says, and gets a
404, because batches do not exist there. The page was not wrong, it was
written for one route. So what each platform supports lives in one matrix,
the page needs a note wherever it covers a feature that differs, and a sample
only claims a platform it has passed on."

**The follow-up is usually "why not just say the samples use the first-party
API".** That is a fine answer for a small difference, and it is honest. It
stops being enough when a large share of readers arrive through a cloud
platform, because then the page is accurate and useless for them, and the
support load lands on the team anyway.

**The tradeoff to name.** Running every sample on every platform costs money
and credentials for each cloud, and keeping a matrix current costs attention
every release. The check is only as good as the matrix, and a matrix nobody
updates produces confident, wrong deltas. Start with the two or three
features most readers use and the platforms most readers arrive on.

**One sharper point.** Parity work has a direction. The first-party API usually
gets features first, so most deltas are about something missing or later on a
platform, and they go stale the day the platform catches up. A delta that says
"not available on Cloud B" needs the same freshness check as any other claim,
or it will keep sending readers to a workaround they no longer need.

## Putting it into practice

**The work product.** A capability matrix for one real product, the delta
check run over the pages that cover its most-used features, and sample runs
on every platform the pages claim.

**Three things to do, in order:**

1. Run the golden path, then write the matrix for one product you document,
   from each platform's own documentation. Expect at least one feature your
   pages describe that a platform does not support.
2. Pick the most-read tutorial and list every platform its samples claim.
   Run them there, or remove the claim.
3. Measure per-platform text on your most platform-heavy page. If any
   platform's share exceeds the shared text, plan the split.

**How to tell it is working.** The drill above runs in this guide's test suite
and its output is the output quoted here. The platforms, matrix and runs are
invented and nothing calls a real cloud, so the
[demonstrated](../demonstrated.md) page records the concept as partial. In your
own docs, the sign is that support tickets from cloud-platform users stop
saying the documentation does not work for them.

## Related

- [Single-sourcing and content reuse](single-sourcing.md), the mechanism, and where it stops paying
- [Code-sample validation](code-sample-validation.md), running samples per route
- [Documentation for partners and internal teams](partner-documentation.md), one corpus for several audiences, a related but different problem
- [Freshness monitoring](freshness-monitoring.md), for deltas that go stale when a platform catches up
- [Versioned documentation](versioning.md), the other axis a page can vary along
