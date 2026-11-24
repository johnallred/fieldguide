---
title: Knowledge architecture
summary: "Structuring what is known rather than where pages live, and auditing the dependency graph against itself."
diataxis: explanation
audience: developer
concept: knowledge-architecture
tags: [ia, core]
---

# Knowledge architecture

`core` · difficulty 3 · 6h

> Working with documentation leads on how knowledge is organized across products, teams and sources.

**Prerequisites:** [Information architecture](information-architecture.md)

## What it is

[Information architecture](information-architecture.md) organizes **pages**:
where they live, how they are labeled, how a reader navigates between them.
Knowledge architecture organizes **what is known**: the concepts, their
relationships, which depend on which, and which are load-bearing.

The distinction matters because the two can disagree. A page can sit in the
obvious place in a navigation tree while the thing it explains depends on four
concepts a reader has not met. Information architecture will not tell you that.
A dependency graph will.

## How this applies to your role

The relationship is usually precise: you **collaborate** with documentation
leads on it, and your contribution is **implementation feedback**, what works,
breaks and scales. The architecture is owned jointly; what you bring is
evidence from having built it.

That framing tells you what the work is not. You are not there to design a
taxonomy in isolation and hand it over. You implement an architecture, find out
where it breaks at scale, and feed that back. Which
means the valuable skill is **measuring an architecture**, and that is what the
golden path does.

It also explains why this concept is difficulty 3 while information
architecture is 2. Organizing pages is a judgment you can make by reading them.
Organizing knowledge requires making the relationships explicit enough to
compute over, and then being willing to find out that your own structure
disagrees with itself.

## The golden path

Audit a real knowledge architecture against its own graph. About forty-five
minutes. Every number below comes from this guide's registry.

**Step 1: make the relationships data**

This guide's knowledge architecture is 120 concepts with a prerequisite edge
wherever one concept assumes another, a tier recording how much of the
reader's time each may claim, and a category for grouping. The prerequisites
are the graph:

```python
from fieldguide.registry import load_registry, topological_order

reg = load_registry(Path("concepts.yaml"))
indeg = {c.id: len(c.prerequisites) for c in reg.concepts}
outdeg = collections.Counter()
for c in reg.concepts:
    for p in c.prerequisites:
        outdeg[p] += 1
```

```
nodes: 120   edges: 138
roots (no prerequisite):   17
leaves (nothing needs it): 58
```

Fifty-eight of 120 concepts are terminal: nothing in the curriculum builds on
them. That is not necessarily wrong, but it is worth knowing, because a graph
that is mostly leaves is closer to a list than to an architecture.

**Step 2: find what is load-bearing**

```python
for cid, n in outdeg.most_common(6):
    print(f"{n:2} dependents   {cid:26} [{by_id[cid].tier}]")
```

```
 8 dependents   content-model              [core]
 8 dependents   docs-as-code               [core]
 6 dependents   documentation-ci           [core]
 5 dependents   metadata                   [core]
 5 dependents   static-site-generators     [core]
 5 dependents   code-sample-validation     [core]
```

These six are the architecture's spine, and two more, agent-ready content and
docs analytics, tie the last of them at five. The practical consequence is about
sequencing: writing a leaf before its prerequisites exist produces a page that
has to re-explain its own foundations, and the dependency count tells you which
pages to write first without guessing.

**Step 3: measure the longest chain**

```python
order = topological_order(reg)
depth = {}
for cid in order:
    depth[cid] = 1 + max((depth[p] for p in by_id[cid].prerequisites), default=0)
```

```
longest prerequisite chain: 11 deep, ending at 'hallucination-guardrails'

information-architecture -> content-model -> metadata -> agent-ready-content
  -> chunking -> embeddings -> vector-stores -> rag -> grounding
  -> output-evaluation -> hallucination-guardrails
```

Eleven. A reader who wants hallucination guardrails and takes the architecture
literally has ten concepts to get through first, and measuring AI answer quality
ties it through the same ten.

That is a finding requiring judgment rather than a fix. Either the chain is
real, in which case the honest answer is that this material is genuinely deep
and a [learning path](learning-paths.md) should offer a shortcut, or some of
those edges are aspirational and should be removed. Depth is the number that
forces the question.

**Step 4: check the tiers against the graph**

The tier is a claim about importance, assigned by hand. Dependents are a fact
about structure, computed. If the claim is sound they should correlate:

```
mean dependents by tier:
   core        n= 66  mean=1.65  max=8
   supporting  n= 45  mean=0.60  max=3
   context     n=  9  mean=0.22  max=1
```

They do, cleanly, which is the first evidence that the hand-assigned tiers are
not arbitrary. Now look for the disagreements, which is where the value is:

```
context-tier concepts that something depends on:
   usd-omniverse (1), inference-serving (1)

supporting concepts with more dependents than the core mean:
   content-lifecycle (3), style-guide (3), reproducible-environments (3),
   single-sourcing (2), ephemeral-environments (2), seo-for-docs (2)
```

Six supporting concepts carry more of the graph than the average core
concept. They are promotion candidates, identified mechanically rather than by
argument.

**Step 5: the finding that is not a defect**

```
core concepts that are isolated (no prerequisites, no dependents):
   reading-code-to-verify, docs-as-product
```

Two concepts are marked `core`, the highest importance, and sit entirely
outside the graph. By the logic of steps 2 and 4 that looks like a
contradiction.

