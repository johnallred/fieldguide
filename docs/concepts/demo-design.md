---
title: Demo design
summary: Designing a product demo as a performance with a time slot, an audience and a result to show first, and making sure someone other than its author can run it.
diataxis: explanation
audience: developer
concept: demo-design
tags: [edu, supporting]
---

# Demo design

`supporting` · difficulty 2 · 3h

> Building demos that show the result first, fit their slot, adapt to the audience, and still work when someone other than their author runs them.

**Prerequisites:** [Sample applications and galleries](sample-apps.md)

**Leads to:** [Field enablement](field-enablement.md)

## What it is

A demo is a performance of a product: a fixed slot, a particular audience, and
a sequence of live steps chosen to make one result land. A
[sample app](sample-apps.md) is something a reader clones and studies at their
own pace; a demo is something a presenter does in front of people, once, in
real time.

That changes what it optimizes for. A sample has to be complete and correct. A
demo has to be short, ordered around the moment that matters to this
audience, and recoverable when a live step fails, because in front of a room
there is no second attempt.

## How this applies to your role

This matters because developer education and enablement teams own demos, and demos are the
documentation most often seen by the people who decide whether to adopt the
product.

On a Tuesday it looks like this. The demo that always works when its author
gives it fails for the field engineer giving it to a customer. Step 3 reads
data from a folder on the author's laptop. Step 4 needs an environment
variable the author set months ago and forgot. The engineer improvises, runs
over time, and never reaches the part where the product survives a restarting
upstream, which was the only part the audience would have remembered. The demo
was fine; it was only ever tested by the person who wrote it.

The design half matters as much. Most demos are built in the order the product
works: context, configuration, setup, and finally the result. The audience
decides in the first minutes whether to pay attention, so the result arrives
after they have stopped. The well-known fix from sales engineering is to show
the result first and let the audience choose how deep to go, which is the
inverted pyramid of a news story applied to software.

## The golden path

Check a demo script and its last rehearsal against the failure modes above,
revise it, and check again. About twenty-five minutes.

The check is committed as `drills/demo_check.py`, which holds every file below
and a test that keeps them identical to this page. The demo and rehearsal are
invented.

**Step 1: the demo as a script, and its last rehearsal**

Each beat is `number | kind | minutes | command | fallback`. A persona variant
replaces one beat and shares the rest. The rehearsal was run by someone other
than the author, which is the only kind of rehearsal that tests anything.

```bash
mkdir -p demo-drill && cd demo-drill
cat > demo.txt <<'DATA'
title: Retries that survive a restarting upstream
slot: 10
setup: WIDGET_TOKEN
1 | context | 3 | open slides/architecture.pdf | -
2 | detail | 3 | widget config set retries 3 | -
3 | detail | 2 | widget sync --source /Users/jallred/demo-data | -
4 | payoff | 3 | widget sync --watch --upstream $FLAKY_UPSTREAM | -
5 | close | 1 | open slides/next-steps.pdf | -
variant data-engineer: 3 | detail | 2 | widget sync --source warehouse://demo | -
DATA
cat > rehearsal.csv <<'DATA'
beat,seconds,worked
1,210,yes
2,150,yes
3,95,no
4,240,no
5,50,yes
DATA
curl -sO https://raw.githubusercontent.com/johnallred/fieldguide/main/drills/demo_check.py
```

**Step 2: check it**

```bash
python3 demo_check.py demo.txt rehearsal.csv
```

```
ORDER     the result is beat 4; show it first
TIME      planned 12 minutes for a 10-minute slot
FALLBACK  live beat 2 has nothing to show if it fails
AUTHOR    beat 3 uses a path on the author's machine
FALLBACK  live beat 3 has nothing to show if it fails
AUTHOR    beat 4 needs $FLAKY_UPSTREAM, which setup does not provide
FALLBACK  live beat 4 has nothing to show if it fails
FALLBACK  live data-engineer beat 3 has nothing to show if it fails
REHEARSAL beat 3 failed in the last dry run
REHEARSAL beat 4 failed in the last dry run
REHEARSAL the dry run took 12.4 minutes
11 finding(s)
variant data-engineer: shares 4 of 5 beats
```

Read the two rehearsal failures against the rest. They are beats 3 and 4, the
same two the check flags as depending on the author's machine. The author never
saw them fail; the first person who was not the author did. Every other
finding is design: the result is shown fourth of five, the plan does not fit
the slot, and no live step has a recording to fall back on.

**Step 3: revise it**

The result moves to the front, the author's paths and variables become part of
the setup every presenter gets, every live beat gains a fallback, and the
architecture slides move behind the result for anyone who asks.

