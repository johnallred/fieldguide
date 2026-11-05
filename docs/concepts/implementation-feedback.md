---
title: Giving architecture owners implementation feedback
summary: Reporting what broke when you built someone else's design, in a form they can act on.
diataxis: explanation
audience: developer
concept: implementation-feedback
tags: [craft, core]
---

# Giving architecture owners implementation feedback

`core` · difficulty 2 · 3h

> sharing implementation feedback (what works, breaks, and scales) to refine content models, information architecture, and AI-readiness patterns

> Source: nvidia posting, verbatim

**Prerequisites:** [A systems mindset](systems-mindset.md)

## What it is

Telling the person who designed a standard what happened when you applied it at
scale, specifically enough that they can change the design. Not escalating a
complaint, and not quietly working around it.

The useful unit is an instance with a count: this rule, this many pages, this
failure, this proposal.

## Why the job asks for it

This is the most distinctive thing in the NVIDIA posting and the easiest to skim
past. Read the two bullets together:

"Collaborate with documentation leads on knowledge architecture, sharing
implementation feedback (what works, breaks, and scales) to refine content
models, information architecture, and AI-readiness patterns."

"A collaborative style: you turn design intent into working systems and give
leads clear, constructive feedback grounded in implementation."

**The role is explicitly the implementer advising the architects.** Documentation
leads own the content model; you apply it to thousands of pages and find out
where it does not hold. That split is deliberate, and it means the job has a
built-in feedback obligation. You are not expected to accept a standard you have
discovered is wrong, and you are not authorised to change it unilaterally
either.

On a Tuesday this is a specific recurring moment. The content model requires an
`audience` field with four allowed values. You apply it across the Omniverse
corpus and find 180 pages that are genuinely for two audiences at once, and
another 40 where the honest answer is a fifth value nobody anticipated. You can
pick the closest value and move on, which corrupts the data quietly. You can
block on it, which stops the migration. Or you can report it in a form the lead
can decide from, which is the job.

The reason this is `core`: the quality of this feedback loop determines whether
the standards improve or ossify. A lead who only hears "done" learns nothing
from a migration that touched three thousand pages.

## The golden path

Turn a real friction into a report someone can decide from. Thirty minutes, and
the artifact is the deliverable.

**Step 1: hit the friction and resist both reflexes**

```bash
mkdir -p feedback-drill && cd feedback-drill
cat > friction.md <<'EOF'
THE STANDARD   Every page declares exactly one `audience`, from:
               new-user | developer | operator | contributor

WHAT HAPPENED  Applying it to 260 pages:
                 - 180 pages are honestly two audiences
                 - 40 pages are for partners, which is not a value
                 - 40 pages fit cleanly

THE TWO WRONG REFLEXES
  Pick the closest value and move on.
      -> the field now contains guesses. Every downstream filter is
         subtly wrong and nobody can tell.
  Block the migration and wait for a decision.
      -> three thousand pages stalled on a taxonomy question.
EOF
cat friction.md
```

**Step 2: get a number, because a number is what makes it a design question**

An anecdote is a complaint. A count is evidence.

```bash
mkdir -p docs
python3 - <<'PY'
# Stand in for a real corpus scan. In practice this reads your pages and
# classifies them; what matters is that the output is counts, not opinions.
import json, pathlib
findings = {
    "total_pages": 260,
    "single_audience_clean": 40,
    "two_audiences_honestly": 180,
    "audience_not_in_vocabulary": 40,
    "examples": {
        "two_audiences": [
            "install/requirements.md  (new-user and operator)",
            "usd/schema-basics.md     (developer and contributor)",
        ],
        "missing_value": [
            "partners/certification.md",
            "partners/branding.md",
        ],
    },
}
pathlib.Path("findings.json").write_text(json.dumps(findings, indent=2))
print(json.dumps(findings, indent=2)[:400], "...")
PY
```

**Step 3: write the report in the shape a decision-maker can use**

Five parts, in this order. The order is the content: the proposal comes after
the evidence, and the recommendation comes last so it is clearly separable from
the facts.

