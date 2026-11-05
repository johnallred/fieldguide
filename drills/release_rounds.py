#!/usr/bin/env python3
"""What stopping at the first failure costs an author, measured on a real command.

    python3 drills/release_rounds.py

The `guided-workflows` page builds a three-step workflow, plants three defects
and counts round trips: four runs when every step gates, two when none does.
That measurement was made against a toy workflow written for the page. This
runs the same experiment against `fieldguide release-check`, which is a real
command with seven steps that check real properties of this repository.

The method is the page's. Copy the repository, plant three independent
defects, then behave like an author: run the workflow, fix exactly what it
reported, run it again, and stop when it passes. Count the runs.

Independence is the whole claim, so the defects are deliberately unrelated: a
generated page left stale, a code fence left open, and a page's front matter
made unparseable. None of the three has any bearing on the others. A workflow
that reports them one at a time is not being careful, it is charging the
author three round trips for the order its steps happened to be written in.

The drill-contract step is left out of the measurement. It shells out to
pytest, it passes in every run here, and a step that always passes cannot
change what a failure costs; including it would make the answer identical and
the drill twenty times slower.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from fieldguide.release import STEPS, Context, release_check  # noqa: E402

#: Copied into the temporary repository. `site/` is a build output and `.git`
#: is large and irrelevant, so neither is worth the seconds.
COPIED = ("concepts.yaml", "demonstrations.yaml", "docs", "drills", "src", "tests")


def plant(root: Path) -> dict[str, object]:
    """Three unrelated defects, each tripping a different step.

    Returns a repair for each, so the author below can fix exactly what the
    workflow reported and nothing else, which is the behaviour being measured.
    """
    coverage = root / "docs" / "coverage.md"
    fenced = root / "docs" / "concepts" / "diataxis.md"
    front = root / "docs" / "concepts" / "link-checking.md"

    original = {path: path.read_text(encoding="utf-8") for path in (coverage, fenced, front)}

    # 1. A generated page edited by hand, which is what forgetting to re-run
    #    `fieldguide build` after a registry change looks like.
    coverage.write_text(
        original[coverage].replace("# Coverage", "# Coverage\n\nEdited by hand.", 1),
        encoding="utf-8",
    )
    # 2. An unclosed code fence, which renders the rest of the page as code.
    fenced.write_text(original[fenced] + "\n```python\nprint('unclosed')\n", encoding="utf-8")
    # 3. Front matter no YAML parser will read, which is invisible in a browser.
    front.write_text(
        original[front].replace("---\n", "---\nsummary: [unclosed\n", 1), encoding="utf-8"
    )

    return {
        "every generated page is up to date": (coverage, original[coverage]),
        "fence structure is sound in every page": (fenced, original[fenced]),
        "every page's front matter parses as YAML": (front, original[front]),
    }


def count_runs(root: Path, *, everything_gates: bool) -> int:
    """Behave like an author, and count how many times they had to run it."""
    repairs = plant(root)
    context = Context(
        root=root,
        registry=root / "concepts.yaml",
        docs=root / "docs",
        demos=root / "demonstrations.yaml",
    )
    measured = [s for s in STEPS if s.step_name != STEPS[-1].step_name]

    runs = 0
    while True:
        runs += 1
        run = release_check(context, everything_gates=everything_gates, steps=measured)
        print(f"  run {runs}: blocked {len(run.blocked)} of {len(measured)}")
        if run.ok:
            return runs
        for result in run.blocked:
            # A step this drill did not plant is a defect that was already in
            # the repository. Say which one: the first version of this loop
            # just kept going and reported that the author gave up after
            # eleven runs, which is true and useless. It happened the first
            # time it ran against a register change with no rebuild behind it.
            if result.name not in repairs:
                raise SystemExit(
                    f"{result.name!r} is blocked and this drill did not plant "
                    f"it, so the repository itself is not releasable:\n  "
                    f"{result.detail}"
                )
            path, text = repairs[result.name]
            path.write_text(text, encoding="utf-8")
        if runs > 10:
            raise SystemExit("the author gave up; something is not converging")


def staged(destination: Path) -> Path:
    root = destination / "fieldguide"
    root.mkdir()
    for name in COPIED:
        source = REPO / name
        if source.is_dir():
            shutil.copytree(source, root / name, ignore=shutil.ignore_patterns("__pycache__"))
        else:
            shutil.copy2(source, root / name)
    return root


def main() -> int:
    print("three independent defects, and an author fixing exactly what is reported\n")

    with TemporaryDirectory() as tmp:
        print("everything gates, which is what break-on-failure does:")
        pessimistic = count_runs(staged(Path(tmp)), everything_gates=True)
        print(f"  runs needed: {pessimistic}\n")

    with TemporaryDirectory() as tmp:
        print("one real gate, which is what fieldguide release-check does:")
        actual = count_runs(staged(Path(tmp)), everything_gates=False)
        print(f"  runs needed: {actual}")

    print(
        f"\n{pessimistic} runs against {actual}, same defects, same fixes. The "
        "difference is\nentirely the decision about which steps gate, and six "
        "of this workflow's\nseven steps do not."
    )
    ok = (pessimistic, actual) == (4, 2)
    if not ok:
        print(
            f"\nunexpected: measured {pessimistic} and {actual} rather than 4 and 2",
            file=sys.stderr,
        )
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
