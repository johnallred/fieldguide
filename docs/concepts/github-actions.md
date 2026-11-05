---
title: GitHub Actions for docs
summary: Implementing the gates so CI and a contributor's laptop run the same checks.
diataxis: how-to
audience: developer
concept: github-actions
tags: [qa, core]
---

# GitHub Actions for docs

`core` · difficulty 2 · 4h

!!! note "Not a quotation (derived)"
    Both postings name CI/CD for documentation. GitHub Actions is the most
    common implementation of it, and the one both companies' public
    documentation repositories use.

**Prerequisites:** [Documentation CI](documentation-ci.md)

## What it is

The YAML that runs your documentation gates on every pull request, publishes
the site on merge, and caches enough of the environment that the whole thing
finishes before the author has switched tasks.

The interesting problem is not the syntax. It is that the workflow file is a
*second* definition of what the checks are, and a second definition drifts from
the first.

## Why the job asks for it

Neither posting says "GitHub Actions" and both describe the thing it does.
NVIDIA asks for CI/CD builds, linting, link and code-sample validation and
publishing; Intel asks for docs-as-code pipelines and documentation CI. Those
are the steps in the file.

What makes this a real engineering concern rather than configuration is the
gap between CI and the contributor. If the gates live only in the workflow, a
writer cannot run them before pushing, so they push, wait four minutes, read a
log, fix one thing and push again. That loop is why people stop contributing to
documentation, and it is entirely self-inflicted.

## The golden path

Discover drift between CI and the local commands, then remove the possibility
of it. About thirty minutes. There is one thing you cannot do locally, named
honestly at the end.

**Step 1: the shape almost everyone writes first**

````bash
mkdir -p gha-demo/.github/workflows && cd gha-demo

cat > Makefile <<'EOF'
.PHONY: check
check:
	mkdocs build --strict
	python3 gate_style.py
EOF

cat > .github/workflows/docs.yml <<'EOF'
name: docs
on: [push, pull_request]
jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: mkdocs build --strict
      - run: python3 gate_style.py
      - run: python3 gate_links.py
EOF
````

Two definitions of "the checks": the Makefile and the workflow. Look closely
and they already disagree.

**Step 2: detect the drift**

```python
# drift.py
import re
from pathlib import Path

import yaml

workflow = yaml.safe_load(Path(".github/workflows/docs.yml").read_text())
ci = [s["run"].strip() for job in workflow["jobs"].values()
      for s in job["steps"] if "run" in s]

body = re.search(r"^check:\n((?:\t.*\n)+)", Path("Makefile").read_text(), re.M)
local = [line.strip() for line in body.group(1).splitlines() if line.strip()]

only_ci = [c for c in ci if c not in local]
only_local = [c for c in local if c not in ci]
for c in only_ci:
    print(f"DRIFT  CI runs but `make check` does not: {c}")
for c in only_local:
    print(f"DRIFT  `make check` runs but CI does not: {c}")
n = len(only_ci) + len(only_local)
print(f"{'FAIL' if n else 'ok'}: {len(ci)} CI command(s), {len(local)} local, {n} drifted")
raise SystemExit(1 if n else 0)
```

```bash
python3 drift.py
```

```
DRIFT  CI runs but `make check` does not: python3 gate_links.py
FAIL: 3 CI command(s), 2 local, 1 drifted
```

A contributor runs `make check`, gets a green light, pushes, and CI fails on a
gate they had no way to run. That is the drift, and it is the normal state of
most documentation repositories.

**Step 3: watch the detector get it wrong**

Add the realistic parts to CI, the ones a contributor does not need because
their environment already exists:

````bash
cat > .github/workflows/docs.yml <<'EOF'
name: docs
on: [push, pull_request]
jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip
      - run: pip install -e ".[dev,docs]"
      - run: mkdocs build --strict
      - run: python3 gate_style.py
      - run: python3 gate_links.py
EOF

python3 drift.py
````

```
DRIFT  CI runs but `make check` does not: pip install -e ".[dev,docs]"
FAIL: 4 CI command(s), 3 local, 1 drifted
```

A false positive. `pip install` belongs only in CI, and the detector has no way
to tell a setup step from a gate. You could teach it a list of exceptions, and
then the exception list becomes the third definition that drifts.

**Step 4: remove the class instead of detecting it**

```bash
cat > .github/workflows/docs.yml <<'EOF'
name: docs
on: [push, pull_request]
jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip
      - run: pip install -e ".[dev,docs]"

      # One definition of "the gates". A contributor runs exactly this.
      - name: Documentation gates
        run: make -k check
EOF
```

Now there is nothing to compare, because there is one definition. The workflow
does environment setup; the Makefile owns what a gate is.

**Step 5: the trap in step 4, which this guide walked into**

[Documentation CI](documentation-ci.md) argues that gates must be independent
so one failure does not hide another. A Makefile recipe with three command
lines short-circuits exactly like `&&`:

```bash
make check
```

