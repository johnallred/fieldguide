---
title: Output evaluation
summary: Scoring generated text against labelled examples, so a prompt change is a measurement rather than a feeling.
diataxis: explanation
audience: developer
concept: output-evaluation
tags: [ai, core]
---

# Output evaluation

`core` · difficulty 3 · 6h

> Practical experience applying LLMs to content workflows (prompting, retrieval and grounding, output evaluation)

> Source: nvidia posting, verbatim

**Prerequisites:** [Grounding and citation](grounding.md), [Retrieval evaluation](retrieval-evaluation.md)

**Leads to:** [Measuring AI answer quality](ai-answer-quality.md), [Hallucination and guardrails](hallucination-guardrails.md)

## What it is

Scoring generated text against examples you labelled yourself, so that a change
to a prompt or a model produces a number instead of an impression.

[Retrieval evaluation](retrieval-evaluation.md) asks whether the right page came
back. This asks whether the text produced from it was any good, which is a
harder question because there is no single correct output to compare against.

## Why the job asks for it

NVIDIA lists it third in the required triple: "prompting, retrieval and
grounding, output evaluation". The ordering is the pipeline, and this is the
stage that tells you whether the first two worked.

What makes it `core` and difficulty 3 is that it has no obvious answer key.
Retrieval has one: the expected page is either in the results or it is not.
A generated paragraph can be correct, incomplete, correct-but-unhelpful, or
subtly fused, and **"does this read well" is not a measurement.** Building the
answer key is most of the work, and it is work most teams skip, which is why
every prompt change in this field is justified by somebody having tried five
examples.

On a Tuesday it is the thing that stops a bad change shipping. Somebody tightens
the audit prompt to reduce false positives. On the three pages they tried, it
looks better. Across the labelled set, precision held at 1.00 and recall fell from
1.00 to 0.43, which means the audit now misses eight of the fourteen real
defects while every finding it does report is correct.

**Only one of those two numbers is observable by reviewing the output**, which
is why the labelled set exists.

## The golden path

Build a labelled set, score two prompt versions against it, and find the
tradeoff that eyeballing hides. Fifty minutes, dependency-free.

**Step 1: the task and the labels**

The labels are the expensive part and the whole asset. Label by hand, record
why, and never let a model generate them.

```bash
mkdir -p outeval-drill && cd outeval-drill
cat > labelled.yaml <<'EOF'
# The answer key: ten pages, each with the defects a human found by reading.
#
# Rules that keep this usable:
#   - Labelled by a person, recorded with a quote. A model-labelled set
#     measures agreement with that model, not correctness.
#   - Includes CLEAN pages. A set of only defective pages cannot measure
#     false positives, which is the failure that destroys trust in an audit.
#   - `notes` says why a case is interesting, so nobody deletes a hard one.

- page: p01
  text: "Simply set the cache_mode flag. It should work on widget 1.9 or newer."
  requires: "2.4"
  kind: how-to
  defects: [hedge, hedge, stale_version, no_example]
  notes: >
    Two hedges, a version older than the requirement, and no example:
    `cache_mode` is a flag name in backticks, not a command.

- page: p02
  text: "Run `widget keys rotate` to rotate the signing key."
  requires: "2.4"
  kind: how-to
  defects: []
  notes: >
    Clean. A set without clean pages cannot measure precision at all. The
    inline `widget keys rotate` counts as an example: it is a runnable
    command, not an identifier.

- page: p03
  text: "Configure the pool size. This is easy to get wrong."
  requires: "2.4"
  kind: how-to
  defects: [hedge, no_example]
  notes: A how-to with no code block at all.

- page: p04
  text: "The scheduler uses a work-stealing queue to balance shots across nodes."
  requires: "2.4"
  kind: explanation
  defects: []
  notes: Clean, and NOT a no_example defect because it is an explanation page.

- page: p05
  text: "Just pass --force. Requires widget 2.0 or newer."
  requires: "2.4"
  kind: how-to
  defects: [hedge, stale_version, no_example]
  notes: Three defects in two sentences.

- page: p06
  text: "Set `batch_size` to 1 for latency-sensitive endpoints.\n```\nbatch_size = 1\n```"
  requires: "2.4"
  kind: how-to
  defects: []
  notes: Clean how-to with an example. The easy true negative.

- page: p07
  text: "You should see the server start within ten seconds."
  requires: "2.4"
  kind: how-to
  defects: [hedge, no_example]
  notes: >
    "should" here describes an EXPECTATION of observed behaviour, not an
    uncertain claim about the software. A strict hedge rule flags it; a human
    might not. Deliberately ambiguous, kept to expose the disagreement.

- page: p08
  text: "Deployment requires widget 2.6 or newer and a running Redis."
  requires: "2.4"
  kind: reference
  defects: []
  notes: 2.6 is NEWER than the requirement, so it is not stale. Tests direction.

- page: p09
  text: "This simply works out of the box on widget 1.0."
  requires: "2.4"
  kind: explanation
  defects: [hedge, stale_version]
  notes: An explanation page, so no_example must not fire.

- page: p10
  text: "Pass `--dry-run` first.\n```\nwidget apply --dry-run\n```\nIt is easy to verify."
  requires: "2.4"
  kind: how-to
  defects: [hedge]
  notes: Has an example; only the hedge should fire.
EOF
python3 -c "
import yaml
cases = yaml.safe_load(open('labelled.yaml'))
clean = sum(1 for c in cases if not c['defects'])
total = sum(len(c['defects']) for c in cases)
print(f'{len(cases)} pages, {clean} clean, {total} labelled defects')
assert clean >= 3, 'need clean pages to measure precision'
assert all(c.get('notes') for c in cases), 'every case needs notes'
print('set is usable')
"
```

