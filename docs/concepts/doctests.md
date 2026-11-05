---
title: Doctests and executable docstrings
summary: Making the example in a docstring run, and measuring the examples that are not there.
diataxis: how-to
audience: developer
concept: doctests
tags: [qa, supporting]
---

# Doctests and executable docstrings

`supporting` · difficulty 2 · 2h

!!! quote "Asked for by name"
    NVIDIA: "Content quality automation you've built, such as Vale or custom linters, doc test harnesses, or freshness monitoring"

**Prerequisites:** [Code-sample validation](code-sample-validation.md)

## What it is

An example written inside a docstring, in the form of an interactive session,
that a test runner executes and checks. The example that appears in your
[generated API reference](api-reference-generation.md) is the same text that
has to pass CI, so the reference cannot drift from the code it documents.

It is the cheapest form of [code-sample validation](code-sample-validation.md),
because the sample and the implementation are in the same file and cannot be
edited separately.

## Why the job asks for it

NVIDIA asks for doc test harnesses. Doctests are the version of that which
costs nothing to adopt: one flag in `pyproject.toml` and every docstring
example is executed on every run.

The specific decay they prevent is the worst kind, because it is invisible. A
function's behaviour changes, the docstring example still *looks* plausible,
and the generated reference publishes a wrong answer with the authority of
auto-generated documentation. Readers trust generated reference material more
than hand-written prose, which makes a stale example in it more damaging.

They also change how people write docstrings. An example that must execute
cannot be hand-waved, which tends to produce more concrete, more useful
documentation than one that only has to look reasonable.

## The golden path

Adopt doctests, hit the trap everyone hits, then measure the examples you do
not have. About twenty-five minutes.

**Step 1: a module with examples**

````bash
mkdir -p doctest-demo && cd doctest-demo
cat > money.py <<'EOF'
"""Money helpers."""


def split(total, ways):
    """Split a total into equal shares.

    >>> split(10, 4)
    [2.5, 2.5, 2.5, 2.5]
    >>> split(10, 3)
    [3.33, 3.33, 3.34]
    """
    base = round(total / ways, 2)
    shares = [base] * ways
    shares[-1] = round(total - base * (ways - 1), 2)
    return shares


def fees(amount):
    """Return the fee.

    >>> fees(100)
    2.9
    """
    return amount * 0.029
EOF
````

Both examples look correct. One of them is not.

**Step 2: run them**

```bash
python3 -m pytest --doctest-modules money.py -q
```

```
_____________________________ [doctest] money.fees _____________________________
021 >>> fees(100)
Expected:
    2.9
Got:
    2.9000000000000004

1 failed, 1 passed
```

`100 * 0.029` is not 2.9 in binary floating point. Nobody writing that
docstring by hand would have written `2.9000000000000004`, and nobody reviewing
it would have queried `2.9`. This is the entire argument for doctests in four
lines: the example was wrong, in a way review does not catch, and execution
found it immediately.

Note the `split(10, 3)` example passed. The uneven split genuinely returns
`[3.33, 3.33, 3.34]`, which is worth knowing and is exactly the kind of
behaviour a reader wants documented.

**Step 3: fix it the right way**

```bash
python3 - <<'PY'
from pathlib import Path
t = Path("money.py").read_text()
Path("money.py").write_text(t.replace(
    "    >>> fees(100)\n    2.9\n",
    "    >>> round(fees(100), 2)\n    2.9\n"))
PY
python3 -m pytest --doctest-modules money.py -q
```

```
2 passed in 0.02s
```

Rounding in the example is better than pasting the full float. The reader
learns the rounded figure they care about, and the assertion stops being
hostage to the last bit of a float.

**Step 4: the exit codes, which are not what you expect**

```bash
printf 'def f(x):\n    """No example here."""\n    return x\n' > empty.py

python3 -m doctest empty.py >/dev/null 2>&1
echo "python -m doctest, module with no doctests: exit=$?"

python3 -m pytest --doctest-modules empty.py -q >/dev/null 2>&1
echo "pytest --doctest-modules, same module:     exit=$?"
```

```
python -m doctest, module with no doctests: exit=0
pytest --doctest-modules, same module:     exit=5
```

`python -m doctest` is silent and successful on a module with no examples,
which is correct behaviour and a trap: if a docstring is reformatted and the
`>>>` lines are lost, nothing fails. Pytest's exit 5 means "no tests were
collected", which CI reads as a failure and which you will hit the first time
you point `--doctest-modules` at a single file.

**Step 5: measure the examples that do not exist**

A doctest that was never written cannot fail, so coverage is the missing
number:

