---
title: Reproducible environments
summary: "What a clean environment costs, which isolation level catches which defect, and the pinning decision nobody makes deliberately."
diataxis: explanation
audience: developer
concept: reproducible-environments
tags: [gp, supporting]
---

# Reproducible environments

`supporting` · difficulty 3 · 4h

!!! quote "Asked for by name"
    Intel: "golden paths and curriculum that take a developer from a clean environment to a working result"

**Prerequisites:** [Golden paths](golden-paths.md)

**Leads to:** [Cold-start testing](coldstart-testing.md)

## What it is

The "clean environment" half of Intel's sentence. Making it true requires three
decisions: what level of isolation a reader is asked to create, whether
dependencies are pinned, and what your CI reproduces.

They look like infrastructure decisions and they are documentation decisions,
because each one changes what your quickstart can honestly promise.

## Why the job asks for it

Intel's phrase is "from a clean environment", and the word *clean* is doing a
lot of work. A clean environment is the only starting state a document can
assume, because it is the only one that is the same for everyone.

The difficulty is that reproducibility and speed trade off directly, and both
matter to [time to first success](time-to-first-success.md). A reader asked to
build a container before seeing anything work has a slower first success than
one who runs a single `pip install`, and the container reader has a more
reliable one. That trade has no universally right answer, which is why this is
difficulty 3.

## The golden path

Measure the four isolation levels, then find out what each one can and cannot
catch. About thirty-five minutes.

**Step 1: measure the cost of isolation**

The same trivial task, run four ways:

```bash
cat > task.py <<'EOF'
import sys
print("working result:", sys.version_info[:2])
EOF

# level 1: ambient interpreter
python3 task.py

# level 2: fresh virtual environment
python3 -m venv .v1 && .v1/bin/python task.py

# level 3: fresh environment plus one dependency
python3 -m venv .v2 && .v2/bin/pip install -q requests && .v2/bin/python task.py

# level 4: from a lockfile
.v2/bin/pip freeze > requirements.lock
python3 -m venv .v3 && .v3/bin/pip install -q -r requirements.lock
```

```
level 1: ambient interpreter        0.02s
level 2: fresh venv, no deps        3.40s
level 3: fresh venv + one dep       4.81s
level 4: pinned, from a lockfile    3.69s
```

Two things worth noticing. Creating a virtual environment costs about three and
a half seconds before any dependency is installed, which is the floor on any
cold-start check. And `requests` turned out to pin **five** packages, so one
documented dependency is five unversioned decisions unless you pin.

Level 4 came out faster than level 3 here, because of a warm wheel cache.
Pinning is not inherently slower; it is more *predictable*, which is the actual
property you want.

**Step 2: find out what each level can catch**

Isolation is not a quality ladder. Each level catches a different class of
defect, and choosing one is choosing which defects you are willing to miss:

| Level | Catches | Misses |
|---|---|---|
| Ambient | Nothing about setup | Every undeclared dependency |
| Virtual environment | Undeclared Python packages, missing steps | System packages, interpreter version, locale |
| Container | Also system packages, interpreter, locale, `apt` steps | A dead package index |
| Container, no network cache | Also a yanked release, a registry outage | Very little |

The second row is the common choice and its blind spot is specific: a
quickstart that says `pip install widget` while `widget` needs `libpq-dev` will
pass every virtual-environment check and fail for a reader on a clean machine.
If your instructions contain `apt install`, a virtual environment is not
sufficient isolation and you need a container.

**Step 3: the pinning decision, stated as a trade**

```bash
for i in 1 2; do
  python3 -m venv ".p$i" && ".p$i/bin/pip" install -q cowsay
  echo "run $i: $(".p$i/bin/pip" freeze | tr '\n' ' ')"
done
```

```
run 1: cowsay==6.1
run 2: cowsay==6.1
```

Identical today. Nothing on the page guarantees tomorrow, and that is the whole
decision:

| | Pinned | Unpinned |
|---|---|---|
| Reader gets | What you tested | Whatever is current |
| Breaks when | You update the pin | Upstream ships a change |
| Cold-start test tells you | That your pin still works | That reality still matches the page |
| Maintenance | Scheduled | Unscheduled, and surprising |
| Right for | Tutorials, reproducible research | Quickstarts, where current is the point |

The non-obvious half is in the third row. A pinned cold-start test verifies
your lockfile and stops telling you about the world. An unpinned one is flakier
and reports something you need to know, which is that a reader following your
page today would hit a problem.

The resolution most projects land on: pin the tutorial, leave the quickstart
unpinned, and run the unpinned check on a schedule rather than as a merge gate
so its flakiness does not block contributors.

**Step 4: what to actually write on the page**

