---
title: Taxonomy and controlled vocabularies
summary: "Closing a vocabulary so values can be relied on, and checking that something actually reads it."
diataxis: explanation
audience: developer
concept: taxonomy
tags: [ia, core]
---

# Taxonomy and controlled vocabularies

`core` · difficulty 2 · 3h

!!! quote "Asked for by name"
    NVIDIA: "Information architecture skills: content modeling, taxonomy, and metadata for both navigation and machine retrieval"

**Prerequisites:** [Content models](content-model.md)

**Leads to:** [Style guides and terminology management](style-guide.md), [Detecting terminology drift](terminology-drift.md)

## What it is

The set of agreed terms your content is classified by, and the decision about
which of those sets are **closed**. A closed vocabulary has a fixed list of
permitted values and a check that rejects anything else. An open one is a text
field people type into.

That distinction is the whole concept. An open vocabulary is a suggestion. A
closed one is a guarantee, and a guarantee is the only thing a pipeline can be
built on.

## Why the job asks for it

NVIDIA names taxonomy between content modeling and metadata, which is where it
belongs: the model says a field exists, the taxonomy says what may go in it,
and metadata is the result.

The practical stake is filtering. "Show me the how-to pages for operators" is
answerable only if `diataxis` and `audience` are closed, because a query
against an open field has to guess at spellings, synonyms and capitalisation.
Every retrieval feature in the [AI-ready](agent-ready-content.md) category is
a filter over a vocabulary, so a corpus with open vocabularies caps how good
retrieval can get no matter which model is behind it.

The second stake is that closing a vocabulary forces a decision. Arguing about
whether a page is a tutorial or a how-to is a useful argument, and an open
field lets everybody avoid having it.

## The golden path

Close a vocabulary, then discover the failure a closed vocabulary does not
protect against. About twenty-five minutes.

**Step 1: see what a real corpus's vocabularies look like**

```python
import collections
import re
from pathlib import Path

import yaml

fields = collections.Counter()
values = collections.defaultdict(collections.Counter)
pages = 0
for p in sorted(Path("docs").rglob("*.md")):
    m = re.match(r"^---\n(.*?)\n---\n", p.read_text(), re.S)
    if not m:
        continue
    pages += 1
    for k, v in (yaml.safe_load(m.group(1)) or {}).items():
        fields[k] += 1
        if isinstance(v, list):
            for item in v:
                values[k][str(item)] += 1
        elif isinstance(v, (str, bool)) and len(str(v)) < 30:
            values[k][str(v)] += 1
```

```
121 pages

field        pages  coverage  values
title          121      100%  free text
summary        121      100%  free text
diataxis       121      100%  reference(53), explanation(46), how-to(22)
audience       121      100%  developer(100), new-user(13), operator(5), contributor(3)
concept         64       52%  64 distinct
tags            64       52%  core(43), ai(21), supporting(19), qa(14), dac(14) +3 more
generated       53       43%  True(53)
```

Two vocabularies look healthy: `diataxis` with three values and `audience`
with four, both at full coverage. `tags` sits at 52 per cent, which means it
cannot be depended on for anything, exactly as the
[content model](content-model.md) page argues about optional fields.

**Step 2: look harder at the healthy-looking one**

`diataxis: reference` on 53 pages. Split that by whether the page was
generated:

```python
(gen_types if fm.get("generated") else hand_types)[fm.get("diataxis")] += 1
```

```
generated pages by diataxis: {'reference': 53}
hand-written by diataxis:    {'how-to': 22, 'explanation': 46}
```

Every generated page is `reference`. **No hand-written page is.**

So in this corpus `diataxis: reference` did not mean reference documentation.
It meant "generated stub", because the placeholder generator hardcoded the
value. The vocabulary was closed, every value was legal, and the field was
lying on 44 per cent of the pages.

A closed vocabulary guarantees values come from the list. It guarantees nothing
about whether they are *true*.

**Step 3: find out why nobody noticed**

```bash
grep -rn "diataxis" src/fieldguide/*.py hooks/*.py mkdocs.yml
```

```
src/fieldguide/generate.py:144:        "diataxis": "reference",
src/fieldguide/scaffold.py:102:        "diataxis: explanation",
```

Two writers, **zero readers**. Nothing consumed the field: not navigation, not
search, not a hook, not a validator. A vocabulary nobody reads is a vocabulary
that is already wrong, and nothing exists that would tell you.

That is the general rule worth taking away. What keeps a vocabulary honest is
not the list of permitted values. It is a consumer that breaks when the values
are wrong.

**Step 4: make the value honest**

A generated stub has no Diátaxis type, because it has no content. Claiming one
is the lie, so add the value that is true:

```python
DIATAXIS = ("tutorial", "how-to", "reference", "explanation", "placeholder")
```

```python
# in the placeholder generator
"diataxis": "placeholder",
```

```
all pages by diataxis:  {'how-to': 22, 'explanation': 46, 'placeholder': 53}
generated pages:        {'placeholder': 53}
```

`placeholder` is not part of Diátaxis. Adding a value the framework lacks is
the right call when the alternative is a value that is wrong: the vocabulary
describes your corpus, not a book.

**Step 5: give it a reader, so it cannot drift again**

