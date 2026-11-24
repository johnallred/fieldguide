#!/usr/bin/env python3
"""Audit a lab for what stops it running in another partition or an isolated region.

    python3 drills/partition_audit.py                                   # embedded samples
    python3 drills/partition_audit.py template.yaml lab.md target.csv   # your files
    python3 drills/partition_audit.py path/to/repo                      # steps 1 and 2 over a tree

A lab written in a commercial AWS region carries assumptions that stop being
true elsewhere. An AWS partition is a group of regions with its own ARN
prefix and, for some partitions, its own DNS suffix: `aws`, `aws-cn`,
`aws-us-gov`, and isolated partitions whose endpoints are not under
amazonaws.com at all. A lab that writes `arn:aws:` or `amazonaws.com` into a
template, downloads from the public internet while it runs, or uses a service
the target region does not offer, fails there however well it runs here.

Three checks, each a reason a lab fails on arrival:

1. Partition, endpoint, region and account written as literals.
2. Anything fetched from outside while the lab runs.
3. Services the lab uses that the target region does not list.

The template, lab document and target service list are invented, and the
target list is illustrative: real availability comes from the provider's own
list for the region you are publishing to.
"""

from __future__ import annotations

import csv
import io
import os
import re
import sys

TEMPLATE = """\
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
"""

LAB = """\
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
"""

TARGET = """\
service,available
sqs,yes
lambda,yes
s3,yes
iam,yes
logs,yes
cloudformation,yes
stepfunctions,no
"""

PARTITION = re.compile(r"\barn:aws:")
SUFFIX = re.compile(r"\bamazonaws\.com\b")
REGION = re.compile(r"\b(?:us|eu|ap|sa|ca|me|af|il|mx)-(?:gov-)?(?:north|south|east|west|central|northeast|southeast|northwest|southwest)-\d\b")
ACCOUNT = re.compile(r"(?<![\w-])(?!111122223333|123456789012)\d{12}(?![\w-])")
SET_ONCE = re.compile(r"\b\w*REGION\w*\s*=|environ\.get\(\s*[\"']\w*REGION")
COMMENT = re.compile(r"^\s*(#|//)")
FETCH = re.compile(r"\b(?:pip3? install|npm (?:install|i)|curl|wget|git clone|docker pull)\b")
CFN_TYPE = re.compile(r"Type:\s*AWS::(\w+)::")
CLI = re.compile(r"\baws\s+([a-z0-9-]+)\s")
CFN_SERVICE = {"SQS": "sqs", "Lambda": "lambda", "S3": "s3", "IAM": "iam",
               "Logs": "logs", "StepFunctions": "stepfunctions", "SNS": "sns",
               "DynamoDB": "dynamodb", "Events": "events", "EC2": "ec2"}
SKIP_DIRS = {".git", "node_modules", "cdk.out", ".venv", "venv", "__pycache__", "tests", "site"}
GROUPS = [
    ("what the learner runs", lambda n: n.startswith("lab" + os.sep)),
    ("what the lab deploys", lambda n: n.startswith("infra" + os.sep)),
    ("what tests and publishes it", lambda n: True),
]
TEXT = (".yaml", ".yml", ".json", ".md", ".py", ".sh", ".ts", ".js", ".txt", ".toml")


def code_lines(name: str, text: str):
    """(number, line) for the lines that run: fenced blocks only, in Markdown."""
    inside = not name.endswith(".md")
    for number, line in enumerate(text.splitlines(), 1):
        if name.endswith(".md") and line.lstrip().startswith(("```", "~~~")):
            inside = not inside
            continue
        if inside and not COMMENT.match(line):
            yield number, line


def literal_findings(name: str, text: str) -> list[str]:
    found = []
    for number, line in code_lines(name, text):
        where = f"{name}:{number}"
        if REGION.search(line) and SET_ONCE.search(line):
            continue
        if PARTITION.search(line):
            found.append(f"{where}  literal partition 'arn:aws:'; use ${{AWS::Partition}} or read it from the ARN you were given")
        if SUFFIX.search(line):
            found.append(f"{where}  literal DNS suffix; use ${{AWS::URLSuffix}} or let the SDK resolve the endpoint")
        if REGION.search(line):
            found.append(f"{where}  literal region '{REGION.search(line).group(0)}'; take it from a variable")
        if ACCOUNT.search(line):
            found.append(f"{where}  literal account ID; use ${{AWS::AccountId}} or a variable")
    return found


def fetch_findings(name: str, text: str) -> list[str]:
    found = []
    for number, line in code_lines(name, text):
        if FETCH.search(line):
            found.append(f"{name}:{number}  fetches at run time: {line.strip()[:60]}")
    return found


def services(texts: list[str]) -> set[str]:
    used = set()
    for text in texts:
        used |= {CFN_SERVICE.get(m, m.lower()) for m in CFN_TYPE.findall(text)}
        used |= set(CLI.findall(text))
    return used


def report(files: dict[str, str], target: str | None) -> int:
    literal = [f for name, text in files.items() for f in literal_findings(name, text)]
    fetches = [f for name, text in files.items() for f in fetch_findings(name, text)]
    print("step 1: what is written as a literal")
    for line in literal or ["  none"]:
        print(f"  {line}" if line != "  none" else line)
    print()
    print("step 2: what is fetched from outside while it runs")
    for line in fetches or ["  none"]:
        print(f"  {line}" if line != "  none" else line)
    missing = []
    if target is not None:
        available = {r["service"] for r in csv.DictReader(io.StringIO(target)) if r["available"] == "yes"}
        used = services(list(files.values()))
        missing = sorted(used - available)
        print()
        print("step 3: what the target region does not offer")
        print(f"  the lab uses: {', '.join(sorted(used))}")
        for service in missing:
            print(f"  MISSING  {service}: redesign the step or do not publish there")
        if not missing:
            print("  none")
    total = len(literal) + len(fetches) + len(missing)
    print()
    print(f"{total} thing(s) to fix before this lab runs in another partition or an isolated region")
    return 1 if total else 0


def walk(root: str) -> dict[str, str]:
    files = {}
    for here, dirs, names in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for name in sorted(names):
            if name.endswith(TEXT):
                path = os.path.join(here, name)
                with open(path, encoding="utf-8", errors="replace") as handle:
                    files[os.path.relpath(path, root)] = handle.read()
    return files


def main() -> int:
    args = sys.argv[1:]
    if len(args) == 1 and os.path.isdir(args[0]):
        files = walk(args[0])
        total = 0
        for group, test in GROUPS:
            mine = {n: t for n, t in files.items() if test(n)}
            files = {n: t for n, t in files.items() if n not in mine}
            print(f"== {group} ({len(mine)} files)")
            total += report(mine, None)
            print()
        return 1 if total else 0
    if len(args) == 3:
        template, lab, target = (open(p, encoding="utf-8").read() for p in args)
        return report({os.path.basename(args[0]): template, os.path.basename(args[1]): lab}, target)
    return report({"template.yaml": TEMPLATE, "lab.md": LAB}, TARGET)


if __name__ == "__main__":
    sys.exit(main())
