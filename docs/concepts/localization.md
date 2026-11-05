---
title: Localization and translation pipelines
summary: Segmenting Markdown for translators, protecting what must not be translated, and verifying it came back intact.
diataxis: how-to
audience: developer
concept: localization
tags: [dac, supporting]
---

# Localization and translation pipelines

`supporting` · difficulty 3 · 4h

!!! note "Not a quotation (adjacent)"
    Neither posting mentions localization. It is here because a platform
    documentation role at a company selling worldwide meets it eventually, and
    because the engineering is a content-model problem rather than a language
    one.

**Prerequisites:** [Content models](content-model.md), [Single-sourcing](single-sourcing.md)

## What it is

The pipeline that gets documentation translated and keeps the translations in
sync as the source changes. Mechanically: segment the source into translatable
units, protect the parts that must not be translated, send the units out, get
them back, verify them, and rebuild.

The reason it is difficulty 3 is that almost all of the difficulty is in
segmentation and protection, both of which are decisions about your content
model. Translation itself is somebody else's job.

## Why the job asks for it

It does not, and the banner says so. The case for knowing it is that
localization is the most unforgiving test of a content model that exists.

A corpus with inconsistent structure, inline HTML, text baked into screenshots
and sentences that assemble themselves out of fragments can be published in
English indefinitely. Try to translate it and every one of those becomes a cost
multiplied by the number of languages. Teams routinely discover their content
model is broken only when the localization bill arrives.

So it belongs in this category as the stress test. If your corpus localizes
cleanly, it is well modelled.

## The golden path

Extract translatable segments from a real Markdown page, break it the way
everybody breaks it first, and verify the round trip. About thirty-five
minutes.

**Step 1: a page with the usual hazards**

````bash
mkdir -p l10n-demo && cd l10n-demo
pip install --quiet polib

cat > page.md <<'EOF'
---
title: Rotate a key
summary: How to rotate an access token.
---

# Rotate a key

Run `widget keys rotate` to replace the current token.

The command prints the new token. See [the configuration guide](configure.md).

!!! warning
    The old token stops working immediately.
EOF
````

Four hazards in eleven lines: front matter with translatable values, an inline
code span that must survive untouched, a link whose text is translatable and
whose target is not, and an admonition whose marker is syntax and whose body is
prose.

**Step 2: segment and protect**

```python
# extract.py
import itertools
import re

PROTECT = [
    (re.compile(r"`[^`\n]+`"), "CODE"),
    (re.compile(r"\]\(([^)\s]+)\)"), "LINK"),   # this one is wrong; see step 3
]


def protect(s):
    counter = itertools.count(1)
    kept = {}
    for pattern, label in PROTECT:
        def sub(m, label=label):
            key = f"{{{label}{next(counter)}}}"
            kept[key] = m.group(0)
            return key
        s = pattern.sub(sub, s)
    return s, kept
