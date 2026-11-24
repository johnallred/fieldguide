---
title: Technical writing as a craft
summary: Writing that a competent stranger can act on without asking you a question.
diataxis: explanation
audience: developer
concept: technical-writing
tags: [craft, core]
---

# Technical writing as a craft

`core` · difficulty 2 · 8h

> Writing developer documentation a reader can act on without asking you a question.

**Leads to:** [Release notes and changelogs](release-notes.md)

## What it is

Writing that a competent stranger can act on without asking you a question. The
test is behavioural rather than aesthetic: not whether the prose reads well, but
whether the reader does the right thing next.

It is a craft in the specific sense that it improves with deliberate practice on
feedback, and that people who are good at it can say *why* a sentence is wrong.

## How this applies to your role

Everything else in this guide rests on it. Strong technical writing goes hand
in hand with information architecture, and the people who do this work best
are usually writers who build: technical writers and developer-documentation
specialists who also own the tooling.

This guide's first version covered pipelines, retrieval, taxonomy and validators
and had no page for writing well. That was its worst gap, and the reason it was
easy to fall into is worth naming: **everything else in this field is more
legible.** A chunker either works or does not. A link checker either fails the
build or does not. Prose quality has no test suite, so it quietly becomes the
thing nobody budgets for while everyone agrees it matters.

On a Tuesday this is less glamorous than it sounds. An engineer hands
you four paragraphs about a new flag. The paragraphs are accurate. They also
open with implementation history, use three names for the same thing, bury the
one command a reader needs in the middle of the third sentence, and never say
what happens if you get it wrong. Turning that into a page someone can act on,
in twenty minutes, without losing anything true, is the job. You will do it
several times a day.

The second reason it is `core`: when you are the one building the validators, your
own writing is the reference implementation. A style rule you cannot follow is a
style rule the team will litigate.

## The golden path

No installation, which makes this the one golden path in the guide that is pure
practice. About thirty minutes, and it still ends in a measurement.

**Step 1: get a page that is accurate and unusable**

```bash
mkdir -p writing-drill && cd writing-drill
cat > before.md <<'EOF'
# Configuring Retry Behaviour

Historically the widget client did not retry at all, which caused problems
during the 2024 migration when the upstream service was being restarted
frequently. We subsequently added retry logic, and after some discussion
about whether the backoff should be linear or exponential, exponential was
chosen. The retry configuration is controlled through the client
configuration object, which also controls other things like timeouts, and
users should be aware that the retry count does not include the initial
attempt, so a retry count of 3 means 4 total requests will be made. It is
generally recommended that you do not set the retry count very high because
this can cause the client to block for a long time, and in some cases it may
be better to fail fast and let the caller decide. The maximum is 10.
EOF
wc -w before.md
```

Nothing in that paragraph is false. A reader who needs to set a retry count has
to read 140 words and do arithmetic.

**Step 2: four passes, in this order**

Order matters: reorganizing sentences you are about to delete is wasted work.

```bash
cat > passes.md <<'EOF'
1. CUT      Remove what the reader does not need in order to act. History,
            decision records and hedging all go. Target: half the words.
2. ANSWER   Put the thing they came for in the first sentence.
3. NAME     One term per concept, every time. No synonyms for variety.
4. FAIL     Say what goes wrong, and what to do about it.
EOF
cat passes.md
```

**Step 3: do the passes**

```bash
cat > after.md <<'EOF'
# Configure retry behaviour

Set `retries` on the client. The default is 3.

    client = WidgetClient(retries=3)

`retries` counts retries, not attempts: `retries=3` makes up to 4 requests.
The maximum is 10.

## Choosing a value

| Situation | Value |
|---|---|
| A caller is waiting on the response | 1 to 2 |
| Background job that can afford to wait | 3 to 5 |
| Upstream is known to restart often | up to 10 |

Retries use exponential backoff, so a high count blocks for a long time. If the
caller handles failure better than the client can wait, prefer failing fast
over raising this.

## Why exponential backoff

See the retry design note.
EOF
echo "before: $(wc -w < before.md) words"
echo "after:  $(wc -w < after.md) words"
```

