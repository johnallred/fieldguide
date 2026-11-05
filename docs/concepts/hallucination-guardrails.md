---
title: Hallucination and guardrails
summary: Why a grounded system still invents things, and the layered checks that bound the damage.
diataxis: explanation
audience: developer
concept: hallucination-guardrails
tags: [ai, supporting]
---

# Hallucination and guardrails

`supporting` · difficulty 3 · 4h

> sound judgment about where AI can be trusted

> Source: nvidia posting, verbatim

**Prerequisites:** [Grounding and citation](grounding.md), [Output evaluation](output-evaluation.md)

## What it is

A hallucination is a fluent, confident claim with nothing behind it. A guardrail
is a mechanism that catches one before a reader acts on it.

The useful framing is not "stop hallucination", which is not available. It is
**bound the damage and make the failures visible**, which is.

## Why the job asks for it

NVIDIA asks for "sound judgment about where AI can be trusted" and for "human
review where judgment matters". Both are about this. The posting never uses the
word hallucination, which is why the tag is `quoted` on a different phrase: they
are asking about the behaviour rather than the vocabulary.

What makes this `supporting` rather than `core` is that most of the work lives in
[grounding](grounding.md) and [output evaluation](output-evaluation.md). This
page is the taxonomy that tells you which of those mechanisms to reach for, plus
the failure modes neither catches.

On a Tuesday it is a specific, nasty class of ticket. A developer says the
assistant told them to pass `--retry-budget`, which does not exist. The flag
name is plausible, the sentence was well formed, and the cited page is real.
**Grounding caught nothing, because the fabricated flag sat inside a sentence
otherwise copied from the real page**, so it was one unmatched word among
several that matched. That is the case the layered guardrails below exist for,
and the golden path reproduces it.

## The golden path

Build a layered guardrail and find what each layer catches that the others
miss. Thirty-five minutes, dependency-free.

Committed as `drills/guardrails.py`, which stages these files and runs this
page's `run.py` in one go. Two tests hold it to the page: the five files must
still match what is written here, and the results table below must still be
the matrix the code produces.

**Step 1: five answers, each wrong in a different way**

```bash
mkdir -p guard-drill && cd guard-drill
cat > context.json <<'EOF'
{
  "c3": "max_memory_gb caps the GPU memory the server will allocate. The default is 16.",
  "c6": "Pass --dry-run to preview changes without applying them.",
  "c1": "batch_size controls how many requests are grouped per forward pass. The default is 32."
}
EOF

cat > known.json <<'EOF'
{
  "flags": ["--dry-run", "--config", "--verbose", "max_memory_gb", "batch_size"],
  "versions": ["2.0", "2.2", "2.4", "2.6"]
}
EOF

cat > answers.json <<'EOF'
[
  {"label": "correct",
   "text": "Pass --dry-run to preview changes. [c6]"},
  {"label": "flag-bare",
   "text": "Pass --retry-budget to bound retries. [c6]"},
  {"label": "flag-camouflaged",
   "text": "Pass --retry-budget to preview changes without applying them. [c6]"},
  {"label": "flag-appended",
   "text": "max_memory_gb caps the GPU memory the server will allocate, and --memory-strict enforces it. [c3]"},
  {"label": "invented-number",
   "text": "max_memory_gb defaults to 24. [c3]"},
  {"label": "invented-version",
   "text": "This requires widget 3.1 or newer. [c3]"},
  {"label": "plausible-fusion",
   "text": "max_memory_gb defaults to 32. [c3]"},
  {"label": "evasive",
   "text": "Set the memory ceiling in the configuration file. [c3]"}
]
EOF
python3 -c "import json; print(len(json.load(open('answers.json'))), 'answers')"
```

Read those eight. Every one is fluent. Six are wrong and one is evasive.

The three `flag-*` cases are the same fabrication, `--retry-budget` or
`--memory-strict`, surrounded by different amounts of real text. That variation
is the experiment.

**Step 2: four layers, cheapest first**

