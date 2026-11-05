#!/usr/bin/env python3
"""Reference documentation that fails the build when the code is renamed.

    python3 drills/sphinx_autodoc.py

Needs `sphinx` and `myst-parser`, neither of which this guide depends on.

Reproduces the `sphinx` page's golden path: autodoc pulls a typed signature and
its parameter documentation out of real source, then the function is renamed
and `-W` with `nitpicky = True` turns the now-unresolvable cross-reference into
a failed build.

That is the mechanism worth forty minutes, and the page is careful to say it is
not unique to Sphinx: MkDocs with `mkdocstrings` resolves `[text][symbol]`
against collected objects and fails the same way under `--strict`. What is
Sphinx's own is the breadth, several language domains in one corpus and
`intersphinx` extending the same check across project boundaries.

Everything here runs in a temporary directory. The package, the config and the
page are the page's own heredocs, verbatim, and a test asserts they stay that
way.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

#: The page's step-1 and step-2 heredocs, verbatim.
WIDGET = '''\
"""Widget client."""


def retry(times: int = 5, backoff: float = 1.5) -> int:
    """Retry an operation.

    Args:
        times: How many attempts.
        backoff: Multiplier between attempts.

    Returns:
        The number of attempts made.
    """
    return times


class Client:
    """A client."""

    def connect(self, url: str) -> bool:
        """Open a connection."""
        return True
'''

CONF = '''\
import os
import sys

sys.path.insert(0, os.path.abspath(".."))
project = "W"
extensions = ["sphinx.ext.autodoc", "sphinx.ext.napoleon", "myst_parser"]
nitpicky = True
'''

INDEX = """\
# API

```{eval-rst}
.. automodule:: pkg.widget
   :members:
```

See {py:func}`pkg.widget.retry` and {py:class}`pkg.widget.Client`.
"""

#: Strings the built page must contain for the extraction to have worked.
EXTRACTED = ("backoff", "Multiplier", "connect", "Parameters", "Returns")


def build(root: Path, out: str) -> tuple[int, str]:
    result = subprocess.run(
        [sys.executable, "-m", "sphinx", "-q", "-W", "-b", "html", "src", out],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=300,
    )
    return result.returncode, (result.stdout + result.stderr).strip()


def main() -> int:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "pkg").mkdir()
        (root / "src").mkdir()
        (root / "pkg" / "widget.py").write_text(WIDGET, encoding="utf-8")
        (root / "src" / "conf.py").write_text(CONF, encoding="utf-8")
        (root / "src" / "index.md").write_text(INDEX, encoding="utf-8")

        print("step 2: a page that pulls the reference out of the code\n")
        code, output = build(root, "out")
        if output:
            print(output)
        print(f"exit={code}")

        html = (root / "out" / "index.html").read_text(encoding="utf-8")
        # Tags are stripped and entities are not, which is why the arrow below
        # arrives as `&#x2192;`. The page used to quote it as a real arrow,
        # which is a small thing and exactly the kind of small thing that
        # means a reader's output does not match what they were promised.
        plain = re.sub("<[^>]+>", "", html)
        match = re.search(r"retry.{0,70}", plain)
        print()
        print(match.group(0) if match else "(retry not found)")
        for needle in EXTRACTED:
            print(f"  {needle:12} {needle in html}")

        print(
            "\nThe full typed signature, the parameter descriptions and the "
            "return\ndocumentation, all pulled from the source. Nothing about "
            "the signature was\nwritten by hand, so nothing about it can be "
            "out of date."
        )

        print("\n\nstep 3: the demonstration\n")
        renamed = WIDGET.replace("def retry(", "def attempt(")
        (root / "pkg" / "widget.py").write_text(renamed, encoding="utf-8")
        after_code, after_output = build(root, "out2")
        # The warning is prefixed with the absolute path of a temporary
        # directory, which would make this drill's output different on every
        # run. Only the part a reader needs is printed.
        for line in after_output.splitlines():
            print(line.split("WARNING:", 1)[-1].strip() if "WARNING:" in line else line)
        print(f"exit={after_code}")

        print(
            "\nThe documentation build failed because a function was renamed "
            "in the code,\nand nothing in the documentation was touched. An "
            "ordinary Markdown link\ncannot do this: `[retry](api.md#retry)` "
            "resolves against a heading slug, so\nafter the rename the anchor "
            "simply dies and the page ships."
        )

    ok = code == 0 and after_code == 1 and all(n in html for n in EXTRACTED)
    if not ok:
        print(
            f"unexpected: the clean build should pass and the renamed one "
            f"should fail (got {code} then {after_code})",
            file=sys.stderr,
        )
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
