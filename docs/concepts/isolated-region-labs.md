---
title: Labs for isolated regions
summary: Finding what stops a lab built in a commercial AWS region from running in another partition or an isolated region, and separating the lab, which can be made portable, from the tooling that tests it.
diataxis: explanation
audience: developer
concept: isolated-region-labs
tags: [qa, supporting]
---

# Labs for isolated regions

`supporting` · difficulty 3 · 5h

> Making a lab that runs in one AWS partition run in another, including isolated regions with no route to the public internet.

!!! warning "Nothing here ran outside a commercial region"
    No GovCloud, China or isolated-region account was available, so nothing on this page was run in one. The partition facts were checked against AWS's documentation and the partition data published in AWS's own SDK. The target service list in the golden path is invented. The audit of coldlab in step 5 is real, but it is a scan for assumptions, not a deployment: it shows what would have to change, not that the changed lab works.

**Prerequisites:** [Lab publishing pipelines](lab-publishing.md), [Multi-platform parity](multi-platform-parity.md)

## What it is

AWS groups its regions into partitions. Each partition has its own ARN
prefix, an account belongs to exactly one, and some partitions use their own
DNS suffix for service endpoints. The commercial partition is `aws`; GovCloud
is `aws-us-gov`; China is `aws-cn`; and AWS's SDKs also list isolated
partitions whose endpoints are not under `amazonaws.com` at all.

A lab written in a commercial region carries assumptions that only hold there:
an ARN that begins `arn:aws:`, an endpoint that ends `amazonaws.com`, a region
name, a `pip install` or `curl` that reaches the public internet while the lab
runs, and services that every commercial region offers and a given isolated
region may not. None of these fails where the lab was written. All of them
fail on arrival somewhere else.

## How this applies to your role

This matters because labs for isolated or government regions are written by people who
mostly work in commercial ones, and the cost of an assumption is paid by an
instructor in a room you cannot enter.

On a Tuesday it looks like this. A lab that has run nightly for months is
requested for a dedicated region. It deploys, then fails at step one, where
the learner runs `pip install` and there is no route out. Fixed, it fails
again, because the template attaches a managed policy by an ARN that begins
`arn:aws:`. Fixed again, the third step starts a Step Functions execution, and
the target region does not offer it. Three round trips, each one needing
someone with access to the target, for problems a scan could have listed in
seconds before anything was sent.

There is a second, quieter problem. Even when the lab is fixed, the system
that tests it usually is not portable: hosted CI runners, a public identity
provider, packages installed from public indexes on every run. A lab can be
ready for an isolated region while its health checks cannot follow it there.

## The golden path

Audit a lab's template and document against a target region's service list,
then run the same audit over a real repository. About twenty-five minutes.

The audit is committed as `drills/partition_audit.py`, which holds the three
files below and a test that keeps them identical to this page. The template,
lab and target list are invented.

**Step 1: the template**

```bash
mkdir -p partition-drill && cd partition-drill
cat > template.yaml <<'DATA'
Resources:
  Queue:
    Type: AWS::SQS::Queue
  WorkerRole:
    Type: AWS::IAM::Role
    Properties:
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
  Worker:
    Type: AWS::Lambda::Function
    Properties:
      Environment:
        Variables:
          QUEUE_ENDPOINT: https://sqs.us-east-1.amazonaws.com
  Flow:
    Type: AWS::StepFunctions::StateMachine
  BucketPolicy:
    Type: AWS::S3::BucketPolicy
    Properties:
      PolicyDocument:
        Statement:
          - Resource: !Sub arn:${AWS::Partition}:s3:::${Bucket}/*
DATA
```

**Step 2: the lab document and the target**

The target list stands in for the service list of the region you are
publishing to. Real availability comes from the provider's own list for that
region; this one is invented.

````bash
cat > lab.md <<'DATA'
# Retries with a state machine

## Set up your shell

```bash
pip install boto3
curl -sO https://raw.githubusercontent.com/example/lab-helpers/main/watch.py
```

## Start the flow

```bash
aws stepfunctions start-execution --state-machine-arn "$FLOW" --region us-east-1
```

## Check the queue

