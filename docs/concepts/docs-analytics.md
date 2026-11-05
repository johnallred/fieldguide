---
title: Documentation analytics
summary: "Corpus-side analytics need no audience and answer a surprising amount; reader-side analytics need one, and cannot see the terminal where most developer documentation is actually read."
diataxis: explanation
audience: developer
concept: docs-analytics
tags: [meas, core]
---

# Documentation analytics

`core` · difficulty 2 · 4h

!!! quote "Asked for by name"
    Intel: "Instrument documentation analytics and convert findings into improvements to docs, samples, and tooling"

**Prerequisites:** [Documentation CI](documentation-ci.md)

**Leads to:** [Measuring AI answer quality](ai-answer-quality.md), [Search and query log analysis](search-log-analysis.md), [Support deflection](support-deflection.md), [Time to first success](time-to-first-success.md), [Turning developer feedback into changes](developer-feedback-loops.md)

## What it is

Instrumenting a documentation corpus so that claims about it can be checked.
The word covers two activities with almost nothing in common, and conflating
them is why most documentation-analytics work goes nowhere.

**Corpus-side analytics** measure the artifact: how pages connect, what is
reachable, what is findable, what is stale, which claims have no evidence. They
need no audience and work on day zero.

**Reader-side analytics** measure behaviour: page views, search queries, scroll
depth, exit rates, the path through a funnel. They need an audience, a
pipeline, and usually a privacy review.

Intel's bullet says "instrument ... and convert findings into improvements",
and that second half is the part that matters: the deliverable is a change, not
a dashboard.

## Why the job asks for it

Because without it every statement about documentation is an assertion, and
documentation people make a great many statements.

"The quickstart is too long." "Nobody can find the auth page." "That tutorial
is our most valuable asset." Each is testable and almost never tested, so
priorities get set by whoever was most recently annoyed. An instrumented corpus
replaces that with a number somebody can disagree with, which is a lower bar
than being right and a far better starting position.

The reason the split matters is practical. Most teams asking for documentation
analytics are imagining the reader-side dashboard, cannot have it yet (no
traffic, no pipeline, no consent), and conclude they cannot measure anything.
They can measure a great deal. It is all on the other side.

## The golden path

Build the analytics available with no audience whatsoever, against a real
corpus. About thirty minutes, and the last step changes how you read any
documentation dashboard.

Every figure below is one run, when the tree held 121 pages. It holds more now,
and the point of the step is the impossible ratio rather than the count, so the
output is kept as it was printed rather than restated each time a page is
added. `fieldguide audit` is where to read the current numbers.

**Step 1: the link graph, which is most of corpus-side analytics**

```python
LINK = re.compile(r"\]\((?!https?:|mailto:)([^)#]+?)(?:#[^)]*)?\)")
for page in sorted(docs.rglob("*.md")):
    for match in LINK.finditer(page.read_text()):
        dest = (page.parent / match.group(1)).resolve()
        ...
```

```
pages in the tree: 121
internal links: 1127

pages nothing links to: 1
   index.md

reachable from index.md by following links: 134/121
```

**One hundred and thirty-four reachable out of 121.** An impossible ratio, and
the signal to fix the measurement rather than publish it.

**Step 2: two different populations**

The traversal was collecting link *targets* while the denominator counted
*pages*, so every link pointing at something that is not a page in the tree
inflated the numerator. Constrain the traversal to real pages, and report the
remainder separately instead of silently absorbing it:

```
pages: 121   links to real pages: 1108
link targets that are not pages in this tree: 14 distinct
   install.md                                 x9
   guide.md                                   x4
   {BASE}/docs/{path.name}                    x2
   tuning.md                                  x2
```

Those fourteen are filenames inside golden-path code samples, belonging to the
fictional corpora the exercises build. Correct content, and not links, which is
why the link checker had never flagged them.

A measurement that counts one population and reports it as another is the most
common analytics defect there is, and the hardest to notice, because the number
looks like a number.

**Step 3: the corrected picture**

