---
title: Diátaxis
summary: Four kinds of documentation that serve different needs and must not be mixed on one page.
diataxis: explanation
audience: developer
concept: diataxis
tags: [ia, core]
---

# Diátaxis

`core` · difficulty 1 · 2h

!!! note "Not a quotation (adjacent)"
    The dominant framework for documentation structure. Neither posting names it; both describe the problem it solves.

**Prerequisites:** [Information architecture](information-architecture.md)

**Leads to:** [Designing tutorials](tutorial-design.md), [Golden paths](golden-paths.md), [Learning paths and curriculum](learning-paths.md)

## What it is

A claim that documentation serves four separate needs, and that a page trying
to serve more than one serves none of them well. The four are **tutorials**
(learning by doing), **how-to guides** (achieving a goal), **reference**
(finding a fact), and **explanation** (understanding why).

It is attributed to Daniele Procida and has been adopted as the organising
framework by Canonical, Django, Gatsby, Cloudflare and a long list of others.
It is the closest thing this field has to a standard.

## Why the job asks for it

Neither posting says "Diátaxis", which is why this concept is tagged
`adjacent`. Both describe the problem it solves, repeatedly. Intel asks for
golden paths, curriculum, tutorials, sample walkthroughs and reference
documentation as *separate deliverables*, which is a Diátaxis decomposition
written out without the name. NVIDIA asks for content modeling and for content
structured for machine retrieval, and the type of a page is the single most
useful field in that model.

The reason it earns `core` status despite being unquoted is that it answers the
first question anyone asks when they open an unfamiliar corpus: **what is a
page?** Without an answer, every page drifts toward being the same page: a bit
of motivation, some steps, a table of options, and a paragraph about design
philosophy. That page is comfortable to write and bad to read, because the
reader arrived with exactly one of those four needs and has to filter out three
quarters of what is in front of them.

On a Tuesday this shows up as a specific recurring decision. An engineer gives
you a page that says "Getting started with the inference server" and it contains
an installation sequence, a conceptual overview of the serving architecture, a
full table of configuration flags, and three worked examples. Diátaxis is how
you explain, without it sounding like an aesthetic preference, that this is four
pages, and which four.

The retrieval argument is the newer and stronger one. A page with four jobs
produces chunks with four jobs, and a retriever that returns the
architecture-overview paragraph to someone who asked "how do I set the batch
size" has failed in a way no ranking improvement will fix. **Type separation is
retrieval hygiene**, not just navigation hygiene.

## The golden path

Take one page that does four jobs and split it, then feel the difference. Thirty
minutes, no tooling.

**Step 1: write the page everybody writes**

```bash
mkdir -p diataxis-demo && cd diataxis-demo
cat > before.md <<'EOF'
# Getting started with the widget queue

The widget queue exists because synchronous processing could not keep up with
burst traffic during launches. We chose an at-least-once delivery model rather
than exactly-once because exactly-once requires distributed transactions, and
the cost of a duplicate widget is lower than the cost of a dropped one.

## Installation

Run `pip install widget-queue`. You need Python 3.10 or newer and a running
Redis instance.

## Configuration options

| Flag | Default | Description |
|---|---|---|
| `--workers` | 4 | Number of worker processes |
| `--batch-size` | 100 | Items pulled per poll |
| `--visibility-timeout` | 30s | How long a claimed item stays hidden |

## Your first queue

Create a queue, push an item, and consume it. By the end you will have seen a
widget travel end to end.

## Draining a queue before a deploy

Call `widget-queue drain --wait`. This stops new claims and waits for in-flight
items. Always do this before a deploy that changes the item schema.
EOF
wc -l before.md
```

That page is not badly written. It is five pages.

**Step 2: sort the content by the reader's state**

The test is not "what is this paragraph about". It is two questions about the
person reading it:

```bash
cat > sorting-test.md <<'EOF'
                 |  Studying            |  Working
-----------------|----------------------|------------------------
Practical steps  |  TUTORIAL            |  HOW-TO GUIDE
Theory, facts    |  EXPLANATION         |  REFERENCE
EOF
cat sorting-test.md
```

Apply it to each section above:

