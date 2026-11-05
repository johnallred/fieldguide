#!/usr/bin/env python3
"""Copy-paste drifts, line-range transclusion fails worse, named anchors hold.

    python3 drills/walkthrough_transclusion.py

Reproduces the five states the `sample-walkthroughs` page walks through, with a
real MkDocs build behind the three that render:

  1 a copied block that has drifted from the sample, caught by a string check
  2 the same block transcluded by line range, so drift becomes impossible
  3 the file edited, and the page following it automatically
  4 two lines inserted near the top, and the transclusion silently lying
  5 a named anchor, which survives the insertion

State 4 is the reason this exists. The page renders `import click` under the
heading "the retry count", renders the second block empty, and the build exits
zero. Nothing in the output is wrong by its own standards: the transclusion
asked for lines 4 to 4 and got them. A check that compares a quoted block to
its source cannot help, because nothing is quoted any more.

Requires `mkdocs` and `pymdownx` (both in the guide's own dependencies). The
sample is never executed, so `click` need not be installed.
"""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

#: The page's step-1 heredocs, verbatim. A test asserts these still match.
SAMPLE = '''\
"""A minimal sync tool."""
import click

RETRIES = 5


@click.command()
@click.option("--dry-run", is_flag=True, help="Report without writing.")
def main(dry_run):
    """Sync records."""
    mode = "would sync" if dry_run else "synced"
    print(f"{mode} 0 records (retries={RETRIES})")


if __name__ == "__main__":
    main()
'''

WALKTHROUGH = """\
# Walkthrough: the sync tool

The retry count is a module constant:

```python
RETRIES = 3
```

The command takes one flag:

```python
@click.option("--dry-run", is_flag=True, help="Report without writing.")
```
"""

MKDOCS = """\
site_name: W
markdown_extensions:
  - pymdownx.snippets:
      base_path: ["."]
      check_paths: true
  - pymdownx.superfences
"""

#: The page shows only the first of these two blocks. Both are needed for
#: state 4 to report what the page says it reports, since its second line is
#: about the flag block.
BY_LINE_RANGE = """\
# Walkthrough: the sync tool

The retry count is a module constant:

```python
--8<-- "samples/sync.py:4:4"
```

The command takes one flag:

```python
--8<-- "samples/sync.py:8:8"
```
"""

BY_ANCHOR = """\
# Walkthrough: the sync tool

The retry count is a module constant:

```python
--8<-- "samples/sync.py:retries"
```

The command takes one flag:

```python
--8<-- "samples/sync.py:flag"
```
"""


def check_quoted_blocks(walkthrough: str, sample: str) -> int:
    """State 1: the page's step-2 check, completed.

    Twelve lines, and the minimum a copy-paste walkthrough needs: the failure
    it catches is invisible to a reader, because the prose is coherent and the
    code is plausible.
    """
    blocks = re.findall(r"^```python\n(.*?)^```", walkthrough, re.S | re.M)
    problems = []
    for number, block in enumerate(blocks, 1):
        snippet = block.rstrip("\n")
        if snippet not in sample:
            problems.append(
                f"block {number}: not found in samples/sync.py: "
                f"{snippet.splitlines()[0]!r}"
            )
    for problem in problems:
        print(f"WALK  {problem}")
    print(
        f"{'FAIL' if problems else 'ok'}: {len(blocks)} quoted block(s), "
        f"{len(problems)} drifted"
    )
    return len(problems)


def rendered(root: Path) -> list[str]:
    """Build the site and return the text of each rendered code block."""
    build = subprocess.run(
        [sys.executable, "-m", "mkdocs", "build", "-q"],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=180,
    )
    if build.returncode != 0:
        print(build.stdout + build.stderr, file=sys.stderr)
        raise SystemExit("mkdocs build failed")
    html = (root / "site" / "index.html").read_text(encoding="utf-8")
    return [
        re.sub(r"<[^>]+>", "", block).strip()
        for block in re.findall(r"<code[^>]*>(.*?)</code>", html, re.S)
    ]


def show(blocks: list[str]) -> None:
    labels = ('"the retry count":', '"the command flag":')
    for label, text in zip(labels, blocks + ["", ""]):
        first = text.splitlines()[0] if text else "(empty)"
        print(f"{'rendered for ' + label:<32} {first}")


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "samples").mkdir()
        (root / "docs").mkdir()
        sample = root / "samples" / "sync.py"
        sample.write_text(SAMPLE, encoding="utf-8")
        (root / "mkdocs.yml").write_text(MKDOCS, encoding="utf-8")

        print("step 2: check every quoted block against the file\n")
        drifted = check_quoted_blocks(WALKTHROUGH, SAMPLE)

        print("\nstep 3: remove the possibility instead of checking for it\n")
        (root / "docs" / "index.md").write_text(BY_LINE_RANGE, encoding="utf-8")
        print("rendered: ", rendered(root)[0])

        print("\nchange the file and rebuild:\n")
        sample.write_text(SAMPLE.replace("RETRIES = 5", "RETRIES = 7"), encoding="utf-8")
        print("rendered: ", rendered(root)[0])

        print("\nstep 4: break the fix\n")
        lines = sample.read_text(encoding="utf-8").splitlines(keepends=True)
        lines.insert(1, "\nfrom __future__ import annotations\n")
        sample.write_text("".join(lines), encoding="utf-8")
        broken = rendered(root)
        show(broken)

        print("\nstep 5: anchor by name\n")
        anchored = sample.read_text(encoding="utf-8")
        anchored = anchored.replace(
            "RETRIES = 7",
            "# --8<-- [start:retries]\nRETRIES = 7\n# --8<-- [end:retries]",
        ).replace(
            '@click.option("--dry-run", is_flag=True, help="Report without writing.")',
            "# --8<-- [start:flag]\n"
            '@click.option("--dry-run", is_flag=True, help="Report without writing.")\n'
            "# --8<-- [end:flag]",
        )
        sample.write_text(anchored, encoding="utf-8")
        (root / "docs" / "index.md").write_text(BY_ANCHOR, encoding="utf-8")
        fixed = rendered(root)
        print("rendered: ", fixed[0])

    # The argument is that state 4 is quieter than state 1, so assert exactly
    # that: one caught drift, then a wrong render nothing complained about,
    # then a correct render after anchoring.
    ok = (
        drifted == 1
        and broken[0] == "import click"
        and broken[1] == ""
        and fixed[0] == "RETRIES = 7"
    )
    if not ok:
        print(
            "\nunexpected: the line-range transclusion no longer fails silently "
            f"(got {broken!r})",
            file=sys.stderr,
        )
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
