---
title: Templates and scaffolding
summary: "Generating a page that already satisfies the contract, and the gate a helpful template quietly weakens."
diataxis: how-to
audience: developer
concept: templates-scaffolding
tags: [gp, core]
---

# Templates and scaffolding

`core` · difficulty 2 · 3h

!!! quote "Asked for by name"
    NVIDIA: "Encode standards (user stories, release readiness, onboarding, security guidance) into templates, validators, and guided workflows rather than static documents"

**Prerequisites:** [Content models](content-model.md)

**Leads to:** [Guided workflows](guided-workflows.md)

## What it is

A command that produces a new page already shaped correctly: the required
front matter present, the required sections in the required order, the
cross-references computed, and a prompt in each section saying what belongs
there.

The difference between a template and scaffolding is that a template is a file
you copy and scaffolding is a program that generates one. The program can fill
in what it knows, which on a corpus with a
[content model](content-model.md) is most of the metadata.

## Why the job asks for it

NVIDIA's bullet says templates **rather than static documents**, which is the
whole argument. A style guide tells an author what a page should contain, and
is read once. A scaffold hands them a page that already contains it, and is
used every time.

The deeper reason is that it makes the standard the path of least resistance,
which is NVIDIA's other phrase: build systems where the right way is easier
than the wrong way. An author who runs `fieldguide new` gets the contract for
free. An author who copies a neighbouring page gets whatever that page had.

The failure mode this page is really about is more interesting: a scaffold is
so helpful that it can accidentally satisfy the checks that were supposed to
hold the author to a standard.

## The golden path

Scaffold a page, check it against the validator, then find out what the
scaffold is doing to your own quality gate. About twenty-five minutes.

**Step 1: generate a page from the registry**

```bash
fieldguide new docs-analytics --dry-run
```

```
---
title: Documentation analytics
summary: 'TODO: one sentence on what documentation analytics is and why this role needs it.'
diataxis: explanation
audience: developer
concept: docs-analytics
tags: [meas, core]
---

# Documentation analytics

`core` · difficulty 2 · 4h

> Instrument documentation analytics and convert findings into improvements to
> docs, samples, and tooling

> Source: intel posting, verbatim

**Prerequisites:** [Documentation CI](documentation-ci.md)

**Leads to:** [Measuring AI answer quality](ai-answer-quality.md), [Search and
query log analysis](search-log-analysis.md), [Support deflection](support-deflection.md),
[Time to first success](time-to-first-success.md), ...
```

Four things were computed rather than typed: the tags from category and tier,
the posting quote verbatim from the registry, the prerequisites, and the
concepts that depend on this one. None of them can be wrong, because none of
them were transcribed.

**Step 2: the prompts, which are the interesting part**

```markdown
## What it is

<!-- Define it in two sentences, for someone who has heard the
term in a meeting and not admitted they do not know it. No history, no
motivation, no list of benefits.

The failure mode here is writing the Wikipedia opening: a definition so
careful it is useless. Prefer the sentence you would actually say out loud.
-->
```

Each section carries a prompt **and a named failure mode**. That is the part
worth copying. "Define it in two sentences" is a brief; "the failure mode is
the Wikipedia opening" is the thing that actually changes what gets written,
because it names the mistake the author is about to make.

**Step 3: check the scaffold against the validator**

A scaffold and a validator are separate programs with separate ideas of a
valid page. If they drift, your tooling tells contributors to run a command
whose output your own CI rejects. So test every one:

```python
for c in [x for x in reg.concepts if x.status == "planned"]:
    text = render_concept_page(reg, c.id)
    heads = _headings_outside_fences(text)
    missing = [s for s in REQUIRED_SECTIONS if s not in heads]
    order = [heads[s] for s in REQUIRED_SECTIONS if s in heads]
    assert not missing and order == sorted(order)
```

```
planned concepts: 27
scaffolded pages failing the section contract: 0
```

Twenty-seven for twenty-seven. This check belongs in CI, not in a one-off
script, because the two modules are edited independently.

**Step 4: now measure what the scaffold did to your word gate**

The contract says a page marked `complete` must be at least 450 words, which
exists to stop a stub wearing a label. Measure a fresh scaffold against it:

```
scaffold word count: min=372 max=402   (complete minimum is 450)
```

Comfortable, apparently: no scaffold can pass as complete. But count where
those words are:

```python
COMMENT = re.compile(r"<!--.*?-->", re.S)
total    = len(text.split())
stripped = len(COMMENT.sub(" ", text).split())
```

```
concept                     total  outside comments  in comments
sample-apps                   376                87          289
templates-scaffolding         385                96          289
docs-analytics                400               111          289
```

**289 of about 380 words are prompt text inside HTML comments**, and the gate
was counting them. So the arithmetic an author faced was:

```
real prose required to cross the 450-word gate: ~74 words
```

Seventy-four. A gate meant to require a substantial page was 84 per cent
pre-satisfied by the template's own instructions, so two paragraphs and a
status change would mark a page complete with most of its prompts unanswered.

Two good ideas, a helpful template and a word-count gate, combining into a
weak gate. Neither is wrong on its own.

**Step 5: fix the measurement, not the template**

