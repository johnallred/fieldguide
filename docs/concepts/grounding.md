---
title: Grounding and citation
summary: Making an answer traceable to the text it came from, and failing it mechanically when it is not.
diataxis: explanation
audience: developer
concept: grounding
tags: [ai, core]
---

# Grounding and citation

`core` · difficulty 2 · 4h

> Practical experience applying LLMs to content workflows (prompting, retrieval and grounding, output evaluation)

> Source: nvidia posting, verbatim

**Prerequisites:** [RAG pipelines](rag.md)

**Leads to:** [Documentation-backed AI assistants](ai-assistants.md), [Hallucination and guardrails](hallucination-guardrails.md), [Output evaluation](output-evaluation.md)

## What it is

Requiring every claim in an answer to be traceable to a specific piece of
retrieved text, and checking that requirement mechanically rather than trusting
it. Citation is the visible half: the answer names its sources. Grounding is the
enforcement: a claim with no supporting text is rejected before anyone reads it.

The distinction matters because **a citation is not evidence of grounding.** A
model will happily attach `[c3]` to a sentence `c3` does not support.

## Why the job asks for it

NVIDIA lists it in the middle of the three-part requirement: "prompting,
retrieval and grounding, output evaluation". The ordering is the pipeline, and
grounding is the stage that makes the other two auditable.

What makes it `core` rather than a nicety is the asymmetry described in
[RAG](rag.md): a generated answer hides the ranking. A reader looking at a
search results page judges five results themselves. A reader looking at a
paragraph has no way to tell whether it synthesised two relevant chunks or
invented a bridge between two half-relevant ones. **Citation restores the
reader's ability to check, and mechanical grounding restores yours.**

On a Tuesday it is a specific and common defect. The assistant says "Set
`max_memory_mb` to cap GPU memory, with a default of 16. [c3]" That sentence
contains two facts from two chunks: the flag name from the legacy page and the
default from the current one, fused into a claim that is true of neither. The
citation is present. The answer is wrong. **Only a check that tests the claim
against the cited text catches it**, and the check is about forty lines.

## The golden path

Build a grounding checker, run it against answers that look right, and watch it
reject three different kinds of ungrounded claim. Forty minutes, dependency-free.

**Step 1: the context, and four answers to judge**

```bash
mkdir -p ground-drill && cd ground-drill
cat > context.json <<'EOF'
{
  "c3": "max_memory_gb caps the GPU memory the server will allocate. The default is 16. Size for peak load, not startup.",
  "c4": "max_memory_mb was the 1.x equivalent of max_memory_gb. It was removed in 2.0 and is ignored if set.",
  "c1": "batch_size controls how many requests are grouped per forward pass. The default is 32. The maximum is 512."
}
EOF

cat > answers.json <<'EOF'
[
  {"label": "grounded",
   "text": "Set max_memory_gb to cap GPU memory. [c3] The default is 16. [c3]"},
  {"label": "fused",
   "text": "Set max_memory_mb to cap GPU memory, with a default of 16. [c3]"},
  {"label": "half-cited",
   "text": "Set max_memory_gb to cap GPU memory. The default is 16. [c3]"},
  {"label": "uncited",
   "text": "Set max_memory_gb to cap GPU memory. The default is 16."},
  {"label": "invented",
   "text": "Set max_memory_gb to cap GPU memory. [c3] The default is 24. [c3]"},
  {"label": "wrong-source",
   "text": "The default is 32. [c3]"},
  {"label": "dangling",
   "text": "Set max_memory_gb to cap GPU memory. [c9]"}
]
EOF
python3 -c "import json; print(len(json.load(open('answers.json'))), 'answers to judge')"
```

Read those five. Four of them look like a correct answer at a glance, and three
are wrong in ways a reader cannot detect.

**Step 2: the checker**