It is not. Both are craft skills: reading code to verify a claim, and treating
documentation as a product. Technical writing was a third until release notes
named it as a prerequisite, which is fair: a changelog is writing. They are among the most important
things on the curriculum and they are not *prerequisites* for anything,
because you do not learn them once and build on them. You get better at them
across everything else.

So **importance and graph position are different axes**, and the mistake is
assuming a dependency graph ranks importance. It ranks *sequence*. Conflating
the two produces curricula that teach tooling thoroughly and never mention
judgment, because judgment has no prerequisites and therefore no place in a
tree.

**What you built.** An architecture you can interrogate: a spine, a depth
measurement, six promotion candidates found mechanically, and one finding that
looked like a defect and was a property of the domain.

## Reference

### Information architecture against knowledge architecture

| | Information architecture | Knowledge architecture |
|---|---|---|
| Organizes | Pages and their labels | Concepts and their relationships |
| Artifact | Navigation, URL structure, taxonomy | A concept graph with dependencies |
| Question it answers | Where does this page go? | What must a reader already know? |
| Failure | A reader cannot find the page | A reader finds it and cannot follow it |
| Validated by | Card sorting, tree testing, search logs | Graph properties, and reader drop-off |
| Who owns it | Often the docs team alone | Jointly, with documentation leads |

### What a knowledge graph lets you compute

| Property | Tells you |
|---|---|
| Out-degree | What is load-bearing, and what to write first |
| Depth | Whether the material is genuinely deep or over-linked |
| Cycles | A circular explanation; always a defect |
| Leaf fraction | Whether this is an architecture or a list |
| Tier against out-degree | Whether hand-assigned importance matches structure |
| Isolated nodes | Either a gap, or a craft skill; see step 5 |
| Topological order | A defensible writing and reading order |

None of these are available from a navigation tree, which is the argument for
making relationships explicit.

### Patterns worth knowing

| Pattern | Shape | Use |
|---|---|---|
| Prerequisite graph | Directed, acyclic | Curriculum, onboarding, learning paths |
| Concept map | Undirected, typed edges | Explaining a domain's shape |
| Taxonomy | Tree, is-a | Classification; see [taxonomy](taxonomy.md) |
| Topic map | Hub and spoke | A landing page per area |
| Decision graph | Branching on conditions | [Playbooks](playbooks.md) |

Prerequisite graphs and taxonomies get confused most often. A taxonomy says
what a thing *is*; a prerequisite graph says what you must know *first*. A
corpus with only a taxonomy can be perfectly organized and still impossible to
read in order.

### Keeping it honest

| Rule | Why |
|---|---|
| Acyclic, enforced | A cycle is a circular explanation |
| Every edge means "assumes", not "related to" | "Related" edges make everything adjacent and the graph useless |
| Prerequisites resolve to real concepts | A dangling edge is a silent gap |
| Tiers are reviewed against out-degree | Hand-assigned importance drifts |
| Depth is monitored | Over-linking inflates it quietly |

The second row is the discipline that keeps the graph meaningful. It is
tempting to add an edge whenever two concepts are mentioned together, and the
result is a graph with no sequence in it.

## Explaining it to your team

**Lead with the distinction.** "Information architecture organizes pages;
knowledge architecture organizes what is known. They can disagree: a page can
be in the obvious place while depending on four concepts the reader has not
met. The second one is a graph, which means you can compute over it."

**Be precise about ownership.** You collaborate with documentation leads and
bring implementation feedback. So the description of your part is not "I
design the architecture", it is "I implement it, measure it, and tell the leads
what breaks". Then give an example of a measurement: depth of
eleven, six supporting concepts carrying more of the graph than the average
core concept.

**The tradeoff to name.** Making relationships explicit is real ongoing
cost. Every new concept needs its edges decided, the graph needs validating in
CI, and the temptation to add "related to" edges has to be resisted
continuously or the graph stops encoding sequence. On a corpus of thirty pages
this is overhead for nothing; it starts paying somewhere in the low hundreds.

**One sharper point.** A dependency graph ranks
sequence, not importance, and conflating them is how curricula end up
teaching tooling thoroughly and never mentioning judgment. Two of the most
important concepts in my own registry are isolated nodes, because craft skills
are not prerequisites for anything: you do not learn to verify a claim once
and build on it. An architecture that cannot represent those will quietly drop
them.

## Putting it into practice

**The work product.** A concept graph for a corpus you own, validated in CI, plus
the audit from steps 2 through 5.

**Three things to do, in order:**

1. Write the prerequisite edges for twenty concepts in a domain you know. The
   arguments about which edges are real are the work.
2. Compute out-degree and depth. The spine and the longest chain are both
   immediately actionable. Predict the spine before you compute it; where your
   guess and the out-degree disagree, one of the two is the finding.
3. Compare your hand-assigned importance against out-degree. The disagreements
   are either mis-tierings or craft skills, and telling those apart is the
   judgment this concept is about.

**How to tell it is working.** Neither of this guide's
repositories was recorded as demonstrating this, and the honest position is
that the registry itself is the demonstration: 120 concepts, 138 edges,
acyclic and enforced, with prerequisite resolution failing the build and a
topological order driving the writing sequence. Every number on this page came
from running the audit against it, including the one that corrected my own
assumption about tiers.

## Related

- [Information architecture](information-architecture.md), the page-level discipline
- [Content models](content-model.md), the most load-bearing concept in this graph
- [Learning paths](learning-paths.md), the shortcuts a deep graph needs
- [Playbooks and decision guides](playbooks.md), a different graph shape for a different job
