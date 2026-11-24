---
title: LMS administration
summary: Running courses in a learning management system as a maintained system, with the repository as the source and the LMS as one of its outputs.
diataxis: explanation
audience: developer
concept: lms-administration
tags: [edu, supporting]
---

# LMS administration

`supporting` · difficulty 2 · 4h

> Keeping the courses in a learning management system true to their source, enrolled correctly, and reporting completion you can act on.

**Prerequisites:** [Learning paths and curriculum](learning-paths.md)

**Leads to:** [Learning content standards](learning-content-standards.md)

## What it is

The work of running courses inside a learning management system (LMS) such as
Canvas, Moodle or a corporate platform: course shells and templates,
enrollments and sections, publishing and availability, integrations, and the
completion data everyone eventually asks for.

For a documentation engineer the useful framing is that an LMS is another
publishing target. The course has a source, ideally a repository, and the LMS
is one place it is rendered. Most LMS problems are what happens when that
relationship is left implicit and people edit the output directly.

## How this applies to your role

This matters because training and lab teams deliver through an LMS, and the LMS is where a
well-designed course quietly stops working.

On a Tuesday it looks like this. A manager asks why only three of twenty people
finished the retries course. The content is fine; it was tested. You open the
course and find that someone unpublished a module in the LMS interface three
weeks ago to fix a typo and never published it again, that an old FAQ module
was added by hand, and that the partner section was enrolled but never sent an
invitation. None of that is visible from the repository, and none of it is a
content problem. It is administration, and it is the first place to look.

The second reason is reporting. Completion data is how a training program is
judged, and it is easy to misread. A drop-off at one module looks like a hard
module until you notice the learners could not reach it. Reading LMS data well
is the difference between rewriting a module and republishing it.

## The golden path

Compare a course in the repository with what the LMS is serving, read the
completion funnel, and find which problems are administrative. About thirty
minutes, with no LMS needed: the live side is an export in the shape the
Canvas modules API returns.

The comparison is committed as `drills/lms_admin.py`, which holds the three
files below and a test that keeps them identical to this page. The learners and
their progress are invented for the exercise.

**Step 1: the course as the repository defines it**

```bash
mkdir -p lms-drill && cd lms-drill
cat > course.txt <<'DATA'
1 | What you will build | published
2 | Configure retries | published
3 | Choosing a value | published
4 | Diagnose an exhausted budget | published
5 | Check yourself | published
DATA
```

**Step 2: the course as the LMS reports it, and who is enrolled**

In a real course, `modules.json` comes from
`GET /api/v1/courses/:course_id/modules`. Canvas returns ten items per page by
default and puts the rest behind a `Link` header, so a script that reads only
the first response sees only the first ten modules and reports the others as
missing.

```bash
cat > modules.json <<'DATA'
[
  {"name": "What you will build", "position": 1, "published": true},
  {"name": "Configure retries", "position": 2, "published": true},
  {"name": "Diagnose an exhausted budget", "position": 3, "published": true},
  {"name": "Choosing a value", "position": 4, "published": false},
  {"name": "Retries FAQ (old)", "position": 5, "published": true}
]
DATA
cat > progress.csv <<'DATA'
learner,section,completed
l01,spring,5
l02,spring,5
l03,spring,4
l04,spring,2
l05,spring,2
l06,spring,2
l07,spring,1
l08,spring,0
l09,spring,5
l10,spring,2
l11,spring,3
l12,spring,2
l13,partners,0
l14,partners,0
l15,partners,1
l16,partners,0
l17,partners,2
l18,partners,0
l19,partners,0
l20,partners,2
DATA
curl -sO https://raw.githubusercontent.com/johnallred/fieldguide/main/drills/lms_admin.py
```

**Step 3: compare and read**

```bash
python3 lms_admin.py course.txt modules.json progress.csv
```

```
step 1: does the live course match its source?
  unpublished in the LMS:   Choosing a value
  missing from the LMS:     Check yourself
  only in the LMS:          Retries FAQ (old)
  order differs:            What you will build > Configure retries > Diagnose an exhausted budget > Choosing a value
  4 difference(s)

step 2: where do learners stop?
  1 What you will build             14/20  (-6)
  2 Configure retries               12/20  (-2)
  3 Choosing a value                 5/20  (-7)
  4 Diagnose an exhausted budget     4/20  (-1)
  5 Check yourself                   3/20  (-1)
  largest drop: Choosing a value (-7)

step 3: who never started?
  spring      1/12 never started
  partners    5/8 never started
```

**Step 4: read the three answers together**

The live course has drifted from its source in four ways, all from edits made
directly in the LMS. The one that matters is the unpublished module, because it
explains step 2: the largest drop, seven learners, is at "Choosing a value",
the module nobody can currently open. The five who completed it did so before
it was unpublished. That drop is an administrative fault, and rewriting the
module would not have touched it.