```bash
cat > ground.py <<'PY'
"""Check that every sentence in an answer is supported by its cited chunk.

Three checks, in increasing strictness, and the second is the one that earns
its keep:

  CITED       does every sentence carry a citation at all?
  SUPPORTED   do the sentence's content words appear in the cited chunk?
  NUMBERS     does every number in the sentence appear in the cited chunk?

The NUMBERS check is separate because numbers are where ungrounded answers do
the most damage and where word-overlap scoring is blindest: "the default is
16" and "the default is 24" differ by one token out of five and by everything
that matters.
"""
import json
import re
import sys

CITATION = re.compile(r"\[(\w+)\]")
STOP = {
    "the", "a", "an", "to", "is", "are", "of", "in", "on", "for", "with",
    "and", "or", "it", "its", "set", "was", "be", "by", "at", "as", "this",
    "that", "will", "can", "you", "your", "not", "from", "which",
}

#: A sentence must have at least this share of its content words present in
#: the cited chunk. Deliberately not 1.0: an answer is allowed to paraphrase
#: and to use connective words the source does not contain.
SUPPORT_THRESHOLD = 0.7


def content_words(text):
    return [
        w for w in re.findall(r"[a-z0-9_]+", text.lower())
        if w not in STOP and len(w) > 1
    ]


def numbers(text):
    return set(re.findall(r"\b\d+(?:\.\d+)?\b", text))


#: A sentence, followed by any citations that trail it. Matching them together
#: is the whole point: splitting on `(?<=[.!?])\s+` first puts a trailing
#: `[c3]` in its own fragment and leaves the sentence it belongs to looking
#: uncited, which made the first version of this checker reject every answer.
SENTENCE = re.compile(r"(.+?[.!?])((?:\s*\[\w+\])*)", re.S)


def sentences(answer):
    """Split into (sentence, citations), with a trailing citation kept.

    A citation applies to the sentence it follows. One citation covering three
    sentences is NOT accepted, which is strict on purpose: a single citation
    spanning several claims is exactly the pattern that hides a fused answer.
    """
    out = []
    for match in SENTENCE.finditer(answer.strip()):
        text = CITATION.sub("", match.group(1)).strip()
        if text:
            out.append((text, CITATION.findall(match.group(2))))
    return out


def check(answer, context):
    findings = []
    for text, cited in sentences(answer):
        if not cited:
            findings.append(("uncited", text, "no citation on this sentence"))
            continue

        source = " ".join(context.get(c, "") for c in cited)
        missing_sources = [c for c in cited if c not in context]
        if missing_sources:
            findings.append(
                ("bad-citation", text, f"cites {missing_sources}, not in the context")
            )
            continue

        source_words = set(content_words(source))
        words = content_words(text)
        present = [w for w in words if w in source_words]
        ratio = len(present) / len(words) if words else 1.0
        if ratio < SUPPORT_THRESHOLD:
            absent = [w for w in words if w not in source_words]
            findings.append((
                "unsupported", text,
                f"{ratio:.0%} of content words in {cited}; missing {absent}",
            ))

        absent_numbers = numbers(text) - numbers(source)
        if absent_numbers:
            findings.append((
                "ungrounded-number", text,
                f"{sorted(absent_numbers)} not in {cited}",
            ))
    return findings


def main():
    context = json.load(open("context.json"))
    for answer in json.load(open("answers.json")):
        findings = check(answer["text"], context)
        verdict = "PASS" if not findings else "REJECT"
        print(f"{verdict:<7} [{answer['label']}] {answer['text']}")
        for kind, text, why in findings:
            print(f"        {kind}: {why}")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
PY
python3 ground.py
```

**Step 3: see what each check catches that the others do not**

```bash
python3 - <<'PY'
import json

from ground import check, content_words

context = json.load(open("context.json"))
source_words = set(content_words(context["c3"]))


def overlap(answer):
    words = content_words(answer.replace("[c3]", ""))
    return sum(1 for w in words if w in source_words) / len(words)


print("=== when does the NUMBERS check earn its keep? ===")
print("A wrong number is itself a missing content word, so on a SHORT")
print("sentence the support check catches it anyway. On a long one it does not.\n")

for answer in [
    "The default is 16. [c3]",
    "The default is 24. [c3]",
    "max_memory_gb caps the GPU memory the server will allocate, "
    "and the default is 16. [c3]",
    "max_memory_gb caps the GPU memory the server will allocate, "
    "and the default is 24. [c3]",
]:
    kinds = [f[0] for f in check(answer, context)] or ["none"]
    print(f"  overlap {overlap(answer):5.0%}   findings {kinds}")
    print(f"    {answer}")

print()
print("=== the fused answer, in detail ===")
fused = "Set max_memory_mb to cap GPU memory, with a default of 16. [c3]"
for kind, text, why in check(fused, context):
    print(f"  {kind}: {why}")
PY
```

