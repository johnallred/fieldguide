---
title: Golden paths
summary: "One route from a clean environment to a working result, and the cost of every alternative you offer alongside it."
diataxis: explanation
audience: developer
concept: golden-paths
tags: [gp, core]
---

# Golden paths

`core` · difficulty 3 · 5h

!!! quote "Asked for by name"
    Intel: "Design and maintain golden paths and curriculum that take a developer from a clean environment to a working result"

    Intel: "Treats setup, runnable samples, and docs as one product, engineering docs-as-code with cold-start and link CI so a developer reaches first success in minutes with zero help"

**Prerequisites:** [Diátaxis](diataxis.md)

**Leads to:** [Quickstarts that survive contact](quickstarts.md), [Reproducible environments](reproducible-environments.md)

## What it is

**One** documented route from nothing to a working result. Not the best route
for every reader, not every supported configuration: one route, chosen,
written down, and tested end to end.

The word that does the work in Intel's phrasing is *a*. A golden path is
singular. The moment there are two, neither is golden, because you can no
longer say "this is the route we test and support".

## Why the job asks for it

Intel asks for it twice, and the second quote gives the acceptance criterion:
first success in minutes, with zero help. That is a measurable claim about a
specific artifact, which is unusual and worth taking seriously.

The reason golden paths are hard is that they require **saying no** in a
document whose author wants to be helpful. Every reader on a different
platform, package manager or deployment model is a temptation to add a branch,
and each branch feels like inclusion. The golden path discipline says those
belong on a different page, because a path that accommodates everyone is tested
for nobody.

That is a judgment call you have to be able to defend, which is why this is
difficulty 3 while [quickstarts](quickstarts.md) is 2.

## The golden path

Count the routes through a page, which turns a style argument into a number.
About thirty-five minutes.

**Step 1: two versions of the same quickstart**

The accommodating one, written by somebody being helpful:

````bash
mkdir -p paths-demo && cd paths-demo
cat > quickstart-bad.md <<'MDEOF'
# Get started

## Install

If you use pip, run `pip install widget`. Alternatively, with conda,
run `conda install -c widget widget`. On macOS you can also use Homebrew.

## Configure

Either set `WIDGET_TOKEN` in your environment, or create `~/.widgetrc`.
Optionally you can pass `--token` on every command instead.

## Choose a backend

Depending on your deployment, use the local backend or the hosted one.
If you are behind a proxy, also set `HTTPS_PROXY`.

## Run

Run `widget sync`. If you chose the hosted backend, add `--remote`.
MDEOF
````

And the golden one:

````bash
cat > quickstart-good.md <<'MDEOF'
# Get started

## Install

```bash
pip install widget
```

## Configure

```bash
export WIDGET_TOKEN="$(cat ~/.config/widget/token)"
```

## Run

```bash
widget sync
```

You should see `synced 0 records`.

Using conda, a hosted backend or a proxy? See [Installation options](install.md).
MDEOF
````

The second one is not less helpful. It moved the alternatives one click away
and kept a single tested route on the page.

**Step 2: count the routes**

A branch marker only counts if the same sentence also tells the reader to *do*
something, because English reuses those words rhetorically:

```python
MARKER = re.compile(
    r"(?i)\b(if you use|if your|either|alternatively|optionally"
    r"|depending on|or you can|you can also)\b")
ACTION = re.compile(r"(?i)(`[^`]+`|\b(run|use|set|install|create|pass|add)\b)")

for section in re.split(r"^##\s+", text, flags=re.M)[1:]:
    n = sum(1 for s in sentences(section)
            if MARKER.search(s) and ACTION.search(s))
    per.append(n)
routes = math.prod(n + 1 for n in per)
```

```
quickstart-bad.md    sections=4 branches=[3, 2, 1, 0] routes=24
quickstart-good.md   sections=3 branches=[0, 0, 0]    routes=1
```

**Twenty-four against one**, for pages of roughly the same length. The first
page offers twenty-four distinct journeys and the reader has to choose at every
section without knowing which combinations anybody has tried.

**Step 3: connect the number to testing**

This is the argument that settles it. A [cold-start test](coldstart-testing.md)
follows the document's commands in order, so it can test exactly **one** route.

| Page | Routes | Tested | Untested |
|---|---|---|---|
| `quickstart-bad.md` | 24 | 1 | 23 |
| `quickstart-good.md` | 1 | 1 | 0 |

Twenty-three untested routes, each of which a reader will take, and each of
which can break without anybody noticing. The branches did not add support;
they added unverified surface that looks supported.

**Step 4: get a real baseline**

```
docpack getting-started.md     sections=9 branches=[0 x 9]  routes=1
```

A real, shipped tutorial: nine sections, zero branches, one route. 566 words,
five steps, nine code blocks. That is what the discipline looks like in
practice, and it is achievable.

**Step 5: be honest about the metric**

Run it over this guide's own pages and one comes back with 2:

```
link-checking.md     branches=[0, 0, 0, 1, 0, 0, 0, 0]  routes=2
```

The sentence is: "`install.md#tuning` does not exist either, because
`install.md` has no Tuning heading." That is "either" as a negative
conjunction, not a branch. The narrowed rule removed two of three such false
positives from my own corpus and could not remove this one, because English
reuses branch words conjunctively.

