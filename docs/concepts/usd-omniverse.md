---
title: OpenUSD and Omniverse
summary: "USD's whole model is a resolution order, and the surprising part is that the first sublayer wins, not the last."
diataxis: explanation
audience: developer
concept: usd-omniverse
tags: [dom, context]
---

# OpenUSD and Omniverse

`context` · difficulty 2 · 4h

!!! quote "Asked for by name"
    NVIDIA: "familiarity with USD, Omniverse, Isaac Sim, or ROS"

**Leads to:** [Robotics simulation](robotics-sim.md)

## What it is

OpenUSD is a scene description format and, more importantly, a **composition
engine**: several files each state opinions about the same objects, and USD
resolves them into one scene at read time. Omniverse is NVIDIA's platform built
on it, where the composition happens live across applications.

The format is the easy half. Everything that confuses people, and everything a
documentation role has to explain, is the resolution: when two files disagree,
which one wins.

`context` tier means the goal is to follow a conversation and know what you do
not know, not to ship scene code.

## Why the job asks for it

Because NVIDIA lists USD among the things to be familiar with, and because the
documentation failure around it is unusually clear-cut.

USD's reference material describes composition as a set of **arcs**:
sublayers, references, payloads, inherits, variant sets, specialises. Each is
documented accurately. A reader finishes knowing six mechanisms and still
cannot answer the only question they came with, which is why their override is
being ignored.

That gap is the documentable thing. The arcs are a feature list; the reader
needs an ordering.

## The golden path

Build a layered stage and find out which opinion wins. About twenty-five
minutes, and the second result is the one worth remembering.

```bash
pip install usd-core
```

**Step 1: a base asset, and an override that does not touch it**

```python
base = Usd.Stage.CreateNew("base.usda")
arm = UsdGeom.Cube.Define(base, "/Robot/Arm")
arm.GetPrim().CreateAttribute("payload_kg", Sdf.ValueTypeNames.Float).Set(2.5)

over = Usd.Stage.CreateNew("studio.usda")
over.GetRootLayer().subLayerPaths = ["./base.usda"]
ov = over.OverridePrim("/Robot/Arm")
ov.CreateAttribute("payload_kg", Sdf.ValueTypeNames.Float).Set(4.0)
```

```
base.usda        payload_kg = 2.5
studio.usda      payload_kg = 4.0   <- the override wins

base file on disk, unchanged:
          custom float payload_kg = 2.5
```

That is the point of the format in one result. A studio changes a vendor's
asset without editing the vendor's file, and the vendor can ship an update.

USD will also tell you exactly where a value came from, which is the single
most useful debugging call in the API:

```python
for spec in attr.GetPropertyStack(Usd.TimeCode.Default()):
    print(spec.layer.identifier, spec.default)
```

```
  studio.usda                  4.0
  base.usda                    2.5
```

**Step 2: two layers disagree, and the ordering is not what you expect**

Two sublayers, both setting `speed`, one to 10 and one to 20:

```python
root.GetRootLayer().subLayerPaths = ["./a.usda", "./b.usda"]
```

```
subLayerPaths = ['./a.usda', './b.usda']   a sets 10, b sets 20
  resolved speed = 10
  stack, strongest first:
    a.usda       10.0
    b.usda       20.0
```

```
subLayerPaths = ['./b.usda', './a.usda']   the same two files, reordered
  resolved speed = 20
```

**The first sublayer wins.** Not the last.

That is the opposite of nearly every ordering a developer already knows. CSS
later-wins, a shell `source` later-wins, `#include` later-wins, a dict update
later-wins, a Docker layer later-wins. Here the list is strongest-first, and a
reader who assumes otherwise has a scene that silently uses the wrong value,
with no error anywhere.

**Step 3: a local opinion beats a reference**

```python
inst.GetPrim().GetReferences().AddReference("./asset.usda", "/Asset")
```

```
reference only:          mass = 100
local opinion added:     mass = 7   <- local beats the reference
```

This is the LIVRPS ordering: **L**ocal, **I**nherits, **V**ariant sets,
**R**eferences, **P**ayloads, **S**pecialises, strongest first. Six arcs, one
order, and knowing the acronym answers the override question that the six
individual arc pages do not.

**Step 4: what this says about documenting it**

The reference material was accurate throughout. What was missing is a page that
leads with the order and demonstrates the counter-intuitive case, because the
counter-intuitive case is the one that generates the support question.

A [golden path](golden-paths.md) for USD is three files and one printed
resolution, and it is worth more than six accurate arc pages. That is the
general shape of this problem. A reader whose mental model is wrong in one
specific way needs that specific correction, and complete reference material
will not deliver it.

**What you built.** A layered stage, an override that leaves its base file
untouched, the resolution order printed from the API, and the one ordering fact
most newcomers get backwards.

## Reference

### The arcs, in strength order