The four-line table is the argument, and it is narrower than the usual claim:

| Answer | Overlap | Fires |
|---|---|---|
| short, default 16 | 100% | nothing. Correct |
| short, default **24** | 50% | `unsupported` *and* `ungrounded-number` |
| long, default 16 | 100% | nothing. Correct |
| long, default **24** | **88%** | **`ungrounded-number` only** |

On a short sentence a wrong number is a large share of the content words, so
the support check catches it without help. **On a long sentence the same
fabrication sits at 88% overlap, comfortably above any usable threshold, and
only the dedicated numbers check sees it.** Since real answers are long
sentences, that is where the check pays for itself.

The fused answer is rejected for missing `max_memory_mb` and `cap`. The first
is the finding; the second is a false positive, because `c3` says "caps" and
this checker does no stemming. Worth noticing: **lexical support is a proxy
with real noise in it**, which is why the threshold is 0.7 rather than 1.0 and
why it has to be set from a labelled set rather than reasoned to.

**Step 4: the prompt side, which reduces the problem rather than solving it**

```bash
cat > prompt.txt <<'EOF'
Answer the question using ONLY the numbered sources below.

Rules:
- Put a citation [id] at the end of EVERY sentence, naming the single source
  that supports that sentence.
- If a sentence needs two sources, split it into two sentences.
- Quote exact values (numbers, flag names, version strings) verbatim from the
  source. Never convert, round, or infer a value.
- If the sources do not contain the answer, reply exactly:
  "I could not find this in the documentation."
  That is a correct and expected answer.

Sources:
{context}

Question: {question}
EOF
cat prompt.txt
```

**What you built.** A checker that rejects three kinds of ungrounded answer, and
the prompt that reduces how often they occur.

The division of labour is the lesson. **The prompt makes grounded answers more
likely; the checker makes ungrounded ones not ship.** Only the second is a
guarantee, and the "split it into two sentences" rule exists specifically to
make the checker's job possible: one citation covering three claims cannot be
verified, so the prompt is designed around what the validator can check.

## Reference

### The three failures, and which check catches each

| Failure | Looks like | Caught by |
|---|---|---|
| Uncited claim | A plausible sentence with no source | Citation presence |
| Fused claim | Two true facts from two chunks, combined into a false one | Word support against the cited chunk |
| Invented value | A number or name that is nowhere in the context | The numbers check |
| Wrong source | A true sentence citing the wrong chunk | Word support |
| Dangling citation | A citation to a chunk not in the context | Citation resolution |

### Why numbers get their own check

| Answer | Overlap with `c3` | Support check | Numbers check |
|---|---|---|---|
| "…allocate, and the default is 16." | 100% | passes | passes |
| "…allocate, and the default is 24." | **88%** | **passes** | **fails** |

A wrong number is one token. In a sentence of eight content words that is 88%
overlap, which sits above any threshold loose enough to allow paraphrase. **A
grounding check that is only a similarity score will pass fabricated numbers in
exactly the answers that are long enough to sound authoritative.**

The same argument applies to flag names, version strings and error codes, which
is why the checker tokenizes keeping underscores.

### Prompt rules that make checking possible

| Rule | Why it exists |
|---|---|
| Citation at the end of every sentence | A paragraph-level citation cannot be verified per claim |
| Split a sentence that needs two sources | Makes fused claims structurally impossible to express |
| Quote values verbatim, never convert | Gives the numbers check something exact to match |
| An explicit refusal string | A refusal must be available, or the model fills the gap |
| Sources numbered, not pasted raw | The citation needs a stable label |

Notice that four of the five are written for the benefit of the *validator*
rather than the reader. That is the right way round: design the output format so
it can be checked, then check it.

### Degrees of grounding, from cheap to strict

