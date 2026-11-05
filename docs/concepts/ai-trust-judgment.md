---
title: Judging where AI can be trusted
summary: Deciding which content tasks an LLM can own, which it can draft, and which it must never touch.
diataxis: explanation
audience: developer
concept: ai-trust-judgment
tags: [craft, core]
---

# Judging where AI can be trusted

`core` · difficulty 2 · 4h

> sound judgment about where AI can be trusted

> Source: nvidia posting, verbatim

**Prerequisites:** [Prompting for content work](prompting.md)

## What it is

Deciding, per task, whether an LLM can own it, draft it for review, or must not
be used on it at all. The judgement rests on one question: **what does a wrong
output cost, and would anyone notice?**

It is a design skill rather than a prompting skill. The output is usually a
pipeline with a human in a specific place, not a better prompt.

## Why the job asks for it

NVIDIA asks for it twice, and the second instance is the more revealing one. The
qualification is "practical experience applying LLMs to content workflows
(prompting, retrieval and grounding, output evaluation) and sound judgment about
where AI can be trusted." The responsibility is "Automate the content lifecycle
with LLMs and scripting, from drafting and updating to auditing, with checks for
freshness, code accuracy, and terminology drift, **and human review where
judgment matters**."

That last clause is the job. They are not asking whether you can get an LLM to
write a page. They are asking where you would put the human, and that is a
question about failure cost, not about model capability.

On a Tuesday it is a sequence of small decisions that compound. You are
auditing 400 pages for stale version references. An LLM can find candidates
reliably and cannot decide which are actually wrong, so it proposes and you
dispose. Then someone suggests using it to generate the reference tables from the
source, and the right answer there is no. A reference table should be
*generated from the code*, deterministically. An LLM that is right 97 per cent
of the time on parameter defaults is a worse tool than mkdocstrings being
right every time.

That second decision is the one that distinguishes judgement from enthusiasm.
**The question is not "can the model do this", it is "is a model the right
mechanism".** A deterministic generator beats a reliable LLM wherever one is
available, and a great deal of documentation work has one available.

## The golden path

Classify a real set of content tasks by failure cost, then build the one that
sits in the interesting middle. Forty minutes.

**Step 1: the two axes that decide everything**

```bash
mkdir -p trust-drill && cd trust-drill
cat > axes.md <<'EOF'
                    WOULD ANYONE NOTICE A WRONG OUTPUT?

                        Yes, quickly        No, or not for months
                    +-------------------+-------------------------+
  COST   Low        |  LLM OWNS IT      |  LLM DRAFTS, YOU REVIEW |
  OF A              |                   |                         |
  WRONG  High       |  LLM DRAFTS,      |  DO NOT USE AN LLM      |
  OUTPUT            |  YOU REVIEW       |  (generate it instead)  |
                    +-------------------+-------------------------+
EOF
cat axes.md
```

The bottom-right cell is the one people get wrong. High cost plus invisible
failure is where an LLM is most dangerous and most tempting, because the output
looks right and nothing contradicts it.

**Step 2: classify real tasks**

```bash
cat > tasks.md <<'EOF'
| Task                                        | Cost | Noticed?   | Verdict |
|---------------------------------------------|------|------------|---------|
| Suggest a page title                        | low  | yes        | owns    |
| Draft a summary for front matter            | low  | yes        | owns    |
| Find pages mentioning a deprecated flag     | low  | yes        | owns    |
| Rewrite a paragraph for clarity             | low  | yes        | owns    |
| Propose which stale pages need review       | low  | yes        | owns    |
| Draft release notes from a changelog        | med  | yes        | drafts  |
| Write a how-to for a feature you know       | med  | yes        | drafts  |
| Audit 400 pages for terminology drift       | low  | no         | drafts  |
| Write a parameter reference table           | high | no         | NEVER   |
| State a default value                       | high | no         | NEVER   |
| Write a security instruction                | high | no         | NEVER   |
| Generate a runnable code sample             | high | yes (CI)   | drafts* |
| Decide what content to retire               | high | no         | NEVER   |
EOF
cat tasks.md
echo
echo "* drafts only because code-sample validation makes the failure visible."
echo "  Without that gate it belongs in the NEVER row."
```

That footnote is the whole idea: **a gate can move a task between cells.** Trust
is not a property of the task, it is a property of the task plus the checks
around it.

**Step 3: build the interesting one**

Terminology drift is low cost, invisible, high volume. That is the cell where an
LLM proposes and a human disposes, and where the design work is in making review
cheap.