```bash
cat > report.md <<'EOF'
# Content model: the `audience` field does not survive the Omniverse corpus

## What I did
Applied the content model to 260 pages in `omniverse/`, the first corpus large
enough to test the closed vocabulary.

## What happened
| Outcome | Pages |
|---|---|
| One audience, cleanly | 40 |
| Honestly two audiences | 180 |
| Audience not in the vocabulary (partners) | 40 |

69% of pages cannot satisfy the field as written. Examples:
- `install/requirements.md` is read by new users and by operators, and the
  page is correct for both.
- `partners/certification.md` has no available value.

## What I think is happening
The field conflates two things: *who the page is written for* (one answer, a
real editorial decision) and *who reads it* (several answers, an observation).
The vocabulary is right for the first and is being asked to do the second.

## Options, with what each costs
| Option | Cost | Who pays |
|---|---|---|
| Allow a list of audiences | Every filter becomes a set operation; navigation needs a primary anyway | Tooling, once |
| Add `primary_audience` plus optional `also_read_by` | One more field; migration can default the second to empty | Authors, slightly |
| Add `partner` to the vocabulary | Solves 40 pages, not the 180 | Nobody, but it is a partial fix |
| Keep as is, authors pick the closest | Free today; the field silently becomes unreliable | Every downstream consumer, forever |

## What I would do
`primary_audience` plus optional `also_read_by`. It keeps the editorial
decision single-valued, which is what navigation and retrieval filters need,
and it stops authors guessing. I can migrate the 260 pages in a day with the
primary inferred from the directory and `also_read_by` left empty.

I am not blocking on this: I will hold the Omniverse migration for a week and
proceed with the other corpora, which do not hit it.
EOF
wc -l report.md
```

**Step 4: check it against the test that matters**

```bash
cat > test.md <<'EOF'
Can the lead decide from this without talking to me?

[x] Is there a number?                      69% of 260 pages
[x] Can they see the actual pages?          two examples per case
[x] Is my diagnosis separable from the data? "What I think is happening"
[x] Are the options costed?                  table, with who pays
[x] Is my recommendation last and labelled?  "What I would do"
[x] Do they know what happens if they say nothing?  holding one week
EOF
cat test.md
```

**What you built.** A report that is decidable without a meeting. The last line
of the checklist is the one people forget: a lead needs to know the default
outcome if they do nothing, because that is what converts your report from a
question into a decision with a deadline.

## Reference

### The five parts, and why the order matters

| Part | Purpose |
|---|---|
| What I did | Scope, so they know how much the finding generalises |
| What happened | Counts and examples. No interpretation yet |
| What I think is happening | Your diagnosis, clearly marked as yours |
| Options, costed | Shows you understand the design space, not just your preference |
| What I would do | Last, so it is separable. A recommendation, not a conclusion |

Putting the recommendation first reads as advocacy, and a lead who disagrees
with it discounts the evidence behind it. Putting it last lets them reach a
different conclusion from the same facts without overruling you.

### What makes feedback actionable

| Actionable | Not actionable |
|---|---|
| "180 of 260 pages are two audiences" | "The audience field is awkward" |
| "Here are two example pages" | "Lots of pages have this problem" |
| "Option A costs tooling work once" | "We should allow multiple values" |
| "I am holding one corpus for a week" | "Let me know what you think" |
| "This is the first corpus large enough to test it" | "This has always been a problem" |

### Things worth reporting that people do not

| Report | Why it is valuable |
|---|---|
| A standard that worked better than expected | Leads hear only about breakage and over-correct |
| A rule nobody violated in 3,000 pages | It may be unnecessary, and removing it is cheap |
| A validator whose warnings are universally ignored | A dead gate is worse than none |
| The cost of a rule in author time | Nobody measures this and it is the main objection |
| Where the model held under scale | "What works" is in the posting's own phrasing |

That last row is in the quote and is the part almost everybody drops. "What
works, breaks, and scales" is three things.

### Failure modes

| Failure | What it causes |
|---|---|
| Silent workaround | Data corruption nobody can trace. The worst one |
| Blocking on every ambiguity | You become the reason the migration stalled |
| Reporting friction without counts | Reads as a complaint, gets deferred |
| Arriving with one option | Reads as a demand; leads defend the status quo |
| Reporting only failures | The lead over-corrects a working standard |
| No default if they do nothing | Your report joins a backlog |

## How to talk about it

**What a competent answer sounds like.** Tell it as a report, with the number
first. "The content model required one audience per page. Applying it to 260
pages, 69 percent either had two honest audiences or had none in the
vocabulary. I wrote it up with the counts, example pages, three options with
their costs, and my recommendation last, and I kept the other corpora moving
while the lead decided. We ended up splitting the field into a primary and an
optional secondary."

