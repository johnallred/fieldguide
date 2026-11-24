#!/usr/bin/env python3
"""Docusaurus against MkDocs on the same Markdown corpus, cold and warm.

    DOCUSAURUS_HOME=/path/to/install python3 drills/docusaurus_build.py

Needs `mkdocs`, Node 20 or later, and a directory where
`npm install @docusaurus/core@3 @docusaurus/preset-classic@3 react react-dom`
has been run; point DOCUSAURUS_HOME at it. Takes several minutes.

The static-site-generators page used to say Docusaurus was left out of the
comparison because measuring it needed an npm install. That is a reason to do
the install, not a reason to leave a claim unmeasured, so this drill does it.

Unlike `generator_build.py`, both sides here read the *same* Markdown files,
so the toolchain is the only variable. What still differs, and favours MkDocs:

- Docusaurus compiles every page to a React component, bundles client and
  server JavaScript with webpack, and pre-renders each route. Bare MkDocs
  templates HTML. Some of the cost buys a single-page app MkDocs does not make.
- Both run close to bare: MkDocs with no theme options or plugins, Docusaurus
  with only the docs plugin and the classic theme it cannot build without.

"Cold" deletes every cache Docusaurus keeps (`build`, `.docusaurus` and the
webpack cache in `node_modules/.cache`), which is what a fresh CI container
pays. "Warm" is a second build with those caches in place, which is what a
writer pays. MkDocs has no cache, so it has one number.

Read the shape and not the seconds; the seconds are one machine.

What it found, on MkDocs 1.6.1 and Docusaurus 3.10.2 (the concept page has the
table): Docusaurus is mostly a fixed cost, about 45 seconds cold and 6 warm
whatever the size, while MkDocs grows faster than linearly because the default
theme writes the whole nav into every page. The warm gap closes from 15x at
121 pages to 3x at 960 and does not cross in that range.

Not run in CI: the install is 1,276 packages and a 960-page run takes most of
three minutes, and its verdict is a timing, which the gates do not
assert for the reason given beside `generator_build.py` in gates.yml.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from tempfile import TemporaryDirectory

SIZES = (121, 240, 480)

MKDOCS = [sys.executable, "-m", "mkdocs", "build", "-q"]

CONFIG = """\
module.exports = {
  title: 'Bench',
  url: 'https://example.com',
  baseUrl: '/',
  onBrokenLinks: 'throw',
  presets: [['classic', {
    docs: { routeBasePath: '/', sidebarPath: false },
    blog: false,
    pages: false,
    theme: {},
  }]],
};
"""


def install_dir() -> Path:
    home = os.environ.get("DOCUSAURUS_HOME")
    if not home or not (Path(home) / "node_modules" / ".bin" / "docusaurus").exists():
        raise SystemExit(
            "set DOCUSAURUS_HOME to a directory where @docusaurus/core and "
            "@docusaurus/preset-classic are installed"
        )
    return Path(home)


def write_corpus(docs: Path, pages: int) -> None:
    names = [f"p{index:04d}" for index in range(pages)]
    docs.mkdir(parents=True)
    (docs / "index.md").write_text("# Index\n\nHome.\n", encoding="utf-8")
    for index, name in enumerate(names):
        nxt = names[(index + 1) % pages]
        (docs / f"{name}.md").write_text(
            f"# Page {index}\n\nParagraph one.\n\nSee [next]({nxt}.md).\n",
            encoding="utf-8",
        )


def write_projects(root: Path, pages: int, home: Path) -> tuple[Path, Path]:
    mkdocs = root / "mkdocs-project"
    write_corpus(mkdocs / "docs", pages)
    (mkdocs / "mkdocs.yml").write_text("site_name: Bench\n", encoding="utf-8")

    docusaurus = root / "docusaurus-project"
    write_corpus(docusaurus / "docs", pages)
    (docusaurus / "docusaurus.config.js").write_text(CONFIG, encoding="utf-8")
    (docusaurus / "package.json").write_text('{"private": true}\n', encoding="utf-8")
    (docusaurus / "node_modules").symlink_to(home / "node_modules")
    return mkdocs, docusaurus


def run(command: list[str], cwd: Path) -> float:
    start = time.perf_counter()
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=900)
    if result.returncode != 0:
        raise SystemExit(
            f"{command[0]} build failed in {cwd.name}:\n"
            + (result.stdout + result.stderr)[-1200:]
        )
    return time.perf_counter() - start


def docusaurus_command(home: Path) -> list[str]:
    return [str(home / "node_modules" / ".bin" / "docusaurus"), "build", "--no-minify"]


def clear_caches(project: Path, home: Path) -> None:
    for path in (project / "build", project / ".docusaurus", home / "node_modules" / ".cache"):
        shutil.rmtree(path, ignore_errors=True)


#: Builds per measurement, best taken. Two by default; DRILL_REPEATS=1 halves
#: the run time at the cost of letting one noisy build through.
REPEATS = int(os.environ.get("DRILL_REPEATS", "2"))


def measure(pages: int, home: Path) -> tuple[float, float, float]:
    """MkDocs, Docusaurus cold and Docusaurus warm, each the best of REPEATS."""
    with TemporaryDirectory() as tmp:
        mkdocs, docusaurus = write_projects(Path(tmp), pages, home)
        command = docusaurus_command(home)
        mkdocs_time = min(run(MKDOCS, mkdocs) for _ in range(REPEATS))
        cold = float("inf")
        for _ in range(REPEATS):
            clear_caches(docusaurus, home)
            cold = min(cold, run(command, docusaurus))
        warm = min(run(command, docusaurus) for _ in range(REPEATS))
        built = len(list((docusaurus / "build").rglob("index.html")))
        if built < pages:
            raise SystemExit(f"docusaurus built {built} pages, expected {pages}")
        clear_caches(docusaurus, home)
        return mkdocs_time, cold, warm


def main() -> int:
    home = install_dir()
    sizes = [int(arg) for arg in sys.argv[1:]] or list(SIZES)
    print("  pages   mkdocs   docusaurus cold   docusaurus warm   cold/mkdocs   warm/mkdocs")
    rows = {}
    for pages in sizes:
        mkdocs_time, cold, warm = measure(pages, home)
        rows[pages] = (mkdocs_time, cold, warm)
        print(
            "  %5d   %6.2f   %15.2f   %15.2f   %10.0fx   %10.1fx"
            % (pages, mkdocs_time, cold, warm, cold / mkdocs_time, warm / mkdocs_time)
        )
    slower_everywhere = all(warm > mkdocs for mkdocs, _, warm in rows.values())
    print(
        "\n  Docusaurus warm is slower than MkDocs at every size measured: %s."
        % ("yes" if slower_everywhere else "no, there is a crossover")
    )
    if len(rows) > 1:
        small, large = min(rows), max(rows)
        print(
            "  From %d to %d pages (x%.1f): MkDocs x%.1f, Docusaurus cold x%.1f, warm x%.1f."
            % (
                small,
                large,
                large / small,
                rows[large][0] / rows[small][0],
                rows[large][1] / rows[small][1],
                rows[large][2] / rows[small][2],
            )
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
