---
title: Sphinx
summary: The generator whose build fails when a symbol moves, and what that costs.
diataxis: how-to
audience: developer
concept: sphinx
tags: [dac, core]
---

# Sphinx

`core` · difficulty 3 · 6h

!!! quote "Asked for by name"
    NVIDIA: "static site generators (Sphinx, MkDocs, Docusaurus, or similar)"

**Prerequisites:** [Choosing a static site generator](static-site-generators.md), [reStructuredText](restructuredtext.md)

## What it is

A documentation generator built around an intermediate representation called
the **doctree**, which is what makes its distinguishing feature possible:
typed cross-references that resolve against a symbol table. A reference to
`pkg.widget.retry` is not a link to a URL you hoped would exist. It is a
reference to a function, and if that function is renamed, **the documentation
build fails**.

It is the strictest of the generators and the hardest to adopt, and those are
the same fact.

## Why the job asks for it

NVIDIA's documentation estate is Python and C++ tooling: Omniverse, Isaac Sim,
OpenUSD. That is Sphinx territory and has been for twenty years, because
Sphinx is the only common generator that treats API symbols as first-class
objects with their own namespaces.

The thing being tested is whether you know what it buys. Anyone can describe
Sphinx as "the Python one with RST". The useful answer is that its build is a
correctness gate on the relationship between documentation and code. The honest
version adds that `mkdocstrings` achieves the same gate for Python on MkDocs,
and that what stays distinctively Sphinx is multi-language domains and
cross-project checking through `intersphinx`.

## The golden path

Generate reference documentation from real source, then rename the function and
watch the build fail. About forty minutes.

Committed as `drills/sphinx_autodoc.py`, which runs both states in one go. It
needs `sphinx` and `myst-parser`, neither of which this guide depends on, so it
is not in the test suite's default run; the page states what it prints and the
drill is how you check that.

One thing changed when it was committed. The signature line below arrives as
`&#x2192;` rather than as a real arrow, because the extraction script strips
tags and leaves entities alone. This page used to show the arrow. That is a
trivial defect with a non-trivial consequence: a reader who follows the steps
sees output that does not match what they were promised, and has no way to tell
whether the difference matters.

**Step 1: a package and a Sphinx project**

````bash
mkdir -p sx-demo/src sx-demo/pkg && cd sx-demo
cat > pkg/widget.py <<'EOF'
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
EOF

cat > src/conf.py <<'EOF'
import os
import sys

sys.path.insert(0, os.path.abspath(".."))
project = "W"
extensions = ["sphinx.ext.autodoc", "sphinx.ext.napoleon", "myst_parser"]
nitpicky = True
EOF
````

Three extensions and `nitpicky = True`. `autodoc` reads the source,
`napoleon` understands Google-style docstrings, `myst_parser` lets the pages be
Markdown, and `nitpicky` turns every unresolved reference into a warning.

**Step 2: a page that pulls the reference out of the code**

````bash
cat > src/index.md <<'EOF'
# API

```{eval-rst}
.. automodule:: pkg.widget
   :members:
```

See {py:func}`pkg.widget.retry` and {py:class}`pkg.widget.Client`.
EOF

sphinx-build -q -W -b html src out
echo "exit=$?"
````

```
exit=0
```

Check what it produced:

```bash
python3 - <<'PY'
import re
from pathlib import Path
html = Path("out/index.html").read_text()
plain = re.sub("<[^>]+>", "", html)
print(re.search(r"retry.{0,70}", plain).group(0))
for s in ("backoff", "Multiplier", "connect", "Parameters", "Returns"):
    print(f"  {s:12} {s in html}")
PY
```

```
retry(times: int = 5, backoff: float = 1.5) &#x2192; int¶
  backoff      True
  Multiplier   True
  connect      True
  Parameters   True
  Returns      True
```

The full typed signature, the parameter descriptions, and the return
documentation, all pulled from the source. Nothing about the signature was
written by hand, so nothing about it can be out of date.

**Step 3: the demonstration**

Rename the function in the code and leave the documentation untouched, which is
precisely what happens in a real refactor:

```bash
sed -i 's/^def retry(/def attempt(/' pkg/widget.py
sphinx-build -q -W -b html src out2
echo "exit=$?"
```

```
WARNING: py:func reference target not found: pkg.widget.retry [ref.func]
exit=1
```

**The documentation build failed because a function was renamed in the code.**
An ordinary Markdown link cannot do this. `[retry](api.md#retry)` resolves
against a heading slug, so after the rename the heading is `attempt`, the
anchor dies, and [MkDocs ships it](link-checking.md) even in strict mode.

**But Sphinx is not alone in this, and it would be wrong to say so.** MkDocs
with `mkdocstrings` has its own cross-reference syntax, `[text][symbol]`, and
those *are* resolved against the collected objects: a reference to a renamed
symbol produces `Could not find cross-reference target`, which `--strict` turns
into a failed build. The comparison is drawn properly on
[generated API reference](api-reference-generation.md).

What remains genuinely Sphinx's is the breadth: multiple language domains in
one corpus, and `intersphinx` extending the same checking across project
boundaries. The rename demonstration is worth forty minutes either way, because
it is the mechanism both approaches depend on.

**Step 4: what the strictness costs, measured**

`drills/generator_build.py` builds an identical corpus under both generators,
bare, across three sizes:

```
  pages   mkdocs   sphinx cold   sphinx warm   warm vs mkdocs
    121     0.50          1.57          0.59   mkdocs 1.2x faster
    240     0.91          2.36          0.58   sphinx 1.6x faster
    480     1.94          4.10          0.65   sphinx 3.0x faster
```

One machine, one run; the shape is the claim and not the seconds.

The doctree that makes step 3 possible is also what makes incremental rebuilds
possible, so **MkDocs rebuilds everything every time and Sphinx rebuilds what
changed.** MkDocs' time therefore scales with the corpus and Sphinx's warm
build is nearly flat, and the two cross just above a hundred and twenty pages.

This page used to quote a single row of that table, 0.58 against 3.52 seconds,
and conclude "six times slower cold". The direction survives and the magnitude
does not: cold Sphinx measures about three times MkDocs in steady state here,
and the 3.52 was most likely a first-ever build paying for imports that were
not yet in the filesystem cache. CI pays that first number on every run and a
laptop pays it once, which is a distinction a single figure cannot carry.

The authoring loop, which is what the cost actually feels like:

```
  one page edited in 121: mkdocs 0.53s, sphinx 0.59s  (mkdocs 1.1x faster)
  one page edited in 480: mkdocs 1.78s, sphinx 0.70s  (sphinx 2.5x faster)
```

So "often the faster of the two in day-to-day authoring" was right, and only
past a certain size. Below it MkDocs still wins, because rebuilding a hundred
trivial pages costs less than Sphinx's fixed startup.

**What you built.** Reference documentation that cannot drift from its
signatures, and a build that fails when code and docs disagree.

## Reference

### What `-W` plus `nitpicky` catches

| Defect | Caught |
|---|---|
| Link to a missing page | Yes |
| Link to a missing heading anchor | Yes |
| Page in no `toctree` | Yes, `toc.not_included` |
| Reference to a renamed symbol | Yes, `ref.func` |
| Duplicate label | Yes |
| A type annotation that does not resolve | Yes, and this is the noisy one |

The last row is why `nitpicky` is divisive. It flags every unresolvable type,
including standard-library and third-party types Sphinx cannot find, so
adopting it on an existing project means a session with `nitpick_ignore`.
Worth it, but do not turn it on an hour before a release.

### The extensions that matter

| Extension | Does |
|---|---|
| `sphinx.ext.autodoc` | Pull docstrings and signatures from source |
| `sphinx.ext.napoleon` | Understand Google and NumPy docstring styles |
| `sphinx.ext.intersphinx` | Cross-reference *other* projects' symbols |
| `sphinx.ext.viewcode` | Link reference entries to highlighted source |
| `myst_parser` | Author pages in Markdown |
| `sphinx.ext.doctest` | Run the examples in your docs; see [doctests](doctests.md) |
| `sphinx-autobuild` | Live reload while authoring |

