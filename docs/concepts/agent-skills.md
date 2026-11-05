---
title: Agent skills and context kits
summary: Packaging the conventions an agent needs before it writes anything, so it does not have to infer them from the code.
diataxis: explanation
audience: developer
concept: agent-skills
tags: [ai, core]
---

# Agent skills and context kits

`core` · difficulty 2 · 4h

> including llms.txt, MCP-accessible sources, agent skills and context kits, and evaluation sets for answer accuracy

> Source: nvidia posting, verbatim

**Prerequisites:** [Model Context Protocol](mcp.md), [Templates and scaffolding](templates-scaffolding.md)

**Leads to:** [Agentic workflows](agentic-workflows.md)

## What it is

Instructions written for an agent rather than for a person: the conventions,
the commands, the things it must not do, loaded before it starts work. A
**context kit** is the bundle of files an agent reads to orient itself in a
repository. An **agent skill** is a narrower thing: instructions for one kind of
task, loaded when that task comes up.

The distinction that matters is not the naming. It is that **this content is
read by something that will act on it immediately and cannot ask a follow-up
question.**

## Why the job asks for it

NVIDIA names both in the same breath as llms.txt and MCP: "agent skills and
context kits". Under ways to stand out, "agent skill and context libraries
backed by documentation".

This is the newest concept in the guide and the one with the least settled
practice, which is exactly why it is worth having an opinion about. The
underlying need is old and the tooling is three years old at most.

What makes it `core`: it is the only AI-ready artifact aimed at an agent that
**writes** rather than one that answers. An assistant that gets something wrong
produces a bad answer. An agent that gets your conventions wrong produces a
pull request that looks plausible and violates six rules nobody wrote down,
and a reviewer spends longer fixing it than writing it would have taken.

On a Tuesday it is a recurring cost you can see in review comments. Every agent
pull request against the docs repo gets the same four notes: the page is missing
front matter, it uses "repo" instead of "repository", it was put in `guides/`
instead of by Diátaxis type, and the code sample is not runnable so CI fails.
Those four notes are **tribal knowledge about a repository**, they are the same
four every time, and they are a context kit that nobody has written.

## The golden path

Write a context kit for a real repository, then test it the only way that
works: by checking whether the conventions in it are the ones CI enforces.
Thirty-five minutes.

**Step 1: find the conventions by looking at what CI rejects**

Do not write the kit from memory. Derive it from the gates, because a
convention that is not enforced is a preference and a gate that is not
documented is a trap.

```bash
mkdir -p skills-drill && cd skills-drill
mkdir -p docs/how-to .github/workflows styles

cat > .github/workflows/docs.yml <<'EOF'
name: docs
on: [pull_request]
jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - run: python validate_frontmatter.py docs/
      - run: vale docs/
      - run: python -m pytest tests/test_doc_samples.py
EOF

cat > validate_frontmatter.py <<'PY'
"""The real content model. Five required fields, two closed vocabularies."""
import sys
from pathlib import Path

import yaml

REQUIRED = ("title", "summary", "diataxis", "audience", "updated")
DIATAXIS = ("tutorial", "how-to", "reference", "explanation")
AUDIENCES = ("new-user", "developer", "operator", "contributor")
DIRECTORIES = {"tutorial": "tutorials", "how-to": "how-to",
               "reference": "reference", "explanation": "explanation"}


def main(root: Path) -> int:
    failures = []
    for page in sorted(root.rglob("*.md")):
        text = page.read_text(encoding="utf-8")
        if not text.startswith("---"):
            failures.append(f"{page}: no front matter")
            continue
        meta = yaml.safe_load(text.split("---")[1]) or {}
        for field in REQUIRED:
            if field not in meta:
                failures.append(f"{page}: missing {field!r}")
        if meta.get("diataxis") not in DIATAXIS:
            failures.append(f"{page}: diataxis must be one of {list(DIATAXIS)}")
        elif page.parent.name != DIRECTORIES[meta["diataxis"]]:
            failures.append(
                f"{page}: a {meta['diataxis']} page belongs in "
                f"{DIRECTORIES[meta['diataxis']]}/"
            )
        if meta.get("audience") not in AUDIENCES:
            failures.append(f"{page}: audience must be one of {list(AUDIENCES)}")
    for failure in failures:
        print(f"CONTENT MODEL  {failure}", file=sys.stderr)
    print(f"{'FAIL' if failures else 'ok'}: {len(failures)} violation(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1])))
PY

cat > styles/Terms.yml <<'EOF'
extends: substitution
level: error
message: "Use '%s' instead of '%s'."
swap:
  repo: repository
  PR: pull request
  docs site: documentation site
EOF
ls -R | head -20
```