| Section in `before.md` | Studying or working? | Steps or facts? | Type |
|---|---|---|---|
| Why at-least-once | Studying | Theory | Explanation |
| Installation | Working | Steps | How-to |
| Configuration options | Working | Facts | Reference |
| Your first queue | Studying | Steps | Tutorial |
| Draining before a deploy | Working | Steps | How-to |

**Step 3: split it**

````bash
mkdir -p tutorials how-to reference explanation

cat > explanation/delivery-guarantees.md <<'EOF'
# Why the queue is at-least-once

Exactly-once delivery requires distributed transactions across the queue and
the consumer's datastore. At-least-once requires only that consumers be
idempotent.

## What this costs you

Every consumer must tolerate seeing the same item twice. That is real work
pushed onto every team that uses the queue, and it is the honest price of the
decision.
EOF

cat > how-to/install.md <<'EOF'
# Install the widget queue

```bash
pip install widget-queue
```

Requires Python 3.10 or newer and a reachable Redis instance.
EOF

cat > reference/configuration.md <<'EOF'
# Configuration reference

| Flag | Default | Description |
|---|---|---|
| `--workers` | 4 | Number of worker processes |
| `--batch-size` | 100 | Items pulled per poll |
| `--visibility-timeout` | 30s | How long a claimed item stays hidden |
EOF

cat > tutorials/first-queue.md <<'EOF'
# Your first queue

By the end of this you will have pushed a widget through a queue and seen a
consumer handle it. About ten minutes.
EOF

cat > how-to/drain-before-deploy.md <<'EOF'
# Drain a queue before a deploy

```bash
widget-queue drain --wait
```

Do this before any deploy that changes the item schema.

## If it hangs

A consumer holding an item past its visibility timeout blocks the drain. Find
it with `widget-queue inspect --claimed`.
EOF

find . -name "*.md" -not -name before.md -not -name sorting-test.md | sort
````

**Step 4: see what the split bought you**

```bash
echo "--- A reader mid-deploy, who needs one command ---"
cat how-to/drain-before-deploy.md
echo
echo "--- The same question against the original ---"
grep -n -A3 "Draining" before.md
```

The how-to guide is the whole answer and nothing else. In `before.md` the same
answer is four paragraphs down a page that opens with distributed-transaction
theory. **The content is identical; only the boundaries changed.**

One more thing the split bought, which is easy to miss: writing
`explanation/delivery-guarantees.md` as its own page made it obvious that it was
missing a "what this costs you" section. A page whose only job is to explain a
decision invites the question "and what is the downside", and a page where that
argument is buried under an installation command does not.

**What you built.** One mixed page split into four, and the evidence for why:
each piece became checkable in a way the combined page was not, and one of
them revealed a section that had been missing all along.

## Reference

### The four types

| Type | Reader's state | Answers | Must not contain |
|---|---|---|---|
| **Tutorial** | Learning, no context | "Can I get something working?" | Options, alternatives, edge cases |
| **How-to guide** | Working, competent | "How do I achieve X?" | Teaching, motivation, background |
| **Reference** | Working, needs a fact | "What are the parameters?" | Narrative, opinion, tasks |
| **Explanation** | Studying, wants to understand | "Why is it like this?" | Instructions |

### The distinguishing tests

| Question | Tutorial | How-to | Reference | Explanation |
|---|---|---|---|---|
| Who chooses the goal? | Author | Reader | Neither | Neither |
| Can the reader fail? | No, never | Yes | n/a | n/a |
| Are alternatives offered? | Never | Sometimes | Exhaustively | Discussed |
| Is it read start to finish? | Yes | No | No | Yes |
| Structure mirrors | A lesson | A task | The code | An argument |

The "who chooses the goal" row is the sharpest tool here. **A tutorial's goal
belongs to the author**; the reader does not know enough to have a goal yet, and
offering them a choice is the commonest way tutorials fail. A how-to guide's
goal belongs to the reader, who arrived with it already.

### Common failures and their fix

