---
title: Playbooks and decision guides
summary: "Turning what one person knows into a branching path other people can follow, and validating that every branch ends."
diataxis: how-to
audience: developer
concept: playbooks
tags: [ia, core]
---

# Playbooks and decision guides

`core` · difficulty 2 · 4h

!!! quote "Asked for by name"
    NVIDIA: "Capture tribal knowledge from engineering, product, and operations, and turn it into playbooks, decision guides, and self-service paths"

**Prerequisites:** [Interviewing subject-matter experts](sme-interviews.md)

## What it is

A page that branches. A tutorial takes one reader down one path; a playbook
asks what situation you are in and routes you accordingly. It is the right
shape for troubleshooting, for incident response, and for any question whose
honest answer is "it depends", because it makes the *depends* explicit.

The move that turns it from a document into infrastructure is writing the
branches as **data** rather than as prose. Then you can render the page and
validate the structure, which is the difference between a playbook and a wiki
page with a lot of nested bullets.

## Why the job asks for it

NVIDIA's bullet is the clearest statement of leverage anywhere in either
posting: capture what individuals know and turn it into self-service paths, so
fewer people have to ask "how do I…?".

The reason this needs a page of its own rather than being a kind of how-to is
that tribal knowledge is *conditional*. The expert does not know one procedure;
they know how to tell which of six situations they are in, and the
discriminating questions are the knowledge. Writing a linear how-to for each
branch loses the part that made the expert valuable, which is the routing.

It is also the output of [SME interviews](sme-interviews.md), which is why that
is the prerequisite rather than information architecture. You cannot write the
branches without having asked somebody "how do you know which one it is?"

## The golden path

Write a decision guide as data, then validate its structure. About thirty-five
minutes.

Committed as `drills/playbook.py`, which is the complete version of what
follows: this page prints the playbook in full and the validator in fragments,
so the output below used to come from a `check_playbook.py` that appears
nowhere. A test asserts the drill still prints what this page quotes, and that
the playbook it validates is the one below.

**Step 1: the branches, as data**

The subject is a real one: an integration has failed and you have to work out
why. This is the shape of knowledge a Boomi or ETL engineer carries around in
their head.

````bash
mkdir -p playbook-demo && cd playbook-demo
cat > playbook.yaml <<'EOF'
name: Integration is failing
entry: symptom
nodes:
  symptom:
    ask: What does the failure look like?
    options:
      - {answer: No data arrived at all, go: check-trigger}
      - {answer: Some records missing, go: check-filter}
      - {answer: Wrong values in the data, go: check-mapping}
  check-trigger:
    ask: Did the schedule fire?
    options:
      - {answer: "No", do: fix-schedule}
      - {answer: "Yes", go: check-auth}
  check-auth:
    ask: Are the credentials current?
    options:
      - {answer: "No", do: rotate-credentials}
      - {answer: "Yes", do: escalate-platform}
  check-filter:
    ask: Does the filter reference a field that was renamed?
    options:
      - {answer: "Yes", do: fix-filter}
      - {answer: "No", do: escalate-platform}
  check-mapping:
    ask: Is a dynamic process property set where you expect?
    options:
      - {answer: "No", do: trace-dpp}
      - {answer: "Yes", do: escalate-platform}
outcomes:
  fix-schedule: Re-enable the schedule and note why it was off.
  rotate-credentials: Rotate the token, then re-run the failed window.
  fix-filter: Update the filter to the current field name.
  trace-dpp: Find every get and set of the property, then correct the source.
  escalate-platform: Hand to the platform team with the trace attached.
  orphaned-outcome: Nothing routes here.
EOF
````

Note the shape. Every node is a **question with discriminating answers**, and
every path terminates in an outcome that says what to do. `escalate-platform`
appears three times, which is correct: "I have ruled out what I can" is a
legitimate destination and a playbook that pretends otherwise sends people in
circles.

**Step 2: the five things that can be wrong with it**

