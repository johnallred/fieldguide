---
title: Generative engine optimization
summary: Being the source an assistant cites, which rewards different things from being the result a human clicks.
diataxis: explanation
audience: developer
concept: geo
tags: [ai, core]
---

# Generative engine optimization

`core` · difficulty 2 · 3h

> Optimize documentation for search (SEO and GEO) and for AI assistants and coding agents through agentready, LLMdigestible content

> Source: intel posting, verbatim

**Prerequisites:** [SEO for documentation](seo-for-docs.md), [Agent-ready content](agent-ready-content.md)

## What it is

Making your documentation the source an assistant retrieves, cites and quotes
correctly, rather than the result a human clicks. The acronym is new and
contested; the underlying question is not.

**The useful framing: a search engine ranks pages, an assistant extracts
passages.** Everything that differs follows from that.

## Why the job asks for it

Intel names it twice, in a responsibility and in minimum qualifications, and
pairs it with SEO both times. That pairing is the instruction: the same work
serves both, and the parts that differ are worth knowing.

What makes it `core` despite being the newest idea here is that the mechanism
is concrete even though the branding is not. An assistant answering a developer
question retrieves a passage, not a page, and whether your passage is usable
depends on properties you control: whether it stands alone, whether the claim
and its qualifier are in the same chunk, whether the exact identifier appears
as text.

On a Tuesday it looks like a complaint with an unfamiliar shape. A developer
says an assistant told them the retry default is 3. Your page says 3 in the
opening sentence and corrects it four paragraphs later, under a heading about
version 2.5. **The page is accurate and the passage is not**, because the
correction and the claim ended up in different chunks. No amount of ranking
helps; the page needs rewriting so the qualifier travels with the claim.

## The golden path

Take a page that is correct and extracts badly, measure why, and fix it.
Thirty-five minutes.

**Step 1: a page that is accurate and quotes wrong**

```bash
mkdir -p geo-drill && cd geo-drill
cat > before.md <<'EOF'
---
title: Configure retries
summary: Retry configuration for the widget client.
diataxis: how-to
updated: 2026-10-20
---
# Configure retries

The client retries failed requests automatically. The default is 3.

## Backoff

Backoff is exponential with jitter. This avoids synchronised retries across
many clients, which was a problem in the 2.3 release.

## Limits

The maximum is 10. Setting it higher is rejected at construction time.

## Changes in 2.5

As of 2.5 the default changed from 3 to 5, because the previous value was
too low for the new upstream timeout.
EOF
wc -w before.md
```

Every sentence in that page is true. The first sentence of the page is also
wrong as of 2.5, and that first sentence is what gets extracted.

**Step 2: chunk it and see which passage answers the question**

```bash
cat > extract.py <<'PY'
"""Chunk a page and show which passage answers a question.

This is the GEO measurement: not whether the page is correct, but whether the
PASSAGE an assistant would lift is correct and self-contained.
"""
import re
import sys
from pathlib import Path

HEADING = re.compile(r"^(#{1,6}) +(.*?)\s*$")
FENCE = re.compile(r"^\s*(```|~~~)")


def chunks(path):
    text = path.read_text(encoding="utf-8")
    body = text.partition("---\n")[2].partition("\n---\n")[2]
    trail, buffer, out, in_fence = [], [], [], False
    for line in body.splitlines():
        if FENCE.match(line):
            in_fence = not in_fence
            buffer.append(line)
            continue
        match = None if in_fence else HEADING.match(line)
        if match:
            if buffer:
                out.append((" > ".join(trail), "\n".join(buffer).strip()))
            buffer = []
            depth = len(match.group(1))
            trail = trail[: depth - 1] + [match.group(2)]
        else:
            buffer.append(line)
    if buffer:
        out.append((" > ".join(trail), "\n".join(buffer).strip()))
    return [(c, t) for c, t in out if t]


def best(path, question):
    terms = [t for t in re.findall(r"[a-z0-9_]+", question.lower()) if len(t) > 2]
    scored = []
    for crumb, text in chunks(path):
        hay = f"{crumb} {text}".lower()
        scored.append((sum(hay.count(t) for t in terms), crumb, text))
    scored.sort(reverse=True)
    return scored[0]


