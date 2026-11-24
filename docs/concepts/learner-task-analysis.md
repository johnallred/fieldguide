---
title: Learner and task analysis
summary: Finding out what readers actually do and already know before writing a single objective, and noticing when the fix is not teaching at all.
diataxis: explanation
audience: developer
concept: learner-task-analysis
tags: [edu, core]
---

# Learner and task analysis

`core` · difficulty 2 · 5h

> Finding out who your readers are and what they actually do before deciding what any tutorial, lab or course should teach.

**Prerequisites:** [Learning science for developer education](learning-science.md)

**Leads to:** [Instructional design for developers](instructional-design.md)

## What it is

The analysis that comes before design: what tasks readers actually perform,
what decisions those tasks involve, what readers already know, and which of
their problems are not knowledge problems at all. Its output is the list of
objectives; everything in [instructional design](instructional-design.md)
assumes that list is right.

It has two halves. **Task analysis** breaks the work into steps and decisions.
**Learner analysis** describes the people doing it: their prior experience,
their setting, and what they are trying to get done.

## How this applies to your role

This matters because objectives written from the product's feature list describe what the
product can do, not what readers need to do with it, and the difference shows
up later as support tickets.

On a Tuesday it looks like this. You are asked to write a tutorial on retries.
The engineer who built the feature walks you through it in ten minutes, and it
sounds complete: set the argument, pick a value, done. Then you sit with a
developer who is actually using it and watch them stop three times, each time
at a decision the engineer never mentioned: is anyone waiting on this request,
is that 429 a rejection or an outage, is the retry budget shared across
workers. The engineer is not hiding anything. They stopped noticing those
decisions years ago, which is the most consistent finding in this research.

The second half of the job is saying no. Some tasks readers struggle with are
not knowledge gaps: the console hides the button, the error message points at
a broken link, the package does not install on their platform. Writing a
tutorial for those spends a week teaching around a defect that an engineer
could fix in an afternoon. Analysis is where you find that out before the week
is spent.

## The golden path

Build a task inventory from an expert and from observation, weigh it against
real support questions and a reader survey, and turn the result into
objectives. About forty minutes.

The analysis is committed as `drills/task_analysis.py`, which holds the three
files below and a test that keeps them identical to this page. The tickets and
survey counts are invented for the exercise; the arithmetic over them is real.

**Step 1: an inventory, from what the expert said and what you watched**

Each task lists steps (`-`) and decision points (`?`), tagged with where each
came from. Write the `[said]` lines during the interview, then add the
`[observed]` ones while watching someone new do the task.

```bash
mkdir -p ta-drill && cd ta-drill
cat > tasks.txt <<'TXT'
T1 configure retries | taught | high
  - set retries on the client [said]
  - pick a value for the workload [said]
  ? is a caller waiting on the response [observed]
  ? does the upstream restart during deploys [observed]
T2 diagnose an exhausted retry budget | not taught | high
  - read the status code in RetryExhausted [said]
  ? is it 429 (rejected) or 503 (down) [observed]
  ? is the budget shared across workers [observed]
  - check the upstream status page [observed]
T3 rotate the API key | not taught | medium
  - open the key page in the console [said]
  - create the new key [said]
  ? which key is production using right now [observed]
  - deploy the new key before revoking the old [observed]
T4 install the client | taught | low
  - pip install widget-client [said]
  ? is the Python version supported [observed]
TXT
```

**Step 2: what readers ask, and who they are**

Each ticket is tagged with its task and its cause: `knowledge` if the reader
did not know how, `environment` if the product or setup got in the way.

```bash
cat > tickets.txt <<'TXT'
T2 knowledge | gave up after 3 retries, is the service down?
T2 knowledge | RetryExhausted 429, what does that mean
T2 knowledge | retries do nothing when every worker fails at once
T2 knowledge | how do I tell rejected from unavailable
T2 knowledge | job stops at night with RetryExhausted
T2 environment | status page link in the error is broken
T2 knowledge | 429 after raising retries to 10
T2 knowledge | should I raise retries when I see 503
T3 environment | cannot find where to create a key
T3 environment | console shows two keys, which is live?
T3 environment | key page times out
T3 knowledge | revoked old key and production broke
T3 environment | new key not shown after creating it
T3 environment | no way to label keys in the console
T1 knowledge | does retries=3 mean three requests?
T1 knowledge | what retry value for a web request
T1 knowledge | retries make my API endpoint slow
T4 environment | pip install fails on Python 3.8
T4 environment | wheel not available for my platform
TXT
cat > survey.txt <<'TXT'
never used a client with retries | 11
used retries in another client | 23
used retries in this client | 6
TXT
curl -sO https://raw.githubusercontent.com/johnallred/fieldguide/main/drills/task_analysis.py
```