```bash
cat > demo.txt <<'DATA'
title: Retries that survive a restarting upstream
slot: 10
setup: WIDGET_TOKEN, FLAKY_UPSTREAM
1 | payoff | 2 | widget sync --watch --upstream $FLAKY_UPSTREAM | recordings/survives-restart.mp4
2 | detail | 2 | widget config set retries 3 | screenshots/config.png
3 | detail | 2 | widget sync --source ./demo-data | recordings/sync.mp4
4 | context | 1 | open slides/architecture.pdf | -
5 | close | 1 | open slides/next-steps.pdf | -
variant data-engineer: 3 | detail | 2 | widget sync --source warehouse://demo | recordings/warehouse.mp4
DATA
cat > rehearsal.csv <<'DATA'
beat,seconds,worked
1,130,yes
2,110,yes
3,100,yes
4,55,yes
5,45,yes
DATA
python3 demo_check.py demo.txt rehearsal.csv
```

```
0 finding(s)
variant data-engineer: shares 4 of 5 beats
```

The data-engineer variant changes one beat and keeps four, so updating the
shared beats updates both demos.

**What you built.** A demo that shows its result in the first two minutes,
fits its slot with room for questions, runs from a setup any presenter gets,
has something to show for every live step that fails, and was rehearsed by
someone who did not write it.

## Reference

### A demo is not a sample

| | Sample app | Demo |
|---|---|---|
| Used by | A reader, alone, at their own pace | A presenter, live, in front of an audience |
| Optimizes for | Completeness and correctness | One result landing in a fixed slot |
| Order | The order the code is built | The result first, detail on request |
| Fails by | Not running when cloned | Running over, burying the result, breaking live |
| Tested by | Running it in CI | Rehearsal by someone else, timed |

### Show the result first

| Beat | What it does |
|---|---|
| The result | The output the audience cares about: the job surviving, the dashboard, the report |
| The question | Ask how deep they want to go, and offer rather than push |
| The detail | Only the steps they asked about, most important first |
| The close | What to do next, with links they can follow alone |

This is the "do the last thing first" approach from Peter Cohan's *Great
Demo!*: start with the reports, deliverables and dashboards that a traditional
demo saves for the end, then go as deep as the audience asks.

### Persona variants from one spine

| Keep shared | Vary per persona |
|---|---|
| The setup and the environment | The data the demo runs on |
| The result's shape | Which result is shown first |
| The fallbacks for shared beats | The one or two beats that speak to their work |
| The close | The examples in the close |

### What the check enforces

| Rule | Catches |
|---|---|
| The first beat is the result | The result arriving after attention has gone |
| Planned minutes fit the slot | A demo that cannot end on time |
| No paths or variables only the author has | A demo only its author can run |
| Every live beat has a fallback | A broken step with nothing to show instead |
| The last rehearsal, by someone else, worked and fit | Everything the author cannot see |

### Sources

Opened and checked on 2026-11-23: Peter Cohan, author of *Great Demo!*, on
"do the last thing first" and the inverted pyramid, in an
[interview transcript](https://www.buzzsprout.com/1452916/16274198/transcript).

## Explaining it to your team

**How to explain it.** Lead with the person who is not the author. "Our demo
works every time I give it. It failed twice when a colleague rehearsed it, on the
two steps that read files and variables from my laptop. So setup is now
something every presenter gets, every live step has a recording behind it, and
a demo is not ready until someone other than its author has run it inside the
slot."

**The follow-up is usually "will showing the result first spoil the
story".** No, it creates the story. The audience now knows what they are
looking at and why each later step matters. A demo that saves the result for
the end is a mystery whose audience leaves before the reveal.

**The tradeoff to name.** Fallback recordings and shared setup are work that
pays off only on the day something breaks, and they go stale when the product
changes, so a recording of the old interface undermines the live parts. Keep
the fallbacks in the same repository as the demo and re-record them when the
rehearsal check fails, not on a schedule.

**One sharper point.** A demo's success is a reaction, which no script can
check. What can be checked is everything that prevents the reaction: a buried
result, an overrun, a broken step, a dependency on one laptop. Measure the
reaction separately, by what the audience asks afterwards. Questions about
their own data mean it landed; questions about what they just saw mean it did
not.

## Putting it into practice

**The work product.** One real demo rewritten as a script with timed beats and
fallbacks, checked, and rehearsed by someone who did not write it, with a
persona variant that shares every beat it can.

**Three things to do, in order:**

1. Run the golden path, then write your most-given demo as a script and run
   the check on it. Expect the result to be in the second half.
2. Ask someone else to rehearse it from the script alone, and time each beat.
   Predict which beat will fail before they start.
3. Record a fallback for every live beat, and store the recordings in the
   same repository as the script.

**How to tell it is working.** The drill above runs in this guide's test suite
and its output is the output quoted here. The demo and rehearsal are invented,
and no audience has reacted to anything, so the
[demonstrated](../demonstrated.md) page records the concept as partial. In your
own demos, the sign is that presenters other than the author give them without
calling the author first.

## Related

- [Sample applications and galleries](sample-apps.md), the clonable counterpart to a performed demo
- [Workshops and hands-on labs](workshops.md), the longer, hands-on form of the same live risk
- [Reproducible environments](reproducible-environments.md), the setup every presenter gets
- [Screencasts and video](screencasts.md), where fallback recordings come from
- [Learning science for developer education](learning-science.md), the problem-centred principle behind showing the result first