def audit(path, question, truth):
    score, crumb, text = best(path, question)
    print(f"  question: {question!r}")
    print(f"  passage:  {crumb}")
    print(f"  text:     {text.splitlines()[0][:72]}")
    standalone = truth in text
    contradicted = any(truth in t for _, t in chunks(path)) and not standalone
    print(f"  contains the current answer ({truth!r}): {standalone}")
    if contradicted:
        print("  >>> the correct value is elsewhere on the page, in another chunk")
    return standalone


if __name__ == "__main__":
    path = Path(sys.argv[1])
    print(f"=== {path.name}: {len(chunks(path))} chunks ===")
    for crumb, text in chunks(path):
        print(f"  [{len(text):>4}] {crumb}")
    print()
    # Two questions, because WHICH question decides whether the stale chunk
    # or the corrective one is retrieved. That sensitivity is the point: the
    # page is a coin flip, and you do not control the phrasing.
    for question in (
        "does the client retry automatically",
        "what is the default retry count",
    ):
        audit(path, question, "default is 5")
        print()
PY
python3 extract.py before.md
```

**Step 3: fix it for extraction, not for reading order**

```bash
cat > after.md <<'EOF'
---
title: Configure retries
summary: Set the retry count on the widget client; the default is 5 as of version 2.5.
diataxis: how-to
updated: 2026-10-20
---
# Configure retries

## The retry default

The client retries failed requests automatically. **The default is 5** as of
widget 2.5. Before 2.5 it was 3, which was too low for the current upstream
timeout.

Set it explicitly to avoid depending on the default:

    client = WidgetClient(api_key="sk-...", retries=5)

## The retry maximum

**The maximum is 10** as of widget 2.5. A higher value is rejected at
construction time, not at request time.

## Backoff behaviour

Retries use exponential backoff with jitter, as of widget 2.5. Jitter avoids
synchronised retries across many clients, which caused a thundering-herd
problem before the 2.3 release.
EOF
python3 extract.py after.md
```

**Step 4: measure the properties, rather than asserting the fix worked**

```bash
cat > geocheck.py <<'PY'
"""Score a page on properties that decide whether its passages extract well.

Four checks. Each one corresponds to a failure that leaves the PAGE correct
and the PASSAGE wrong or unusable.

  SELF-CONTAINED  does each chunk state its own subject, or does it rely on
                  a sentence in a different chunk?
  QUALIFIED       do claims carry their version or condition in the SAME
                  chunk as the claim?
  NO CONTRADICTION  do two chunks give different answers to one question?
  IDENTIFIERS     do exact names appear as text, not only in prose about them?
"""
import re
import sys
from pathlib import Path

from extract import chunks

VALUE = re.compile(r"\b(?:default|maximum|minimum) is (\d+)", re.I)
#: "the default changed from 3 to 5" states the CURRENT value as the second
#: number. Without this, a page whose correction is phrased as a change rather
#: than as a restatement evades the contradiction check entirely, which is
#: exactly what the `before.md` fixture does.
CHANGED = re.compile(
    r"\b(default|maximum|minimum) changed from (\d+) to (\d+)", re.I
)
QUALIFIER = re.compile(r"\b(as of|before|since|in) (?:widget )?\d+\.\d+", re.I)
PRONOUN_START = re.compile(r"^\s*(it|this|that|these|they|the above)\b", re.I)


def audit(path):
    findings = []
    page_chunks = chunks(path)

    # Claims of the same kind that disagree across chunks.
    claims = {}
    for crumb, text in page_chunks:
        for match in VALUE.finditer(text):
            kind = match.group(0).split(" is ")[0].lower()
            claims.setdefault(kind, []).append((crumb, match.group(1)))
        for match in CHANGED.finditer(text):
            kind = match.group(1).lower()
            claims.setdefault(kind, []).append((crumb, match.group(3)))

    for kind, found in claims.items():
        values = {value for _, value in found}
        if len(values) > 1:
            where = "; ".join(f"{crumb}: {value}" for crumb, value in found)
            findings.append(("contradiction", f"{kind} is given as {sorted(values)} ({where})"))

    for crumb, text in page_chunks:
        first = text.splitlines()[0] if text.splitlines() else ""

        if PRONOUN_START.match(first):
            findings.append(("not-self-contained",
                             f"{crumb!r} opens with a pronoun: {first[:46]!r}"))

        if (VALUE.search(text) or CHANGED.search(text)) and not QUALIFIER.search(text):
            findings.append(("unqualified-claim",
                             f"{crumb!r} states a value with no version or condition"))

    return findings