**Step 2: write the kit, derived from those gates**

````bash
cat > AGENTS.md <<'EOF'
# Working in this repository

You are editing a documentation corpus with a validated content model. The
checks below run on every pull request and will reject work that ignores
them. Read this before creating or editing any page.

## Before you write a page

Run `python validate_frontmatter.py docs/` to see the current state. It must
pass before and after your change.

## Required front matter

Every page needs exactly these five fields:

```yaml
---
title: Rotate an API key
summary: Replace a key without downtime.
diataxis: how-to
audience: operator
updated: 2026-10-26
---
```

- `diataxis` must be one of: `tutorial`, `how-to`, `reference`, `explanation`.
- `audience` must be one of: `new-user`, `developer`, `operator`, `contributor`.
- Do not invent values for either. Adding one is a change to
  `validate_frontmatter.py` and needs a human.

## Where a page goes

The directory is determined by `diataxis`, not by topic:

| `diataxis` | directory |
|---|---|
| `tutorial` | `docs/tutorials/` |
| `how-to` | `docs/how-to/` |
| `reference` | `docs/reference/` |
| `explanation` | `docs/explanation/` |

There is no `guides/` directory. A page about a task is a `how-to`.

## Terminology

`vale docs/` fails the build on these. Use the right-hand column:

| Do not write | Write |
|---|---|
| repo | repository |
| PR | pull request |
| docs site | documentation site |

## Code samples

Every fenced `python` block in `docs/` is extracted and executed by
`tests/test_doc_samples.py`. A sample that cannot run standalone must be
marked:

```python
# docpack: skip
client.connect(SECRET_TOKEN)
```

Prefer making the sample runnable over skipping it.

## What to do when you are unsure

Stop and say so. Specifically:

- **Do not add a value** to `diataxis` or `audience`.
- **Do not create a new top-level directory.**
- **Do not edit `validate_frontmatter.py` or `styles/`** to make your page
  pass. If a rule is wrong, say which rule and why, and leave it alone.
- **Do not mark a sample `skip`** just because it fails. Find out why first.

The last one matters most: the escape hatches in this repository are load
bearing, and widening one to get a green build defeats the gate for everyone.
EOF
wc -l AGENTS.md
````

**Step 3: test the kit against the gates**

A context kit is documentation, so it rots like documentation. The test that
matters is whether it still describes what CI enforces.

