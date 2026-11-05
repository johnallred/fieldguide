---
title: Freshness monitoring
summary: Measuring staleness against the thing a page documents rather than against the calendar.
diataxis: how-to
audience: developer
concept: freshness-monitoring
tags: [qa, core]
---

# Freshness monitoring

`core` · difficulty 2 · 4h

!!! quote "Asked for by name"
    NVIDIA: "Automate the content lifecycle with LLMs and scripting, from drafting and updating to auditing, with checks for freshness, code accuracy, and terminology drift, and human review where judgment matters"

**Prerequisites:** [Content lifecycle](content-lifecycle.md), [Documentation CI](documentation-ci.md)

## What it is

A recurring check that identifies pages likely to have stopped being true. The
naive implementation flags pages older than some number of days. The useful one
compares a page against **the thing it documents**, because age is not
staleness and the two are only loosely correlated.

## Why the job asks for it

NVIDIA groups freshness with code accuracy and terminology drift as the three
things content auditing should cover. They share a shape: correct when written,
falsified by something that happened elsewhere.

Freshness is the hardest of the three to measure honestly, which is why most
implementations are theatre. A "last updated" date in a footer tells a reader
almost nothing: a page edited yesterday to fix a typo is no more accurate than
it was the day before, and a page untouched for three years documenting
something that has not changed in three years is perfectly correct.

What a reader actually needs to know is whether the page has been *verified
against its subject* since the subject last moved. That is a different
question, it needs different data, and the golden path below shows the two
answers diverging completely.

## The golden path

Build three definitions of staleness, run all three over the same repository,
and watch them disagree. About thirty-five minutes.

**Step 1: a repository where the code moved ahead of the docs**

````bash
mkdir -p fresh-demo/docs fresh-demo/src && cd fresh-demo
git init -q && git config user.email d@e.f && git config user.name dev

cat > src/client.py <<'EOF'
def retry(times=3):
    return times
EOF
cat > docs/retries.md <<'EOF'
---
documents: src/client.py
reviewed: 2026-01-10
---
# Retries

The default is 3.
EOF

git add -A
GIT_AUTHOR_DATE="2026-01-10T10:00:00" GIT_COMMITTER_DATE="2026-01-10T10:00:00" \
  git commit -q -m "initial"

# The code changes. The documentation does not.
cat > src/client.py <<'EOF'
def retry(times=5):
    return times
EOF
git add -A
GIT_AUTHOR_DATE="2026-09-01T10:00:00" GIT_COMMITTER_DATE="2026-09-01T10:00:00" \
  git commit -q -m "default retries 3 -> 5"
````

`docs/retries.md` now says the default is 3 and the software says 5. Add two
more pages: one documenting something genuinely unchanged, and a bulk commit
that touches every page's front matter, which is the kind of thing that happens
when a team adds a metadata field.

**Step 2: three ways to ask the question**

```python
TODAY = date(2026, 10, 27)
AGE_LIMIT_DAYS = 180

by_clock  = (TODAY - edited).days > AGE_LIMIT_DAYS   # how old is the page?
by_edit   = subject > edited                         # did the subject move since the last edit?
by_review = subject > reviewed                       # ... since the last actual review?
```

`edited` comes from `git log -1 --format=%ad`, `subject` from the same query
against the file named in `documents:`, and `reviewed` from a front-matter
field that a human sets only when they have actually checked the content.

**Step 3: run all three**

```bash
python3 freshness.py
```

```
page               edited      reviewed    subject      clock  vs-edit  vs-review
---------------------------------------------------------------------------------
overview.md        2026-10-20  2026-01-10  2026-09-01   ok     ok       STALE
retries.md         2026-10-20  2026-01-10  2026-09-01   ok     ok       STALE
stable.md          2026-01-10  2026-01-10  2026-01-10   STALE  ok       ok

  clock      flags: ['stable.md']
  vs-edit    flags: (none)
  vs-review  flags: ['overview.md', 'retries.md']
```

Read that carefully, because all three columns are informative and two of them
are wrong.

**The clock flags exactly one page, and it is the only correct page in the
repository.** `stable.md` documents something that has not changed since
January. It is old and it is true. Meanwhile `retries.md` is actively lying to
readers and the clock says it is fine.

**Comparing against the last edit flags nothing at all.** The metadata commit
on 2026-10-20 touched every page, so every page's edit date is now newer than
the code change. One bulk commit defeated the entire check. This is not a
contrived scenario: adding a front-matter field, running a formatter, or fixing
a license header across a corpus all do exactly this.

**Only comparing against an explicit review date finds the real problem.**
`retries.md` was last verified in January, the code moved in September, so the
page needs a human.

**Step 4: be honest about the third method too**

`vs-review` also flags `overview.md`, which contains only general notes and
makes no claim about the retry default. That is a false positive, and it is
structural: the check knows the page's subject changed but not whether the page
says anything about the part that changed. File-level granularity over-reports.

