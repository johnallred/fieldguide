---
title: Generated API reference
summary: Pulling signatures from source so they cannot drift, and which half of the drift that actually fixes.
diataxis: how-to
audience: developer
concept: api-reference-generation
tags: [dac, core]
---

# Generated API reference

`core` · difficulty 2 · 4h

!!! quote "Asked for by name"
    Intel: "Write and maintain reference documentation, tutorials, and sample walkthroughs that assume no prior context"

**Prerequisites:** [Docs-as-code](docs-as-code.md)

**Leads to:** [OpenAPI and REST reference](openapi.md)

## What it is

Building the reference layer of your documentation from the source code rather
than writing it by hand. A tool reads signatures, type annotations and
docstrings and emits pages, so the published signature is the real one by
construction.

The part worth understanding precisely is which drift this removes and which it
does not. Generation makes signatures correct automatically. It does nothing
for prose that describes behaviour, and it does nothing for the links *into*
the reference unless you use the right reference syntax.

## Why the job asks for it

Intel asks for reference documentation that assumes no prior context, alongside
tutorials and sample walkthroughs. Reference is the layer where hand-authoring
fails first and worst: a corpus with two hundred functions cannot be
hand-maintained through a refactor, and the failure is silent.

It is also the layer readers trust most. A generated signature carries an
implicit promise of being authoritative, which means a stale one does more
damage than a stale paragraph of prose. Automating it is less about writer
effort than about where the corpus is allowed to lie.

## The golden path

Generate reference in two toolchains, then rename the function and find out
exactly what each one catches. About forty minutes.

**Step 1: a package worth documenting**

````bash
mkdir -p apiref/pkg apiref/docs && cd apiref
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
EOF
touch pkg/__init__.py
````

Google-style docstring, type annotations, a default value. Everything a
generator needs.

**Step 2: generate it with mkdocstrings**

````bash
pip install --quiet mkdocs mkdocstrings mkdocstrings-python

cat > mkdocs.yml <<'EOF'
site_name: API
plugins:
  - mkdocstrings:
      handlers:
        python:
          paths: [.]
EOF

cat > docs/index.md <<'EOF'
# API

::: pkg.widget.retry
EOF

python3 -m mkdocs build --strict && echo "exit=$?"
````

The output contains the signature, pulled from the code:

```
retry(times: int = 5, backoff: float = 1.5) -> int:
```

plus the parameter descriptions and the return documentation, parsed out of the
docstring sections. The same package through
[Sphinx](sphinx.md) with `autodoc` and `napoleon` produces the equivalent:

```
retry(times: int = 5, backoff: float = 1.5) → int
```

Both read the real signature. Neither can publish a stale one.

**Step 3: rename the function and see what breaks**

```bash
sed -i 's/^def retry(/def attempt(/' pkg/widget.py
python3 -m mkdocs build --strict
```

```
ERROR - mkdocstrings: pkg.widget.retry could not be found
ERROR - Could not collect 'pkg.widget.retry'
exit=1
```

The directive fails hard. Sphinx behaves the same way. **The generation side is
safe in both:** point a generator at a symbol that no longer exists and the
build stops.

**Step 4: the half that is not safe**

Fix the directive to point at `attempt`, and leave behind an ordinary Markdown
link to the old anchor:

````bash
cat > docs/index.md <<'EOF'
# API

::: pkg.widget.attempt

