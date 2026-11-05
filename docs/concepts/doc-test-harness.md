---
title: Building a doc test harness
summary: "The infrastructure around sample execution: shell state, failure attribution, and a check that cannot be fooled."
diataxis: how-to
audience: developer
concept: doc-test-harness
tags: [qa, core]
---

# Building a doc test harness

`core` · difficulty 3 · 6h

!!! quote "Asked for by name"
    NVIDIA: "Content quality automation you've built, such as Vale or custom linters, doc test harnesses, or freshness monitoring"

**Prerequisites:** [Code-sample validation](code-sample-validation.md)

## What it is

The infrastructure that turns sample execution from a script into something a
team can rely on. [Code-sample validation](code-sample-validation.md) is the
idea: run the examples. A harness is what you need once the corpus has more
than one language in it, samples that depend on each other, and contributors
who will be reading its failure output at 5pm on a Friday.

Three problems make it real work: shell samples carry state a subprocess does
not inherit, concatenating them destroys failure attribution, and any harness
built on parsing source can be fooled by the source.

## Why the job asks for it

NVIDIA lists doc test harnesses as a thing you have built. The word is doing
work: a harness, not a test. The difference is everything in this page.

A script that executes Python blocks is a weekend. A real harness is not: it
handles bash and Python, keeps per-page state, attributes failures to a source
line, carries a reviewable skip convention with a budget, and verifies its
conclusions against what the reader actually receives. That is a piece of
engineering, and it is the most direct evidence you can offer that
documentation correctness is something you enforce rather than hope for.

## The golden path

Build up the shell half, discovering the two traps that make it harder than
Python. About fifty minutes.

**Step 1: a quickstart whose steps depend on each other**

````bash
mkdir -p harness-demo/docs && cd harness-demo
cat > docs/quickstart.md <<'MDEOF'
# Quickstart

```bash
mkdir -p project && cd project
printf 'name = "demo"\n' > config.toml
```

```bash
cat config.toml
```

```
name = "demo"
```
MDEOF
````

**Step 2: isolate each block, the safe-sounding choice**

```python
import subprocess
import tempfile

for start, code in blocks(page, "bash"):
    with tempfile.TemporaryDirectory() as d:
        r = subprocess.run(["bash", "-e", "-c", code], cwd=d,
                           capture_output=True, text=True)
        print(f"  block@{start}: exit={r.returncode} err={r.stderr.strip()!r}")
```

```
  block@3: exit=0 err=''
  block@8: exit=1 err='cat: config.toml: No such file or directory'
```

Same failure as the Python case: a quickstart is a sequence. Isolation tests a
document nobody wrote.

**Step 3: share the directory, and watch it still fail**

```python
with tempfile.TemporaryDirectory() as d:
    for start, code in blocks(page, "bash"):
        r = subprocess.run(["bash", "-e", "-c", code], cwd=d, ...)
```

```
  block@3: exit=0 err=''
  block@8: exit=1 err='cat: config.toml: No such file or directory'
```

Identical. This is the trap that makes shell harder than Python: block one ran
`cd project`, and `cd` changes the working directory of *that subprocess*.
Block two gets a new subprocess, starting in the shared directory's root, and
the file it wants is one level down.

Sharing a directory is not sharing a shell. Environment variables set by a
block are lost the same way.

**Step 4: one shell per page**

```python
with tempfile.TemporaryDirectory() as d:
    script = "\n".join(code for _start, code in blocks(page, "bash"))
    r = subprocess.run(["bash", "-e", "-c", script], cwd=d,
                       capture_output=True, text=True)
    print(f"  exit={r.returncode} out={r.stdout.strip()!r}")
```

```
  exit=0 out='name = "demo"'
```

Correct. `cd` persists, the file is found, and the output matches what the page
promises.

**Step 5: discover what concatenation cost you**

Add a block that fails:

````bash
cat >> docs/quickstart.md <<'MDEOF'

```bash
cat missing-file.toml
```
MDEOF
````

```
  exit=1  stderr='cat: missing-file.toml: No such file or directory'
  -> no line number, no block identity
```

The harness knows the page is broken and cannot say where. On a 200-line
quickstart with nine shell blocks, that report sends the reader to read the
whole page. Concatenation bought shared state and sold failure attribution.

**Step 6: buy it back with sentinels**

```python
parts = []
for start, code in blocks(page, "bash"):
    parts.append(f'echo "__BLOCK__ {page}:{start}" >&2')
    parts.append(code)

r = subprocess.run(["bash", "-e", "-c", "\n".join(parts)], cwd=d,
                   capture_output=True, text=True)

last = None
for line in r.stderr.splitlines():
    if line.startswith("__BLOCK__"):
        last = line.split(None, 1)[1]
real = [l for l in r.stderr.splitlines() if not l.startswith("__BLOCK__")]
print(f"  exit={r.returncode}  failing block={last}")
print(f"  error={real[-1] if real else ''}")
```

```
  exit=1  failing block=docs/quickstart.md:16
  error=cat: missing-file.toml: No such file or directory
```

A source line and the real error. Because `bash -e` stops at the first failure,
the last sentinel seen is the block that broke, which is all the bookkeeping
this needs.

