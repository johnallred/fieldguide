---
title: SEO for documentation
summary: Making a page findable by someone searching the problem rather than the product.
diataxis: explanation
audience: developer
concept: seo-for-docs
tags: [ai, supporting]
---

# SEO for documentation

`supporting` · difficulty 2 · 3h

> Optimize documentation for search (SEO and GEO) and for AI assistants and coding agents through agentready, LLMdigestible content

> Source: intel posting, verbatim

**Prerequisites:** [Metadata for navigation and retrieval](metadata.md)

**Leads to:** [Crawlability and the agent-ready front door](crawlability.md), [Generative engine optimization](geo.md)

## What it is

Making a documentation page findable by someone who searches the problem rather
than the product. Most developers do not navigate to your docs; they search an
error message, a symptom, or a task, and land deep inside.

Documentation SEO is a narrow and unglamorous subset of SEO. There is no link
building and no content marketing. It is mostly titles, descriptions, headings
and URLs, done consistently, derived from a [content model](content-model.md)
rather than hand-tuned per page.

## Why the job asks for it

Intel names it in a responsibility and again in minimum qualifications:
"Experience optimizing technical content for search (SEO and GEO) and for AI
assistants." That is unusual for an engineering-adjacent role and it tells you
something about how Intel sees the job: the front door is a search result page
they do not own.

On a Tuesday it is a specific recurring decision. An engineer titles a page
"Configuration Options Reference". Nobody searches that. The developer who needs
it is searching "widget server out of memory" or "how to set batch size", and
your page ranks for neither because it contains the word "configuration" where
the reader used the word "memory".

The reason this is `supporting` rather than `core`: once the content model
requires a real `title` and `summary`, most of the mechanical work is a build
step, and the rest is a writing habit covered by
[technical writing](technical-writing.md). But the habit is worth a page because
the default failure is systematic. Documentation gets titled from the
*structure of the product* and searched from the *state of the reader*, and
nothing in a normal review catches the mismatch.

## The golden path

Generate the search-visible surface from the content model, then find the pages
whose vocabulary does not match their readers'. Thirty minutes.

**Step 1: a corpus with the usual problem**

```bash
mkdir -p seo-drill/docs && cd seo-drill
cat > docs/configuration-reference.md <<'EOF'
---
title: Configuration Options Reference
summary: Reference for configuration options.
kind: reference
updated: 2026-10-26
---
# Configuration Options Reference

| Flag | Default |
|---|---|
| `max_memory_gb` | 16 |
| `batch_size` | 32 |

Setting `max_memory_gb` too low causes the server to exit during load rather
than at startup.
EOF

cat > docs/getting-started.md <<'EOF'
---
title: Getting Started
summary: Get started with the widget platform.
kind: tutorial
updated: 2026-10-26
---
# Getting Started

Install the CLI with `pip install widget`, then run your first inference.
EOF

cat > docs/troubleshooting-oom.md <<'EOF'
---
title: Fix an out-of-memory error under load
summary: Diagnose and fix a widget server that runs out of GPU memory under load but starts fine.
kind: how-to
updated: 2026-10-26
---
# Fix an out-of-memory error under load

If the server starts cleanly and dies under traffic, it is sized for startup
memory rather than peak.
EOF
ls docs/
```

**Step 2: generate the search surface, do not hand-write it**

```bash
cat > seo.py <<'PY'
"""Generate the search-visible surface from the content model.

Every field here is derived from front matter the content model already
requires. The reason to generate rather than hand-write: a per-page SEO
description written once at publication describes a page that no longer
exists, and nothing in the site contradicts it.
"""
import datetime as dt
from pathlib import Path

import yaml

BASE = "https://widget.example/docs"
SITE = "Widget platform"


def pages(docs: Path):
    for path in sorted(docs.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        front, _, body = text.partition("---\n")[2].partition("\n---\n")
        yield path, yaml.safe_load(front), body


def head_tags(path: Path, meta) -> str:
    url = f"{BASE}/{path.stem}/"
    # The title tag is NOT the page title: it carries the site name for
    # recognition in a result list, and search engines truncate around 60
    # characters, so the distinctive part goes first.
    title_tag = f"{meta['title']} | {SITE}"
    return "\n".join([
        f"<title>{title_tag}</title>",
        f'<meta name="description" content="{meta["summary"]}">',
        f'<link rel="canonical" href="{url}">',
        f'<meta property="og:title" content="{meta["title"]}">',
        f'<meta property="og:description" content="{meta["summary"]}">',
        f'<meta property="og:url" content="{url}">',
    ])


def audit(path: Path, meta, body: str):
    """Report the mechanical problems, which are the ones worth automating."""
    problems = []
    title = meta["title"]
    summary = meta["summary"]

    if len(f"{title} | {SITE}") > 60:
        problems.append(f"title tag is {len(title) + len(SITE) + 3} chars, over 60")
    if len(summary) < 50:
        problems.append(f"description is {len(summary)} chars, under 50")
    if len(summary) > 160:
        problems.append(f"description is {len(summary)} chars, over 160")

    # The highest-value check: does the summary repeat the title and add
    # nothing? That is a description with no search surface of its own.
    title_words = {w.lower() for w in title.split() if len(w) > 3}
    summary_words = {w.lower() for w in summary.split() if len(w) > 3}
    new = summary_words - title_words
    if len(new) < 3:
        problems.append(
            f"description adds only {len(new)} new word(s) beyond the title"
        )

    if not body.strip().startswith("#"):
        problems.append("no H1")
    return problems


for path, meta, body in pages(Path("docs")):
    print(f"=== {path.name} ===")
    print(head_tags(path, meta))
    problems = audit(path, meta, body)
    if problems:
        for problem in problems:
            print(f"  SEO  {problem}")
    else:
        print("  SEO  ok")
    print()
PY
python3 seo.py
```

