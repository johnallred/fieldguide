---
title: Lab publishing pipelines
summary: Gating a lab document before it ships, promoting immutable lab versions on evidence, and deciding between rollback and fix-forward when a published lab breaks.
diataxis: explanation
audience: developer
concept: lab-publishing
tags: [qa, supporting]
---

# Lab publishing pipelines

`supporting` · difficulty 3 · 5h

> Shipping hands-on labs through gates, versions and channels, so a broken lab is stopped before learners meet it and a published one can be pulled or rolled back.

**Prerequisites:** [Ephemeral lab environments](ephemeral-environments.md), [Documentation CI](documentation-ci.md)

**Leads to:** [Labs for isolated regions](isolated-region-labs.md)

## What it is

The path a lab takes from a curriculum developer's draft to the catalog
learners and instructors use. It does three things a documentation pipeline
does not have to.

It gates the lab document itself, because the document is not only prose: its
commands are what the learner types and what the health harness runs. It
versions labs immutably and moves a version between channels, such as beta
and prod, only on evidence recorded against that exact version. And it decides
what happens when a published lab breaks, which for a lab is a harder question
than for software, because a lab can break without anyone changing it.

## How this applies to your role

This matters because the people writing labs are usually not the people running the
pipeline, and the pipeline is what turns their drafts into something an
instructor can rely on in front of a room.

On a Tuesday it looks like this. A curriculum developer merges an edit to a
lab: a `sleep 120` where a wait used to be declared, and a `pip install` added
for a helper. The site rebuilds and the lab goes live. On Thursday a class in
a network with no route to the public package index fails at that step, and the
health run starts failing intermittently on the sleep. Nobody can say which
version the class used, whether the previous one still works, or whether
pulling the edit would fix it. Every one of those questions has an answer if
the pipeline records versions and evidence; none does if publishing is "merge
and rebuild".

The pipeline's job is to make those questions cheap: a gate that stops the
edit, a version history that says what ran, and a rule for what to do when
prod fails.

## The golden path

Gate a candidate lab document, decide which lab versions move to prod, and
decide rollback or fix-forward for two failing labs. About thirty minutes.

