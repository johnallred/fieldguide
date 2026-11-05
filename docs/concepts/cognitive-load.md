---
title: Cognitive load in technical content
summary: "The mean sentence length is fine on almost every corpus; the per-page maximum and the unprepared cross-reference are what actually cost the reader."
diataxis: explanation
audience: developer
concept: cognitive-load
tags: [edu, core]
---

# Cognitive load in technical content

`core` · difficulty 2 · 3h

!!! quote "Adjacent, not quoted"
    Neither posting names it. It is the mechanism behind every claim about reaching first success in minutes.

**Prerequisites:** [Instructional design for developers](instructional-design.md)

## What it is

The working-memory cost of following a page. The useful split is into three parts. The **intrinsic** difficulty of the
subject, which you cannot reduce without teaching something easier. The
**extraneous** cost added by the presentation, which is the only part a writer
controls. And the **germane** effort the reader spends actually building a
model, which is the part you want them to have capacity left for.

Nearly every documentation complaint that gets reported as "too complicated"
is extraneous load, and nearly every attempt to fix it by adding explanation
makes it worse.

## Why the job asks for it

Because "a developer reaches a working result in fifteen minutes" is a claim
about working memory, not about word count.

A reader following a quickstart is holding several things at once: what they
are trying to achieve, where they are in the sequence, what the last command
printed, which of three similar-looking names they are supposed to use, and
whether the thing that just appeared on screen is a problem. Every item the
page adds to that stack is taken from the capacity they need for the actual
subject. Exceed it and they do not report confusion, they close the tab, which
is why this shows up in [time to first success](time-to-first-success.md) as a
drop-off rather than as feedback.

## The golden path

Measure load on a real corpus, discover that the summary statistic is useless,
and find a worse problem the summary statistic hides. About thirty minutes.

**Step 1: the obvious measurement**

```python
sents = []
for c in complete:
    prose = prose_of((docs / c.page).read_text())
    sents += [len(s.split()) for s in SENT.split(prose) if len(s.split()) >= 3]
```

```
sentences: 4847   mean 19.6 words
longest sentence per page: mean 50   max 103 (tutorial-design)
```

(Steps 1 and 2 were run when the corpus was 82 pages. They are kept as the
pair that exposed the bug; every figure from step 3 onward is the finished
106-page corpus.)

A 103-word sentence would be remarkable. Look at it:

```
103 | The architectural ordering, eight steps, output only at the end:
      mkdir sync && cd sync python3 -m venv .venv && source .venv/bin/activate
      pip install widget click mkdir src tests cat > src/config.py <<'EOF' ...
```

That is a shell session. The prose extractor had re-implemented fence
detection as a toggle, and the page opens a four-backtick fence containing
heredocs, so the toggle closed early and treated the commands as a sentence.

The repository already contained a correct fence parser, written precisely
because this problem is harder than it looks. The audit did not use it.

**Step 2: the same measurement, using the parser that already existed**

```python
from fieldguide.fences import fence_spans, heredoc_body_lines
lines = text.splitlines()
skip  = heredoc_body_lines(lines)
incode = {n for sp in fence_spans(lines, skip=skip)
            for n in range(sp.open_line, sp.close_line + 1)}
```

```
sentences: 5341   mean 16.7 words   median 15
longest sentence per page: mean 46   max 66 (reading-code-to-verify)
```

Every figure moved, and the sentence count went **up** by 494, because the
broken version had been swallowing real prose into pseudo-sentences as well as
inventing them. An audit that re-implements a solved problem inherits exactly
the bug the solution exists for.

**Step 3: the summary statistic is fine and it is useless**

The original run, when the corpus held 7,178 sentences rather than today's
8,541:

```
mean 17.1 words, median 15
sentences over 45 words: 95 of 7178 (1.3%)
```

By any style guide that is a healthy corpus. Now count pages rather than
sentences:

```
pages whose longest sentence exceeds 35 words: 100/106
pages whose longest sentence exceeds 45 words:  59/106
pages whose longest sentence exceeds 60 words:   6/106
```

**One and a third per cent of the sentences, and more than half the pages.**
Those two rows describe the same data, and only the second one describes the
reader's experience, because a reader does not meet a corpus average. They meet
one page, and on 59 of 106 pages they meet a sentence they have to read twice.

The actionable metric is the per-page maximum. A mean is a measurement of the
corpus; a maximum is a measurement of the worst moment a reader has, and load
failures are worst-moment failures.

**Step 3a: part of that number was the splitter**

Acting on the figures above turned up a defect in the thing that produced them,
which by now is the expected order of events in this corpus.

The sentence boundary was a terminator followed by an optional closing quote or
bracket, then whitespace. This corpus ends dozens of sentences in **bold**, so
`.**` was not a boundary and every bolded sentence was silently joined to the
one after it. Three of the six "sentences over 60 words" were two sentences
with a `.**` between them, and the over-45 sentence count fell from 111 to 56
the moment the class was widened to include markup.

