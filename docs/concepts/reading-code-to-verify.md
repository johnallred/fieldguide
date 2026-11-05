---
title: Reading code to verify accuracy
summary: Checking a documented claim against the implementation instead of against the person who told you.
diataxis: explanation
audience: developer
concept: reading-code-to-verify
tags: [craft, core]
---

# Reading code to verify accuracy

`core` · difficulty 2 · 5h

> Enough technical depth to read code and APIs, verify accuracy, and write working examples

> Source: nvidia posting, verbatim

## What it is

Opening the implementation to check whether a documented claim is true, rather
than asking the person who wrote it. Specifically: finding the default value,
the validation rule, the error path, and the thing the docstring forgot.

It is not software engineering. The skill is narrow and reading-only: navigate
an unfamiliar codebase well enough to answer one factual question, then get out.

## Why the job asks for it

NVIDIA puts this in minimum qualifications, and the phrasing is precise: "enough
technical depth to read code and APIs, verify accuracy, and write working
examples." The word doing the work is **enough**. They are not asking you to
contribute to the simulation engine. They are asking you to stop being dependent
on an engineer's memory.

That dependency is the thing to understand. Here is the default workflow in a
documentation team that cannot read code: you notice a page might be wrong, you
ask in Slack, an engineer answers from memory, you write down what they said.
Every step of that is slow, and the last one is unreliable in a specific way.
An engineer's memory of a default value is a memory of what it was when they
wrote it. Defaults change in pull requests that nobody thought were
documentation changes.

On a Tuesday it looks like this. The page says the visibility timeout defaults
to 30 seconds. You open the client, find the constructor, and the default is
`None`, which falls through to a server-side value that is 60 seconds in one
region. Nobody lied; the page was right two years ago. **You could only find
that by looking.**

The second reason, and the one that gets you hired: it changes what you are in
a room with engineers. A writer who arrives with "the page says 30, the
constructor says None, which is right?" gets a different conversation than one
who arrives with "can you explain timeouts to me." It is the difference between
being a channel and being a reviewer, and it is most of what
[implementation feedback](implementation-feedback.md) rests on.

## The golden path

Verify three documented claims against a real codebase you have never read.
About forty minutes.

**Step 1: get a codebase and its docs**

```bash
mkdir -p verify-drill && cd verify-drill
python3 -m venv .venv && source .venv/bin/activate
pip install --quiet requests
python -c "import requests, pathlib; print(pathlib.Path(requests.__file__).parent)"
```

`requests` is a good target: widely documented, widely misdocumented in blog
posts, and small enough to navigate.

**Step 2: pick claims that are checkable**

A claim is checkable when it names a value, a type, or a behaviour on a
specific input. "Requests is user-friendly" is not checkable.

```bash
cat > claims.md <<'EOF'
1. `requests.get()` follows redirects by default.
2. `requests.get()` has no timeout by default.
3. `raise_for_status()` raises on a 4xx or 5xx response.
EOF
cat claims.md
```

**Step 3: find the answer in the source, not in the docs**

The technique is three tools in a fixed order: find the entry point, read the
signature, follow one level down.

```bash
python3 - <<'PY'
import inspect, requests

# Claim 1 and 2: the signature carries the defaults.
print("--- requests.get signature ---")
print(inspect.signature(requests.get))
print()
print("--- requests.request signature (one level down) ---")
print(inspect.signature(requests.Session.request))
PY
```

Read the output before continuing, because it teaches the lesson better than
this page can.

`requests.get` does **not** show you the defaults. Its signature is
`(url, params=None, **kwargs: Unpack[GetKwargs])`. The convenience wrapper
forwards everything through typed keyword arguments, so the defaults are not
visible at the level a reader naturally looks.

One level down, `Session.request` shows them plainly: `timeout=None` and
`allow_redirects=True`. Claims 1 and 2 are confirmed, but only from the second
signature.

That is the whole technique in one observation. **The signature of the function
you call is often not the signature that holds the defaults**, and a writer who
stops at the first one documents a default of "whatever the wrapper does". When
you see `**kwargs`, you are not finished.

An earlier draft of this page asserted that `requests.get` shows
`allow_redirects=True`. Running the step is what proved otherwise.

**Step 4: when the signature is not enough, read the body**

Claim 3 is about behaviour, so the signature cannot answer it.