```bash
cat > test_kit.py <<'PY'
"""Check the context kit against the checks it claims to describe.

This is the only test of a context kit that catches the failure that
matters. A kit is read by something that cannot ask a follow-up question, so
a stale instruction in it is not a confusing sentence, it is a wrong action
taken confidently.

Three checks:
  VOCABULARY  every value the kit lists must be in the validator
  COMPLETE    every value the validator accepts must be in the kit
  COMMANDS    every command the kit tells an agent to run must exist
"""
import re
import sys
from pathlib import Path

import validate_frontmatter as validator

kit = Path("AGENTS.md").read_text(encoding="utf-8")
failures = []

# 1. Values the kit lists are real.
for field, allowed in (("diataxis", validator.DIATAXIS),
                       ("audience", validator.AUDIENCES)):
    match = re.search(rf"`{field}` must be one of: (.+?)\.", kit)
    if not match:
        failures.append(f"the kit does not state the allowed values for {field!r}")
        continue
    listed = set(re.findall(r"`([a-z-]+)`", match.group(1)))
    unreal = listed - set(allowed)
    if unreal:
        failures.append(f"{field}: kit lists {sorted(unreal)}, validator rejects them")
    # 2. Values the validator accepts are all in the kit.
    undocumented = set(allowed) - listed
    if undocumented:
        failures.append(
            f"{field}: validator accepts {sorted(undocumented)}, kit omits them"
        )

# 3. Required fields match.
listed_fields = set(re.findall(r"^- `(\w+)`", kit, re.M)) | set(
    re.findall(r"^(\w+):", kit.split("```yaml")[1].split("```")[0], re.M)
)
missing = set(validator.REQUIRED) - listed_fields
if missing:
    failures.append(f"required fields {sorted(missing)} are not shown in the kit")

# 4. Directory mapping matches.
for kind, directory in validator.DIRECTORIES.items():
    if f"docs/{directory}/" not in kit:
        failures.append(f"the kit does not mention docs/{directory}/ for {kind}")

# 5. Every command the kit tells an agent to run exists.
for command in re.findall(r"`(python [\w./]+\.py[^`]*|vale [^`]+)`", kit):
    target = command.split()[1]
    if target.endswith(".py") and not Path(target).exists():
        failures.append(f"the kit says to run {command!r} but {target} does not exist")

for failure in failures:
    print(f"KIT DRIFT  {failure}", file=sys.stderr)
print(f"{'FAIL' if failures else 'ok'}: context kit matches the gates "
      f"({len(failures)} problem(s))")
sys.exit(1 if failures else 0)
PY
python3 test_kit.py; echo "exit=$?"
```

**Step 4: break the gate and watch the test catch the drift**

```bash
echo "--- someone adds a new audience to the validator and forgets the kit ---"
python3 - <<'PY'
import pathlib
p = pathlib.Path("validate_frontmatter.py")
p.write_text(p.read_text().replace(
    'AUDIENCES = ("new-user", "developer", "operator", "contributor")',
    'AUDIENCES = ("new-user", "developer", "operator", "contributor", "partner")'))
PY
python3 test_kit.py; echo "exit=$?"

echo
echo "--- and the reverse: the kit promises a command that was deleted ---"
python3 - <<'PY'
import pathlib
p = pathlib.Path("validate_frontmatter.py")
p.write_text(p.read_text().replace(
    'AUDIENCES = ("new-user", "developer", "operator", "contributor", "partner")',
    'AUDIENCES = ("new-user", "developer", "operator", "contributor")'))
PY
mv validate_frontmatter.py check_model.py
python3 - <<'PY'
# The test imports the validator, so point it at the new name to isolate the
# one thing being tested: the kit's command reference is now wrong.
import pathlib
p = pathlib.Path("test_kit.py")
p.write_text(p.read_text().replace("import validate_frontmatter as validator",
                                   "import check_model as validator"))
PY
python3 test_kit.py; echo "exit=$?"
mv check_model.py validate_frontmatter.py
```

**What you built.** A context kit derived from the gates rather than from
memory, and a test that fails when the two disagree in either direction.

That test is the contribution. **A context kit is read by something that cannot
ask you a follow-up question**, so a stale instruction is not a confusing
sentence, it is a wrong action taken confidently and then reviewed by a human
who assumes the agent was told correctly.

## Reference

### Kits, skills, and what goes where

| Artifact | Loaded | Contains |
|---|---|---|
| **Context kit** (`AGENTS.md`, `CLAUDE.md`) | Always, at the start | Conventions, commands, directory rules, prohibitions |
| **Agent skill** | When a matching task comes up | How to do one kind of work well |
| [MCP server](mcp.md) | On demand, as tool calls | Content the agent queries |
| [llms.txt](llms-txt.md) | By a model that fetches URLs | A map of the published corpus |