**Step 3: run the analysis**

```bash
python3 task_analysis.py tasks.txt tickets.txt survey.txt
```

```
step 1: what the expert said, against what was observed
  steps the expert described:     6/8
  decisions the expert described: 0/6

step 2: which tasks readers struggle with, and why
  task                                    tickets  knowledge  taught  action
  T2 diagnose an exhausted retry budget      8      7/8      no      teach it
  T3 rotate the API key                      6      1/6      no      fix the product, not the page
  T1 configure retries                       3      3/3      yes     keep, check it works
  T4 install the client                      2      0/2      yes     fix the product, not the page

step 3: who the readers are
  never used a client with retries    11  (28%)
  used retries in another client      23  (58%)
  used retries in this client          6  (15%)
  already used retries somewhere: 29/40 (72%)
```

**Step 4: read each finding as a decision**

The expert described six of eight steps and none of the six decisions. Every
decision in the inventory came from watching someone, which is why an
interview alone is not an analysis.

Key rotation has six tickets and is not taught, which looks like the next
tutorial to write. Five of the six are about the console: a hidden button, a
page that times out, two unlabelled keys. That is an obstacle, not a knowledge
gap, and the fix is a bug report to the console team with these tickets
attached. The one knowledge ticket (revoking the old key first) becomes a
single warning on an existing page.

Installation is the same case, smaller. Configuring retries is taught and
still produces three knowledge tickets, so the existing tutorial is not
working, and that is a question for [assessment](assessment.md), not for a new
page.

**Step 5: write the objectives the analysis supports**

Diagnosing an exhausted retry budget gets the new tutorial, and its objectives
come from the inventory, decisions included:

```
O1  Configure retries on the client
O2  Choose a retry count for a workload  (is a caller waiting? does it restart?)
O3  Diagnose a retry budget that is exhausted  (429 or 503? shared budget?)
```

Those are the three objectives the [learning science](learning-science.md)
drill audits. The survey changes one more thing: 72 per cent of readers have
used retries before, so the tutorial needs a route past the basics for them,
because support that helps a newcomer can slow down someone who already knows.

**What you built.** A task inventory with every decision attributed to its
source, a ranked list of tasks with a cause behind each, two problems routed
to the product team instead of to a tutorial, and three objectives grounded in
what readers do.

## Reference

### Task analysis methods

Five families, from the standard handbook on the subject:

| Family | Breaks the work into | Use it when |
|---|---|---|
| Job or behavioural analysis | Observable steps | The task is a procedure |
| Learning analysis | Prerequisite skills in order | You need to sequence a path |
| Cognitive task analysis | Decisions, cues and judgements | Experts disagree with novices about what is hard |
| Activity-based analysis | The task in its real setting | Tools, people and constraints shape the work |
| Subject matter analysis | Concepts and their relations | The content is knowledge rather than a task |

### Where the information comes from

| Technique | Finds | Misses |
|---|---|---|
| Expert interview | Steps, vocabulary, the official route | Most decisions; what has become automatic |
| Observation of a newcomer | Where people stop, every decision | Why the expert does it that way |
| Think-aloud | The reasoning at each decision | Speed; people slow down when narrating |
| Support tickets and search logs | What readers struggle with at scale | Everyone who gave up without asking |
| Existing documentation | The current claims | Whether anyone could follow them |
| Survey | Prior experience and setting, at scale | Anything respondents cannot report about themselves |

### Is it a teaching problem?

The performance-analysis questions, adapted to documentation:

| Question | If the answer is no |
|---|---|
| Does the problem matter? | Leave it |
| Is it a knowledge or skill gap? | Look at the environment instead |
| Did they never know it, or know it and forget? | Never knew: teach it. Forgot: a reference page or a reminder |
| Is something in the way? | Remove the obstacle: fix the console, the error, the install |
| Is doing it right punished, or doing it wrong rewarded? | Change the incentive, not the page |

### Learner analysis, the questions that change a design