**Step 2: two auditors, standing in for two prompt versions**

```bash
cat > auditors.py <<'PY'
"""Two auditors, standing in for two versions of an audit prompt.

LOOSE   flags every hedge word anywhere. High recall, flags p07's "should"
        where a human might not.
STRICT  someone tightened it to reduce false positives: it only flags a
        hedge when it describes the SOFTWARE's behaviour, and it stopped
        checking versions it cannot parse confidently.

The point is that `strict` looks better on the pages a person would spot
check, and is worse where it matters. A deterministic stand-in keeps that
reproducible; a real prompt change produces the same shape of result.
"""
import re

HEDGES = ("simply", "just", "easy", "should")
SOFTWARE_HEDGE = re.compile(r"\b(it|this|the \w+)\s+(should|simply)\b", re.I)

#: An inline code span containing a space, or starting with the tool name, is
#: a command. A single identifier in backticks (`cache_mode`) is a flag name
#: and is not an example of anything.
#:
#: This definition exists because the first run of this harness disagreed with
#: the answer key on two pages, and the investigation found that `no_example`
#: had never been defined precisely enough to label against. See the page.
INLINE_COMMAND = re.compile(r"`([^`]*\s[^`]*|widget[^`]*)`")


def _has_example(text):
    return "```" in text or bool(INLINE_COMMAND.search(text))


def loose(case):
    """Flag every hedge; check every version; require an example on how-tos."""
    found = []
    text = case["text"]
    for hedge in HEDGES:
        found += ["hedge"] * len(re.findall(rf"\b{hedge}\b", text, re.I))
    for version in re.findall(r"widget (\d+\.\d+)", text, re.I):
        if _older(version, case["requires"]):
            found.append("stale_version")
    if case["kind"] == "how-to" and not _has_example(text):
        found.append("no_example")
    return found


def strict(case):
    """Tightened: hedges only when describing the software, versions skipped."""
    found = []
    text = case["text"]
    found += ["hedge"] * len(SOFTWARE_HEDGE.findall(text))
    # The tightening that does the damage: version checking was dropped
    # because it produced "false positives" on p08, where 2.6 is newer.
    if case["kind"] == "how-to" and not _has_example(text):
        found.append("no_example")
    return found


def _older(found, required):
    return tuple(int(x) for x in found.split(".")) < tuple(
        int(x) for x in required.split(".")
    )


AUDITORS = {"loose": loose, "strict": strict}
PY
echo "auditors written"
```

**Step 3: score both, as sets of defects per page**

```bash
cat > score.py <<'PY'
"""Score each auditor against the labelled set.

Multiset comparison, not set comparison: a page with two hedges and an
auditor that finds one is a partial miss, and collapsing to a set would call
it a complete hit.
"""
import sys
from collections import Counter

import yaml

from auditors import AUDITORS


def confusion(cases, auditor):
    tp = fp = fn = 0
    per_type = {}
    for case in cases:
        expected = Counter(case["defects"])
        found = Counter(auditor(case))
        for defect in set(expected) | set(found):
            e, f = expected[defect], found[defect]
            hit, over, under = min(e, f), max(0, f - e), max(0, e - f)
            tp += hit
            fp += over
            fn += under
            bucket = per_type.setdefault(defect, [0, 0, 0])
            bucket[0] += hit
            bucket[1] += over
            bucket[2] += under
    return tp, fp, fn, per_type


def metrics(tp, fp, fn):
    precision = tp / (tp + fp) if tp + fp else 1.0
    recall = tp / (tp + fn) if tp + fn else 1.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return precision, recall, f1


def main():
    cases = yaml.safe_load(open("labelled.yaml"))
    results = {}

    for name, auditor in AUDITORS.items():
        tp, fp, fn, per_type = confusion(cases, auditor)
        precision, recall, f1 = metrics(tp, fp, fn)
        results[name] = (precision, recall, f1)

        print(f"\n=== {name} ===")
        print(f"  true positives {tp}, false positives {fp}, false negatives {fn}")
        print(f"  precision {precision:.2f}   recall {recall:.2f}   F1 {f1:.2f}")
        print("  by defect type:")
        for defect, (hit, over, under) in sorted(per_type.items()):
            p, r, _ = metrics(hit, over, under)
            print(f"    {defect:<14} precision {p:.2f}  recall {r:.2f}"
                  f"   (tp {hit}, fp {over}, fn {under})")

        # Per-page disagreements, which is where you look to fix a prompt.
        print("  pages where it disagreed with the labels:")
        any_diff = False
        for case in cases:
            expected, found = Counter(case["defects"]), Counter(auditor(case))
            if expected != found:
                any_diff = True
                missed = sorted((expected - found).elements())
                spurious = sorted((found - expected).elements())
                parts = []
                if missed:
                    parts.append(f"missed {missed}")
                if spurious:
                    parts.append(f"invented {spurious}")
                print(f"    {case['page']}: {', '.join(parts)}")
        if not any_diff:
            print("    none")

    print("\n" + "=" * 56)
    print(f"{'version':<10} {'precision':>10} {'recall':>8} {'F1':>7}")
    print("-" * 56)
    for name, (precision, recall, f1) in results.items():
        print(f"{name:<10} {precision:>10.2f} {recall:>8.2f} {f1:>7.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
PY
python3 score.py
```

**Step 4: see what a reviewer can and cannot observe**

A reviewer does not read the labelled set. They read the auditor's *findings*
and judge each one. That turns out to decide everything.

```bash
python3 - <<'PY'
"""What a human reviewing the OUTPUT can actually see.

A reviewer works through the findings the auditor produced. They can judge
every one of those. They cannot see a defect that was never flagged, because
nothing in their queue refers to it.
"""
from collections import Counter

import yaml

from auditors import AUDITORS

cases = yaml.safe_load(open("labelled.yaml"))

for name, auditor in AUDITORS.items():
    flagged = correct = missed = 0
    for case in cases:
        expected, found = Counter(case["defects"]), Counter(auditor(case))
        flagged += sum(found.values())
        correct += sum((found & expected).values())
        missed += sum((expected - found).values())

    apparent = correct / flagged if flagged else 1.0
    print(f"{name}:")
    print(f"  findings in the review queue      {flagged}")
    print(f"  of those, real                    {correct}")
    print(f"  apparent precision to a reviewer  {apparent:.2f}")
    print(f"  defects the reviewer NEVER SEES   {missed}")
    print()
PY
```

**What you built.** A labelled set with clean and ambiguous cases, precision and
recall overall and per defect type, the per-page disagreements, and a
demonstration of what review structurally cannot catch.

### What the measurement said

| version | precision | recall | F1 |
|---|---|---|---|
| loose | 1.00 | 1.00 | 1.00 |
| strict | 1.00 | **0.43** | 0.60 |

The tightened prompt kept perfect precision and **lost 57% of its recall.** It
finds 6 of 14 real defects. Per defect type, the damage is specific: hedge
recall fell from 1.00 to 0.29, and `stale_version` recall went to **zero**,
because the tightening dropped version checking entirely to avoid a false
positive on `p08`.

Now step 4, which is the part that matters:

| version | findings in the queue | real | apparent precision | never seen |
|---|---|---|---|---|
| loose | 14 | 14 | 1.00 | 0 |
| strict | 6 | 6 | 1.00 | **8** |

**Both look perfect to a reviewer.** Every finding in each queue is real, so a
reviewer working through either one concludes the auditor is excellent. One of
them is silently missing eight defects, and **nothing in the review queue
refers to a defect that was never flagged.**

That asymmetry is the entire argument for a labelled set. Human review can
measure precision, because false positives arrive in the queue and annoy
someone. Human review **cannot measure recall at any volume**, because a false
negative is an absence. Only an answer key sees it.

### Two things the first run found, which were wrong with the answer key

Worth recording, because this is the ordinary experience of building one.

The first run reported false positives on `p01` and `p02` for `no_example`, and
the auditor was right both times. `p01` was mislabelled: it is a how-to whose
only backticked text is `cache_mode`, a flag name, so it genuinely has no
example. And `no_example` had never been *defined* precisely enough to label
against: does an inline `` `widget keys rotate` `` count as an example? The
answer here is yes, a runnable command counts and a bare identifier does not,
and that definition is now in the auditor and in the case notes.

**A disagreement between the auditor and the answer key is not automatically an
auditor bug.** Roughly half the time, early on, it is the labels.

## Reference

### The metrics, and which failure each one hides

| Metric | Measures | Blind to |
|---|---|---|
| Precision | Of what it flagged, how much was real | Everything it missed |
| Recall | Of what was real, how much it flagged | Everything it invented |
| F1 | The harmonic mean | Which of the two moved |
| Per-type precision and recall | Where the prompt is weak | Nothing; this is the useful view |
| Accuracy | Overall correctness | Useless here: most pages are mostly clean |

**Never report F1 alone on a content task.** In the golden path above F1 fell
from 1.00 to 0.60, which correctly signals that something got worse but hides
*which* thing: precision was untouched and recall collapsed. A change in the
other direction, trading recall for precision, can leave F1 roughly flat. The
two outcomes are not interchangeable: a reviewer drowning in false positives stops reviewing,
and an audit that misses half the defects leaves a corpus that looks checked.
Which failure you prefer is a judgement about who pays, and you can only make it
if both numbers are on the table.

### Precision or recall, depending on the job

| Task | Prefer | Why |
|---|---|---|
| Audit with human review | **recall** | A human filters false positives; nothing recovers a miss |
| Automated fix with no review | **precision** | A wrong automated edit is a defect you introduced |
| Finding candidates for a backlog | **recall** | Cheap to discard, expensive to never see |
| Blocking a build | **precision** | A flaky gate gets disabled, and then nothing is checked |
| Answering a user | **precision** | A confident wrong answer is worse than a refusal |

### Building a labelled set that is worth having

| Rule | Why |
|---|---|
| Label by hand | A model-labelled set measures agreement with that model |
| Include clean cases, at least a third | Without them you cannot measure precision at all |
| Include deliberately ambiguous cases | They expose where humans disagree, which bounds the achievable score |
| Record a note per case | So nobody deletes a hard case for lowering the score |
| Keep it small and real | 20 to 50 cases from real content beats 500 synthetic |
| Never tune parameters against it | That makes it training data and the score meaningless |

The ambiguous cases matter more than they look. `p07` uses "should" to describe
expected behaviour rather than to hedge a claim, and two careful reviewers will
disagree about it. **That disagreement is the ceiling on your achievable
score**, and a set with no ambiguous cases will tell you an auditor is worse
than it is.

### Sample size, again

| Cases | One defect is worth | Honest resolution |
|---|---|---|
| 10 pages, ~15 defects | about 7 points | a very large difference only |
| 50 pages, ~70 defects | about 1.5 points | a few points |
| 200 pages, ~300 defects | 0.3 points | small differences |

A ten-page set catches a change that breaks something. It cannot support a
claim that precision improved by four points.

### What this cannot measure

| Not measured | Why | What to do |
|---|---|---|
| Whether the writing is good | No answer key exists | [Review](docs-review.md) by a person |
| Whether the page is accurate | Needs the implementation | [Read the code](reading-code-to-verify.md) |
| Whether readers succeeded | Needs an audience | [Time to first success](time-to-first-success.md) |
| Whether an answer is helpful | Partly subjective | Thumbs, then sample and read |

Two layers above this are worth naming. **LLM-as-judge** scales labelling by
having a model grade outputs against a rubric, and introduces a second model
whose agreement with humans you now have to measure, on a labelled set, which
is this concept again one level up. **Pairwise comparison** asks which of two
outputs is better, which humans do far more reliably than absolute scoring and
which is the right method when the task has no answer key at all.

## How to talk about it

**What a competent answer sounds like.** Lead with the tradeoff that eyeballing
hides. "I keep a hand-labelled set of pages, including clean ones, because
without clean cases you cannot measure precision at all. When someone tightened
our audit prompt, both versions looked perfect to a reviewer, because every
finding in both queues was real. Against the labelled set the tightened one had
dropped from 1.00 recall to 0.43: it was missing eight of fourteen defects, and
version checking had gone to zero. A reviewer can never see that, because
nothing in a review queue refers to a defect that was never flagged."

**The follow-up is "how do you label enough data",** and the honest answer has
two parts. You do not need much: twenty to fifty real pages is enough to catch a
regression, and it is the resolution rather than the count that you should be
honest about. And the way to grow it is to add a case every time a reviewer
rejects a finding, so the set accumulates from real disagreements rather than
from an afternoon of invention. If someone suggests having a model label the
set, that is LLM-as-judge, and it needs its own human-labelled set to validate
against, so it does not remove the labelling, it moves it.

**The tradeoff to volunteer.** A labelled set is a target, and the same
Goodhart problem as [retrieval evaluation](retrieval-evaluation.md) applies more
sharply here because prompts are so cheap to iterate. Sweep a few prompt
variants against the set and you have fitted the prompt to twenty pages and
learned nothing about the other four hundred. The discipline is to change the
prompt for a stated reason and then measure, never to search for a prompt that
scores well, and to hold back a few cases you do not look at.

**One sharper point.** The strongest thing to say is that **the ambiguous cases
set the ceiling, and most teams never find out what their ceiling is.** If two
careful reviewers disagree about `p07`, no prompt can score 1.0, and an
auditor hitting 0.85 might already be at the limit of the task. Measuring
inter-annotator agreement before optimising tells you whether you are chasing a
real gap or noise, and almost nobody does it. That observation separates someone
who has run an evaluation from someone who has read about metrics.

## How to prove it

**The artifact.** A labelled set with clean and ambiguous cases, a scorer
reporting precision and recall per defect type, and one documented case where
the measurement contradicted the spot check.

**Three things to do, in order:**

1. **Run the golden path, including step 4.** The gap between the three-page
   spot check and the full numbers is the demonstration, and it takes two
   minutes to show.
2. **Label twenty real pages for one defect type.** One type, by hand, with
   notes. An hour, and it is the only artifact on this page that cannot be
   faked.
3. **Measure your own agreement with yourself.** Label ten pages, wait a week,
   label them again blind, and count the disagreements. That number is your
   ceiling, and reporting it alongside a precision figure is unusual enough to
   be memorable. Expect to disagree with yourself on at least one page in ten.
   A perfect second pass means you are remembering your labels rather than re-
   deriving them, and the week was not long enough.

**What makes it credible rather than decorative.** Quoting precision and recall is a definition anyone
can recite. A labelled set containing deliberately ambiguous cases, per-type
metrics, and a worked example where tightening a prompt halved recall while F1
stayed flat demonstrates that you have been misled by a spot check and built
the thing that stops it happening again.

### How this would be demonstrated elsewhere

No model was available here, so no generated output was scored. The procedure
below is the one this page argues for, and it is cheap enough that the absence
is a scheduling problem rather than a technical one.

**What you need.** Access to whichever model your readers actually reach your
docs through, by API or locally, plus the twenty-case golden set that
[retrieval evaluation](retrieval-evaluation.md) already requires. Budget is
small: twenty questions against two or three prompt variants is a few hundred
calls, which is cents rather than dollars on any current model.

**What you would run.** For each question, retrieve context, generate an answer, and score it on three
axes that need no human. Whether every claim in it appears in the retrieved
context. Whether it cites a source that actually contains the cited fact. And
whether it refuses when the corpus has no answer.

```python
answer = model.generate(prompt.format(context=chunks, question=q))
grounded = all(claim_supported(c, chunks) for c in split_claims(answer))
refused  = looks_like_refusal(answer)
```

**What you would see.**

| Observation | Rough magnitude | What it tells you |
|---|---|---|
| Answers whose claims are all in context | 70 to 90% | The ceiling your retrieval sets |
| Answers citing a chunk that lacks the cited fact | 5 to 20% | Citation is not grounding; both need checking |
| Refusal rate on questions the corpus cannot answer | often near 0% | The most dangerous number on the page |
| Agreement between two runs at temperature 0 | high but not 1.0 | Why n=1 evaluation misleads |
| Effect of a prompt change on grounding | several points | Larger than most model upgrades |

The third row is the finding worth building the harness for. Add five questions
whose answers are deliberately absent from your corpus, and measure how often
the system invents something instead of saying it does not know. A system that
never refuses is not accurate, it is confident, and no retrieval metric exposes
that at all.

**How you would know it had failed.** A grounding score at or near 100% almost
always means the claim splitter is too coarse, so whole paragraphs count as one
claim that matches loosely. A refusal rate of 100% means the prompt is
over-constrained and the system is useless rather than safe. And if scores do
not move when you deliberately corrupt the retrieved context, the grader is
reading the answer rather than comparing it with anything.

## Related

- [Prompting for content work](prompting.md), what gets evaluated
- [Grounding and citation](grounding.md), the mechanical checks underneath
- [Retrieval evaluation](retrieval-evaluation.md), the same discipline one stage earlier
- [Judging where AI can be trusted](ai-trust-judgment.md), the decision these numbers inform
