---
title: Reviewing documentation
summary: Spending human attention only on what no check can judge, and shrinking the checklist as automation grows.
diataxis: how-to
audience: developer
concept: docs-review
tags: [qa, supporting]
---

# Reviewing documentation

`supporting` · difficulty 2 · 3h

!!! quote "Asked for by name"
    NVIDIA: "Hands-on docs-as-code experience: Git, pull request review, Markdown/RST, static site generators ... and CI/CD"

**Prerequisites:** [Git authoring workflows for writers](git-authoring.md), [Style guides](style-guide.md)

## What it is

Pull request review for documentation, and more usefully, the decision about
what a human reviewer should be looking at. Human attention is the scarcest
thing in this whole category, so the design question is not "what should a
reviewer check" but "what is left once everything checkable has been
automated."

That boundary is not fixed. It moves every time you make an artifact
executable, and the golden path below moves it.

## Why the job asks for it

NVIDIA lists pull request review alongside Git and CI, in the same breath. That
grouping is the point: review is one stage of a pipeline, not a substitute for
one.

The failure mode in most organisations is a review checklist that grew by
accretion. A reviewer is asked to verify terminology, link validity, heading
case, sample correctness and British spelling, all of which a machine does
better. By the time they reach the only question that matters, whether the
page is true and useful, they have no attention left for it.

A second failure mode is believing review is a safety net it cannot be. Review
observes what the reviewer looks at, and a reviewer looks at a diff.

## The golden path

Plant two defects, one that looks automatable and one that looks like it needs
judgment, then discover the second one is automatable too. About thirty
minutes.

**Step 1: a page with two defects**

````bash
mkdir -p review-demo/docs && cd review-demo
printf 'site_name: Review demo\n' > mkdocs.yml

cat > docs/setup.md <<'EOF'
# Set up the widget

## Steps

1. Run `widget start` to launch the service.
2. Run `widget init` to create the config file.
3. Confirm with `widget status`.

