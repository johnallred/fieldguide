"""Every drill runs, and still prints what its page quotes.

This is the check the `scratch` triage reason existed for, and the reason that
reason could be retired. Eight pages quoted output from a measurement that ran
once in a temporary directory, so the figure on the page and the code that
produced it could drift apart with nothing noticing. All eight now have a
committed drill and an entry below. A reader could follow the page's golden path and get a different
answer from the one printed beside it, which is the defect `docpack` solves for
in-page samples and this guide had not solved for its own.

So each drill is committed, and each entry below names the exact lines its page
quotes. If a drill's behaviour changes, the page is wrong and this fails.

The table is deliberately literal. Matching on a loose pattern would let the
page and the drill drift in the ways that matter, which is the whole thing
being prevented: a figure is either the one the reader sees or it is not.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
DRILLS = REPO / "drills"

#: drill filename -> (page, exit code, lines the page quotes verbatim)
#:
#: `expect_exit` is part of the contract: a drill whose last state is a failing
#: check should exit non-zero, and one that walks through several states and
#: ends having proved them all should exit zero. Both appear below.
EXPECTED: dict[str, tuple[str, int, tuple[str, ...]]] = {
    "screencast_script.py": (
        "docs/concepts/screencasts.md",
        0,
        (
            "DRIFT  00:41  expected '{\"widgets\": 3}', got 'widgets: 3'",
            "1/2 beats still match what the video shows",
            "2/2 beats still match what the video shows",
            "DRIFT  00:12  expected 'widgets: 3', got '3 widgets found'",
        ),
    ),
    "vector_store.py": (
        "docs/concepts/vector-stores.md",
        0,
        (
            "       1       67     0.548",
            "       8      521     0.988",
            "      64     4000     1.000",
            "  lexical    1.000          0.135          0.568",
            "  dense      0.880          0.000          0.440",
            "  hybrid     0.935          0.065          0.500",
        ),
    ),
    "walkthrough_transclusion.py": (
        "docs/concepts/sample-walkthroughs.md",
        0,
        (
            "WALK  block 1: not found in samples/sync.py: 'RETRIES = 3'",
            "FAIL: 2 quoted block(s), 1 drifted",
            'rendered for "the retry count":  import click',
            'rendered for "the command flag": (empty)',
            "rendered:  RETRIES = 7",
        ),
    ),
    "gallery_audit.py": (
        "docs/concepts/sample-apps.md",
        0,
        (
            "GALLERY  stale: expected 'streamed 10 chunks', got 'streamed 8 chunks'",
            "GALLERY  missing: entrypoint samples/missing/main.py does not exist",
            "FAIL: 2/4 samples verified",
            "tickets about uncovered topics: 114 of 123",
            "retries                    -       41",
            "install                  yes        0",
            "demand coverage: 9 of 123 tickets",
        ),
    ),
    "guardrails.py": (
        "docs/concepts/hallucination-guardrails.md",
        0,
        (
            "which layer caught each failure, and which layers alone would miss it",
        ),
    ),
    "playbook.py": (
        "docs/concepts/playbooks.md",
        0,
        (
            "PLAYBOOK  outcome 'orphaned-outcome': nothing routes here",
            "FAIL: 5 nodes, 6 outcomes, 1 problem(s)",
            "ok: 5 nodes, 5 outcomes, 0 problem(s)",
            "    check-trigger: 'go: check-athu' is not a node",
            "    node 'check-auth': unreachable from 'symptom'",
            "    cycle: symptom -> check-trigger -> check-auth -> symptom",
            "    check-trigger: option 'No' goes nowhere",
            "    outcome 'fix-schedule': nothing routes here",
            "    node 'check-retry': unreachable from 'symptom'",
        ),
    ),
    "release_rounds.py": (
        "docs/concepts/guided-workflows.md",
        0,
        (
            "  run 1: blocked 3 of 6",
            "  runs needed: 4",
            "  runs needed: 2",
        ),
    ),
    "crawlability.py": (
        "docs/concepts/crawlability.md",
        0,
        (
            "CRAWL  api/reference.html: no-server-content: 4 words of text without running JavaScript",
            "CRAWL  docs/configure.html: no-server-content: 16 words of text without running JavaScript",
            "CRAWL  sitemap.xml: sitemap-ghost: lists https://widget.example/docs/legacy/, not served",
            "FAIL: 3 pages, 10 problem(s)",
            "generated sitemap with 3 url(s)",
            "ok: 3 pages, 0 problem(s)",
        ),
    ),
    "security_lint.py": (
        "docs/concepts/security-documentation.md",
        0,
        (
            "SEC  docs/quickstart.md:6:  pipe-to-shell: piping a downloaded script into a shell teaches an unverifiable install",
            "SEC  docs/quickstart.md:7:  hardcoded-secret: a credential-shaped literal; use a placeholder or an env var",
            "SEC  docs/quickstart.md:15: hardcoded-secret: a credential-shaped literal; use a placeholder or an env var",
            "SEC  docs/quickstart.md:21: world-writable: world-writable permissions",
            "FAIL: 5 finding(s)",
            "FAIL: 6 finding(s)",
            "ok: 0 finding(s)",
        ),
    ),
    "terminology_drift.py": (
        "docs/concepts/terminology-drift.md",
        0,
        (
            "widget                    3      5    60%  Widget CLI(1), widget-cli(1)",
            "widget                    1      3    33%  Widget CLI(1), widget-cli(1)",
            "worst pages: docs/b.md (3), docs/c.md (3)",
            "FAIL: 6 deprecated usage(s)",
            "widget                    3      3   100%",
            "ok: 0 deprecated usage(s)",
            "docs/b.md: ...'e\\nPoint the Widget CLI at your'...",
        ),
    ),
    "workshop_arithmetic.py": (
        "docs/concepts/workshops.md",
        0,
        (
            "two hours against the 34-hour first-week path: 6%",
            "shortest path in the guide: domain-context, 6 concepts, 24h (8%)",
            "concepts in this corpus of 3h or less: 48/106",
            "  Technical writing as a craft                     8h",
            "                                            total 34h",
        ),
    ),
}

#: drill filename -> the page heredocs its sample constants must equal.
#:
#: The quoted-output contract above catches a drill that stops printing what
#: its page shows. It does not catch the subtler case: a drill whose *inputs*
#: have drifted from the ones the page tells the reader to create. Then both
#: halves agree about the output and neither matches what the reader typed,
#: which is the failure this file exists to make impossible.
SAMPLE_CONTRACTS: dict[str, tuple[str, str, tuple[str, ...]]] = {
    "security_lint.py": (
        "docs/concepts/security-documentation.md",
        "cat > docs/quickstart.md <<'MDEOF'\n",
        ("QUICKSTART_BAD", "QUICKSTART_FIXED"),
    ),
    "terminology_drift.py": (
        "docs/concepts/terminology-drift.md",
        "<<'EOF'\n",
        ("GLOSSARY", "PAGE_A", "PAGE_B", "PAGE_C"),
    ),
    "gallery_audit.py": (
        "docs/concepts/sample-apps.md",
        "cat > gallery.yaml <<'EOF'\n",
        ("MANIFEST",),
    ),
    "walkthrough_transclusion.py": (
        "docs/concepts/sample-walkthroughs.md",
        "cat > samples/sync.py <<'EOF'\n",
        ("SAMPLE",),
    ),
    "playbook.py": (
        "docs/concepts/playbooks.md",
        "cat > playbook.yaml <<'EOF'\n",
        ("PLAYBOOK",),
    ),
}


def test_the_guardrail_table_is_the_matrix_the_code_produces():
    """A markdown table is prose. This makes it an assertion.

    The `hallucination-guardrails` page publishes its results as a table
    rather than as console output, which reads better and rots the same way.
    Its argument rests on two rows passing one layer and failing another, so
    the table is parsed here and compared cell by cell to a real run.
    """
    page = (REPO / "docs/concepts/hallucination-guardrails.md").read_text(encoding="utf-8")
    result = run_drill("guardrails.py")
    assert result.returncode == 0, result.stdout + result.stderr

    computed = {}
    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) == 5 and set(parts[1:]) <= {"CAUGHT", "-"}:
            computed[parts[0]] = tuple(parts[1:])
    assert computed, f"no matrix rows parsed from the drill:\n{result.stdout}"

    published = {}
    for line in page.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip().strip("*").strip() for c in line.strip("|").split("|")]
        if len(cells) == 5 and set(cells[1:]) <= {"CAUGHT", "-"}:
            published[cells[0]] = tuple(cells[1:])

    assert published == computed, (
        "the published guardrail table is no longer what the code produces\n"
        f"page:  {sorted(published.items())}\n"
        f"drill: {sorted(computed.items())}"
    )


def test_the_crawlability_drill_runs_the_pages_own_audit():
    """The strongest form of the contract: the drill *is* the page's script.

    `drills/crawlability.py` writes the page's `crawl.py` to a temporary
    directory and runs it as a subprocess rather than reimplementing it, so
    there is exactly one copy of the logic being demonstrated. This asserts
    the copy in the drill is still byte-for-byte the one the page prints, and
    that the eight sample files are the ones the page tells you to create.
    """
    page = (REPO / "docs/concepts/crawlability.md").read_text(encoding="utf-8")

    opener = "cat > crawl.py <<'PY'\n"
    start = page.index(opener) + len(opener)
    expected_audit = page[start : page.index("\nPY\n", start)] + "\n"

    module = load_drill("crawlability.py")
    assert module["AUDIT_SOURCE"] == expected_audit, (
        "drills/crawlability.py no longer carries the audit the page prints"
    )

    staged = []
    position = 0
    while (found := page.find("cat > ", position)) != -1:
        line_end = page.index("\n", found)
        line = page[found:line_end]
        if line.endswith("<<'EOF'"):
            name = line[len("cat > ") : -len(" <<'EOF'")]
            body_end = page.index("\nEOF\n", line_end)
            staged.append((name, page[line_end + 1 : body_end] + "\n"))
        position = line_end

    assert module["SITE_BEFORE"] + module["SITE_AFTER"] == tuple(staged), (
        "the drill's sample site is no longer the one the page writes"
    )


@pytest.mark.parametrize("name", sorted(SAMPLE_CONTRACTS))
def test_a_drill_uses_the_same_samples_its_page_tells_you_to_write(name):
    page, opener, constants = SAMPLE_CONTRACTS[name]
    # The heredoc delimiter is whatever word the opener used.
    terminator = opener.strip().rsplit("<<", 1)[1].strip("'\"") + "\n"
    text = (REPO / page).read_text(encoding="utf-8")

    bodies = []
    position = 0
    while (found := text.find(opener, position)) != -1:
        start = found + len(opener)
        end = text.index(terminator, start)
        bodies.append(text[start:end])
        position = end
    assert len(bodies) == len(constants), (
        f"{page} has {len(bodies)} heredocs, but {name} declares {len(constants)} samples"
    )

    module = load_drill(name)
    for constant, body in zip(constants, bodies):
        assert module[constant] == body, (
            f"{name}:{constant} is no longer the text {page} writes.\n"
            f"--- the page says ---\n{body}\n--- the drill has ---\n{module[constant]}"
        )


def load_drill(name: str) -> dict[str, object]:
    """Import a drill for its constants, without running it.

    A bare `exec` into a dict is not enough: `@dataclass` looks its own module
    up in `sys.modules` to resolve annotations, so a drill that defines one
    fails with an AttributeError about `NoneType`. `playbook.py` was the first
    drill to hit that. Building a real module and registering it fixes it, and
    `__name__` is deliberately not "__main__" so importing does not run it.
    """
    module_name = f"drill_{name.removesuffix('.py')}"
    spec = importlib.util.spec_from_file_location(module_name, DRILLS / name)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(module_name, None)
    return vars(module)


def run_drill(name: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(DRILLS / name)],
        capture_output=True,
        text=True,
        timeout=180,
        cwd=REPO,
    )


@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_a_drill_still_prints_what_its_page_quotes(name):
    page, expect_exit, lines = EXPECTED[name]
    result = run_drill(name)
    assert result.returncode == expect_exit, (
        f"{name} exited {result.returncode}, expected {expect_exit}\n{result.stdout}\n{result.stderr}"
    )
    for line in lines:
        assert line in result.stdout, (
            f"{name} no longer prints a line {page} quotes:\n  {line!r}\n"
            f"--- its output ---\n{result.stdout}"
        )


@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_the_page_still_quotes_what_the_drill_prints(name):
    """The other direction, which is the one that rots quietly.

    A drill can be updated and its page left alone. Then the drill is correct,
    the test above passes, and the page carries a figure nothing produces.
    """
    page, _, lines = EXPECTED[name]
    text = (REPO / page).read_text(encoding="utf-8")
    for line in lines:
        assert line in text, f"{page} no longer quotes a line {name} prints:\n  {line!r}"


def test_every_committed_drill_is_covered():
    """A drill nobody asserts on is a drill that can quietly stop working."""
    committed = {
        path.name for path in DRILLS.glob("*.py") if not path.name.startswith("_")
    }
    # These eight report timings rather than constants, so their pages state
    # the figures as one run on one machine and the shape as the claim. They
    # cannot join the page-figure contract: asserting a figure that moves by
    # 30% between runs would make the suite flaky and teach nothing. Three of
    # them are covered by `test_a_drill_runs_at_all` below; the other five
    # need a dependency this guide does not have, and say so on their pages.
    # `sphinx_autodoc.py` reports no timings but belongs with them: its
    # dependencies are not installed by default, so the suite cannot run it.
    timing_dependent = {
        "arithmetic_intensity.py",
        "deadline_sweep.py",
        "frames.py",
        "generator_build.py",
        "inference_sweep.py",
        "sphinx_autodoc.py",
        "onnx_compat.py",
        "usd_composition.py",
    }
    uncovered = committed - set(EXPECTED) - timing_dependent
    assert not uncovered, f"committed drills with no assertion: {sorted(uncovered)}"


@pytest.mark.parametrize(
    "name",
    sorted(
        {"arithmetic_intensity.py", "deadline_sweep.py", "frames.py"}
    ),
)
def test_a_drill_runs_at_all(name):
    """For the drills whose numbers are machine-dependent, at least assert they run.

    The five excluded from this list need `usd-core`, `onnx`, `onnxruntime`,
    `sphinx` or `myst-parser`,
    which the guide does not depend on; their pages say so and name the install.
    """
    result = run_drill(name)
    assert result.returncode == 0, f"{name} failed:\n{result.stdout}\n{result.stderr}"
    assert result.stdout.strip(), f"{name} printed nothing"