```
                                  before   after the fix   after editing
sentences over 45 words              111             56              33
pages whose longest exceeds 45        59             43              27
pages whose longest exceeds 60         6              5               0
longest sentence in the corpus        71             71              50
```

The 111 in that first column and the 95 above it are the same measurement at
two different times: the corpus kept growing between them. The page counts are
the stable comparison, which is the argument for the per-page maximum made
twice over.

The editing pass is real work and it moved the middle column to the right one.
The splitter fix moved the left column to the middle without touching a word of
prose. Both are in the table because publishing only the second would make the
editing look twice as effective as it was.

**Step 3b: the metric has a hole, and measuring it closed it**

A list item is not a sentence, so the prose measurement excludes list items.
That exclusion is also a loophole: a 70-word sentence becomes compliant the
moment somebody puts a hyphen in front of it, and the reader is no better off
unless the content was genuinely a list.

Four of the five worst sentences here *were* genuinely lists, and converting
them to bullets is the right edit for a reader. It is also an edit that removes
them from the metric rather than improving them, and those two facts are
independent. So `fieldguide audit` now reports the longest sentence *inside*
list items alongside the prose figure:

```
    in list items: longest mean 21, max 34
                   45+ on   0/106 pages
```

No list item in this corpus hides a long sentence, which is worth knowing
rather than assuming. The first version of that measurement counted each
item's total words and reported an 81-word item, which was four short sentences
in a proof task and not a readability problem at all. Sentences inside items
are the comparable unit; item length is not.

**Step 4: the cost nobody measures**

Sentence length is the cheap half. Count what a page asks the reader to hold
by way of cross-references:

```
distinct concepts linked per page: mean 6.3   max 15 (systems-mindset)   min 4
```

Then ask whether those links point at anything the reader has been prepared
for. For each [learning path](learning-paths.md), classify every link on its
pages as backward (already read), forward (later in this path), or off-path:

```
  first-week           backward   9  forward  14  off-path  52
  content-architect    backward  15  forward  18  off-path  45
  docs-engineer        backward  34  forward  35  off-path  39
  knowledgeops         backward  44  forward  38  off-path  49
  developer-educator   backward  22  forward  27  off-path  32
  writer-who-builds    backward   4  forward   8  off-path  60
  prove-it             backward  22  forward  20  off-path  55
  prove-the-outcomes   backward  15  forward  15  off-path  32
  domain-context       backward   9  forward   7  off-path   8
```

```
backward 174   forward 182   off-path 372
links pointing at material the reader has not read: 76%
```

Nine paths, where this measurement first ran over seven. Two paths were added
after it, and the per-path rows moved as well as the totals, because pages
gained cross-references. The 76 per cent did not move at all, which is the
useful thing about a ratio: it is the shape of the corpus rather than its size,
and it is why that figure is the one quoted elsewhere.

On `first-week`, a reader meets 75 concept links and **nine** of them point at
something they have already read. The other 66 are an invitation to leave, each
one carrying a small decision: is this a prerequisite I am missing, or an
aside?

That decision is pure extraneous load, and it is invisible to every readability
measure. The corpus reads well sentence by sentence and asks its readers to
make sixty-six unnecessary judgments per path.

**Step 5: what to do about each half**

The sentence half is a straightforward editing job against a per-page maximum.
The six pages over 60 words took an afternoon, and there are now none.

The link half is not fixed by linking less. A guide whose pages do not
cross-reference is a worse guide. It is fixed by making the *kind* of link visible, so the reader's decision is
made for them. A prerequisites line is a link you must follow. A "related"
list at the foot is a link you may ignore. An inline link is neither, which is
why the inline ones generate the load.
This corpus has the first and the last and uses inline links for both jobs,
which is the finding.

**What you built.** A load measurement that uses the corpus's own fence parser,
a per-page maximum that replaced a useless mean, and a cross-reference census
showing 78 per cent of links point at unread material.

## Reference

### The three loads, and what moves each one

| Load | Source | Lever |
|---|---|---|
| Intrinsic | The subject's real difficulty | Teach a smaller subject first |
| Extraneous | Presentation | Everything on this page |
| Germane | Model-building | Protect capacity for it |

The common mistake is attacking intrinsic load by adding explanation, which
raises extraneous load and leaves less room for germane effort. The reader
reports the same confusion about a longer page.

### Extraneous load, by source

| Source | Shows up as | Measured by |
|---|---|---|
| Long sentences | Re-reading | Per-page maximum, not the mean |
| Unprepared cross-references | A decision per link | The backward/forward/off-path census |
| Split attention | Scrolling between code and its explanation | Code and prose adjacency |
| Near-identical names | Using the wrong one | A terminology inventory |
| Unstated prerequisites | Failure three steps later | [Cold-start testing](coldstart-testing.md) |
| Options presented before a default | Paralysis at step 1 | Counting choices before first success |
| Output not shown | Uncertainty whether it worked | Expected output per command |

