---
title: Documentation-backed AI assistants
summary: Wrapping retrieval in a product, where the hard parts are refusal, conversation state, and what happens when it is wrong in public.
diataxis: explanation
audience: developer
concept: ai-assistants
tags: [ai, core]
---

# Documentation-backed AI assistants

`core` · difficulty 3 · 8h

> structure and package content for RAG, internal assistants, and agentic workflows

> Source: nvidia posting, verbatim

**Prerequisites:** [RAG pipelines](rag.md), [Grounding and citation](grounding.md)

## What it is

A product built on [retrieval](rag.md): a developer asks a question in prose and
gets an answer with citations. NVIDIA's phrase is "internal assistants", which
is the common case, since an internal assistant has a known audience and a
forgiving failure mode.

The retrieval is the easy half. The hard half is everything around it: when to
refuse, what to do with a follow-up question, and how a wrong answer gets
noticed and fixed.

## Why the job asks for it

NVIDIA names it twice, in the AI-ready bullet and under ways to stand out ("RAG
pipelines, AI assistants, MCP servers"). Intel's version is "makes
documentation discoverable and usable by both developers and AI assistants",
which is the other side: being the corpus an assistant reads.

What makes it `core` rather than a product-management concern is that the
decisions are documentation decisions. **Refusal thresholds, citation display
and scope boundaries are all editorial judgements**, and a team that treats them
as engineering ships an assistant that answers questions about billing because
nobody said it should not.

On a Tuesday it is the thing that determines whether people keep using it. The
assistant has been live a month. Usage dropped after week two. Looking at the
logs: 40% of questions get a refusal, almost all because they are follow-ups
that lost the subject ("what about for quantised models?"), and the refusals are
indistinguishable from "we have no documentation on this". **Nobody filed a bug,
they just stopped asking**, which is the characteristic failure of this product
category and it is invisible without instrumentation.

## The golden path

Build the assistant layer on top of a retriever: refusal, follow-up rewriting,
scope, and a feedback loop. Fifty minutes, dependency-free.

**Step 1: the retriever and a corpus with a scope boundary**

```bash
mkdir -p assistant-drill && cd assistant-drill
cat > corpus.json <<'EOF'
[
  {"id": "c1", "source": "reference/flags.md", "crumb": "Server flags > batch_size", "kind": "reference",
   "text": "batch_size controls how many requests are grouped per forward pass. The default is 32."},
  {"id": "c2", "source": "how-to/latency.md", "crumb": "Reduce latency > Lower the batch size", "kind": "how-to",
   "text": "If your p99 is too high, set batch_size to 1 or 2. A batch of 32 waits for 32 requests to arrive."},
  {"id": "c3", "source": "how-to/quantised.md", "crumb": "Quantised models > Batch sizing", "kind": "how-to",
   "text": "Quantised models tolerate much larger batches. Start at 64 and raise while watching memory."},
  {"id": "c4", "source": "reference/flags.md", "crumb": "Server flags > max_memory_gb", "kind": "reference",
   "text": "max_memory_gb caps the GPU memory the server will allocate. The default is 16."}
]
EOF
python3 -c "import json; print(len(json.load(open('corpus.json'))), 'chunks')"
```

**Step 2: the assistant layer**

```bash
cat > assistant.py <<'PY'
"""The layer between a retriever and a person.

The retrieval is taken as given; what follows is the product. Four
decisions, and three of them are editorial rather than technical.

  SCOPE      refuse questions the corpus was never meant to answer, with a
             message that says so, distinctly from "I could not find it"
  FOLLOW-UP  rewrite "what about for quantised models?" into a standalone
             query, or the retriever sees four meaningless words
  REFUSAL    a confidence floor, with the refusal naming WHY it refused
  FEEDBACK   log every answer with its retrieval trace, so a wrong answer is
             a fixable report rather than a complaint
"""
import json
import math
import re
from collections import Counter
from dataclasses import dataclass, field

K1, B = 1.2, 0.75

#: Below this top score, the assistant refuses rather than answering from weak
#: evidence.
#:
#: This number was MEASURED, not chosen. Step 3 of the golden path scores ten
#: questions whose answerability is known, and on this corpus the answerable
#: ones land at 2.29 and above while the gaps top out at 1.59. Any floor
#: between those separates them; 1.9 is the midpoint.
#:
#: The first draft of this page guessed 1.2 and four of five known gaps were
#: answered confidently from an unrelated chunk. A guessed threshold is the
#: single commonest way an assistant fabricates.
CONFIDENCE_FLOOR = 1.9

#: Subjects the corpus does not cover. Refusing these with a DIFFERENT
#: message from "not found" is the whole point: one is a scope boundary and
#: the other is a documentation gap, and conflating them means the gap
#: reports are buried in the noise.
OUT_OF_SCOPE = {
    "billing": ["invoice", "billing", "price", "cost per", "subscription", "refund"],
    "accounts": ["password", "sign in", "login", "my account", "2fa"],
    "legal": ["license", "licence", "terms of service", "gdpr", "sla"],
}

#: A follow-up has no subject of its own. These are the giveaways.
FOLLOWUP_MARKERS = (
    "what about", "and for", "does that", "is it", "what if", "how about",
    "same for", "and if", "why not",
)


def tokenize(text):
    """Tokenize, indexing an underscore identifier both whole and split.

    `batch_size` is emitted as `batch_size`, `batch` and `size`. Keeping only
    the whole form means the question "what is the default batch size" can
    never match the chunk that documents `batch_size`, which is a real defect
    this guide found twice: once on the retrieval-evaluation page and again
    here, where it sent a reference question to a how-to chunk.

    Splitting only is also wrong, since it destroys the exact-identifier match
    that lexical search exists for. Both forms, indexed together.
    """
    out = []
    for token in re.findall(r"[a-z0-9_]+", text.lower()):
        if len(token) <= 1:
            continue
        out.append(token)
        if "_" in token:
            out.extend(part for part in token.split("_") if len(part) > 1)
    return out


class Retriever:
    def __init__(self, chunks):
        self.chunks = chunks
        self.docs = [Counter(tokenize(f"{c['crumb']} {c['text']}")) for c in chunks]
        self.lengths = [sum(d.values()) for d in self.docs]
        self.avg = sum(self.lengths) / len(self.docs)
        df = Counter()
        for d in self.docs:
            df.update(d.keys())
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - c + 0.5) / (c + 0.5)) for t, c in df.items()}

    def search(self, query, limit=3):
        terms = tokenize(query)
        scored = []
        for chunk, doc, length in zip(self.chunks, self.docs, self.lengths):
            score = 0.0
            for t in terms:
                f = doc.get(t, 0)
                if not f:
                    continue
                norm = 1 - B + B * (length / self.avg)
                score += self.idf.get(t, 0.0) * (f * (K1 + 1)) / (f + K1 * norm)
            if score > 0:
                scored.append((score, chunk))
        scored.sort(key=lambda s: (-s[0], s[1]["id"]))
        return scored[:limit]


@dataclass
class Turn:
    """One exchange, with everything needed to diagnose it later."""

    question: str
    rewritten: str = ""
    outcome: str = ""  # answered | refused_scope | refused_confidence
    reason: str = ""
    retrieved: list = field(default_factory=list)
    answer: str = ""
    cited: list = field(default_factory=list)


def classify_scope(question):
    lowered = question.lower()
    for topic, cues in OUT_OF_SCOPE.items():
        for cue in cues:
            if cue in lowered:
                return topic
    return None


def is_followup(question):
    lowered = question.lower().strip()
    return any(lowered.startswith(m) or f" {m}" in lowered for m in FOLLOWUP_MARKERS)


def rewrite(question, history):
    """Turn a follow-up into a standalone query using the last subject.

    Crude and deliberately so: it appends the previous question's content
    words. A production version asks a small model to rewrite, which is
    better and introduces a failure mode of its own. Either way the point is
    that SOMETHING must do this, because "what about for quantised models?"
    is four words with no subject and the retriever has no memory.
    """
    if not history or not is_followup(question):
        return question
    previous = history[-1].rewritten or history[-1].question
    carried = [w for w in tokenize(previous) if w not in set(tokenize(question))]
    return f"{question} {' '.join(carried)}".strip()


class Assistant:
    def __init__(self, retriever):
        self.retriever = retriever
        self.history: list[Turn] = []
        self.log: list[Turn] = []

    def ask(self, question):
        turn = Turn(question=question)

        topic = classify_scope(question)
        if topic:
            turn.outcome = "refused_scope"
            turn.reason = topic
            turn.answer = (
                f"I only cover the widget platform documentation, and {topic} is "
                f"outside that. Try the {topic} team's own resources."
            )
            self.log.append(turn)
            return turn

        turn.rewritten = rewrite(question, self.history)
        hits = self.retriever.search(turn.rewritten)
        turn.retrieved = [(round(s, 2), c["id"], c["crumb"]) for s, c in hits]

        if not hits or hits[0][0] < CONFIDENCE_FLOOR:
            turn.outcome = "refused_confidence"
            top = hits[0][0] if hits else 0.0
            turn.reason = f"top score {top:.2f} below floor {CONFIDENCE_FLOOR}"
            turn.answer = (
                "I could not find this in the documentation. This may be a gap; "
                "the question has been logged."
            )
            self.log.append(turn)
            self.history.append(turn)
            return turn

        score, chunk = hits[0]
        turn.outcome = "answered"
        turn.answer = f"{chunk['text']} [{chunk['id']}]  (source: {chunk['source']})"
        turn.cited = [chunk["id"]]
        self.log.append(turn)
        self.history.append(turn)
        return turn

    def report(self):
        """What the team looks at weekly. This is the product's real output."""
        total = len(self.log)
        by_outcome = Counter(t.outcome for t in self.log)
        gaps = [t for t in self.log if t.outcome == "refused_confidence"]
        scope = Counter(t.reason for t in self.log if t.outcome == "refused_scope")

        print(f"  turns: {total}")
        for outcome, count in sorted(by_outcome.items()):
            print(f"    {outcome:<22} {count:>2}  ({count / total:.0%})")
        if scope:
            print(f"    out-of-scope topics asked: {dict(scope)}")
        if gaps:
            print("    questions with no good answer (a content backlog):")
            for turn in gaps:
                print(f"      {turn.question!r}  [{turn.reason}]")
PY
echo "assistant written"
```

**Step 3: calibrate the refusal threshold before using it**

The confidence floor is the single most consequential number in the product,
and it cannot be reasoned to. Measure it.

```bash
cat > calibrate.py <<'PY'
"""Measure the refusal threshold instead of guessing it.

Two lists: questions you know the corpus answers, and questions you know it
does not. If the two score distributions separate, any floor between them
works. If they overlap, no threshold can distinguish them and the honest
conclusion is that refusal alone will not save you.
"""
import json

from assistant import Retriever

ANSWERABLE = [
    "what is the default batch size",
    "how do I cap gpu memory",
    "my p99 is too high",
    "batch size for quantised models",
    "what does max_memory_gb do",
]
GAPS = [
    "how do I rotate a signing key",
    "how do I enable tls",
    "what is the retry policy",
    "how do I add a webhook",
    "where are the logs",
]

retriever = Retriever(json.load(open("corpus.json")))


def top(question):
    hits = retriever.search(question)
    return (hits[0][0], hits[0][1]["id"]) if hits else (0.0, "none")


answerable, gaps = [], []
print("ANSWERABLE                             score   top")
for question in ANSWERABLE:
    score, cid = top(question)
    answerable.append(score)
    print(f"  {question:<36} {score:6.2f}   {cid}")

print("GAPS                                   score   top")
for question in GAPS:
    score, cid = top(question)
    gaps.append(score)
    print(f"  {question:<36} {score:6.2f}   {cid}")

low, high = min(answerable), max(gaps)
print(f"\n  lowest answerable {low:.2f}, highest gap {high:.2f}")
if low > high:
    print(f"  clean separation: any floor in ({high:.2f}, {low:.2f}) works; "
          f"midpoint {(low + high) / 2:.2f}")
else:
    print("  OVERLAP: no threshold separates these. Refusal alone cannot fix this.")
PY
python3 calibrate.py
```

**Step 4: a realistic conversation, including the awkward turns**

```bash
cat > session.py <<'PY'
import json

from assistant import Assistant, Retriever

assistant = Assistant(Retriever(json.load(open("corpus.json"))))

conversation = [
    "what is the default batch size",            # answerable
    "what about for quantised models?",          # follow-up, no subject
    "how do I cap gpu memory",                   # answerable, new subject
    "what about for quantised models?",          # same follow-up, new subject
    "how do I get a refund",                     # out of scope
    "how do I rotate a signing key",             # a real gap
]

for question in conversation:
    turn = assistant.ask(question)
    print(f"Q: {question}")
    if turn.rewritten and turn.rewritten != question:
        print(f"   rewritten -> {turn.rewritten!r}")
    print(f"   [{turn.outcome}] {turn.reason}")
    print(f"   {turn.answer[:88]}")
    print()

print("=== weekly report ===")
assistant.report()
PY
python3 session.py
```

**Step 5: show what the follow-up rewriting is worth**

```bash
python3 - <<'PY'
import json

from assistant import Assistant, Retriever

chunks = json.load(open("corpus.json"))
pair = ["what is the default batch size", "what about for quantised models?"]

for label, rewriting in (("with rewriting", True), ("without rewriting", False)):
    assistant = Assistant(Retriever(chunks))
    if not rewriting:
        assistant_rewrite = None
        import assistant as module
        module.rewrite = lambda question, history: question
    print(f"=== {label} ===")
    for question in pair:
        turn = assistant.ask(question)
        print(f"  {question!r}")
        print(f"    -> [{turn.outcome}] {turn.answer[:70]}")
    print()
PY
```

**What you built.** An assistant layer with a scope boundary, follow-up
rewriting, a measured confidence floor, and a weekly report that is a content
backlog.

The report is the deliverable, not the answers:

```
turns: 6
  answered                4  (67%)
  refused_confidence      1  (17%)
  refused_scope           1  (17%)
  out-of-scope topics asked: {'billing': 1}
  questions with no good answer (a content backlog):
    'how do I rotate a signing key'  [top score 1.23 below floor 1.9]
```

**Every low-confidence refusal is a reader telling you, in their own words,
about a page you have not written.** Every out-of-scope question tells you what
people think this thing is for. Neither is available from a search box.

### Two things the first draft got wrong, both measured

**The guessed threshold fabricated.** The first version of this page set the
confidence floor to 1.2 by eye. At that floor, "how do I rotate a signing key"
was answered confidently from the `batch_size` chunk, and four of five known
gaps got answers. Calibration puts the answerable questions at 2.29 and above
and the gaps at 1.59 and below, so the floor belongs at about 1.9. **A guessed
threshold is the commonest way one of these fabricates**, and the fix costs ten
labelled questions.

**The tokenizer sent a reference question to a how-to page.** "What is the
default batch size" returned the latency guide, because `batch_size` with an
underscore cannot match "batch size" with a space. That is the same defect
[retrieval evaluation](retrieval-evaluation.md) found on its own corpus, showing
up a second time in a different component. Indexing underscore identifiers both
whole and split fixes it, and it *strengthens* the exact-identifier case rather
than weakening it: "what does `max_memory_gb` do" went from 1.73 to 6.06.

Finding the same bug twice in two components is the argument for the tokenizer
being a shared, tested function rather than six lines copied into each
retriever.

## Reference

### The four decisions, and which are editorial

| Decision | Who owns it | Failure if wrong |
|---|---|---|
| Scope boundary | **Documentation** | Answers questions about billing from a page about batching |
| Refusal threshold | **Documentation**, with data | Too low: fabrication. Too high: people stop asking |
| Citation display | **Documentation** | A reader cannot verify, so trust is binary |
| Follow-up handling | Engineering | Half of all turns fail and look like content gaps |

Three of four are editorial. That is the argument for this concept living in a
documentation role rather than in a platform team.

### Two refusals that must not look the same

| Refusal | Means | Action it should produce |
|---|---|---|
| Out of scope | We never intended to cover this | Point elsewhere. No backlog item |
| Low confidence | We should cover this and apparently do not | **A backlog item with the reader's wording** |

Conflating them is the commonest design mistake, and it destroys the single most
valuable output of the whole product. A log where both read "I could not find
this" cannot be sorted into gaps and non-gaps.

### Why follow-ups are most of the problem

A standalone-question assistant is a search box with better prose. People
immediately use it as a conversation:

| Turn | Words the retriever sees without rewriting |
|---|---|
| "what is the default batch size" | the whole question |
| "what about for quantised models?" | `about`, `for`, `quantised`, `models` |
| "is that per request or per batch?" | `that`, `per`, `request`, `batch` |
| "why?" | nothing |

Rewriting options, in increasing cost:

| Approach | Quality | Cost |
|---|---|---|
| Append the previous question's terms | crude, better than nothing | trivial |
| Keep a running subject and prepend it | decent | cheap |
| Ask a small model to rewrite into a standalone query | good | a model call per turn |
| Pass the whole history to the retriever | poor; old terms dominate | trivial |

The last row is what teams do by accident, and it degrades as conversations
lengthen.

### What to log, per turn

| Field | Why |
|---|---|
| The question, verbatim | Reader vocabulary, which is your [SEO](seo-for-docs.md) and eval input |
| The rewritten query | Otherwise a rewriting bug looks like a retrieval bug |
| The ranked retrieval list with scores | [The only way to debug](rag.md) |
| Outcome and reason | Separates scope refusals from gaps |
| Citations | So you can check [grounding](grounding.md) after the fact |
| Feedback, if any | The one signal you cannot reconstruct later |

### The metrics that matter

| Metric | Healthy | What it tells you |
|---|---|---|
| Refusal rate | 5 to 20% | Near zero means fabrication; over 40% means people will leave |
| Gap refusals per week | declining | Whether the backlog is being worked |
| Repeat question rate | declining | Whether answers are landing |
| Citation click-through | nonzero | Whether anyone verifies, and whether the pages are good |
| Turns per conversation | over 1 | If it is 1.0, follow-ups are failing silently |

**Turns per conversation is the underrated one.** An assistant with an average
of 1.1 turns is being used as a search box, which usually means follow-ups fail
and people learned not to try.

### Honest limitations

| Limitation | Consequence |
|---|---|
| It inherits every error in the corpus | A grounded answer from a wrong page is wrong |
| A stale index is a confident liar | Rebuild on publish, and surface the index date |
| Silent abandonment | The main failure mode, invisible without the metrics above |
| It cannot say "nobody wrote this yet" without you logging it | Gaps look like failures |
| Internal and external need different scope and tone | And different [visibility filtering](partner-documentation.md) |

## How to talk about it

**What a competent answer sounds like.** Lead with the two refusals, because it
is the design decision that shows you have operated one. "The retrieval is the
easy half. The thing that decided whether ours was useful was separating two
refusals: out of scope, which points you elsewhere, and low confidence, which
says we should cover this and do not and logs your exact wording. Conflating
them throws away the best output of the whole product, which is a content
backlog in readers' own words. After that, follow-up rewriting, because people
converse immediately and 'what about for quantised models' is four words with no
subject."

**The follow-up is "how do you set the confidence threshold",** and the answer
has to be empirical or it signals you guessed. You need a labelled set: questions
you know the corpus answers and questions you know it does not, then pick the
floor that minimises both fabrication and false refusal. That is
[output evaluation](output-evaluation.md) applied to a product decision, and the
threshold moves whenever the corpus or the retriever changes, which is why it
belongs in CI rather than in a config file somebody tuned once.

**The tradeoff to volunteer.** An assistant reduces the number of people who read
your documentation, and that is partly a loss. A reader who lands on a page sees
the surrounding caveats, the related links, and the thing they did not know to
ask about. A reader who gets a paragraph gets exactly what they asked for and
none of the context, so the omission failure from
[grounding](grounding.md) gets systematically worse: every answer is correct and
narrower than the page. Citations partly compensate, and only if people click
them, which is why click-through is on the metrics list.

**One sharper point.** The strongest framing is that **an assistant is a measurement
instrument pointed at your documentation.** Its refusals are your gaps, its
repeat questions are your unclear pages, and its question log is the vocabulary
your readers actually use, which is the input
[SEO](seo-for-docs.md), [chunking](chunking.md) and
[evaluation sets](retrieval-evaluation.md) all need and almost nobody has. A
documentation team that ships one and treats the logs as a product feature has
acquired the user research it was never funded to do. That reframes the project
from an AI initiative into instrumentation, which is both true and a much better
pitch.

## How to prove it

**The artifact.** An assistant with the two distinct refusals, a turn log, and a
weekly report that lists gap refusals with the reader's wording.

**Three things to do, in order:**

1. **Run the golden path.** The weekly report is the demonstration: it turns a
   conversation into a content backlog, which is the thing nobody expects.
2. **Calibrate the threshold on a labelled set.** Twenty questions you know are
   answerable and ten you know are not. Report the refusal rate at three
   thresholds. That is a small experiment with a real number.
3. **Instrument turns per conversation** on anything you ship. If it is near
   1.0, your follow-up handling is broken and nobody has told you.

**What makes it credible rather than decorative.** A working chatbot over docs is a weekend project. A
scope boundary, two semantically different refusals, a logged rewriting step,
and a report that produces a prioritised content backlog demonstrates that you
built it as documentation infrastructure rather than as a demo.

### How this would be demonstrated elsewhere

This environment has the retrieval half, in `docpack`, and not the generation
half. So the pipeline this page describes exists up to the point where an
answer would be produced, and stops there.

**What you need.** The existing retrieval stack plus a model, and one thing that
is harder to get than either: a set of questions real readers asked. The
twenty-case golden set substitutes for it and is written by the corpus's author,
which makes it systematically optimistic, as
[search log analysis](search-log-analysis.md) measures.

**What you would run.** Wire the retrieved chunks into a prompt, generate
answers for every case, and then score the system end to end rather than in
halves.

```
question -> retrieve(k) -> prompt -> answer -> grounded? cited? refused?
```

**What you would see.**

| Observation | Rough magnitude | What it tells you |
|---|---|---|
| End-to-end correct answers | below your `grounded@k` | Retrieval sets a ceiling generation does not reach |
| Correct answers from wrong chunks | a few per cent | The model knew it anyway; your corpus got no credit |
| Wrong answers from correct chunks | the interesting bucket | A generation or prompt problem, not a retrieval one |
| Answers on questions with no corpus answer | mostly invented | The reason a refusal path is mandatory |
| Effect of raising `k` from 3 to 10 | small, then negative | More context is not more accuracy |

The second and third rows are why end-to-end evaluation cannot be replaced by
retrieval metrics. A system can look healthy on `hit@1` and answer badly, or
answer well while retrieving nothing useful because the model already knew the
answer, and only the paired measurement distinguishes them. On a documentation
assistant the second case is the dangerous one: it works until a reader asks
about something your product changed last week.

**How you would know it had failed.** End-to-end accuracy above your grounding
ceiling means the model is answering from its own weights, so the test is not
measuring your corpus. Accuracy that does not drop when you shuffle the
retrieved chunks means the same thing, and it is the cheapest check available:
corrupt the context deliberately and confirm the answers get worse.

## Related

- [RAG pipelines](rag.md), the half underneath this
- [Grounding and citation](grounding.md), what makes an answer checkable
- [Hallucination and guardrails](hallucination-guardrails.md), what to put in front of the answer
- [Repeat-question analysis](repeat-questions.md), what to do with the logs