```python
import ast
import pathlib

for path in [pathlib.Path("money.py"), pathlib.Path("empty.py")]:
    tree = ast.parse(path.read_text())
    rows = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.name.startswith("_"):
                continue
            rows.append((node.name, ">>>" in (ast.get_docstring(node) or "")))
    covered = sum(1 for _n, ok in rows if ok)
    print(f"{path}: {covered}/{len(rows)} public callables carry a runnable example")
    for name, ok in rows:
        print(f"    {'yes' if ok else 'NO '}  {name}")
```

```
money.py: 2/2 public callables carry a runnable example
    yes  split
    yes  fees
empty.py: 0/1 public callables carry a runnable example
    NO   f
```

**What you built.** Executed examples, plus the number that tells you how much
of your public surface has one. The second is the part most projects never add,
and it is the difference between "our doctests pass" and "our public API is
documented with examples that pass."

## Reference

### Enabling them

```toml
# pyproject.toml
[tool.pytest.ini_options]
addopts = "--doctest-modules"
testpaths = ["tests", "src"]
```

`testpaths` must include the source tree, not just `tests`, or the docstrings
are never collected. This is the most common reason a project believes it runs
doctests and does not.

### Directives worth knowing

| Directive | Use for |
|---|---|
| `# doctest: +ELLIPSIS` | Output containing a path, address or timestamp; `...` matches anything |
| `# doctest: +SKIP` | An example that is illustrative and cannot run |
| `# doctest: +NORMALIZE_WHITESPACE` | Wrapped output you do not want to match exactly |
| `# doctest: +IGNORE_EXCEPTION_DETAIL` | An expected exception whose message may change |

Reach for `+ELLIPSIS` before `+SKIP`. A skipped doctest looks like coverage in
the file and provides none.

### What doctests are good and bad at

| Good | Bad |
|---|---|
| Small, pure functions with a clear return | Anything needing setup or fixtures |
| Showing a return value's exact shape | Floating point, unless you round |
| Documenting edge cases, as `split(10, 3)` does | Dict or set ordering |
| Keeping a generated reference honest | Multi-step workflows, which belong in a tutorial |
| Error messages a user will see | Anything slow, networked or stateful |

When a doctest wants fixtures, it has stopped being documentation and become a
unit test written in an awkward syntax. Move it.

### Where this fits against the alternatives

| Approach | Sample lives | Catches drift when |
|---|---|---|
| Doctests | In the docstring | The function's behaviour changes |
| [Sample validation](code-sample-validation.md) | In Markdown pages | A tutorial or how-to goes stale |
| [Doc test harness](doc-test-harness.md) | Either, with infrastructure | You need skip budgets, output fixtures, reporting |
| [Cold-start testing](coldstart-testing.md) | In the quickstart | The install path breaks |

They are complements. Doctests cover the reference layer, where functions are
small and examples are one-liners. They are a poor fit for tutorials, and
trying to force a tutorial into docstrings is how projects end up with
unreadable module headers.

## How to talk about it

**Lead with the generated reference.** "Doctests keep the examples in generated
API documentation honest, which matters because readers trust generated
reference material more than prose and therefore get hurt worse when it is
stale. The cost is one line in `pyproject.toml`."

**The follow-up is where they break down**, and the answer should be specific:
floating point, dict ordering, and anything needing fixtures. Say that you
round in the example rather than pasting a full float repr, and that a doctest
wanting a fixture should become a unit test.

**The tradeoff to volunteer.** Doctests make docstrings longer and partly
mortgage readability to testability. A module whose header is forty lines of
session transcript is worse documentation than one with a clear paragraph, even
though the transcript is verified. The honest position is that doctests belong
on small functions with interesting return values, not on everything.

**One sharper point.** A doctest that does not exist cannot fail, so "our
doctests pass" is a claim about the examples somebody happened to write. The
useful metric is what fraction of the public surface carries a runnable
example, which is twenty lines of `ast` walking and is almost never measured.
Bring the number.

## How to prove it

**The artifact.** A repository with `--doctest-modules` enabled against the
source tree, and ideally a coverage number for runnable examples.

**Three things to do, in order:**

1. Run the golden path. The `fees(100)` failure is the whole pitch, and it
   takes two minutes to reproduce.
2. Add `--doctest-modules` to a project you own, with `testpaths` including the
   source. Whatever fails was already wrong in your published reference.
3. Run the step 5 coverage script over your package and write the number down.
   That is the sentence nobody else in the interview will have.

**What makes it credible rather than decorative.** `docpack` runs
`--doctest-modules` across its package, so every docstring example is executed,
and one of them broke a strict build and had to be fixed. The broken one is the
story: it proves the examples are load-bearing rather than decorative.

## Related

- [Code-sample validation](code-sample-validation.md), the same idea for Markdown pages
- [Building a doc test harness](doc-test-harness.md), when one flag is no longer enough
- [Generated API reference](api-reference-generation.md), what doctests keep honest
- [Automating docs with Python](python-for-content.md), the tooling underneath
