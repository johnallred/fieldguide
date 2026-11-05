---
title: Information architecture
summary: Deciding what the units of your content are, what they are called, and how someone finds the one they need.
diataxis: explanation
audience: developer
concept: information-architecture
tags: [ia, core]
---

# Information architecture

`core` · difficulty 2 · 4h

> Information architecture skills: content modeling, taxonomy, and metadata for both navigation and machine retrieval

> Source: nvidia posting, verbatim

**Leads to:** [Content models](content-model.md), [Diátaxis](diataxis.md), [Knowledge architecture](knowledge-architecture.md), [Metadata for navigation and retrieval](metadata.md)

## What it is

Deciding what the units of your content are, what each unit is called, and how
someone looking for one of them finds it. It is the structural layer underneath
writing: not what a page says, but what the set of pages *is*.

Three decisions make up almost all of it. **What is a page?** **What is a page
about, formally, in a way a machine can read?** **How does a reader get from
not knowing to the right page?**

## Why the job asks for it

NVIDIA names it directly and then does something unusual: it specifies the
purpose twice, "for both navigation and machine retrieval". That second half is
the whole reason this concept is `core` rather than historical.

For thirty years information architecture meant navigation design: menus,
breadcrumbs, sitemaps, card sorting, where things go so humans can click to
them. That work still exists. But a documentation corpus in 2026 has a second
audience that does not navigate at all. A retrieval system never sees your menu.
An assistant answering a developer's question does not traverse your hierarchy;
it matches a fragment of text and returns it with whatever context travelled
alongside. **Structure that only exists in the navigation is invisible to that
reader.**

That is the practical shift, and it is what someone in either role deals with
on a Tuesday. The decision that used to be "which section does this page go in"
is now "what does this page declare about itself, such that both a sidebar and a
retriever can act on it". A folder name is a fact about one of those audiences.
A metadata field is a fact about both.

The second reason this is `core`: information architecture is the concept that
makes every later concept in this guide tractable. [Chunking](chunking.md) is a
structural decision. [RAG packaging](rag.md) is a structural decision with
embeddings attached. [llms.txt](llms-txt.md) is a navigation artifact for
machines. If the corpus has no structure, all of those are operating on mush,
and no amount of retrieval sophistication recovers from it.

## The golden path

Take an unstructured pile of pages and give it a structure, then prove the
structure is real by querying it. About forty minutes, no dependencies beyond
Python.

**Step 1: make the mess**

This is the realistic starting state: pages that are individually fine and
collectively unnavigable.

```bash
mkdir -p ia-demo/pages && cd ia-demo
cat > pages/install.md <<'EOF'
# Installing the widget CLI
Run `pip install widget`. Requires Python 3.10 or newer.
EOF
cat > pages/rotate-keys.md <<'EOF'
# Rotating an API key
Call `widget keys rotate`. The old key stays valid for one hour.
EOF
cat > pages/why-keys-expire.md <<'EOF'
# Why keys expire
A long-lived credential is a long-lived risk. One hour of overlap is
the shortest window that does not break deployments mid-rollout.
EOF
cat > pages/cli-reference.md <<'EOF'
# CLI reference
`widget keys rotate` rotates the signing key. `widget keys list` lists them.
EOF
cat > pages/first-deploy.md <<'EOF'
# Your first deploy
By the end of this you will have a running widget. Start by installing.
EOF
ls pages/
```

Five pages, one flat folder. A reader asking "how do I rotate a key" has to
read filenames and guess.

**Step 2: decide what a page declares about itself**

This is the actual architecture work, and it takes judgement rather than
typing. For this corpus, three facts are worth declaring: what kind of page it
is, who it is for, and what it is about.