```bash
cat > guards.py <<'PY'
"""Four guardrail layers, in increasing cost, each catching what the
previous one cannot.

The ordering is the design. A cheap deterministic check that runs on every
answer is worth more than an expensive check that runs on a sample, because
the cheap one cannot be skipped under deadline pressure.

  1 GROUNDING    content words and numbers against the cited chunk
  2 VOCABULARY   every flag and version against a KNOWN-GOOD list
  3 SPECIFICITY  an answer that avoids the question rather than refusing
  4 ABSTENTION   was a refusal available, and did the model take it

Layer 2 is the one that catches the flag-name fabrication, and it is the one
most teams do not have, because it needs a list of real identifiers that
nothing else in the pipeline requires.
"""
import json
import re

CITATION = re.compile(r"\[(\w+)\]")
FLAG = re.compile(r"(?<![\w-])(--[a-z][a-z0-9-]*|[a-z][a-z0-9]*(?:_[a-z0-9]+)+)")
VERSION = re.compile(r"\bwidget (\d+\.\d+)\b", re.I)
NUMBER = re.compile(r"\b\d+(?:\.\d+)?\b")

STOP = {
    "the", "a", "an", "to", "is", "are", "of", "in", "on", "for", "with",
    "and", "or", "it", "its", "set", "pass", "without", "by", "this", "that",
    "will", "can", "you", "your", "not", "from", "which", "default", "defaults",
}
SUPPORT_THRESHOLD = 0.6

#: Phrases that describe an action without naming it. A model that cannot
#: find the answer and will not refuse produces these.
VAGUE = (
    "in the configuration file", "in the settings", "as appropriate",
    "the relevant", "accordingly", "as needed", "the appropriate",
)
REFUSAL = "i could not find this in the documentation"


def words(text):
    return [
        w for w in re.findall(r"[a-z0-9_-]+", text.lower())
        if w not in STOP and len(w) > 1
    ]


def guard_grounding(answer, context, known):
    """Layer 1: is the claim supported by the chunk it cites?"""
    findings = []
    cited = CITATION.findall(answer)
    body = CITATION.sub("", answer).strip()
    if not cited:
        return [("uncited", "no citation")]

    source = " ".join(context.get(c, "") for c in cited)
    source_words = set(words(source))
    present = [w for w in words(body) if w in source_words]
    ratio = len(present) / len(words(body)) if words(body) else 1.0
    if ratio < SUPPORT_THRESHOLD:
        findings.append(("unsupported", f"{ratio:.0%} of content words in {cited}"))

    absent = set(NUMBER.findall(body)) - set(NUMBER.findall(source))
    if absent:
        findings.append(("ungrounded-number", f"{sorted(absent)} not in {cited}"))
    return findings


def guard_vocabulary(answer, context, known):
    """Layer 2: does every identifier and version actually exist?

    This is the layer that catches a fabricated flag name. Grounding cannot:
    a plausible flag is a single unmatched content word, which sits inside
    any support threshold loose enough to allow paraphrase.
    """
    findings = []
    body = CITATION.sub("", answer)
    for flag in set(FLAG.findall(body)):
        if flag not in known["flags"]:
            findings.append(("unknown-identifier", f"{flag!r} is not a real flag"))
    for version in set(VERSION.findall(body)):
        if version not in known["versions"]:
            findings.append(("unknown-version", f"widget {version} does not exist"))
    return findings


def guard_specificity(answer, context, known):
    """Layer 3: is the answer avoiding the question?"""
    lowered = answer.lower()
    if lowered.strip().startswith(REFUSAL):
        return []
    for phrase in VAGUE:
        if phrase in lowered:
            return [("evasive", f"says {phrase!r} instead of naming the thing")]
    return []


def guard_abstention(answer, context, known):
    """Layer 4: did it answer when it should have refused?

    Heuristic and deliberately weak: if the answer names no identifier and no
    number and is not a refusal, it has probably asserted something it could
    not support. Reported as a warning, never as a hard failure.
    """
    body = CITATION.sub("", answer).lower()
    if body.strip().startswith(REFUSAL):
        return []
    if not FLAG.search(body) and not NUMBER.search(body):
        return [("unspecific", "no identifier or value; a refusal may have been correct")]
    return []


LAYERS = [
    ("grounding", guard_grounding),
    ("vocabulary", guard_vocabulary),
    ("specificity", guard_specificity),
    ("abstention", guard_abstention),
]


def check(answer, context, known):
    out = []
    for name, layer in LAYERS:
        for kind, why in layer(answer, context, known):
            out.append((name, kind, why))
    return out
PY
echo "guards written"
```

**Step 3: run every layer against every answer**

