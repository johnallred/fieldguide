---
title: Search and query log analysis
summary: "Query logs are the only direct statement of what readers wanted, and an attempt to substitute a hand-built retrieval proxy for them measures the proxy."
diataxis: explanation
audience: developer
concept: search-log-analysis
tags: [meas, supporting]
---

# Search and query log analysis

`supporting` · difficulty 2 · 3h

!!! quote "Adjacent, not quoted"
    Not named in either posting. The input that turns a hand-written evaluation set into a representative one.

**Prerequisites:** [Findability and search design](findability.md), [Documentation analytics](docs-analytics.md)

## What it is

Reading what people typed into your search box. It is the highest-value
reader-side signal in documentation and among the cheapest to collect, and it
differs in kind from everything else on a dashboard: page views say what people
found, queries say **what they were looking for**, including every time they
did not find it.

The most useful single output is the zero-result list, which is a list, in
readers' own words, of content you do not have.

## Why the job asks for it

Because every other way of deciding what readers want is the author guessing.

A documentation roadmap is usually assembled from support escalations, the
loudest internal stakeholder, and what the team believes is missing. Queries
are the only input coming from readers who were not motivated enough to file a
ticket, which is almost all of them.

The reason this sits beside [retrieval evaluation](retrieval-evaluation.md) in
this curriculum is narrower and more interesting. A golden set of questions is
hand-written, so it encodes the author's model of what readers ask. Query logs
are what turn that set from plausible into representative, and without them
there is no way to know which it is.

## The golden path

Try to do this without logs, fail, and work out what the failure is worth.
About thirty minutes. The first measurement gets published nowhere.

**Step 1: attempt the substitute**

With no query logs, the obvious move is to simulate the reader. Take the most
basic query anyone would type, a page's own name, and check whether that page
comes back first. Score it over the site's real search index of 1,358 entries:

```python
def search(q, limit=5):
    qt = toks(q)
    for loc, t in docs:
        tf = Counter(t)
        s = sum((tf[w] / len(t)) * math.log(N / (1 + df[w])) for w in qt if w in tf)
```

```
concepts searched by their own title: 90
rank of their own page: {1: 7, 2: 14, 3: 10, '4+': 42, 'none': 17}

not first for their own name: 83
   Information architecture   rank 9     top: paths/content-architect/#1-information-architecture
   Diátaxis                   rank None  top: paths/developer-educator/#5-designing-tutorials
   Content models             rank None  top: concepts/content-data-transformation/#read-first
```

**Seven of ninety pages rank first for their own title.** A catastrophic
findability result with an obvious story attached: generated navigation pages
carry concept names as headings, they are short, and a short document with the
term in its heading beats the long page that explains it.

The story is wrong.

**Step 2: check the mechanism before believing the number**

That story claims generated pages duplicate concept titles and compete with
them. The claim is structural, so it can be checked with no scorer at all:

```
concept titles appearing as an index entry's title outside their own page: 1 distinct
total such competing entries: 1
   Time to first success   concepts/quickstarts/#time-to-first-success   77 words
```

**One.** There is no duplication problem. The 7-of-90 figure came from my own
length normalisation: dividing term frequency by document length rewards short
sections, and a path page's one-line entry for a concept is about as short as a
document gets. MkDocs Material uses lunr, with boosted title fields and
different length handling, and does not rank this way.

I had built a proxy for search in order to avoid needing query logs, and the
proxy measured itself. That is this page's lesson, reached the expensive way:
**a hand-built retrieval model is not a substitute for knowing what readers
typed**, because its failures are indistinguishable from findings.

**Step 3: measure what does not depend on a ranking function**

Three properties are structural, so no scorer can corrupt them:

```
complete pages whose own title words are absent from their text: 0/106
pages absent from the search index:                                 0
index entry titles that are not unique:                            42
```

The first two are clean. The third is the real finding:

```
Related                   x109
What it is                x107
Why the job asks for it   x107
The golden path           x107
Reference                 x107
How to talk about it      x107
How to prove it           x107

entries carrying one of those seven titles: 751 of 1505  (50%)
```

**Half the search index carries one of seven titles.** The
page contract that makes this corpus consistent, and that CI enforces, has
produced 751 sections indistinguishable by title.

The disambiguating information exists: every entry carries its `location`, so
the page is recoverable, and Material's search UI uses it and shows the parent
page, so a human browsing the site is fine. Any consumer using `title` alone is
not, and that now includes retrieval pipelines and assistants reading an index
directly. It is the same defect as a grounding report naming the page when it
checked the chunk: the identifier has to carry the section, or ninety-one
things look like one thing.

**Step 4: the test logs would have passed**

A golden set is meant to be representative. Twenty cases, hand-written by the
author of the corpus. Then a real reader arrived with a real question, the only
genuine query this project has ever received:

> what is docpack actually creating or doing, and what should I be looking at

Scored against the twenty:

```
closest golden case: llms-txt-what   what is llms.txt and who proposed it      shared key terms: 1
closest golden case: install         how do I install docpack                  shared key terms: 1
closest golden case: exit-codes      what exit codes does the command return   shared key terms: 1
```

**One shared key term, at best.** A twenty-case set written specifically to
represent reader questions held nothing resembling the first real one, and the
missing case was not exotic: it was "what does this thing do", which is the
question every reader has first.

One query is not a sample. The direction is not ambiguous either. The author
wrote twenty questions about what the corpus explains, and the reader asked
about what it had not thought to say.