```bash
python3 - <<'PY'
import pathlib, json

# The architecture, written down. Deciding this IS the work; the code below
# just applies it.
MODEL = {
    "install.md":        ("how-to",      "new-user",  ["installation"]),
    "first-deploy.md":   ("tutorial",    "new-user",  ["installation", "deployment"]),
    "rotate-keys.md":    ("how-to",      "operator",  ["keys", "security"]),
    "why-keys-expire.md":("explanation", "operator",  ["keys", "security"]),
    "cli-reference.md":  ("reference",   "developer", ["keys", "cli"]),
}

for name, (kind, audience, topics) in MODEL.items():
    path = pathlib.Path("pages") / name
    body = path.read_text()
    title = body.splitlines()[0].lstrip("# ").strip()
    front = (
        "---\n"
        f"title: {title}\n"
        f"kind: {kind}\n"
        f"audience: {audience}\n"
        f"topics: [{', '.join(topics)}]\n"
        "---\n\n"
    )
    path.write_text(front + body)
print("structure applied to", len(MODEL), "pages")
PY
head -8 pages/rotate-keys.md
```

**Step 3: prove the structure is real by querying it**

Structure you cannot query is decoration. This is the test:

```bash
python3 - <<'PY'
import pathlib, re

def meta(path):
    text = path.read_text()
    block = text.split("---")[1]
    out = {}
    for line in block.strip().splitlines():
        key, _, value = line.partition(":")
        value = value.strip()
        if value.startswith("["):
            value = [v.strip() for v in value[1:-1].split(",")]
        out[key.strip()] = value
    return out

pages = {p.name: meta(p) for p in sorted(pathlib.Path("pages").glob("*.md"))}

print("Q: I am an operator, what should I read about keys?")
for name, m in pages.items():
    if m["audience"] == "operator" and "keys" in m["topics"]:
        print(f"   {m['kind']:<12} {m['title']}")

print("\nQ: I want instructions, not background.")
for name, m in pages.items():
    if m["kind"] in ("how-to", "tutorial"):
        print(f"   {m['kind']:<12} {m['title']}")

print("\nQ: is anything missing?")
kinds = {m["kind"] for m in pages.values()}
topics = {t for m in pages.values() for t in m["topics"]}
for topic in sorted(topics):
    present = {m["kind"] for m in pages.values() if topic in m["topics"]}
    gaps = kinds - present
    if gaps:
        print(f"   {topic}: no {', '.join(sorted(gaps))} page")
PY
```

**What you built.** The same five files answer three questions they could not
answer before, and the third one is the payoff: **the structure found gaps in
the content.** It reports that `installation` has no reference or explanation
page, that `keys` has no tutorial, and five more besides. Nobody had to notice
any of that by reading.

Two caveats worth holding onto, because this is where a naive coverage check
turns into busywork. Not every gap is a gap: `security` almost certainly does
not need its own tutorial, and a checker that demands all four types for every
topic will generate a backlog of pages nobody wants. And the gaps it found are
only as good as the vocabulary: `topics` here was assigned by hand, so the
report reflects the architecture, not the truth. What the structure gives you is
a question worth asking about each cell, which is still far more than a flat
folder gives you.

## Reference

### The three decisions, and what each one governs

| Decision | Artifact | Governs |
|---|---|---|
| What is a unit of content? | [Content model](content-model.md) | Page boundaries, required fields, what may not be mixed |
| What is it about? | [Taxonomy](taxonomy.md) | The closed vocabularies, their terms, who may add one |
| How is it found? | [Metadata](metadata.md), [findability](findability.md) | Navigation, facets, search, retrieval filters |

### Two kinds of structure, and which audience sees them

| Structure | Humans see it | Machines see it |
|---|---|---|
| Folder layout | Yes, via navigation | Only as a path string |
| Navigation config | Yes | No |
| Front-matter fields | Rarely, as rendered facets | Yes, directly |
| Headings | Yes | Yes, if your [chunker keeps them](chunking.md) |
| Prose that implies structure | Yes | No |

The lesson in that table is the one claim worth remembering from this page:
**structure expressed only as folders and menus does not survive retrieval.**
If it matters, it belongs in a field.

### Vocabulary

| Term | Meaning |
|---|---|
| Content model | The schema a page must satisfy |
| Taxonomy | A controlled set of terms, often hierarchical |
| Facet | One independent axis of classification (audience, product, version) |
| Controlled vocabulary | A closed list; adding a term is a deliberate act |
| Folksonomy | An open tag field. Drifts into `howto`, `how-to` and `How To` within a year |
| Information scent | How well a link predicts what is behind it |
| Card sorting | Research method: users group content, you learn their categories |
| Polyhierarchy | A topic belonging in more than one place at once |

