---
title: Field enablement
summary: Teaching the people who demo, sell and support the product, measuring whether they can deliver without you, and carrying what they hear back to product.
diataxis: explanation
audience: developer
concept: field-enablement
tags: [edu, supporting]
---

# Field enablement

`supporting` · difficulty 2 · 4h

> Teaching the people who demo, sell and support the product until they can deliver without you, and turning what they hear into changes.

**Prerequisites:** [Workshops and hands-on labs](workshops.md), [Demo design](demo-design.md)

## What it is

Enablement for the people between the product and its users: solutions
engineers, account teams, partners and support. They do not need to use the
product the way a developer does. They need to explain it, demo it and answer
questions about it, in front of someone else, without the person who built
the material.

So the goal is a different one. Enabling a learner ends when they can do the
task. Enabling a deliverer ends when they can make someone else able to do it,
which is a performance skill and has to be practised and checked as one.

## How this applies to your role

Because developer education teams build the demos, labs and guides the field
uses, and the measure of that work is whether the field can use them without
calling you.

On a Tuesday it looks like this. Twelve people attended the training last
month, and the attendance report says the field is enabled. Then a customer
demo goes badly, an account manager cannot answer a question about pricing,
and the same four people keep messaging you about retries. Attendance measured
whether people were in the room. It did not measure whether any of them could
give the demo, and it did not notice that pricing has no resource at all.

The field is also the best source of product signal most teams never use. Its
questions are what customers asked an hour ago. When four people across three
roles ask whether batch works on a cloud platform, that is not an enablement
gap; it is a product gap reported by the people closest to the buyer, and
routing it to product is part of the job.

## The golden path

Read a roster, a month of field questions and the self-service resources, and
answer three questions: who can deliver without you, what self-service does
not cover, and what the field is telling product. About twenty-five minutes.

The report is committed as `drills/field_enablement.py`, which holds the three
files below and a test that keeps them identical to this page. The people,
questions and resources are invented.

**Step 1: who did what**

A teach-back here means the person delivered the demo back, unassisted, to
someone who checked it. It is the deliverer's version of a test.

```bash
mkdir -p field-drill && cd field-drill
cat > roster.csv <<'DATA'
person,role,attended,practised,teach_back
se1,SE,yes,yes,pass
se2,SE,yes,yes,pass
se3,SE,yes,yes,pass
se4,SE,yes,yes,fail
se5,SE,yes,no,-
ae1,AE,yes,yes,pass
ae2,AE,yes,no,-
ae3,AE,yes,no,-
ae4,AE,yes,no,-
p1,partner,yes,yes,fail
p2,partner,yes,no,-
p3,partner,yes,no,-
DATA
```

**Step 2: what the field asked, and what answered it**

```bash
cat > questions.csv <<'DATA'
person,topic,kind,resource
se5,retries,knowledge,configure-retries
ae2,retries,knowledge,configure-retries
ae3,retries,knowledge,configure-retries
p2,retries,knowledge,-
ae4,retries,knowledge,configure-retries
p3,retries,knowledge,-
se4,retries,knowledge,configure-retries
ae2,retries,knowledge,configure-retries
ae1,pricing,knowledge,-
ae3,pricing,knowledge,-
ae4,pricing,knowledge,-
p1,pricing,knowledge,-
p2,pricing,knowledge,-
se1,auth,knowledge,auth-guide
p3,auth,knowledge,auth-guide
ae2,auth,knowledge,auth-guide
se2,batch on cloud-b,product,-
se3,batch on cloud-b,product,-
ae1,batch on cloud-b,product,-
p1,batch on cloud-b,product,-
DATA
cat > resources.csv <<'DATA'
name,topic,views_30d
configure-retries,retries,140
retry-faq,retries,0
auth-guide,auth,60
DATA
curl -sO https://raw.githubusercontent.com/johnallred/fieldguide/main/drills/field_enablement.py
```

**Step 3: run the report**

```bash
python3 field_enablement.py roster.csv questions.csv resources.csv
```

```
step 1: who can deliver without you
  attended the training      12/12
  practised with feedback     6/12
  passed a teach-back         4/12
  by role: SE 3/5, AE 1/4, partner 0/3

step 2: what the field asks, and whether self-service answers it
  topic               questions  answered  action
  retries                  8        6/8    point the field at it
  pricing                  5        0/5    write a resource
  auth                     3        3/3    covered
  unused resource: retry-faq (0 views, answered nothing): merge or retire

step 3: what the field is telling product
  batch on cloud-b: 4 questions, from SE, AE, partner
```

**Step 4: read it as three decisions**

Everyone attended and a third can deliver. Practice with feedback, not
attendance, is where the drop happens: half the roster never practised, and
none of the people who skipped practice reached the teach-back. Partners are
at zero, so the next session goes to them, not to another round for everyone.

Pricing has five questions and no resource, which is the next thing to write.
Retries has a resource that answers most questions, and two people did not
find it, which is a pointer problem, not a content one. The retry FAQ has no
views and answered nothing, so it gets merged into the page people do use.

The batch questions are not about knowledge. Four people in three roles asked
about something the product does not do on one platform, which is the gap the
[multi-platform parity](multi-platform-parity.md) page documents. That goes to
product with the count attached, not into another enablement session.