```
reachable from index.md: 121/121
clicks from the front door: {0: 1, 1: 8, 2: 111, 3: 1}
unreachable by any link path: 0
```

Everything is reachable, and the shape is the finding: **nine pages in ten sit
exactly two clicks from the front door**, one at three. That is a flat corpus,
which is right for a reference guide and would be a warning in a tutorial
series, where depth should track sequence.

One page has nothing linking to it, and it is `index.md`. Correct: a front door
is entered, not linked.

**Step 4: what else needs no audience**

```
search index entries:                              1358
pages absent from the search index:                   0
concept pages with a distinct meta description:  106/106
pages whose longest sentence exceeds 45 words:    38/82
golden paths with no stated result:                0/82
demonstrations resolving to real concepts:           50
concepts with no demonstration anywhere:             56
```

Every line is a finding, each points at specific pages, and none required a
pipeline, a cookie banner, or a quarter of accumulated traffic.

**Step 5: the limit, which arrived unannounced**

On the day this page was written, the project's first real reader followed the
README of the companion repository, ran every command in its quick start,
watched all of them exit zero, and reported that he could not tell what the
library did.

Now ask what reader-side analytics would have shown.

```
page views in that session:   0
search queries:               0
time on page:                 none
exit page:                    none
funnel step reached:          not applicable
```

**Zero, because he never opened the site.** He read a README on a code host and
worked in a terminal, which is where developer documentation is mostly
consumed and where no analytics system has any visibility whatsoever. The most
important documentation failure in this project was invisible to the entire
reader-side category, and it surfaced because a person said something.

That is not an argument against reader-side analytics. It is the boundary of
the instrument. A dashboard reporting healthy numbers for a corpus nobody can
get started with is reporting on the subset of readers who got far enough to be
counted.

**What you built.** A corpus-side analytics report over the whole corpus that
needed no audience, a measurement bug caught by an impossible ratio, and a worked
example of the failure class the other half of analytics cannot see.

## Reference

### The two halves

| | Corpus-side | Reader-side |
|---|---|---|
| Needs an audience | No | Yes |
| Available on day zero | Yes | No |
| Sees terminal and README use | Yes | No |
| Sees what readers wanted | No | Partly |
| Points at a specific page | Usually | Rarely |
| Can be confidently wrong | Yes | Yes |
| Privacy review | No | Usually |

The fourth row is reader-side analytics' real advantage and the reason to build
it eventually: a corpus-side check can tell you a page is unreachable, never
that nobody wanted it.

### Corpus-side measurements, roughly by value

| Measurement | Finds |
|---|---|
| Reachability from the front door | Pages that exist and cannot be arrived at |
| Click depth distribution | A corpus shaped wrongly for its purpose |
| Inbound links per page | Orphans, and accidentally load-bearing pages |
| Presence in the search index | Content that is live and unfindable |
| Distinct meta descriptions | Pages indistinguishable in results |
| Key terms absent from their own page | [Findability](findability.md) failures |
| Review age against change rate | [Freshness](freshness-monitoring.md) candidates |
| Claims with no demonstration | Where a corpus overstates itself |
| Per-page maximum sentence length | [Load](cognitive-load.md) outliers |

### Reader-side measurements, and what each is worth

| Measurement | Worth | Caveat |
|---|---|---|
| Internal search queries | High | The clearest statement of intent available |
| Zero-result searches | Very high | A list of content you do not have |
| [Support ticket volume](support-deflection.md) | High | Confounded by everything |
| Entry pages | Medium | Where people arrive, not whether it helped |
| Page views | Low | Popularity, not usefulness |
| Time on page | Very low | Confused and careful reading look identical |
| Scroll depth | Very low | Mostly measures page length |
| "Was this helpful?" | Near zero | Measures mood, and never produces bad news |

The top two are worth more than everything below them combined, which is why
[search log analysis](search-log-analysis.md) is a concept of its own.

### Where developer documentation is actually read