See [the tuning guide](setup.md#tuning) for more.
EOF
````

Defect one: a dead heading anchor, `#tuning` does not exist. Defect two: the
steps are in the wrong order, because you cannot start a service before its
config file exists.

The first looks like a job for CI. The second looks like a job for a reviewer
who knows the product.

**Step 2: confirm CI catches the first and not the second**

```bash
mkdocs build --strict 2>&1 | grep -E "INFO.*anchor"
```

```
INFO - Doc file 'setup.md' contains a link 'setup.md#tuning', but there is no
       such anchor on this page.
```

A [link checker](link-checking.md) reports the dead anchor precisely. Nothing
in any linter has an opinion about whether step 1 should precede step 2, and no
amount of pattern matching will acquire one.

So far this confirms the usual story: machines check mechanics, humans check
meaning.

**Step 3: make the steps executable and watch the story change**

Give the commands a real implementation, where `start` requires a config:

```bash
mkdir -p bin
cat > bin/widget <<'EOF'
#!/usr/bin/env bash
case "$1" in
  init)   printf 'name = "demo"\n' > widget.toml; echo "initialised";;
  start)  [ -f widget.toml ] || { echo "error: no widget.toml; run 'widget init' first" >&2; exit 1; }
          echo "started";;
  status) [ -f widget.toml ] && echo "running" || { echo "error: not initialised" >&2; exit 1; };;
esac
EOF
chmod +x bin/widget
export PATH="$PWD/bin:$PATH"
```

Now run the documented steps in the documented order, as
[cold-start testing](coldstart-testing.md) would:

```bash
widget start; widget init; widget status
```

```
error: no widget.toml; run 'widget init' first
  step 1 FAILED
initialised
running
```

The ordering defect is mechanically detectable after all, and the error message
even names the fix. In the correct order all three pass.

The lesson is not that reviewers are unnecessary. It is that **the boundary
between "needs judgment" and "automatable" is a function of how much of your
documentation is executable**, and it moves whenever you invest. A review
checklist written two years ago is asking humans to do work a machine now does.

**Step 4: find what is left**

Executing the steps proves the sequence *runs*. It says nothing about whether
this is the sequence a real user needs, whether step 3 is reassuring or
patronising, whether the page should exist at all, or whether it answers the
question people actually arrive with. Those are the review questions, and
there are fewer of them than most checklists contain.

**What you built.** A review checklist with four items instead of fifteen, and
a habit of asking, for every finding, whether a machine could have caught it.

## Reference

### What only a human can judge

| Question | Why no check can answer it |
|---|---|
| Should this page exist? | Requires knowing the corpus and the audience |
| Is the explanation *correct*? | Requires domain knowledge |
| Is this the sequence a user needs? | Running is not the same as teaching |
| Is the reader's likely question answered? | Requires knowing what readers ask |
| Is this the right Diátaxis type? | A tutorial written as reference runs fine |
| Does this duplicate an existing page? | Requires judgment about near-duplicates |
| Is the tone right for this audience? | Taste, and audience knowledge |

### What should never be in a review checklist

| Item | Automate with |
|---|---|
| Dead links and anchors | [Link checking](link-checking.md) |
| Terminology and banned phrases | [Prose linting](prose-linting.md) |
| Samples that no longer run | [Sample validation](code-sample-validation.md) |
| Steps in an impossible order | [Cold-start testing](coldstart-testing.md) |
| Missing front-matter fields | [Content model](content-model.md) validation |
| Heading case | A Vale `capitalization` rule |
| Heading levels skipping | [Accessibility checks](accessibility.md) |

Every row is something humans do worse than a script, more slowly, and at the
cost of the rows in the previous table.

### What review structurally cannot see

Review observes what the reviewer looks at, which is a diff. Three blind spots
follow, and the first one is not theoretical:

| Blind spot | Example |
|---|---|
| A source-to-render discrepancy | Seven pages in this guide shipped code samples rendered as prose. The Markdown source looked correct, because it *was* correct as text; the defect was in how the parser read a heredoc. No amount of careful reading of a diff finds that. |
| What is missing | A reviewer sees the lines that changed, not the step nobody wrote |
| Corpus-level effects | A page that is fine alone and duplicates two others |

The first blind spot is the general case worth remembering: a human reading
source cannot verify a claim about the artifact. That needs a check that reads
the artifact.

### Review mechanics that help

| Practice | Effect |
|---|---|
| [Preview deployments](preview-deployments.md) | Reviewers read rendered pages; non-engineers can participate |
| CI green before human review | Nobody spends attention on what a gate already covers |
| A template naming the four judgment questions | Keeps review on the irreducible part |
| Separate "blocking" from "suggestion" in comments | An author knows what must change |
| Review the page, not the diff, for structural changes | A diff hides reordering |

The second row is a sequencing decision with real leverage. A reviewer who
opens a pull request with a red build spends their attention triaging CI
failures. Make CI pass first, and human review starts where machines stop.

## How to talk about it

**Lead with the boundary, not the checklist.** "I treat review as the stage
that handles what no check can judge: whether the page should exist, whether
the explanation is correct, whether it answers the question readers actually
arrive with. Everything mechanical belongs in CI, and the review template says
so explicitly, because a checklist asking humans to verify links is spending
the scarcest resource on the easiest problem."

**The follow-up is often a challenge that this trusts automation too much.**
The strong answer concedes the real limit: review cannot catch a
source-to-render discrepancy, and automation cannot catch a procedure that runs
but teaches badly. They fail in different directions, which is why you want
both and why neither is a safety net for the other.

**The tradeoff to volunteer.** Shrinking the checklist assumes the automation
exists and works. On a corpus with no CI, the fifteen-item checklist is doing
real work badly, and taking items off it before building the gates makes things
worse. The sequence matters: automate, then shrink, and be able to point at
which gate replaced which checklist item.

**One sharper point.** The boundary between judgment and automation moves. A
wrong step order looks like it needs a reviewer who knows the product, and
becomes a failing cold-start test the moment the quickstart is executable. So
the useful question in a review is not "is this correct" but "could a machine
have caught this", and when the answer is yes the fix goes in the pipeline
rather than in the page.

## How to prove it

**The artifact.** A pull request template that names the judgment questions
only, plus the list of gates that replaced the mechanical ones.

**Three things to do, in order:**

1. Run the golden path. Step 3 is the one that changes how you think about
   review checklists.
2. Take your current review checklist and split it in two columns: automatable
   and not. Build the gate for the largest automatable item.
3. Write the four judgment questions into a template. If the template is longer
   than about five items, something on it is a machine's job.

**What makes it credible rather than decorative.** Neither of this guide's
repositories demonstrates review process, which is recorded on the
[demonstrated](../demonstrated.md) page, and process is genuinely hard to
evidence in a portfolio. What travels instead is a specific story: a checklist
item you deleted, the gate you built to replace it, and one defect that got
through review anyway and what you added afterwards. This guide's own answer to
the last part is the fence defect in seven pages and the render check that now
prevents it.

### How this would be demonstrated elsewhere

Review is two people and a diff, so a single-author repository removes it by
construction. The mechanisable part is here, as linters and a page contract;
the part that matters is what a human catches that no check can.

**What you need.** Someone else's draft, and the standing to comment on it.

**What a learner would do.** Review ten pages you did not write, and for each
comment, label it: mechanical, factual, or structural. Then ask which of the
mechanical ones a linter could have caught, and automate those instead of
making them again.

**What you would see.**

| Comment class | Rough share | What to do with it |
|---|---|---|
| Mechanical: style, terminology, formatting | Most of them | Automate; making these by hand is waste |
| Factual: the claim is wrong or stale | Few, and the highest value | Needs a reviewer who read the code |
| Structural: the page answers the wrong question | Fewest, and the most valuable | Only a human finds these |
| Preference with no basis | More than anyone admits | Drop it, or write it into the style guide |

The ratio is the finding. A review culture spending most of its attention on
row one is expensive and feels productive, and the fix is a linter rather than
a better reviewer.

**Why it does not commit.** The comments live in someone else's review thread.
What a repository can show is the result of the exercise: checks that exist
because a reviewer got tired of making the same comment. Several in this
project exist for exactly that reason, which is the nearest thing to evidence
available here.

## Related

- [Git authoring workflows for writers](git-authoring.md), the mechanics around review
- [Preview deployments and publishing](preview-deployments.md), what makes review by non-engineers real
- [Documentation CI](documentation-ci.md), the gates that shrink the checklist
- [Release readiness](release-readiness.md), the wider checklist this is one stage of