```python
# every `go` and `do` target resolves, and no option goes nowhere
for nid, node in nodes.items():
    for opt in node["options"]:
        if "go" in opt and opt["go"] not in nodes:
            problems.append(f"{nid}: 'go: {opt['go']}' is not a node")
        if "do" in opt and opt["do"] not in outcomes:
            problems.append(f"{nid}: 'do: {opt['do']}' is not an outcome")
        if "go" not in opt and "do" not in opt:
            problems.append(f"{nid}: option {opt['answer']!r} goes nowhere")

# every outcome is reachable
reached = {o["do"] for n in nodes.values() for o in n["options"] if "do" in o}
for oid in outcomes:
    if oid not in reached:
        problems.append(f"outcome {oid!r}: nothing routes here")

# every node is reachable from the entry
reachable, frontier = {entry}, [entry]
while frontier:
    for opt in nodes[frontier.pop()]["options"]:
        if opt.get("go") in nodes and opt["go"] not in reachable:
            reachable.add(opt["go"])
            frontier.append(opt["go"])
for nid in nodes:
    if nid not in reachable:
        problems.append(f"node {nid!r}: unreachable from {entry!r}")

# no cycles, because a decision guide that loops never ends
```

The node-reachability check is the same defect as the outcome one, a level up,
and it is the likelier of the two in a guide that has been edited for a year. A
question nobody can reach is a branch of the expert's knowledge that has
quietly left the playbook, and it is harder to notice by reading than an
orphaned outcome, because an unreachable node is perfectly well-formed on its
own.

**Step 3: run it**

```bash
python3 check_playbook.py
```

```
PLAYBOOK  outcome 'orphaned-outcome': nothing routes here
FAIL: 5 nodes, 6 outcomes, 1 problem(s)
```

One finding, which is the deliberately planted orphan. Remove it:

```
ok: 5 nodes, 5 outcomes, 0 problem(s)
```

**Step 4: confirm each defect class is caught**

Inject the other four, one at a time, and print every finding each produces:

```
  dangling-go  a target that does not resolve
    check-trigger: 'go: check-athu' is not a node
    node 'check-auth': unreachable from 'symptom'
  cycle        a path that never ends
    cycle: symptom -> check-trigger -> check-auth -> symptom
  dead-end     an option with no next step
    check-trigger: option 'No' goes nowhere
    outcome 'fix-schedule': nothing routes here
  unreachable  a question nobody can get to
    node 'check-retry': unreachable from 'symptom'
```

Five classes, five catches. Each is a specific way a prose playbook fails
silently:

| Defect | What a reader experiences |
|---|---|
| Orphaned outcome | Advice nobody can reach; usually the most interesting advice |
| Unreachable node | A question that has silently left the guide, taking its branch with it |
| Dangling target | "See the authentication section", which does not exist |
| Cycle | Being sent back to a question already answered |
| Dead-end option | An answer with no next step, so the reader is stuck |

Every one of those exists in prose troubleshooting guides and none is
detectable by reading, because reading follows one path at a time and these are
properties of the whole graph.

### A findings count is not a defect count

Two of those four injections report two findings, and both second findings are
consequences of the first.

Removing the `do` from `check-trigger`'s first option leaves that option
dangling **and** orphans `fix-schedule`, because that option was the only route
to it. Mistyping the `go` target breaks that edge **and** strands `check-auth`,
which nothing else routes to.

So four injected defects produce six findings, and two of the six vanish when
the other four are fixed. That matters the moment anybody plans work from the
number: a graph validator reports symptoms, and in a graph one broken edge
produces as many symptoms as there are properties that depended on it. The
repair list is shorter than the findings list, always, and the only way to know
how much shorter is to fix one and re-run.

This page used to show a single line per class, which hid both cascades. The
block above is what the validator actually prints.

**What you built.** A decision guide whose structure is checkable, the knowledge
that the cycle in step 4 is the failure readers complain about without being
able to name, and a worked reason to distrust findings counts.

## Reference

### When a playbook is the right shape

| Use a playbook | Use something else |
|---|---|
| The answer depends on observable conditions | One procedure, one audience: a how-to |
| An expert routes before acting | The task is linear |
| Troubleshooting, triage, incident response | Explaining why something works: an explanation |
| "It depends" is the honest answer | There is a single best path: a [golden path](golden-paths.md) |
| Several paths converge on an escalation | Nobody ever needs to escalate |

### The questions that make it work

A playbook's quality is in its discriminating questions, and the test for each
one is whether a reader can answer it **without already knowing the diagnosis**.