**Step 3: the check that actually finds the real problem**

The mechanical checks above catch lengths. The real failure is vocabulary, and
it needs the reader's words as input.

```bash
cat > vocabulary.py <<'PY'
"""Find pages whose searchable text lacks the words readers actually use.

The queries are the input that makes this work, and they are not invented:
they come from search logs, support tickets and the zero-click queries nobody
exports. See docs-prioritization.
"""
from pathlib import Path

import yaml

# Real reader phrasings, with the page that should win each one.
QUERIES = [
    ("widget server out of memory", "troubleshooting-oom.md"),
    ("how to set batch size", "configuration-reference.md"),
    ("max_memory_gb default", "configuration-reference.md"),
    ("install widget cli", "getting-started.md"),
]


def surface(path: Path):
    """The text a search engine weights most: title, description, H1, headings."""
    text = path.read_text(encoding="utf-8")
    front, _, body = text.partition("---\n")[2].partition("\n---\n")
    meta = yaml.safe_load(front)
    headings = [l.lstrip("# ").strip() for l in body.splitlines() if l.startswith("#")]
    return f"{meta['title']} {meta['summary']} {' '.join(headings)}".lower()


surfaces = {p.name: surface(p) for p in sorted(Path("docs").glob("*.md"))}

for query, expected in QUERIES:
    terms = [t for t in query.lower().split() if len(t) > 2]
    scores = {
        name: sum(1 for t in terms if t in text) for name, text in surfaces.items()
    }
    best = max(scores, key=scores.get)
    hit = scores[best] > 0 and best == expected
    missing = [t for t in terms if t not in surfaces[expected]]
    print(f"  {'OK ' if hit else '   '} {query:<32} -> {best} ({scores[best]}/{len(terms)})")
    if missing:
        print(f"         {expected} is missing: {missing}")
PY
python3 vocabulary.py
```

**Step 4: fix one page and re-measure**

```bash
cat > docs/configuration-reference.md <<'EOF'
---
title: Server configuration flags
summary: Every server flag with its default, including batch_size and max_memory_gb, and what happens when each is set too low.
kind: reference
updated: 2026-10-26
---
# Server configuration flags

## batch_size

| Flag | Default |
|---|---|
| `batch_size` | 32 |

## max_memory_gb

| Flag | Default |
|---|---|
| `max_memory_gb` | 16 |

Setting `max_memory_gb` too low causes the server to exit during load rather
than at startup.
EOF
python3 vocabulary.py
```

**What you built.** A generated search surface, a length audit, and a
vocabulary check driven by real reader phrasings.

Step 4 is the point, and the numbers are unambiguous:

| | Before | After |
|---|---|---|
| Queries routed to the right page | 2 of 4 | **4 of 4** |
| `how to set batch size` | 0 of 4 terms matched | 3 of 4 |
| `max_memory_gb default` | 0 of 2 | 2 of 2 |
| Length audit on that page | 2 problems | ok |

The page did not get better documentation. **It got the reader's words into the
places a search engine weights**, by naming the flags in H2 headings and in the
summary rather than only inside a table cell.

Two honest residuals. `install widget cli` still wins on 1 of 3 terms, because
`getting-started.md` never says "install" or "CLI" in its title, summary or
headings: it wins by default rather than by merit, and a competing page would
take it. And `how` is missing from the fixed page, which is correct, since
reference pages should not be titled as questions. The check reports it; you
decide it does not matter. That is the right division of labour between a linter
and a person.

## Reference

### The fields that matter, and where they come from

