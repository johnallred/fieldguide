#!/usr/bin/env python3
"""Check a Mermaid diagram against the system it describes, then generate it.

    python3 drills/diagram_drift.py                          # embedded samples
    python3 drills/diagram_drift.py workflow.yml page.md     # check a page
    python3 drills/diagram_drift.py --generate workflow.yml  # print a diagram

Needs `pyyaml`. A diagram drawn by hand is a copy of a system, and copies drift
the same way code samples do. This drill reads the jobs and `needs:` edges of a
GitHub Actions workflow, reads every `mermaid` block in a Markdown page, and
reports edges and nodes that disagree, plus any diagram with no accessible
title or description. Then it generates the diagram from the workflow, so the
check passes by construction.

It parses a small subset of Mermaid flowchart syntax: `flowchart`, `A --> B`
chains, and `id[label]` nodes. That is enough for pipeline diagrams and is not
a Mermaid parser.
"""

from __future__ import annotations

import re
import sys

import yaml

WORKFLOW = """\
name: docs
on: [pull_request]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps: [{run: vale docs}]
  build:
    needs: lint
    runs-on: ubuntu-latest
    steps: [{run: mkdocs build --strict}]
  linkcheck:
    needs: build
    runs-on: ubuntu-latest
    steps: [{run: python3 check_links.py site}]
  samples:
    needs: build
    runs-on: ubuntu-latest
    steps: [{run: pytest docs}]
  deploy:
    needs: [linkcheck, samples]
    runs-on: ubuntu-latest
    steps: [{run: mkdocs gh-deploy}]
"""

PAGE = """\
# How a docs change ships

Every pull request runs this pipeline:

```mermaid
flowchart LR
  lint --> build --> test --> deploy
```
"""

FENCE = re.compile(r"```mermaid\n(.*?)```", re.S)
NODE = re.compile(r"^([A-Za-z_][\w-]*)")


def workflow_graph(text: str) -> tuple[set[str], set[tuple[str, str]]]:
    jobs = yaml.safe_load(text)["jobs"]
    edges = set()
    for job, spec in jobs.items():
        needs = spec.get("needs", [])
        for dep in [needs] if isinstance(needs, str) else needs:
            edges.add((dep, job))
    return set(jobs), edges


def diagram_graph(block: str) -> tuple[set[str], set[tuple[str, str]], bool, bool]:
    nodes, edges = set(), set()
    title = "accTitle:" in block
    description = "accDescr" in block
    for line in block.splitlines():
        line = line.strip()
        if "-->" not in line:
            continue
        parts = [NODE.match(p.strip()).group(1) for p in line.split("-->")]
        nodes.update(parts)
        edges.update(zip(parts, parts[1:]))
    return nodes, edges, title, description


def check(workflow_text: str, page_text: str, name: str) -> int:
    jobs, real = workflow_graph(workflow_text)
    print(f"== {name}")
    found = []
    for n, block in enumerate(FENCE.findall(page_text), 1):
        nodes, drawn, title, description = diagram_graph(block)
        for a, b in sorted(drawn - real):
            found.append(f"DRIFT  edge {a} -> {b}: in the diagram, not in the workflow")
        for a, b in sorted(real - drawn):
            found.append(f"DRIFT  edge {a} -> {b}: in the workflow, not in the diagram")
        for node in sorted(nodes - jobs):
            found.append(f"DRIFT  node {node}: no job of that name")
        if not title:
            found.append(f"A11Y   mermaid block {n} has no accTitle")
        if not description:
            found.append(f"A11Y   mermaid block {n} has no accDescr")
    for line in found:
        print(line)
    print(f"{len(found)} finding(s)")
    return len(found)


def generate(workflow_text: str) -> str:
    workflow = yaml.safe_load(workflow_text)
    jobs, edges = workflow_graph(workflow_text)
    order = list(workflow["jobs"])
    lines = ["```mermaid", "flowchart LR",
             f"  accTitle: The {workflow['name']} pipeline",
             f"  accDescr: {describe(order, edges)}"]
    lines += [f"  {a} --> {b}" for a, b in sorted(edges, key=lambda e: (order.index(e[0]), order.index(e[1])))]
    lines.append("```")
    return "# How a docs change ships\n\nEvery pull request runs this pipeline:\n\n" + "\n".join(lines) + "\n"


def describe(order: list[str], edges: set[tuple[str, str]]) -> str:
    """One sentence a screen reader can say, generated from the same edges."""
    parts = []
    for job in order:
        deps = sorted((a for a, b in edges if b == job), key=order.index)
        if deps:
            parts.append(f"{job} runs after {' and '.join(deps)}")
    return f"{order[0]} runs first; " + "; ".join(parts) + "."


def main() -> int:
    args = sys.argv[1:]
    if args[:1] == ["--generate"]:
        with open(args[1], encoding="utf-8") as handle:
            sys.stdout.write(generate(handle.read()))
        return 0
    if len(args) == 2:
        texts = []
        for path in args:
            with open(path, encoding="utf-8") as handle:
                texts.append(handle.read())
        return 1 if check(texts[0], texts[1], args[1]) else 0
    check(WORKFLOW, PAGE, "pipeline.md")
    print()
    generated = generate(WORKFLOW)
    print(generated)
    return 1 if check(WORKFLOW, generated, "pipeline.md, generated") else 0


if __name__ == "__main__":
    sys.exit(main())