```

```bash
python3 extract.py
```

```
extracted 5 segment(s); 2 protected span(s)
  [heading   ] Rotate a key
  [sentence  ] Run {CODE1} to replace the current token.
  [sentence  ] The command prints the new token.
  [sentence  ] See [the configuration guide{LINK1}.
  [admonition] !!! warning
    The old token stops working immediately.
```

**Step 3: read the output properly, because two segments are broken**

Look at the fourth segment: `See [the configuration guide{LINK1}.` The opening
bracket has no closing bracket. The placeholder swallowed it, because
`\]\(([^)\s]+)\)` matches the `]` as well as the parenthesised URL.

A translator receiving that has been handed malformed Markdown and no way to
know where the link text ends. The fix is a lookbehind, so the `]` stays in the
segment:

```python
re.compile(r"(?<=\])\(([^)\s]+)\)")
```

```
naive:   See [the configuration guide{LINK1}.
better:  See [the configuration guide]{LINK1}.
```

The fifth segment has the same class of problem from the other direction. The
admonition is one unit containing both `!!! warning`, which is syntax and must
not be translated, and the body, which must be. Split them:

```python
m = re.match(r"^(!!!\s+\w+.*?)\n(\s+)(.*)$", block, re.S)
# m.group(1) = '!!! warning'                     -> do not translate
# m.group(3) = 'The old token stops working...'   -> translate
```

Neither bug is exotic. Both are what happens when you write segmentation rules
against a few example pages, and both produce segments a translator cannot do
anything sensible with. **Segmentation quality is the whole job**, and the way
to check it is to read your own output as if you were the translator.

**Step 4: verify the round trip**

The returned translation, and the check that matters:

```python
src  = "Run {CODE1} to replace the current token."
de   = "Führen Sie {CODE1} aus, um das aktuelle Token zu ersetzen."
kept = {"{CODE1}": "`widget keys rotate`"}

missing = [k for k in kept if k not in de]
print("placeholders dropped:", missing or "none")
```

```
placeholders dropped: none
reinserted: Führen Sie `widget keys rotate` aus, um das aktuelle Token zu ersetzen.
```

And the failure this check exists for, a translation that dropped the
placeholder because it read as noise:

```
a translation that dropped it: Führen Sie den Befehl aus, um das Token zu ersetzen.
placeholders dropped: ['{CODE1}']
```

Without that check, the German page tells the reader to run "the command" and
never says which. A placeholder-integrity check on every returned segment is
not optional.

**Step 5: measure expansion, on the right basis**

```
masked segment (what the translator sees):  en= 41 de= 58  +41%
full sentence (what the reader sees):       en= 54 de= 71  +31%
```

Use the second figure. The masked one is inflated, because `{CODE1}` is shorter
than the code it stands for and so understates the English. Measure expansion
on the reinserted string.

Thirty per cent is the usual working figure for German against English, and it
is why layouts with fixed-width elements break on translation rather than
merely looking different.

**What you built.** A segmentation pass, two corrected rules, a
placeholder-integrity check, and an honest expansion number.

## Reference

### What must not be translated

| Element | Why |
|---|---|
| Code spans and blocks | They are executed, not read |
| Command names, flags, API identifiers | Same |
| Link targets | A URL is not prose |
| File paths and environment variables | Same |
| Admonition markers and directive names | Syntax |
| Front-matter keys | Schema; the *values* often are translatable |
| Product names | Policy; decide once and record it |

Front matter is the one teams get wrong in both directions: translating the
keys breaks the build, and failing to translate `title` and `summary` leaves
the navigation in English.

### What breaks when you actually ship it

| Problem | What it does |
|---|---|
| Text expansion, roughly 30% for German | Breaks fixed-width layouts, truncates nav labels |
| Right-to-left scripts | Needs logical CSS properties, not `left` and `right` |
| Double-byte scripts | Font, line-breaking and input-method issues |
| Screenshots with embedded text | Untranslatable without regenerating them |
| Sentences assembled from fragments | Word order differs; fragments cannot be reordered |
| Sorting and collation | Alphabetical order is language-specific |
| Dates, numbers, units | Formats differ; a hard-coded format is a bug |

The fragment row is a content-model failure rather than a presentation one. A
sentence built as `"Set " + field + " to enable " + feature` cannot be
translated correctly into a language with different word order, and the only
fix is to make the whole sentence one translatable unit with named
placeholders.

### Keeping translations in sync

| Mechanism | Does |
|---|---|
| Translation memory | Reuses previous translations for unchanged segments |
| Source hashing per segment | Marks a translation stale when its source changes |
| Fuzzy matching | Flags near-matches for review rather than silently reusing |
| Fallback to source | Shows English rather than nothing for untranslated segments |
| A per-language freshness report | The [freshness](freshness-monitoring.md) problem, times N |

Segment-level staleness is what makes this maintainable. Without it, any source
edit invalidates a whole page and you pay to retranslate work that did not
change.

### Where this sits in the generators

| Generator | Support |
|---|---|
| Docusaurus | Built in: per-locale builds and a translation directory |
| Sphinx | `gettext` builder, a mature and conventional workflow |
| MkDocs | Plugin, and the least mature of the three |
| Antora | Component-based; a locale is usually a separate component |

If localization is known to be coming, it belongs in the
[generator choice](static-site-generators.md), because retrofitting it is
substantially harder than starting with it.

## How to talk about it

**Lead with it as a content-model test.** "Localization is the most
unforgiving test of a content model. A corpus with inline HTML, assembled
sentences and text baked into screenshots publishes fine in English and
multiplies every one of those defects by the number of languages. Most teams
find out their model is broken when the first translation bill arrives."

**The follow-up is about keeping translations current**, and the answer is
segment-level staleness: hash each source segment so a change invalidates only
the segments it touched. Without it, a typo fix invalidates a whole page.

**The tradeoff to volunteer.** Segmentation is where the quality lives and it
is never finished. My own first pass produced two broken segments out of five:
a placeholder that ate a link's closing bracket, and an admonition whose syntax
marker was bundled with its prose. Both would have reached a translator. You
have to read your own extraction output as the translator will, and you need a
placeholder-integrity check on everything that comes back, because a dropped
placeholder produces fluent, confident, wrong instructions.

**One sharper point.** Assembled sentences are the defect that cannot be fixed
downstream. Concatenating fragments is fine in English and impossible to
translate correctly where word order differs, so the whole sentence has to be
one unit with named placeholders. That decision is made in the content model
long before anybody thinks about languages, which is why localization belongs
in this category rather than in a translation one.

## How to prove it

**The artifact.** An extraction script whose output you have read as a
translator would, plus a placeholder-integrity check on returned segments.

**Three things to do, in order:**

1. Run the golden path, and read step 2's output before step 3 tells you what
   is wrong with it. Spotting the malformed segment yourself is the exercise.
2. Grep a corpus you own for assembled sentences: string concatenation in
   templates, or one sentence split across a list. Each is untranslatable.
3. Write the placeholder-integrity check. It is five lines, and it is the
   difference between a wrong page and a caught error.

**What makes it credible rather than decorative.** Neither of this guide's
repositories is localized, which the [demonstrated](../demonstrated.md) page
records. What travels is the specific engineering: a segmentation pass, the two
bugs it had on first run, why each one matters to a translator, and an
expansion figure measured on the right basis rather than quoted from a blog
post.

## Related

- [Content models](content-model.md), which localization stress-tests
- [Single-sourcing](single-sourcing.md), whose fragments are a localization hazard
- [Freshness monitoring](freshness-monitoring.md), the same problem per language
- [Choosing a static site generator](static-site-generators.md), where support differs most
