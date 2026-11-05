---
title: Code-sample validation
summary: Executing the examples in your documentation, and asserting their output rather than just their exit code.
diataxis: how-to
audience: developer
concept: code-sample-validation
tags: [qa, core]
---

# Code-sample validation

`core` · difficulty 3 · 5h

!!! quote "Asked for by name"
    Intel: "documentation CI, including link and code-sample validation"

    NVIDIA: "Build and run docs-as-code pipelines: Git authoring, CI/CD builds, linting, link and code-sample validation, and publishing"

**Prerequisites:** [Docs-as-code](docs-as-code.md)

## What it is

Extracting the code blocks out of your documentation and running them, so that
a sample which no longer works fails a build instead of failing a reader.

Both postings name it. The distinction that separates a real implementation
from a checkbox is whether you assert the **output** or merely the exit code,
and the golden path below makes the difference measurable.

## Why the job asks for it

A code sample is the part of a page a reader trusts most and the part most
likely to be wrong. Prose ages gracefully; a sample either runs or it does not,
and when it does not the reader concludes that nothing on the page can be
relied on.

Samples rot for reasons that have nothing to do with the writer. A parameter is
renamed, a default changes, a method moves, a dependency releases a major
version. Nobody edited the page, and the page became false. This is the
canonical case for automation, because no review process catches it: there is
no diff to review.

The reason it is difficulty 3 rather than 1 is that the obvious implementation
has a hole in it big enough to drive the entire problem through, which is the
subject of step 5.

## The golden path

Build an extractor, discover the state problem, add a skip convention, then
find out that your passing harness is lying to you. About forty-five minutes.

**Step 1: a tutorial and the library it documents**

````bash
mkdir -p samples-demo/docs && cd samples-demo

cat > docs/tutorial.md <<'MDEOF'
# Tutorial

First create a client:

```python
from widget import Client
client = Client(token="test")
```

Then list the data sets:

```python
sets = client.list_data_sets()
print(len(sets))
```

A snippet that cannot run here:

```python
client.delete_everything()
```
MDEOF

cat > widget.py <<'EOF'
class Client:
    def __init__(self, token): self.token = token
    def list_data_sets(self): return ["a", "b", "c"]
EOF
````

**Step 2: extract the blocks**

```python
# extract.py
import re
from pathlib import Path

FENCE = re.compile(r"^```(\w+)?\s*$")


def blocks(path, lang="python"):
    out, cur, cur_lang, start = [], None, None, 0
    for n, line in enumerate(path.read_text().splitlines(), 1):
        m = FENCE.match(line)
        if m and cur is None:
            cur, cur_lang, start = [], m.group(1), n
        elif m and cur is not None:
            if cur_lang == lang:
                out.append((start, "\n".join(cur)))
            cur = None
        elif cur is not None:
            cur.append(line)
    return out
```

**Step 3: run each block, and watch the obvious approach fail**

```python
from pathlib import Path
from extract import blocks

for p in sorted(Path("docs").rglob("*.md")):
    for start, code in blocks(p):
        try:
            exec(compile(code, f"{p}:{start}", "exec"), {})
            print(f"  PASS {p}:{start}")
        except Exception as e:
            print(f"  FAIL {p}:{start}  {type(e).__name__}: {e}")
```

```
  PASS docs/tutorial.md:5
  FAIL docs/tutorial.md:12  NameError: name 'client' is not defined
  FAIL docs/tutorial.md:19  NameError: name 'client' is not defined
```

Two failures, neither of them a real defect. A tutorial is a sequence: block
two uses the `client` that block one created. Executing blocks in isolation
tests a document nobody wrote.

**Step 4: one namespace per page**

```python
for p in sorted(Path("docs").rglob("*.md")):
    ns = {}   # shared across this page's blocks, fresh for the next page
    for start, code in blocks(p):
        exec(compile(code, f"{p}:{start}", "exec"), ns)
```

```
  PASS docs/tutorial.md:5
3
  PASS docs/tutorial.md:12
  FAIL docs/tutorial.md:19  AttributeError: 'Client' object has no attribute 'delete_everything'
```

Now the two tutorial steps pass and the remaining failure is honest: that
method does not exist. Per-page rather than per-corpus, because page order is
not a contract and a global namespace makes every page depend on every other.

**Step 5: the step that matters**

Add a skip convention for the destructive block, declare the expected output of
block two, and check it:

````bash
cat >> docs/tutorial.md <<'EOF'
EOF
# edit the destructive block to carry a reason
python3 - <<'PY'
from pathlib import Path
p = Path("docs/tutorial.md")
p.write_text(p.read_text().replace(
    "client.delete_everything()",
    "# docs: skip (destructive)\nclient.delete_everything()"))
PY
````

The harness now captures stdout and compares it against an untagged fence
following the block:

```python
import io
import re
from contextlib import redirect_stdout

SKIP = re.compile(r"^#\s*docs:\s*skip(?:\s*\((?P<why>[^)]*)\))?\s*$", re.M)
BUDGET = 0.25

# ... for each block:
if m := SKIP.search(code):
    skipped += 1
    print(f"  SKIP {p}:{start}  ({m.group('why') or 'no reason given'})")
    continue
buf = io.StringIO()
with redirect_stdout(buf):
    exec(compile(code, f"{p}:{start}", "exec"), ns)
want = expected_after(p, start + len(code.splitlines()) + 1)
got = buf.getvalue().strip()
if want is not None and want != got:
    print(f"  DIFF {p}:{start}  expected {want!r}, got {got!r}")