```bash
mkdir -p docs
cat > docs/a.md <<'EOF'
# Getting started
Clone the repo and install the deps. The repo has a sample config.
EOF
cat > docs/b.md <<'EOF'
# Contributing
Fork the repository, then open a pull request against main.
EOF
cat > docs/c.md <<'EOF'
# Troubleshooting
If the PR build fails, check the repo settings and re-run the job.
EOF

cat > terms.yaml <<'EOF'
# The approved term, and the variants that should become it.
repository:
  - repo
  - repos
pull request:
  - PR
  - MR
  - merge request
EOF

cat > audit.py <<'PY'
"""Find terminology drift and emit a reviewable proposal, not an edit.

The LLM-shaped part of this task is judging whether a hit is really drift:
"PR" in prose is drift, "PR" inside a code block or a URL is not. This script
is the deterministic half, and it exists to make the human review cheap enough
to actually happen. That division is the point: automate the finding, keep the
deciding.
"""
import re
import sys
from pathlib import Path

import yaml


def main(docs: Path, terms_file: Path) -> int:
    terms = yaml.safe_load(terms_file.read_text(encoding="utf-8"))
    proposals = []

    for page in sorted(docs.glob("*.md")):
        lines = page.read_text(encoding="utf-8").splitlines()
        in_fence = False
        for number, line in enumerate(lines, 1):
            if line.strip().startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            for approved, variants in terms.items():
                for variant in variants:
                    if re.search(rf"\b{re.escape(variant)}\b", line):
                        proposals.append(
                            (page.name, number, variant, approved, line.strip())
                        )

    for name, number, variant, approved, text in proposals:
        print(f"{name}:{number}")
        print(f"  {variant!r} -> {approved!r}")
        print(f"  {text}")
        print("  [ ] accept   [ ] reject (quoting a UI label, a URL, or a proper noun)")
        print()

    print(f"{len(proposals)} proposals for review. Nothing has been changed.")
    return 0


if __name__ == "__main__":
    sys.exit(main(Path("docs"), Path("terms.yaml")))
PY
python3 audit.py
```

**Step 4: check that the design holds where it matters**

````bash
cat >> docs/c.md <<'EOF'

Run this:

```bash
# clone the repo first
gh repo clone example/widget
```
EOF
python3 audit.py | tail -3
echo
echo "The 'repo' inside the fenced block was not proposed. Fence awareness is"
echo "deterministic; asking a model to respect code blocks is not."
````

**What you built.** A pipeline that proposes and never edits, with a review line
per proposal and a reject reason prompted. The LLM's job in the full version is
pre-filtering the proposals it can tell are false positives, which reduces human
review without ever giving the model write access.

Note which half is deterministic. **Fence awareness is a parser's job**, and
handing it to a model would be choosing unreliability for no reason.

## Reference

### The decision, as four questions

| Question | If the answer is bad news |
|---|---|
| What does a wrong output cost? | Raise the review level |
| Would anyone notice, and how fast? | Invisible failure is the dangerous case |
| Is there a deterministic alternative? | Use it. This question outranks the others |
| Can a gate make the failure visible? | A gate can promote the task one cell |

The third question is the one that gets skipped. Before asking how to prompt
well, ask whether the task is a generation problem at all.

### Tasks by verdict

| Verdict | Tasks |
|---|---|
| **LLM owns it** | Title suggestions, summaries, clarity rewrites, finding candidates, classifying pages, proposing review queues |
| **LLM drafts, human disposes** | Release notes from a changelog, first drafts of how-tos, terminology audits, freshness triage, test-case generation |
| **Never an LLM** | Parameter references, default values, version requirements, security instructions, anything about data handling, retirement decisions, anything a generator can produce |

### Why "never" for the last group

Not squeamishness. Three specific reasons:

| Reason | Example |
|---|---|
| A deterministic generator exists and is exactly right | [Generated API reference](api-reference-generation.md) beats a 97-percent-accurate table |
| The failure is silent and expensive | A wrong default costs each reader an afternoon and nothing flags it |
| The failure is unbounded | A wrong security instruction is not a documentation defect |

### What makes a gate good enough to promote a task

| Gate | Promotes |
|---|---|
| [Code-sample validation](code-sample-validation.md) | Generated samples, from never to drafts |
| [Doc test harness](doc-test-harness.md) | Generated examples in prose |
| [Link checking](link-checking.md) | Generated cross-references |
| A human review queue with a reject reason | Any high-volume audit |
| [Evaluation sets](retrieval-evaluation.md) | Assistant answers, from unmeasured to measured |

A gate only counts if it **fails loudly and nobody can merge past it.** A gate
that produces a warning promotes nothing, because warnings are ignored.

### Where this judgement usually goes wrong

| Mistake | Consequence |
|---|---|
| Asking an LLM for facts a generator could produce | Confident, occasionally wrong reference |
| Trusting a task because the output reads well | Fluency is uncorrelated with accuracy |
| Review with no reject reason | Reviewers accept everything by the fortieth item |
| No sampling after the pipeline is trusted | Model or prompt changes silently degrade it |
| Treating "the model is better now" as a reason to remove the human | The failure cost did not change |