**Step 4: measure the thing that matters**

Word count is a proxy. The real test is how far a reader travels before they can
act.

```bash
python3 - <<'PY'
import pathlib

# where each page first states the retry default the reader came for
ANSWER = {"before.md": "retry count of 3", "after.md": "The default is 3"}

def words_before_the_answer(path):
    text = pathlib.Path(path).read_text()
    index = text.find(ANSWER[path])
    assert index >= 0, f"{path}: answer not found"
    return len(text[:index].split())

for name in ANSWER:
    print(f"{name:<12} {words_before_the_answer(name):>3} words before the answer")
PY
```

```
before.md     83 words before the answer
after.md       9 words before the answer
```

**What you built.** The same facts and the default the original never stated,
with the reader reaching the answer in a
fraction of the distance, plus two things the original lacked entirely: a table
for choosing a value, and a statement of what goes wrong.

Note that the rewrite is not merely shorter. The history moved to an explanation
page rather than being destroyed, which is [Diátaxis](diataxis.md) doing the
work. Keep both files: a before-and-after is the most useful thing to share with whoever wrote the original.

## Reference

### The four passes

| Pass | Question | Typical cut |
|---|---|---|
| **Cut** | Does the reader need this to act? | Implementation history, decision narrative, hedging, apologies |
| **Answer** | Is the thing they came for first? | Move the command or the value to sentence one |
| **Name** | One term per concept? | Synonyms introduced for variety |
| **Fail** | What goes wrong, and then what? | Usually missing entirely |

### Sentence-level habits that carry most of the weight

| Habit | Instead of | Write |
|---|---|---|
| Active voice for instructions | "The flag should be set" | "Set the flag" |
| Second person | "Users can configure" | "Configure" |
| Present tense | "The client will retry" | "The client retries" |
| Condition first | "Run `drain` if deploying a schema change" | "Before a schema change, run `drain`" |
| Say the number | "A reasonably high value" | "Up to 10" |
| One idea per sentence | Three clauses and a however | Three sentences |

Condition-first is the least obvious and the most valuable. A reader scanning
for their situation needs to know whether a sentence applies to them *before*
they read it.

### Words that signal a problem

| Word | What it usually hides |
|---|---|
| "simply", "just", "easy" | A step the author stopped seeing |
| "should" | Nobody checked whether it does |
| "note that", "it is important to" | Something belonging earlier, or in a callout |
| "etc.", "and so on" | The author did not finish the list |
| "robust", "seamless", "powerful" | Nothing. Delete |
| "obviously", "of course" | The reader is about to feel stupid |

These are exactly what a [Vale rule](prose-linting.md) catches, which is the
link between this page and the automation half of the job.

### What technical writing is not

| Not | Difference |
|---|---|
| Good prose | Literary quality is irrelevant; actionability is not |
| Brevity | A reference page should be exhaustive. Short is a means |
| Simplification | Never make it less true to make it shorter |
| Explaining everything | An explanation inside a how-to guide is a defect |

## Explaining it to your team

**How to explain it.** Do not call your writing clear and
concise; everyone does. Describe a specific edit and its cost. "The page
documented a flag accurately in 140 words of history. I moved the history to an
explanation page, put the default in the first sentence, added a table for
choosing a value and a line on what happens if you set it too high. The reader
reaches the answer in one sentence instead of five, and nothing true was lost."

**The follow-up is usually "how do you get engineers to write documentation".**
The honest answer is that mostly you do not, and designing around that is
the skill. You take their accurate, badly organized paragraph as a *source*
rather than a draft, and you ask them to review for accuracy rather than for
style. An engineer will happily confirm a number is right. They will not
happily restructure a page.

**The tradeoff to name.** Editing someone else's writing hard enough to
make it usable costs political capital every time, and the cost is highest with
the people whose expertise you most need. There is a real version of this job
where you keep every contributor happy and the documentation stays bad. The
mitigation is to move standards into [linters](prose-linting.md) and
[templates](templates-scaffolding.md), so the rule is impersonal and the
argument happens once against the rule rather than weekly against a person.
That is [the systems mindset](systems-mindset.md) applied to a social problem.

