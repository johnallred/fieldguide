---
title: Learner sandbox guardrails
summary: Layering an identity policy, a permissions boundary, a service control policy and a budget so a learner can do the lab and nothing that breaks the account, the bill or the lab itself.
diataxis: explanation
audience: developer
concept: learner-sandbox-guardrails
tags: [qa, supporting]
---

# Learner sandbox guardrails

`supporting` · difficulty 3 · 5h

> Letting a learner do everything the lab needs in a real cloud account, and nothing that breaks the account, the bill or the lab.

!!! warning "Evaluated offline, against a simplified model"
    The golden path evaluates requests with a small model of AWS's documented policy evaluation logic: identity policy, permissions boundary and service control policy in one account, with no resource-based policies, session policies or full condition language. It runs no AWS call. The policies and requests are invented. The coldlab material in step 5 is real configuration, read rather than tested against a learner.

**Prerequisites:** [Ephemeral lab environments](ephemeral-environments.md), [Security guidance as encoded standard](security-documentation.md)

## What it is

A hands-on lab gives a learner credentials in a real account. The guardrails
decide what those credentials can do, and in AWS they come in layers that
behave differently. An identity policy on the learner's role grants. A
permissions boundary on that role caps what any identity policy can grant. A
service control policy on the account caps everything in the account. A
request succeeds only if all three allow it, and an explicit deny in any of
them wins.

Policies answer "may this request happen". They cannot answer "how many" or
"how much", so a sandbox also needs service quotas and a budget, and it needs
the lab's own resources, such as the harness's records, out of the learner's
reach.

## How this applies to your role

Because a lab that gives learners too little fails on step three, and a lab
that gives them too much is the one that turns up in a security review, an
invoice, or a broken shared account the next morning.

On a Tuesday it looks like this. A lab needs Lambda, so its role was given
`lambda:*` and `iam:PassRole` on `*`, because PassRole is what lets the
learner attach a role to a function. It works. Then a learner passes the
harness's admin role to their function, and their function can now do anything
in the account. Nobody wrote a policy that allowed escalation. Two broad
statements combined into one.

The work is to find those combinations before learners do: write down what the
lab needs and what it must never allow, and test every layer against both
lists.

## The golden path

Evaluate ten learner requests through three policy layers, see what each layer
stops on its own, and trace the two that got through. About twenty-five
minutes.

The evaluation is committed as `drills/sandbox_guardrails.py`, which holds the
two files below and a test that keeps them identical to this page. One
statement per line; an action beginning with `!` is a NotAction.

**Step 1: the three layers**

```bash
mkdir -p sandbox-drill && cd sandbox-drill
cat > policies.csv <<'DATA'
layer,effect,action,resource,condition
identity,allow,*,*,-
boundary,allow,sqs:*,*,-
boundary,allow,lambda:*,*,-
boundary,allow,logs:*,*,-
boundary,allow,s3:*,*,-
boundary,allow,iam:PassRole,*,-
boundary,allow,ec2:RunInstances,*,instance-type=t3.*
scp,allow,*,*,-
scp,deny,!iam:*,*,region!=us-east-2
scp,deny,cloudtrail:StopLogging,*,-
scp,deny,iam:CreateUser,*,-
DATA
```

The identity policy allows everything, which is common in lab roles because
the boundary is meant to do the limiting. The SCP starts from allow-all and
adds denies, which is how SCPs are usually written. Its region deny exempts
`iam:*`, for a reason step 4 explains.

**Step 2: what learners will try, and what they should get**

The last column is the requirement: what the lab needs to allow, and what it
must never allow.

```bash
cat > requests.csv <<'DATA'
action,resource,region,instance_type,should
sqs:SendMessage,arn:aws:sqs:us-east-2:111122223333:lab-queue,us-east-2,-,allow
lambda:UpdateFunctionCode,arn:aws:lambda:us-east-2:111122223333:function:lab-worker,us-east-2,-,allow
ec2:RunInstances,arn:aws:ec2:us-east-2:111122223333:instance/*,us-east-2,t3.micro,allow
iam:PassRole,arn:aws:iam::111122223333:role/lab-worker-role,us-east-1,-,allow
ec2:RunInstances,arn:aws:ec2:us-east-2:111122223333:instance/*,us-east-2,p5.48xlarge,deny
ec2:RunInstances,arn:aws:ec2:us-east-1:111122223333:instance/*,us-east-1,t3.micro,deny
cloudtrail:StopLogging,arn:aws:cloudtrail:us-east-2:111122223333:trail/org-trail,us-east-2,-,deny
iam:CreateUser,arn:aws:iam::111122223333:user/backdoor,us-east-1,-,deny
iam:PassRole,arn:aws:iam::111122223333:role/LabHarnessAdmin,us-east-1,-,deny
s3:DeleteBucket,arn:aws:s3:::lab-health-records,us-east-2,-,deny
DATA
curl -sO https://raw.githubusercontent.com/johnallred/fieldguide/main/drills/sandbox_guardrails.py
```

