---
title: Ephemeral lab environments
summary: Provisioning a real environment for each lab run, asserting on what happened, and proving the teardown left nothing behind.
diataxis: explanation
audience: developer
concept: ephemeral-environments
tags: [gp, supporting]
---

# Ephemeral lab environments

`supporting` · difficulty 3 · 6h

> Standing up a real cloud environment for every lab run, checking the lab against it, and proving the teardown left nothing running.

!!! warning "One lab, one account, a young record"
    The lifecycle on this page was demonstrated by [coldlab](https://github.com/johnallred/coldlab), which runs one lab against one personal AWS account. Its record is `health/health.jsonl`, which grows with every run, and its summary is generated into `health/HEALTH.md`; every figure below names the run it was read at. Cost per run was measured once, on 2026-11-23, from usage times published prices rather than from a bill, and carries the caveats given with it. Account vending, a catalog of labs, multiple regions and the rest of what coldlab's README lists under "What it deliberately does not prove" are described here and were not built. The drill runs offline on a dated copy of the record; it does not touch AWS.

**Prerequisites:** [Reproducible environments](reproducible-environments.md), [Cold-start testing](coldstart-testing.md)

**Leads to:** [Lab publishing pipelines](lab-publishing.md), [Learner sandbox guardrails](learner-sandbox-guardrails.md)

## What it is

A lab that runs against real infrastructure, tested the way a learner meets it:
provision a fresh environment, run the lab's own steps, assert on what the
cloud actually did, tear the environment down, and then prove the teardown
worked. Every run starts from nothing and ends with nothing.

Two things make it more than a container test. The environment is real, so it
costs money while it exists and behaves with the eventual consistency real
services have. And teardown is not a cleanup step, it is an assertion: a run
that passed every lab check and left a resource behind has failed.

## How this applies to your role

This matters because hands-on labs are only as good as the account they run in, and labs
against cloud services rot without anyone editing them. A service changes a
default, a quota tightens, an organization adds a policy, and the lab that
worked at launch fails on step four for every learner who tries it.

On a Tuesday it looks like this. A workshop is on Thursday. The lab passed
when it was written, and nobody has run it since. You run it by hand, it
works, and you call it ready. On Thursday forty people provision forty
environments, two of the steps behave differently from your run because a
queue answered a short poll with nothing, and one environment never tears down
because a resource outside the stack kept it alive. The first you hear of the
leak is the bill.

The answer is to run the lab on a schedule, record every run, and read the
record. A lab that passes once tells you it can work. A lab with a record
tells you how often it works, how long it takes, and which check is unreliable.

## The golden path

Read a lab's health record, size what a nightly catalog would cost,
and verify a teardown against the services rather than against a tag index.
About thirty minutes.

The analysis is committed as `drills/lab_lifecycle.py`, which holds the three
files below and a test that keeps them identical to this page. The runs and
checks are coldlab's `health/health.jsonl` as of 2026-11-24T00:01Z, reshaped
into two tables, with durations rounded and errors summarized. The teardown
rows are illustrative except the event source mapping, which is the case
coldlab met on its first real teardown.

**Step 1: the runs and their checks**

Each run provisions the stack, runs the steps a student is told to type,
asserts on the result and tears down. `P` and `F` are a check's result in that
run; `-` means the check did not run, because the run stopped first. Gating
checks set the exit code; advisory ones are recorded but do not.

```bash
mkdir -p lab-drill && cd lab-drill
cat > runs.csv <<'DATA'
run,seconds,passed,stopped_by
2026-11-19T23:00Z,19,no,deploy refused by an organisation policy
2026-11-23T21:22Z,398,no,lab step exited 1 (aws s3 ls on an empty prefix)
2026-11-23T21:31Z,492,yes,-
2026-11-23T21:49Z,453,yes,-
2026-11-23T23:53Z,478,yes,-
DATA
cat > checks.csv <<'DATA'
check,gating,r1,r2,r3,r4,r5
run.completed,yes,-,F,P,P,P
dlq.depth,yes,-,-,P,P,P
dlq.receive_count_at_least_max_plus_one,yes,-,-,P,P,P
dlq.receive_count_exact,no,-,-,F,-,-
dlq.receive_count_in_observed_set,no,-,-,-,P,P
dlq.sent_timestamp_preserved,yes,-,-,P,P,P
bucket.failing_file_absent,yes,-,-,P,P,P
bucket.success_file_present,yes,-,-,P,P,P
timing.redrive_within_tolerance,no,-,-,P,P,P
teardown.stack_deleted,yes,P,P,P,P,P
teardown.no_leaks,yes,P,P,P,P,P
teardown.all_tagged_resolved,yes,P,P,P,P,P
DATA
```

**Step 2: what the tag query found after a teardown**

The tagging API listed these ARNs after the stack was deleted. The second
column is the exit code of the command that asks the owning service whether
the resource still exists: zero means it does, non-zero means it does not, and
`-` means there is no command for that kind of resource.

```bash
cat > teardown.csv <<'DATA'
arn,describe_exit
arn:aws:cloudformation:us-east-2:111122223333:stack/ColdlabSqsRetry/1a2b3c,254
arn:aws:lambda:us-east-2:111122223333:event-source-mapping:6f1e2a9c,254
arn:aws:logs:us-east-2:111122223333:log-group:/aws/lambda/ColdlabWorker,0
arn:aws:states:us-east-2:111122223333:stateMachine:ColdlabRetry,-
DATA
curl -sO https://raw.githubusercontent.com/johnallred/fieldguide/main/drills/lab_lifecycle.py
```

**Step 3: run the report**

```bash
python3 lab_lifecycle.py runs.csv checks.csv teardown.csv
```

```
step 1: what the record says
  runs 5, passed 3 (60%)
  failed 2026-11-19T23:00Z after 19s: deploy refused by an organisation policy
  failed 2026-11-23T21:22Z after 398s: lab step exited 1 (aws s3 ls on an empty prefix)
  flaky: run.completed (1 of 4 runs failed)
  advisory, failed every time it ran, never decided a run: dlq.receive_count_exact
  median duration: 453s over all runs, 478s over full lifecycles

step 2: what a nightly catalogue costs in time
  200 labs x 478s = 26.6 hours, one after another
  to finish in 4 hours: 7 labs running at once

step 3: is anything left?
  stack/ColdlabSqsRetry/1a2b3c                  gone: its service says so, the index was stale
  event-source-mapping:6f1e2a9c                 gone: its service says so, the index was stale
  log-group:/aws/lambda/ColdlabWorker           LEAK: its service still describes it
  stateMachine:ColdlabRetry                     unresolved: nothing here can ask its service

  tag query alone would report: 4 leftover resource(s)
  PASS  teardown.stack_deleted
  FAIL  teardown.no_leaks  (log-group:/aws/lambda/ColdlabWorker)
  FAIL  teardown.all_tagged_resolved  (stateMachine:ColdlabRetry)
```

It exits 1, because two of the three teardown checks failed.

**Step 4: read the record**

In this snapshot, two of five runs failed, and neither failure was the lab
being wrong. The
first stopped at deploy, nineteen seconds in, because an organization policy
refused a check the deploy tool makes, so every teardown check is green and
nothing else ran. A run that fails before the lab starts is a fact about the
account, and it belongs in the record as much as a lab failure does.

The second is the useful one. `run.completed` is flaky: it failed once and
passed three times. In coldlab that was a real defect, not noise. The lab tells
the student to list an S3 prefix to confirm a file never landed, and
`aws s3 ls` exits 1 when the prefix is empty, which is the success case. The
harness treated every non-zero exit as failure. The fix was to let the lab
document declare the exit code each step expects. A flaky check is the record
pointing at an assumption someone got wrong.

`dlq.receive_count_exact` failed the only time it ran, and the run still
passed, because it was advisory. That is the mechanism working: the receive
count was 5 on the hand run and 4 on the automated ones, so an exact value was
never a real expectation. It was retired in favor of a floor, which gates,
and the values ever seen, `[5, 4]`, became a drift detector that flags a new
one without failing the run.

**Step 5: size a catalog, in time and then in money**

In this snapshot the median over all runs is 453 seconds, the figure
coldlab's generated summary showed after the run of 2026-11-23T23:53Z; the
median over runs that went the whole way is 478. Use the second for planning,
because failed runs are short, and recompute both from the record rather than
copying either. Two hundred labs is 26.6 hours
run one after another, so the first decision a catalog forces is concurrency,
not cost: seven at once to fit a four-hour window, and seven at once means
seven stacks, seven sets of quotas and seven teardowns in flight.

Then cost, in four parts: what the resources cost, what the CI costs, which
dominates, and where that says to spend effort. coldlab's README section "What
a run costs" measured it on 2026-11-23 from four recorded runs.

- **Resources.** Lambda compute and requests plus SQS requests came to about
  $0.00003 a run.
- **CI.** The same run took 8.5 minutes of a Linux 2-core [GitHub-hosted](github-actions.md)
  runner, at $0.006 a minute: $0.051.
- **Which dominates.** The runner, by about seventeen hundred times. At two
  hundred labs a night that is roughly $0.18 a month of AWS against $306 a
  month of CI, and on public repositories the CI line is zero, because standard
  runners are free there.
- **Where to spend effort.** Not on the lab's infrastructure, which is close to
  free, but on duration: the wall clock is the bill, and on a public repository
  it is the only bill. Measured in runner minutes, two hundred labs is about 28
  hours a night, a little more than the 26.6 above because the runner also
  spends time setting up the job.

Why it tracks duration: of the roughly 78 SQS requests a run makes that
CloudWatch counts, 68 are empty receives, the event source mapping polling an
empty queue for as long as the stack exists. The lab itself sends two messages.
Resource cost follows stack lifetime, not lab activity, and so do runner
minutes.

The caveats travel with the figures. The AWS lines are measured usage
multiplied by published unit prices, not a bill. The Lambda rates come from
worked examples on AWS's pricing page, which are stated for N. Virginia rather
than Ohio, where the lab runs, because the page's rate tables did not render.
The SQS rate is the one coldlab used, and its published table did not render
either, so treat that line as approximate. None of this moves the conclusion,
because the gap is three orders of magnitude. If you quote one thing, quote the
ratio.

**Step 6: read the teardown three ways**

The tag query alone reports four leftover resources. Two of them are gone: the
index was stale, which is exactly what coldlab measured when the tag query
listed an event source mapping that Lambda said did not exist. One is a real
leak, the only line that costs money. One cannot be checked at all, and is
reported as unresolved rather than as clean, because "I could not check" is
not "it is gone".

**What you built.** A reading of a lab's record that separates account
failures from lab failures, a flaky check traced to its cause, a catalog sized
in hours, and a teardown verdict that a tag index cannot fool.

## Reference

### The lifecycle

| Phase | What it does | What can go wrong |
|---|---|---|
| Provision | Deploy a fresh stack, named and tagged for this run | Policy denials, quotas, a region default that is not the one you meant |
| Run | Execute the steps the learner is told to type, from the lab document | A step whose non-zero exit means success, eventual consistency |
| Assert | Compare what happened with recorded expectations | Expectations guessed rather than measured |
| Tear down | Delete the stack in a `finally` block | A crash, timeout or kill before cleanup runs |
| Verify | Prove nothing is left | A stale index, untagged resources, resources outside the stack |
| Record | Append the run to a history | Nothing, if it is append-only and committed |

### Teardown is three checks

| Check | Catches | Misses |
|---|---|---|
| The stack is gone | Anything the stack owns that failed to delete | Resources created outside the stack |
| No tagged resource survives, after resolving each ARN | Leaks outside the stack that carry the run's tags | Resources that carry no tags |
| Every tagged ARN was resolved | Resource kinds nobody wrote a resolver for | Nothing; that is its job |

Neither of the first two is enough. In coldlab, 8 of the stack's 15 resources
carry the lab tags, because generated policies and the S3 auto-delete
provider do not, so the tag check alone misses seven of them, and the stack check misses
anything created outside it.

### Flake rate as a signal

| Pattern in the record | Means |
|---|---|
| A check that always fails | A broken lab or a broken check; easy to see |
| A check that sometimes fails | An unexamined assumption: timing, consistency, an exit code |
| A run that fails before any lab check | The account or its policies, not the lab |
| An advisory check that disagrees with itself | The expectation was never a single value |

### Claims generated from the record

An observation belongs in the record. Only a value something asserts against
belongs in a file beside the code. coldlab keeps the receive counts ever seen,
`[5, 4]`, in `expected.yaml`, because the harness reads that set as its drift
detector: it is an expectation. Redrive timings are observations, recorded per
run in `health/health.jsonl`, and `expected.yaml` now points there instead of
listing them.

It learned that the usual way. A hand-kept list of redrive timings went stale
within three runs, disagreeing with the record it copied, and the README said
there was no nightly run for a while after there was one. Neither was a cloud
failure. Both were a claim maintained by hand next to a system that already
knew the answer. A lab environment's health claims should be generated from
its records, because a hand-maintained claim about an automated system rots at
the speed the system runs. This page follows the same rule: its figures name
the run they were read at.

### What a catalog in production adds

| Here | In production |
|---|---|
| One personal account, isolated by stack name and tag | A throwaway account per learner or per run, provisioned through the organization and closed afterwards |
| One lab | A catalog, run concurrently in a window |
| One region | The [regions learners use](isolated-region-labs.md) |
| Cost from usage times published prices | Cost attributed per lab by cost allocation tags, activated in the management account |

### Why the bill could not answer

Two reasons, and the second is the one that carries over. Free tier absorbs a
run at this volume, so a personal account bills a catalog at nothing. And
coldlab's account is a linked account in an AWS Organization, where
`aws ce update-cost-allocation-tags-status` is refused: activating a cost
allocation tag needs the management account. coldlab tags every resource it
creates and still gets no cost attribution. The team that runs labs is usually
not the team that owns the management account, so "tag everything and read
Cost Explorer" is advice that fails in the common case. Usage from CloudWatch,
which is attributable by resource name and needs no billing access, multiplied
by published prices, is what works.

AWS calls its account-provisioning service Account Factory, part of Control
Tower: it provisions member accounts in an organization and can close or
repurpose them. coldlab does not use it, and nothing on this page shows it
working.

### Sources

Opened and checked on 2026-11-23, all in the coldlab repository:

- [`README.md`](https://github.com/johnallred/coldlab/blob/main/README.md): the `finally` teardown, the five measured behaviors, gating and advisory checks, and "What a run costs": the per-run figures, the method and why the bill could not be used. Its section "What it deliberately does not prove" covers account vending, one lab rather than a catalog, and a single region and account.
- [`health/HEALTH.md`](https://github.com/johnallred/coldlab/blob/main/health/HEALTH.md): the generated summary (runs, pass rate, median duration, flaky checks), current as of its last run.
- [`lab/sqs-retry/expected.yaml`](https://github.com/johnallred/coldlab/blob/main/lab/sqs-retry/expected.yaml): the stale tag index, the two required teardown checks and 8 of 15 resources tagged. It keeps `receive_count_observed` as an expectation and leaves redrive observations to the record.
- [`harness/arns.py`](https://github.com/johnallred/coldlab/blob/main/harness/arns.py) and [`harness/checks.py`](https://github.com/johnallred/coldlab/blob/main/harness/checks.py): resolution of each ARN against its service, and the three teardown checks.
- [`health/health.jsonl`](https://github.com/johnallred/coldlab/blob/main/health/health.jsonl): the five run records this drill reshapes.

And outside sources, opened the same day:

- AWS, [Provision and manage accounts with Account Factory](https://docs.aws.amazon.com/controltower/latest/userguide/account-factory.html), AWS Control Tower User Guide.
- AWS, [AWS Lambda pricing](https://aws.amazon.com/lambda/pricing/): the $0.0000166667 per GB-second and $0.20 per million requests rates appear in worked examples stated for N. Virginia; the rate table did not render.
- AWS, [Amazon SQS pricing](https://aws.amazon.com/sqs/pricing/): the request-tier table did not render, so the SQS rate was not checked here.
- GitHub, [Actions runner pricing](https://docs.github.com/en/billing/reference/actions-runner-pricing): $0.006 a minute for a standard Linux 2-core runner; and [GitHub Actions billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions): standard runners in public repositories are free.

## Explaining it to your team

**How to explain it.** Lead with the record, not the harness, and say which
run you read it at. At the snapshot on this page that sounded like: "As of last
night's run, the lab has run five times and three passed. One failure was the
account refusing the deploy, and one was a bug in how we read an exit code,
which is fixed. A full run takes about eight minutes. Teardown is checked three
ways on every run and has not left anything behind." Next month the numbers
change and the shape of the sentence does not.

**The follow-up is usually "why not just check the tags?".** Because the tag
index is eventually consistent and incomplete. It reported a resource that had
already been deleted, and it never sees the untagged half of the stack. A leak
detector that cries wolf gets ignored, and then the real leak is ignored with
it, so every ARN the index returns is checked against the service that owns it.

**The tradeoff to name.** Most of a run is `cdk deploy` and `cdk destroy`,
so the obvious saving is a warm stack, reset between runs. It would cut the
dominant cost, runner time, and it would delete the check that found the stale
tag index, because a stack that is never destroyed has no teardown to verify.
coldlab keeps deploy and destroy per run, deliberately. Present it as a
decision with a cost on both sides rather than as an optimization, because
asking for teardown as an assertion and for a low cost per run is exactly where
the two pull apart. Separately: a handful of runs proves the loop closes and
says nothing yet about reliability, so do not promise a flake rate until the
record holds enough runs to state one.

**One sharper point.** The lab document should be the step list. When the
harness runs the commands a student is told to type, instead of its own copy
of them, the test cannot drift from the lab, and a step that only works on the
author's machine fails in the record before it fails in a workshop.

## Putting it into practice

**The work product.** A harness that provisions, runs, asserts, tears down
and verifies one lab, an append-only health record, and a generated summary
that says how often the lab passes and how long it takes.

**Three things to do, in order:**

1. Run the golden path, then pick the one lab in your catalog that runs
   against a cloud service and write down every assumption its steps make
   about timing, exit codes and defaults.
2. Make teardown run in a `finally` block and add the three teardown checks,
   with a resolver for each kind of resource the lab creates. An ARN with no
   resolver fails the run until someone writes one.
3. Schedule the lab nightly, append every run to a committed record, and read
   the flaky checks before reading the pass rate.

**How to tell it is working.** The drill above runs in this guide's test suite
and its output is the output quoted here. The lifecycle itself runs in coldlab
against a real account, with one lab, a young record and one cost measurement,
so the [demonstrated](../demonstrated.md) page records the concept as partial.
In your own work, the sign is that a lab breaks in the record before it breaks
in front of learners, and that nobody has opened the billing console to find
a leak.

## Related

- [Reproducible environments](reproducible-environments.md), the same idea for a local machine
- [Cold-start testing](coldstart-testing.md), testing from nothing, without a cloud account
- [Workshops and hands-on labs](workshops.md), where these environments are used
- [Documentation CI](documentation-ci.md), where a scheduled run like this one lives
- [Code-sample validation](code-sample-validation.md), the same assertion habit applied to samples
