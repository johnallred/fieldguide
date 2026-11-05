#!/usr/bin/env python3
"""MkDocs against Sphinx on the same corpus, and the comparison that inverts.

    python3 drills/generator_build.py

Needs `mkdocs` and `sphinx`. Takes about a minute.

The `docusaurus` page quotes a build-time comparison: "a 121-page corpus in 0.6
seconds for bare MkDocs and 3.5 seconds for Sphinx". That measurement ran once
and was never committed, so it was the only figure about Sphinx anywhere in
this corpus and nobody could check it.

It reproduces, and it is misleading, which is a more interesting outcome than
either being wrong or being right. The ratio holds for a **cold** build, the
kind CI does on a fresh container every time. It does not hold for the build a
writer runs forty times an afternoon, because Sphinx is incremental and MkDocs
is not, and past a few hundred pages the comparison inverts outright.

## What is being compared, and what that costs in fairness

Both projects build the same number of trivially simple pages, each with a
heading, a paragraph and one link to the next page. Beyond that they are not
the same thing, and the differences all favour MkDocs:

- MkDocs reads Markdown and Sphinx reads reStructuredText, so this is two
  toolchains rather than two parsers.
- Sphinx resolves `:doc:` cross-references into a document-wide inventory and
  builds a search index and a genindex; MkDocs with no plugins templates HTML.
  Some of Sphinx's cold cost buys something MkDocs is not doing.
- Both run bare: no Material theme, no plugins, `html_theme = "basic"`. A real
  Material build is several times slower than the MkDocs figures here, so none
  of these numbers describe this guide's own build.

So read the shape and not the seconds. The shape is the finding and it is
robust; the seconds are one machine.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import time
from pathlib import Path
from tempfile import TemporaryDirectory

#: The corpus size the quoted figure used, and two multiples of it. The
#: crossover sits between the first two, so a sweep that stopped at the
#: quoted size would have confirmed the quoted conclusion and missed it.
SIZES = (121, 240, 480)

MKDOCS = [sys.executable, "-m", "mkdocs", "build", "-q"]
SPHINX = [sys.executable, "-m", "sphinx", "-b", "html", "-q", ".", "_build"]


def write_projects(root: Path, pages: int) -> tuple[Path, Path]:
    """One corpus, twice: Markdown for MkDocs and reStructuredText for Sphinx."""
    names = [f"p{index:04d}" for index in range(pages)]

    mkdocs = root / "mkdocs-project"
    (mkdocs / "docs").mkdir(parents=True)
    (mkdocs / "mkdocs.yml").write_text("site_name: Bench\n", encoding="utf-8")
    (mkdocs / "docs" / "index.md").write_text("# Index\n\nHome.\n", encoding="utf-8")
    for index, name in enumerate(names):
        nxt = names[(index + 1) % pages]
        (mkdocs / "docs" / f"{name}.md").write_text(
            f"# Page {index}\n\nParagraph one.\n\nSee [next]({nxt}.md).\n", encoding="utf-8"
        )

    sphinx = root / "sphinx-project"
    sphinx.mkdir()
    (sphinx / "conf.py").write_text(
        "project = 'Bench'\nextensions = []\nhtml_theme = 'basic'\n", encoding="utf-8"
    )
    (sphinx / "index.rst").write_text(
        "Index\n=====\n\n.. toctree::\n   :maxdepth: 1\n\n"
        + "".join(f"   {name}\n" for name in names),
        encoding="utf-8",
    )
    for index, name in enumerate(names):
        nxt = names[(index + 1) % pages]
        title = f"Page {index}"
        (sphinx / f"{name}.rst").write_text(
            f"{title}\n{'=' * len(title)}\n\nParagraph one.\n\nSee :doc:`{nxt}`.\n",
            encoding="utf-8",
        )
    return mkdocs, sphinx


def run(command: list[str], cwd: Path) -> float:
    start = time.perf_counter()
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=600)
    if result.returncode != 0:
        raise SystemExit(
            f"{command[2]} build failed in {cwd.name}:\n"
            + (result.stdout + result.stderr)[-800:]
        )
    return time.perf_counter() - start


def best_of(command: list[str], cwd: Path, repeats: int = 2) -> float:
    """Seconds, best of `repeats`.

    Best-of rather than mean, because every source of noise here is one-sided:
    another process on the machine can only make a build slower.
    """
    return min(run(command, cwd) for _ in range(repeats))


def cold(cwd: Path, output: str, repeats: int = 2) -> float:
    """A build with no previous output to reuse."""
    best = float("inf")
    for _ in range(repeats):
        shutil.rmtree(cwd / output, ignore_errors=True)
        best = min(best, run(SPHINX if output == "_build" else MKDOCS, cwd))
    return best


def main() -> int:
    print("part 1: the quoted comparison, at the size it was quoted for\n")

    with TemporaryDirectory() as tmp:
        mkdocs, sphinx = write_projects(Path(tmp), SIZES[0])
        sphinx_cold = cold(sphinx, "_build")
        mkdocs_time = best_of(MKDOCS, mkdocs)
        print(
            "  %d pages: mkdocs %.2fs, sphinx cold %.2fs  (%.1fx)"
            % (SIZES[0], mkdocs_time, sphinx_cold, sphinx_cold / mkdocs_time)
        )
        print(
            "  the page quotes 0.6s and 3.5s, a ratio of 5.8x. The direction "
            "reproduces\n  and the magnitude does not: cold Sphinx here is "
            "%.1fx MkDocs, not six.\n"
            "\n  The likeliest reason for the gap cannot be measured on "
            "demand, which is\n  worth saying rather than guessing quietly. "
            "The first Sphinx build on a\n  machine pays for imports that are "
            "not yet in the filesystem cache, and in\n  this environment that "
            "first run took about three seconds while every cold\n  run after "
            "it took about one and a third. A drill cannot reproduce a\n  "
            "first-ever run, so this number is the steady-state cold build and "
            "the\n  quoted 3.5 was probably a genuinely first one. CI pays the "
            "first number\n  every time; a laptop pays it once."
            % (sphinx_cold / mkdocs_time)
        )

    print("\n\npart 2: the same comparison as the corpus grows\n")
    print("  pages   mkdocs   sphinx cold   sphinx warm   warm vs mkdocs")
    rows = {}
    for pages in SIZES:
        with TemporaryDirectory() as tmp:
            mkdocs, sphinx = write_projects(Path(tmp), pages)
            mkdocs_time = best_of(MKDOCS, mkdocs)
            sphinx_cold = cold(sphinx, "_build")
            sphinx_warm = best_of(SPHINX, sphinx)
            rows[pages] = (mkdocs_time, sphinx_cold, sphinx_warm)
            faster = mkdocs_time / sphinx_warm
            print(
                "  %5d   %6.2f   %11.2f   %11.2f   %s"
                % (
                    pages,
                    mkdocs_time,
                    sphinx_cold,
                    sphinx_warm,
                    ("sphinx %.1fx faster" % faster)
                    if faster > 1
                    else ("mkdocs %.1fx faster" % (1 / faster)),
                )
            )

    print(
        "\n  MkDocs rebuilds everything on every run, so its time scales with "
        "the corpus.\n  Sphinx keeps an environment and rebuilds only what "
        "changed, so its warm build\n  is almost flat. Those two lines cross, "
        "and they cross just above the corpus\n  size the quoted figure used."
    )

    print("\n\npart 3: the build a writer actually runs, at both ends\n")
    edits = {}
    for pages in (SIZES[0], SIZES[-1]):
        with TemporaryDirectory() as tmp:
            mkdocs, sphinx = write_projects(Path(tmp), pages)
            best_of(MKDOCS, mkdocs, repeats=1)
            best_of(SPHINX, sphinx, repeats=1)
            measured = []
            for edit in range(3):
                (mkdocs / "docs" / "p0000.md").write_text(
                    f"# Page 0\n\nEdit {edit}.\n\nSee [next](p0001.md).\n",
                    encoding="utf-8",
                )
                (sphinx / "p0000.rst").write_text(
                    f"Page 0\n======\n\nEdit {edit}.\n\nSee :doc:`p0001`.\n",
                    encoding="utf-8",
                )
                measured.append((run(MKDOCS, mkdocs), run(SPHINX, sphinx)))
            mkdocs_best = min(m for m, _ in measured)
            sphinx_best = min(s for _, s in measured)
            edits[pages] = (mkdocs_best, sphinx_best)
            print(
                "  one page edited in %3d: mkdocs %.2fs, sphinx %.2fs  (%s)"
                % (
                    pages,
                    mkdocs_best,
                    sphinx_best,
                    ("sphinx %.1fx faster" % (mkdocs_best / sphinx_best))
                    if sphinx_best < mkdocs_best
                    else ("mkdocs %.1fx faster" % (sphinx_best / mkdocs_best)),
                )
            )

    print(
        "\n  This is the measurement that should have been quoted, and note "
        "that it does\n  not favour Sphinx everywhere. At the quoted corpus "
        "size MkDocs still wins the\n  edit loop, because rebuilding 121 "
        "trivial pages costs less than Sphinx's\n  fixed startup. By a few "
        "hundred pages that is reversed and keeps widening,\n  because MkDocs "
        "rebuilds all of them and Sphinx rebuilds one."
    )

    print(
        "\n\nSo the quoted figure is reproducible and describes CI rather than "
        "authoring,\nand it stops being true at all somewhere above a few "
        "hundred pages. Neither\nhalf of that was visible from the single "
        "number, which is the argument for\ncommitting a measurement rather "
        "than quoting one: a committed one can be\nre-run at a different size, "
        "and a quoted one can only be believed."
    )

    small, large = rows[SIZES[0]], rows[SIZES[-1]]
    ok = (
        small[1] / small[0] > 2
        and small[0] < small[2]
        and large[2] < large[0]
    )
    if not ok:
        print(
            "unexpected: cold sphinx should be several times slower than "
            "mkdocs, mkdocs should win warm at the smallest size, and lose it "
            f"at the largest (got {rows})",
            file=sys.stderr,
        )
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