**One sharper point.** The hardest part of technical writing is not sentences, it
is **knowing what the reader does not know**, and it is hard because writing a
page destroys your ability to judge it. Once you understand the system, the gap
you left is invisible to you. Nothing fixes that from the inside, which is the
real argument for [cold-start testing](coldstart-testing.md) and for watching
someone new follow your page without helping them. Saying that connects the
craft to the automation, which is what this whole field is about.

## Putting it into practice

**The work product.** A before-and-after, with the reasoning. Not just a finished
page: a page shows the writing, and an edit shows the diagnosis, which is the
part a team can learn from.

**Three things to do, in order:**

1. **Run the golden path on a real page.** Find a genuinely bad page in a
   project you know, rewrite it with the four passes, and write three sentences
   on what each pass removed. Twenty minutes, and the most useful habit on this
   page.
2. **Encode one of your own rules as a linter.** Take a habit you care about,
   hedge words or synonym drift, and write the [Vale rule](prose-linting.md). A
   writer who ships their style guide as code has made the standard impersonal,
   which is what makes it stick.
3. **Watch someone follow one of your pages without helping them.** Note where
   they stop, then fix the page rather than explaining it. That note teaches
   you more about your judgment than any finished page. Predict where they
   will stop before you watch. Being wrong about that is the point of doing it
   with a person rather than from the page.

**How to tell it is working.** Readers act on the page without asking a question,
and support questions about it stop. Underneath that is a habit: being able to
say what is wrong with a page and in what order you would fix it, including
pages where you were the one who was wrong. If the "before" is always someone
else's writing, the habit is only half formed.

### How this would be demonstrated elsewhere

This one cannot be demonstrated by a repository anywhere, not for want of
tooling. A repository can show that a page exists, conforms and is accurate; it
cannot show that a reader understood it, and understanding is the claim.

**Where the skill is actually exercised.** In an edit of someone else's draft,
where the measure is whether the author accepts the change and can say why. In
the gap between a first draft and a third. In the decision to cut a section that
took a day to write.

**What a learner would do.** Take a page you did not write and that works, and
rewrite it badly on purpose: bury the first instruction under motivation, move
the expected output away from the command, replace the reader's word with the
precise term everywhere. Then read both aloud. The exercise is instructive in
the direction people do not try, because the defects you introduce deliberately
are the ones you stop introducing accidentally.

Then the reverse: take a page that does not work, and fix it without adding
words. The constraint is the whole exercise. Most bad documentation is bad by
addition, and the instinct to explain more is the instinct to resist.

**What competence looks like.**

| Evidence | Why it carries weight |
|---|---|
| A diff that shortens a page and improves it | The rarest and most valuable edit |
| An author thanking you for a cut | They had to agree, which is the test |
| A page whose support questions stopped | Indirect, and the only outcome measure |
| A style decision you reversed, with the reason | Shows the judgment is live rather than inherited |
| Writing that survives a hostile review | Review is the nearest thing to a reader |

**Why none of that commits to a repository.** The diff is in someone else's
project. The acknowledgment is in a review thread. The support question that
stopped is an absence, and absences do not appear in version control. This is
the honest reason this concept has no demonstration here and would have none
anywhere: the evidence exists, it is just not the kind of thing you can clone.

What a corpus *can* show is the mechanizable part, which is why this guide
enforces a page contract, a duration, a stated result and a verification
section. Those are the floor. The craft is what happens above it, and the
distance between a page that satisfies the contract and a page that works is
the whole subject.

## Related

- [Prose linting with Vale](prose-linting.md), these rules made enforceable
- [Diátaxis](diataxis.md), where the content you cut should go
- [Reading code to verify accuracy](reading-code-to-verify.md), the other half of the craft
- [Cognitive load in technical content](cognitive-load.md), the research behind the four passes
