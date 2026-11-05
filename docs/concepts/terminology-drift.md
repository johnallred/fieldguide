---
title: Detecting terminology drift
summary: Measuring how consistently a corpus uses its own vocabulary, and finding where it stopped.
diataxis: how-to
audience: developer
concept: terminology-drift
tags: [qa, supporting]
---

# Detecting terminology drift

`supporting` · difficulty 2 · 3h

!!! quote "Asked for by name"
    NVIDIA: "Automate the content lifecycle with LLMs and scripting, from drafting and updating to auditing, with checks for freshness, code accuracy, and terminology drift, and human review where judgment matters"

**Prerequisites:** [Taxonomy](taxonomy.md), [Prose linting with Vale](prose-linting.md)

## What it is

Measuring, across a whole corpus, how often each concept is referred to by its
agreed name versus by something else. A [Vale rule](prose-linting.md) catches a
deprecated term in one pull request. Drift detection answers the different
question of how far the corpus as a whole has already moved, which pages are
worst, and whether the situation is improving.

The distinction matters because the two produce different actions. A linter
finding is a fix. A drift measurement is a decision: rename the thing, update
the glossary, or accept that the term you chose lost.

## Why the job asks for it

NVIDIA names it alongside freshness and code accuracy as one of three things
the content lifecycle should be audited for. All three share a shape: the
individual page was correct when written, and the world moved.

Terminology drift is the one that damages trust fastest, because it is
invisible page by page. Every page is internally consistent. The reader meets
`access token` in the quickstart, `API key` in the reference and `auth token`
in the troubleshooting guide, and has to work out whether those are three
things or one. Nothing is wrong; the corpus is just no longer speaking with one
voice, and a reader who cannot tell whether two names mean the same thing stops
trusting any of them.

It also breaks retrieval, which is why it sits next to the AI-readiness work. A
search for `access token` cannot rank a page that calls it an API key, and
[embeddings](embeddings.md) blur the distinction without resolving it. Three
names for one concept means a retriever has three weaker clusters instead of
one strong one.

## The golden path

Measure drift against a glossary, then discover that the naive measurement
flatters you. About thirty minutes.

Committed as `drills/terminology_drift.py`, which walks all four states in one
run. Tests assert it still prints the tables below, and that the glossary and
three sample pages it measures are the ones this page tells you to write.

**Step 1: a glossary as data**

````bash
mkdir -p drift-demo/docs && cd drift-demo

cat > glossary.yaml <<'EOF'
terms:
  - canonical: widget
    deprecated: [Widget CLI, widget-cli, WidgetCLI]
  - canonical: data set
    deprecated: [dataset, data-set]
  - canonical: access token
    deprecated: [API key, apikey, auth token]
EOF

cat > docs/a.md <<'EOF'
# Install
Install widget, then create an access token.
EOF
cat > docs/b.md <<'EOF'
# Configure
Point the Widget CLI at your dataset. Use your API key.
EOF
cat > docs/c.md <<'EOF'
# Troubleshoot
If widget-cli fails, check the auth token and the data-set path.
EOF
````

Three pages, deliberately inconsistent, which is what a real corpus looks like
after two years and nine contributors.

**Step 2: the obvious measurement**

Count canonical uses, count deprecated uses, divide. Running that version
produces this:

```
canonical        conformant  total   rate  variants
widget                    3      5    60%  Widget CLI(1), widget-cli(1)
data set                  0      2     0%  dataset(1), data-set(1)
access token              1      3    33%  API key(1), auth token(1)
```

Sixty per cent conformance on `widget`. That number is wrong, and wrong in the
flattering direction.

**Step 3: find out why**

```bash
python3 - <<'PY'
import re
from pathlib import Path
pat = re.compile(r"\bwidget\b", re.I)
for p in sorted(Path("docs").rglob("*.md")):
    text = p.read_text()
    for m in pat.finditer(text):
        print(f"{p}: ...{text[max(0, m.start() - 12):m.end() + 12]!r}...")
PY
```

```
docs/a.md: ...'all\nInstall widget, then creat'...
docs/b.md: ...'e\nPoint the Widget CLI at your'...
docs/c.md: ...'bleshoot\nIf widget-cli fails, '...
```

Two of the three "conformant" matches are the canonical term matching **inside
its own deprecated variants**. `\bwidget\b` matches the `Widget` in `Widget
CLI` and the `widget` in `widget-cli`, because a hyphen is a word boundary.

This is not a quirk of this example. The canonical term is a substring of its
deprecated forms most of the time, because deprecated forms are usually the
canonical term plus something: a suffix, a hyphen, a product word. So the naive
measurement systematically counts drift as conformance, and the worse the drift
the more it flatters you.

**Step 4: mask before you count**

```python
# drift.py
import re
from collections import Counter
from pathlib import Path

import yaml

terms = yaml.safe_load(Path("glossary.yaml").read_text())["terms"]
rows, per_page = [], Counter()

for entry in terms:
    canon = entry["canonical"]
    # Longest first, so "API key" is consumed before any shorter variant.
    deprecated = sorted(entry["deprecated"], key=len, reverse=True)
    variants, conformant = Counter(), 0

    for page in sorted(Path("docs").rglob("*.md")):
        text = page.read_text()
        for bad in deprecated:
            pattern = re.compile(r"\b" + re.escape(bad) + r"\b")
            found = pattern.findall(text)
            if found:
                variants[bad] += len(found)
                per_page[str(page)] += len(found)
            # Mask it so the canonical count cannot see it.
            text = pattern.sub("\x00" * len(bad), text)
        conformant += len(re.findall(r"\b" + re.escape(canon) + r"\b", text, re.I))

    total = conformant + sum(variants.values())
    rows.append((canon, conformant, total, variants))

print(f"{'canonical':16} {'conformant':>10} {'total':>6} {'rate':>6}  variants")
for canon, ok, total, variants in rows:
    rate = f"{100 * ok // total}%" if total else "n/a"
    v = ", ".join(f"{k}({n})" for k, n in variants.most_common())
    print(f"{canon:16} {ok:>10} {total:>6} {rate:>6}  {v}")
print()
print("worst pages:", ", ".join(f"{p} ({n})" for p, n in per_page.most_common(3)))
drifted = sum(sum(v.values()) for _c, _o, _t, v in rows)
print(f"\n{'FAIL' if drifted else 'ok'}: {drifted} deprecated usage(s)")
raise SystemExit(1 if drifted else 0)
```

