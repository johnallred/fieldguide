---
title: Findability and search design
summary: "Auditing what your search index actually contains, which is usually less than you think."
diataxis: how-to
audience: developer
concept: findability
tags: [ia, supporting]
---

# Findability and search design

`supporting` · difficulty 2 · 3h

!!! quote "Asked for by name"
    Intel: "The role makes documentation discoverable and usable by both developers and AI assistants through search optimization and agentready content"

**Prerequisites:** [Metadata for navigation and retrieval](metadata.md)

## What it is

Whether a reader who knows what they want can get to it. On a documentation
site that means three overlapping mechanisms: navigation, on-site search, and
external search engines. This page is about the middle one, which is the one
nobody audits.

The useful move is to stop treating search as a feature your generator
provides and start treating the search index as an artifact you are
responsible for. It is a file. You can open it.

## Why the job asks for it

Intel pairs discoverability for developers with discoverability for AI
assistants in one sentence, which is the right pairing: both are retrieval
over the same corpus, and both fail for the same reasons.

The reason this is engineering rather than a content concern is that the
failure is invisible from the outside. A search box that returns results looks
like it works. Whether it returns the *right* results depends on what went
into the index, and what went into the index is a function of your
[metadata](metadata.md), your [chunking](chunking.md) granularity, and
defaults you probably never looked at.

## The golden path

Open your own search index, find out what is missing from it, and fix the
cause. About thirty-five minutes. The measurement in step 3 was wrong the
first time, which is part of the lesson.

**Step 1: open the index**

```python
import json
from pathlib import Path

data = json.loads(Path("site/search/search_index.json").read_text())
docs = data["docs"]
print(f"{len(docs)} entries, {Path('site/search/search_index.json').stat().st_size/1024:.0f} KB")
print(f"keys: {sorted(docs[0].keys())}")
```

```
1201 entries, 1177 KB
keys: ['location', 'text', 'title']
```

Two facts immediately. The index is **1.1 megabytes**, downloaded by every
visitor who uses search. And each entry has three fields, which tells you what
can be matched.

**Step 2: find the granularity**

```python
by_page = collections.Counter(d["location"].split("#")[0] for d in docs)
print(f"pages: {len(by_page)}  entries per page: "
      f"min={min(by_page.values())} max={max(by_page.values())} "
      f"mean={sum(by_page.values())/len(by_page):.1f}")
```

```
pages: 121  entries per page: min=3 max=19 mean=9.9
```

Section-level, not page-level: roughly ten entries per page, one per heading.
That is good news, and it means your heading structure *is* your search
granularity. Headings that are vague or inconsistent degrade search directly,
which is a concrete reason the [accessibility](accessibility.md) heading
structure work pays twice.

**Step 3: check whether your metadata is in there**

This is the audit worth running, and my first attempt at it was broken. I
tested whether three stopword-stripped words from each summary appeared
contiguously in the index text, which they essentially never would, so it
reported 83 failures that were an artifact of the test.

The correct test is simpler: normalise both sides and look for the whole
summary.

```python
def norm(s):
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", s)).strip().lower()

if norm(summary) in norm(" ".join(index_text_for_page)):
    found += 1
```

```
pages with a real summary: 73
summary present in the search index: 1
absent: 72
```

**Seventy-two of 73.** Every page in this guide carries a one-line `summary`
in its front matter, and on all but one of them that sentence was not
searchable, because front matter is not page content and the search plugin
never saw it.

The summary is the single most retrieval-useful sentence on a page. It was
written 121 times and indexed once.

**Step 4: find out who else was not reading it**

```bash
grep -rn "summary" src/fieldguide/*.py hooks/*.py mkdocs.yml
```

Nothing consumed it. Not the search index, not the page body, and not the meta
description, because Material falls back to `site_description` unless a page
sets `description` explicitly. So the field had **zero readers** while two
generators wrote it.

**Step 5: one field, three readers**

The fix is a hook that puts the summary into the Markdown, early enough for
the search plugin to index it:

```python
def on_page_markdown(markdown, page, config, files):
    summary = page.meta.get("summary")
    if not summary or page.meta.get("diataxis") == "placeholder":
        return markdown
    match = TITLE.search(markdown)
    lead = f"\n*{summary.strip()}*\n"
    return markdown[:match.end()] + lead + markdown[match.end():]


def on_page_context(context, page, config, nav):
    summary = page.meta.get("summary")
    if summary and not page.meta.get("description"):
        page.meta["description"] = summary
    return context
```

```
summary present in the search index: 73 / 73
distinct meta descriptions:         121 / 121 pages
```

And the reader now sees it as a standfirst under the title. One field, three
consumers, where it previously had none.

**Step 6: assert it in CI, because the unit tests cannot**

A hook's tests pass whether or not it is wired into `mkdocs.yml`. So the gate
has to read the built output:

