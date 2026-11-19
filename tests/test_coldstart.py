"""The quick start's contract, checked without paying for a full cold start.

`scripts/coldstart.py` runs the README quick start in a fresh virtual
environment. It is honest and it is slow: a venv, an install and the whole test
suite, which is why it is its own CI job rather than part of this one.

These tests cover the half that is cheap. They do not run the commands; they
assert that every line in the block has a stated disposition, so that a line
cannot be silently skipped, and they encode the ordering defect that started
this file: `fieldguide render site` reads a built site, and for most of this
project's life the quick start never built one. It passed for the author
because `site/` was committed, and would have failed for the first reader.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent


def _load():
    """Import the script by path; `scripts/` is not a package.

    The module is registered in `sys.modules` before it is executed, for the
    same reason `tests/test_drills.py::load_drill` does it: `@dataclass`
    resolves its annotations by looking its own module up there, and without
    the registration `Step` fails with an AttributeError about `NoneType`.
    """
    spec = importlib.util.spec_from_file_location(
        "coldstart_script", REPO / "scripts" / "coldstart.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


coldstart = _load()


@pytest.fixture(scope="module")
def steps():
    return coldstart.quick_start((REPO / "README.md").read_text(encoding="utf-8"))


def test_the_quick_start_has_commands_in_it(steps):
    """Guards against an extraction that silently returns nothing.

    A parser that finds no lines would make every other test here vacuous, and
    the cold start would report success over an empty list.
    """
    assert len(steps) >= 8, f"only {len(steps)} line(s) extracted"
    commands = [s.command for s in steps]
    assert any(c.startswith("fieldguide check") for c in commands)
    assert any("pytest" in c for c in commands)


def test_the_quick_start_builds_the_site_before_it_reads_it(steps):
    """The defect this file exists for.

    `fieldguide render site` takes a built site directory. If nothing builds
    one first, the line works only where a stale `site/` happens to be lying
    around, which is exactly the state a new clone is not in.
    """
    order = [s.command for s in steps]
    reads = next((i for i, c in enumerate(order) if c.startswith("fieldguide render")), None)
    assert reads is not None, "the quick start no longer renders the site"
    builds = [i for i, c in enumerate(order) if c.startswith("mkdocs build")]
    assert builds, "nothing in the quick start builds the site"
    assert min(builds) < reads, (
        "`fieldguide render site` comes before anything builds a site:\n  "
        + "\n  ".join(f"{i}: {c}" for i, c in enumerate(order))
    )


def test_a_line_that_is_not_run_says_why(steps):
    """A skip with no reason is indistinguishable from an oversight."""
    for step in steps:
        if step.skip:
            assert len(step.skip) > 10, f"{step.command!r} is skipped without a reason"


def test_a_line_expected_to_fail_says_why(steps):
    """An expected non-zero exit is a claim, and claims carry their reason.

    `fieldguide new diataxis` exits 2 because every registered concept already
    has a page and an unregistered one is refused. That is worth stating, both
    so a reader is not alarmed and so the line is revisited if it ever starts
    passing.
    """
    readme = (REPO / "README.md").read_text(encoding="utf-8")
    for step in steps:
        if step.expected != 0:
            line = next(l for l in readme.splitlines() if l.startswith(step.command))
            reason = line.split(f"exits {step.expected}", 1)[1].lstrip(": ").strip()
            assert reason, f"{step.command!r} expects {step.expected} with no reason given"
