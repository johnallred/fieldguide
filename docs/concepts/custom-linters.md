---
title: Writing custom linters
summary: Building the check no off-the-shelf tool can express, and learning what its first run tells you.
diataxis: how-to
audience: developer
concept: custom-linters
tags: [qa, supporting]
---

# Writing custom linters

`supporting` · difficulty 3 · 5h

!!! quote "Asked for by name"
    NVIDIA: "Content quality automation you've built, such as Vale or custom linters, doc test harnesses, or freshness monitoring"

**Prerequisites:** [Prose linting with Vale](prose-linting.md)

## What it is

A check you write yourself because the rule you need is not a pattern. Vale and
its relatives match text. Some of the most valuable documentation rules require
*parsing*: knowing which lines are code, which are heredoc data, whether a
front-matter field is a member of a closed vocabulary, whether the version
mentioned in a sentence is the one in the lockfile.

The phrase in the posting is "content quality automation you've built." Built,
not configured.

## Why the job asks for it

Because the interesting defects in a documentation corpus are structural, and
structure is exactly what a text matcher cannot see.

Consider three rules. "Do not write *simply*" is a pattern, and Vale does it in
four lines. "Every page has a `kind` field whose value is one of four strings"
is a schema check against front matter. "No code fence contains a nested fence
that closes it early" requires modeling shell heredocs. The second and third
are not expressible as patterns at any length, and the third is the one that
silently broke seven pages of this guide.

The deeper reason is that a custom linter encodes a decision. Once a rule is
code, the convention it enforces becomes explicit, testable and arguable in a
pull request, which is NVIDIA's "encode standards into templates, validators
and guided workflows rather than static documents."

## The golden path

Write a plausible rule, measure it against a real corpus, and let the
measurement change the rule. About forty minutes. The point of this path is
the measurement, not the code.

**Step 1: the rule that sounds obviously right**

Every code fence should declare its language, so syntax highlighting works.
A reasonable house rule, and not expressible in Vale, which excludes code
blocks from its analysis by design.

```python
# lint_fences.py
import re
import sys
from pathlib import Path

MARKER = re.compile(r"^(?P<indent> {0,3})(?P<ticks>`{3,})(?P<info>.*)$")


def spans(lines):
    """Closed fence blocks as (open, close), ignoring heredoc data."""
    out, open_at, open_ticks = [], None, ""
    for n, line in enumerate(lines, 1):
        m = MARKER.match(line)
        if not m:
            continue
        ticks, info = m.group("ticks"), m.group("info").strip()
        if open_at is None:
            open_at, open_ticks = n, ticks
        elif len(ticks) >= len(open_ticks) and not info:
            out.append((open_at, n))
            open_at, open_ticks = None, ""
    return out


def check(root):
    findings = []
    for page in sorted(root.rglob("*.md")):
        lines = page.read_text(encoding="utf-8").splitlines()
        for open_at, _close in spans(lines):
            if not MARKER.match(lines[open_at - 1]).group("info").strip():
                findings.append(f"{page}:{open_at}: fence has no language tag")
    return findings


if __name__ == "__main__":
    found = check(Path(sys.argv[1] if len(sys.argv) > 1 else "docs"))
    for f in found:
        print(f"LINT  {f}")
    print(f"{'FAIL' if found else 'ok'}: {len(found)} finding(s)")
    raise SystemExit(1 if found else 0)
```

**Step 2: run it against a corpus that is not a toy**

```bash
python3 lint_fences.py docs/ | tail -4
```

```
LINT  docs/concepts/github-actions.md:219: fence has no language tag
LINT  docs/concepts/prose-linting.md:231: fence has no language tag
FAIL: 21 finding(s)
```

Twenty-one findings out of 207 fences. At this point the instinct is to open
twenty-one pages and add language tags. Do not. Read the findings first.

**Step 3: read what the findings actually are**

```bash
sed -n '98,100p' docs/concepts/documentation-ci.md
sed -n '110,112p' docs/concepts/github-actions.md
```

````text
```
chain exit=1
```
````

````text
```
DRIFT  CI runs but `make check` does not: python3 gate_links.py
FAIL: 3 CI command(s), 2 local, 1 drifted
```
````

Those are not code. They are **program output**, and there is no language tag
that is correct for the stdout of a shell script. The rule is firing on exactly
the case where no tag is the right answer.

Sample the rest and the pattern holds. The rule has close to a 100 per cent
false-positive rate on this corpus, and it would have cost an afternoon of
edits that made every page slightly worse.

**Step 4: try to fix it with a heuristic, and measure again**

An untagged block that directly follows a tagged block is probably that
command's output:

```python
# in check(), replace the inner loop
blocks = spans(lines)
for i, (open_at, close) in enumerate(blocks):
    if MARKER.match(lines[open_at - 1]).group("info").strip():
        continue
    prev = blocks[i - 1] if i else None
    if prev and MARKER.match(lines[prev[0] - 1]).group("info").strip() \
            and open_at - prev[1] <= 4:
        continue   # output of the command above
    findings.append(f"{page}:{open_at}: fence has no language tag")