```bash
cat > run.py <<'PY'
import json

from guards import LAYERS, check

context = json.load(open("context.json"))
known = json.load(open("known.json"))
answers = json.load(open("answers.json"))

for answer in answers:
    findings = check(answer["text"], context, known)
    verdict = "PASS" if not findings else "REJECT"
    print(f"{verdict:<7} [{answer['label']}] {answer['text']}")
    for layer, kind, why in findings:
        print(f"        {layer}/{kind}: {why}")
    print()

print("=" * 68)
print("which layer caught each failure, and which layers alone would miss it")
print("=" * 68)
header = f"{'answer':<30}" + "".join(f"{n[:9]:>11}" for n, _ in LAYERS)
print(header)
print("-" * len(header))
for answer in answers:
    row = f"{answer['label']:<30}"
    for name, layer in LAYERS:
        hit = layer(answer["text"], context, known)
        row += f"{('CAUGHT' if hit else '-'):>11}"
    print(row)
PY
python3 run.py
```

**What you built.** Four layers and a matrix showing which one catches each
failure. Here is what it reports:

| answer | grounding | vocabulary | specificity | abstention |
|---|---|---|---|---|
| correct | - | - | - | - |
| flag-bare | CAUGHT | CAUGHT | - | - |
| **flag-camouflaged** | **-** | **CAUGHT** | - | - |
| **flag-appended** | **-** | **CAUGHT** | - | - |
| invented-number | CAUGHT | - | - | - |
| invented-version | CAUGHT | CAUGHT | - | - |
| plausible-fusion | CAUGHT | - | - | - |
| evasive | CAUGHT | - | CAUGHT | CAUGHT |

The two bolded rows are the whole point, and they are the reason this page
needed three variants of one fabrication rather than one.

**`flag-bare`** invents `--retry-budget` in a short sentence that shares almost
nothing with its cited chunk, so the fabricated flag is most of the content and
grounding catches it at 0% support.

**`flag-camouflaged`** invents the same flag inside a sentence otherwise copied
from the source: "Pass `--retry-budget` to preview changes without applying
them." Grounding **passes it**. The fabrication is one unmatched word among
several that match, which sits comfortably inside any support threshold loose
enough to permit paraphrase.

**`flag-appended`** does the same thing by addition: a correct sentence about
`max_memory_gb` with "and `--memory-strict` enforces it" bolted on. Grounding
passes that too.

Only the vocabulary layer catches either, and it catches both trivially,
because `--retry-budget` and `--memory-strict` are simply not in the list of
real flags.

Note also that **no row is caught by every layer and no layer catches every
row.** `invented-number` and `plausible-fusion` are invisible to the vocabulary
check, since `24` and `32` are not identifiers. That non-overlap is what makes
this layered rather than a choice between mechanisms.

## Reference

### A taxonomy that maps to fixes

| Failure | Looks like | Caught by |
|---|---|---|
| Uncited claim | A plausible sentence, no source | [Grounding](grounding.md) |
| Fused claim | Two true facts combined into a false one | Grounding, word support |
| Invented value | A number nowhere in the context | Grounding, numbers check |
| **Invented identifier** | A flag or method that follows your naming conventions | **A known-good vocabulary list** |
| Invented version | "requires 3.1" for a product at 2.6 | A known-good version list |
| Stale truth | Correct in March, wrong now | A freshness field, [monitoring](freshness-monitoring.md) |
| Evasive answer | "Set it in the configuration file" | A specificity check |
| Confident non-refusal | An answer where a refusal was correct | Abstention rate, sampling |
| Wrong because the page is wrong | Perfectly grounded, still wrong | [Verify against code](reading-code-to-verify.md) |

**The identifier row is the one worth building for.** It is the most damaging
failure in developer documentation, because a plausible flag name costs a
reader twenty minutes of trying it. And grounding catches it only when the
fabrication is *bare*: surround it with text copied from the source and the
support ratio stays high, as the golden path's `flag-camouflaged` and
`flag-appended` cases demonstrate. Grounding is not useless here, it is
unreliable here, which is worse, because it looks like coverage.

### Where the known-good list comes from

You already have it, which is why this check is cheaper than it sounds:

