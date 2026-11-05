"""A guided workflow for releasing this guide, as distinct from a validator.

`fieldguide check` is a validator: it reports everything it can see at once and
says nothing about what to do next. This is the other thing the
`guided-workflows` page describes, and the difference is not cosmetic. Three
properties make a step a workflow step rather than a test:

- a **human-readable name** that reads like a checklist item, so the output is
  a record somebody can hand to somebody else;
- a **detail on success**, so a passing step says what it observed rather than
  printing a tick; and
- a **specific remedy on failure**, raised as `Blocked` with the thing to fix,
  not an assertion error with a traceback.

The interesting part is `GATES`. A step gates when later steps genuinely
cannot run without it, and the default most people write is that everything
gates, because `break` on failure is the shortest code. The `guided-workflows`
page builds a three-step workflow and finds that none of its steps gate
anything, which halves the number of round trips an author needs.

This workflow has one real gate, and that is the more useful result: gates are
not a myth, they are just far rarer than sequential code implies. Every step
below reads the registry, so if the registry does not parse there is nothing
for the other six to say, and running them would produce six confusing
secondary failures instead of one true one. Everything else here is
independent: a stale generated page has no bearing on whether a fence is
balanced, and a reader who has to learn that in two separate runs has been
charged a round trip for the author's convenience.
"""

from __future__ import annotations

import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

import yaml

from .demos import DemonstrationError, load_demonstrations
from .dialect import front_matter_findings
from .fences import fence_findings
from .generate import (
    coverage_page,
    demonstrated_page,
    path_page,
    paths_index_page,
    placeholder_page,
    study_plan_page,
)
from .registry import RegistryError, load_registry, validate_against_tree


class Blocked(Exception):
    """A step that cannot pass, carrying the specific thing to fix.

    The message is the remedy, not the diagnosis. "missing summary: b.md" is
    actionable; "summary check failed" sends the reader back to the source.
    """


@dataclass(frozen=True)
class Context:
    """Where the workflow runs. Everything a step needs, nothing it does not."""

    root: Path
    registry: Path
    docs: Path
    demos: Path


class Step(Protocol):
    step_name: str

    def __call__(self, context: Context) -> str: ...


STEPS: list[Step] = []


def step(name: str) -> Callable[[Callable[[Context], str]], Step]:
    """Register a workflow step under a name that reads like a checklist item."""

    def decorate(function: Callable[[Context], str]) -> Step:
        function.step_name = name  # type: ignore[attr-defined]
        STEPS.append(function)  # type: ignore[arg-type]
        return function  # type: ignore[return-value]

    return decorate


@step("the registry parses")
def check_registry_parses(context: Context) -> str:
    try:
        registry = load_registry(context.registry)
    except FileNotFoundError as error:
        raise Blocked(f"{context.registry} is missing") from error
    except (RegistryError, yaml.YAMLError) as error:
        # `yaml.YAMLError` is not decoration. A step named "the registry
        # parses" that catches only the registry's own validation error
        # misses the commonest way a registry fails to parse, which is a
        # syntax error in the YAML. The first version of this step did
        # exactly that, and `test_a_broken_registry_stops_the_workflow`
        # is the reason it does not any more.
        first = str(error).strip().splitlines()[0]
        raise Blocked(f"{context.registry.name} does not parse: {first}") from error
    return (
        f"{len(registry.concepts)} concepts and {len(registry.paths)} paths "
        f"loaded from {context.registry.name}"
    )


@step("every concept page satisfies the page contract")
def check_page_contract(context: Context) -> str:
    registry = load_registry(context.registry)
    findings = validate_against_tree(registry, context.docs)
    if not findings.ok:
        first = findings.render().strip().splitlines()
        detail = next((line.strip() for line in first if line.strip().startswith("-")), "")
        raise Blocked(
            f"the registry and the docs tree disagree; run `fieldguide check`"
            + (f" (first: {detail})" if detail else "")
        )
    written = sum(1 for c in registry.concepts if c.status != "planned")
    return f"{written} written pages carry all seven required sections"


@step("the demonstration register decides every concept")
def check_demonstration_register(context: Context) -> str:
    registry = load_registry(context.registry)
    try:
        demos = load_demonstrations(context.demos, registry)
    except DemonstrationError as error:
        raise Blocked(f"{context.demos.name}: {error}") from error
    # Several entries can point at one concept, so count concepts rather than
    # entries: the claim is coverage, and 78 entries over 72 concepts would
    # read as though the two numbers summed to the corpus.
    demonstrated = {entry.concept for entry in demos.entries}
    return (
        f"{len(demonstrated)} concepts demonstrated and {len(demos.triage)} "
        f"triaged, covering all {len(demonstrated) + len(demos.triage)}"
    )