```bash
python3 - <<'PY'
import inspect, requests
source = inspect.getsource(requests.Response.raise_for_status)
# Print only the lines that decide something: the conditions and the raises.
for line in source.splitlines():
    stripped = line.strip()
    if stripped.startswith(("if ", "elif ", "raise ")):
        print(stripped)
PY
```

That shows the actual boundaries: which status ranges produce which error class.
Note what you have now that the documentation did not give you, which is the
exact condition rather than a summary of it.

**Step 5: verify by running it, which is the only check that cannot be wrong**

```bash
python3 - <<'PY'
import requests

# Claim 3, tested rather than read.
r = requests.Response()
r.status_code = 404
try:
    r.raise_for_status()
    print("404: did NOT raise  <- claim is false")
except Exception as exc:
    print(f"404: raised {type(exc).__name__}  <- claim holds")

r.status_code = 204
try:
    r.raise_for_status()
    print("204: did not raise  <- claim holds")
except Exception as exc:
    print(f"204: raised {type(exc).__name__}  <- unexpected")
PY
```

**What you built.** Three claims verified against an implementation you had
never opened, using four techniques in increasing cost order: signature, then
body, then the conditions only, then execution. That escalation *is* the skill.
Most questions stop at step 3, and a writer who knows to look at the signature
first answers in thirty seconds what otherwise becomes a Slack thread.

## Reference

### The escalation, cheapest first

| Technique | Answers | Cost |
|---|---|---|
| Read the signature | Defaults, types, required arguments | Seconds |
| Follow `**kwargs` one level down | The defaults the wrapper hid | Seconds |
| Read the docstring, then distrust it | What the author intended | Seconds |
| Grep for the constant | Where a magic number really comes from | A minute |
| Read the function body's conditionals | Boundaries, error paths | Minutes |
| Read the tests | Intended behaviour, including edge cases | Minutes |
| Run it | The truth | Minutes |

**The tests are the most underrated row.** A test suite is executable
documentation of intent, it is maintained because it fails otherwise, and it
usually contains exactly the edge cases your page is missing.

### Python tools worth knowing by heart

| Tool | Use |
|---|---|
| `inspect.signature(f)` | Defaults and parameter names without reading source |
| `inspect.getsource(f)` | The actual body |
| `inspect.getfile(m)` | Where a module lives on disk |
| `help(f)` | Docstring plus signature |
| `python -m pdb` | Step through to see which branch is taken |
| `git log -S"30"` / `git blame` | When and why a value changed |
| `rg "DEFAULT_"` | Constants, which is where defaults usually hide |

`git log -S` is the one that wins arguments. It finds the commit that introduced
a value, which tells you whether the documentation or the code is the thing that
drifted.

### What makes a claim checkable

| Checkable | Not checkable |
|---|---|
| "The default is 30 seconds" | "Performance is good" |
| "Raises `ValueError` on an empty list" | "Handles errors gracefully" |
| "Retries 3 times" | "Is resilient to failure" |
| "Requires Python 3.10 or newer" | "Works with modern Python" |

The right-hand column is not just vague writing. It is **unverifiable**, which
means it can never be found wrong, which means it will rot without any signal.
Rewriting an unverifiable claim into a checkable one is a documentation
improvement before anyone checks it.

### Where documented claims go wrong, in order of frequency

1. **A default changed** and the pull request did not touch the docs.
2. **The documented default is the library's, and a layer above overrides it.**
3. **The error class is wrong**, usually a parent class named instead of the
   specific one.
4. **A version requirement is stale**, having been raised without a docs change.
5. **The example works only in the author's environment**, which is what
   [cold-start testing](coldstart-testing.md) exists for.

## How to talk about it

**What a competent answer sounds like.** Give a concrete catch. "The page said
the visibility timeout defaulted to 30 seconds. The constructor passes `None`,
which falls through to a server-side default that differs by region. The page
had been right two years earlier. I found it by reading the signature, and I
fixed the class of problem by adding a check that compares documented defaults
against the signatures."

That last clause is the one that gets remembered, because it is
[the systems mindset](systems-mindset.md) in the same breath.

**The follow-up is "what do you do when you cannot read the code",** meaning a
compiled component, a service you have no access to, a C++ simulation kernel.
This is a real situation at NVIDIA in particular. The honest answer has three
parts. Read the public API surface and the tests, which are usually available
even when the implementation is not. Verify behaviour by running it and
observing, which is slower but authoritative. And when neither is possible,
**document the claim's provenance in the page**, so a future reader knows it
came from an engineer's statement in 2026 rather than from the code. The failure
mode to avoid is writing an unsourced claim with the same confidence as a
verified one.