| Element | Length | Source | Notes |
|---|---|---|---|
| `<title>` | under ~60 chars | `title` + site name | Distinctive part first; it gets truncated |
| `<meta name="description">` | 50 to 160 chars | `summary` | Not a ranking factor; decides the click |
| `<link rel="canonical">` | n/a | page URL | Essential with versioned docs |
| H1 | one per page | the page title | Must match the title's intent |
| H2/H3 | n/a | the page's own structure | Where task phrasing belongs |
| URL slug | short | filename | Stable; a renamed URL loses its ranking |
| `og:` tags | n/a | `title` and `summary` | Link previews in Slack and chat |

Deriving all of these from two required fields is the whole trick. It means
nobody writes a separate SEO description, which is the artifact that always goes
stale.

### Where to put the reader's vocabulary

In order of weight:

1. **Title.** "Fix an out-of-memory error under load" beats "Memory configuration".
2. **H2 headings.** One per task or symptom. This is where "out of memory under load" lives.
3. **Description.** The sentence that decides the click, in the reader's words.
4. **First paragraph.** Answer the question; do not introduce the topic.
5. **The exact identifiers.** `max_memory_gb` must appear as text, not only in a table cell nobody indexes well.

### Documentation-specific concerns

| Concern | Why it is different here |
|---|---|
| Versioned docs | Multiple URLs per page; canonical must point at the current version or you split your own ranking |
| Deep landing | Most arrivals are on an interior page, so every page needs orientation and a route onward |
| Error messages | Developers search the literal string. A page containing the exact message outranks a general one |
| Generated reference | Thousands of near-identical pages; thin-content risk, and canonicalisation matters |
| Retired versions | [Retired pages](content-retirement.md) that stay indexed outrank current ones |

The error-message row is the cheapest high-value action in documentation SEO and
almost nobody does it: put the literal text of common errors in the page that
fixes them.

### What does not apply

| Not relevant | Why |
|---|---|
| Keyword density | Write for the reader; the vocabulary check above is sufficient |
| Link building | Your docs rank on relevance and site authority you already have |
| Content refresh for its own sake | A `updated` date you bumped without changing anything is dishonest |
| Long-form padding | A reference page should be exactly as long as the interface |

## How to talk about it

**What a competent answer sounds like.** Lead with the vocabulary mismatch,
because it is the documentation-specific insight. "Documentation gets titled
from the structure of the product and searched from the state of the reader.
A page called 'Configuration Options Reference' does not rank for 'server out
of memory', and no review catches that because the page is correct. So I derive
the title tag, description, canonical and Open Graph tags from the content
model's required fields, and then run a separate check that takes real search
queries and reports which pages lack the reader's words in their title,
headings and summary."

**The follow-up is "how do you get the real queries",** and the honest answer is
that most teams have them and nobody exports them. Site search logs, support
ticket subject lines, and the zero-click queries from Search Console are all
cheap and all underused. A list of fifty real phrasings is worth more than any
amount of SEO advice, and gathering it is an afternoon.

**The tradeoff to volunteer.** Optimising for search vocabulary pulls titles
toward symptoms and away from structure, and a corpus titled entirely by symptom
is hard to navigate for someone browsing rather than searching. "Fix an
out-of-memory error under load" is a better search result and a worse table-of-
contents entry than "Memory". The resolution is usually that reference pages stay
structural and how-to pages go symptomatic, which is
[Diátaxis](diataxis.md) deciding an SEO question, but it is a real tension rather
than a free win.

**One sharper point.** The strongest observation is that **documentation SEO and
[retrieval](rag.md) want the same thing for the same reason.** Both are
vocabulary-matching problems between a reader's phrasing and an author's. A
summary written in the reader's words improves the search snippet, the retrieval
snippet, the [llms.txt](llms-txt.md) annotation and the embedding, all at once,
from one edit. That is why the content model's `summary` field is load-bearing
far out of proportion to its size, and why "optimise for SEO and GEO" in Intel's
posting is one task rather than two.

## How to prove it

**The artifact.** A generated head-tag build step, plus the vocabulary check run
against real queries, plus one before-and-after page.

**Three things to do, in order:**

1. **Export fifty real queries** from any documentation site you can access,
   especially the ones with no click. Ten minutes, and it is the input
   everything else needs.
2. **Run the vocabulary check** and list the pages whose surface lacks their own
   readers' words. That list is a prioritised backlog nobody else has.
3. **Generate the head tags from front matter** and add a CI check that the
   descriptions are not all identical. The commonest real-world failure is a
   site serving one site-wide description on every page, which looks fine and
   destroys every snippet.

**What makes it credible rather than decorative.** Describing title tags proves nothing. A vocabulary
check driven by exported queries, a list of mismatched pages, and a measured
before-and-after on one of them demonstrates that you treated findability as
measurable.

## Related

- [Generative engine optimization](geo.md), the same problem for assistants
- [Crawlability and the agent-ready front door](crawlability.md), being reachable at all
- [Structured data and JSON-LD](structured-data.md), the machine-readable layer
- [Metadata for navigation and retrieval](metadata.md), where the fields come from