## How to talk about it

**What a competent answer sounds like.** Lead with a refusal, because the
refusals are the evidence of judgement. "I use an LLM to find candidate pages
for a terminology audit and to pre-filter the false positives, with a human
accepting each change. I do not use one to write parameter tables, because
mkdocstrings generates them from the signatures and is right every time. A
model that is right 97 percent of the time on defaults is a worse tool than a
generator, even though it is more impressive."

**The follow-up is "what about now that models are better",** and it is a real
question rather than a trap. The answer is that model capability changes which
cell a task sits in on the *cost* axis, slowly, and changes nothing about the
visibility axis. The reason not to generate a default value is not that the
model cannot usually get it right. It is that when it is wrong, nothing in the
system disagrees with it. That property is about the pipeline, not the model, so
it does not improve with the model.

**The tradeoff to volunteer.** Every human review step you add is a step that
will be skipped under deadline pressure, and a review queue nobody works is
worse than no automation, because the proposals accumulate and the corpus looks
audited. So the design constraint is not "where should a human review" but
"where can a human review *cheaply enough that they will*". That is why the
golden path's script prints a reject reason prompt: a reviewer who has to think
about why rejects less carelessly, and a reviewer facing 400 undifferentiated
proposals accepts all of them.

**One sharper point.** The strongest version of this judgement is that **an LLM is
the right tool for tasks where the output is a proposal and the wrong tool for
tasks where the output is a fact.** Proposals are cheap to reject; facts are
expensive to be wrong about and nothing rejects them. Almost every good
LLM-in-documentation design turns a fact-production task into a
proposal-production task, and almost every bad one does the reverse.

## How to prove it

**The artifact.** A pipeline with the human in a documented place, and a written
list of tasks you decided not to automate, with reasons. The second half is
rarer and more convincing.

**Three things to do, in order:**

1. **Classify twenty real content tasks** on the two axes. An hour. The output
   is a table you can show, and the "never" rows are the interesting part.
2. **Build the proposal pipeline from the golden path** against a real corpus,
   with a real term list. Measure how many proposals a reviewer accepts; if it
   is above 95 percent your filter is too loose and the review is theatre.
3. **Write down one thing you refused to automate and why.** One paragraph. This
   is the single most direct answer to NVIDIA's "sound judgment" line, and
   almost nobody brings one.

**What makes it credible rather than decorative.** Enthusiasm about LLMs is universal and worthless as
a signal. A candidate who says "I would not use a model for that, here is the
generator I would use instead" is demonstrating exactly the thing the posting
asks for, and it is a short sentence that is very hard to fake.

### How this would be demonstrated elsewhere

This is the only concept on the curriculum whose demonstration is a record of
being wrong, which is why it has none here: the project has no accumulated
history of predictions against outcomes.

**What you need.** No special tooling. A model, a log, and several months. The
instrument is a written prediction made *before* each delegated task, which is
the part that cannot be reconstructed afterwards and the reason this cannot be
demonstrated retrospectively.

**What you would run.** Before handing any task to a model, write down one line:
what you expect it to get right, what you expect to have to fix, and how you
will check. Afterwards, record what actually happened. Thirty entries is enough
to be interesting.

```
task                       predicted            actual               checked by
draft the API reference     structure ok,       structure ok,        validator
                            names wrong          two names invented
```

**What you would see.**

| Pattern | What it tells you |
|---|---|
| Tasks you predicted well | Where your model of the tool is calibrated |
| Tasks it did better than predicted | Where you are over-reviewing, and paying for it |
| Tasks it did worse | The real boundary, which is narrower than the discourse suggests |
| Tasks you could not check | The actual danger: not inaccuracy, unverifiability |
| Drift over months | Whether your judgment is updating or hardening |

The fourth row is the one worth the exercise. The decisive question is almost
never "can the model do this" but "if it does it wrong, will I notice", and a
prediction log makes that visible in a way no benchmark does. Tasks whose output
you cannot verify are the ones to refuse regardless of how capable the tool
looks.

**How you would know it had failed.** A log where you were right every time is
a log written afterwards; genuine prediction produces surprises at a decent
rate. A log with no refusals means the judgment is not being exercised, only
the tool. And if every entry's check is "I read it and it looked fine", the
exercise has recorded confidence rather than accuracy, which is the thing it
exists to distinguish.

## Related

- [Prompting for content work](prompting.md), the mechanics
- [Output evaluation](output-evaluation.md), how you know it is working
- [LLMs in the content lifecycle](llm-content-lifecycle.md), where this gets applied
- [Hallucination and guardrails](hallucination-guardrails.md), the failure mode
- [Generated API reference](api-reference-generation.md), the deterministic alternative