| Symptom | Diagnosis | Fix |
|---|---|---|
| Tutorial offers three ways to install | Reference leaking into tutorial | One way; link the rest |
| How-to guide opens with two paragraphs of context | Explanation leaking into how-to | Move it; link it |
| Reference page has a worked example with narration | Tutorial leaking into reference | Keep the example, drop the narration |
| Explanation page lists every flag | Reference leaking into explanation | Link the reference |
| A page called "Overview" | Usually all four | Split, then decide if the overview is needed at all |
| A `guides/` folder | Tutorials and how-tos conflated | The most common corpus-level error |

### What Diátaxis does not cover

Worth knowing, because being asked is likely:

- **Release notes and changelogs.** Chronological, not topical. Outside the model.
- **Troubleshooting pages.** Usually a how-to guide indexed by symptom rather than goal, which the model handles awkwardly.
- **API reference generated from source.** Reference, but the type is determined by the generator rather than a choice.
- **Landing and orientation pages.** Navigation, not content.

## How to talk about it

**What a competent answer sounds like.** Name the four, then immediately give
the discriminating test rather than definitions, because the definitions are
googleable and the test is what you use. "The useful question is what state the
reader is in: studying or working, and do they want steps or facts. That gives
you the four quadrants, and it tells you which of two plausible-looking pages a
piece of content belongs on."

**The follow-up you will get is "isn't this just rigid?"** or some version of
an objection to the purity of it. Do not defend the framework as doctrine. The
honest answer is that the value is almost entirely in the *separation of
tutorial from how-to* and *reference from explanation*, because those are the
two pairs people conflate by default. Whether a particular page is a how-to
guide or a tutorial matters much less than whether anyone asked the question.

**The tradeoffs to volunteer, and there are three real ones:**

**It multiplies page count.** One page becomes four, navigation gets wider,
and a reader who wanted the old all-in-one page now follows links. For a small
product that is a net loss, and Diátaxis applied to a corpus of fifteen pages is
overhead with no payoff.

**It fragments the thing a reader is holding.** Some readers genuinely do want
installation, concept, and example in one scroll, and the framework's answer,
which is "link them clearly", is weaker than its proponents admit. A good
landing page partly compensates. Partly.

**The boundaries are genuinely ambiguous in practice.** Troubleshooting is the
clearest case: it is tasks indexed by symptom instead of by goal, which the
model has no slot for. Anyone who tells you the four types partition all
documentation cleanly has not migrated a large corpus.

**One sharper point.** The strongest modern argument for Diátaxis is not
navigational at all, and it is the one most candidates miss: type separation is
what makes retrieval filterable. If every page declares one of four types, a
retrieval system can be told to return only how-to content for a "how do I"
question, which is a hard constraint rather than a hope that the embedding
noticed the genre. Diátaxis was proposed years before anyone was packaging docs
for language models, and it turned out to be the most useful metadata field in
the corpus. That is worth saying out loud.

## How to prove it

**The artifact.** A corpus organised by type, where the type is a declared
field and not only a folder name, and something that uses the field.

**Three things to do, in order:**

1. **Run the golden path.** Keep both files. `before.md` next to the split
   tree is a two-minute demonstration in an interview, and showing the before
   is what makes the after land.
2. **Audit a real corpus by type.** Take a project's documentation, classify
   thirty pages into the four types, and count how many are more than one.
   The number is usually between a third and a half, and reporting it with the
   examples is a genuinely useful piece of analysis. Do it on your own project's
   docs first; doing it on an employer's corpus is a strong interview artifact
   but check whether you can share it.
3. **Make the type do work.** Add it as a required field, validate it in
   [documentation CI](documentation-ci.md), and then use it for something: a
   faceted navigation, a filter in your [retrieval](rag.md) layer, or grouping
   in [llms.txt](llms-txt.md). A type field nothing reads is a convention; a
   type field that filters a search is architecture.

**What makes it credible rather than decorative.** Everyone in this field can name the four types.
The signal is the migration: having taken a real page apart, and being able to
say which boundary was genuinely ambiguous and how you decided. Interviewers in
this category have all fought with the troubleshooting question. Having an
opinion about it marks you as someone who has done the work.

## Related

- [Information architecture](information-architecture.md), the layer this sits inside
- [Content models](content-model.md), how to make the type a validated field
- [Designing tutorials](tutorial-design.md), the hardest of the four to write well
- [Golden paths](golden-paths.md), what Intel calls the tutorial done properly
