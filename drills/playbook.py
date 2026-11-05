#!/usr/bin/env python3
"""A decision guide validated as a graph, and the five ways one breaks.

    python3 drills/playbook.py

Reproduces the `playbooks` page's golden path: the integration-failure guide it
tells you to write, the validator it shows in fragments, and each defect class
injected one at a time to prove the check catches it.

The page prints its playbook in full and its validator in pieces, then quotes
the output of a `check_playbook.py` whose source never appears. So the drill is
the complete version. The playbook below is the page's, verbatim, and a test
asserts it stays that way.

Five classes rather than the page's four. The page checks that every *outcome*
is reachable and not that every *node* is, which is the same defect one level
up and the more likely one in a guide that has been edited for a year: a
question nobody can get to is a branch of the expert's knowledge that has
silently left the playbook. It is also the harder one to notice by reading,
because an unreachable node is perfectly well-formed in isolation.

Why this is worth validating at all: every one of the five is invisible to
reading. A reader follows one path at a time, and all five are properties of
the whole graph.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field

import yaml

#: The page's step-1 heredoc, verbatim. A test asserts this still matches.
PLAYBOOK = """\
name: Integration is failing
entry: symptom
nodes:
  symptom:
    ask: What does the failure look like?
    options:
      - {answer: No data arrived at all, go: check-trigger}
      - {answer: Some records missing, go: check-filter}
      - {answer: Wrong values in the data, go: check-mapping}
  check-trigger:
    ask: Did the schedule fire?
    options:
      - {answer: "No", do: fix-schedule}
      - {answer: "Yes", go: check-auth}
  check-auth:
    ask: Are the credentials current?
    options:
      - {answer: "No", do: rotate-credentials}
      - {answer: "Yes", do: escalate-platform}
  check-filter:
    ask: Does the filter reference a field that was renamed?
    options:
      - {answer: "Yes", do: fix-filter}
      - {answer: "No", do: escalate-platform}
  check-mapping:
    ask: Is a dynamic process property set where you expect?
    options:
      - {answer: "No", do: trace-dpp}
      - {answer: "Yes", do: escalate-platform}
outcomes:
  fix-schedule: Re-enable the schedule and note why it was off.
  rotate-credentials: Rotate the token, then re-run the failed window.
  fix-filter: Update the filter to the current field name.
  trace-dpp: Find every get and set of the property, then correct the source.
  escalate-platform: Hand to the platform team with the trace attached.
  orphaned-outcome: Nothing routes here.