if __name__ == "__main__":
    total = 0
    for name in sys.argv[1:]:
        path = Path(name)
        findings = audit(path)
        total += len(findings)
        print(f"=== {path.name} ===")
        if not findings:
            print("  ok")
        for kind, why in findings:
            print(f"  {kind}: {why}")
        print()
    print(f"{'FAIL' if total else 'ok'}: {total} problem(s)")
    sys.exit(1 if total else 0)
PY
python3 geocheck.py before.md after.md; echo "exit=$?"
```

**What you built.** A chunk-level view of a page, a rewrite aimed at extraction,
and a checker for the properties that decide whether a passage survives being
lifted out.

### What the measurement showed

`before.md` splits into four chunks, and **which one answers the question
depends on the phrasing**:

| Question | Passage retrieved | Contains the current value? |
|---|---|---|
| "does the client retry automatically" | `Configure retries` | **No**, says 3 |
| "what is the default retry count" | `Configure retries > Changes in 2.5` | **No**, says "changed from 3 to 5" |

Neither passage is usable. The first is stale. The second is *correct* and
phrased as a change rather than a statement, so a reader quoted it gets history
instead of an answer. **You do not control which phrasing a developer uses**,
and the page is a coin flip between two bad passages.

`after.md` returns the same correct passage for both phrasings, because the
value, its qualifier and the subject sit in one chunk.

The checker reports three problems on `before.md` and none on `after.md`:

```
contradiction: default is given as ['3', '5']
  (Configure retries: 3; Configure retries > Changes in 2.5: 5)
