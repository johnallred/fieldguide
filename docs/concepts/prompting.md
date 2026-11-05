---
title: Prompting for content work
summary: Writing instructions for a model the way you would write a spec for a contractor, and checking the output the same way.
diataxis: explanation
audience: developer
concept: prompting
tags: [ai, core]
---

# Prompting for content work

`core` · difficulty 2 · 3h

> Practical experience applying LLMs to content workflows (prompting, retrieval and grounding, output evaluation)

> Source: nvidia posting, verbatim

**Leads to:** [Judging where AI can be trusted](ai-trust-judgment.md), [LLMs in the content lifecycle](llm-content-lifecycle.md)

## What it is

Writing the instruction that produces a usable output on a content task:
drafting, auditing, classifying, rewriting. For documentation work the prompt is
usually part of a script rather than a conversation, which changes what good
looks like: it has to work on the four hundredth input as well as the first.

## Why the job asks for it

NVIDIA lists it first in a three-part requirement: "prompting, retrieval and
grounding, output evaluation". The ordering is the pipeline, and prompting is
the part people think is the whole thing.

What makes it `core` in a documentation role rather than a general skill is the
shape of the task. **You are almost never writing a prompt for one output.** You
are writing a prompt that will run over 400 pages in a batch, where you will
review a sample and accept the rest. That changes every decision: consistency
matters more than peak quality, the output format has to be machine-parseable,
and the prompt needs to be able to say "no finding here" without being pushed
into inventing one.

On a Tuesday it is a specific failure. You ask a model to flag pages whose
examples use a deprecated API. It returns a finding for every page, because
nothing in the prompt made "nothing wrong with this page" an acceptable answer,
and a model asked to find problems will find problems. **The fix is in the
prompt, not the model**, and knowing that is the difference between a usable
audit and 400 false positives.

## The golden path

Write a prompt for a real content task, then break it four ways and fix each.
Thirty-five minutes. No API key: the exercise is the prompt text and a mock
model that exposes each flaw.

**Step 1: the task, and the naive prompt**

```bash
mkdir -p prompt-drill && cd prompt-drill
cat > v1.txt <<'EOF'
Review this documentation page and tell me what is wrong with it.
EOF
cat v1.txt
```

That prompt has four defects, and they are the four that matter.

**Step 2: name them before fixing them**

```bash
cat > defects.md <<'EOF'
| Defect                 | What it causes at scale                          |
|------------------------|--------------------------------------------------|
| No definition of wrong | Every reviewer, human or model, invents criteria |
| No output format       | Unparseable. You cannot aggregate 400 of these   |
| No null answer         | "Nothing is wrong" is not an option, so it finds |
|                        | something. This is the expensive one             |
| No grounding rule      | It will comment on things not in the page        |
EOF
cat defects.md
```

**Step 3: the fixed prompt**

```bash
cat > v2.txt <<'EOF'
You are auditing one documentation page for a specific, closed set of defects.

Report ONLY these defect types:
  stale_version   a version number or requirement that contradicts the
                  `requires` field in the page's front matter
  no_example      a how-to page with no code block
  hedge           the words "simply", "just", "easy", or "should" used to
                  describe what the software does
  undefined_term  a term in backticks that the page never defines and does
                  not link to

Rules:
- Report a defect ONLY if you can quote the exact text from the page that
  demonstrates it. If you cannot quote it, do not report it.
- If the page has none of these defects, return an empty findings list. An
  empty list is a correct and expected answer.
- Do not comment on anything outside the list above. Do not suggest
  improvements. Do not rate the page.

Return JSON only, no prose, matching exactly:

{"findings": [{"type": "<one of the four>", "quote": "<exact text from the page>", "line_hint": "<the heading it appears under>"}]}

Page:
---
{page}
---
EOF
wc -l v2.txt
```

**Step 4: test it against the four failures with a mock model**

The mock is not a toy. It encodes the four ways a real model fails on this task,
so you can see which ones the prompt closes.

````bash
mkdir -p docs
cat > docs/good.md <<'EOF'
---
title: Rotate a key
requires: widget>=2.4
kind: how-to
---
# Rotate a key

Run the rotation command.

```bash
widget keys rotate
```
EOF

