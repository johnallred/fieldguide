---
title: Workshops and hands-on labs
summary: "A three-hour workshop covers about one step of a thirty-four-hour path, so the design question is which step genuinely needs a room."
diataxis: how-to
audience: developer
concept: workshops
tags: [edu, supporting]
---

# Workshops and hands-on labs

`supporting` · difficulty 2 · 4h

!!! quote "Adjacent, not quoted"
    Neither posting mentions workshops. A standard developer-relations deliverable, and the only setting where you can watch a reader fail.

**Prerequisites:** [Learning paths and curriculum](learning-paths.md), [Reproducible environments](reproducible-environments.md)

## What it is

A fixed block of time in which a group works through material together, with
someone present who can unblock them. The defining constraint is not the
content, it is **synchrony**: everyone has to be at the same place at the same
time, so the slowest person sets the pace and any environment failure strands
one attendee while the room moves on without them.

Everything that makes workshop design different from writing a tutorial
follows from that constraint.

## Why the job asks for it

Two reasons, and only one of them is about teaching.

The honest teaching reason is that a room is the only place you can watch
people fail. [Assessment](assessment.md) over a corpus tells you whether your
tasks are well formed; it cannot tell you where readers get stuck. Twenty
people attempting your quickstart in front of you produces that information in
forty minutes, and it is the highest-quality signal available anywhere in this
job.

The other reason is that workshops are a developer-relations deliverable with a
conference schedule attached, which means the date is fixed before the content
exists. Worth naming, because it drives the characteristic failure: a workshop
scoped as though it were a tutorial, discovered on the morning to be three
times too long.

## The golden path

Measure the two things that decide whether a workshop works: what the
environment costs, and how much material fits. About thirty minutes, and both
numbers are worse than people expect.

The second half is committed as `drills/workshop_arithmetic.py`, which computes
it from the registry rather than quoting a figure. The first half is not, and
cannot be: it needs a network, a stopwatch and a particular machine, and the
numbers below are one run on one of them. Treat the shape as the claim and the
seconds as an anecdote.

**Step 1: time the setup, in ideal conditions**

This is a quiet cloud machine with a warm package index and a fast link, which
no attendee will have. Nothing checks these seconds, so do not reuse them:

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install mkdocs mkdocs-material pyyaml pytest
```

```
venv_create_s=3
pip_upgrade_s=3
deps_install_s=14
packages_installed=34
bytes_on_disk=94697572
first_build_s=0  rc=0
total_s=21
```

Twenty-one seconds. The number that matters is underneath it:

```
requested=4   installed=34
```

**Four packages asked for, thirty-four installed.** The failure surface of this
workshop is thirty-four independent resolutions, not four, and every one can
resolve differently on an attendee's laptop depending on their Python version,
their existing site-packages, their corporate proxy, and what pip decides is
newest that morning.

Ninety-five megabytes per attendee, times a room.

**Step 2: remove the network from the room**

The mitigation is to resolve the dependency graph once, in advance, and ship
the result:

```bash
pip download --dest wheelhouse mkdocs mkdocs-material pyyaml pytest
pip install --no-index --find-links wheelhouse mkdocs mkdocs-material pyyaml pytest
```

```
wheelhouse_build_s=2   files=33   bytes=28411989
offline_install_s=6    rc=0       packages=34
```

Six seconds instead of fourteen, 28 MB on a stick or on a laptop serving the
room, and, more importantly, **the same thirty-four packages for everybody**.
The resolution happened once, on a machine you could inspect.

That last property is the whole value. Speed is a bonus; determinism is the
reason, because a workshop where two attendees have different transitive
dependencies is a workshop where you debug one laptop while eighteen people
watch.

**Step 3: the arithmetic that kills most workshop plans**

This guide's [first-week path](../paths/first-week.md) is ten concepts.
`drills/workshop_arithmetic.py` reads them out of the registry, so the numbers
below are the current ones rather than the ones that were true when this page
was written:

```
  Technical writing as a craft                     8h
  Treating docs, setup and samples as one product  3h
  Docs-as-code                                     2h
  Markdown and its dialects                        2h
  Git authoring workflows for writers              4h
  Diátaxis                                         2h
  Choosing a static site generator                 3h
  MkDocs and Material                              4h
  Link checking                                    2h
  Documentation CI                                 4h
                                            total 34h