| Surface | Reader-side visibility |
|---|---|
| The documentation site | Full |
| A README on a code host | Almost none |
| A terminal, via `--help` | None |
| An IDE hover or completion | None |
| A package registry page | Vendor-dependent |
| An assistant answering from the corpus | None, unless you built the assistant |
| A snippet copied into somebody's codebase | None |

Only the first row is instrumented, and it is not obviously the largest. Any
claim resting on reader-side analytics alone is a claim about one surface.

### Converting findings into changes

Intel's bullet ends "improvements to docs, samples, and tooling", and that
ordering is a useful discipline: a finding that produces only a documentation
edit is often a finding about the tooling.

| Finding | Weak response | Better |
|---|---|---|
| A page is unreachable | Link to it | Ask why the navigation omitted it |
| A term is searched and absent | Write the page | Also fix the vocabulary that hid it |
| The quickstart is abandoned | Rewrite the prose | Cut the steps before first success |
| The same support question recurs | Add an FAQ entry | Change the thing people get wrong |
| Nobody runs the samples | Promote them | Check whether they still work |

## How to talk about it

**Lead with the split, because it is the useful idea.** "Documentation
analytics is two jobs. Corpus-side measures the artifact and needs no audience:
reachability, click depth, findability, staleness, which claims have no
evidence. Reader-side measures behaviour and needs traffic, a pipeline and
usually a privacy review. Teams who want the second and cannot have it conclude
they can measure nothing, and they are wrong by a wide margin."

**The follow-up is what corpus-side analytics actually caught.** On a corpus
with no readers: every page reachable, nine in ten exactly two clicks from the
front door, nothing missing from the search index, 27 of 106 pages carrying a
sentence over 45 words, and 56 concepts whose claims have no
demonstration anywhere. Each of those points at a page, which is the property
reader-side numbers mostly lack.

**The thing to volunteer, and the best point here.** The most important failure
this project has had was invisible to reader-side analytics. The first real
reader followed a README, ran the commands in a terminal, and could not tell
what the library did. Page views for that session: zero, because he never
opened the site. Developer documentation is read in READMEs, in terminals, in
IDE hovers and increasingly through assistants, and the site is the only one of
those that is instrumented. A dashboard of healthy numbers describes the
readers who got far enough to be counted.

**The tradeoff.** Corpus-side analytics can be confidently wrong, and mine was:
the first reachability run said 134 pages reachable out of 121, because the
traversal counted link targets while the denominator counted pages. An
impossible ratio is a lucky way to discover that, since most measurement bugs
produce a plausible number instead. Every figure here gets a fixture with a
known answer before it is quoted anywhere.

## How to prove it

**The artifact.** A script in your own repository reporting reachability, click
depth and orphans, run in CI so the numbers show up in a diff.

**Three things to do, in order:**

1. Compute reachability and click depth for a corpus you own, predicting the
   number of unreachable pages first. If the ratio comes out impossible, you
   have found your measurement bug early and cheaply.
2. List the surfaces your documentation is read on and mark which are
   instrumented. The honest answer is usually one of five or six.
3. Take your most confident claim about your documentation and work out which
   half of analytics could test it. If it is neither, it is an assertion.

**What makes it credible rather than decorative.** The corpus-side
measurements above run against this guide's own pages and its built search
index, and the 134-of-121 bug is recorded rather than tidied away. That page
count is deliberately not quoted here: it changes whenever a learning path is
added, and a figure that moves for reasons unrelated to the claim is a figure
that will be wrong before anyone notices. What does
not exist is any reader-side analytics at all: no site has been published, so
there are no views, no queries and no funnel, and every reader-side figure in
the tables is drawn from general practice rather than from this project. The
[demonstrated](../demonstrated.md) page records the category on that basis.

## Related

- [Time to first success](time-to-first-success.md), the most useful reader-side metric
- [Search and query log analysis](search-log-analysis.md), the highest-value query data
- [Support deflection](support-deflection.md), the business-facing claim
- [Turning developer feedback into changes](developer-feedback-loops.md), what the human channel catches instead
- [Findability and search](findability.md), the corpus-side half of search
- [Documentation CI](documentation-ci.md), where these measurements run
