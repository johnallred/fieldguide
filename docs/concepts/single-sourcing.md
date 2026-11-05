---
title: Single-sourcing and content reuse
summary: "Writing a fact once, and the new silent failure that reuse introduces."
diataxis: explanation
audience: developer
concept: single-sourcing
tags: [ia, supporting]
---

# Single-sourcing and content reuse

`supporting` · difficulty 2 · 3h

!!! note "Not a quotation (adjacent)"
    Neither posting mentions single-sourcing. It is the mechanism behind every
    claim about documentation scaling, so it is here as the thing those claims
    depend on.

**Prerequisites:** [Content models](content-model.md)

## What it is

Writing a fact in one place and referencing it everywhere else, rather than
copying it. Three mechanisms, in increasing order of power: **includes**, which
pull a block of text into several pages; **variables**, which substitute a
value such as a version number; and **generation**, which renders many pages
from one template and one data source.

The reason it is worth a page of its own is that reuse introduces a failure
mode that copied prose does not have. A duplicated paragraph goes stale. A
broken include can make a page disappear, and the build may not mention it.

## Why the job asks for it

It does not, by name. It is here because both postings make claims that depend
on it. "A small team of educators operating with the reach of an organisation ten
times larger", in Anthropic's phrasing. Or NVIDIA's "turn documentation,
standards and tribal knowledge into tooling, templates and self-service
paths". Both are statements about leverage, and leverage in a documentation
corpus means not writing the same thing N times.

It also decides how expensive your [localization](localization.md) is, since
every duplicated paragraph is translated once per copy, and how coherent your
corpus looks, since N copies of a fact diverge in N directions.

## The golden path

Measure duplication, set up includes, then find the silent failure. About
thirty minutes.

**Step 1: measure what is actually duplicated**

Before adopting a mechanism, find out whether you have the problem. Normalise
prose sentences outside code fences and count the ones that appear on more than
one page:

```python
norm = lambda s: re.sub(r"\s+", " ", s.strip().lower())
seen = collections.defaultdict(list)
for p in sorted(Path("docs").rglob("*.md")):
    # ... skip fenced lines, tables and headings ...
    for s in re.split(r"(?<=[.!?])\s+", prose):
        if len(norm(s).split()) >= 8:
            seen[norm(s)].append(p.name)

dupes = {k: v for k, v in seen.items() if len(set(v)) > 1}
```

```
prose sentences (8+ words): 3654
appearing on more than one page: 27

   40 pages: this concept is on the curriculum and the prose is not written yet
   40 pages: everything below comes from the registry, so it is accurate as far
   40 pages: the [page contract](../explanation/the-page-contract.md) applies t
    5 pages: neither posting names it; both describe the problem it solves.
    4 pages: you will be asked to do it; it is not the centre of the role.
```

Read that carefully, because the top three are not a problem. They appear on 40
pages each because they come from **one generator template**, which is
single-sourcing working correctly: one definition, forty renders, and changing
the sentence changes all forty.

The 5-page and 4-page entries are the real duplication: hand-written sentences
copied between pages. Twenty-seven duplicated sentences out of 3,654 is a low
rate, which is itself the answer for this corpus. Measure before you build.

**Step 2: set up includes**

```bash
mkdir -p ss-demo/docs ss-demo/snippets && cd ss-demo
cat > mkdocs.yml <<'EOF'
site_name: SS
markdown_extensions:
  - pymdownx.snippets:
      base_path: ["snippets"]
      check_paths: true
EOF
printf 'You need Python 3.10 or later and an access token.\n' > snippets/prereqs.md
```

```bash
cat > docs/a.md <<'EOF'
# Install

--8<-- "prereqs.md"

Then run the installer.
EOF
```

```bash
python3 -m mkdocs build -q
grep -c 'Python 3.10' site/a/index.html site/b/index.html
```

```
site/a/index.html:1
site/b/index.html:1
```

One source, two pages. The prerequisite now changes in one place.

**Step 3: break the include, with the check on**

```bash
printf '# Configure\n\n--8<-- "nonexistent.md"\n' > docs/c.md
python3 -m mkdocs build -q; echo "exit=$?"
```

```
ERROR - Error reading page 'c.md': Snippet at path 'nonexistent.md' could not be found
exit=1
```

Good. A missing include fails the build.

**Step 4: break it again, with the default configuration**

Remove `check_paths: true`, which is **not** the default:

```bash
python3 -m mkdocs build -q; echo "exit=$?"
```

```
exit=0
```

Exit zero. And the page that ships:

```
   page text: ''
```

**Empty.** The missing include was silently dropped, so `docs/c.md` published
with nothing in its body, and the build said nothing at all.

That is the failure mode reuse introduces. A copied paragraph can go stale; a
broken include can delete a page's content, and by default nobody is told.
`check_paths: true` is not an optimisation, it is the thing that makes the
mechanism safe.