cat > docs/bad.md <<'EOF'
---
title: Configure caching
requires: widget>=2.4
kind: how-to
---
# Configure caching

Simply set the `cache_mode` flag. It should work on widget 1.9 or newer.
EOF

cat > mock.py <<'PY'
"""A mock model that fails the way real ones do on audit tasks.

Four behaviours, each switchable, so the prompt can be tested against them
without an API key:

  invents     reports a finding on a clean page (no null answer allowed)
  rambles     wraps the JSON in prose (no format discipline)
  ungrounded  reports a defect it cannot quote from the page
  disciplined obeys a prompt that closes all three holes

The point is not that this mock is realistic in detail. It is that each
behaviour maps to a prompt defect, so you can see which clause prevents
which failure.
"""
import json
import re
import sys
from pathlib import Path

HEDGES = ("simply", "just", "easy", "should")


def disciplined(page: str) -> str:
    findings = []
    front = page.split("---")[1] if page.startswith("---") else ""
    requires = re.search(r"requires:\s*\S+?>=([\d.]+)", front)
    body = page.split("---", 2)[-1]

    for hedge in HEDGES:
        match = re.search(rf"\b{hedge}\b", body, re.I)
        if match:
            sentence = re.search(rf"[^.]*\b{hedge}\b[^.]*\.", body, re.I)
            findings.append({
                "type": "hedge",
                "quote": (sentence.group(0) if sentence else match.group(0)).strip(),
                "line_hint": "body",
            })
    if requires:
        for version in re.findall(r"widget (\d+\.\d+)", body):
            if version < requires.group(1):
                sentence = re.search(rf"[^.]*widget {re.escape(version)}[^.]*\.", body)
                findings.append({
                    "type": "stale_version",
                    "quote": (sentence.group(0) if sentence else version).strip(),
                    "line_hint": "body",
                })
    if "kind: how-to" in front and "```" not in body:
        findings.append({"type": "no_example", "quote": "", "line_hint": "whole page"})
    return json.dumps({"findings": findings})


def invents(page: str) -> str:
    return json.dumps({"findings": [
        {"type": "unclear", "quote": "the page could be clearer", "line_hint": "intro"}
    ]})


def rambles(page: str) -> str:
    inner = disciplined(page)
    return (
        "Sure! I reviewed the page. Here is what I found:\n\n"
        f"```json\n{inner}\n```\n\n"
        "Let me know if you would like me to suggest improvements!"
    )


def ungrounded(page: str) -> str:
    return json.dumps({"findings": [
        {"type": "stale_version", "quote": "requires widget 1.2", "line_hint": "body"}
    ]})


MODES = {"invents": invents, "rambles": rambles,
         "ungrounded": ungrounded, "disciplined": disciplined}