**Step 3: evaluate**

```bash
python3 sandbox_guardrails.py policies.csv requests.csv
```

```
step 1: every request through all three layers
       ALLOW  sqs:SendMessage lab-queue (us-east-2)
              every layer allows it
       ALLOW  lambda:UpdateFunctionCode function:lab-worker (us-east-2)
              every layer allows it
       ALLOW  ec2:RunInstances instance/* t3.micro (us-east-2)
              every layer allows it
       ALLOW  iam:PassRole role/lab-worker-role (us-east-1)
              every layer allows it
       DENY   ec2:RunInstances instance/* p5.48xlarge (us-east-2)
              boundary: no statement allows it
       DENY   ec2:RunInstances instance/* t3.micro (us-east-1)
              scp: explicit deny (!iam:*, region!=us-east-2)
       DENY   cloudtrail:StopLogging trail/org-trail (us-east-2)
              scp: explicit deny (cloudtrail:StopLogging)
       DENY   iam:CreateUser user/backdoor (us-east-1)
              scp: explicit deny (iam:CreateUser)
  GAP  ALLOW  iam:PassRole role/LabHarnessAdmin (us-east-1)
              every layer allows it
  GAP  ALLOW  s3:DeleteBucket lab-health-records (us-east-2)
              every layer allows it

step 2: what each layer would stop on its own
  identity  alone stops 0 of 6
  boundary  alone stops 3 of 6
  scp       alone stops 3 of 6
  together  stop 4 of 6

step 3: why the gaps got through
  iam:PassRole role/LabHarnessAdmin (us-east-1)
    the boundary allows iam:PassRole on *: scope it to the lab's own resources
  s3:DeleteBucket lab-health-records (us-east-2)
    the boundary allows s3:* on *: scope it to the lab's own resources
  no statement here limits how many t3 instances a learner starts: that is a quota or a budget
```

It exits 1, because two requests that should be denied were allowed.

**Step 4: read the layers**

The identity policy stops nothing, by design. The boundary and the SCP each
stop three of the six, and they overlap on one, so together they stop four. The
boundary caps instance types, which the SCP does not know about. The SCP caps
regions and protects the audit trail for every role in the account, including
roles that have no boundary.

The region deny exempts `iam:*` because IAM has a single endpoint. AWS's
documentation says IAM calls are always made to `us-east-1`, so a deny on every
other region without that exemption would also deny the legitimate PassRole in
row four. That is a classic way for a region guardrail to break a lab.

**Step 5: trace the two gaps**

Both came through the same shape: a broad action on `*` in the boundary. PassRole
on `*` lets a learner hand any role in the account to their function,
including the harness's admin role, which is privilege escalation without a
single statement that mentions escalation. `s3:*` on `*` lets a learner delete
the bucket where the lab's health records live. The fix for both is resource
scoping: PassRole only on roles named for the lab, and S3 only on buckets with
the learner's prefix.

The last line is the limit of policies. A learner can start as many `t3`
instances as the quota allows. That needs a service quota and a budget, not
another statement.

**What you built.** A requirement list of what a lab must and must never
allow, an evaluation of every request through every layer, a count of what
each layer contributes, and two scoped fixes.

## Reference

### The layers

| Layer | Attached to | Grants? | Use it for |
|---|---|---|---|
| Identity policy | The learner's role | Yes | What the lab needs |
| Permissions boundary | The learner's role | No, caps | The most any lab role can ever get, including roles learners create |
| Service control policy | The account or its organizational unit | No, caps | Account-wide rules: regions, audit trail, identity creation |
| Service quotas | The account | n/a | How many |
| Budget | The account | n/a | How much, noticed in time |

An explicit deny in any policy layer overrides every allow. An SCP does not
apply to the organisation's management account or to service-linked roles, so
a sandbox account is never the management account.

### Common gaps

| Statement | Lets a learner | Scope it to |
|---|---|---|
| `iam:PassRole` on `*` | Hand any role to a service they control | Roles named for the lab |
| `service:*` on `*` | Touch the lab's own infrastructure | The learner's prefix or tag |
| `iam:CreateRole` without a boundary requirement | Create a role with no cap | Require the boundary on any role they create |
| A region deny without global-service exemptions | Nothing, it blocks too much | Exempt IAM and other global services |
| No quota or budget | Unlimited count and spend | Quotas per account, budget with a forecast alert |

### The deployer is part of the sandbox

A learner's role is only one identity in a lab account. The tooling that
deploys the lab has its own. The AWS CDK, by default, deploys stacks through a
CloudFormation execution role with the `AdministratorAccess` managed policy,
and `cdk bootstrap --cloudformation-execution-policies` replaces it. A learner
role that can pass or assume the deployer's roles inherits that.

### What coldlab shows