unqualified-claim: 'Configure retries' states a value with no version
unqualified-claim: 'Configure retries > Limits' states a value with no version
```

### The contradiction check almost did not work

In its first version that check never fired on this page. It matched only the
form "default is N", and `before.md` phrases its correction as "the default
changed from 3 to 5", so the two claims were never compared.

The pattern is worth sitting with, because it recurs: **a checker that
recognises only the canonical phrasing misses exactly the pages that are phrased
loosely, which are the pages most likely to be wrong.** The fix adds the
"changed from X to Y" form. Other phrasings will still evade it, and that is a
real limitation of lexical checking rather than something to regex away
indefinitely. The honest claim is that it catches the two commonest forms, not
that it finds every contradiction.

## Reference

### What differs between SEO and GEO

| | SEO | GEO |
|---|---|---|
| Unit | the page | **the passage** |
| Goal | be clicked | be cited, and quoted correctly |
| Reader | sees the whole page | sees one chunk, usually |
| Reading order | matters | **does not exist** |
| A correction later on the page | works | **does not travel with the claim** |
| Signals | links, titles, freshness | self-containment, qualifiers, identifiers as text |
| Measurement | rankings, clicks | [retrieval evaluation](retrieval-evaluation.md), citation checks |

**The "reading order does not exist" row is the whole discipline.** A page is
read top to bottom by a human and sampled at a random heading by a machine.

### The four properties that matter

| Property | Failure if absent |
|---|---|
| **Self-contained chunks** | A passage opening "It defaults to 3" with no subject |
| **Qualifiers with their claims** | The version caveat in a different chunk from the value |
| **No contradictions across chunks** | Two passages, two answers, one gets cited |
| **Identifiers as text** | `max_memory_gb` only in a table cell or an image |

### Writing habits that follow

| Habit | Why |
|---|---|
| Put the current value in a heading's own section | So the chunk containing it is the one retrieved |
| State the version in the same sentence as the value | "The default is 5 as of 2.5" |
| Never open a section with a pronoun | The antecedent is in another chunk |
| Replace a "Changes in 2.5" section with inline qualifiers | A changes section strands the correction |
| Repeat the subject in each section | Mild redundancy for a human, essential for a machine |
| Put exact identifiers in prose, not only tables | Tables chunk badly and extract worse |

The fourth is the counter-intuitive one. A "what changed in 2.5" section is good
documentation practice and **actively harmful for extraction**, because it
separates a correction from the thing it corrects. Keep the section for humans
if you like, and also fix the claim where it is made.

### Mild redundancy is correct here

A human reading three consecutive sections does not need "as of widget 2.5"
three times. A machine retrieving one of those sections needs it every time.

That is a real cost: the page is slightly worse to read. For developer
documentation where a wrong default costs an afternoon, it is the right trade,
and saying so plainly is better than pretending there is no tension.

### The honest status of the term

| Claim | Reality |
|---|---|
| "GEO is an established discipline" | The term is about two years old and contested |
| "There are GEO best practices" | There are retrieval properties, which are measurable |
| "You can rank in an assistant" | There is no ranking to see. You can measure citation |
| "It replaces SEO" | No. Most documentation traffic is still search |
| "Vendors can do it for you" | The work is rewriting your pages |

Present it internally as "making passages extract correctly", which is
checkable, rather than as GEO, which invites a debate about whether the term
means anything. Intel used the word, so use it on your résumé and describe the
mechanism in the interview.

### How to measure it, since the usual metrics do not exist

| Measurement | How |
|---|---|
| Does the right passage come back? | [Retrieval evaluation](retrieval-evaluation.md) with page-level expectations |
| Is the cited passage correct? | [Grounding checks](grounding.md) against the chunk, not the page |
| Do chunks contradict? | The checker above, in CI |
| Are identifiers findable? | Query your own index for each flag name |
| Does an assistant cite you? | Ask it, repeatedly, and record. Crude and the only direct signal |

## How to talk about it

**What a competent answer sounds like.** Define it by the unit, then give the
failure. "SEO optimises a page to be clicked; GEO optimises a passage to be
quoted correctly. The failure that taught me the difference was a page whose
first sentence said the retry default is 3 and whose last section said it
changed to 5 in 2.5. The page was accurate, reading order fixed it for a human,
and an assistant retrieved the first chunk and gave people the old value. So I
check that chunks are self-contained, that a claim carries its version
qualifier in the same chunk, and that no two chunks answer one question
differently."

**The follow-up is "is GEO a real thing or marketing",** and the answer should
concede the branding and keep the mechanism. The term is contested and about two
years old. What is not contested is that assistants retrieve passages, that a
passage can be wrong while its page is right, and that this is measurable with a
retrieval eval and a grounding check. Lead with the mechanism and the word stops
mattering.

**The tradeoff to volunteer.** Writing for extraction makes pages slightly worse
to read. Repeating "as of 2.5" in three consecutive sections is redundant for a
human and necessary for a machine, and replacing a tidy "what changed" section
with inline qualifiers scatters information a human would rather have in one
place. It is a genuine conflict between audiences, it resolves in favour of the
machine only where a wrong answer is expensive, and anyone claiming the two
audiences always want the same thing has not tried it.

**One sharper point.** The strongest observation is that **GEO is mostly a
rediscovery of standalone writing.** "Do not open a section with a pronoun" and
"state the condition with the claim" are decades-old technical-writing advice
that got skipped because a human reader could recover from violating them.
Retrieval removed that slack. So the work is less a new optimisation discipline
than an old quality bar that finally has a failure mode visible enough to fund,
which is the same pattern as [RAG](rag.md) surfacing content gaps and
[coding agents](coding-agents.md) surfacing unmarked fragments. Noticing that
pattern three times is worth saying: **machine consumers did not create these
defects, they made them measurable.**

## How to prove it

**The artifact.** A before-and-after page with the chunk-level audit, plus the
checker in CI.

**Three things to do, in order:**

1. **Run the golden path.** The before-and-after on one page, measured at the
   chunk level, is the demonstration and it takes five minutes to show.
2. **Find a real contradiction in a corpus you know.** A value stated in an
   introduction and corrected in a later section. They are common, and the
   checker finds them automatically. Expect to find one within the first
   twenty pages. If you do not, you are reading for sense rather than for
   contradiction, which is the harder habit and the whole exercise.
3. **Add the self-contained and qualifier checks to CI.** Thirty lines. The
   pronoun-opening check alone catches a surprising amount.

**What makes it credible rather than decorative.** Using the word GEO proves nothing and may cost you
credibility with a sceptic. A page rewritten for extraction, a chunk-level audit
showing which passage gets lifted, and a CI check for cross-chunk contradictions
demonstrates that you understand what assistants actually do with your content.

## Related

- [SEO for documentation](seo-for-docs.md), the half that is about being found
- [Chunking strategies](chunking.md), the unit this is all about
- [Structured data and JSON-LD](structured-data.md), the machine-readable layer
- [Retrieval evaluation](retrieval-evaluation.md), how to measure any of this