```python
HTML_COMMENT = re.compile(r"<!--.*?-->", re.S)

def prose_words(text: str) -> int:
    """Count words a reader would see, excluding HTML comments."""
    return len(HTML_COMMENT.sub(" ", text).split())
```

```
scaffold raw words:   376
scaffold prose words: 87
real prose needed:    363 (was 74)
```

The threshold did not move. What the threshold *means* changed, from 74 words
of prose to 363.

**What you built.** A scaffold that computes what it can and names the failure
modes, a CI check that it agrees with the validator, and a word gate that
measures prose rather than instructions.

## Reference

### What a scaffold should compute rather than ask for

| Field | Source |
|---|---|
| Tags, category, tier | The registry entry |
| Title | The registry entry |
| Required sections | The page contract |
| Prerequisites and dependents | The [knowledge graph](knowledge-architecture.md) |
| A source quotation | The registry's `demanded_by` |
| Date fields | The clock |
| Summary, body | The author; these are the actual work |

Anything on the top half that an author types is something they can get wrong.
The bottom two rows are where human effort belongs, and a scaffold that
pre-fills them with plausible text is worse than one that leaves a `TODO`.

### What makes a prompt work

| Weak prompt | Better |
|---|---|
| "Describe the concept" | "Two sentences, for someone who heard it in a meeting" |
| "Add examples" | "The shortest exercise that produces a working result" |
| "Keep it concise" | "The failure mode is the Wikipedia opening" |
| "Explain the benefits" | Delete; nobody needs a benefits section |

Naming the failure mode is the highest-leverage sentence in a template,
because an author about to make a mistake rarely knows which mistake it is.

### Template, scaffold, generator

| | Is | Drifts because |
|---|---|---|
| Template | A file you copy | Nothing enforces that you copied the current one |
| Scaffold | A program producing a new file | It can disagree with the validator |
| [Generator](single-sourcing.md) | A program producing pages from data | Committed output can go stale |

Each step up removes a class of drift and adds a program to maintain. The
scaffold-versus-validator agreement from step 3 is the drift you take on by
moving from a template to a scaffold, and it is cheap to check.

### Mechanisms worth encoding this way

| Standard | Scaffolded as |
|---|---|
| Page contract | `fieldguide new <concept>` |
| [Content model](content-model.md) | Front matter pre-filled and validated |
| [Security guidance](security-documentation.md) | Approved patterns in the sample stub |
| [Release readiness](release-readiness.md) | A checklist issue template |
| [Playbooks](playbooks.md) | A node-and-outcome skeleton |
| Pull request expectations | A template asking the judgment questions |

### Keeping it honest

| Rule | Why |
|---|---|
| CI asserts the scaffold satisfies the validator | They are separate programs |
| Prompts live in comments, not placeholder prose | Placeholder prose gets published |
| Comments are excluded from word counts | See step 4 |
| `TODO` markers fail a `complete` status | Otherwise they ship |
| The scaffold is the documented way to start | A scaffold nobody runs is a template |

## How to talk about it

**Lead with least resistance.** "A template rather than a static document means
the standard arrives as a working file instead of as a page somebody read once.
The scaffold computes everything it can from the content model, so metadata
cannot be mistyped, and each section carries a prompt that names the failure
mode rather than restating the requirement."

**The follow-up is drift**, and the answer is that a scaffold and a validator
are two programs with two ideas of a valid page, so CI asserts that scaffolded
output passes validation. Twenty-seven for twenty-seven, checked on every
build rather than once.

**The tradeoff to volunteer.** A scaffold is code you own, and it has to be
version-aware: when the page contract changes, every page generated by the old
scaffold is now non-conforming and nothing tells you which ones. A template has
the same problem and no way to detect it, which is the argument for the
scaffold, but neither solves it.

**One sharper point, and the best thing here.** A helpful template can quietly
weaken your quality gates. Mine put 289 of roughly 380 words into prompt
comments, and because the word-count gate counted raw words, an author needed
only 74 words of real prose to mark a page complete. The fix was to count
prose rather than instructions, which left the threshold unchanged and changed
what it meant from 74 words to 363. The lesson generalises: when you add a
generator, re-derive every metric that counts the generated artifact.

## How to prove it

**The artifact.** A `new` command in a repository of yours, a CI step asserting
its output passes your validator, and a word count that excludes the template's
own text.

**Three things to do, in order:**

1. Run the golden path. Step 4 is the one worth doing on your own tooling.
2. Check whether your scaffold's output passes your own validator. If nobody
   has checked, assume it does not.
3. Add a named failure mode to the three prompts in your template that produce
   the worst writing. It is the cheapest editorial intervention available.

**What makes it credible rather than decorative.** `docpack` has
`docpack new <type> --title`, which serialises front matter with
`yaml.safe_dump` after an f-string version broke on its own default
placeholder, and this guide's `fieldguide new` is checked against the
validator in CI for every planned concept. The story to tell is step 4: the
scaffold was quietly supplying 84 per cent of a gate meant to hold authors to
a standard, and nothing was wrong with either piece on its own.

## Related

- [Guided workflows](guided-workflows.md), the next step up from a scaffold
- [Content models](content-model.md), what the scaffold reads
- [Single-sourcing and content reuse](single-sourcing.md), generation at the page level
- [Security guidance as encoded standard](security-documentation.md), the same move for security