@step("every generated page is up to date")
def check_generated_pages(context: Context) -> str:
    registry = load_registry(context.registry)
    demos = load_demonstrations(context.demos, registry)
    targets: dict[Path, str] = {
        context.docs / "coverage.md": coverage_page(registry),
        context.docs / "study-plan.md": study_plan_page(registry),
        context.docs / "paths" / "index.md": paths_index_page(registry),
        context.docs / "demonstrated.md": demonstrated_page(registry, demos),
    }
    for learning_path in registry.paths:
        targets[context.docs / "paths" / f"{learning_path.id}.md"] = path_page(
            registry, learning_path.id
        )
    for concept in registry.concepts:
        if concept.status != "planned":
            continue
        page = context.docs / concept.page
        if page.exists() and "generated: true" not in page.read_text(encoding="utf-8"):
            continue
        targets[page] = placeholder_page(registry, concept.id)

    stale = [
        path.name
        for path, text in targets.items()
        if not path.exists() or path.read_text(encoding="utf-8") != text
    ]
    if stale:
        raise Blocked(
            f"run `fieldguide build` and commit: {', '.join(sorted(stale)[:4])}"
            + (f" and {len(stale) - 4} more" if len(stale) > 4 else "")
        )
    return f"{len(targets)} generated pages match the registry"


@step("fence structure is sound in every page")
def check_fences(context: Context) -> str:
    pages = sorted(context.docs.rglob("*.md"))
    findings = [f for page in pages for f in fence_findings(page)]
    if findings:
        raise Blocked(f"unbalanced code fences: {findings[0]}")
    return f"{len(pages)} pages open and close every code fence"


@step("every page's front matter parses as YAML")
def check_front_matter(context: Context) -> str:
    findings = front_matter_findings(context.docs)
    if findings:
        raise Blocked(f"unparseable front matter: {findings[0]}")
    return "every page is machine-readable above the first heading"


@step("every committed drill still prints what its page quotes")
def check_drills(context: Context) -> str:
    """The contract from `tests/test_drills.py`, as a release step.

    It belongs here rather than only in the test suite because it is the one
    check whose failure means a published page is lying to a reader, which is
    a different severity from a stale index.
    """
    tests = context.root / "tests" / "test_drills.py"
    if not tests.exists():
        raise Blocked(f"{tests.relative_to(context.root)} is missing")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(tests), "-q", "--no-header"],
        cwd=context.root,
        capture_output=True,
        text=True,
        timeout=600,
    )
    if result.returncode != 0:
        failures = [
            line.strip()
            for line in result.stdout.splitlines()
            if line.startswith("FAILED") or line.startswith("ERROR")
        ]
        raise Blocked(
            "a page and its drill disagree: "
            + (failures[0] if failures else "run `pytest tests/test_drills.py`")
        )
    # The timing is dropped: a release record that changes on every run is
    # one nobody can diff, and this detail is about how many contracts held.
    summary = next(
        (line.strip() for line in reversed(result.stdout.splitlines()) if "passed" in line),
        "",
    )
    count = summary.split(" passed", 1)[0].strip() if " passed" in summary else "every"
    return f"{count} page-and-drill contract(s) hold"


#: A step gates when later steps genuinely cannot run without it.
#:
#: Exactly one does. Every other step calls `load_registry`, so a registry
#: that will not parse turns the remaining six into six secondary failures
#: about a file none of them could read. Nothing else here is a dependency:
#: fences, front matter, the register and the generated pages are independent
#: properties of the same tree, and stopping at the first one costs the author
#: a round trip for nothing.
GATES: frozenset[str] = frozenset({"the registry parses"})


@dataclass
class Result:
    number: int
    name: str
    status: str
    detail: str


@dataclass
class Run:
    results: list[Result] = field(default_factory=list)
    stopped_at: int | None = None

    @property
    def blocked(self) -> list[Result]:
        return [r for r in self.results if r.status == "BLOCKED"]

    @property
    def ok(self) -> bool:
        return not self.blocked

    def render(self, total: int) -> str:
        lines = []
        for result in self.results:
            if result.status == "BLOCKED":
                lines.append(f"  [{result.number}/{total}] BLOCKED  {result.name}")
                lines.append(f"           {result.detail}")
            else:
                lines.append(f"  [{result.number}/{total}] ok       {result.name}")
                lines.append(f"           {result.detail}")
        if self.stopped_at is not None:
            lines.append("")
            lines.append(
                f"stopped at step {self.stopped_at}, which gates the rest. "
                "Fix the above and re-run."
            )
        elif self.blocked:
            lines.append("")
            lines.append(
                f"{len(self.blocked)} of {total} steps blocked. "
                "All of them are independent, so fix them together and re-run once."
            )
        else:
            lines.append("")
            lines.append(f"all {total} steps passed; ready to release")
        return "\n".join(lines)


def release_check(
    context: Context,
    *,
    everything_gates: bool = False,
    steps: list[Step] | None = None,
) -> Run:
    """Run every step, stopping only for a step that genuinely gates the rest.

    `everything_gates` is the comparison the `guided-workflows` page measures:
    it is the behaviour of a `break`-on-failure loop, kept here so the cost of
    that default can be reproduced against this command rather than asserted.

    `steps` narrows the workflow, which the round-trip drill uses to leave out
    the step that shells out to pytest. An always-passing step cannot change
    how many runs a failure costs, and leaving it in would make the
    measurement twenty times slower for an identical answer.
    """
    run = Run()
    for number, function in enumerate(steps if steps is not None else STEPS, 1):
        try:
            detail = function(context)
        except Blocked as blocked:
            run.results.append(Result(number, function.step_name, "BLOCKED", str(blocked)))
            if everything_gates or function.step_name in GATES:
                run.stopped_at = number
                break
        else:
            run.results.append(Result(number, function.step_name, "ok", detail))
    return run
