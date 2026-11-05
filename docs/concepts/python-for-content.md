---
title: Python for content automation
summary: "Counting the prose in a corpus five ways: the naive answer is a quarter high, and the last correction is worth 0.2 per cent in aggregate and four per cent on one page in five."
diataxis: explanation
audience: developer
concept: python-for-content
tags: [auto, core]
---

# Python for content automation

`core` · difficulty 2 · 5h

!!! quote "Asked for by name"
    NVIDIA: "Working proficiency in Python or similar to automate content tasks, transform data, and integrate with APIs"

**Leads to:** [Content and data transformation](content-data-transformation.md), [API integration](api-integration.md)

## What it is

Writing programs whose input is documentation. Not a specialism in the
language, which is the ordinary standard library and nothing exotic, but a
specialism in the data: **documentation is text that carries structure, and
structure is invisible to the tools text invites you to reach for.**

Every interesting bug in this area comes from that sentence. A Markdown file
looks like lines, so you process lines; the meaning lives in nesting, fences
and front matter, which lines cannot see.

## Why the job asks for it

NVIDIA's bullet is one sentence naming three jobs: automate content tasks,
transform data, integrate with APIs. This concept is the first, and the other
two have pages of their own because they fail differently.

The reason it is a requirement rather than a nice-to-have is arithmetic. A
corpus of a hundred pages has a few hundred cross-references, a few hundred
code samples and a metadata field on every page, and every claim anybody makes
about it ("every page has a summary", "no sample is broken", "this concept is
unreachable") is a loop over files. Without that, the claims are assertions
somebody remembers checking once.

The reason it is harder than it looks is that the loop is easy and the parsing
is not, and a wrong parse produces a plausible number rather than an error.

## The golden path

One task, five implementations, each correcting the last. Count the words a
reader would actually read across all 106 pages. About twenty-five minutes,
and the interesting part is which corrections turn out to matter.

**Step 1: the obvious one**

```python
words = sum(len(p.read_text().split()) for p in pages)
```

```
corpus: 106 written pages

approach                        words      error
1  split() on the file         224929        27%
```

Twenty-nine per cent high, and nothing about the program suggests so. It would
be reported, used to set a page-length policy, and never questioned.

**Step 2: front matter is not prose**

Every page opens with a YAML block carrying `title`, `summary`, `diataxis`,
`audience`, `concept` and `tags`. A reader sees none of it.

```python
FM = re.compile(r"^---\n.*?\n---\n", re.S)
```

```
2  minus front matter          221166        25%
```

Two points. Worth fixing and not the problem.

**Step 3: HTML comments are not prose either**

```python
COMMENT = re.compile(r"<!--.*?-->", re.S)
```

```
3  minus HTML comments         221101        25%
```

**Sixty-six words across the whole corpus.** Three hundredths of one per cent,
which looks like a correction not worth writing.

Hold that thought until step 6, because it is the most misleading number on
this page.

**Step 4: code is not prose, and this is where the error lives**

```
4  minus fences, toggled       191137         0%
5  minus fences, parsed        190748    (truth)
```

Forty-five thousand words, **nineteen per cent of everything outside the front
matter**, are inside code fences. That single distinction is worth ten times the other corrections
combined, and it is the one a line-oriented program cannot make without
tracking state.

**Step 5: the two fence implementations, and why the aggregate lies**

Version 4 toggles a flag on any line that looks like a fence marker. Version 5
uses a parser that tracks marker length and skips heredoc bodies. The
difference across the corpus:

```
corpus-level error of the toggle:  +389 words  (0.2%)
```

Two tenths of one per cent. By that number the parser was a waste of an
afternoon. Now count pages instead of words:

```
pages where the two agree:      86/106
pages where they disagree:      20/106

page                           parsed    delta    error
coding-agents                    2139      +85       4%
security-documentation           1546      +58       4%
tutorial-design                  1554      +57       4%
agent-skills                     2274      +23       1%
chunking                         1753      +20       1%
```

**A fifth of the pages are wrong, the worst by four per cent, and the corpus
total is accurate to two decimal places.** The errors are small, one-directional
and sparse, so summing them produces a number close to the truth by cancellation
of significance rather than by correctness.

Which measurement you believe depends entirely on whether you aggregate, and
the aggregate is the one people report.

The pages that disagree have a common shape: a four-backtick fence containing
three-backtick fences, because they document Markdown or contain heredocs that
write Markdown. The toggle sees the inner marker and closes the outer block, so
shell commands become prose. Nothing about that is visible in a 0.2 per cent
error.

**Step 6: the correction from step 3, measured on a different sample**

HTML comments were a few dozen words, three hundredths of one per cent. At the
time the corpus still held nine pages the scaffold had generated and nobody had
written, so the identical measurement had a second sample to run over:

```
written pages (106):
  words outside front matter: 235983
  of those, inside comments:       79   (0.03%)

freshly scaffolded pages (9):
  words outside front matter:   3160
  of those, inside comments:    2601   (82%)
```

The first block is current and moves whenever a page is edited. The second
cannot be re-run: all 106 pages are written now, so that sample no longer
exists, and it is kept because it is the whole point of the step.

**The same term in the same measurement: 0.03 per cent on one sample and 82 per
cent on another.** Scaffolded pages are mostly authoring prompts inside
comments, which is their job, and the prompts are deleted as pages get written.

So the correction I nearly dropped as negligible is the dominant term for any
measurement that includes unwritten pages, and a word-count gate that ignored
it was once 84 per cent pre-satisfied by the template's own instructions. The
honest conclusion is not that comments matter; it is that **"this correction is
negligible" is a statement about a sample, not about a corpus**, and it has to
be re-checked whenever the sample changes.

**What you built.** One measurement in five versions, an error budget showing
where the naive quarter actually sits, a demonstration that a 0.2 per cent
aggregate error can mean a fifth of pages are wrong, and a negligible
correction that becomes dominant on a different slice.

## Reference

### The standard library does almost all of it

| Need | Reach for | Not |
|---|---|---|
| Walking a tree | `pathlib.Path.rglob` | `os.walk` with string joins |
| Front matter | `yaml.safe_load` | A regex per field |
| Writing front matter | `yaml.safe_dump` | f-strings; they break on a colon |
| Counting and grouping | `collections.Counter` | Hand-rolled dicts |
| Stable identifiers | `hashlib` on normalised content | `hash()`, which is salted per process |
| Running a sample | `subprocess.run(capture_output=True)` | `os.system` |
| Structured records | `json`, one object per line | A CSV with embedded newlines |
| Fences, nesting, headings | A parser you own and test | A regex |

Only the last row needs writing, and only because no dependency does exactly
what a corpus-specific checker needs.

### What defeats a regex, specifically

| Construct | Why |
|---|---|
| Nested fences | Needs marker length, which is state |
| Heredocs inside fences | The body may contain fence markers |
| A `#` inside a code block | A shell comment, not a heading |
| Indented fences in list items | Up to three spaces, then content indentation |
| Inline code spans | `` `like this` `` can contain anything |
| Links with parentheses in the URL | Balanced delimiters are not regular |
| A YAML colon in a value | Breaks any hand-rolled serialiser |

Each of those produced a real bug in this project, and none produced an
exception. They produced numbers.

### Error budgets beat precision

Before optimising a measurement, find out which term dominates:

| Correction | Worth, on written pages |
|---|---|
| Excluding code fences | 25% |
| Excluding front matter | 2% |
| A correct fence parser over a toggle | 0.2% |
| Excluding HTML comments | 0.04% |

Then check the same table on the sample you will actually run against, because
two of those four rows change by more than an order of magnitude between
written and unwritten pages.

### Aggregate against per-item

| Reported as | Hides | Use for |
|---|---|---|
| A corpus total | Sparse, one-directional, small errors | Reporting |
| A per-page figure | Nothing; it is the reader's experience | Deciding what to fix |
| A count of pages over a threshold | The size of each failure | Planning |
| A maximum | How common the failure is | Finding the worst case |

A sum is the single worst way to look for a parsing bug, because parsing bugs
are sparse and sums are robust to sparse error. That is the opposite of what you
want from a check.

### Habits that prevent the plausible wrong number

| Habit | Prevents |
|---|---|
| A fixture with a hand-counted answer | Every bug on this page |
| Printing the worst item, not just the total | Aggregate blindness |
| Asserting the measurement on a known-bad input | Silent regression |
| Three states, never two: present, absent, out of scope | Conflating "no anchors" with "not in the tree" |
| Re-deriving every metric after adding a generator | A template satisfying its own gate |
| Normalising whitespace before matching | Wrapped prose defeating a pattern |

## How to talk about it

**Lead with the data, not the language.** "Python for content automation is not
a language specialism, it is knowing that documentation is text carrying
structure, and that structure is invisible to the line-oriented tools text
invites you to use. Every real bug I have had in this area came from that, and
none of them raised an exception. They returned numbers."

**The follow-up is a worked example, and this one is short.** Counting the prose
in a 106-page corpus: the naive `split()` is 27 per cent high. Front matter
accounts for two points, HTML comments for four hundredths of one, and code
fences for twenty-five. So the single distinction worth making is that code is
not prose, and it is exactly the one a line-oriented program cannot make
without tracking state.

**Then the part that generalises.** Replacing a naive fence toggle with a real
parser moved the corpus total by 0.2 per cent, which says the parser was not
worth writing. Counting pages instead, a fifth of them were wrong and the worst
by five per cent. Parsing errors are sparse and one-directional, so a sum is
robust to exactly the defect you are looking for. A sum is the worst available
instrument for finding a parsing bug.

**The tradeoff to volunteer.** Writing your own parser is a maintenance
liability and I would not recommend it as a default: use a real Markdown library
where you can. The case for owning the fence logic in a checker is that it has
to answer questions a renderer does not, such as whether a closing fence
carries an info string, and that it has to be fast enough to run on every
commit. That is a narrow justification and it does not extend to parsing links
or tables, which I would not hand-roll.

**One sharper point.** The correction I nearly discarded as negligible, 65 words
across the corpus, is 84 per cent of the text in a freshly scaffolded page. The
same term, the same measurement, three orders of magnitude apart depending on
which pages are in the sample. "This correction is negligible" is a claim about
a sample and not about a corpus, and it needs re-checking whenever the sample
changes, which in a growing corpus is constantly.

## How to prove it

**The artifact.** A measurement over a corpus you own, with its error budget
written down and a fixture that pins the answer.

**Three things to do, in order:**

1. Count something about your own corpus the naive way, then subtract front
   matter, comments and code in that order, and write down what each correction
   was worth. Predict the ranking first; most people put code third.
2. Take any corpus measurement you already trust and report its worst single
   item alongside the total. If they tell different stories, the total was
   hiding a bug.
3. Build a two-page fixture, one ordinary and one with a four-backtick fence
   containing three-backtick fences, and count both by hand. Every parsing bug
   in this project would have been caught by that one file.

**What makes it credible rather than decorative.** `docpack` is seven modules
and 134 tests operating on a documentation tree as data, and this guide's own
`src/fieldguide/fences.py` exists because three successive naive versions
returned plausible wrong answers; every figure above is reproducible from the
two repositories. What is not demonstrated is scale: the largest corpus here is
106 pages, and nothing on this page has been tested against the tens of
thousands where streaming, incremental parsing and caching would start to
matter.

## Related

- [Content and data transformation](content-data-transformation.md), the next job in NVIDIA's sentence
- [API integration](api-integration.md), the third one
- [Custom linters](custom-linters.md), where these habits get enforced
- [Code-sample validation](code-sample-validation.md), the fence parser's main consumer
- [Cognitive load in technical content](cognitive-load.md), where the aggregate-against-per-item lesson first appears