| Good question | Bad question |
|---|---|
| "Did the schedule fire?" | "Is the trigger misconfigured?" |
| "Are the credentials current?" | "Is this an auth problem?" |
| "Is the property set where you expect?" | "Is the mapping wrong?" |

The bad column asks the reader to make the determination the playbook exists to
help them make. This is the single most common defect in hand-written
troubleshooting guides, and no validator catches it: it needs a reader who does
not already know the answer.

### Getting it out of somebody's head

| Technique | Produces |
|---|---|
| Watch them do it, and write down the questions they ask | The branch structure |
| Ask "how do you know it is that and not the other thing?" | The discriminating questions |
| Ask for the last five times they were wrong | The branches a confident expert omits |
| Ask what they check first and why | The entry node |
| Ask when they give up and escalate | The terminal outcomes |

The third row is the one that improves a playbook most. Experts narrate their
successful path and omit the branches they have learned to skip, and those
skipped branches are exactly where a newcomer gets lost.

### Playbook as data, and what it buys

| Output | From the same file |
|---|---|
| A rendered page | Generated, so prose and structure cannot disagree |
| Structural validation | The four checks above |
| An interactive widget | Optional; the data supports it |
| An [agent skill](agent-skills.md) | A model can walk the graph rather than guess |
| Coverage measurement | Which outcomes fire most, from incident records |

The last two are why this is worth the extra work. A playbook as prose is a
page; a playbook as data is something an assistant can traverse, and the
routing is the part an assistant is otherwise worst at.

### Keeping one honest

| Rule | Why |
|---|---|
| Every path terminates | Checked above |
| Escalation is a real outcome | Pretending otherwise sends people round again |
| Questions are observable, not diagnostic | See the table above |
| Review it after an incident it failed to cover | The missing branch is now known |
| Date the outcomes | "Rotate the token" changes when the auth system does |

## How to talk about it

**Lead with the routing.** "Tribal knowledge is conditional. The expert does
not know one procedure, they know how to tell which of six situations they are
in, and the discriminating questions are the actual knowledge. A linear how-to
per branch loses exactly that, which is why these are decision guides and not
tutorials."

**The follow-up is how you keep one correct**, and the answer is to write the
branches as data and validate the graph: no dangling targets, no cycles, no
dead-end options, no unreachable outcomes. Four checks that catch failures no
amount of reading will, because reading follows one path and these are
properties of the whole structure.

**The tradeoff to volunteer.** A playbook as data costs you a generator and a
validator, and it makes casual editing harder: a contributor who wants to add a
sentence now has to understand a schema. On a guide with four branches that is
not worth it, and prose with a diagram is the better answer. It starts paying
when the graph is big enough that nobody can hold it in their head, which is
roughly the point at which it also stops being maintainable as prose.

**One sharper point.** The quality of a playbook is entirely in whether its
questions can be answered by someone who does not already know the answer.
"Is the trigger misconfigured?" is useless and extremely common; "Did the
schedule fire?" is useful. No validator catches that, which is why these need
testing with a reader who is genuinely stuck rather than review by the expert
who wrote them.

## How to prove it

**The artifact.** A playbook for something you actually know, as data, with the
four structural checks and a rendered page from the same source.

**Three things to do, in order:**

1. Run the golden path. Step 4 is worth doing in full, because the cycle
   finding is the reader complaint you have probably received without
   recognising it.
2. Take the thing colleagues ask you most often and write its branches. Not the
   procedure, the questions.
3. Give it to someone who does not know the answer and watch where they stop.
   That is the diagnostic-question defect, and it is the only way to find it.

**What makes it credible rather than decorative.** Neither of this guide's
repositories contains a playbook, which the
[demonstrated](../demonstrated.md) page records. The validator above is real
and runs, and the honest limit is that it checks structure only: it proves
every path ends somewhere, and it cannot tell you whether the questions are
answerable. Being clear about which half a tool covers is the point.

## Related

- [Interviewing subject-matter experts](sme-interviews.md), where the branches come from
- [Knowledge architecture](knowledge-architecture.md), the graph shapes compared
- [Agent skills and context kits](agent-skills.md), where a traversable playbook pays off
- [Golden paths](golden-paths.md), the opposite shape for a different problem
