---
title: Prioritizing documentation work
summary: Deciding what to build, fix and retire from evidence rather than from whoever asked most recently.
diataxis: explanation
audience: operator
concept: docs-prioritization
tags: [craft, supporting]
---

# Prioritizing documentation work

`core` · difficulty 2 · 3h

> use the data to decide what to build, fix, or retire

> Source: nvidia posting, verbatim

**Prerequisites:** [Repeat-question analysis](repeat-questions.md), [A systems mindset](systems-mindset.md)

## What it is

Choosing which documentation work to do from evidence rather than from whoever
asked most recently. The output is a ranked list with a stated basis, and
crucially a **retire** column, which most documentation backlogs do not have.

## Why the job asks for it

NVIDIA's phrasing is one clause at the end of the measurement bullet: "Measure
outcomes such as time-to-first-success, support deflection, repeat questions,
and AI answer quality, and use the data to decide what to build, fix, or
retire."

The three verbs are the content. Most documentation prioritisation has two
options, build and fix, and a backlog that therefore only grows. **Retire is the
one that makes the other two sustainable**, and it is in the posting explicitly.

On a Tuesday this is the thing that decides whether you are useful. A
documentation backlog at a company this size has a few hundred items: requests
from engineers, gaps you found, support escalations, a migration somebody
promised, and forty pages marked for review. You can do maybe three things this
week. Without a basis, the three you do are whichever came with the most senior
request attached, which is a reasonable heuristic and an expensive one.

The reason it is `core`: the backlog in this field is unbounded. The product
ships continuously, every release creates potential gaps, and the corpus ages
whether you touch it or not. Prioritisation is not an occasional planning
activity, it is the mechanism that converts an infinite queue into a finite week.

## The golden path

Build a ranking from evidence you can actually get, and see it disagree with
your instinct. Thirty minutes.

**Step 1: get the inputs that are cheap and the ones that are not**

```bash
mkdir -p prio-drill && cd prio-drill
cat > inputs.md <<'EOF'
| Input                        | Cost to get        | What it tells you |
|------------------------------|--------------------|-------------------|
| Support ticket topics        | cheap (export)     | what fails in the field |
| Repeat questions in channels | cheap (search)     | what docs failed to answer |
| Page views                   | cheap (analytics)  | demand, not satisfaction |
| Search queries with no click | cheap, underused   | a gap, stated in the reader's words |
| Time to first success        | expensive (study)  | whether the golden path works |
| Staleness by review date     | free (front matter)| risk, not impact |
| Requests from engineers      | free (they arrive) | what a colleague noticed |

The fourth row is the best value in the list and almost nobody uses it.
A query with no click is a reader telling you, in their own words, that
the answer is not there.
EOF
cat inputs.md
```

**Step 2: score on impact and cost, and write down the basis**

```bash
cat > backlog.csv <<'EOF'
item,action,evidence,affected_per_month,effort_hours,basis
Batch size guidance,build,"12 support tickets, 3 repeat asks",40,4,tickets
Rewrite install page,fix,"search: 'install fails' 60/mo no click",300,6,search
Migrate 40 pages to new model,fix,"migration commitment",0,30,commitment
USD schema reference,build,"2 engineer requests",8,20,request
Retire 2.x upgrade guides,retire,"0 views in 6 months, 11 pages",0,2,analytics
Fix 7 stale pages flagged by CI,fix,"review date >365d",25,5,staleness
Tutorial for the agentic toolkit,build,"product launch in 3 weeks",200,16,launch
EOF
column -s, -t backlog.csv
```

**Step 3: rank it mechanically, then look at what moved**

```bash
python3 - <<'PY'
import csv

rows = list(csv.DictReader(open("backlog.csv")))
for row in rows:
    affected = float(row["affected_per_month"])
    effort = float(row["effort_hours"])
    # Deliberately crude: people helped per hour of work. The number is not
    # the decision, it is a way to notice when your instinct disagrees with
    # the evidence and to make yourself say why.
    row["score"] = affected / effort if effort else 0.0

rows.sort(key=lambda r: -r["score"])
print(f"{'item':<34} {'action':<8} {'per mo':>7} {'hrs':>5} {'score':>7}  basis")
print("-" * 86)
for row in rows:
    print(f"{row['item']:<34} {row['action']:<8} "
          f"{row['affected_per_month']:>7} {row['effort_hours']:>5} "
          f"{row['score']:>7.1f}  {row['basis']}")
PY
```