**What you learned.** Measure duplication before adopting a mechanism, and
when you adopt one, turn on its integrity check in the same commit.

## Reference

### The three mechanisms

| Mechanism | Reuses | Good for | Cost |
|---|---|---|---|
| Includes | A block of text | Prerequisites, warnings, shared procedures | A page's content can vanish; see step 4 |
| Variables | A value | Version numbers, product names, URLs | Substitution is invisible in source |
| Generation | A whole page | Indexes, API reference, matrices | The generator becomes software you own |

Generation is the most powerful and the most underused. This guide's coverage
matrix, study plan, learning paths and 40-odd placeholders are all generated
from one registry, which is why `fieldguide build --check` can fail when a
committed view is stale.

### When reuse is wrong

| Situation | Why copying is better |
|---|---|
| The two pages will diverge | An include forces them to stay identical |
| The shared text is one sentence | The indirection costs more than the duplication |
| The copies have different audiences | Same facts, different framing, is not duplication |
| It is an example | Examples should suit their context |

The first row is the one that bites. An include is a commitment that these
passages are the same thing forever, and when one page needs a variation you
get a parameterised include, then a conditional, and eventually a templating
language inside your documentation.

### What reuse does to the rest of the pipeline

| Concern | Effect |
|---|---|
| [Chunking](chunking.md) | A source consumer sees the include directive, not the text |
| [Localization](localization.md) | Reuse cuts translation cost proportionally; it is the biggest single lever |
| [Link checking](link-checking.md) | Links inside an include resolve relative to the including page |
| Review | A reviewer sees a one-line diff whose effect is on 40 pages |
| [Freshness](freshness-monitoring.md) | An included block's age is not the page's age |

The chunking row deserves attention in an AI-ready corpus. Anything reading
your Markdown source rather than your built HTML sees `--8<-- "prereqs.md"`
instead of the prerequisite, so retrieval pipelines should be built on the
rendered output when includes are in play.

### Integrity checks that are not optional

| Mechanism | Check | Default |
|---|---|---|
| `pymdownx.snippets` | `check_paths: true` | Off, and silent when off |
| Sphinx `.. include::` | Warns on a missing file | On, fails with `-W` |
| Variables | A check for undefined references | Usually absent; write it |
| Generation | Regenerate in CI and fail if output differs | You implement it |

The last row is the one that makes generation trustworthy. Generating pages is
easy; the hard part is guaranteeing that the committed output matches what the
generator produces today, and that is a `--check` mode plus a CI step.

## How to talk about it

**Lead with measurement.** "I measure duplication before adopting a mechanism.
On this corpus, 27 of 3,654 prose sentences appeared on more than one page, and
the biggest clusters were generated from one template, which is reuse working.
The actual hand-copied duplication was tiny, so includes would have added
indirection for very little."

**The follow-up is about the risk**, and this is the strong answer: reuse
introduces a failure copying does not have. With `pymdownx.snippets` at its
default settings, a missing include is silently dropped and the page ships with
an empty body at exit zero. So the integrity check goes in with the mechanism,
in the same commit.

**The tradeoff to volunteer.** An include is a commitment that two passages are
the same thing permanently, and the pressure is always toward parameterising it
when one page needs a variation. That road ends in a templating language inside
your prose, which is worse than the duplication you started with. Reuse facts
and procedures; do not reuse explanations, which legitimately differ by
audience.

**One sharper point.** Generation is the mechanism people underuse. Includes
reuse a paragraph; generation reuses a page's entire structure, and it is what
makes an index, a coverage matrix or an API reference impossible to leave
stale. It costs you a generator that is real software, and the discipline that
makes it safe is a `--check` mode that fails when committed output has drifted.

## How to prove it

**The artifact.** A corpus with one reuse mechanism, its integrity check
enabled, and a duplication measurement that justified choosing it.

**Three things to do, in order:**

1. Run step 1 on your own corpus. The number will probably surprise you in one
   direction or the other, and either way it tells you what to do.
2. If you already use includes, check whether path validation is on. For
   `pymdownx.snippets` it is off by default, and off means silent.
3. Find the fact in your corpus that is copied the most times and single-source
   that one. Start with a version number or a prerequisite, not an
   explanation.

**What makes it credible rather than decorative.** `docpack` single-sources
page summaries through `hooks/seo.py`, so one front-matter field feeds the
page, the meta description and the retrieval artifacts, which is recorded as a
partial demonstration. This guide's own generation is the stronger example:
four views and 40-odd placeholders from one registry, with
`fieldguide build --check` failing in CI when committed output is stale.

## Related

- [Content models](content-model.md), which is what generation reads
- [Localization and translation pipelines](localization.md), where reuse pays most
- [Chunking](chunking.md), which sees include directives rather than text
- [Content lifecycle and governance](content-lifecycle.md), the process around all of this