See [retry](#pkgwidgetretry).
EOF
python3 -m mkdocs build --strict; echo "exit=$?"
````

```
INFO - Doc file 'index.md' contains a link '#pkgwidgetretry', but there is no
       such anchor on this page.
exit=0
```

Exit 0. The link is dead twice over, because the real anchor mkdocstrings emits
is `pkg.widget.retry` with the dots, and that symbol no longer exists anyway.
MkDocs logs `INFO` and publishes it, exactly as on the
[link checking](link-checking.md) page.

So generating the reference did not protect the references *into* it.

**Step 5: use the reference syntax, which is checked**

mkdocstrings ships `autorefs`, where `[text][symbol]` resolves against the
collected objects rather than against a heading slug:

````bash
cat > docs/index.md <<'EOF'
# API

::: pkg.widget.attempt

Autorefs style: [attempt][pkg.widget.attempt] and a dead one [gone][pkg.widget.retry].
EOF
python3 -m mkdocs build --strict; echo "exit=$?"
````

```
WARNING - mkdocs_autorefs: index.md: Could not find cross-reference target
          'pkg.widget.retry'
Aborted with 1 warnings in strict mode!
exit=1
```

Caught, and the good one resolved to `href="#pkg.widget.attempt"`. The dead
one was left as literal `[gone][pkg.widget.retry]` in the output, which is the
usual Markdown failure mode and the reason the warning matters.

**What you learned.** Generation fixes signatures. Cross-references into the
reference are a separate problem with a separate fix, and the fix is to use the
symbol-reference syntax instead of hand-written anchors. Two different gates,
and most teams have only the first.

## Reference

### What generation fixes, and what it does not

| Drift | Fixed by generation |
|---|---|
| A parameter renamed | Yes |
| A type annotation changed | Yes |
| A default value changed | Yes |
| A function removed | Yes, the build fails |
| A link to a removed symbol | **No**, unless you use symbol references |
| Prose describing behaviour | No |
| An example that no longer runs | No; see [sample validation](code-sample-validation.md) |
| Which functions deserve a tutorial | No |

### Toolchains

| Tool | Reads | Checks symbol references |
|---|---|---|
| Sphinx `autodoc` plus `napoleon` | Python docstrings, annotations | Yes, `py:func` and the domains |
| `mkdocstrings` plus `mkdocstrings-python` | The same | Yes, `[text][symbol]` autorefs |
| `sphinx.ext.intersphinx` | Other projects' inventories | Yes, across projects |
| `typedoc` | TypeScript | Yes, within the project |
| `javadoc`, `doxygen` | Java, C++ | Within the project |
| OpenAPI generators | A spec, not code | See [OpenAPI](openapi.md) |

The practical upshot: you do not need Sphinx to get checked symbol references
for Python. You need a tool that collects symbols, and either of the first two
qualifies. What stays distinctively Sphinx is several language domains in one
corpus plus `intersphinx`.

### Docstring styles

| Style | Looks like | Needs |
|---|---|---|
| Google | `Args:` and `Returns:` sections | `napoleon`, or mkdocstrings default |
| NumPy | Underlined sections | `napoleon` |
| reStructuredText | `:param x:` | Nothing extra in Sphinx |
| Plain prose | No structure | Nothing, and you get no parameter table |

Pick one and enforce it with a [linter](custom-linters.md). A corpus with three
styles renders inconsistently and the parameter tables silently stop appearing
on the pages that drifted.

### Where generated reference stops being enough

Generated reference tells a reader what a function's signature is. It does not
tell them which function to call, in what order, or why. That is what
[golden paths](golden-paths.md) and [tutorial design](tutorial-design.md) are for, and a
corpus that is only generated reference is the most common failure mode in
developer documentation: complete, accurate, and unusable by a newcomer.

Reference is necessary and it is the easy half.

## How to talk about it

**Lead with the split.** "Generating reference from source means the published
signature is the real one by construction, so a rename fails the build instead
of shipping. What it does not fix is the links *into* the reference: a
hand-written anchor to a renamed symbol is a dead link that MkDocs publishes.
So I use the symbol-reference syntax, which is resolved against the collected
objects."

**The follow-up is often whether you need Sphinx for this**, and the answer is
no for a Python-only corpus. `mkdocstrings` gives you generation and checked
`[text][symbol]` references on MkDocs. Sphinx wins when you have several
language domains or want `intersphinx` checking across projects.

**The tradeoff to volunteer.** Generated reference is only as good as the
docstrings, and generation creates pressure to write docstrings for the tool
rather than for the reader. You end up with two hundred pages that are
technically complete and tell nobody how to accomplish anything. The mitigation
is to treat reference as the floor and spend the real effort on golden paths,
which is a staffing argument as much as a tooling one.

**One sharper point.** The anchor format is not what you would guess.
mkdocstrings emits `id="pkg.widget.retry"`, dots included, so hand-written
links to generated pages are usually wrong on the first attempt and usually
ship anyway, because MkDocs treats a dead anchor as `INFO`. That is the
specific, checkable reason to use the reference syntax rather than a preference
for it.

## How to prove it

**The artifact.** A repository where reference is generated and where a renamed
symbol fails the build, plus the use of symbol references rather than anchors.

**Three things to do, in order:**

1. Run the golden path. Steps 3 and 4 together are the lesson: the directive
   fails, the link does not.
2. Grep your own docs for hand-written links into generated reference pages.
   Each one is an unchecked reference. If you find none, check whether
   anything links into the reference at all: a generated section nobody links
   to is a different problem with the same symptom.
3. Convert the five most important of those to `[text][symbol]` form and turn
   on `--strict`. Whatever fails was already broken.

**What makes it credible rather than decorative.** `docpack` generates its
reference with `mkdocstrings` and runs `--doctest-modules` across the package,
so the docstrings that feed the reference are themselves executed. The
combination is the thing to point at: generation keeps the signature honest,
and doctests keep the examples in it honest, which are two different kinds of
lie.

## Related

- [OpenAPI and REST reference](openapi.md), the same idea for an HTTP surface
- [Sphinx](sphinx.md), one of the two toolchains compared here
- [Doctests](doctests.md), which verify the examples inside the docstrings
- [Golden paths](golden-paths.md), the half generated reference cannot provide
