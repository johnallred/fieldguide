---
title: Metadata for navigation and retrieval
summary: "Two audiences read your front matter, they want different fields, and a field with no reader is already wrong."
diataxis: explanation
audience: developer
concept: metadata
tags: [ia, core]
---

# Metadata for navigation and retrieval

`core` · difficulty 2 · 3h

!!! quote "Asked for by name"
    NVIDIA: "content modeling, taxonomy, and metadata for both navigation and machine retrieval"

**Prerequisites:** [Content models](content-model.md)

**Leads to:** [Findability and search design](findability.md), [Agent-ready content](agent-ready-content.md)

## What it is

The structured data attached to each page, usually in front matter. NVIDIA's
phrasing is unusually precise and worth taking literally: metadata **for both
navigation and machine retrieval**. Those are two audiences with different
needs, and a single field set rarely serves both well.

Navigation metadata answers "where does this page belong and what do I call
it in a sidebar". Retrieval metadata answers "which subset of the corpus
should a query search". They overlap and they are not the same, and the
mistake is designing one and assuming it covers the other.

## Why the job asks for it

Because the retrieval half is new and most corpora do not have it.

Navigation metadata is well understood: a title, a position, a section. It has
existed as long as documentation sites have. Retrieval metadata is what makes a
filtered search possible, what lets a chunk carry its context into a vector
store, and what an assistant uses to decide where to look. NVIDIA asking for
both in one phrase is a signal that they know the second is a separate design
problem.

The uncomfortable part, and the subject of the golden path, is that adding
fields is easy and keeping them true is not. A field written by a generator and
read by nothing will be wrong within weeks, and nothing will report it.

## The golden path

Audit a real corpus's metadata, find the field that is lying, and work out why
nobody noticed. About thirty minutes.

**Step 1: measure coverage, not existence**

```
121 pages

field        pages  coverage
title          121      100%
summary        121      100%
diataxis       121      100%
audience       121      100%
concept         64       52%
tags           64       52%
generated      53       43%
```

Coverage is the first question because an optional field cannot be built on. A
filter on `tags` here would silently exclude 48 per cent of the corpus, and the
result would look like a retrieval problem rather than a metadata problem.

**Step 2: check that the populated fields are true**

Full coverage is necessary and not sufficient. Split each field's values by
whether the page was generated:

```
generated pages by diataxis: {'reference': 53}
hand-written by diataxis:    {'how-to': 22, 'explanation': 46}
```

`diataxis` had 100 per cent coverage, three legal values, and was **wrong on 53
pages**. The placeholder generator hardcoded `reference`, so that value meant
"not written yet" while no real page used it.

A filter for reference documentation would have returned exclusively stubs.

**Step 3: count the readers**

```bash
grep -rn "diataxis" src/fieldguide/*.py hooks/*.py mkdocs.yml
```

```
src/fieldguide/generate.py:144:        "diataxis": "reference",
src/fieldguide/scaffold.py:102:        "diataxis: explanation",
```

Two writers, zero readers. That is the explanation for step 2: nothing
consumed the field, so nothing could notice it was wrong.

**The reader count is the diagnostic.** Write it down for every field you have.
A field with more writers than readers is decoration, and decoration rots.

**Step 4: check the field is even parseable**

```python
m = re.match(r"^---\n(.*?)\n---\n", p.read_text(), re.S)
try:
    yaml.safe_load(m.group(1))
except yaml.YAMLError:
    bad.append(p)
```

```
front matter parses: 75 pages
front matter INVALID: 46 pages
```

Forty-six pages whose front matter no YAML parser could read, because a
generated summary contained an unquoted colon. MkDocs' own metadata parser is
more forgiving than YAML, so the build was green and the pages looked fine.

The visible symptom was in the wrong place entirely:

```
meta description: A validated curriculum for documentation engineering, ...
```

Every one of those 46 pages fell back to the site description, because its own
`summary` was unreadable. A navigation-and-SEO symptom caused by a
serialisation bug, which is why this check belongs next to the metadata work
rather than in the SEO work.

**Step 5: fix all three classes**

| Problem | Fix |
|---|---|
| Unparseable front matter | Serialise with `yaml.safe_dump`, never f-strings |
| A field that lies | Add the honest value: `diataxis: placeholder` |
| A field with no reader | Give it one, so drift fails a build |

```
ok: every page's front matter parses as YAML
all pages by diataxis: {'how-to': 22, 'explanation': 46, 'placeholder': 53}
  FIRES: diataxis is 'refrence', which is not one of [...]
```

**What you learned.** Metadata health has three questions and most audits ask
only the first: is it present, is it true, and does anything read it.

## Reference

### The two audiences, and what each wants