Step 3 adds a second one. Five of eight partners never started, against one of
twelve in the spring cohort. A difference that large between sections is
almost always enrollment or access (an invitation not sent, a login that does
not work for external users), not motivation.

**Step 5: fix it from the source**

Republish the module, delete the stray FAQ, add the missing module, and do all
three by publishing from the repository rather than by editing the LMS, so the
next comparison comes back clean. Canvas Blueprint courses do the same at
scale: changes to one source course sync to every associated course, and the
blueprint can restrict editing in the copies so they cannot drift.

**What you built.** A drift check between a course's source and its live copy,
a completion funnel that separates administrative faults from content
problems, and two fixes (a republished module and a partner enrollment) that no
amount of rewriting would have found.

## Reference

### What administration covers

| Area | The work | Typical fault |
|---|---|---|
| Course structure | Shells, templates, modules, availability dates | Edited in the UI, drifted from source |
| Enrollment | Sections, roles, cohorts, external users | Enrolled but never invited, or wrong role |
| Publishing | What learners can see, and when | Unpublished module blocks everyone after it |
| Integrations | LTI tools, SCORM and xAPI packages | A tool launch that fails for one role |
| Copies | Course copy, templates, Blueprint sync | Fix applied to one copy of ten |
| Reporting | Completion, scores, activity | Reading an access fault as a content fault |

### Canvas API facts worth knowing

| Fact | Why it matters |
|---|---|
| `GET /api/v1/courses/:course_id/modules` lists modules with name, position and published | The basis of any drift check |
| Module items come only with `include[]=items`, and may be omitted for large modules | Use the module items endpoint to be sure |
| Lists are paginated through the `Link` header, ten per page by default | Unpaginated scripts silently see only the first page |
| A Blueprint sync is a `POST` to the blueprint template's migrations endpoint | One source course updates every associated course |
| Blueprint restrictions limit editing of content, points, due dates and availability in copies | The LMS-side defense against drift |

### Reading completion data

| Pattern | Usually means | Check first |
|---|---|---|
| A cliff at one module | It cannot be reached, or it is genuinely hard | Is it published and available? |
| One section far behind another | Enrollment or access | Were they invited? Can they log in? |
| Many enrolled, no activity | The course was never announced | Who was told it exists? |
| Steady small losses at every step | Normal attrition | Compare with the previous cohort |

### Sources

Opened and checked on 2026-11-23: Canvas LMS REST API documentation for
[modules](https://canvas.instructure.com/doc/api/modules.html),
[pagination](https://canvas.instructure.com/doc/api/file.pagination.html) and
[Blueprint courses](https://canvas.instructure.com/doc/api/blueprint_courses.html).

## Explaining it to your team

**How to explain it.** Lead with the source. "The repository is the course; the
LMS is where we publish it. When someone fixes a typo in the LMS, the two
disagree, and the next publish either loses the fix or nobody publishes again.
So every change goes through the repository, and a weekly check compares the
two and reports anything that drifted."

**The follow-up is usually "the LMS editor is easier for the trainers".** It
is, and it is a fair objection. The answer is not to forbid it but to make the
drift visible: a weekly report of differences turns an invisible problem into a
short list, and someone can decide each time whether the LMS edit should be
copied back to the source.

**The tradeoff to name.** Treating an LMS as a publishing target means building
and maintaining a sync, and LMS APIs differ, change, and do not cover
everything the interface can do. For one small course, careful manual
administration is cheaper. The investment pays off with many courses, many
copies, or frequent change.

**One sharper point.** Completion reports are read as evidence about content,
and they are at least as often evidence about administration. Before anyone
rewrites a module because learners stop there, check that they can reach it.
It is the cheapest check and the one most often skipped.

## Putting it into practice

**The work product.** A drift report between a real course's source and its
LMS copy, run on a schedule, and a completion funnel with each drop explained
as content, access or attrition.

**Three things to do, in order:**

1. Run the golden path, then export the module list of one real course and
   compare it with wherever its source lives. Expect at least one difference
   nobody knew about.
2. Read the completion funnel for that course and check that every module
   with a large drop is published and available before calling it hard.
3. Schedule the drift check weekly. If it reports nothing for a month, reduce
   it to monthly rather than deleting it.

**How to tell it is working.** The drill above runs in this guide's test suite
and its output is the output quoted here. It runs against an export in the
Canvas API's shape, not against a live LMS, and the learner data is invented,
so the [demonstrated](../demonstrated.md) page records the concept as partial.
In your own courses, the sign is a drift report that stays empty and
completion drops that are explained before anyone rewrites content.

## Related

- [Learning content standards](learning-content-standards.md), how packages and tracking data reach the LMS
- [Learning paths and curriculum](learning-paths.md), the course structure the LMS renders
- [Docs-as-code](docs-as-code.md), the same source-of-truth argument for documentation
- [Documentation analytics](docs-analytics.md), reading usage data without over-reading it
- [Learner and task analysis](learner-task-analysis.md), the same habit of checking whether a problem is teaching at all
