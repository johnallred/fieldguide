---
title: Sample walkthroughs
summary: "Explaining code that already exists, and transcluding it so the prose cannot quietly disagree with the file."
diataxis: how-to
audience: developer
concept: sample-walkthroughs
tags: [gp, core]
---

# Sample walkthroughs

`core` · difficulty 2 · 3h

!!! quote "Asked for by name"
    Intel: "Write and maintain reference documentation, tutorials, and sample walkthroughs that assume no prior context"

**Prerequisites:** [Designing tutorials](tutorial-design.md)

**Leads to:** [Sample applications and galleries](sample-apps.md)

## What it is

A page that explains a sample that already exists. The reader does not build
anything; they read working code with a guide pointing at the parts that
matter and saying why each is there.

It is the inverse of a [tutorial](tutorial-design.md). A tutorial withholds the
finished thing and grows it; a walkthrough starts from the finished thing and
decomposes it. Both are legitimate, and they fail differently: a tutorial fails
on sequencing, a walkthrough fails on **drift**, because it quotes code that
lives somewhere else.

## Why the job asks for it

Intel lists walkthroughs alongside reference and tutorials, which is the right
company: all three are the explain-this-thing layer rather than the get-started
layer.

Walkthroughs matter disproportionately for a sample gallery, which Intel also
names. A gallery of twenty samples with no walkthroughs is twenty repositories
a reader has to reverse-engineer. The walkthrough is what converts a sample
from a thing you can run into a thing you can learn from.

The engineering problem is specific. A walkthrough is prose containing copies
of code, and copies drift. Nothing about the prose changes when the sample is
edited, so the page becomes wrong silently and confidently.

## The golden path

Catch a drifted walkthrough, fix it with transclusion, then find out how the
fix fails. About thirty minutes.

Committed as `drills/walkthrough_transclusion.py`, which runs all five states
with a real MkDocs build behind the three that render. A test asserts it still
prints what this page quotes.

Committing it corrected a count. This page used to report three quoted blocks
where the walkthrough it tells you to write has two, a figure left over from an
earlier version of the sample. The drifted-block finding was right and the
total beside it was not, which is a fair illustration of the page's own
argument: a quoted figure has no idea what it is describing.

**Step 1: a sample and a walkthrough of it**

````bash
mkdir -p walk-demo/samples && cd walk-demo
cat > samples/sync.py <<'EOF'
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
EOF
````

And a walkthrough that quotes it, with one value already stale:

````bash
cat > walkthrough.md <<'MDEOF'
# Walkthrough: the sync tool

The retry count is a module constant:

```python
RETRIES = 3
```

The command takes one flag:

```python
@click.option("--dry-run", is_flag=True, help="Report without writing.")
```
MDEOF
````

**Step 2: check every quoted block against the file**

```python
sample = Path("samples/sync.py").read_text()
blocks = re.findall(r"^```python\n(.*?)^```", text, re.S | re.M)

for i, b in enumerate(blocks, 1):
    snippet = b.rstrip("\n")
    if snippet not in sample:
        problems.append(f"block {i}: not found in samples/sync.py: "
                        f"{snippet.splitlines()[0]!r}")
```

```bash
python3 check_walkthrough.py
```

```
WALK  block 1: not found in samples/sync.py: 'RETRIES = 3'
FAIL: 2 quoted block(s), 1 drifted
```

Caught. That check is twelve lines and it is the minimum a walkthrough needs,
because this failure is undetectable by reading: the prose is internally
coherent and the code looks plausible.

**Step 3: remove the possibility instead of checking for it**

Transclude the lines rather than copying them:

````bash
cat > mkdocs.yml <<'EOF'
site_name: W
markdown_extensions:
  - pymdownx.snippets:
      base_path: ["."]
      check_paths: true
  - pymdownx.superfences
EOF

cat > docs/index.md <<'MDEOF'
# Walkthrough: the sync tool

The retry count is a module constant:

```python
--8<-- "samples/sync.py:4:4"
```
MDEOF
````

```
rendered:  RETRIES = 5
```

The page now shows what the file says. Change the file and rebuild:

```bash
sed -i 's/^RETRIES = 5/RETRIES = 7/' samples/sync.py
```

```
rendered:  RETRIES = 7
```

Drift is now impossible rather than merely detected.

**Step 4: break the fix**

Line numbers are a reference into a file that moves. Insert two lines near the
top, which is what adding an import looks like:

```bash
# insert a blank line and `from __future__ import annotations` after line 1
python3 -m mkdocs build -q
```

```
rendered for "the retry count":  import click
rendered for "the command flag": (empty)
```

**Silently wrong.** The page confidently presents `import click` as the retry
count, the second block renders empty, and the build exits zero. This is worse
than the drift in step 2, because step 2's defect was at least detectable by a
string comparison and this one is not: the transclusion is working exactly as
instructed.

