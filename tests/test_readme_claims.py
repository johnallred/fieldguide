"""The numbers the README states, checked against the things they count.

The README claimed nine CI gates for most of this project's life. There was one
workflow, `pages.yml`, and it deployed. Nothing was deleted: the gates workflow
was never written. A wrong number written as a word is valid prose that spells
clean, and the one claim a reader can check in ten seconds was the one that was
false, in a repository whose whole argument is that standards should be enforced
by machinery rather than by review comments.

The companion repository already had this test. This one did not, which is why
this one had the defect.

Counting gates needs a rule for which steps are gates. `docpack` filtered step
names by prefix, and that filter swallowed a real gate whose label happened to
start with an excluded word; it reported nine for a workflow with ten and failed
against a correct README. A prefix match on a human-written label is a guess. So
the rule here is structural instead: **a gate is a step with a `name`**, setup
steps are left unnamed, and `gates.yml` says so in a comment. Nothing has to be
inferred from what a label happens to begin with.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parent.parent
WORKFLOWS = REPO / ".github" / "workflows"

# Jobs that run after a change has landed. They are not gates, whatever they
# check, because by the time they run the change is already on main.
NOT_GATES = {"deploy", "publish"}

NUMBER_WORDS = {
    1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six",
    7: "seven", 8: "eight", 9: "nine", 10: "ten", 11: "eleven", 12: "twelve",
}


def readme() -> str:
    return (REPO / "README.md").read_text(encoding="utf-8")


def gates() -> list[str]:
    """Every named step in every workflow job that is not a deploy."""
    found: list[str] = []
    for path in sorted(WORKFLOWS.glob("*.yml")):
        workflow = yaml.safe_load(path.read_text(encoding="utf-8"))
        for job_id, job in (workflow.get("jobs") or {}).items():
            if job_id in NOT_GATES:
                continue
            for step in job.get("steps", []):
                if "name" in step:
                    found.append(f"{path.name}:{job_id}: {step['name']}")
    return found


def test_the_readme_states_the_number_of_gates_that_exist():
    found = gates()
    quoted = re.search(r"(\w+) gates on every pull request", readme())
    assert quoted, "the README no longer states a gate count"
    assert quoted.group(1).lower() == NUMBER_WORDS.get(len(found), ""), (
        f"the README says {quoted.group(1)} gates; the workflows define "
        f"{len(found)}:\n  " + "\n  ".join(found)
    )


def test_every_gate_is_a_step_that_runs_something():
    """The counting rule only holds if named steps are commands.

    If a named step were an action (`uses:`), the count would include setup and
    the rule above would quietly become the prefix guess it replaced.
    """
    offenders = []
    for path in sorted(WORKFLOWS.glob("*.yml")):
        workflow = yaml.safe_load(path.read_text(encoding="utf-8"))
        for job_id, job in (workflow.get("jobs") or {}).items():
            if job_id in NOT_GATES:
                continue
            for step in job.get("steps", []):
                if "name" in step and "run" not in step:
                    offenders.append(f"{path.name}:{job_id}: {step['name']}")
    assert not offenders, (
        "a named step is not a command, so it would be miscounted as a gate:\n  "
        + "\n  ".join(offenders)
    )


def test_the_gates_run_before_a_change_lands():
    """A gate that only runs on push is a gate on publication, not on merge.

    This is the half of the original defect that the count alone would not have
    caught: three real checks existed, inside the deploy workflow, triggered on
    push to main. They blocked the site going out. They never blocked a merge.
    """
    gating = [
        p.name
        for p in sorted(WORKFLOWS.glob("*.yml"))
        if set(yaml.safe_load(p.read_text(encoding="utf-8")).get("jobs", {})) - NOT_GATES
    ]
    assert gating, "no workflow defines a gating job"
    for name in gating:
        workflow = yaml.safe_load((WORKFLOWS / name).read_text(encoding="utf-8"))
        # PyYAML reads a bare `on:` key as the boolean True.
        triggers = workflow.get("on", workflow.get(True))
        assert "pull_request" in (triggers or {}), (
            f"{name} defines gating jobs but has no pull_request trigger, so "
            "nothing it checks can block a merge"
        )


def _collected(*paths: str) -> int:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q",
         "-p", "no:cacheprovider", *paths],
        cwd=REPO, capture_output=True, text=True, timeout=300,
    )
    match = re.search(r"(\d+) tests? collected", result.stdout)
    assert match, f"could not read a collected count:\n{result.stdout[-500:]}"
    return int(match.group(1))


@pytest.mark.parametrize(
    "pattern, paths, what",
    [
        (r"pytest -q\s+#\s*(\d+) tests", (), "everything pytest collects"),
        (r"\((\d+) with the src/ doctests", (), "everything pytest collects"),
        (r"tests/\s+(\d+) tests,", ("tests",), "the tests directory alone"),
    ],
)
def test_the_readme_states_the_number_of_tests_that_exist(pattern, paths, what):
    """Three figures, two of which must agree with each other.

    The README quotes the total in the quick start and again in the layout
    block, alongside the tests-directory figure. Checking only one of them
    leaves the other free to rot.
    """
    quoted = re.search(pattern, readme())
    assert quoted, f"the README no longer states a count for {what}"
    actual = _collected(*paths)
    assert int(quoted.group(1)) == actual, (
        f"the README says {quoted.group(1)} for {what}; pytest collects {actual}"
    )