So the metric is a **screening signal, not a precise count**. A page at 24 or
72 is unmistakably branchy; the difference between 1 and 2 is noise. Use it to
find the pages that need attention, not to certify the ones that do not.

**What you built.** A number that converts "this page is too accommodating"
from an opinion into a finding, plus the testing argument that makes it matter.

## Reference

### What makes a path golden

| Property | Why |
|---|---|
| One route | So it can be tested; see step 3 |
| From a clean environment | The author's machine is not a starting state |
| To a stated, checkable result | "You should see `synced 0 records`" |
| Every command copy-pasteable | No placeholders the reader must resolve |
| No decisions | A decision is a branch, and a branch is untested surface |
| Tested in CI | [Cold-start testing](coldstart-testing.md) |
| Minutes, and the number is known | Intel's own criterion |

### Where the alternatives go

| Reader | Page |
|---|---|
| The default case | The golden path |
| A different package manager | Installation options |
| A different deployment | A how-to per deployment |
| Behind a proxy, air-gapped | A networking how-to |
| Wants to understand why | An explanation |

The link at the bottom of the golden path is what makes this humane rather than
exclusionary. One sentence, one link, and the reader who is not in the default
case is one click from their case instead of being asked to disambiguate four
sections of prose.

### Choosing the one route

| Criterion | Pick the option that |
|---|---|
| Population | The largest group of readers actually uses |
| Reliability | Fails least often, not the one that is newest |
| Speed to result | Reaches a working state soonest |
| Fewest prerequisites | Needs the least already installed |
| Testability | You can run in CI without credentials |

These conflict, and the last one wins more often than people expect. A route
you cannot test in CI is a route that will be broken and unnoticed, which
makes it a worse default than a slightly less popular route you can verify
every night.

### Golden path against its neighbours

| Concept | Is |
|---|---|
| Golden path | The one supported route, the organising decision |
| [Quickstart](quickstarts.md) | The page that implements it, usually the shortest one |
| [Tutorial](tutorial-design.md) | Teaching; a golden path optimises for working, not learning |
| [Sample walkthrough](sample-walkthroughs.md) | Explaining existing code, not building up to it |
| How-to | One task, assumes you are already set up |

Golden path and tutorial get conflated most. A tutorial may deliberately take a
longer route because the detour teaches something. A golden path takes the
shortest route to working and teaches nothing it does not have to.

## How to talk about it

**Lead with the number.** "A golden path is one route from a clean environment
to a stated result. The reason it is one is testability: a cold-start test
follows the document's commands, so it tests exactly one route. I measured an
accommodating quickstart at 24 distinct routes, which means 23 of them were
untested and looked supported."

**The follow-up is about excluding readers**, and the answer is that the
alternatives get a page and a link rather than deletion. The reader who uses
conda is one click from their instructions instead of disambiguating four
sections, and that reader's page can now be tested too.

**The tradeoff to volunteer.** Choosing one route means someone's case is not
the default, and the person whose case it is will tell you. The honest answer
is that this is the cost, it is paid by a minority of readers, and the
alternative is a page where every reader's route is untested. Also: testability
sometimes beats popularity when picking the default, and that is uncomfortable
to defend in a room that wants the most-used option.

**One sharper point.** My own route-count metric over-counts, because English
uses "either", "or" and "if you" conjunctively and rhetorically as well as to
branch. Narrowing it to sentences that also contain an action removed two of
three false positives in my corpus and not the third. So it is a screening
signal: good for finding the 24-route page, useless for distinguishing 1 from
2. Saying which half a metric is good for is worth more than the metric.

## How to prove it

**The artifact.** A quickstart with one route, a stated expected output, a
cold-start test, and a separate options page carrying everything you removed.

**Three things to do, in order:**

1. Run the route count over your own quickstart. If it is above about 4, you
   have found your next piece of work.
2. Count how many of those routes your CI actually tests. The answer is one.
3. Move the alternatives to a second page and leave one link behind. The
   quickstart gets shorter and the alternatives get testable.

**What makes it credible rather than decorative.** `docpack`'s
`docs/tutorials/getting-started.md` is a single route verified by
`scripts/coldstart.sh`, which builds a fresh virtual environment, follows the
tutorial literally and asserts the exact output string the tutorial promises.
Measured at one route across nine sections. The combination is the evidence:
not that the page is short, but that the one route it offers is the one the
nightly build walks.

## Related

- [Quickstarts that survive contact](quickstarts.md), the page that implements this
- [Cold-start testing](coldstart-testing.md), what makes the single route verifiable
- [Reproducible environments](reproducible-environments.md), the "clean environment" half
- [Time to first success](time-to-first-success.md), the metric Intel names