### Where information architecture is usually wrong

| Symptom | Underlying mistake |
|---|---|
| A `misc/` or `advanced/` folder | A category defined by what it is not |
| Pages titled "Overview" in six places | No content model; "overview" is doing four different jobs |
| Navigation six levels deep | Hierarchy used where faceting was needed |
| Search works better than the menu | The structure is in the prose, not in the model |
| Everything tagged `api` | A vocabulary with no discrimination is not a vocabulary |

## How to talk about it

**What a competent answer sounds like.** Do not define the term. Describe a
decision you made and what it cost. "The corpus had a `guides/` folder that
contained tutorials, task instructions and background, so readers mid-task had
to wade through motivation. I split the type out as a declared field rather
than a folder, which meant the navigation and the retrieval filters could both
use it."

**The follow-up is almost always hierarchy versus facets**, and it is the
question that separates people who have done this from people who have read
about it. The answer: hierarchy is for one primary reading order; facets are for
independent axes. Audience, product, version and page type are facets, because
a page has a value on all four simultaneously and no nesting order is right for
every reader. Forcing facets into a tree is the single most common
information-architecture failure, and the symptom is a deep menu with the same
leaf repeated in four branches.

**The tradeoff to volunteer.** Structure costs authoring friction, permanently.
Every required field is a thing a contributor must decide before they can
publish, and every closed vocabulary is an occasional argument about whether a
term should be added. On a corpus of twenty pages that overhead is not worth
paying; the structure is in your head and your head is big enough. The crossover
is somewhere around fifty pages or the second author, whichever comes first.
Saying this unprompted signals that you have paid the cost rather than only
read about the benefit.

**One sharper point.** The strongest version of the NVIDIA bullet is that
navigation and retrieval have different failure modes, so structure designed
only for one fails the other quietly. Navigation fails visibly: a reader cannot
find the page and complains. Retrieval fails invisibly: a model returns a
plausible wrong chunk and the reader never knows there was a better page. That
asymmetry is why machine-readable structure is now the more urgent half, and it
is a genuinely good thing to say out loud.

## How to prove it

**The artifact.** A corpus with a declared content model, and something that
queries it. The query is what makes it real: anyone can add front matter.

**Three things to do, in order:**

1. **Run the golden path** and keep the gap-finding script. Twenty lines that
   report "this topic has no reference page" is a more compelling artifact than
   any diagram of a hierarchy.
2. **Take a real corpus you did not design** and write a one-page audit: what
   the units are, what facets are implicit in the folder names, what is
   mixed that should be split. Your own project's docs, an open-source project's,
   or a previous employer's. The skill being demonstrated is seeing the
   structure that is already there and unstated.
3. **Add a validator** that rejects a page violating the model, and wire it
   into [documentation CI](documentation-ci.md). The step from "we have a
   convention" to "the convention is enforced" is the one that distinguishes
   information architecture as a practice from information architecture as a
   document nobody reads.

**What makes it credible rather than decorative.** A diagram of a proposed hierarchy proves nothing;
every candidate has one. A script that reads a real corpus and reports what is
structurally wrong with it proves you can do the work on content you did not
write, which is the actual job.

This guide's own `concepts.yaml` is the worked example, recorded on the
[demonstrated](../demonstrated.md) page: 106 units, a closed vocabulary for
category, tier and Diátaxis type, a prerequisite graph with a cycle check, and
every route generated from it rather than hand-maintained. The honest limit is
the third decision. Whether a reader actually gets from not knowing to the
right page is a question about readers, and there are none yet.

## Related

- [Diátaxis](diataxis.md), the best-known answer to "what is a unit of content"
- [Content models](content-model.md), the schema layer
- [Taxonomy and controlled vocabularies](taxonomy.md), the naming layer
- [Knowledge architecture](knowledge-architecture.md), what this becomes when the consumers are systems