```python
if isinstance(data, dict) and "diataxis" in data:
    if data["diataxis"] not in DIATAXIS:
        out.append(f"{page}: diataxis is {data['diataxis']!r}, "
                   f"which is not one of {list(DIATAXIS)}")
```

```
  FIRES: diataxis is 'refrence', which is not one of ['tutorial', 'how-to', ...]
```

Plus a regression test asserting that no generated page claims a type it has
not earned. The field now has a consumer, so a typo or a hardcoded default
fails a build.

**What you learned.** Closing a vocabulary stops illegal values. Only a
consumer stops untrue ones, and a field nothing reads drifts immediately and
silently.

## Reference

### What to close and what to leave open

| Field | Closed? | Why |
|---|---|---|
| Page type (`diataxis`) | Yes | Three or four values, and filters depend on it |
| Audience | Yes | Small set; open produces "devs", "developer", "Developers" |
| Status or lifecycle stage | Yes | A workflow with unlimited states is not a workflow |
| Product area or component | Yes, from the product's own list | It must match what engineering calls it |
| Tags or keywords | Usually open, and therefore mostly useless | See below |
| Title, summary | Open | They are prose |
| Author | Open, or a people directory | Not a classification |

### Why free tags disappoint

`tags` above sits at 52 per cent coverage with eight distinct values. A tag
vocabulary fails in a predictable sequence: it is optional, so half the corpus
omits it; it is open, so synonyms accumulate; nothing depends on it, because it
is unreliable; and because nothing depends on it, nobody maintains it.

If you want tags to work, close the list and require them. If you are not
willing to do both, the honest move is to delete the field rather than keep a
half-populated one implying a classification nobody can trust.

### The three properties a vocabulary needs

| Property | Without it |
|---|---|
| Closed | Synonyms and spellings accumulate, so filters miss |
| Required | Absent half the time, so nothing can depend on it |
| Consumed | Nothing breaks when values are wrong, so they go wrong |

All three, or you do not have a vocabulary. The third is the one teams skip,
and the one this guide got wrong across 53 pages.

### Taxonomy against its neighbours

| Concept | Is about |
|---|---|
| Taxonomy | Which terms are permitted, as classification |
| [Style guide](style-guide.md) | Which terms to use in prose |
| [Terminology drift](terminology-drift.md) | Whether the corpus still obeys either |
| [Metadata](metadata.md) | The values actually attached to pages |
| [Content model](content-model.md) | Which fields exist at all |

Taxonomy and style guide overlap without being the same thing. `access token`
as the canonical term in prose is a style decision; `audience: operator` as a
permitted classification value is a taxonomy decision. Confusing them produces
a style guide full of metadata rules nobody can enforce.

### Who owns the vocabulary

The product's own terms are not yours to invent. If engineering calls a
component `ingest-gateway`, your `component` vocabulary uses that string even
if a nicer name exists, because a classification that disagrees with the
product is one readers cannot map onto anything.

Where there is no external source of truth, as with page type and audience,
you own it, and the right size is the smallest set that supports a filter
somebody actually wants.

## How to talk about it

**Lead with filtering, not tidiness.** "Closing a vocabulary is what makes
filtering possible: 'how-to pages for operators' is answerable only if those
two fields have fixed value sets. Every retrieval feature is a filter over a
vocabulary, so open vocabularies cap how good retrieval can get regardless of
the model."

**The follow-up that separates experience from theory** is what keeps a
vocabulary honest, and the answer is a consumer. I had a closed, fully
populated `diataxis` field whose value was wrong on 44 per cent of pages,
because a generator hardcoded one value and nothing read the field.

**The tradeoff to volunteer.** Every closed vocabulary is an argument you have
to have, and then a constraint contributors live with. A vocabulary that is too
small forces pages into the wrong bucket, and the mitigation is to add the
value that is true rather than making authors lie. `placeholder` is not in
Diátaxis, and adding it beat having 53 pages claim to be reference
documentation.

**One sharper point.** Free-tag fields are where taxonomies go to die, and the
failure is mechanical rather than cultural: optional means half-populated,
half-populated means nothing can depend on it, and nothing depending on it
means nobody fixes it. Either close the list and require it, or delete the
field.

## How to prove it

**The artifact.** A closed vocabulary, a check that rejects values outside it,
and something that consumes it.

**Three things to do, in order:**

1. Run step 1 against a corpus you own and print the value distribution for
   every field. Skew is the signal: one value dominating usually means a
   default somewhere.
2. Grep for readers of your most important metadata field. If writers
   outnumber readers, that field is already wrong.
3. Pick your least reliable vocabulary and either close and require it, or
   remove it. Both are improvements; leaving it half-populated is not.

**What makes it credible rather than decorative.** `docpack` validates five
front-matter fields, two of them closed vocabularies, rejected in CI. The more
useful story is this one: a closed vocabulary that was fully populated,
entirely legal and wrong on 53 pages, found by comparing the value distribution
between generated and hand-written pages, and fixed by adding an honest value
plus a consumer that fails the build.

## Related

- [Content models](content-model.md), which declares that the field exists
- [Metadata for navigation and retrieval](metadata.md), the values and who reads them
- [Style guides and terminology management](style-guide.md), the prose half
- [Detecting terminology drift](terminology-drift.md), measuring whether either is obeyed
