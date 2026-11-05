"""The release workflow, including the three properties that make it one.

A validator and a guided workflow can both be a list of checks. What separates
them is what the output is for, so these tests assert on the shape of the
record rather than only on the exit code: a step with no name, no detail or no
remedy has silently become a test again, and nothing else would notice.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from fieldguide.release import (
    GATES,
    STEPS,
    Blocked,
    Context,
    release_check,
)

REPO = Path(__file__).resolve().parent.parent
COPIED = ("concepts.yaml", "demonstrations.yaml", "docs", "drills", "src", "tests")

#: Every step but the last, which shells out to pytest. These tests run under
#: pytest already, and a nested session would quadruple the suite's runtime to
#: assert something `tests/test_drills.py` asserts directly.
FAST_STEPS = [s for s in STEPS if s.step_name != STEPS[-1].step_name]


def context_for(root: Path) -> Context:
    return Context(
        root=root,
        registry=root / "concepts.yaml",
        docs=root / "docs",
        demos=root / "demonstrations.yaml",
    )


@pytest.fixture
def copy_of_repo(tmp_path: Path) -> Path:
    root = tmp_path / "fieldguide"
    root.mkdir()
    for name in COPIED:
        source = REPO / name
        if source.is_dir():
            shutil.copytree(source, root / name, ignore=shutil.ignore_patterns("__pycache__"))
        else:
            shutil.copy2(source, root / name)
    return root


def test_every_step_has_a_name_that_reads_like_a_checklist_item():
    for function in STEPS:
        name = function.step_name
        assert name == name.lower() or name.split()[0].islower(), (
            f"{name!r} is titled like a test, not a checklist item"
        )
        assert not name.startswith("check"), f"{name!r} names the code, not the property"
        assert len(name.split()) >= 3, f"{name!r} is too terse to read as a record"


def test_every_step_returns_a_detail_on_success(copy_of_repo):
    """A passing step that prints a tick is a test. The detail is the record."""
    run = release_check(context_for(copy_of_repo), steps=FAST_STEPS)
    assert run.ok, run.render(len(FAST_STEPS))
    for result in run.results:
        assert result.detail.strip(), f"{result.name} passed without saying what it saw"
        assert result.detail != result.name


def test_a_blocked_step_names_the_thing_to_fix(copy_of_repo):
    page = copy_of_repo / "docs" / "concepts" / "diataxis.md"
    page.write_text(page.read_text(encoding="utf-8") + "\n```python\n", encoding="utf-8")

    run = release_check(context_for(copy_of_repo), steps=FAST_STEPS)
    blocked = run.blocked
    assert len(blocked) == 1, run.render(len(FAST_STEPS))
    assert "diataxis.md" in blocked[0].detail, (
        f"the remedy does not name the file: {blocked[0].detail!r}"
    )


def test_a_stale_generated_page_names_the_command_that_fixes_it(copy_of_repo):
    coverage = copy_of_repo / "docs" / "coverage.md"
    coverage.write_text("# Coverage\n\nEdited by hand.\n", encoding="utf-8")

    run = release_check(context_for(copy_of_repo), steps=FAST_STEPS)
    detail = next(r.detail for r in run.blocked)
    assert "fieldguide build" in detail, f"no remedy in {detail!r}"
    assert "coverage.md" in detail


def test_exactly_one_step_gates_and_it_is_the_one_everything_depends_on():
    """The page's finding was that nothing gated. Here one thing does.

    Every other step calls `load_registry`, so a registry that will not parse
    turns the rest into secondary failures about a file none of them could
    read. If a second step ever joins `GATES`, that is a claim about a real
    dependency and this test should be the place it gets argued.
    """
    assert GATES == frozenset({"the registry parses"})
    assert STEPS[0].step_name in GATES, "the gate must run first to be a gate"
    assert sum(1 for s in STEPS if s.step_name in GATES) == 1


def test_a_broken_registry_stops_the_workflow(copy_of_repo):
    (copy_of_repo / "concepts.yaml").write_text("concepts: [oh dear\n", encoding="utf-8")

    run = release_check(context_for(copy_of_repo), steps=FAST_STEPS)
    assert run.stopped_at == 1
    assert len(run.results) == 1, "a failed gate must not be followed by secondary failures"
    assert "concepts.yaml" in run.results[0].detail


def test_independent_failures_are_all_reported_in_one_run(copy_of_repo):
    """The behaviour the round-trip measurement depends on."""
    fenced = copy_of_repo / "docs" / "concepts" / "diataxis.md"
    fenced.write_text(fenced.read_text(encoding="utf-8") + "\n```python\n", encoding="utf-8")
    front = copy_of_repo / "docs" / "concepts" / "link-checking.md"
    front.write_text(
        front.read_text(encoding="utf-8").replace("---\n", "---\nsummary: [unclosed\n", 1),
        encoding="utf-8",
    )

    run = release_check(context_for(copy_of_repo), steps=FAST_STEPS)
    assert run.stopped_at is None, "a non-gating failure must not stop the workflow"
    assert len(run.blocked) == 2, run.render(len(FAST_STEPS))


def test_everything_gates_reports_one_failure_at_a_time(copy_of_repo):
    """The comparison, so the drill's 4-against-2 is a property of the code."""
    fenced = copy_of_repo / "docs" / "concepts" / "diataxis.md"
    fenced.write_text(fenced.read_text(encoding="utf-8") + "\n```python\n", encoding="utf-8")
    front = copy_of_repo / "docs" / "concepts" / "link-checking.md"
    front.write_text(
        front.read_text(encoding="utf-8").replace("---\n", "---\nsummary: [unclosed\n", 1),
        encoding="utf-8",
    )

    run = release_check(context_for(copy_of_repo), everything_gates=True, steps=FAST_STEPS)
    assert len(run.blocked) == 1
    assert run.stopped_at is not None


def test_the_record_says_what_to_do_next(copy_of_repo):
    fenced = copy_of_repo / "docs" / "concepts" / "diataxis.md"
    fenced.write_text(fenced.read_text(encoding="utf-8") + "\n```python\n", encoding="utf-8")

    rendered = release_check(context_for(copy_of_repo), steps=FAST_STEPS).render(
        len(FAST_STEPS)
    )
    assert "independent" in rendered and "re-run once" in rendered, (
        "a run with only independent failures should tell the author to fix them together"
    )


def test_a_clean_run_says_it_is_ready(copy_of_repo):
    rendered = release_check(context_for(copy_of_repo), steps=FAST_STEPS).render(
        len(FAST_STEPS)
    )
    assert "ready to release" in rendered


def test_blocked_carries_a_remedy_rather_than_a_diagnosis():
    """A convention, asserted so it stays one."""
    with pytest.raises(Blocked) as raised:
        raise Blocked("run `fieldguide build` and commit: coverage.md")
    assert "`" in str(raised.value) or ":" in str(raised.value)