**The tradeoff to volunteer.** Verification is slow, and the slowness is not
distributed evenly: it is most expensive exactly when you are new, which is when
you have the most pages to write. A writer who verifies every claim on every
page ships very little. The judgement is about which claims are worth it, and
the useful heuristic is **verify anything a reader will paste, and anything
numeric.** A conceptual sentence being slightly imprecise costs a reader some
confusion. A wrong default costs them an afternoon.

**One sharper point.** The real value is not the errors you catch, it is that
**verifiability becomes a property you can design for.** Once you are the person
who checks, you start writing claims in forms that a script could check later,
which is how you get from manual verification to
[freshness monitoring](freshness-monitoring.md) and
[doc test harnesses](doc-test-harness.md). The reading skill is the thing that
teaches you what is automatable.

## How to prove it

**The artifact.** A pull request fixing a documented claim, with the source
reference in the description. That is a small, specific, unfakeable thing, and
open-source projects are full of opportunities for it.

**Three things to do, in order:**

1. **Run the golden path, then do it for real.** Pick a library you use, choose
   five documented claims about defaults or error behaviour, and check them. In
   a mature project you will find at least one wrong. File it.
2. **Write the check that would have caught it.** If the claim was a default
   value, write twenty lines that compare documented defaults against
   `inspect.signature` and fail if they disagree. This is the step that converts
   a catch into a system, and it is a genuinely strong portfolio piece.
3. **Add provenance to one page.** Take a page with claims you cannot verify
   and mark which ones came from a conversation rather than from code. Then go
   verify the two that matter most. The marking is the discipline; the
   verification is the payoff.

**What makes it credible rather than decorative.** Saying you can read code is unfalsifiable. A merged
pull request that says "the docs say 30, the signature says None, here is the
commit that changed it" is not. One of those is worth more than a paragraph of
self-assessment.

### How this would be demonstrated elsewhere

This is the most nearly demonstrable of the craft concepts, and it still is
not, because the artifact is a correction and a correction looks identical
whether you found it by reading code or were told about it.

**What you need.** A codebase you did not write and its documentation. Nothing
else. The exercise works better the less you know about the language, which is
the counter-intuitive part: verifying a documented default does not require
fluency, it requires knowing where defaults live.

**What a learner would do.** Take ten specific, checkable claims from someone
else's documentation, the kind with a value in them, and verify each against
the source:

```
"defaults to 30 seconds"        -> find the constant
"retries three times"           -> find the loop bound
"is idempotent"                 -> find the write path
"returns 404 if absent"         -> find the error branch
"logs at warning level"         -> find the call
```

Record, for each, whether the claim held and how long it took to settle. The
second number is the one that matters: a claim you cannot verify in ten minutes
is a claim the documentation should not have made in that form.

**What you would find, in rough proportions.**

| Outcome | Rough share | What it means |
|---|---|---|
| Claim correct and easy to verify | about half | The healthy case |
| Claim correct, hard to verify | common | The value is now indirect; say where it comes from |
| Claim stale: true of an older version | a few | The commonest documentation defect of all |
| Claim true of one path, false of another | a few | The most dangerous kind |
| Claim unverifiable from source alone | some | Runtime or deployment behaviour |

The fourth row is the one worth hunting. "Idempotent" is usually true of the
documented endpoint and false of a code path reached under retry, and that
distinction is invisible unless somebody reads both.

**What competence looks like.** A correction with a file and line in it. A
documented value that now matches a named constant. A claim rewritten from "is
idempotent" to "is idempotent for the documented endpoint; the bulk path is
not". And, most persuasive, a generated reference that removed the need for the
exercise entirely.

**Why it does not commit.** The correction commits; the reading does not. A
reviewer sees "fix timeout default: 30s not 60s" and cannot tell whether it came
from the source, a ticket or a guess that happened to be right. The strongest
available evidence is a habit of citing the file in the commit message, which is
cheap and still only evidence of a habit.

## Related

- [Technical writing as a craft](technical-writing.md), the other half of the job
- [Code-sample validation](code-sample-validation.md), this automated
- [Freshness monitoring](freshness-monitoring.md), where verification goes when it scales
- [Giving architecture owners implementation feedback](implementation-feedback.md), what this buys you socially