```bash
aws sqs get-queue-attributes --queue-url "$QUEUE" --attribute-names All --region "$REGION"
```
DATA
cat > target.csv <<'DATA'
service,available
sqs,yes
lambda,yes
s3,yes
iam,yes
logs,yes
cloudformation,yes
stepfunctions,no
DATA
curl -sO https://raw.githubusercontent.com/johnallred/fieldguide/main/drills/partition_audit.py
````

**Step 3: run the audit**

```bash
python3 partition_audit.py template.yaml lab.md target.csv
```

```
step 1: what is written as a literal
  template.yaml:8  literal partition 'arn:aws:'; use ${AWS::Partition} or read it from the ARN you were given
  template.yaml:14  literal DNS suffix; use ${AWS::URLSuffix} or let the SDK resolve the endpoint
  template.yaml:14  literal region 'us-east-1'; take it from a variable
  lab.md:13  literal region 'us-east-1'; take it from a variable

step 2: what is fetched from outside while it runs
  lab.md:6  fetches at run time: pip install boto3
  lab.md:7  fetches at run time: curl -sO https://raw.githubusercontent.com/example/lab-helpe

step 3: what the target region does not offer
  the lab uses: iam, lambda, s3, sqs, stepfunctions
  MISSING  stepfunctions: redesign the step or do not publish there

7 thing(s) to fix before this lab runs in another partition or an isolated region
```

It exits 1.

**Step 4: read it, and fix the template the way it already shows**

Every literal has a portable form, and the template already uses one: the
bucket policy writes `arn:${AWS::Partition}:s3:::`, which CloudFormation
fills in with whatever partition the stack is in. The managed-policy ARN on
line 8 needs the same treatment, and the endpoint on line 14 should use
`${AWS::URLSuffix}` or be left to the SDK, which already knows the endpoint
for the region it is in. The region in the lab document should come from the
variable the rest of the lab already uses.

The two downloads cannot be fixed by substitution. The packages a learner
needs go into the lab image or a mirror inside the target, and the helper
script goes into the lab package. The missing service is a design question:
rewrite the step, or do not publish the lab there.

**Step 5: run it over a real repository**