The mitigations, in order of cost: name a narrower subject in `documents:`,
point at a symbol rather than a file, or accept the over-reporting because the
output is a review queue rather than a build failure.

**What you built.** A freshness signal that survives a bulk commit, plus a
clear-eyed view of its remaining error mode.

## Reference

### The three definitions, and what each is good for

| Definition | Finds | False positives | False negatives |
|---|---|---|---|
| Age since last edit | Nothing reliably | Stable, correct pages | Any page edited cosmetically |
| Subject moved since last edit | Real drift, until a bulk commit | Few | Every page after a formatting run |
| Subject moved since last review | Real drift | Pages that mention the subject without claiming anything about it | Pages whose subject is not tracked |

The third needs a `reviewed:` field that humans maintain, which is its real
cost. A field that nobody updates degrades into the second definition.

### Why "last updated" in a footer is worse than nothing

| What the reader infers | What it actually means |
|---|---|
| Someone checked this recently | A character changed in this file |
| The content is current | Nothing about the content |
| Old date means do not trust it | Possibly that nothing needed changing |

Publishing an edit date invites a conclusion the data does not support. If you
publish a date, publish the review date, and if you do not have one, consider
publishing nothing.

### What to track as the subject

| Subject | Good for | Cost |
|---|---|---|
| A source file | API reference, configuration pages | Coarse; any change in the file flags the page |
| A symbol or function | Reference pages for one function | Needs parsing, or a convention |
| A dependency version | Install and compatibility pages | Easy, from the lockfile |
| A release tag | Release notes, upgrade guides | Easy |
| An OpenAPI path | Endpoint documentation | Easy if the spec is in the repo |
| Nothing trackable | Conceptual explanation | Fall back to review cadence by importance |

Conceptual pages have no mechanical subject, and pretending otherwise produces
noise. For those, a review cadence weighted by traffic is the honest answer.

### Make it a queue, not a gate

| Property | Freshness | A gate like [link checking](link-checking.md) |
|---|---|---|
| Deterministic | Yes, but about likelihood | Yes, about correctness |
| False positives | Common and structural | Rare |
| Right response | A human reviews it | Fix it now |
| Belongs in the merge path | No | Yes |

Freshness findings are probabilistic. Blocking a merge on "this page may have
stopped being true" fails builds for authors who cannot act on them, and the
check gets switched off. Run it on a schedule, open issues, and track how long
the queue is.

## How to talk about it

**Lead with the divergence.** "Age is not staleness. A page edited yesterday
for a typo is no more accurate, and a three-year-old page about something that
has not changed is correct. So I compare against the thing the page documents,
using a review date rather than an edit date, because one bulk commit across
the corpus resets every edit date and silently defeats the check."

**The follow-up is where the review date comes from**, and the honest answer is
that a human sets it when they verify the page, which means the mechanism
depends on a habit. Say that a `reviewed:` field nobody maintains decays into
the weaker check, and that you would rather measure the decay than assume it
away.

**The tradeoff to volunteer.** Subject tracking is coarse. A page flagged
because its source file changed may say nothing about the part that changed,
which is the `overview.md` case above. Narrowing the subject to a symbol costs
parsing and a convention nobody will follow perfectly. Since the output is a
review queue rather than a build failure, over-reporting is the right error to
make, but it is still an error and it still costs someone an afternoon.

**One sharper point.** Publishing a "last updated" date is actively misleading,
because readers draw a conclusion about accuracy from a fact about file
modification. Either publish a review date that means what readers think it
means, or publish nothing and keep the signal internal.

## How to prove it

**The artifact.** A scheduled job that produces a ranked review queue rather
than a pass or fail, with a tracked subject per page.

**Three things to do, in order:**

1. Run the golden path. The three-column table is the argument, and the
   `vs-edit` column flagging nothing is the part people have not considered.
2. Add a `documents:` field to twenty pages in a repository you own and run the
   comparison. Whatever it flags has been wrong for a while.
3. Measure your queue length twice, a month apart. One measurement is a
   complaint; two are a trend, and a trend is what gets staffing. Predict the
   direction before the second measurement. A queue you expected to grow and
   did not is as useful a finding as the trend you went looking for.

**What makes it credible rather than decorative.** `docpack` implements the
weak version honestly and says so: `PageMeta.is_stale` fires at 365 days and is
surfaced as a warning and as an `## Optional` section in `llms.txt`. That is
recorded as a **partial** demonstration rather than written up as a complete
one, because a clock-based check is exactly what this page argues against.
Being able to name the weakness of your own implementation is worth more in an
interview than a stronger claim nobody can verify.

## Related

- [Content lifecycle](content-lifecycle.md), the process this measures
- [Content retirement](content-retirement.md), what happens to pages that cannot be saved
- [Detecting terminology drift](terminology-drift.md), the same auditing shape for vocabulary
- [LLM content lifecycle](llm-content-lifecycle.md), automating the review the queue asks for