```bash
python3 drift.py
```

```
canonical        conformant  total   rate  variants
widget                    1      3    33%  Widget CLI(1), widget-cli(1)
data set                  0      2     0%  dataset(1), data-set(1)
access token              1      3    33%  API key(1), auth token(1)

worst pages: docs/b.md (3), docs/c.md (3)

FAIL: 6 deprecated usage(s)
```

`widget` drops from 60 per cent to 33 per cent, which is the true figure. The
masking also gives you the two outputs that make this actionable: a per-term
rate, and a ranked list of which pages to fix first.

**Step 5: confirm it goes green**

```bash
printf '# Configure\nPoint widget at your data set. Use your access token.\n' > docs/b.md
printf '# Troubleshoot\nIf widget fails, check the access token and the data set path.\n' > docs/c.md
python3 drift.py
```

```
widget                    3      3   100%
data set                  2      2   100%
access token              3      3   100%

ok: 0 deprecated usage(s)
```

**What you built.** A measurement with a direction, which is what makes drift
a managed quantity rather than a complaint. Run it on a schedule and the rate
over time tells you whether the glossary is winning.

## Reference

### Linting versus drift detection

| | Vale rule | Drift measurement |
|---|---|---|
| Scope | One pull request | The whole corpus |
| Output | A finding to fix | A rate and a ranking |
| Runs | On every change | On a schedule |
| Answers | Did this diff regress? | How bad is it, and where? |
| Blocks a merge | Yes, for terminology | No |
| Needs a glossary | Implicitly, in the rule | Explicitly, as data |

Build both. The linter stops new drift; the measurement tells you about the
drift you already have, which the linter will never mention because those pages
are not being changed.

### What the rate tells you to do

| Conformance | Interpretation | Action |
|---|---|---|
| Above 95% | The term is established | Keep the linter, stop measuring |
| 60% to 95% | Real drift, fixable | Fix the worst pages, keep the gate |
| Below 60% | The glossary lost | Reconsider the canonical term |
| 0% with usages | The canonical name is aspirational | Someone renamed it in a document and nowhere else |

That last row happens more than it should. A term is changed in a style guide,
nobody updates the corpus, and a year later the canonical name exists only in
the glossary. The measurement makes that visible in one run.

### Counting traps

| Trap | Effect | Fix |
|---|---|---|
| Canonical matches inside its variants | Inflates conformance | Mask deprecated forms first |
| Overlapping variants | Double counts | Match longest first |
| Code samples and identifiers | False positives on `api_key` | Exclude fenced blocks, or treat identifiers as a separate vocabulary |
| Quoted third-party names | Flags correct prose | An allow-list, plus a suppression comment |
| Case-insensitive canonical | `Widget` and `widget` merge | Decide whether casing is part of the term |

The third one is the most common in developer documentation. `access token` in
prose and `ACCESS_TOKEN` in a sample are both correct, and a checker that does
not separate prose vocabulary from code identifiers will drown you.

## How to talk about it

**Lead with retrieval, not consistency**, because it is the stronger argument
and the one that connects to the rest of the job. "Three names for one concept
means a retriever has three weak clusters instead of one strong one, so drift
degrades search and assistant answers before anyone complains about style."

**The follow-up is how you decide what the canonical term is**, and the honest
answer involves usage data rather than preference: what the product calls it in
the UI, what support tickets call it, what the search logs show people typing.
A glossary that disagrees with all three will lose.

**The tradeoff to volunteer.** A drift report is only as good as its glossary,
and maintaining a glossary is real ongoing work that nobody is assigned. If you
automate the measurement without owning the glossary, you get a dashboard
measuring a stale list. Say that the glossary is the artifact and the script is
the easy part.

**One sharper point.** The naive measurement flatters you in proportion to how
bad the drift is, because the canonical term is usually a substring of its own
deprecated forms. A conformance number produced without masking is not
conservative, it is biased toward good news, which is the worst property a
quality metric can have.

## How to prove it

**The artifact.** A glossary in version control, a script that reports a rate
per term and a ranked list of pages, and a before-and-after number.

**Three things to do, in order:**

1. Run the golden path. Step 3 is the part worth your time: watch the canonical
   term match inside its own variants.
2. Write a ten-term glossary for a corpus you already have, and run the
   measurement. The first number is almost always worse than the team's
   estimate, which is the point.
3. Pick the term with the lowest rate and decide, in writing, whether to fix
   the corpus or change the glossary. That decision is the deliverable.

**What makes it credible rather than decorative.** A rate measured twice, with
work in between. One measurement is a complaint; two measurements and a
glossary commit are a managed quantity. Nothing in this guide's own
repositories demonstrates this yet, which is recorded honestly on the
[demonstrated](../demonstrated.md) page rather than implied.

## Related

- [Prose linting with Vale](prose-linting.md), the per-change gate
- [Taxonomy](taxonomy.md), where the canonical vocabulary is decided
- [Freshness monitoring](freshness-monitoring.md), the same auditing shape applied to age
- [Embeddings](embeddings.md), why three names for one concept hurt retrieval