The decisions are committed as `drills/lab_publish.py`, which holds the three
files below and a test that keeps them identical to this page. The labs,
versions and runs are invented. The directive syntax, written as shell
comments so it runs harmlessly if a learner copies a block, is the one
[coldlab](https://github.com/johnallred/coldlab)'s `harness/extract.py` reads.

**Step 1: the candidate document**

A lab document as a curriculum developer would submit it. `# step:` names a
block, and `# exits 1: <why>` declares a non-zero exit that means success.

````bash
mkdir -p publish-drill && cd publish-drill
cat > candidate.md <<'DATA'
# Retries and dead-letter queues

## Send a message

```bash
# step: send
aws sqs send-message --queue-url "$QUEUE_URL" --message-body '{"file":"invoice-9001.csv"}'
```

## Wait for the redrive

```bash
sleep 120
```

## Confirm the file never landed

```bash
# step: confirm absent
# exits 1:
aws s3 ls "s3://$BUCKET/landed/"
```

## Inspect the worker

```bash
# step: inspect worker
pip install sqs-inspect
aws lambda get-function --function-name arn:aws:lambda:us-east-2:111122223333:function:Worker
```
DATA
````

**Step 2: the versions and the health runs**

Each version is named by a hash of its content and never edited after
publishing. Each run records which version it tested and in which channel.

```bash
cat > versions.csv <<'DATA'
lab,version,content,published
sqs-retry,1,a1b2c3,2026-09-30
sqs-retry,2,c3d4e5,2026-11-02
sqs-retry,3,e5f6a7,2026-11-19
s3-events,1,0a0b0c,2026-09-15
s3-events,2,1c1d1e,2026-11-18
ec2-basics,1,9f8e7d,2026-08-01
vpc-basics,1,4d5e6f,2026-10-10
vpc-basics,2,7a8b9c,2026-11-21
DATA
cat > runs.csv <<'DATA'
lab,version,date,channel,passed
sqs-retry,2,2026-11-17,prod,yes
sqs-retry,2,2026-11-18,prod,yes
sqs-retry,2,2026-11-19,prod,yes
sqs-retry,3,2026-11-20,beta,yes
sqs-retry,3,2026-11-21,beta,yes
sqs-retry,3,2026-11-22,beta,yes
s3-events,1,2026-11-16,prod,yes
s3-events,1,2026-11-17,prod,yes
s3-events,2,2026-11-19,prod,no
s3-events,2,2026-11-20,prod,no
s3-events,1,2026-11-20,beta,yes
ec2-basics,1,2026-11-19,prod,yes
ec2-basics,1,2026-11-20,prod,yes
ec2-basics,1,2026-11-21,prod,no
ec2-basics,1,2026-11-22,prod,no
vpc-basics,1,2026-11-20,prod,yes
vpc-basics,1,2026-11-21,prod,yes
vpc-basics,1,2026-11-22,prod,yes
vpc-basics,2,2026-11-22,beta,yes
DATA
curl -sO https://raw.githubusercontent.com/johnallred/fieldguide/main/drills/lab_publish.py
```

**Step 3: run the pipeline's decisions**

```bash
python3 lab_publish.py candidate.md versions.csv runs.csv
```

```
step 1: can this document be published?
  candidate content 768d87, 4 runnable blocks
  BLOCKED  Wait for the redrive: no '# step:' name, so a failure cannot say which step broke
  BLOCKED  Wait for the redrive: bare sleep; declare what the harness waits for instead
  BLOCKED  confirm absent: '# exits 1:' gives no reason, so the exception becomes permanent
  BLOCKED  inspect worker: downloads at lab time, which fails wherever there is no route out
  BLOCKED  inspect worker: hardcodes a partition or account, which fails in any other

step 2: what moves to prod
  sqs-retry   v3 PROMOTE: 3 passing beta runs on this exact content
  s3-events   v2 in prod; nothing newer
  ec2-basics  v1 in prod; nothing newer
  vpc-basics  v2 stays in beta: 1 of 3 passing runs on its content

step 3: prod is failing; roll back or fix forward?
  s3-events   v2 failed 2 times since content 1c1d1e was published
              v1 still passes: ROLL BACK prod to v1, then fix v2
  ec2-basics  v1 passed in prod, then failed 2 times with unchanged content
              the environment changed, not the lab: rolling back cannot help;
              pull it from the catalogue, tell instructors, fix forward
```

It exits 1, because the candidate is blocked.

**Step 4: read the gate**

Five problems, and each one would ship a lab that is less testable or less
portable than the one before it. An unnamed block means a failing run reports
a heading instead of a step. A bare `sleep` either wastes time or fails a run
that was merely early, which is how a lab's flakiness gets blamed on a
learner. An exit code exception with no reason is how an exception becomes
permanent. A download at lab time fails anywhere without a route out, and an
ARN written with the commercial partition and one account fails in any other.
None of these would fail a documentation build, and none is caught by reading
the page.

**Step 5: read the promotions**

`sqs-retry` v3 has three passing beta runs on its own content, so it moves.
`vpc-basics` has four passing runs for the lab, but only one is against v2's
content; the three prod runs tested v1. Counting runs per lab rather than per
version would have promoted it.

**Step 6: read the two failures**

They look the same in a health dashboard, two red runs in prod, and they need
opposite responses. `s3-events` began failing when v2 was published, and v1
still passes, so the previous version is the fix: roll back, then fix v2.
`ec2-basics` passed for weeks and then failed with no change to its content.
The lab did not change; the service, a default or a quota did. There is
nothing to roll back to, so the lab is pulled from the catalog, instructors
are told, and the fix goes forward as a new version.

**What you built.** A publishing gate that encodes what the health harness
needs from a lab document, a promotion rule that counts evidence per version,
and a rule that separates the two kinds of prod failure.

## Reference

### The stages

| Stage | What it checks | What it produces |
|---|---|---|
| Lint the document | Directives, step names, waits, portability | A document the harness can run unchanged |
| Build the package | Content hash, assets, the infrastructure template | An immutable version |
| Cold run in beta | The full lifecycle against a fresh environment | Health runs recorded against that version |
| Promote | Enough consecutive passes on that version | The prod channel points at it |
| Watch prod | Nightly runs of what learners are using | The signal for pull, roll back or fix forward |

### Rules worth enforcing at the gate

| Rule | Why |
|---|---|
| Every runnable block has a step name | A failure has to name the step that broke |
| No bare sleeps; declare what to wait for | Fixed sleeps make labs slow or flaky |
| Every exception carries a reason | Reasonless exceptions become permanent |
| No downloads while the lab runs | Fails where there is no route out, and changes when the upstream does |
| No hardcoded partition or account | Fails in any other partition or account |
| Step names are unique | Health records are keyed by step |

coldlab enforces a lab-specific version of this: `extract.py` refuses a
document that would weaken the test, such as a short-polled read or a bare
sleep, and raises rather than running fewer steps than the document claims.
It also names an unnamed block after its heading rather than refusing it; the
gate in this drill is stricter.

coldlab also has the promotion half. `harness/publish.py` names a lab version
by a hash of the files a learner uses, and every nightly run records the
version it tested. A version is copied into `published/` for learners only
after three consecutive passing runs against that exact content. The nightly
workflow runs the promotion itself, so it happens on evidence rather than by
decision.
Because a published version must already have passed with its content, a
published version that later fails points at the environment, and the tool's
status says to fix forward; a rollback command points learners back at the
previous copy for the rarer case. The first promotion waits for three nightly
runs, because runs recorded before versioning carry no version.

### Roll back or fix forward

| Pattern | Means | Do |
|---|---|---|
| Failures begin with a new version, the previous still passes | The edit broke it | Roll back, then fix the new version |
| Failures begin with a new version, the previous has no recent pass | Unknown | Pull the lab; do not roll back blind |
| Failures begin with no content change | The environment changed | Pull, notify instructors, fix forward |
| One failure, then passes | A flaky check | Read the check, not the pass rate |

### A real gate, smaller

This guide is published the same way at a smaller scale. Its workflow,
`.github/workflows/gates.yml`, runs five gate jobs on every change, and the
deploy job `needs:` all five and runs only on a push to `main`. The comment at
the top records why: it was once two workflows that raced, so a deploy could
publish a commit whose gates were still running or already red. A lab pipeline
needs the same property, with the health runs as one of the gates.

### Sources

Opened and checked on 2026-11-23:

- coldlab, [`harness/extract.py`](https://github.com/johnallred/coldlab/blob/main/harness/extract.py): the four directives, the required reasons, and validation that refuses a weakened document.
- This guide's [`.github/workflows/gates.yml`](https://github.com/johnallred/fieldguide/blob/main/.github/workflows/gates.yml): the five gate jobs and the deploy that needs them.

## Explaining it to your team

**How to explain it.** Lead with the two failures from step 6. "Both labs went
red twice in prod. One broke because we published an edit, and the previous
version still passes, so we rolled back. The other broke without any edit, so
a rollback would have changed nothing; we pulled it and told instructors. The
pipeline told those apart because it records which version every run tested."

**The follow-up is usually "why can't writers just merge?".** They can; the
merge is not the publish. A lab document is executable, so the gate checks the
things a harness and a learner need, and the beta channel gives a new version
real runs before a class depends on it. A writer's edit should reach learners
quickly, but not before anything has run it.

**The tradeoff to name.** Promotion on evidence means a fix waits for its runs.
Three nightly passes is three days before a corrected lab reaches prod, which
is too slow when a lab is pulled. Decide in advance which changes may skip the
wait, such as restoring a known-good version, and record each time one does.

**One sharper point.** A lab can break without anyone touching it, which
software mostly cannot. Any process that assumes "find the change that broke
it and revert it" will be wrong for those labs every time, and the version
history is what shows which kind of failure you have.

## Putting it into practice

**The work product.** A gate over your lab documents, a version table with a
content hash per version, health runs keyed by version and channel, and a
written rule for pull, roll back and fix forward.

**Three things to do, in order:**

1. Run the golden path, then run the gate's rules by hand over one of your own
   labs and count how many would block it.
2. Start recording, for every health run, which version of the lab it tested.
   Without that column, none of the promotion or rollback decisions can be
   made from data.
3. Write the rollback rule down before the next failure, including who tells
   instructors when a lab is pulled.

**How to tell it is working.** The drill above runs in this guide's test suite
and its output is the output quoted here. The labs and runs are invented, and
no lab catalog is published through such a pipeline here, so the
[demonstrated](../demonstrated.md) page records the concept as partial. In
your own work, the sign is that an instructor's report of a broken lab can be
answered with a version number and a decision, the same day.

## Related

- [Ephemeral lab environments](ephemeral-environments.md), the health runs this pipeline promotes on
- [Documentation CI](documentation-ci.md), the same gates for prose
- [Release readiness](release-readiness.md), content ready on the day a product ships
- [Versioning](versioning.md), versioning documentation rather than labs
- [Retiring content](content-retirement.md), what pulling a lab permanently becomes