```

A three-hour workshop, after setup and questions, offers perhaps two hours of
hands-on time.

```
two hours against the 34-hour first-week path: 6%
shortest path in the guide: domain-context, 6 concepts, 24h (8%)
concepts in this corpus of 3h or less: 48/106
```

That second line is here because of a mistake. This page used to call
first-week the shortest path in the guide, which it was, until a six-concept
domain path was added and took the title by ten hours. The claim was prose, the
answer was in `concepts.yaml`, and nothing connected them, so the page was
wrong for as long as it took somebody to compute it. The drill now prints the
shortest path by name and a test compares it to this block, which is the only
reason the sentence you are reading is true.

Note which direction the correction goes. The shortest path in the guide is
twenty-four hours, so two hours of hands-on time is eight percent of it rather
than six. The superlative was wrong and the argument got worse.

**A three-hour workshop covers about one step of a ten-step path.** Not a
compressed version of the path. One step of it.

Most workshop abstracts promise the path. The abstract is written in June for a
conference in October, it says "learn to build and ship a documentation
pipeline", and in October somebody tries to deliver thirty-four hours in three.

**Step 4: the design consequence**

If a workshop is one step, the only question worth asking is **which step needs
a room**, and the answer is not the most important step.

```
Needs a room:   failure is confusing, recovery needs judgment, and
                seeing the person next to you helps