def parse(raw: str, page: str):
    """Parse a response the way a batch job must: strictly, then report why."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None, "not JSON (prose or fences around it)"
    if "findings" not in data:
        return None, "no findings key"

    kept, dropped = [], []
    for finding in data["findings"]:
        if finding["type"] not in ("stale_version", "no_example", "hedge", "undefined_term"):
            dropped.append((finding, "type not in the closed set"))
        elif finding["quote"] and finding["quote"] not in page:
            dropped.append((finding, "quote not found in the page"))
        else:
            kept.append(finding)
    return (kept, dropped), None


for name in sorted(Path("docs").glob("*.md")):
    page = name.read_text()
    print(f"\n=== {name.name} ===")
    for mode in ("invents", "rambles", "ungrounded", "disciplined"):
        raw = MODES[mode](page)
        result, error = parse(raw, page)
        if error:
            print(f"  {mode:<12} REJECTED: {error}")
            continue
        kept, dropped = result
        detail = ", ".join(f["type"] for f in kept) or "none"
        note = f"  ({len(dropped)} dropped: {dropped[0][1]})" if dropped else ""
        print(f"  {mode:<12} {len(kept)} finding(s): {detail}{note}")
PY
python3 mock.py
````

**What you built.** A prompt with a closed defect set, a required quote, an
explicit null answer and a strict output format, plus a harness that shows what
each clause prevents.

Read the output carefully, because each failure is caught by a *different*
clause and that mapping is the lesson.

| Mode | Result | What caught it |
|---|---|---|
| `invents` | 0 findings, 1 dropped | **The closed set.** It reported type `unclear`, which is not one of the four |
| `rambles` | rejected | **The format rule.** Prose and code fences around the JSON make it unparseable |
| `ungrounded` | 0 findings, 1 dropped | **The quote rule.** It fabricated `requires widget 1.2`, which is not in the page |
| `disciplined` | 4 on `bad.md`, **0 on `good.md`** | nothing; it is correct |

The last cell is the one to notice. On the clean page the disciplined mode
returns an empty list, which is only possible because the prompt says an empty
list is a correct answer. Every other mode returns something on every page.

And the broader lesson: **three of the four failures were caught by validating
the output, not by improving the prompt.** The prompt reduces them; the
validator is what makes a 400-page batch safe. That is the same division of
labour as [judging where AI can be trusted](ai-trust-judgment.md).

## Reference

### The five clauses a content prompt needs

| Clause | Prevents |
|---|---|
| A closed set of categories | Invented categories you cannot aggregate |
| A required quote from the source | Fabrication, which is the expensive failure |
| An explicit null answer | A finding on every input |
| A strict output format | Unparseable results in a batch |
| An explicit "do not" list | Helpful additions you did not ask for |

### Why the null answer matters most

A model asked to find problems finds problems. On an audit over 400 pages, a
prompt without an explicit empty-list instruction produces a near-100 percent
finding rate, a reviewer who accepts everything by page forty, and a corpus that
looks audited and is not.

One sentence fixes it: *"If the page has none of these defects, return an empty
findings list. An empty list is a correct and expected answer."*

### Patterns worth knowing

| Pattern | Use |
|---|---|
| Closed vocabulary in the prompt | Classification into your [taxonomy](taxonomy.md) |
| Quote-or-drop | Any audit or extraction task |
| Few-shot with a null example | When the empty case keeps getting missed; show it |
| Chain of custody | Ask for the source line, then validate it mechanically |
| Two-pass propose-then-filter | High-volume audits; cheap model proposes, you filter |
| Rubric in the prompt | Review tasks, so judgements are comparable across runs |
| Refuse-if-unsure | "If you cannot determine this from the text, say unknown" |

### What not to ask a model to do

| Task | Why not |
|---|---|
| State a default value | A [generator](api-reference-generation.md) is right every time |
| Write a parameter table | Same |
| Decide what to retire | Irreversible, and the failure is invisible |
| Write security instructions | Unbounded failure cost |
| Confirm that a page is accurate | It has no access to the implementation |

See [judging where AI can be trusted](ai-trust-judgment.md) for the decision
procedure behind that table.

### Operational details that matter in a batch

| Detail | Why |
|---|---|
| Pin the model version | A model update silently changes the output distribution |
| Set temperature to 0 for classification | Reproducibility; you will rerun this |
| Store the prompt in version control, not in a notebook | It is code, and it changes behaviour |
| Log the prompt version with every output | You will need to know which prompt produced a finding |
| Sample and review after you start trusting it | Quality drifts, and nothing tells you |

## How to talk about it

**What a competent answer sounds like.** Lead with the null answer, because it is
the clause that shows you have run a batch rather than written a prompt. "On an
audit prompt the clause that matters most is telling the model that an empty
findings list is a correct answer. Without it, a model asked to find problems
finds one on every page, and by page forty your reviewer is accepting
everything. The second is requiring a verbatim quote from the source, which I
then check mechanically: if the quoted text is not in the page, the finding is
dropped before a human ever sees it."

**The follow-up is "how do you know the prompt is good",** and the answer is that
you do not know from reading it. You need a small labelled set: twenty pages you
have reviewed yourself, with the defects you expect, scored for precision and
recall. That is [output evaluation](output-evaluation.md) and it is the only way
to tell a prompt improvement from a coincidence. Anyone who answers this
question by describing their prompt rather than their measurement has not run
one at scale.

**The tradeoff to volunteer.** Every clause you add constrains the model, and
over-constraining produces a different failure: a prompt with a tightly closed
defect set will miss real problems that fall outside it, confidently and
silently. The quote-or-drop rule has the same shape, since a genuine defect that
is structural rather than textual, like a missing section, has no quote and gets
dropped. So the closed set has to be revisited as you learn what it misses, and
a prompt that has not changed in six months is probably missing things rather
than being finished.

**One sharper point.** The strongest framing is that **a prompt is a specification,
and the clauses that make it work are the clauses that make any specification
work**: define the terms, state the acceptance criteria, say what is out of
scope, and require evidence for claims. That is why documentation people are
often good at this: you already write specifications for human contractors and
already know that "tell me what's wrong with it" is a bad brief. Saying that
connects the LLM work to the craft rather than treating it as a separate skill,
which is exactly how NVIDIA's posting frames the whole role.

## How to prove it

**The artifact.** A prompt in version control, with the labelled set you scored
it against, and the validator that drops ungrounded findings.

**Three things to do, in order:**

1. **Run the golden path.** The four-mode mock shows which clause closes which
   failure, and the quote-check dropping a fabricated finding is the convincing
   moment.
2. **Build a twenty-page labelled set** for one real audit task and score
   precision and recall. Twenty is enough to catch a prompt that finds
   something on everything. Predict both numbers before you score. Precision
   is the one that surprises people, because a prompt that finds everything
   looks like it is working.
3. **Write the validator before the prompt is good.** The quote-must-appear
   check is ten lines and it catches fabrication regardless of which model or
   prompt you end up with. Shipping the validator first is the move that shows
   judgement.

**What makes it credible rather than decorative.** Showing a prompt proves nothing; everyone has
prompts. A prompt plus a labelled set plus a mechanical grounding check plus a
precision number, including the version where precision was bad, demonstrates
that you treated it as engineering.

### How this would be demonstrated elsewhere

No model ran here, so every prompt comparison on this page is reasoning. The
demonstration is unusually easy to set up and unusually easy to fool yourself
with, which is why the failure signatures below matter more than the procedure.

**What you need.** Any model you can call repeatedly, and a task with a
checkable answer. That second requirement is the whole difficulty: prompting
demonstrations are usually run on tasks whose output can only be judged by
reading it, which is how everyone concludes their favourite prompt is best.

**What you would run.** Pick a content task with a mechanical check, such as
"rewrite this page's front matter to the content model" where a validator can
score it, or "extract every flag name from this reference page" where the true
list is known. Then run three or four prompt variants, twenty inputs each, and
score with the validator rather than by eye.

```python
for variant in VARIANTS:
    scores = [validate(model.generate(variant.format(page=p))) for p in pages]
```

**What you would see.**

| Observation | Rough magnitude | What it tells you |
|---|---|---|
| Spread between the best and worst variant | 10 to 40 points | Prompting is worth measuring |
| Spread between two runs of the *same* variant | several points | Why single-run comparisons are noise |
| Effect of adding one worked example | usually the largest single gain | Examples beat instructions |
| Effect of adding three more examples | small | Where the returns stop |
| Effect of asking for a format you then parse | large, and brittle | Format compliance is its own metric |
| Effect of politeness, persona, emphasis | within noise | The things people tune hardest |

The second row disciplines everything else. If two runs of one prompt differ by
five points, then a five-point difference between two prompts is not a finding,
and most published prompt advice is built on exactly that size of difference
measured once.

**The measurement that changes how you work.** Run your current best prompt
twenty times on one input and record the variance. That single number tells you
how large a difference has to be before you are allowed to believe it, and it is
the measurement nobody takes before redesigning a prompt.

**How you would know it had failed.** Zero variance across runs means
temperature is pinned and you are measuring one sample repeatedly, which is
fine for regression testing and useless for comparison. A validator that passes
every output means it is too lenient to rank anything. And if the best variant
changes every time you re-run the comparison, the spread is smaller than the
noise and the honest answer is that the variants are equivalent.

## Related

- [Judging where AI can be trusted](ai-trust-judgment.md), which tasks to give a model at all
- [Output evaluation](output-evaluation.md), how to tell whether a prompt improved
- [LLMs in the content lifecycle](llm-content-lifecycle.md), where these prompts run
- [Grounding and citation](grounding.md), the same discipline applied to answers