**Step 5: anchor by name**

Mark the region in the sample and reference it by name:

```python
# --8<-- [start:retries]
RETRIES = 7
# --8<-- [end:retries]
```

```markdown
--8<-- "samples/sync.py:retries"
```

```
rendered:  RETRIES = 7
```

Now insertions anywhere else in the file do not affect it, because the
reference is to a named region rather than to a position. The cost is two
comment lines in the sample, which is the right price.

**What you built.** A drift check, a transclusion that removes the drift, and
the knowledge that line-range transclusion introduces a quieter failure than
the one it fixes.

## Reference

### Three ways to put code in a walkthrough

| Approach | Drift | Fails when | Cost |
|---|---|---|---|
| Copy and paste | Likely | The sample is edited | None up front |
| Transclude by line range | Impossible | Lines are inserted above | A build dependency |
| Transclude by named anchor | Impossible | The anchor is deleted | Two comment lines in the sample |

Named anchors are the answer, and the reason to know all three is that you will
inherit the first and be tempted to stop at the second.

### Walkthrough against tutorial

| | Walkthrough | Tutorial |
|---|---|---|
| Starting point | Finished sample | Empty directory |
| Reader types | Nothing, or runs it once | Everything |
| Risk | Prose drifts from the sample | Sequencing hides defects |
| Mitigation | Transclusion | Output at every step |
| Good for | Showing how a real thing is built | Teaching how to build one |
| Length | Bounded by the sample | Bounded by the lesson |

### What to point at, and in what order

| Order | Explain |
|---|---|
| 1 | What the sample does, from the outside, with its output |
| 2 | The entry point, so the reader can orient |
| 3 | The parts that carry the interesting decisions |
| 4 | What was deliberately left out, and why |
| Never | Every line |

The fourth row is the one that distinguishes a good walkthrough. A sample omits
error handling, retries, authentication and configuration, and a reader who is
not told that will assume the sample is a template for production. Saying what
is missing is part of explaining what is there.

### Keeping a walkthrough honest

| Check | Catches |
|---|---|
| Quoted blocks appear in the sample | Copy-paste drift |
| Named anchors still exist | A deleted region, which transclusion fails loudly on |
| The sample runs | See [sample validation](code-sample-validation.md) |
| The stated output matches | The sample's behaviour changed |
| Anchor count in the sample matches references | An orphaned anchor nobody removed |

The last one is cheap and worth having. An anchor left in a sample after the
walkthrough stopped using it is a small mess that accumulates.

## How to talk about it

**Lead with the failure mode, because it is specific to this form.** "A
walkthrough is prose containing copies of code, so it drifts: nothing about the
page changes when the sample is edited, and the page becomes confidently wrong.
So I transclude rather than quote, and the page cannot disagree with the file."

**The follow-up is how transclusion itself fails**, and this is the part worth
having run. Line-range transclusion breaks on insertion, silently: after
adding two lines to my sample, the paragraph about the retry count rendered
`import click` and the build exited zero. Named anchors fix it, and the cost is
two comment lines in the sample.

**The tradeoff to volunteer.** Transclusion puts documentation markers in
source files, which some teams will not accept, and it means the walkthrough
cannot show a simplified version of the code. Sometimes you *want* to show a
cut-down snippet for teaching, and then you are back to copying with a drift
check. Both mechanisms have a place; the mistake is using copying by default.

**One sharper point.** Say what the sample leaves out. A reader who is not told
that a sample omits error handling and authentication will treat it as a
production template, and samples are copied into production constantly. That
sentence costs nothing and prevents the most expensive misreading a walkthrough
can produce.

## How to prove it

**The artifact.** A walkthrough that transcludes by named anchor, plus a check
that no quoted block has drifted for anything still copied.

**Three things to do, in order:**

1. Run the step 2 check against a walkthrough you own. Copy-paste drift is
   extremely common and completely invisible to review.
2. If you already transclude by line range, insert a line above one of the
   ranges and rebuild. The silence is the finding.
3. Add one sentence to your most-read walkthrough saying what the sample
   deliberately omits.

**What makes it credible rather than decorative.** Neither of this guide's
repositories contains a sample walkthrough, which the
[demonstrated](../demonstrated.md) page records. What travels is the measured
progression: a drift check that caught a stale constant, a transclusion that
made drift impossible, and the insertion test showing that the obvious
transclusion fails more quietly than the problem it solved.

## Related

- [Designing tutorials](tutorial-design.md), the inverse form
- [Sample applications and galleries](sample-apps.md), what walkthroughs accompany
- [Single-sourcing and content reuse](single-sourcing.md), the transclusion mechanism
- [Code-sample validation](code-sample-validation.md), which checks the sample runs