| Arc | Use | Mnemonic position |
|---|---|---|
| Local opinions | Direct edits in this layer | L, strongest |
| Inherits | Class-like shared edits | I |
| Variant sets | Switchable alternatives | V |
| References | Pulling in another asset | R |
| Payloads | References you can defer loading | P |
| Specialises | Fallbacks that stay weaker | S, weakest |

Within the local layer stack, earlier sublayers are stronger. Both orderings
have to be known; neither is guessable.

### References against payloads

| | Reference | Payload |
|---|---|---|
| Loaded | Always | On request |
| Use for | Composition you always need | Heavy geometry |
| Cost | Paid at open | Deferred |

A scene that opens slowly is usually references where payloads belong, and that
is the commonest performance question in USD documentation.

### Terms worth recognising

| Term | Means |
|---|---|
| Prim | A node in the scene hierarchy |
| Attribute, relationship | A prim's typed value, or its link to another prim |
| Stage | The composed result of one or more layers |
| Layer | One file of opinions, `.usda` text or `.usdc` binary |
| Opinion | A value stated by a layer, which may lose |
| Over | An edit to a prim defined elsewhere |
| Schema | A typed API over prims, such as `UsdGeom` |
| Stage traversal | Walking the composed hierarchy |

`.usda` is text and diffable; `.usdc` is binary and is not. For documentation
work, always show `.usda`.

### Where Omniverse sits

| Layer | What it is |
|---|---|
| OpenUSD | The open format and composition engine |
| Omniverse Kit | NVIDIA's application framework over USD |
| Connectors | Live sync between Omniverse and other tools |
| Isaac Sim | A robotics simulator built on Kit |

Being clear about this boundary matters in writing: a reader's problem is often
with USD and not with the vendor platform, or the reverse, and the two have
separate documentation sets and separate failure modes.

### What usually goes wrong

| Symptom | Cause |
|---|---|
| "My override is ignored" | Sublayer ordering, or a weaker arc |
| "The value changed when I added a file" | A stronger opinion appeared |
| "It works for me and not in the pipeline" | A different layer stack |
| "The scene takes a minute to open" | References where payloads belong |
| "The diff is unreadable" | `.usdc` instead of `.usda` |

Every row is a resolution question, which is the argument for leading the
documentation with resolution.

## How to talk about it

**Lead with composition rather than the format.** "USD is a scene format and
really a composition engine: several files state opinions about the same
objects and USD resolves them at read time. So a studio can override a vendor's
asset without touching the vendor's file, and the vendor can still ship
updates. The format is the easy half."

**The concrete thing to bring.** The first sublayer wins, not the last. I
checked it by building two layers that disagree and reordering them, and the
resolved value flips. That is the opposite of CSS, `#include`, shell `source`
and Docker layers, so a developer's existing intuition is reliably wrong in one
specific direction, and they get a silently incorrect scene rather than an
error.

**The documentation point, which is the reason this is worth discussing in an
interview.** USD's reference material documents six composition arcs
accurately, and a reader finishes it able to name all six and unable to answer
why their override is ignored. The arcs are a feature list; what the reader
needs is the resolution order, LIVRPS, plus a demonstration of the
counter-intuitive case. Three files and one printed resolution beat six
accurate arc pages, and `GetPropertyStack` prints exactly where a winning value
came from, which is the first thing I would put in a troubleshooting page.

**Be honest about the depth.** I have composed layers, resolved overrides and
read the API; I have not shipped a production scene graph, tuned payload
loading on heavy assets, or used Omniverse itself. For this role that is the
right amount: enough to write the page that is missing and to know which
questions to take to an engineer.

## How to prove it

**The artifact.** Three `.usda` files and a script that prints the resolution
order, which fits in a gist and demonstrates the thing newcomers get wrong.

**Three things to do, in order:**

1. Install `usd-core` and run step 2. Predict which sublayer wins before you
   run it; the prediction is the exercise.
2. Call `GetPropertyStack` on an attribute with more than one opinion. It is
   the answer to most USD support questions and it is not where a newcomer
   looks.
3. Write the paragraph that states the resolution order and names the
   intuition it violates. It is the page that does not exist.

**What makes it credible rather than decorative.** Every result above was
executed against `usd-core` 0.26.11 on this machine, and the files are three
short scripts. What is absent is the platform: no Omniverse, no Kit, no live
Connector, no heavy asset, and no production pipeline, so this is familiarity
with the composition model rather than experience of the product. The
[demonstrated](../demonstrated.md) page records it that way, and `context` tier
is the honest claim.

## Related

- [Robotics simulation, Isaac Sim and ROS](robotics-sim.md), the platform built on this
- [Golden paths](golden-paths.md), the shape the USD documentation is missing
- [Diátaxis](diataxis.md), why a reference set alone left the reader stuck
- [Real-time and graphics systems](realtime-systems.md), the neighbouring domain
