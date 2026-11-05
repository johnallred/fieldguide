---
title: Cold-start testing
summary: Following the quickstart literally, from an empty environment, so the reader is not the first to try it.
diataxis: how-to
audience: developer
concept: coldstart-testing
tags: [qa, core]
---

# Cold-start testing

`core` · difficulty 3 · 5h

!!! quote "Asked for by name"
    Intel: "Build and maintain docsascode pipelines and documentation CI, including link checking and coldstart testing of quickstarts"

    Intel: "Treats setup, runnable samples, and docs as one product ... so a developer reaches first success in minutes with zero help"

**Prerequisites:** [Code-sample validation](code-sample-validation.md), [Reproducible environments](reproducible-environments.md)

## What it is

Running the quickstart from an environment that has nothing: a fresh virtual
environment, a clean container, no caches, no credentials the instructions did
not mention. The test is not whether the commands work. It is whether the
*document* is complete.

Intel names it explicitly, which is unusual and tells you something about what
they have been burned by.

## Why the job asks for it

Because a quickstart is the only page whose author is structurally incapable of
testing it. The author has the SDK installed, the token exported, the
repository cloned, a Python with the right version, and three dependencies they
installed last March for something else. They run their own quickstart, it
works, and they ship it.

Then a developer who has none of that follows it and hits `ModuleNotFoundError`
on step two. That developer is now evaluating your product on the basis of a
document that was never true for anyone but its author.

Intel's phrasing is "first success in minutes with zero help." Cold-start
testing is the only mechanism that measures whether that claim holds, and it is
why they list setup, samples and docs as one product. A quickstart is not prose
with code in it. It is an executable artifact that happens to be readable.

## The golden path

Watch a quickstart that passes on your machine fail from a clean environment.
About thirty-five minutes.

**Step 1: a quickstart with a hidden assumption**

````bash
mkdir -p cold-demo/docs && cd cold-demo
cat > docs/quickstart.md <<'MDEOF'
# Quickstart

Install it:

```bash
pip install cowsay
```

Use it:

```bash
python3 -c "import cowsay, requests; print('ok')"
```
MDEOF
````

The install step mentions one package. The sample imports two.

**Step 2: confirm it passes on this machine**

```bash
python3 -c "import requests; print('system-wide:', requests.__version__)"
```

```
system-wide: 2.34.2
```

`requests` is already here, because something installed it once. An author
testing this quickstart in their normal shell sees it work, and the omission is
invisible to them. It is also invisible to
[sample validation](code-sample-validation.md), which runs in the same ambient
environment.

**Step 3: a harness that starts from nothing**

```bash
cat > coldstart.sh <<'EOF'
#!/usr/bin/env bash
# Follow the quickstart literally, from an empty virtual environment.
set -euo pipefail
WORK="$(mktemp -d)"; trap 'rm -rf "$WORK"' EXIT
cd "$WORK"

python3 -m venv .venv
source .venv/bin/activate

# Extract the bash blocks from the quickstart, in order, and run them as one
# shell so that cd and exported variables persist.
python3 - <<'PY' > script.sh
import re
from pathlib import Path
FENCE = re.compile(r"^```(\w+)?\s*$")
out, cur, lang = [], None, None
for line in Path("DOCS").read_text().splitlines():
    m = FENCE.match(line)
    if m and cur is None:
        cur, lang = [], m.group(1)
    elif m and cur is not None:
        if lang == "bash":
            out.append("\n".join(cur))
        cur = None
    elif cur is not None:
        cur.append(line)
print("\n".join(out))
PY

bash -e script.sh
EOF
chmod +x coldstart.sh
```

The important properties: a temp directory so nothing touches the repository, a
virtual environment with no system packages, and the blocks run in document
order as a single shell.

**Step 4: run it**

```bash
./coldstart.sh
```

```
Traceback (most recent call last):
  File "<string>", line 1, in <module>
    import cowsay, requests; print('ok')