Pointed at a directory, the audit runs steps 1 and 2 over every text file and
groups the results by what the file is for. Run over
[coldlab](https://github.com/johnallred/coldlab) at commit d38115f on
2026-11-23, the result was this:

- **What the learner runs** (the lab document and its expectations): one hit,
  `region: us-east-2` in `expected.yaml`. It records where a measurement was
  taken, so it is a fact, not a setting, and needs no change. The lab sets its
  region once, in a variable, and every command reads it.
- **What the lab deploys** (the CDK app): one hit, a region in a docstring
  explaining a past mistake. Nothing to change. The CDK constructs and the
  bootstrap templates already build ARNs from `${AWS::Partition}`.
- **What tests and publishes it** (the harness, workflows, runbook and
  bootstrap): about forty hits. GitHub-hosted runners, GitHub's OIDC provider,
  `pip install` and `npm install` on every run, and `us-east-2` throughout the
  runbook.

So the lab is close to portable and the harness is not. That is the common
shape, and it means a lab can be ready for an isolated region before anything
can prove it nightly there.

**What you built.** A list of what stops a lab from running elsewhere, the
portable form of each literal, a decision for each missing service, and a
reading of a real repository that separates the lab from its test tooling.

## Reference

### Partitions

| Partition | ARN prefix | Endpoint suffix |
|---|---|---|
| Commercial regions | `arn:aws:` | `amazonaws.com` |
| GovCloud (US) | `arn:aws-us-gov:` | `amazonaws.com` |
| China | `arn:aws-cn:` | `amazonaws.com.cn` |
| Isolated partitions (`aws-iso`, `aws-iso-b` and others in the SDK data) | `arn:aws-iso:` and so on | Not under `amazonaws.com` |

An account belongs to one partition, so credentials, roles and ARNs never
cross from one to another.

### Portable forms

| Literal | Portable form |
|---|---|
| `arn:aws:...` in a template | `!Sub arn:${AWS::Partition}:...` |
| `arn:aws:...` in code | Read the partition from an ARN you were given, or from the SDK's region data |
| `https://sqs.us-east-1.amazonaws.com` | Let the SDK resolve it, or `${AWS::URLSuffix}` |
| A region name | A variable, set once |
| An account ID | `${AWS::AccountId}`, or the caller's identity |
| `pip install`, `curl` while the lab runs | Packages in the lab image or an internal mirror; files in the lab package |

### What usually does not carry, and where it lives

| Part | Usually portable? | Why |
|---|---|---|
| The lab document | Yes, once literals are removed | It is text and commands |
| The infrastructure template | Yes, with pseudo parameters | CloudFormation and CDK resolve the partition |
| The services the lab uses | Not always | Each region offers its own set |
| The test harness's runner | Rarely | Hosted CI runners live outside the target |
| The identity the harness uses | Rarely | A public OIDC provider may not be reachable or trusted there |
| Dependencies installed per run | No | Public package indexes are outside |

### Sources

Opened and checked on 2026-11-23:

- AWS, [Identify AWS resources with Amazon Resource Names (ARNs)](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference-arns.html), IAM User Guide: the ARN format, and partitions as groups of regions, each account scoped to one.
- AWS, [Pseudo parameters reference](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/pseudo-parameter-reference.html), CloudFormation User Guide: `AWS::Partition` and `AWS::URLSuffix`. Its own basic example hardcodes `arn:aws:`, which is the mistake this page is about.
- AWS, [Amazon Resource Names (ARNs) in AWS GovCloud (US)](https://docs.aws.amazon.com/govcloud-us/latest/UserGuide/using-govcloud-arns.html): GovCloud ARNs begin `arn:aws-us-gov`.
- AWS, `botocore` 1.44.10, `botocore/data/partitions.json`: the partitions the SDK knows, with their DNS suffixes, including the isolated partitions in the table above.
- coldlab at commit d38115f: `lab/sqs-retry/lab.md`, `infra/`, `bootstrap/oidc-role.yaml` and `.github/workflows/`, scanned with the drill and read.

## Explaining it to your team

**How to explain it.** Lead with step 5's result. "The lab is nearly portable:
the template already uses the partition parameter and the lab sets its region
once. What is not portable is everything that tests it: hosted runners, a
public identity provider, and packages installed on every run. Before we
promise this lab in an isolated region, we need a way to run its health checks
there."

**The follow-up is usually "why not just find and replace `arn:aws`?".**
Because a scan finds the easy half. Downloads need packaging, missing services
need redesign, and some literals are facts rather than settings: the audit
flagged a measurement record and a docstring in coldlab, and both were right as
they stood. A scan produces a list for someone to read, not a patch.

**The tradeoff to name.** Writing every lab to the strictest target from the
start costs effort on labs that will never leave a commercial region, and
packaging dependencies makes labs heavier to update. Writing them loosely
makes every port a series of round trips through people with access. A useful
middle: enforce the cheap rules everywhere, such as no partition or account
literals, and leave service and dependency decisions to the labs that are
actually requested elsewhere.

**One sharper point.** The gate in [lab publishing pipelines](lab-publishing.md)
already blocks a download at lab time and a hardcoded partition. Rules like
these cost nothing for a commercial lab and decide whether a port takes an
afternoon or a month, which is the strongest argument for putting them in the
gate rather than in a porting checklist.

## Putting it into practice

**The work product.** A portability audit for each lab, the fixes for every
literal, a service decision for each target, and a statement of which parts of
the test tooling would have to move with the lab.

**Three things to do, in order:**

1. Run the golden path, then run the audit over one of your own lab
   repositories and sort the findings into the three groups from step 5.
2. Fix the literals in the lab and its template, and add the partition and
   download rules to your publishing gate so new labs start portable.
3. For one target region, list the services your labs use that it does not
   offer, and the parts of your test harness that could not run there.

**How to tell it is working.** The drill above runs in this guide's test suite
and its output is the output quoted here. Nothing was deployed outside a
commercial region, so the [demonstrated](../demonstrated.md) page records the
concept as partial. In your own work, the sign is that a request to publish a
lab in a new region starts with a list rather than a first failed deploy.

## Related

- [Multi-platform parity](multi-platform-parity.md), the same problem for one product reached through several platforms
- [Lab publishing pipelines](lab-publishing.md), where the cheap rules belong
- [Ephemeral lab environments](ephemeral-environments.md), the health runs that would have to follow a lab into a new region
- [Reproducible environments](reproducible-environments.md), packaging dependencies so nothing is fetched at run time