**Step 4: argue with the ranking, in writing**

The ranking is an input, not a decision. This step is the actual skill.

```bash
cat > decisions.md <<'EOF'
# This week

DO  Rewrite install page            (50.0)  highest score, and it is the
                                            first thing every developer touches
DO  Retire 2.x upgrade guides       ( 0.0)  scored zero and I am doing it anyway:
                                            2 hours, removes 11 pages from every
                                            future migration, audit and review
                                            cycle. The score cannot see avoided
                                            future cost.
DO  Batch size guidance             (10.0)  12 tickets is a real number and the
                                            fix is a decision guide, not a page

DEFER  Agentic toolkit tutorial     (12.5)  scored well, but the 200/month is a
                                            forecast rather than a measurement.
                                            Revisit when the launch date is firm.
DEFER  Migrate 40 pages             ( 0.0)  a commitment with no measured impact.
                                            Renegotiate the deadline rather than
                                            spending 30 hours on it this month.
DEFER  USD schema reference         ( 0.4)  20 hours for 8 people. Ask the two
                                            requesters whether a 2-hour decision
                                            guide would do instead.

NOTE  Staleness items scored 5.0 and are genuinely ambiguous: a stale page is
      a risk, not a measured harm. Doing them when they are cheap.
EOF
cat decisions.md
```

**What you built.** A ranking, and a written record of the three places you
overrode it. The overrides are the deliverable. A score nobody argues with is a
score nobody is using; **the point of making it explicit is to make the
disagreements explicit too**, so that next quarter you can tell whether your
instincts were better than the number.

Note the retire item: it scored zero and was done anyway, because the scoring
function cannot see avoided future cost. That is a known limitation written down
rather than a flaw in the method.

## Reference

### The three actions

| Action | When | Common mistake |
|---|---|---|
| **Build** | A gap with measured demand | Building for forecast demand |
| **Fix** | Existing content failing readers | Fixing by staleness date rather than by harm |
| **Retire** | Content with no readers, or superseded | Never doing it, so the corpus only grows |

### Why retire is load-bearing

Every page you keep costs something forever, and the costs are invisible
individually:

| Cost of a page nobody reads | Paid by |
|---|---|
| It appears in search results and in retrieval | Every reader who gets it instead of the right page |
| It is included in every audit and migration | You, repeatedly |
| It must be reviewed to stay in compliance with the model | The review cycle |
| It dilutes [llms.txt](llms-txt.md) and the chunk corpus | Every assistant answer |
| It can be found and followed, and be wrong | A reader, expensively |

The fourth row is new and is the one worth raising in an interview. In a corpus
packaged for retrieval, **a stale page is not merely unread, it is competing**.
That is a materially stronger argument for retirement than it was five years
ago.

### What each input is good and bad for

| Input | Good for | Misleads about |
|---|---|---|
| Page views | Demand | Satisfaction. A heavily viewed page may be heavily re-read because it is bad |
| Support tickets | Real failures | Only covers people who asked. Most do not |
| Repeat questions | Documentation gaps | Biased toward whoever is loudest in a channel |
| Zero-click searches | Gaps in the reader's words | Volume is low, so weak on frequency |
| Staleness | Risk | Harm. An old page about something stable is fine |
| Engineer requests | What a colleague noticed | Impact. Usually reflects their week |

### Honest limits of scoring

| Limit | Consequence |
|---|---|
| Affected-per-month is usually a guess | The ranking is precise about imprecise inputs |
| It cannot see avoided future cost | Retirement and tooling always score badly |
| It cannot see strategic commitments | A launch has value a ticket count does not capture |
| It optimises for the readers you have | Not the readers a new capability might attract |
| Effort estimates are wrong | And wrong in the optimistic direction |