[coldlab](https://github.com/johnallred/coldlab) now has a learner role built
the way this page describes. `bootstrap/learner-role.yaml` grants the lab's
steps on the lab's resources and attaches a boundary that caps every learner
role at coldlab-named resources in one region, with no IAM.
`lab/sqs-retry/sandbox.yaml` is the two-column requirement list: eight things a
learner must be able to do and ten they must never do. `harness/sandbox.py`
asks AWS's policy simulator about every line for the deployed role, and adds the
one finding the simulator cannot see: the lab has learners run `cdk deploy`,
which reaches the administrator deployer described below. Its CI identity has
the same layers, and they are worth reading too:

- `bootstrap/oidc-role.yaml` scopes the CI role by resource wherever the
  service supports it, and its comments say why: conflating "deploy" with "run
  the lab" is "how this ends up as AdministratorAccess". Deployment works by
  assuming the CDK bootstrap roles, not by holding deploy permissions.
- The repository does not pass `--cloudformation-execution-policies`, so by the
  CDK's documented default the stacks themselves deploy with administrator
  access. A scoped CI role in front of an administrator deployer is the shape
  of most lab accounts, and the place a learner sandbox needs the most care.
- An organisation service control policy denied a deploy that went to the
  wrong region, as `infra/app.py` records. The guardrail worked; the error it
  produced talked about bootstrap versions, not regions, which is a reminder to
  make guardrail denials legible to the people who hit them.
- `bootstrap/budget.yaml` sets a deliberately low monthly budget with an
  actual-spend alert and a forecast alert, and its comments note the forecast
  is the one that catches a leaked resource while there is still time.

### Sources

Opened and checked on 2026-11-23:

- AWS, [Policy evaluation logic](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_evaluation-logic.html), IAM User Guide: intersections of identity policies, boundaries and SCPs, and explicit deny overriding allow.
- AWS, [Permissions boundaries for IAM entities](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_boundaries.html): a boundary sets maximum permissions and grants none.
- AWS, [Service control policies](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps.html), Organizations User Guide: SCPs grant nothing, and do not affect the management account or service-linked roles.
- AWS, [Global condition context keys](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_condition-keys.html), `aws:RequestedRegion`: IAM calls are always made to `us-east-1`, so a region deny needs an exemption.
- AWS, [Customize AWS CDK bootstrapping](https://docs.aws.amazon.com/cdk/v2/guide/bootstrapping-customizing.html): the default `AdministratorAccess` execution policy and `--cloudformation-execution-policies`.
- coldlab at commit 1fca32e: `bootstrap/oidc-role.yaml`, `bootstrap/budget.yaml`, `infra/app.py`.

## Explaining it to your team

**How to explain it.** Lead with step 2's counts and the two gaps. "The
identity policy stops nothing, which is fine, because the boundary and the SCP
together stop four of six things learners must never do. The other two got
through because of two broad statements: PassRole on everything, and S3 on
everything. Scoping both to the lab's own resources closes them."

**The follow-up is usually "why not just give learners a read-only role?".**
Because labs are about doing, and a lab that only reads teaches only reading.
The point of a sandbox is a learner who can create, break and delete things
inside a fence. The fence is the work.

**The tradeoff to name.** Tighter guardrails mean more labs fail on legitimate
steps, often with an access-denied message that says nothing about the
guardrail behind it, and every failure lands on an instructor. Looser
guardrails move the risk into the account and the bill. Write the requirement
list first, test both halves of it, and make denials legible.

**One sharper point.** Escalation rarely comes from a statement that grants too
much. It comes from two reasonable statements that combine, PassRole and a
service that runs code. Testing a policy against what learners will try finds
those; reading the policy statement by statement does not.

## Putting it into practice

**The work product.** For each lab, a list of what it must allow and must never
allow, the identity policy, boundary and SCP, an evaluation of the list
through all three, and a quota and budget for the account.

**Three things to do, in order:**

1. Run the golden path, then write the two-column requirement list for one of
   your own labs, starting with what it must never allow.
2. Check every `*` resource in your lab roles and boundary, and scope each one
   to the lab's names, prefix or tags.
3. Test the requirement list against the real policies with the IAM policy
   simulator or a sandbox account, before learners do it for you.

**How to tell it is working.** The drill above runs in this guide's test suite
and its output is the output quoted here. It models the evaluation rather than
calling AWS, and no learner has used a sandbox built this way here, so the
[demonstrated](../demonstrated.md) page records the concept as partial. In your
own work, the sign is that a lab's access-denied failures are the ones you
planned, and that the budget's forecast alert is the only cost surprise.

## Related

- [Ephemeral lab environments](ephemeral-environments.md), the accounts these guardrails apply to
- [Security guidance as encoded standard](security-documentation.md), guidance enforced by validators rather than pages
- [Labs for isolated regions](isolated-region-labs.md), where the region guardrail has another meaning
- [Lab publishing pipelines](lab-publishing.md), the gate that could check a lab's policies before it ships