The reader needs the isolation step to be one command, whatever you chose:

````bash
cat > docs/quickstart.md <<'MDEOF'
# Quickstart

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install widget
widget sync
```

You should see `synced 0 records`.
MDEOF
````

Three lines, and the first one is what makes the other two honest. Omitting it
is the most common reason a quickstart works for its author: they are in an
environment they created months ago and no longer think about.

**What you built.** A measured cost for each isolation level, a defect class
mapped to each, and a pinning decision made on purpose instead of inherited.

## Reference

### Mechanisms, by ecosystem

| Ecosystem | Isolation | Pinning |
|---|---|---|
| Python | `venv`, `virtualenv` | `requirements.lock`, `uv.lock`, `poetry.lock` |
| Node | `node_modules` per project | `package-lock.json`, `pnpm-lock.yaml` |
| Any | Container image | A digest, not a tag |
| Any | Nix, devbox | Lockfile by construction |
| Hosted | Dev containers, Codespaces | The image digest |

The container row is the one that is usually got wrong. `FROM python:3.12` is
not pinned; `FROM python:3.12@sha256:...` is. A tag is a moving reference, so a
"reproducible" container built from a tag reproduces whatever the tag means
today.

### Dev containers as documentation

A `devcontainer.json` is a documentation artifact: it is the setup instructions
in a form a machine can execute, which makes it the one setup document that
cannot drift from what it describes.

| Pays off when | Does not |
|---|---|
| Setup is genuinely complex | `pip install` is the whole story |
| Contributors are on mixed platforms | Everyone is on the same one |
| Onboarding time is a measured problem | Onboarding is already minutes |
| You already maintain an image | You would be adopting containers for this |

It is not a substitute for written instructions. A reader who cannot use your
container still needs the steps, and a repository with only a dev container has
hidden its setup rather than documented it.

### What CI should reproduce

| Reproduce | So that |
|---|---|
| The reader's environment, not yours | The check means something |
| The isolation level you documented | You test what you promised |
| The pinning state you documented | See step 3 |
| A cold cache, periodically | Index and release problems surface |

The first row is the discipline. A CI job that installs from a cached
pre-built environment is testing your cache, and when the cold-start check
fails the temptation is always to make the environment more permissive, which
converts the one check that finds this class of defect into one that cannot.

## How to talk about it

**Lead with the trade rather than the tooling.** "Reproducibility and time to
first success pull against each other, and both are things Intel asks for. A
reader who has to build a container before seeing anything work has a slower
first success and a more reliable one. I pick the weakest isolation that
catches my actual failures, and I can say what each level misses."

**The follow-up is pinning**, and the good answer is that it depends on what
the check is for. A pinned cold-start test verifies your lockfile; an unpinned
one verifies that a reader following the page today succeeds. Those are
different questions, so pin the tutorial, leave the quickstart unpinned, and
schedule the unpinned run rather than gating merges on it.

**The tradeoff to volunteer.** Unpinned cold-start checks are the flakiest
thing you will own, and a flaky required check trains people to re-run CI until
green, which damages the credibility of every other gate. That is a real cost
and the mitigation is scheduling rather than pretending the flakiness is not
there.

**One sharper point.** A virtual environment is not enough isolation if your
instructions contain `apt install`. Python-level isolation will pass a
quickstart that depends on an undeclared system library, and the reader on a
clean machine fails on step two. Matching the isolation level to the kinds of
dependency your instructions actually have is the decision, and almost nobody
makes it explicitly.

## How to prove it

**The artifact.** A cold-start script that creates the isolation level your
docs describe, plus a written reason for your pinning choice.

**Three things to do, in order:**

1. Run the step 1 measurements. Knowing that a bare virtual environment costs
   about three and a half seconds sets your expectations for CI.
2. Grep your setup instructions for `apt`, `brew` or `yum`. Any hit means a
   virtual environment is insufficient isolation for your checks.
3. Write down why your quickstart is or is not pinned. The written reason is
   the deliverable; most projects have the state without the decision.

**What makes it credible rather than decorative.** `docpack`'s
`scripts/coldstart.sh` creates a fresh virtual environment and installs the way
a reader would, which is level 2 in the table above and the right level for a
pure-Python project. The honest limit, recorded rather than glossed: it would
not catch a system-package dependency, and nothing in that repository needs
one. Naming your isolation level and its blind spot is the signal.

## Related

- [Cold-start testing](coldstart-testing.md), what runs in the environment
- [Golden paths](golden-paths.md), which this makes verifiable
- [Quickstarts that survive contact](quickstarts.md), where the venv line belongs
- [Time to first success](time-to-first-success.md), the metric this trades against