| Field | Navigation | Retrieval |
|---|---|---|
| `title` | Essential, it is the label | Useful, it is high-signal text |
| `summary` | Sidebar hints, meta description | Essential, it is what a map lists |
| `diataxis` or page type | Section grouping | Essential filter: "how-to only" |
| `audience` | Sometimes a separate route | Essential filter |
| `position` or `order` | Essential | Useless |
| `product_version` | A version switcher | Essential filter |
| `component` or area | Grouping | Essential filter |
| `updated` or `reviewed` | A date in the footer, with caveats | Staleness filter |
| `tags` | Weak; a tag index few people use | Weak unless closed and required |
| `canonical` | Not used | Deduplication across versions |

The asymmetry in the `position` row is the clearest illustration of the two
audiences. Navigation needs ordering and retrieval does not care. Retrieval
needs filters and navigation can live without most of them.

### What a chunk needs that a page does not

When a page is [chunked](chunking.md) for retrieval, each chunk leaves home
without its context. The metadata a chunk has to carry:

| Field | Why the chunk needs it |
|---|---|
| Source page and anchor | So an answer can cite a link a reader can follow |
| Page title | A chunk from the middle of a page has no title of its own |
| Heading trail | Which section this is, so the chunk is placeable |
| Page type and audience | So a filtered query still works at chunk level |
| Version | So a 2.3 chunk is not returned to a 2.4 reader |

Page-level metadata that is not copied onto chunks is metadata that stops
existing the moment retrieval starts, which is the most common reason filtered
search works in a prototype and not in production.

### How many fields

| Count | Outcome |
|---|---|
| Three or four, required, all consumed | Reliable, and the common good answer |
| Eight or more, half optional | Half-populated, nothing depends on it |
| Any number with no consumers | Decorative, and already wrong |

Start from the filter you want and add the field that makes it possible. Fields
added because they seem like good practice are the ones that end up lying.

### Where metadata lives

| Location | Good for | Watch out |
|---|---|---|
| Front matter | Per-page facts authors control | Must be valid YAML; see step 4 |
| A registry or data file | Relationships, ordering, cross-page rules | Must not disagree with the pages |
| Derived at build time | Word count, last modified, heading trail | Cheap, and invisible to source consumers |
| The file path | Section, product area | Encoded in a URL, so expensive to change |

Deriving is underrated. A heading trail, a word count or a reading time
computed at build time cannot drift, because nothing stores it.

## How to talk about it

**Take NVIDIA's phrasing literally.** "Navigation metadata and retrieval
metadata are different field sets. Navigation needs ordering and a label;
retrieval needs filters, and it needs them copied onto every chunk, because a
chunk leaves the page without its context. A corpus with good navigation
metadata and no retrieval metadata looks fine until you put a search in front
of it."

**The follow-up is how you keep it honest**, and the answer is reader count. A
field with more writers than readers will be wrong and nothing will report it.
I had a fully populated, closed-vocabulary field that was wrong on 44 per cent
of pages for exactly that reason.

**The tradeoff to volunteer.** Every required field is a tax on contribution
and a thing reviewers have to check, so the right number is small. The pressure
runs the other way, because each new filter suggests a new field, and the way
to resist it is to require a named consumer before adding one.

**One sharper point.** Check that your front matter is valid YAML. MkDocs'
metadata parser is more forgiving than YAML, so an unquoted colon builds
cleanly and is invisible to every tool using a real parser. I shipped 46 such
pages, and the only visible symptom was their meta descriptions falling back to
the site default. Four lines of check, and it is the cheapest
[AI-readiness](agent-ready-content.md) work available.

## How to prove it

**The artifact.** A metadata audit of a corpus you own: coverage per field,
value distribution per field, and reader count per field.

**Three things to do, in order:**

1. Print coverage and value distribution for every field in your corpus. Heavy
   skew toward one value usually means a default is being written somewhere.
2. Count readers for each field. Anything with none is either removable or
   needs a consumer.
3. Parse all your front matter with a real YAML parser. This takes four lines
   and finds something more often than it should.

**What makes it credible rather than decorative.** `docpack` carries metadata
through into its retrieval artifacts, so each chunk keeps its source, heading
trail and page type, and `summary` is indexed for search after an evaluation
showed it was being ignored. The more useful story is the audit above: a field
at 100 per cent coverage, legal values, zero readers, wrong on 44 per cent of
pages, and the serialisation bug underneath it.

## Related

- [Taxonomy and controlled vocabularies](taxonomy.md), which constrains the values
- [Content models](content-model.md), which declares the fields
- [Chunking](chunking.md), where retrieval metadata has to be carried
- [Findability and search design](findability.md), what the filters are for
