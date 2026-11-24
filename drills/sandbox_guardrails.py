#!/usr/bin/env python3
"""Evaluate a learner's requests through the three policy layers of a lab sandbox.

    python3 drills/sandbox_guardrails.py                          # embedded samples
    python3 drills/sandbox_guardrails.py policies.csv requests.csv

A learner in a lab account acts through an identity policy, which grants, and
two layers that only limit: a permissions boundary on the learner's role and a
service control policy (SCP) on the account. A request is allowed only if the
identity policy allows it, the boundary allows it and the SCP allows it, and
any explicit deny in any of them wins. That is AWS's documented evaluation
logic for a request inside one account with no resource-based policy, and it
is all this drill models: no resource policies, session policies or the full
condition language.

The policy format is one statement per line. An action beginning with `!` is a
NotAction. Conditions are `region=`, `region!=` and `instance-type=` with shell
wildcards. The policies and requests are invented; the account is the
documentation placeholder.
"""

from __future__ import annotations

import csv
import io
import sys
from fnmatch import fnmatchcase

POLICIES = """\
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
"""

REQUESTS = """\
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
"""

LAYERS = ("identity", "boundary", "scp")


def rows(text: str) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(text)))


def matches(statement: dict[str, str], request: dict[str, str]) -> bool:
    action = statement["action"]
    hit = not fnmatchcase(request["action"], action[1:]) if action.startswith("!") else fnmatchcase(request["action"], action)
    if not hit or not fnmatchcase(request["resource"], statement["resource"]):
        return False
    condition = statement["condition"]
    if condition == "-":
        return True
    if condition.startswith("region!="):
        return not fnmatchcase(request["region"], condition[8:])
    if condition.startswith("region="):
        return fnmatchcase(request["region"], condition[7:])
    if condition.startswith("instance-type="):
        return fnmatchcase(request["instance_type"], condition[14:])
    raise ValueError(f"unknown condition {condition!r}")


def layer_verdict(statements: list[dict[str, str]], request: dict[str, str]) -> tuple[str, dict | None]:
    """'deny' (explicit), 'none' (no allow) or 'allow', with the deciding statement."""
    hits = [s for s in statements if matches(s, request)]
    for s in hits:
        if s["effect"] == "deny":
            return "deny", s
    allow = next((s for s in hits if s["effect"] == "allow"), None)
    return ("allow", allow) if allow else ("none", None)


def evaluate(policies, request, layers=LAYERS) -> tuple[bool, str]:
    verdicts = {name: layer_verdict([p for p in policies if p["layer"] == name], request) for name in layers}
    for name in layers:
        if verdicts[name][0] == "deny":
            s = verdicts[name][1]
            return False, f"{name}: explicit deny ({s['action']}{'' if s['condition'] == '-' else ', ' + s['condition']})"
    for name in layers:
        if verdicts[name][0] == "none":
            return False, f"{name}: no statement allows it"
    return True, "every layer allows it"


def short(request: dict[str, str]) -> str:
    target = request["resource"].split(":", 5)[5] or request["resource"]
    extra = f" {request['instance_type']}" if request["instance_type"] != "-" else ""
    return f"{request['action']} {target}{extra} ({request['region']})"


def main() -> int:
    if len(sys.argv) == 3:
        policies_text, requests_text = (open(p, encoding="utf-8").read() for p in sys.argv[1:])
    else:
        policies_text, requests_text = POLICIES, REQUESTS
    policies, requests = rows(policies_text), rows(requests_text)

    print("step 1: every request through all three layers")
    gaps, blocked = [], []
    for r in requests:
        ok, why = evaluate(policies, r)
        wrong = ok != (r["should"] == "allow")
        mark = "GAP " if wrong and ok else "OVER" if wrong else "    "
        print(f"  {mark} {'ALLOW' if ok else 'DENY '}  {short(r)}")
        print(f"              {why}")
        if wrong and ok:
            gaps.append(r)
        if wrong and not ok:
            blocked.append(r)
    print()

    print("step 2: what each layer would stop on its own")
    should_deny = [r for r in requests if r["should"] == "deny"]
    for name in LAYERS:
        caught = sum(1 for r in should_deny if not evaluate(policies, r, (name,))[0])
        print(f"  {name:<9} alone stops {caught} of {len(should_deny)}")
    together = sum(1 for r in should_deny if not evaluate(policies, r)[0])
    print(f"  {'together':<9} stop {together} of {len(should_deny)}")
    print()

    print("step 3: why the gaps got through")
    for r in gaps:
        statement = layer_verdict([p for p in policies if p["layer"] == "boundary"], r)[1]
        print(f"  {short(r)}")
        print(f"    the boundary allows {statement['action']} on {statement['resource']}: scope it to the lab's own resources")
    print("  no statement here limits how many t3 instances a learner starts: that is a quota or a budget")
    return 1 if gaps or blocked else 0


if __name__ == "__main__":
    sys.exit(main())