The division is about **when it is read**. A kit is always-on and therefore has
to be short. A skill is loaded on demand and can be long. Putting a thousand
words about release notes into the always-on kit spends context on every task
that has nothing to do with release notes.

### What belongs in an always-on kit

| Include | Why |
|---|---|
| The closed vocabularies, listed in full | Otherwise it invents a value |
| Where files go, as a rule not examples | A rule generalises; examples get pattern-matched |
| The commands CI runs | So it can check its own work before opening a pull request |
| Terminology the linter enforces | Cheapest possible review-comment elimination |
| Explicit prohibitions | The highest-value section. See below |
| What to do when unsure | "Stop and say so" needs saying |

| Leave out | Why |
|---|---|
| Anything a tool can answer | Put it behind [MCP](mcp.md) instead |
| Long rationale | A kit is instructions; link the explanation |
| Content that duplicates the corpus | It will drift from the corpus |
| Style advice with no gate behind it | Unenforced advice is noise competing with rules |

### Prohibitions are the part people forget

A kit full of positive instructions tells an agent what good work looks like.
It does not stop the specific failures that cost the most, which are all of the
form *widening a constraint to make a failure go away*:

| Prohibition | What it prevents |
|---|---|
| Do not add a value to a closed vocabulary | Silent corruption of a facet everything filters on |
| Do not edit the validator or the lint rules | A green build that proves nothing |
| Do not mark a sample `skip` to pass CI | Defeating [sample validation](code-sample-validation.md) for everyone |
| Do not create a new top-level directory | Structure drift that is expensive to undo |
| Do not invent a flag or version | [Fabrication](hallucination-guardrails.md) in a committed file |

Every one of those is a *rational* move for something trying to get a green
build. They have to be named.

### Writing for an agent, against writing for a person

| | A person | An agent |
|---|---|---|
| Can ask a follow-up | yes | no |
| Infers from surrounding code | reliably | plausibly, which is worse |
| Reads the whole thing | rarely | yes, every time |
| Skips a rule they disagree with | sometimes | only if ambiguous |
| Cost of ambiguity | a question | a confident wrong action |

The third row is why brevity matters more here. Every word in an always-on kit
is read on every task, and a kit that grows past a page or two is paid for
continuously.

### The honest status of this area

| Claim | Reality |
|---|---|
| "`AGENTS.md` is a standard" | A convention, and a recent one. Filenames vary by tool |
| "Skills are portable between tools" | Partly. The formats differ |
| "A kit replaces a contributing guide" | No. A human guide explains why; a kit instructs |
| "More context is better" | No. Always-on context is a recurring cost |

Present this internally as a cheap, high-return convention rather than as
settled practice, because it is moving fast and a claim of standardisation will
be challenged by someone who read a different blog post last week.

## How to talk about it

**What a competent answer sounds like.** Lead with derivation and with
prohibitions, because both signal you have shipped one. "I derive the kit from
what CI enforces rather than writing it from memory, so every rule in it has a
gate behind it and every gate is documented. Then I test the kit against the
validators in both directions: a value the kit lists that the validator rejects,
and a value the validator accepts that the kit omits. And the section that
earns the most is the prohibitions, because the costly failures are all an agent
widening a constraint to get a green build: adding an audience value, marking a
sample skip, editing the lint rules."

**The follow-up is "how do you know the kit is working",** and the honest answer
is review comments. Count the repeated notes on agent pull requests before and
after. If the same four comments keep appearing, those four things are either
missing from the kit or stated ambiguously in it, and that count is the only
real feedback signal available. There is no eval set for a context kit yet,
which is worth admitting.

