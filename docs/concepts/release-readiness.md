---
title: Release readiness for documentation
summary: Making a documented path part of what shipping means, rather than something that follows it.
diataxis: explanation
audience: operator
concept: release-readiness
tags: [craft, core]
---

# Release readiness for documentation

`core` · difficulty 2 · 4h

> Encode standards (user stories, release readiness, onboarding, security guidance) into templates, validators, and guided workflows rather than static documents

> Source: nvidia posting, verbatim

**Prerequisites:** [Documentation CI](documentation-ci.md)

## What it is

Making documentation part of the definition of done for a release, enforced by
something other than goodwill. The output is a check, a template field, or a
gate in the release pipeline, not a policy document.

## Why the job asks for it

NVIDIA names it inside a list of standards to encode, and the phrasing is the
important part: "into templates, validators, and guided workflows **rather than
static documents**". They are explicitly ruling out the usual artifact, which is
a wiki page titled "Definition of Done" that everyone agreed to in a meeting two
years ago.

The outcome they attach to it is "so every release ships documented,
discoverable, and supportable". Intel's version: "so each new capability ships
with tested documentation".

On a Tuesday this is the recurring unpleasant conversation. A capability shipped
on Thursday. The release notes mention it. There is no page, the sample does not
cover it, and the first support ticket arrives Monday. Nobody did anything
wrong: the engineer shipped a feature, the release manager cut a release, and
documentation was not in anyone's checklist in a way that could block.

The reason this is `core` rather than a process nicety: without it, every other
mechanism in this guide is reactive. You can have excellent
[cold-start testing](coldstart-testing.md) and
[freshness monitoring](freshness-monitoring.md) and still be permanently behind,
because they tell you about content that exists. Release readiness is the only
mechanism that acts *before* the gap is created.

The honest difficulty: this is the most political concept in the guide. The
others are things you can build alone. This one requires someone else to accept
a constraint.

## The golden path

Build the gate, in the weakest form that still works, and see it block.
Thirty-five minutes.

**Step 1: decide what "documented" means, concretely enough to check**

A definition that needs a human to interpret it is a policy document again.

```bash
mkdir -p release-drill && cd release-drill
cat > definition.md <<'EOF'
A user-visible capability is DOCUMENTED when all four are true:

1. A page exists and is reachable from the navigation.
2. The page has a runnable example, or explicitly states there is none.
3. The example is covered by sample validation (so it cannot silently rot).
4. The page names the release it first shipped in.

Deliberately NOT in the definition:
  - "the page is good"      -> not checkable, belongs in review
  - "the page is complete"  -> not checkable, and complete is not a state
  - "approved by docs"      -> a person, not a gate; becomes a bottleneck
EOF
cat definition.md
```

**Step 2: carry the claim in the artifact that already exists**

Do not create a new tracking system. The changelog already lists what shipped.

````bash
cat > CHANGELOG.md <<'EOF'
## 2.4.0 (unreleased)

- feat: batch inference endpoint  (docs: how-to/batch-inference.md)
- feat: quantised model loading   (docs: none)
- fix: memory leak in the pool    (docs: n/a)
EOF

mkdir -p docs/how-to
cat > docs/how-to/batch-inference.md <<'EOF'
---
title: Batch inference
since: 2.4.0
---
# Batch inference

Post several inputs in one request.

```python
client.infer_batch(["a", "b"])
```
EOF
ls docs/how-to/
````

Three entry kinds, which is the whole design: a page, an admitted gap, and
`n/a` for a change with no user-visible surface. **The `n/a` case is what makes
the gate acceptable to engineers**, because without it every bug fix needs a
page and the gate gets disabled within a month.

**Step 3: the gate**