ModuleNotFoundError: No module named 'requests'
exit=1
```

The defect the author could not see. The page is incomplete, and only an
environment with nothing in it can say so.

**Step 5: fix the document, not the environment**

```bash
sed -i 's|pip install cowsay|pip install cowsay requests|' docs/quickstart.md
./coldstart.sh
```

```
Successfully installed certifi-2026.10.23 charset_normalizer-3.5.2 cowsay-6.1 idna-3.20 requests-2.34.2 urllib3-2.8.0
ok
exit=0
```

Note the direction of the fix. The temptation when a cold start fails is to
make the harness more permissive, by using `--system-site-packages` or
pre-installing the dependency. That converts the one check capable of finding
this class of defect into a check that cannot. **The environment is the
specification. If the test fails, the document is wrong.**

**Step 6: know what it costs**

```
cold start (venv + install + run):     ~3.9s
sample execution only (no fresh env):  ~0.04s
```

Two orders of magnitude on a toy. On a real project, where the install pulls a
compiled dependency or a container image, it is minutes against milliseconds.
That ratio is why this runs as its own CI job rather than alongside the fast
gates.

**What you built.** A check that reads the quickstart as a reader would, with
none of the author's advantages.

## Reference

### What each environment can detect

| Environment | Catches an undeclared dependency | Catches a missing step | Catches a wrong version pin | Speed |
|---|---|---|---|---|
| The author's shell | No | No | No | Instant |
| Fresh virtual environment | Yes, for Python packages | Yes | Yes | Seconds |
| Fresh container | Also system packages, locales, system Python | Yes | Yes | Minutes |
| Fresh container, no network cache | Also a dead package index or yanked release | Yes | Yes | Minutes |

Pick the weakest environment that catches your actual failures. A virtual
environment covers most Python quickstarts; a container is required the moment
your instructions say `apt install`.

### The assumptions a cold start flushes out

| Assumption | How it shows up |
|---|---|
| An undeclared dependency | `ModuleNotFoundError`, as above |
| A pre-existing credential | An auth error on a step the author never authenticated for |
| A cloned repository | `cd myproject` with no preceding `git clone` |
| A specific interpreter version | A syntax error, or a dependency resolving differently |
| A warm cache | A timeout, or a surprising first-run message in the expected output |
| A tool installed years ago | `command not found` |
| An implied working directory | A path that resolves only from the author's home |

### Rules that keep it honest

| Rule | Reason |
|---|---|
| Never relax the environment to pass | The isolation *is* the test |
| Run the document, do not reimplement it | A separate script drifts from the page |
| Blocks run in document order, as one shell | A quickstart is a sequence; `cd` must persist |
| Assert the final output, not just exit codes | "First success" means the reader saw the right thing |
| Pin nothing the document does not pin | If the quickstart is unpinned, test it unpinned and accept the flakiness as information |
| Its own CI job | Minutes, not seconds; do not gate typo fixes on it |

That fifth rule is contentious and worth holding. An unpinned quickstart that
breaks because a dependency released a major version has told you something
true about what a reader will experience today. Pinning the test environment
hides that until a reader reports it.

### Where it sits among the other checks

| Check | Question |
|---|---|
| [Link checking](link-checking.md) | Do the cross-references resolve? |
| [Sample validation](code-sample-validation.md) | Do the examples still run and return the right thing? |
| [Doc test harness](doc-test-harness.md) | Can we run samples in several languages with attribution? |
| Cold-start testing | Is the document *complete*? |

Only the last one is about omissions, and omissions are what make a quickstart
fail for a stranger.

## How to talk about it

**Lead with the author's blind spot.** "A quickstart is the one page its author
cannot test, because their machine already has everything. So it runs from an
empty virtual environment in CI, following the document's own blocks in order.
The failures it finds are always omissions: an undeclared dependency, a missing
clone, a token nobody mentioned."

**The follow-up is about cost**, and the answer is that it runs as its own job
on a schedule or per pull request, never in the fast feedback path, because the
ratio is seconds against milliseconds and more like minutes in a container.

**The tradeoff to volunteer.** Cold-start tests are the flakiest check you will
own, because they depend on package indexes and the network, and a flaky
required check trains people to re-run CI until green. The mitigations are a
separate job, a retry on genuine network failure only, and a clear rule about
who investigates a red cold start. Do not pretend it is as deterministic as a
unit test.

**One sharper point, and the thing to say if you say one thing.** When a cold
start fails, the fix is in the document, not the harness. Every instinct pushes
the other way, because pre-installing the dependency makes the build green in
one line. That single decision is the difference between a cold-start test and
a cold-start-shaped piece of theatre.

## How to prove it

**The artifact.** A script that creates a clean environment, extracts the
quickstart's own commands, runs them in order, and asserts the final output.

**Three things to do, in order:**

1. Run the golden path. Step 2 and step 4 together are the demonstration: the
   same page, passing and failing, depending only on what the environment
   already had.
2. Write `coldstart.sh` for a project you own and run it once. Whatever it
   finds has been in your quickstart for months. If it passes on the first
   run, check that the environment really was empty: a cold-start script that
   goes green immediately is usually testing the machine it was written on.
3. Time it, and put the number in the README. The cost is the reason it lives
   in its own job, and knowing the number is how you defend that decision.

**What makes it credible rather than decorative.** `docpack`'s
`scripts/coldstart.sh` builds a fresh virtual environment, installs the way a
reader would, follows the tutorial literally, and asserts the exact output
string the tutorial promises. The exact-output assertion is the part worth
pointing at: without it, the script proves the commands exit zero, not that the
reader reached first success.

## Related

- [Reproducible environments](reproducible-environments.md), what the harness has to build
- [Quickstarts](quickstarts.md), the page under test
- [Code-sample validation](code-sample-validation.md), the warm-environment version
- [Time to first success](time-to-first-success.md), the metric this protects
