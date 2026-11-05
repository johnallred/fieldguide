---
title: Quickstarts that survive contact
summary: "The page with the shortest half-life in your corpus, and the three claims it makes that can each be checked."
diataxis: how-to
audience: new-user
concept: quickstarts
tags: [gp, core]
---

# Quickstarts that survive contact

`core` · difficulty 2 · 3h

!!! quote "Asked for by name"
    Intel: "documentation CI, including link checking and coldstart testing of quickstarts"

    Intel: "so a developer reaches first success in minutes with zero help"

**Prerequisites:** [Golden paths](golden-paths.md)

## What it is

The page that takes a reader from nothing to one working thing as fast as
possible. It implements the [golden path](golden-paths.md) and it is the single
most consequential page in a developer documentation set, because it is where
people decide whether to continue.

It is also the page with the shortest half-life, for a reason worth stating
plainly: it is the only page whose author cannot test it, because their
machine already has everything.

## Why the job asks for it

Intel names cold-start testing *of quickstarts* specifically, out of everything
it could have named. That phrasing tells you they have been burned by a
quickstart that worked for its author.

The deeper reason is that a quickstart makes several claims at once, and they
fail independently. It claims the commands work from an empty environment, that
the output you will see is what it shows, and that you will reach a useful
result. Most quickstart maintenance treats these as one thing ("is the
quickstart working?") when in fact the first can pass while the second quietly
fails, and the second failing is the one that destroys trust.

## The golden path

Write the three claims as separate checks, then watch each one fail for a
different reason. About thirty minutes.

**Step 1: a quickstart**

````bash
mkdir -p qs-demo && cd qs-demo
cat > qs.md <<'MDEOF'
# Quickstart

```bash
pip install cowsay
python3 -c "import cowsay; cowsay.cow('hi')" | head -1
```

```
  __
| hi |
```
MDEOF
````

**Step 2: the claims, checked separately**

```python
claims = {}
with tempfile.TemporaryDirectory() as d:
    subprocess.run([sys.executable, "-m", "venv", f"{d}/.v"], capture_output=True)
    script = "\n".join(cmds)  # rewritten to use the venv's pip and python
    r = subprocess.run(["bash", "-e", "-c", script], capture_output=True,
                       text=True, cwd=d)
    claims["commands succeed from empty"] = r.returncode == 0
    claims["output matches the page"] = expected[0].strip() in r.stdout.strip()
    claims["result is non-trivial"] = len(r.stdout.strip().splitlines()) >= 1
```

```bash
python3 check_qs.py
```

```
  PASS  commands succeed from empty
  FAIL  output matches the page
  PASS  result is non-trivial
```

The commands ran. The output did not match. A quickstart harness that only
checked exit codes would have reported this page healthy.

**Step 3: find out why, because it is not what you expect**

The real output of that command begins:

```
  __
| hi |
```

Which is exactly what the page shows. So why the mismatch?

The command ends in `| head -1`, so stdout is one line, while the expected
block shows two. **The page is internally inconsistent**: its command
contradicts its own output example.

That is not a drift defect. It is an authoring defect that existed from the
first commit, and no amount of reading would catch it, because a reader
checking the page against itself would have to mentally execute `head`.

```bash
sed -i 's/| head -1/| head -2/' qs.md
python3 check_qs.py
```

```
  PASS  commands succeed from empty
  PASS  output matches the page
  PASS  result is non-trivial
```

**Step 4: now the drift case**

Change the page the way a real product change would, so the command produces
something else:

```
  PASS  commands succeed from empty
  FAIL  output matches the page
  PASS  result is non-trivial
```

Same failing claim, entirely different cause: the first was the page
disagreeing with itself, the second is the page disagreeing with the software.
Both are caught by asserting output and invisible to a harness that checks
exit codes, which is the argument for separating the claims.

**Step 5: check what you are actually installing**

```bash
for i in 1 2; do
  python3 -m venv ".v$i" && ".v$i/bin/pip" install -q cowsay
  echo "run $i: $(".v$i/bin/pip" freeze | tr '\n' ' ')"
done
```

```
run 1: cowsay==6.1
run 2: cowsay==6.1
```

Identical today, and nothing in the quickstart guarantees that. An unpinned
install is a claim about the future that the page cannot keep. Whether to pin
is a real decision, and [reproducible environments](reproducible-environments.md)
is where it gets made; the thing to know here is that the quickstart's
reproducibility is inherited from that choice rather than from anything on the
page.

**What you built.** Three independently failing claims, and a demonstration
that the same failure has two completely different causes.

## Reference

### The three claims, and how each fails

| Claim | Fails when | Caught by |
|---|---|---|
| The commands work from empty | A dependency is undeclared, a step is missing | [Cold-start testing](coldstart-testing.md) |
| The output is what the page shows | The page contradicts itself, or the software changed | Output assertion |
| The result is useful | The quickstart "succeeds" into an empty state | A substantive assertion |

The third is the one nobody checks. A quickstart that ends with `synced 0
records` has technically worked and taught the reader nothing about whether
the product does anything. Asserting something non-trivial about the result is
what distinguishes first success from first exit code.

### What belongs in a quickstart

| In | Out |
|---|---|
| One route; see [golden paths](golden-paths.md) | Alternatives and platform variants |
| The shortest path to a visible result | Explanation of why it works |
| Exact commands, copy-pasteable | Placeholders the reader must resolve |
| The output to expect | Screenshots that go stale |
| One link to the next thing | A list of twelve next things |
| A stated time | Vague reassurance |

### The author's blind spots

| Assumption | How it shows up for a reader |
|---|---|
| A dependency installed years ago | `ModuleNotFoundError` on step two |
| A credential already exported | An auth error with no explanation |
| A repository already cloned | `cd myproject` with no `git clone` |
| A warm cache | A timeout, or an unexpected first-run message |
| Knowing which of two outputs is correct | Paralysis |

Every row is invisible from the author's chair, which is the whole case for
automating this page's verification rather than reviewing it.

### Time to first success

Intel's criterion is minutes. To claim it you have to measure it, which means
timing the cold-start run and publishing the number:

| What to time | Why |
|---|---|
| Install step | Usually dominates, and is the easiest to improve |
| Total to stated result | The number you publish |
| Each step separately | So you know which one to attack |

A quickstart with an unmeasured "it only takes a few minutes" is making a claim
nobody has checked. See [time to first success](time-to-first-success.md).

### Quickstart against tutorial

| | Quickstart | [Tutorial](tutorial-design.md) |
|---|---|---|
| Goal | Working, fast | Understanding |
| Length | Shortest possible | As long as the lesson needs |
| Explanation | Almost none | Essential |
| Detours | Never | Sometimes, if they teach |
| Success | Something works | The reader can now do it themselves |

Merging them produces a page that is too long to be a quickstart and too thin
to teach, which is the most common failure in this category.

## How to talk about it

**Lead with the claims, not the page.** "A quickstart makes three separable
claims: the commands work from empty, the output is what the page shows, and
the result is useful. They fail independently, and most quickstart maintenance
treats them as one thing. Checking exit codes passes a page that is lying about
its own output."

**The follow-up is why its author cannot test it**, and the answer is that
their machine already has everything, so the verification has to come from a
clean environment in CI rather than from a careful reviewer.

**The tradeoff to volunteer.** Asserting output makes the quickstart brittle
against intentional change: every deliberate behaviour change now requires a
documentation update in the same pull request. That is the point and it is real
friction, and on a fast-moving product you will spend time updating expected
output for changes you meant to make.

**One sharper point.** The same failing check has two causes worth
distinguishing. My own test page failed its output assertion not because the
software had drifted but because the page contradicted itself: the command
piped through `head -1` while the expected block showed two lines. That defect
was there from the first commit and no reader would catch it, because catching
it requires mentally executing `head`. Drift gets all the attention; pages that
were never self-consistent are at least as common.

## How to prove it

**The artifact.** A quickstart with a stated expected output, a cold-start test
that asserts it, and a published time to first success.

**Three things to do, in order:**

1. Run the golden path. Step 3 is the interesting one, because the failure is
   not drift.
2. Add an expected-output block to a quickstart you own, then check it. Pages
   frequently disagree with themselves.
3. Time your own quickstart from a clean environment and put the number on the
   page. If you cannot state it, you cannot claim minutes.

**What makes it credible rather than decorative.** `docpack`'s
`scripts/coldstart.sh` builds a fresh virtual environment, installs the way a
reader would, follows the tutorial literally, and asserts the exact output
string the tutorial promises. The exact-output assertion is the part to point
at: without it the script proves the commands exit zero, which is the weakest
of the three claims.

## Related

- [Golden paths](golden-paths.md), the single route this implements
- [Cold-start testing](coldstart-testing.md), how the first claim is checked
- [Reproducible environments](reproducible-environments.md), where pinning is decided
- [Time to first success](time-to-first-success.md), the number Intel asks for