| Level | Check | Cost |
|---|---|---|
| Citation present | Every sentence has an `[id]` | trivial |
| Citation resolves | The id is in the context | trivial |
| Lexical support | Content words appear in the cited chunk | cheap, what this page builds |
| Exact-value support | Numbers and identifiers match verbatim | cheap, highest value |
| Entailment | A model judges whether the source supports the claim | expensive, needs its own evaluation |
| Human review | A person checks | expensive, the only real ceiling |

Lexical plus exact-value is the sweet spot: it runs in CI, costs nothing, and
catches the failures that matter most in documentation. Entailment checking is
better and introduces a second model whose errors you now also have to measure.

### What grounding does not give you

| Claim | Reality |
|---|---|
| "The answer is correct" | It is *supported by the retrieved text*. If the page is wrong, so is the answer |
| "No hallucination" | It bounds fabrication to what retrieval returned |
| "The answer is complete" | A grounded answer can omit the crucial caveat on another page |
| "The citation is the right one" | Lexical support is a proxy; a true sentence can cite a near-miss |

The first row is the one to say out loud. **Grounding inherits the corpus's
errors**, so it is a check on the pipeline and not on the documentation. That is
what [freshness monitoring](freshness-monitoring.md) and
[reading code to verify](reading-code-to-verify.md) are for.

## How to talk about it

**What a competent answer sounds like.** Lead with the fused claim, because it is
the failure that proves you have looked at real output. "Citations are not
evidence of grounding. The failure I check for is a fused claim: the answer
takes a flag name from one chunk and a default value from another and combines
them into a sentence that is true of neither, with a citation attached. So every
sentence carries exactly one citation, and a checker verifies the sentence's
content words and every number against that specific chunk. The numbers check is
separate, because a fabricated default inside a long sentence sits at 88% word
overlap, which is above any threshold loose enough to allow paraphrase."

**The follow-up is "what is your threshold and how did you pick it",** and the
honest answer is that a fixed word-overlap threshold is crude and you pick it
from a labelled set. Too strict and legitimate paraphrase gets rejected, which
trains people to disable the check; too loose and fused claims pass. The
threshold is a parameter you measure, not a number you reason to, which is why
this concept leads directly into
[output evaluation](output-evaluation.md).

**The tradeoff to volunteer.** Strict grounding makes answers worse to read.
A citation at the end of every sentence is noisy, the one-source-per-sentence
rule forbids useful synthesis, and a model constrained this hard produces prose
that reads like a quotation anthology. There is a real tension between an answer
that is pleasant and an answer that is checkable, and for developer
documentation checkable wins, because a wrong command costs more than an awkward
paragraph. For a general-audience assistant that trade might go the other way.

**One sharper point.** The strongest observation is that **grounding is the
mechanism that makes an assistant's failures legible to the documentation team.**
An ungrounded-number rejection points at a specific chunk and a specific claim,
which means your assistant's failure log is a list of pages where the content
and the questions do not line up. Without grounding you have a pile of
complaints; with it you have a prioritised content backlog. That reframes the
work from AI safety into [documentation prioritisation](docs-prioritization.md),
and it is the framing a documentation lead will actually fund.

## How to prove it

**The artifact.** The checker, plus a set of answers it rejects, including one
that looks correct. The fused example is the one to show.

**Three things to do, in order:**

1. **Run the golden path.** Five answers, four of which look right, three
   rejected for three different reasons. The number check passing "16" and
   rejecting "24" at 88% overlap is the moment that lands.
2. **Run it against real output.** Take thirty answers from any
   documentation assistant you can query, and check them. Count the fused
   claims. That number is a finding nobody has.
3. **Put it in CI on a golden set.** The checker plus twenty
   question-and-expected-source pairs, failing the build when the grounded rate
   drops. That is the step from a script to a gate.

**What makes it credible rather than decorative.** Saying "we require citations" is near-universal and
means almost nothing. A checker that rejects a fused claim carrying a valid
citation, with the threshold justified from a labelled set, demonstrates that
you know citations are not grounding.

## Related

- [RAG pipelines](rag.md), where the context comes from
- [Output evaluation](output-evaluation.md), how to set the threshold with data
- [Hallucination and guardrails](hallucination-guardrails.md), the failure this bounds
- [Prompting for content work](prompting.md), the same discipline applied to tasks