```
Aborted with 1 warnings in strict mode!
make: *** [Makefile:3: check] Error 1
```

One failure reported, two gates never run. And `make -k` does **not** fix it,
because `-k` keeps going across *targets*, not across lines inside one recipe.
The fix is one target per gate:

```bash
cat > Makefile <<'EOF'
.PHONY: check gate-build gate-style gate-links

check: gate-build gate-style gate-links

gate-build:
	mkdocs build --strict

gate-style:
	python3 gate_style.py

gate-links:
	python3 gate_links.py
EOF

make -k check
```

```
Aborted with 1 warnings in strict mode!
make: *** [Makefile:10: gate-build] Error 1
STYLE: 1 hedge(s) ['docs/index.md:3']
make: *** [Makefile:13: gate-style] Error 1
LINKS: pretend one is dead
make: *** [Makefile:16: gate-links] Error 1
```

All three gates reported, overall exit non-zero. One entry point *and*
independent failures, which is what both pages were actually asking for.

**What you cannot do locally, stated plainly.** You cannot execute a GitHub
Actions workflow on your laptop. `act` runs an approximation in Docker and is
useful, but it is not the same runner, the same cache, or the same permissions.
What the structure above buys you is that the *gates* are fully runnable
locally and the workflow is thin enough to review by reading. That is the
achievable goal, not local Actions fidelity.

**What you built.** A workflow whose gates cannot disagree with the command a
contributor runs, and which reports every independent failure in one pass
rather than one per round trip.

## Reference

### The jobs a docs repository usually wants

| Job | Triggers on | Why separate |
|---|---|---|
| `quality` | Every push and pull request | Fast, under two minutes, blocks merge |
| `samples` | Every pull request | Executes code, minutes not seconds |
| `coldstart` | Pull request, or nightly | Builds a fresh environment; too slow to gate typos |
| `publish` | Push to the default branch only | Needs write permissions the others must not have |
| `external-links` | Schedule | Non-deterministic, opens an issue instead of failing |

### Things that bite

| Symptom | Cause | Fix |
|---|---|---|
| Gate passes locally, fails in CI | Drift between two definitions | One entry point, as above |
| Only the first failure is reported | `&&` or a multi-line recipe | One target per gate, `make -k` |
| Builds take minutes on a typo fix | No dependency caching | `cache: pip` on `setup-python` |
| Publish job can write to the repo on a fork PR | `pull_request_target`, or broad permissions | Least-privilege `permissions:`, publish only on the default branch |
| Generated pages committed stale | Generation not checked in CI | A `--check` mode that fails instead of rewriting |

### Permissions worth setting explicitly

```yaml
permissions:
  contents: read

jobs:
  publish:
    permissions:
      contents: read
      pages: write
      id-token: write
```

Read-only at the top, elevated only in the job that publishes. A workflow with
no `permissions:` block inherits whatever the repository default is, which on
older repositories is write access for every job.

## How to talk about it

**Lead with the contributor loop, not the YAML.** "The thing I care about in a
docs pipeline is that a writer can run every gate locally before pushing. If
the gates only exist in the workflow file, people learn the pipeline by failing
it, and that is why documentation contribution dies."

**The follow-up is about speed.** Separate jobs, dependency caching, and the
slow cold-start check out of the fast path. Be specific that you would not make
a writer fixing a typo wait on a fresh virtual environment.

**The tradeoff to volunteer.** A single entry point makes the workflow thin and
reviewable, and it moves complexity into a Makefile or script that CI cannot
see into. If that script is badly structured, you lose per-gate reporting in
the Actions UI, where each step is normally its own green or red line. The
honest compromise is a target per gate called from a small number of steps, so
you keep both the single definition and legible output.

**One sharper point.** Most documentation workflows have a job that can write
to the repository and no `permissions:` block, so every step in it inherits
write access including the ones that run third-party actions against
contributor input. Read-only by default, elevated in the publish job only, is
free to implement and the kind of detail that signals you have worked next to a
security team.

## How to prove it

**The artifact.** A workflow where the gate step calls the same command a
contributor runs, with caching, least-privilege permissions, and the slow check
in its own job.

**Three things to do, in order:**

1. Run the golden path. The valuable part is step 5, where a reasonable
   structure turns out to hide failures.
2. Open your own docs workflow and count the definitions of "the checks". If
   the answer is two, you have the drift.
3. Add `permissions: contents: read` at the top of a workflow you own and see
   what breaks. Whatever breaks is a job that was quietly holding write access.

**What makes it credible rather than decorative.** Anybody can paste a
workflow. What a reviewer notices is a repository where `make check` and CI
cannot disagree, because that is a structural decision rather than a copied
file.

## Related

- [Documentation CI](documentation-ci.md), which gates to run and what to block on
- [Preview deployments and publishing](preview-deployments.md), the job that ships the site
- [Cold-start testing](coldstart-testing.md), the slow job worth isolating
- [Reproducible environments](reproducible-environments.md), what the runner has to recreate