```

```
  PASS docs/tutorial.md:5  (no expected output declared)
  PASS docs/tutorial.md:12  output matches '3'
  SKIP docs/tutorial.md:23  (destructive)

ran=2 skipped=1 failed=0 mismatch=0
skip ratio 33% (budget 25%)
```

**Step 6: prove why the output assertion is the whole point**

Change the library the way a real release would, adding a fourth data set:

```bash
cat > widget.py <<'EOF'
class Client:
    def __init__(self, token): self.token = token
    def list_data_sets(self): return ["a", "b", "c", "d"]
EOF
python3 harness.py
```

```
  PASS docs/tutorial.md:5  (no expected output declared)
  DIFF docs/tutorial.md:12  expected '3', got '4'
FAIL
```

Caught. Now run a harness that only checks whether blocks execute:

```
  runs-only harness: 2 block(s) executed with no error -> would report GREEN
```

Green. Both blocks ran perfectly. The documentation says the answer is 3, the
software says 4, and a validation suite that only executes samples reports no
problem at all.

**What you built.** The distinction between a sample that runs and a sample
that is correct. Executing samples catches deletions and renames. Asserting
their output catches everything else, which is most of it.

## Reference

### What each level of rigour catches

| Level | Catches | Misses |
|---|---|---|
| Syntax check or lint | Typos, syntax errors | Anything about behaviour |
| Execute, check exit code | Removed functions, renamed parameters, import errors | Every changed value, every changed shape |
| Execute, assert output | Changed defaults, counts, formats, error messages | Behaviour you did not print |
| Execute in a fresh environment | Missing install steps, undeclared dependencies | Nothing much, and it is slow |

Most teams stop at level two and describe themselves as validating samples.
Level three is where the defects actually are.

### Decisions you have to make

| Decision | Options | What this page recommends |
|---|---|---|
| Namespace | Per block, per page, per corpus | Per page: a tutorial is a sequence, a corpus is not |
| Non-runnable samples | Skip marker, separate tag, exclude by path | A marker in the code, carrying a reason |
| Expected output | Comment, adjacent fence, separate fixture | Adjacent fence, so the reader sees it too |
| Non-determinism | Normalise, redact, or skip | Normalise timestamps and ids; skip only when you cannot |
| Where it runs | Unit test suite, separate CI job | Separate job: it is slower than unit tests |

Declaring expected output in a fence the reader can see is the choice worth
defending. The alternative, a hidden fixture file, means the assertion and the
documentation can disagree without anyone noticing.

### The skip convention, and its budget

A skip marker is necessary and it is also the hole in the system, because the
quickest way to make a failing harness green is to skip the failing block. Two
mitigations, both cheap:

| Mitigation | Effect |
|---|---|
| Require a reason in the marker | A reviewer can judge it; `skip (destructive)` is arguable, bare `skip` is not |
| Cap the skip ratio | The suite fails if too much of the corpus is exempt |

A budget has one honest limitation, visible in step 5: on three blocks, the
ratio can only be 0, 33, 67 or 100 per cent, so the cap fired on a corpus with
nothing wrong with it. Budgets mean something at a hundred blocks and nothing
at ten. Until then, require the reason and read it in review.

## How to talk about it

**Lead with the difference between running and being correct.** "Extracting
and executing samples catches the obvious rot, renames and deletions. It does
not catch a changed default or a changed count, and those are the majority. So
the harness captures stdout and compares it against an expected-output block
that the reader can also see."

**The follow-up is about samples that cannot run**, and the answer is a skip
marker that carries a reason plus a cap on the skip ratio, with the honest
admission that the cap is meaningless on a small corpus.

**The tradeoff to volunteer.** Output assertions make the harness brittle
against legitimate change. Every intentional behaviour change now requires a
documentation update in the same pull request, which is the point and is also
real friction. On a fast-moving product you will spend time updating expected
output for changes you intended. That is the cost of a corpus that cannot
silently lie, and it is worth it, but claiming it is free is the tell of someone
who has not run it.

**One sharper point.** The expected-output fence is a documentation improvement
before it is a testing one. A sample with no output shown makes the reader run
it to find out what happens. Writing the output down helps every reader and
happens to give the harness something to assert, which is the best kind of
quality mechanism: one that makes the page better even when it never fires.

## How to prove it

**The artifact.** A test that extracts samples from your own documentation,
executes them, and asserts at least some of their output, plus a commit where
it caught a real change.

**Three things to do, in order:**

1. Run the golden path through step 6. The side-by-side of DIFF and GREEN is
   the argument.
2. Point the extractor at a docs site you own and just execute the blocks.
   Whatever fails first is a page currently lying to readers.
3. Add an expected-output fence to the one sample readers ask about most. You
   have improved the page and created an assertion in the same edit.

**What makes it credible rather than decorative.** `docpack` extracts every
Python block from its documentation and executes it, with `# docpack: skip`
making exceptions visible and a test asserting the skip ratio stays under 25
per cent. The part worth discussing in an interview is the skip ratio
assertion, because it shows you understood that the escape hatch is the threat.

## Related

- [Doctests and executable docstrings](doctests.md), the same idea inside the source
- [Building a doc test harness](doc-test-harness.md), this grown into infrastructure
- [Cold-start testing](coldstart-testing.md), running the samples in a fresh environment
- [Documentation CI](documentation-ci.md), the job this belongs in