Does not:       mechanical, well documented, succeeds first time
```

On this path, "Documentation CI" needs a room, because its failures are
environmental and a stuck attendee cannot read their way out. "Markdown and its
dialects" does not, however foundational, because a page explains it perfectly
and nobody gets stuck.

That inverts the usual instinct, which is to start at step 1 and get as far as
possible. Starting at step 1 spends the room's scarce resource, a person who
can unblock you, on the material least likely to need one.

**Step 5: what to do with the other nine steps**

Send them. A workshop that covers one step well and hands out a path for the
rest is honest; a workshop that gallops through ten produces twenty people with
a broken environment and a folder they will not reopen.

The handout is the artifact that survives the room, which is the argument for
having the written path exist first. A workshop built on top of a curriculum is
an afternoon's work. A workshop that *is* the curriculum gets rebuilt every
time it is delivered.

**What you built.** A measured setup cost of 34 packages and 95 MB per
attendee, an offline wheelhouse making it deterministic in six seconds, and the
arithmetic showing a three-hour workshop is one step of a ten-step path.

## Reference

### A three-hour block, honestly budgeted

| Minutes | Spent on | Notes |
|---|---|---|
| 20 | Environment, including the two people it fails for | Always; plan it rather than absorb it |
| 10 | What we are building and why | Shorter than you want it to be |
| 100 | The hands-on material | The entire teaching budget |
| 20 | Questions, and the slowest finishers | Not optional |
| 30 | Overrun nobody planned | Something will go wrong |

The last row is the one people leave out, and it is why workshops overrun,
rather than any individual mistake inside them.

### Environment strategies

| Strategy | Cost in the room | Determinism | Fails when |
|---|---|---|---|
| "Install these four packages" | 15 to 40 minutes | None | Always, for somebody |
| Wheelhouse on a stick or local server | Under a minute | High | Someone has the wrong Python |
| Container image, pre-pulled | Under a minute | Very high | Docker is absent or disallowed |
| Hosted environment per attendee | Zero | Total | The venue wifi dies |
| Attendees set up beforehand | Zero, for the prepared | None | Half of them do not |

The last row is the plan most workshops actually have, and the honest reading
is that it is not a plan. Pair it with one of the others.

### What needs a room

| Needs it | Does not |
|---|---|
| Failure modes that are confusing | Anything that works first time |
| Judgment calls with no single right answer | Mechanical procedure |
| Work people will not start alone | Work they will happily read |
| Anything where watching a neighbour helps | Reference material |
| Material where *you* need to watch them | Material you already have feedback on |

The bottom-right cell is the trap: well-understood material is the most
comfortable thing to teach and the least worth the room.

### Workshop against the alternatives

| | Tutorial page | Screencast | Workshop |
|---|---|---|---|
| Pace | The reader's | The video's | The slowest attendee's |
| Scales | Indefinitely | Indefinitely | 20 to 30 |
| Cost per delivery | Nothing | Nothing | A day |
| Shows where people stick | No | No | Yes, immediately |
| Survives the day | Yes | Yes | Only the handout does |

The fourth row is why workshops earn their cost even when the teaching is
mediocre, and the fifth is why the handout matters more than the slides.

### Failure modes

| Failure | Prevention |
|---|---|
| Setup eats an hour | Step 2, plus a greeter who starts people early |
| Scoped as a path, delivered as a sprint | Step 3's arithmetic, before the abstract |
| One broken laptop stops the room | A spare hosted environment, and permission to move on |
| Everyone finishes at a different time | A stated stretch task for the fast |
| Nobody asks anything | A planted checkpoint question, not an invitation |
| The material exists only as slides | Write the path first |

## How to talk about it

**Lead with the arithmetic, because it is the thing nobody has done.** "A
three-hour workshop has about two hours of hands-on time, and the shortest path
through my curriculum is thirty-four hours. So a workshop is one step of a
ten-step path rather than a compressed version of it, and the design question
becomes which step needs a room, not how fast I can go."

**The follow-up is usually environments, and this is where the numbers are.** I
asked for four packages and got thirty-four installed, 95 MB per attendee:
thirty-four independent resolutions that can differ on somebody's laptop. So I
resolve once in advance and ship a wheelhouse, 28 MB, six seconds, offline, and
the same thirty-four packages for everybody. Speed is a bonus; determinism is
the reason, because the alternative is debugging one laptop while eighteen
people watch.

**The non-obvious design point.** The step that needs the room is rarely the
most important one. It is the one where failure is confusing and recovery needs
judgment. Foundational material that a page explains perfectly is the most
comfortable thing to teach and the worst use of the only resource a workshop
has.

**The tradeoff to volunteer.** A workshop costs a day and reaches twenty
people; a page costs a day and reaches thousands. The honest justification is
not teaching efficiency, it is that a room is the only place I get to watch
people fail, and that is feedback no analytics produce. A team running one
workshop a quarter purely to collect it, and publishing a page from what it
learned, would be making the right trade.

## How to prove it

**The artifact.** A wheelhouse or image that installs offline, a timed run of
it, and a workshop plan whose hands-on minutes are written next to the hours of
material it claims to cover.

**Three things to do, in order:**

1. Run `pip download` against your own workshop's dependencies and count the
   files. Write your prediction down first; the gap between four and thirty-four
   is this page's whole subject.
2. Take your next workshop abstract and divide its promised scope by two hours
   of hands-on time. A ratio much over one means the abstract is already wrong,
   and it is far cheaper to fix in June than in October.
3. Ask which step of your material genuinely needs a person in the room. If the
   answer is "all of it", the material has not been written down yet, and
   writing it is the actual task.

**What makes it credible rather than decorative.** The setup measurements were
executed: 34 packages and 94,697,572 bytes from four requested, a wheelhouse of
33 files and 28 MB built in two seconds, an offline install in six. The path
arithmetic comes from this guide's own registry. What has not happened is a
workshop, so the claims about what needs a room are reasoning from the design
rather than observation, and the [demonstrated](../demonstrated.md) page
records workshops as having no demonstration in either repository.

## Related

- [Learning paths and curriculum](learning-paths.md), the thing a workshop takes one step from
- [Reproducible environments](reproducible-environments.md), the mechanism behind step 2
- [Assessment and checks for understanding](assessment.md), what the room is really for
- [Screencasts and video](screencasts.md), the asynchronous substitute and its limits
- [Developer advocacy](developer-advocacy.md), where the fixed conference date comes from