```bash
cat > check_release.py <<'PY'
"""Fail a release when a user-visible change has no documented path.

Reads the unreleased section of the changelog and checks each entry's `docs:`
annotation. Three valid forms:

    docs: <path>   the page must exist and declare `since:` this version
    docs: n/a      no user-visible surface; the author asserts this
    docs: none     a known gap; fails the gate, and is meant to

`none` exists so an author can be honest without lying to the gate. The gate
still fails, which is the point: the gap becomes visible before the release
rather than in a support ticket after it.
"""
import re
import sys
from pathlib import Path

import yaml

VERSION = re.compile(r"^## (\S+) \(unreleased\)")
ENTRY = re.compile(r"^- (\w+): (.+?)\s+\(docs: (.+?)\)\s*$")


def main(changelog: Path, docs: Path) -> int:
    lines = changelog.read_text(encoding="utf-8").splitlines()
    version = next((m.group(1) for m in map(VERSION.match, lines) if m), None)
    if not version:
        print("no unreleased section; nothing to check")
        return 0

    failures = []
    checked = 0
    for line in lines:
        match = ENTRY.match(line)
        if not match:
            continue
        kind, description, claim = match.groups()
        checked += 1

        if claim == "n/a":
            continue
        if claim == "none":
            failures.append(f"{kind}: {description!r} has no documentation")
            continue

        page = docs / claim
        if not page.exists():
            failures.append(f"{kind}: {description!r} points at {claim}, which does not exist")
            continue

        front = yaml.safe_load(page.read_text(encoding="utf-8").split("---")[1]) or {}
        if str(front.get("since", "")) != version:
            failures.append(
                f"{kind}: {claim} has since={front.get('since')!r}, expected {version!r}"
            )

    for failure in failures:
        print(f"NOT RELEASE READY  {failure}", file=sys.stderr)
    print(f"{'FAIL' if failures else 'ok'}: {checked} changelog entries, "
          f"{len(failures)} blocking {version}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(Path("CHANGELOG.md"), Path("docs")))
PY
python3 check_release.py
```

**Step 4: close the gap and watch it go green**

````bash
cat > docs/how-to/quantised-models.md <<'EOF'
---
title: Loading quantised models
since: 2.4.0
---
# Loading quantised models

Pass `quantised=True` when loading.

```python
model = load("widget-7b", quantised=True)
```
EOF
python3 - <<'PY'
import pathlib
p = pathlib.Path("CHANGELOG.md")
p.write_text(p.read_text().replace(
    "- feat: quantised model loading   (docs: none)",
    "- feat: quantised model loading   (docs: how-to/quantised-models.md)"))
PY
python3 check_release.py
````

**What you built.** A gate that blocks a release when a feature has no page,
reading an artifact the team already maintains, with an honest escape hatch for
changes that need no documentation and a deliberately failing value for gaps
the author knows about.

The `since` cross-check is the part that earns its keep over time. It catches
the case where someone points the changelog at a page that exists but documents
the *old* behaviour, which is the failure a simple existence check misses.

## Reference

### What a checkable definition looks like

| Checkable | Not checkable |
|---|---|
| A page exists at this path | The page is good |
| The page declares `since: 2.4.0` | The page is up to date |
| The example is covered by sample validation | The example is realistic |
| The page is in the navigation | The page is discoverable |
| A changelog entry has a `docs:` annotation | Documentation was considered |

The right column is not worthless. It belongs in [review](docs-review.md),
performed by a person. The mistake is putting it in a gate, where it either
blocks on judgement or passes on nothing.

### The three annotation values, and why all three are needed

| Value | Meaning | Gate result |
|---|---|---|
| `<path>` | A page exists and claims this version | passes if true |
| `n/a` | No user-visible surface. An assertion by the author | passes |
| `none` | A known gap | **fails** |

Omitting `n/a` is the commonest way this gate dies. Every internal refactor
needs an annotation, authors resent it, and someone adds `--skip-docs-check` to
the release script. Omitting `none` is the second way: without an honest value
for a gap, authors point at an unrelated page.

### Where to put the gate, from weakest to strongest

| Placement | Blocks | Political cost |
|---|---|---|
| A report emailed after the release | nothing | none |
| A warning in the release pipeline | nothing | none |
| A required field in the PR template | nothing, but prompts | low |
| A failing check on the release branch | the release | medium |
| A failing check on every PR | the merge | high |

Start at the template and the report. **A gate introduced at the top of this
table gets removed**; one that has been producing an accurate report for two
months is much easier to promote, because by then everyone has seen the number.

### What this cannot do

| Limit | Consequence |
|---|---|
| It checks existence, not quality | A one-line stub passes |
| It depends on the changelog being accurate | An unlisted feature is invisible to it |
| It cannot see undocumented behaviour changes | A default changing is not a changelog `feat:` |
| It needs someone to accept the constraint | The only concept here you cannot build alone |