| Source | Gives you |
|---|---|
| `--help` output, parsed | Every real flag |
| An OpenAPI document | Every real endpoint and parameter |
| `inspect.signature` over the public API | Every real function and keyword |
| Git tags | Every real version |
| The [content model's](content-model.md) closed vocabularies | Every real page type and audience |

Generating that list in CI from the artifact that defines it means it cannot
drift, which is the same argument as
[generated reference](api-reference-generation.md).

### The layers, and what each costs

| Layer | Catches | Cost | Runs on |
|---|---|---|---|
| Grounding | Fusion, invented values | trivial | every answer |
| Known-good vocabulary | Invented identifiers and versions | trivial | every answer |
| Specificity | Evasion | trivial | every answer |
| Abstention rate | Non-refusals, in aggregate | cheap | a dashboard |
| LLM-as-judge entailment | Subtler unsupported claims | expensive | a sample |
| Human review | Everything, including a wrong corpus | expensive | a sample |

**Order matters more than coverage.** A trivial check on every answer beats a
sophisticated check on a sample, because the sampled check is the one that stops
running when the team is busy.

### Why abstention deserves a metric

A model that will not refuse fabricates. Measuring the refusal rate is the
cheapest early warning available:

| Symptom | Likely cause |
|---|---|
| Refusal rate near zero | No refusal path in the prompt, or the model is overriding it |
| Refusal rate very high | Retrieval is failing, not the generation |
| Refusal rate falls after a prompt change | You probably made fabrication more likely |

Track it on a dashboard. It is one number, and it moves before the complaints
arrive.

### What none of this fixes

| Limit | Consequence |
|---|---|
| A wrong page | A perfectly grounded answer repeating a wrong default |
| A stale page | Confidently correct as of eighteen months ago |
| Missing content | The model fills a gap it cannot know is a gap |
| Omission | Every claim true, the crucial caveat absent |

The last row has no good mechanical check and is the most common real harm:
an answer about rotating a key that never mentions the one-hour overlap window.
Only a person who knows the subject catches that, which is what
[review](docs-review.md) is for and why
[judging where AI can be trusted](ai-trust-judgment.md) keeps high-cost tasks
away from models entirely.

## How to talk about it

**What a competent answer sounds like.** Lead with the identifier case, because
it shows you have debugged a real system rather than read about hallucination.
"Grounding catches fused claims and invented numbers. Where it gets unreliable
is a fabricated identifier, and specifically a camouflaged one: invent a flag
in a sentence otherwise copied from the source and the support ratio stays
high, so it passes. I tested the same fabrication bare, camouflaged and
appended; grounding caught one of three.
So I check every flag and version in an answer against a known-good list
generated in CI from `--help` output and git tags. That list already exists;
nothing else in the pipeline was using it."

**The follow-up is "can you eliminate hallucination",** and the answer is no,
followed by the reframing that matters: you bound it and you make it visible.
Bounding is grounding plus vocabulary checks, which confine fabrication to
things that exist. Visibility is an abstention metric and a sampled human read,
so the failures you cannot check mechanically still get counted. A candidate who
claims elimination has not operated one of these.

**The tradeoff to volunteer.** Every guardrail increases refusals, and refusals
have a cost that nobody measures. An assistant tuned hard enough to never
fabricate will decline questions it could have answered, and users stop asking,
and the project is judged a failure for being useless rather than for being
wrong. That failure is quieter and just as fatal. The honest position is that
there is a dial between fabrication and unhelpfulness, your guardrails set where
it sits, and you should know your refusal rate as precisely as your error rate.

**One sharper point.** The strongest observation is that **a hallucination in a
documentation assistant is usually a content report.** A model asked about
retry budgets with nothing in the corpus about retry budgets will invent
`--retry-budget`, and the invention is shaped by the gap. So the fabrication log,
grouped by subject, is a ranked list of the pages you have not written, derived
from real reader questions. Teams treat that log as a safety problem; it is also
the most honest [documentation backlog](docs-prioritization.md) you will ever
get, and reframing it that way is what gets the work funded.

## How to prove it

**The artifact.** A vocabulary guardrail whose known-good list is generated in
CI, plus the layer matrix showing what each catches.

**Three things to do, in order:**

1. **Run the golden path.** The matrix is the demonstration: the same
   fabricated flag caught bare and missed when camouflaged, with only the
   vocabulary layer catching all three variants. That is the clearest reason
   layering is not optional.
2. **Generate a real known-good list.** Parse `--help` from any CLI you have,
   or `inspect.signature` over a library's public API. Twenty lines, and it
   turns this page from a concept into a check you own.
3. **Measure your refusal rate.** If you have any assistant over documentation,
   count what fraction of answers are refusals. A rate near zero is the finding,
   and almost nobody has the number.

**What makes it credible rather than decorative.** Discussing hallucination is unfalsifiable. A
vocabulary check against a CI-generated identifier list, a layer matrix showing grounding
catching a fabricated flag in one phrasing and missing it in two others, and a
refusal-rate number, demonstrates that you measured the failure rather than
worried about it.

## Related

- [Grounding and citation](grounding.md), layer one
- [Output evaluation](output-evaluation.md), how to set the thresholds
- [Judging where AI can be trusted](ai-trust-judgment.md), which tasks to avoid entirely
- [Documentation-backed AI assistants](ai-assistants.md), where these layers get deployed