**What you built.** Shared shell state and per-block attribution at the same
time, which were in tension and did not have to be.

## Reference

### The decisions a harness has to make, per language

| Decision | Python | Bash |
|---|---|---|
| State sharing | One `globals()` dict per page | One shell process per page |
| What `cd` does | Not applicable | Persists only inside one process |
| Isolation boundary | Per page | Per page, in a temp directory |
| Failure attribution | Free, via `compile(code, filename)` | Needs sentinels |
| Stopping on first error | Natural, exceptions propagate | Needs `-e` |
| Capturing output | `redirect_stdout` | `capture_output` |

### What belongs in a harness that does not belong in a script

| Feature | Why it earns its place |
|---|---|
| Per-page state, per-corpus isolation | Pages are sequences; the corpus is not |
| Source-line attribution | A failure you cannot locate is a chore, not a fix |
| A skip marker carrying a reason | Reviewable in a diff |
| A skip budget | The escape hatch is the threat; see below |
| Expected-output fences | Catches changed values, which is most rot |
| Language dispatch | A corpus is never one language |
| A scratch directory per page | Samples that write files must not touch the repo |
| A verification half (below) | Because the parsing half can be fooled |

### The escape hatches are the attack surface

Every harness needs a way to exempt a sample, and every exemption is a way to
make a red build green without fixing anything. In `docpack`, the convention is
`# docpack: skip`, the reason is required, and a test asserts the skip ratio
stays under 25 per cent.

The honest limitation, measured in
[code-sample validation](code-sample-validation.md), is that a ratio budget is
meaningless on a small corpus: with three blocks the ratio can only be 0, 33,
67 or 100 per cent, so the cap fires on a clean corpus. Budgets start meaning
something in the low hundreds of blocks. Before that, require the reason and
read it in review.

**Do not widen a budget to get a green build.** The budget is load-bearing, and
relaxing it is the one change that converts the whole harness into decoration.

### Two halves, because the first half can be fooled

The most important structural idea in a harness is that a check which reasons
about *source* can be defeated by the source, so it needs a partner that
compares against what the reader receives.

This guide learned that the expensive way. Its static checks, a registry
validator, a hundred tests and a strict site build all passed while seven pages
rendered code samples as prose, because a heredoc inside a bash sample
contained a fence of its own and closed the outer block early. Every tool was
looking at the Markdown and reasoning about it correctly; none was looking at
the published HTML.

| Half | Reads | Can be fooled by | Speed |
|---|---|---|---|
| Static | Markdown source | Anything that makes the source parse differently than you modelled | Instant |
| Ground truth | Built HTML | Very little; it is what the reader gets | Needs a build |

`src/fieldguide/fences.py` implements both. The second half compares every
fenced source line against the `<pre>` content of the built page, and found 127
defects on the day it was written. Keep the fast half for feedback and the slow
half for truth.

## How to talk about it

**Lead with the shell state problem**, because it is concrete and most people
have not thought it through. "Sharing a temp directory between bash blocks is
not sharing a shell. `cd` and exported variables live in the process, so a
quickstart has to run as one shell per page. That buys shared state and costs
failure attribution, which you get back with a sentinel echo before each
block."

**The follow-up is about the skip mechanism**, and the strong answer names it
as the attack surface: a required reason, a ratio budget, an explicit rule that
you do not widen the budget to go green, and the honest caveat that the budget
does nothing on a small corpus.

**The tradeoff to volunteer.** A harness that runs real shell commands is
running untrusted-ish code from pull requests. It needs a scratch directory, no
credentials in its environment, and ideally a container, and that means
contributors cannot easily reproduce the sandbox locally. You are trading
reproducibility for safety, and the mitigation is to make the sandbox a script
rather than a CI-only incantation.

**One sharper point.** Any harness built on parsing source can be fooled by the
source, so it needs a half that checks the artifact the reader receives. This
guide had every static check green while seven pages shipped code as prose, and
the fix was a comparison against the built HTML, not a smarter parser. If you
can only say one thing about harness design, say that.

## How to prove it

**The artifact.** A harness in a repository of yours that handles more than one
language, attributes failures to a source line, and has a skip convention with
a budget.

**Three things to do, in order:**

1. Run the golden path to step 6. Steps 3 and 5 are the two surprises.
2. Add sentinel attribution to any shell-sample runner you already have. It is
   four lines and it changes the failure report from useless to actionable.
3. Pick one static check you trust and ask what artifact it never looks at.
   That gap is your second half. If the answer is that it looks at everything,
   you have not found the artifact yet: every static check skips something,
   and what it skips is where the next defect lives.

**What makes it credible rather than decorative.** `docpack`'s harness extracts
every Python block, executes it, requires a reason on every skip, and asserts
the skip ratio stays under 25 per cent. The number is the credible part: a
harness with no budget and a dozen silent skips is a harness that stopped
testing a while ago and did not mention it.

## Related

- [Code-sample validation](code-sample-validation.md), the idea this is the infrastructure for
- [Cold-start testing](coldstart-testing.md), the harness run against a fresh environment
- [Doctests](doctests.md), the version that needs no harness at all
- [Writing custom linters](custom-linters.md), the static checks this complements