**The follow-up is "what if the lead disagrees with you",** which is testing
whether you can be overruled gracefully. The answer worth giving: implement
their decision properly and instrument it. If you believed the field would
become unreliable, add a check that measures how often authors pick the closest
value rather than a true one, and report the number in six months. That is
disagreeing with evidence rather than with insistence, and it is the only form
of disagreement that survives a difference in authority.

**The tradeoff to volunteer.** This kind of report costs an hour to write and it
is an hour you are not migrating pages. There is a real version of this job where
you write careful reports about everything and ship nothing, and a lead will
notice. The filter is scale: report what you found because you did the work at
volume, and absorb what is merely awkward. A finding that only appears at 260
pages is worth an hour; a rule you personally find annoying is not.

**One sharper point.** The structural value of this role is that **the implementer
sees things the architect cannot.** A content model is a hypothesis about a
corpus, and the corpus is the only thing that can falsify it. Saying that out
loud reframes the feedback obligation from politeness to epistemics, which is
much closer to how NVIDIA's posting describes it, and it explains why they
wanted this as a named requirement rather than assuming it.

## How to prove it

**The artifact.** One written report in the five-part shape, about something real.
It can be from any context: a schema you applied, a lint rule you rolled out, a
convention you migrated to.

**Three things to do, in order:**

1. **Find a standard you worked around rather than reported.** Everyone has
   one. Write the report retroactively, with the count. The exercise is the
   point. If the count is zero, you have not looked at a wide enough window:
   the workaround nobody reported is the one that has been in place longest.
2. **Report something that worked.** Harder than it sounds, and the rarest
   thing in this category. Find a rule that held up under scale and say so with
   a number.
3. **Find one dead gate.** A check whose warnings nobody acts on. Propose
   removing it. Removing a rule is the clearest possible demonstration that your
   feedback is about the system rather than about your preferences.

**What makes it credible rather than decorative.** "I give constructive feedback" is unfalsifiable. A
one-page report with a percentage, two example files, a costed options table and
a recommendation at the bottom is a thing an interviewer can read in two minutes
and immediately recognise as the output of someone who has done this.

### How this would be demonstrated elsewhere

The whole concept is a conversation with someone who owns a design, so the
evidence is in their repository, their review threads and their decisions, not
in yours.

**Where the skill is exercised.** When documenting a feature reveals that the
feature is confusing, and you have to decide whether to write a clearer page or
say the design is wrong. In a review comment that proposes a product change
rather than a wording change. In being right about it often enough to be asked
next time.

**What a learner would do.** Keep a log, for a month, of every time
documentation work surfaced something that was not a documentation problem:

```
what I was documenting     what I found                  what I did
the retry flag             two flags do the same thing    filed a bug
the error codes            404 and 410 are inconsistent   wrote around it
the setup steps            step 3 exists for a bug        proposed removal
```

Then count the third column. Most people find they wrote around nearly all of
it, which is the finding: documentation work is the most reliable source of
design feedback in an organisation and the least likely to be delivered as
feedback, because writing around a problem is faster and feels like the job.

**What competence looks like.**

| Evidence | Why it carries weight |
|---|---|
| A product change traceable to a docs review | The strongest and rarest |
| A bug filed from writing a page | The habit, present |
| A design review you were invited into | Earned by prior accuracy |
| Feedback given and declined, recorded without rancour | Shows the relationship survived |
| A page you *did* write around, and said why | Honest about the tradeoff |

**The specific skill, which is what to make checkable.** Feedback lands when it
is phrased as a reader's observed difficulty rather than as an opinion about the
design. "This is confusing" is an opinion. "Documenting this takes four
paragraphs to explain which of two flags to use, and here is the draft" is an
observation with the evidence attached, and it is hard to argue with because the
draft is the argument.

**Why it does not commit to a repository.** A single-author project has no
architecture owner to give feedback to. Even in a team, the artifact is a
decision in someone else's system, and the part that demonstrates skill, that
the feedback was accepted and acted on, is precisely the part you do not
control. This is why the concept stays `craft` and why this guide claims no
demonstration of it.

## Related

- [A systems mindset](systems-mindset.md), the same instinct applied downward
- [Working with engineers as sources](working-with-engineers.md), the other direction
- [Content models](content-model.md), the usual subject of this feedback
- [Prioritizing documentation work](docs-prioritization.md), deciding what is worth an hour