The third row is the real residual risk, and it is why
[freshness monitoring](freshness-monitoring.md) and
[claim checking](working-with-engineers.md) are not optional complements to
this.

## How to talk about it

**What a competent answer sounds like.** Lead with the escape hatch, because it
proves you have shipped this rather than proposed it. "I added a `docs:`
annotation to changelog entries and a check that fails the release branch if a
`feat:` entry has no page declaring that version. It takes `n/a` for changes
with no user-visible surface, which is what keeps engineers from disabling it,
and `none` for a known gap, which fails on purpose so the gap is visible before
the release instead of in a ticket after it."

**The follow-up is "what happened when it blocked a release",** and this is the
question the whole concept lives or dies on. Have a real answer. The useful shape
is: it blocked, someone asked for an override, and the override was granted with
the gap recorded. A gate that has never been overridden is either very new or
not actually on the critical path. Saying that you granted an override, and that
the record of it is what later justified headcount, is a much more credible story
than a gate nobody ever fought.

**The tradeoff to volunteer.** This gate moves documentation work from after the
release to before it, which means it sometimes delays releases, and the cost
lands on engineers rather than on you. That is a real transfer and it is why the
gate needs an owner with authority behind it. There is a version of this that is
pure friction: a team that resents the check, writes one-line stubs to satisfy
it, and ships documentation that is technically present and useless. The
stub-passing problem is genuine and the mitigation is not a stricter gate, it is
[review](docs-review.md) by a person on the pages that matter.

**One sharper point.** The strongest argument for release readiness is not
completeness, it is **that an undocumented capability is more expensive than an
unshipped one.** A feature nobody can use generates support load, bad first
impressions, and a backlog item that gets harder every month as context is lost.
Framing it as a cost-of-delay argument rather than a quality argument is what
moves release managers, because quality arguments lose to ship dates and cost
arguments do not.

## How to prove it

**The artifact.** The gate plus the escape hatch, in a repository, with at least
one commit where it failed.

**Three things to do, in order:**

1. **Run the golden path, then point it at a real changelog.** Most projects
   have one and none of them have a `docs:` annotation. Adding the annotation
   retroactively to the last release tells you immediately what the gap rate is,
   and that number is the argument for the gate.
2. **Write the definition of documented for one project**, with the
   deliberately-excluded list. The exclusions are what show judgement; anyone
   can write a wish list. If the excluded list is empty, the definition is not
   finished. Every real one excludes something, and a definition that excludes
   nothing will be overridden the first time it is inconvenient.
3. **Report before you block.** Run the check in report-only mode for a few
   releases and keep the numbers. A gate proposed with two months of data behind
   it is a different conversation from a gate proposed on principle.

**What makes it credible rather than decorative.** A policy document proves nothing, and most people in
this field have written one. A check that reads the changelog, takes `n/a`, and
has a commit where it blocked a release is specific, unfakeable, and
demonstrates that you have had the political conversation rather than theorised
about it.

This repository has the mechanism without the politics, and the distinction is
worth stating plainly rather than blurring. `fieldguide release-check` is a
real gate: seven named steps, a remedy on each failure, run in CI, and it does
block. It carries `--report-only` precisely because of the advice above, so it
can run for several releases and accumulate numbers before anyone is asked to
accept a constraint. What it cannot demonstrate is the constraint being
accepted, because the only author here is also the only reviewer. A gate you
imposed on yourself is a habit, and a gate somebody else agreed to is a
negotiation; the second is the thing this page is actually about, and no
amount of code in a solo repository produces it.

So the honest version in an interview is: here is the mechanism, here is the
report-only mode that exists for the conversation, and the conversation itself
is the part I would be having with your release engineers rather than showing
you from a repository of my own.

## Related

- [Treating docs, setup and samples as one product](docs-as-product.md), the ownership model this needs
- [Documentation CI](documentation-ci.md), where the gate runs
- [Working with engineers as sources](working-with-engineers.md), how the annotation gets filled in
- [Freshness monitoring](freshness-monitoring.md), the complement for changes no changelog catches