```

```
untagged fences that directly follow a tagged block (output): 17
untagged fences that do not:                                  4
    docs/concepts/ai-assistants.md:420
    docs/concepts/geo.md:317
    docs/concepts/llm-content-lifecycle.md:370
    docs/concepts/prose-linting.md:231
```

From 21 to 4. Better. Now check those four, and two of them are *also* output,
just separated from their command by a paragraph of explanation.

The heuristic improved the rule and did not fix it, and it cannot, because "is
this block program output" is a question about intent. No amount of proximity
logic answers it.

**Step 5: change the convention, not the heuristic**

```bash
echo 'Tag output blocks explicitly: ```text for stdout, ```console for a session.' \
  >> CONTRIBUTING.md
```

With that convention adopted, the original rule from step 1 becomes exact: an
untagged fence is now unambiguously a mistake, because output has a tag too.
The linter went from unusable to correct without the code getting smarter.

**What you built.** More usefully than a linter: the knowledge that this rule
requires a convention your corpus does not yet have. The first run of a custom
linter is a measurement of whether your standard is real.

## Reference

### When to write one instead of configuring a tool

| Write your own | Use Vale or similar |
|---|---|
| The rule needs a parse, not a pattern | The rule is a word or phrase |
| It validates front matter against a schema | It is about prose style |
| It compares the doc to something else: a lockfile, an API spec, the built HTML | It is self-contained in the text |
| It must model code structure, heredocs, fences | It must *ignore* code, which Vale already does |
| The finding needs a computed fix suggestion | A static message is enough |

### What the first run tells you

| First run finds | Means | Do this |
|---|---|---|
| Nothing | The rule is already satisfied, or it is broken | Break a page on purpose and confirm it fires |
| A handful of real defects | The rule is right and the corpus drifted | Fix the pages, add the gate |
| Hundreds of findings | The convention was never adopted | Decide the convention first, or do not ship the rule |
| Findings that are all legitimate | The rule encodes a convention that does not exist | Change the convention or drop the rule |

The last row is the one this page's golden path lands in, and it is the most
common outcome for a rule invented in the abstract.

### Design rules that make a linter survive contact

| Rule | Why |
|---|---|
| Report `file:line: message` | A finding that cannot be jumped to is a chore |
| Exit non-zero on findings, zero otherwise | So CI can use it without parsing output |
| Blank fenced lines rather than deleting them | Line numbers stay true |
| Make the unknown case loud | A checker that silently passes on "I could not tell" is theater |
| Ship a test that proves it fires | Otherwise a refactor can neuter it and nothing fails |
| Say how to fix it, with the exact replacement | "Widen the opener to ````" beats "bad fence" |

### The one at scale, in this repository

`src/fieldguide/fences.py` is the real version of this page. It has two halves:
a static check that models heredoc bodies as data rather than markup, and a
dynamic check that compares fenced source lines against the `<pre>` content of
the built HTML.

The second one is the interesting design choice. The static check can be
fooled, because it reasons about the source; the dynamic one compares against
what the reader actually receives, so the only way to pass it is for the sample
to genuinely be code on the page. It found 127 defects across seven pages on
the day it was written, every one of which had passed a strict build, a hundred
tests and a registry validator.

## How to talk about it

**Lead with the class of rule, not the tool.** "Vale covers anything that is a
pattern. I write my own when the rule needs a parse: validating front matter
against a closed vocabulary, or checking that a code fence is still a code
fence on the published page. That last one needed modeling shell heredocs,
which is not a regex."

**The follow-up is about maintenance**, and the answer is tests. A custom
linter without a test that proves it fires is a liability, because a future
refactor can silently neuter it and the build stays green. Say that you write
the failing fixture first.

**The tradeoff to volunteer.** Every custom linter is code you now own, with a
false-positive rate you are responsible for, and a suppression mechanism people
will use. A rule with widespread suppressions is a rule that is wrong, so you
have to watch suppression counts as a signal about the rule rather than about
the writers.

**One sharper point.** The first run of a new
rule is a measurement of your convention, not of your corpus. A rule that
produces hundreds of legitimate findings has discovered that the standard it
encodes was never actually adopted, and shipping it anyway converts that into
an afternoon of edits plus a permanent tax on contributors. Measure, read the
findings, and be willing to conclude that the convention needs changing instead
of the pages.

## How to prove it

**The artifact.** One linter you wrote, with a test that proves it fires, and
a number: how many real defects it found on first run.

**Three things to do, in order:**

1. Run the golden path against a corpus you already have. The twenty-one
   findings are the lesson, not the code.
2. Write the failing fixture before the rule. If you cannot construct a
   document that should fail, you do not yet know what the rule is.
3. Write down the false-positive rate of your rule on your own corpus. That
   number is the most credible thing you can say about a linter, and almost
   nobody has it.

**What makes it credible rather than decorative.** A linter that has never
caught anything proves you can write a loop. A linter with a commit history
showing a red build followed by a real fix proves the rule is about something.
`docpack` has four hand-written Vale rules, and the one worth discussing is the
one that caught the author's own prose.

## Related

- [Prose linting with Vale](prose-linting.md), the half you should not reimplement
- [Documentation CI](documentation-ci.md), where the gate runs
- [Building a doc test harness](doc-test-harness.md), the same idea applied to executable samples
- [Content models](content-model.md), the schema a front-matter linter validates against