```python
assert len(descriptions) > pages * 0.9, (
    f"only {len(descriptions)} distinct descriptions across {pages} pages; "
    f"the summary hook is not wired in")
```

Verified in both directions: with the hook, 121 distinct descriptions across
121 pages. With the `hooks:` key removed, 1 across 121, and the assertion
fails.

**What you built.** An audited index, a field with three readers instead of
zero, and a gate that fails if the wiring is removed.

## Reference

### What to audit in a search index

| Question | How |
|---|---|
| How big is it? | File size; it is downloaded by every searching visitor |
| What granularity? | Entries per page |
| Which fields are matchable? | The keys on an entry |
| Is page metadata in it? | The step 3 comparison |
| Are code samples in it? | Search for an identifier only present in a fence |
| Are generated pages in it? | They may dominate results while saying nothing |

The last row is worth checking on any corpus with stubs or auto-generated
indexes. Forty placeholder pages in a 121-page index is a third of the results
competing with real content.

### The three findability mechanisms

| Mechanism | Serves | Fails when |
|---|---|---|
| Navigation | Browsers who do not know the vocabulary | Deep or inconsistent hierarchies |
| On-site search | Readers who know roughly what they want | The index lacks the text they will type |
| External search | Readers who start on a search engine | See [SEO for docs](seo-for-docs.md) and [GEO](geo.md) |
| Assistant retrieval | Readers who ask a question | See [RAG](rag.md) and [chunking](chunking.md) |

Intel's sentence covers the second and fourth. They share an index-quality
problem and differ in what they do with the results.

### What makes a page findable on-site

| Factor | Why |
|---|---|
| Headings that name what a reader would type | Headings are the index's unit |
| A summary in the body | What a reader would type is often the summary, not the prose |
| Real terms rather than internal names | Your search cannot match a word nobody uses |
| Synonyms somewhere on the page | Lexical search has no concept of similarity |
| Code identifiers present as text | So searching a flag name finds the page |

The synonym row is the one lexical search makes unavoidable. A page about
`access token` does not match a search for "API key" unless the string "API
key" appears on it, which is a reason to name deprecated terms once on the page
rather than purging them.

### Index size

| Corpus | Index | Consequence |
|---|---|---|
| ~120 pages, section-level | ~1.1 MB | Noticeable on a slow connection |
| ~1,000 pages | ~10 MB | Prohibitive; use a hosted search |

Material supports prebuilding and compressing the index, and beyond roughly a
thousand pages the answer is a hosted search service rather than a client-side
one. Knowing the crossover exists, and where yours sits, is the point.

## How to talk about it

**Lead with the index as an artifact.** "I treat the search index as something
I am responsible for rather than a feature the generator provides. It is a JSON
file; you can open it and find out what is actually matchable. On this corpus
it was 1.1 MB, section-level at about ten entries per page, and missing the one
field I most wanted searchable."

**The follow-up is what you found**, and the number is the answer: 72 of 73
page summaries were absent from the index, because front matter is not page
content. The fix gave one field three readers, the page body, the search index
and the meta description, and the CI gate reads the built output because a
hook's unit tests pass whether or not it is wired in.

**The tradeoff to volunteer.** Putting the summary in the body means every page
opens with a sentence that partly repeats its title, which is a small cost in
polish for a large gain in findability. And it is a client-side index, so
everything that improves matching also grows a file every searching visitor
downloads. At this corpus size that trade is clearly worth it; at ten times the
size it is not, and the answer becomes hosted search.

**One sharper point.** Your heading structure is your search granularity. The
index here is section-level at roughly ten entries per page, so a vague heading
is a bad search result, and the heading-level work that an accessibility audit
produces improves search at the same time. Those are usually treated as
unrelated chores.

## How to prove it

**The artifact.** An audit of your own index with numbers: size, granularity,
and one concrete thing you found missing and fixed.

**Three things to do, in order:**

1. Open `site/search/search_index.json` and run steps 1 and 2. Most people
   have never looked.
2. Run the step 3 comparison for your most important metadata field. Be
   careful how you test it; my first attempt produced a plausible wrong number.
3. If you fix it with a hook, add the CI assertion from step 6. Otherwise one
   `mkdocs.yml` edit silently reverts the whole thing.

**What makes it credible rather than decorative.** `docpack` exposes its corpus
through an MCP server with a BM25 index, recorded as a partial demonstration of
this concept, and its retrieval evaluation caught `summary` being unindexed
there too. The same defect existed in this guide, which is the part worth telling. I
wrote the page about metadata having no readers while shipping a field with no
readers, and found it by auditing the index. Every page now carries its own
description, with a gate proving it.

## Related

- [Metadata for navigation and retrieval](metadata.md), the fields this indexes
- [Chunking](chunking.md), the same granularity question for assistants
- [SEO for documentation](seo-for-docs.md), the external-search half
- [Search log analysis](search-log-analysis.md), finding out what readers actually type