A scoring function that is treated as a decision is worse than no scoring
function, because it launders judgement as arithmetic. Treated as a prompt for
disagreement, it is useful.

## How to talk about it

**What a competent answer sounds like.** Lead with an override and with retire.
"I score the backlog on people affected per hour of work, and then I write down
where I disagree with the score. Last quarter the highest-value thing I did
scored zero: retiring eleven pages about a version nobody runs. Two hours, and
it removed them from every future audit and from the retrieval corpus, where
they were competing with the current pages."

**The follow-up is "how do you say no to a senior person",** and it is the real
question. The answer that works is to make the comparison explicit rather than
the refusal. You do not say no; you show the two items and what each is based
on, and ask which they want. "This is 20 hours for 8 people, and this is 6 hours
for 300 based on search data. I can do the first if it matters more for a reason
the data cannot see." That reframes it from your judgement against theirs to a
choice they are making with information.

**The tradeoff to volunteer.** Evidence-based prioritisation systematically
underweights new things. Every input you can cheaply measure is about the
readers you already have and the content that already exists, so a strict
reading of the data never builds documentation for a capability that has not
shipped. That is exactly backwards for
[release readiness](release-readiness.md), where the whole point is being ready
before demand exists. The resolution is to carve out capacity for launch work
*outside* the scored backlog, rather than trying to score a forecast, because a
forecast dressed as a measurement corrupts the whole exercise.

**One sharper point.** The most valuable prioritisation move in this field is
usually not choosing between backlog items at all, it is noticing that several
items share a cause and that the cause is fixable once. Four tickets about four
pages being out of date is not four fix items; it is one
[freshness monitoring](freshness-monitoring.md) item. That is
[the systems mindset](systems-mindset.md) as a prioritisation technique, and it
is how a backlog starts shrinking instead of being triaged forever.

## How to prove it

**The artifact.** A ranked backlog with a basis column and a written record of
the overrides. One page, and it is unusual enough to be memorable.

**Three things to do, in order:**

1. **Export your zero-click search queries** for any documentation site you can
   access. It takes ten minutes, almost nobody does it, and the list is readers
   telling you the gaps in their own words.
2. **Find something to retire.** Pages with no views in six months, or
   documentation for a version out of support. Propose it with the costs from
   the table above, including the retrieval-competition argument.
3. **Score a real backlog and write down your three overrides.** The overrides
   are the artifact. A ranking is arithmetic; knowing when to ignore it is the
   job.

**What makes it credible rather than decorative.** Anyone can say they are data-driven. A backlog with
a basis column, and a documented case where you did the thing that scored zero
and said why, demonstrates that you use evidence without hiding behind it.

### How this would be demonstrated elsewhere

Prioritisation needs a backlog with competing claims on it and someone who can
be overruled. A repository with one author has neither, so what is here is the
reasoning and not the decisions.

**What you need.** A real backlog, a source of demand data, and at least one
stakeholder who wants something different from what the data says.

**What a learner would do.** Take your next ten documentation tasks and give
each a basis column: the ticket count, the search volume, the failing check, or
"someone asked". Then rank by basis and compare with the order you would have
chosen anyway.

**What you would see.**

| Observation | Typical | What it tells you |
|---|---|---|
| Tasks with a measurable basis | Fewer than half | The honest starting point |
| Tasks whose basis is "someone asked" | The largest group | Not illegitimate, but it should be labelled |
| Agreement between the data order and your instinct | Partial | Where it disagrees is the interesting part |
| Tasks you did anyway, against the data | Some, and that is fine | Say why, in the column |

The fourth row is the demonstration. Anyone can claim to be data-driven; the
specific, unfakeable artifact is a backlog where one item scored zero, was done
anyway, and carries the reason.

**Why it does not commit.** A ranked backlog is a snapshot of an argument. The
evidence of skill is in having held the argument and recorded the exception,
and that is a document in someone else's planning tool.

## Related

- [Repeat-question analysis](repeat-questions.md), the highest-signal input
- [Retiring content](content-retirement.md), the mechanics of the third verb
- [Documentation analytics](docs-analytics.md), where most inputs come from
- [A systems mindset](systems-mindset.md), finding the shared cause behind several items