`intersphinx` deserves attention. It lets a reference to `str` or to another
library's class resolve to that project's documentation, which means
cross-project references are also checked. Nothing in the Markdown world has an
equivalent.

### Domains, which is the concept under the feature

A domain is a namespace of object types and roles. `py:func`, `cpp:class`,
`js:method` are all domain-qualified, so Sphinx can tell a Python `Client` from
a C++ `Client` and check each against the right symbol table. On a codebase
with multiple languages, this is the feature that makes a single documentation
set coherent.

### What it costs

| Cost | Detail |
|---|---|
| `conf.py` is a Python program | Powerful, and a configuration file that can have bugs |
| Learning curve | Directives, roles and `toctree` before the first page |
| Error vocabulary | Messages are in docutils and Sphinx terms, not plain English |
| Theme work is harder | Fewer good themes, and customising them is more involved |
| Cold builds are slower | Measured above; mitigated by incremental rebuilds |
| `nitpicky` adoption | A real session of `nitpick_ignore` on any existing project |

### Should a new project use it

| Yes | No |
|---|---|
| The deliverable includes API reference for a library | The corpus is conceptual and narrative |
| The code is Python, C++ or multi-language | The site needs interactive components |
| Symbols are renamed often enough to hurt | The team has no Python experience |
| You need cross-project references | You need a site this afternoon |

## How to talk about it

**Lead with the rename.** "Sphinx's build fails when a function referenced in
the docs is renamed in the code, because references are typed and resolve
against a symbol table rather than a URL. That is not available in any Markdown
generator, and on an API corpus it is the difference between documentation that
drifts and documentation that cannot."

**The follow-up is whether that means RST**, and the answer is no: `myst_parser`
lets contributors write Markdown while keeping domains, `toctree` and typed
references. Knowing that is what separates a current answer from a 2015 one.

**The tradeoff to volunteer.** The doctree buys correctness and costs
approachability. `conf.py` is a Python program that can have bugs, errors are
reported in docutils vocabulary, and `nitpicky` on an existing project produces
a wall of unresolvable standard-library types before it produces value. Sphinx
is the right answer for a library and the wrong answer for a dozen conceptual
pages.

**One sharper point.** `intersphinx` is the underrated piece. It extends
reference checking across project boundaries, so a link to another library's
class is verified rather than hoped for. In an ecosystem of related packages,
that turns a set of separate documentation sites into something closer to one
correct corpus, and almost nobody mentions it.

## How to prove it

**The artifact.** A Sphinx project with `-W` in CI, `autodoc` generating
reference from source, and ideally `nitpicky` on.

**Three things to do, in order:**

1. Run the golden path. Step 3 is the whole point, and seeing your own build
   fail on a rename is more persuasive than any description of it.
2. Turn on `nitpicky` in a project you have and count the warnings. That count
   is the honest size of its reference debt.
3. Add `intersphinx` pointing at the Python standard library and see how many
   previously unresolved types start resolving.

**What makes it credible rather than decorative.** Neither of this guide's
repositories is *built* with Sphinx, which the
[demonstrated](../demonstrated.md) page records, and that is a real gap for a
role at a company whose documentation is Sphinx-shaped. Running it in a drill
is not the same as owning a Sphinx corpus: nothing here involves a large
`conf.py`, a custom extension, a theme fork, or `intersphinx` across teams,
which is where the actual work is.

What is committed is the mechanism. `drills/sphinx_autodoc.py` renames a
function and the build fails with `py:func reference target not found` and exit
1, against the same defect MkDocs publishes, and
`drills/generator_build.py` measures what the doctree behind that costs and
what it buys back incrementally. Both corrected this page: one fixed a quoted
output line, the other replaced a six-times claim with a comparison that
inverts.

## Related

- [reStructuredText](restructuredtext.md), and which half of it is really Sphinx
- [Generated API reference](api-reference-generation.md), what autodoc is an instance of
- [Choosing a static site generator](static-site-generators.md), the comparison
- [Doctests](doctests.md), which `sphinx.ext.doctest` runs for you