"""


@dataclass
class Report:
    nodes: int
    outcomes: int
    problems: list[str] = field(default_factory=list)

    def render(self) -> str:
        lines = [f"PLAYBOOK  {problem}" for problem in self.problems]
        verdict = "FAIL" if self.problems else "ok"
        lines.append(
            f"{verdict}: {self.nodes} nodes, {self.outcomes} outcomes, "
            f"{len(self.problems)} problem(s)"
        )
        return "\n".join(lines)


def validate(playbook: dict) -> Report:
    """Five checks. Each corresponds to a way a prose playbook fails silently."""
    nodes = playbook["nodes"]
    outcomes = playbook["outcomes"]
    entry = playbook["entry"]
    problems: list[str] = []

    if entry not in nodes:
        problems.append(f"entry {entry!r} is not a node")

    # 1 and 2. Every target resolves, and no option goes nowhere.
    for node_id, node in nodes.items():
        for option in node["options"]:
            if "go" in option and option["go"] not in nodes:
                problems.append(f"{node_id}: 'go: {option['go']}' is not a node")
            if "do" in option and option["do"] not in outcomes:
                problems.append(f"{node_id}: 'do: {option['do']}' is not an outcome")
            if "go" not in option and "do" not in option:
                problems.append(f"{node_id}: option {option['answer']!r} goes nowhere")

    # 3. Every outcome is reachable. Advice nobody can reach is usually the
    #    most interesting advice in the guide.
    routed = {o["do"] for n in nodes.values() for o in n["options"] if "do" in o}
    for outcome_id in outcomes:
        if outcome_id not in routed:
            problems.append(f"outcome {outcome_id!r}: nothing routes here")

    # 4. Every node is reachable from the entry. The page does not check this
    #    and it is the same defect as the one above, one level up: a question
    #    nobody can reach is a branch of the expert's knowledge that has
    #    quietly left the playbook, and it looks perfectly fine in isolation.
    reachable = {entry} if entry in nodes else set()
    frontier = list(reachable)
    while frontier:
        for option in nodes[frontier.pop()]["options"]:
            target = option.get("go")
            if target in nodes and target not in reachable:
                reachable.add(target)
                frontier.append(target)
    for node_id in nodes:
        if node_id not in reachable:
            problems.append(f"node {node_id!r}: unreachable from {entry!r}")

    # 5. No cycles, because a decision guide that loops never ends. Reported
    #    as the path, since "there is a cycle" is not actionable and
    #    "symptom -> check-trigger -> check-auth -> symptom" is.
    for cycle in find_cycles(nodes, entry):
        problems.append("cycle: " + " -> ".join(cycle))

    return Report(len(nodes), len(outcomes), problems)


def find_cycles(nodes: dict, entry: str) -> list[list[str]]:
    """Depth-first search from the entry, reporting each back edge once.

    One cycle is reported per back edge rather than per path that contains it:
    a guide with one loop in it has one defect, and printing every route into
    that loop buries the fix.
    """
    found: list[list[str]] = []
    seen_edges: set[tuple[str, str]] = set()

    def walk(node_id: str, path: list[str], on_path: set[str]) -> None:
        for option in nodes[node_id]["options"]:
            target = option.get("go")
            if target not in nodes:
                continue
            if target in on_path:
                edge = (node_id, target)
                if edge not in seen_edges:
                    seen_edges.add(edge)
                    found.append(path[path.index(target) :] + [target])
                continue
            walk(target, path + [target], on_path | {target})

    if entry in nodes:
        walk(entry, [entry], {entry})
    return found


def injections() -> list[tuple[str, str, callable]]:
    """One mutation per defect class, each applied to the repaired playbook."""

    def dangling_go(playbook: dict) -> None:
        playbook["nodes"]["check-trigger"]["options"][1]["go"] = "check-athu"

    def cycle(playbook: dict) -> None:
        option = playbook["nodes"]["check-auth"]["options"][1]
        del option["do"]
        option["go"] = "symptom"

    def dead_end(playbook: dict) -> None:
        del playbook["nodes"]["check-trigger"]["options"][0]["do"]

    def unreachable_node(playbook: dict) -> None:
        playbook["nodes"]["check-retry"] = {
            "ask": "Has it already retried three times?",
            "options": [
                {"answer": "Yes", "do": "escalate-platform"},
                {"answer": "No", "do": "fix-schedule"},
            ],
        }

    return [
        ("dangling-go", "a target that does not resolve", dangling_go),
        ("cycle", "a path that never ends", cycle),
        ("dead-end", "an option with no next step", dead_end),
        ("unreachable", "a question nobody can get to", unreachable_node),
    ]


def main() -> int:
    print("step 3: run it\n")
    report = validate(yaml.safe_load(PLAYBOOK))
    print(report.render())
    print(f"exit={1 if report.problems else 0}")

    print("\nOne finding, which is the deliberately planted orphan. Remove it:\n")
    repaired = yaml.safe_load(PLAYBOOK)
    del repaired["outcomes"]["orphaned-outcome"]
    clean = validate(repaired)
    print(clean.render())
    print(f"exit={1 if clean.problems else 0}")

    print("\n\nstep 4: confirm each defect class is caught\n")
    caught = {}
    for label, description, mutate in injections():
        broken = yaml.safe_load(PLAYBOOK)
        del broken["outcomes"]["orphaned-outcome"]
        mutate(broken)
        result = validate(broken)
        caught[label] = result.problems
        print(f"  {label:<13}{description}")
        for problem in result.problems:
            print(f"    {problem}")

    print(
        "\nFive classes, five catches, and two of the four injections report "
        "two problems\nrather than one. Both second findings are cascades.\n"
        "\nRemoving the `do` from check-trigger's first option leaves that "
        "option dangling\nand orphans `fix-schedule`, because that option was "
        "the only route to it. The\npage's own step 4 shows only the first of "
        "those two, although its orphan check\nwould have produced the second; "
        "the block was trimmed to one line per class.\n"
        "\nMistyping check-trigger's `go` target breaks that edge and also "
        "strands\n`check-auth`, which nothing else routes to. A findings "
        "count is therefore not\na defect count, and sizing a backlog from "
        "one overstates the work: here four\ndefects produce six findings, "
        "and two of the six disappear when the other\nfour are fixed."
    )

    ok = (
        len(report.problems) == 1
        and not clean.problems
        and all(caught[label] for label, _, _ in injections())
        and any("cycle: symptom" in p for p in caught["cycle"])
        and len(caught["dead-end"]) == 2
        and len(caught["dangling-go"]) == 2
    )
    if not ok:
        print(
            "\nunexpected: the five classes no longer behave as the page "
            f"describes (got {caught})",
            file=sys.stderr,
        )
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