The last two rows are the highest-yield fixes in most quickstarts and neither
is a writing problem.

### Why the mean misleads

| Statistic | Describes | Useful for |
|---|---|---|
| Mean sentence length | The corpus | Reporting |
| Median | The corpus | Reporting |
| Per-page maximum | The reader's worst moment | Editing |
| Count of pages over a threshold | The size of the job | Planning |
| Percentage of sentences over it | Nothing a reader experiences | Reassuring yourself |

Load failures are worst-moment failures, so every statistic worth acting on is
a maximum or a count of pages, never a central tendency.

### Chunking, and its limit

Breaking a long procedure into named steps genuinely reduces load, because the
reader can discard the contents of a completed step and keep only its name.
That is why golden paths in this guide are numbered and named.

The limit is that chunking only helps when the chunks are independent. Steps
that require holding state from three steps back are not chunked, they are
merely numbered, and the numbering disguises the problem by making the page
look organised.

### What load is not an argument for

| Not | Because |
|---|---|
| Shorter documentation | A page can be long and low-load |
| Removing detail | Detail the reader needs is intrinsic |
| Simplified vocabulary | The real terms are what they will search for |
| Fewer links | The fix is marking their kind, not deleting them |
| One page per idea | Fragmentation adds navigation load |

## How to talk about it

**Lead with the three-way split, briefly.** "Intrinsic load is the subject,
extraneous load is the presentation, germane load is the reader actually
building a model. Only the middle one is mine, and most attempts to reduce the
first by adding explanation increase the second. 'Fifteen minutes to a working
result' is a claim about working memory, not about word count."

**The follow-up is how you measure it, and this is where to bring the
numbers.** Mean sentence length on my corpus is 15.6 words, which is healthy
and useless. A reader never meets an average, so the metric I act on is the
per-page maximum: 59 of 106 pages carried a sentence over 45 words and six
carried one over 60. After an editing pass, 27 pages and none. The honest part
of that story is that fixing the sentence splitter accounted for as much of the
improvement as the editing did, because it had never treated a sentence ending
in bold as a sentence ending.

**The stronger half, if there is time for one more thing.** I classified every
cross-reference by whether the reader had reached it yet, and 76 per cent of
links point at material they have not read. On the shortest path, nine links
of 75 point backwards. Each of the other 66 is a decision about whether
something is a missing prerequisite or an aside, which is invisible to every
readability score. The fix is not fewer links, it is making the kind of link
visible, because a prerequisites line and a "related" footer make the decision
for the reader and an inline link does not.

**The tradeoff to volunteer.** Load is a model, not a measurement, and the
numbers above are proxies for something nobody can observe directly. A page
with a 60-word sentence may be perfectly clear and a page of short sentences
may be unreadable. The measurements earn their place by finding candidates
quickly, and the reading still has to happen; treating any of them as a gate
produces staccato prose that scores well.

**One sharper point.** My own load audit was wrong, and wrong in the way this
whole area is wrong: it re-implemented fence detection as a toggle, so a page
with four-backtick fences and heredocs leaked a shell session into the prose
and reported a 103-word sentence. The repository already contained a correct
fence parser. The corrected run moved every figure and found 494 *more*
sentences, because the broken version had been merging real prose too. An audit
that re-implements a solved problem inherits the exact bug the solution exists
for.

## How to prove it

**The artifact.** A per-page maximum sentence length and a cross-reference
census over a corpus you own, both computed with that corpus's own parser.

**Three things to do, in order:**

1. Measure the per-page maximum sentence length on your docs, then read the
   three worst sentences out loud. The measurement takes five minutes and the
   reading is what convinces anybody.
2. Take your shortest learning path and classify every link on its pages as
   backward, forward or off-path. The ratio will be worse than you expect.
3. Open your quickstart and count the choices it presents before the reader's
   first success. Each one is extraneous load at the worst possible moment.

**What makes it credible rather than decorative.** Every figure in steps 2
through 4 comes from `fieldguide audit`, a committed subcommand rather than a
script that was thrown away, so a reader can run it and get these numbers.
`fences.py` is the parser it uses, and it exists because the naive version was
wrong three times; `tests/test_audit.py` holds a fixture for each of those
three failures, including the nested fence that leaked a shell session into the
prose.

What the guide does *not* have is any evidence that lowering these numbers
improved comprehension for a real reader, which would need
[assessment](assessment.md) and a population. The
[demonstrated](../demonstrated.md) page records this as `partial` on exactly
that split: the instrument is demonstrated, the effect is not.

## Related

- [Instructional design for developers](instructional-design.md), the commitments this serves
- [Learning paths and curriculum](learning-paths.md), where the cross-reference census comes from
- [Tutorial design](tutorial-design.md), chunking and sequencing at page level
- [Time to first success](time-to-first-success.md), where exceeded load shows up as a number
- [Cold-start testing](coldstart-testing.md), the unstated-prerequisite half