**The tradeoff to volunteer.** An always-on kit is a recurring cost paid on every
task, so it competes directly with the work. A thorough kit that covers every
convention crowds out the actual problem, and the failure mode is subtle: the
agent follows all your conventions and does the task badly. That tension is why
the split between always-on kits and on-demand skills exists, and why a kit
should be ruthlessly short. There is also a real risk of a kit becoming a
second source of truth that drifts from the validators, which is what step 3
exists to prevent and what nobody builds.

**One sharper point.** The strongest observation is that **a context kit is the
tribal-knowledge extraction problem with a new consumer.** The four repeated
review comments are exactly what
[extracting tribal knowledge](sme-interviews.md) is about, and the output form
happens to be a file an agent reads rather than a decision guide a person reads.
The skill is the same: notice what recurs, find the decision behind it, and
write the thing that stops the question. Framing it that way makes it
continuous with the documentation craft rather than a new AI discipline, which
is both more accurate and more reassuring to a documentation lead.

## How to prove it

**The artifact.** A kit with a prohibitions section, and the test that checks it
against the validators in both directions.

**Three things to do, in order:**

1. **Run the golden path, including step 4.** The bidirectional drift test is
   the part nobody builds: an undocumented validator value and a kit promising a
   deleted command both fail it.
2. **Write a kit for a repository you know, derived from its CI.** Read the
   workflow file first. Any rule you cannot point at a gate for either needs a
   gate or does not belong.
3. **Count the repeated review comments** on the last ten pull requests in any
   repository. The ones that recur are your kit's contents, and the count is
   your before number. If no comment recurs across ten pull requests, either
   the reviews are not about conventions or nobody is reviewing: both are
   findings, and neither produces a kit.

**What makes it credible rather than decorative.** An `AGENTS.md` file proves you read about the
convention. One derived from the CI gates, with explicit prohibitions against
widening constraints, and a test that fails when a validator and the kit
disagree, demonstrates that you treated it as documentation with a consumer
that cannot ask questions.

### How this would be demonstrated elsewhere

No agent ran here. This page describes packaging instructions so an agent
behaves consistently, and the demonstration needs an agent that loads such
packages, which this environment cannot provide.

**What you need.** An agent runtime that supports loading instruction bundles
from a directory, plus a repetitive task with a checkable result. The task
matters more than the runtime: the claim being tested is that a written-down
procedure makes an agent's behaviour repeatable, so you need something whose
output you can compare run to run.

**What you would run.** Choose a task your team does by hand, such as adding a
conforming page or preparing a release note, and run it three ways: with no
instructions, with instructions written as prose, and with instructions written
as a skill package including the validator the task has to satisfy. Ten runs of
each.

**What you would see.**

| Observation | Rough magnitude | What it tells you |
|---|---|---|
| Runs passing the validator, no instructions | low and highly variable | The baseline |
| Same, with prose instructions | better, still variable | Instructions help and do not bind |
| Same, with the validator named in the package | high and stable | The gain is the *check*, not the prose |
| Variance across runs | falls sharply with the package | Repeatability is the actual product |
| Behaviour on a case the package does not cover | reverts to baseline | The edges are where packages end |

The third row is the finding. Most of the improvement comes from telling the
agent what will be checked rather than from telling it what to do, which is the
same result the [templates and scaffolding](templates-scaffolding.md) page
reached for human authors and for the same reason.

**How you would know it had failed.** No variance at the baseline means the
task is too easy to discriminate between conditions. A package that improves
results on tasks it does not mention means something else changed, usually
context length. And if the package's own instructions are not reflected in the
output at all, check that the runtime loaded it, which is the commonest and
least interesting failure.

## Related

- [Model Context Protocol](mcp.md), the on-demand half
- [Agentic workflows](agentic-workflows.md), what agents do once oriented
- [Templates and scaffolding](templates-scaffolding.md), the same conventions as a generator
- [Extracting tribal knowledge](sme-interviews.md), where the kit's contents come from