**Step 5: so collect them from day one**

Internal search logging is a few lines of configuration and the only
instrumentation in this field that reports content you do not have. Everything
else measures the content you do.

**What you built.** A retrieval proxy that produced a plausible wrong finding,
the structural check that disproved it, three measurements that survive without
a scorer including 47 per cent of an index sharing seven titles, and a
demonstration that a hand-written query set missed the first real question it
met.

## Reference

### What queries say that nothing else does

| Signal | Means |
|---|---|
| Zero-result queries | Content you do not have, in readers' words |
| High volume, low click-through | The page exists and the result looks wrong |
| Queries that are error messages | Readers arrive with a symptom, not a topic |
| Words your docs never use | A [vocabulary](style-guide.md) gap, not a content gap |
| Queries repeated within a session | The first result failed |
| A query straight after a page view | That page did not answer |

The fourth row is the most commonly misread. A term you do not use is usually
not a missing page, it is a missing synonym on a page you already have, and
writing a new page is the expensive way to fix it.

### What to do with each finding

| Finding | Response |
|---|---|
| Zero results, concept missing | Write it |
| Zero results, concept present | Add the reader's words to the page |
| High volume, wrong page first | Fix titles, summaries and headings |
| Error-message queries | Index error strings; readers paste them verbatim |
| A query refined twice in a session | Watch the session, not the query |
| Queries for things you removed | A [retirement](content-retirement.md) redirect is missing |

### Without logs, what is still honest

| Check | Needs a ranking function |
|---|---|
| Does each page contain its own key terms | No |
| Is every page in the index | No |
| Are index entry titles unique | No |
| Are meta descriptions distinct | No |
| Do synonyms for each concept appear anywhere | No |
| Does each page rank first for its own name | **Yes, see step 2** |
| Which of two retrievers is better | **Yes** |

Everything above the line is worth doing on day zero. Everything below needs
either the real search engine or real queries, and a scorer you wrote yourself
will answer confidently and wrongly.

### Privacy, briefly

Query strings are user-submitted text, and people paste surprising things into
search boxes: internal hostnames, tokens, customer names. Aggregate before
storing, keep a short retention window, and do not log queries alongside an
identity unless someone agreed to that. None of this is a reason to skip
collection; it is a reason to collect the aggregate rather than the transcript.

### Why this concept is adjacent rather than quoted

Neither posting names search logs, and both ask for measurement that depends on
them. NVIDIA's "AI answer quality" and "repeat questions" are each evaluation
over a question set, and a question set without query data is the author's
guess about readers, which is exactly the gap step 4 measures.

## How to talk about it

**Lead with the asymmetry.** "Page views tell me what people found. Queries tell
me what they were looking for, including every time they did not find it. The
zero-result list is the only artifact in documentation analytics that describes
content you do not have, and it costs a few lines of configuration to start
collecting."

**The follow-up is what I did without logs, and the honest answer is that I got
it wrong.** I built a scorer over my own search index to check whether each page
ranks first for its own name, and got seven of ninety, which looked like a
catastrophe with a tidy explanation about generated pages competing for terms.
The explanation was structural, so I checked it, and exactly one competing
entry existed. The seven-of-ninety was my own length normalisation rewarding
short sections. I had built a proxy for search to avoid needing query data, and
measured the proxy.

**What survives without logs is worth saying too.** Structural checks cannot be
corrupted by a scorer: every page contains its own key terms, every page is in
the index, and 751 of 1,505 entries carry one of seven titles because the page
contract gives every page the same seven sections. A human browsing Material is
fine, since the UI shows the parent page, but anything consuming `title` alone,
a retrieval pipeline included, sees ninety-one identical things.

**The point to close on.** My golden set has twenty hand-written questions and
was meant to be representative. The first real reader asked what the thing
actually produces and what he should be looking at, and that shared at most one
key term with any of the twenty. One query is not a sample, but the direction is
not ambiguous: I wrote twenty questions about what the corpus explains, and the
reader asked about what it had not thought to say. Logs close that gap and
nothing else does.

## How to prove it

**The artifact.** Search logging enabled on a corpus you own, and a weekly
zero-result list somebody actually reads.

**Three things to do, in order:**

1. Turn on internal search logging if it is off. It is the cheapest
   instrumentation in this field and the only one that reports absence.
2. Compare your evaluation question set against the last ten real questions you
   received from anybody, counting shared terms. Predict the number first;
   mine was one.
3. Check whether your index entry titles are unique. If your pages share a
   template they are not, and any consumer reading titles without locations is
   presenting duplicates.

**What makes it credible rather than decorative.** The structural measurements
run against this guide's built search index and are reproducible; the failed
proxy and its disproof are both recorded above rather than tidied away. What
does not exist is a single query log: no site has been published, so there are
no queries, no zero-result list and no click-through data, and the one real
reader question in step 4 arrived in conversation rather than through a search
box. The [demonstrated](../demonstrated.md) page records the concept as having
no demonstration on the log side.

## Related

- [Findability and search design](findability.md), the corpus-side half
- [Documentation analytics](docs-analytics.md), where this sits among the signals
- [Retrieval evaluation](retrieval-evaluation.md), the question set logs make representative
- [Repeat-question analysis](repeat-questions.md), the same signal from the support channel
- [Style guides and terminology management](style-guide.md), where a synonym gap gets fixed
- [Agent-ready content](agent-ready-content.md), the consumer that reads titles without locations