| Question | What it changes |
|---|---|
| What have they already done? | Whether an expert route is needed |
| Where will they do this? | Laptop, locked-down workstation, cloud shell, lab |
| What are they trying to finish? | The task that frames the whole tutorial |
| What vocabulary do they arrive with? | Headings, search terms, the names you use |
| How much time do they have? | Tutorial, quick reference, or a course |

### Sources

Opened and checked on 2026-11-23:

- Jonassen, D. H., Tessmer, M., & Hannum, W. H. (1999). *Task Analysis Methods for Instructional Design*. Routledge. [Publisher page](https://www.routledge.com/Task-Analysis-Methods-for-Instructional-Design/Jonassen-Tessmer-Hannum/p/book/9780805830859).
- "The use of cognitive task analysis to reveal the instructional limitations of experts in the teaching of procedural skills." *Academic Medicine*, 89(5), 811–816 (2014). Three experts teaching one procedure omitted 73 per cent of its decision steps. [PubMed](https://pubmed.ncbi.nlm.nih.gov/24667500/).
- Yates, K. A., Feldon, D. F., & Clark, R. C. (2011). Using cognitive task analysis to capture expert knowledge and skills for research and instructional design. Workshop, AERA annual meeting. Its abstract states that experts omit about 70 per cent of their decisions; it is a workshop abstract, not a study. [Record](https://digitalcommons.usu.edu/itls_facpub/454).
- Mager, R. F., & Pipe, P. *Analyzing Performance Problems* (2nd ed., 1984). Lake Publishing. Flowchart as adapted by [Nova Southeastern University](https://app.nova.edu/toolbox/instructionalproducts/8001/EDD8001/SUM12/perf_problems_flowchart.pdf).

## Explaining it to your team

**How to explain it.** Lead with the decision count. "The engineer described
six of the eight steps and none of the six decisions. Every decision came from
watching someone use it. That is normal, not a criticism: experts stop
noticing their own decisions, and decisions are exactly where readers get
stuck. So an interview tells me where to look, and watching someone tells me
what to teach."

**The follow-up is usually "we do not have time for analysis".** The answer is
that it is cheaper than the alternative, and the golden path shows why: two of
the four tasks turned out not to need a tutorial at all. An hour reading
tickets is cheaper than a week writing a page around a console defect, and the
bug report it produces helps every reader, not only the ones who find the
page.

**The tradeoff to name.** Every source is partial. Tickets come only from
people who asked, surveys report what people believe about themselves, and
observation of one or two people can mislead as easily as an interview. The
defence is to combine sources and to treat the result as a hypothesis the
tutorial's own [assessment](assessment.md) will test, not as a finding.

**One sharper point.** The most valuable output of an analysis is often a
tutorial that does not get written. Documentation teams are measured on pages,
so "this is a product defect" feels like failing to deliver. It is the
opposite: a bug report backed by six tickets fixes the problem for every
reader at once, and documentation that routes problems to the right owner is
doing the job the [systems mindset](systems-mindset.md) page describes.

## Putting it into practice

**The work product.** A task inventory for one real feature, with every step
and decision attributed to an interview or an observation, crossed with a
month of real tickets, ending in objectives and a list of problems sent to
their owners.

**Three things to do, in order:**

1. Run the golden path, then interview an expert about one real task and write
   down only what they say. Predict how many decisions they will mention before
   you start, then count them; expect fewer than half of what step 2 finds.
2. Watch one person new to that task attempt it without help. Add every
   decision where they stopped, and compare the counts.
3. Tag a month of tickets for that feature by cause. File every `environment`
   cluster as a bug with the tickets attached before writing any page.

**How to tell it is working.** The drill above runs in this guide's test suite
and its output is the output quoted here, so the method is demonstrated. The
data is not real: the tickets and survey are invented, so nothing here shows
the method's findings on an actual product, and the
[demonstrated](../demonstrated.md) page records the concept as partial on that
basis. In your own work, the sign is fewer tutorials written per quarter and
fewer tickets on the tasks you did teach.

## Related

- [Extracting tribal knowledge](sme-interviews.md), the interview half of the inventory
- [Learning science for developer education](learning-science.md), why the expert route and the decisions matter
- [Instructional design for developers](instructional-design.md), what the objectives feed
- [Repeat-question analysis](repeat-questions.md), the ticket source at scale
- [Search and query log analysis](search-log-analysis.md), the other record of what readers try to do