**Step 5: run a teach-back**

Ask one person who has not passed to give the demo to you, from the script,
without help. Note the first place they stop and the first thing they explain
wrongly, then change the material, not the person: a teach-back checks how
well the material explained the demo. Repeat until they give it unassisted.

**What you built.** A readiness measure based on delivering, not attending, a
self-service backlog ranked by real questions, one resource to retire, and a
product gap with evidence from the people closest to customers.

## Reference

### Enabling a learner and enabling a deliverer

| | Learner | Deliverer |
|---|---|---|
| Done when | They can do the task | They can make someone else able to do it |
| Practised by | Doing the task | Presenting, demoing and answering questions |
| Checked by | An exercise or a quiz | A teach-back, delivered to someone who checks it |
| Feedback on | The content | The delivery: order, timing, explanation, recovery |
| Measured by | Completion and success | How many can deliver without you, by role |

### Practice and feedback

| Practice | What it is for |
|---|---|
| Rehearsal with a reviewer | Feedback on delivery: what was skipped, where it ran long |
| Teach-back | Proof that the person can deliver alone, and a test of the material |
| Office hours | Questions the material did not answer, collected as data |
| Recorded examples | A model of a good delivery, for people who cannot attend |

The evidence for practice is strong but less dramatic than often claimed. The
original deliberate-practice research described structured activity designed
to improve performance, often designed by a teacher. A 2019 replication did
not reproduce its core finding, and a 2020 review concluded that practice is
an important predictor of expertise but probably not as important as proposed.
Treat practice with feedback as necessary, not as a guarantee.

### What field questions tell you

| Pattern | Means | Action |
|---|---|---|
| Many questions, no resource | A gap in self-service | Write the resource |
| Questions a resource answers | People cannot find it | Link it where they ask |
| A resource nobody opens | It answers nothing anyone asks | Merge or retire it |
| Questions about what the product cannot do | A product gap | Route to product with the count |
| The same person asking repeatedly | They are not ready to deliver | Practice and a teach-back |

### Sources

Opened and checked on 2026-11-23:

- Agency for Healthcare Research and Quality, [Use the Teach-Back Method (Health Literacy Universal Precautions Toolkit, Tool 5)](https://www.ahrq.gov/health-literacy/improve/precautions/tool5.html).
- Hambrick, D. Z., Macnamara, B. N., & Oswald, F. L. (2020). Is the deliberate practice view defensible? A review of evidence and discussion of issues. *Frontiers in Psychology*, 11, 1134. [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC7461852). Quotes the original definition from Ericsson, Krampe and Tesch-Römer (1993), *Psychological Review*, 100(3), 363–406.
- Macnamara, B. N., & Maitra, M. (2019). The role of deliberate practice in expert performance: revisiting Ericsson, Krampe & Tesch-Römer (1993). *Royal Society Open Science*, 6(8), 190327. [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC6731745).

## Explaining it to your team

**How to explain it.** Lead with the number that replaced attendance. "All twelve
attended; four can give the demo without help. The drop is practice: nobody
who skipped practice passed a teach-back. So readiness is now how many people
can deliver alone, by role, and the next session goes to the partners, who
are at zero."

**The follow-up is usually "a teach-back feels like a test of my
colleagues".** It is a test of the material. The health-literacy method it
comes from says it directly: the person explaining is being checked, not the
person explaining back. When a teach-back fails, the first fix is to the demo
script or the guide, and that framing is what makes people willing to do one.

**The tradeoff to name.** Practice and teach-backs take time from people whose
calendars are full of customers, and the evidence for practice, while real, is
weaker than its popular version. Spend practice where it changes outcomes: the
demo people give most often, and the roles furthest from ready.

**One sharper point.** The field's questions are the earliest product signal a
team gets, and enablement is usually the only function that sees them all.
Counting them by topic and routing the product ones with the count attached is
the [working with engineers](working-with-engineers.md) habit applied to the
go-to-market side, and it is often the most valuable thing an enablement team
produces.

## Putting it into practice

**The work product.** A roster with practice and teach-back status, a month of
field questions tagged by topic and kind, a ranked self-service backlog, and a
product report with counts.

**Three things to do, in order:**

1. Run the golden path, then replace attendance in your own enablement report
   with teach-back passes by role. Expect the number to be under half.
2. Tag a month of office-hours questions by topic and kind, and write the
   resource for the topic with the most unanswered questions.
3. Send the product questions to product as a count by topic, every month,
   and record what happens to each.

**How to tell it is working.** The drill above runs in this guide's test suite
and its output is the output quoted here. The roster and questions are
invented and no teach-back has been observed, so the
[demonstrated](../demonstrated.md) page records the concept as partial. In your
own work, the sign is that office-hours questions shift from "how do I" to
"what if the customer asks", and that the people asking them can give the demo.

## Related

- [Demo design](demo-design.md), the demo the field delivers
- [Workshops and hands-on labs](workshops.md), the sessions that start enablement
- [Working with engineers as sources](working-with-engineers.md), the same habit on the engineering side
- [Repeat-question analysis](repeat-questions.md), the method behind the question counts
- [Multi-platform parity](multi-platform-parity.md), where the batch gap in the golden path is documented
