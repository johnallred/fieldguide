---
title: Developer advocacy
summary: "Making documentation part of the definition of done needs a gate at capability granularity, and three plausible gates at the wrong granularity all fail in ways that get them switched off."
diataxis: explanation
audience: developer
concept: developer-advocacy
tags: [edu, supporting]
---

# Developer advocacy

`supporting` · difficulty 2 · 3h

!!! quote "Asked for by name"
    Intel: "Partner with engineering, product, and developer advocates so each new capability ships with tested documentation"

## What it is

The part of this job that happens in other people's meetings. Advocacy in the
sense Intel's bullet means is not conference talks and not evangelism: it is
arranging that documentation is produced as part of shipping, by the people who
built the thing, rather than reconstructed afterwards by someone who did not.

The operative phrase is **ships with**. Everything else in the sentence
describes who you have to work with to make that true.

## Why the job asks for it

Because the alternative does not scale and everyone knows it.

A documentation team that writes everything is a queue. Features ship, the
queue lengthens, the docs describe the product of six months ago, and the team
is measured on throughput against an inflow it does not control. The structural
fix is to move authorship to the point where the knowledge already exists, and
that is an organisational change rather than a writing one, which is why it
appears in a job posting as "partner with".

The reason it needs a mechanism rather than goodwill is that goodwill does not
survive a deadline. A definition of done that includes documentation, enforced
in the same place as the tests, is the only version of this that is still true
in the fourth quarter.

And the reason the mechanism is hard is the subject of the golden path: a docs
gate at the wrong granularity produces failures that engineers correctly
identify as noise, and a gate that cries wolf gets switched off within a month.
The gate's design is the whole job.

## The golden path

Build the "ships with documentation" gate against a real package, four times,
getting it wrong three ways. About thirty minutes.

**Step 1: the obvious gate, per public symbol**

```python
for node in ast.parse(f.read_text()).body:
    if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and not node.name.startswith("_"):
        rows.append((f.name, node.name, ast.get_docstring(node) is not None))
```

```
public symbols in the package: 44 across 7 modules
with a docstring: 37/44 (84%)
undocumented:
   cli.py::build_parser
   cli.py::cmd_check
   cli.py::cmd_build
   cli.py::cmd_new
   cli.py::cmd_status
   cli.py::cmd_render
   cli.py::main
```

Eighty-four per cent, and every failure in one module. Look at what it is
accusing:

```
fieldguide build   named in the documentation 32 times
fieldguide check   named in the documentation  5 times
fieldguide new     named in the documentation  5 times
```

The functions without docstrings are the command handlers, and the commands
they implement are **the best-documented part of the entire system**. They are
documented as commands, in prose, in the place a user looks, which is the
correct way to document a command and invisible to a gate that counts
docstrings.

This is how docs gates die. An engineer reads that failure, sees it is wrong,
and is right.

**Step 2: the second gate, per symbol named in the prose**

```
public symbols never named in the documentation: 28/44
   demos.py::DemonstrationError
   demos.py::Demonstration
   fences.py::Span
   dialect.py::front_matter_findings
   ...
```

Worse. Most of those 28 are internal plumbing whose public-ness is an artifact
of Python not having private modules. `Span` is a dataclass used in one place.
Documenting it would be writing documentation nobody will read in order to
satisfy a counter, which is the characteristic output of a badly aimed gate.

Both gates are measuring symbols. The posting says **capability**.

**Step 3: the third gate, per shipped capability**

Ask the program what it ships, rather than inferring it from the source:

```python
subcommands = sorted(next(a.choices for a in build_parser()._actions
                          if getattr(a, "choices", None) and isinstance(a.choices, dict)))
```

```
  build    named in the documentation 32 time(s)
  check    named in the documentation 5 time(s)
  new      named in the documentation 5 time(s)
  render   named in the documentation 1 time(s)
  status   named in the documentation 0 time(s)   <-- ships undocumented
```

A real finding, apparently: a shipped command documented nowhere. Except the
gate searched `docs/` and the README has listed `fieldguide status` in its
quick start since the first commit.

Three gates, three wrong answers, and the third was wrong about *scope* rather
than granularity: documentation is not only the thing in the docs directory.

**Step 4: the gate that works, and what it actually finds**

Capability granularity, every surface a reader looks at:

```
command      docs/   README.md
  build         32       2
  check          5       1
  new            5       1
  render         1       0
  status         0       2
```

Every capability is documented somewhere, and two defects are now visible that
none of the first three gates could see:

`render` is absent from the README's quick start, which is the entry point
readers actually use; it is mentioned once, deep in a page. And while checking
the README against reality:

```
README.md:59  python -m pytest -q   # 72 tests
actual:       119 tests
```

The claim had been stale for the length of this project. Both fixed in the same
commit as the gate, which is the point: the gate is only worth adding if the
first run is allowed to find something.

```python
undocumented = [s for s in subcommands if not re.search(rf"fieldguide {s}\b", prose)]
assert not undocumented, f"shipped but undocumented: {', '.join(undocumented)}"
```

**Step 5: why the granularity argument is the advocacy work**

The gate took twenty minutes to write and three attempts to aim. The reason
that matters is not the code. It is that **the first two versions would have
been rejected by engineers, correctly**, and the rejection would have been
remembered as "the docs team wanted docstrings on everything" for years.

Partnering with engineering on a documentation gate is mostly the work of
making sure the gate is right before anyone else sees it, because you get
roughly one attempt at a definition of done before the proposal acquires a
reputation. Run it on your own repository, let it fail, fix what it finds, and
bring the number rather than the principle.

**What you built.** A documentation gate at capability granularity, wired into
the test suite, plus three instructive wrong versions and two real defects the
right version found on its first run.

## Reference

### Granularity, and what each level gets wrong

| Gate | Flags | Verdict |
|---|---|---|
| Every public symbol has a docstring | Command handlers, documented as commands | Wrong unit |
| Every public symbol is named in prose | Internal plumbing | Wrong notion of public |
| Every capability is named in `docs/` | A capability documented in the README | Wrong scope |
| Every capability is named where readers look | `render` missing from the quick start | Usable |
| Every capability has a *tested* example | The honest target | Expensive, and correct |

The last row is what Intel's sentence actually asks for, and it needs
[code-sample validation](code-sample-validation.md) underneath it to mean
anything.

### A definition of done that survives a deadline

| Item | Enforced by | Fails usefully |
|---|---|---|
| The capability is named in user-facing docs | The gate above | Yes |
| An example exists | A sample manifest | Yes |
| The example runs and asserts its output | CI | Yes |
| The changelog mentions it | A release check | Yes |
| A page explains when to use it | Nothing; needs a person | No |

The bottom row is the honest limit of mechanisation, and pretending otherwise
is how a definition of done becomes a form.

### Who writes what

| Content | Best author | Why |
|---|---|---|
| What it does and the first example | The engineer who built it | They have the knowledge now |
| Reference detail | Generated from source | Nobody should type it twice |
| When to use it, and when not | The docs or advocacy role | Needs the comparison across features |
| The quickstart it affects | The docs role | It is a shared artifact |
| The migration note | Both | One knows the change, one knows the readers |

The common failure is the docs role writing row one, which puts a transcription
step between the knowledge and the reader and guarantees the result is late and
thinner.

### What makes a partnership proposal land

| Do | Instead of |
|---|---|
| Run the gate on your own repo first | Proposing it in a meeting |
| Bring the defects it found | Bringing the principle |
| Make the failure message name the fix | A generic "docs missing" |
| Gate capabilities, not symbols | Anything that flags working docs |
| Let it fail on your code publicly | Exempting yourself |
| Count the false positives before shipping it | Discovering them in review |

### What this concept is not

| Not | Belongs to |
|---|---|
| Conference talks | [Developer relations](publishing-in-public.md), a different job |
| Writing all the documentation | The queue this is meant to replace |
| Reviewing every pull request for docs | Does not scale; gate it |
| Persuasion | Mechanism outlives persuasion |

## How to talk about it

**Lead with what "ships with" implies.** "A documentation team that writes
everything is a queue, and the queue is always behind an inflow it does not
control. So the work is moving authorship to where the knowledge already is,
and making documentation part of the definition of done in the same place the
tests live, because goodwill does not survive the fourth quarter."

**The follow-up is how you would enforce it, and this is the part worth telling
in detail.** I built that gate against my own package and got it wrong three
times. Docstring coverage flagged the five CLI handlers, which are the
best-documented part of the system because they are documented as commands.
Per-symbol prose coverage flagged internal plumbing that nobody should
document. Capability coverage over the docs directory flagged a command that
had been in the README's quick start from the first commit. The fourth version,
capabilities against every surface a reader looks at, passed and immediately
found two real things: one command missing from the quick start, and a README
claiming 72 tests when there were 119.

**The point that makes this advocacy rather than scripting.** The first two
gates would have been rejected by engineers, correctly, and the rejection would
have been remembered as "the docs team wanted docstrings on everything" for
years. You get about one attempt at a definition of done before the proposal
acquires a reputation, so the real work is aiming the gate before anyone else
sees it: run it on your own repository, let it fail, fix what it finds, and
bring the number instead of the principle.

**The tradeoff to volunteer.** A gate can only check that documentation exists,
never that it is any good. "When to use this and when not" is the most valuable
thing in a reference and no mechanism will ever require it. So the gate buys
coverage and the review still has to be human, and a team that mistakes the
first for the second ends up with complete documentation nobody can use.

## How to prove it

**The artifact.** A test in a repository of yours that enumerates shipped
capabilities from the program itself and fails when one is undocumented, plus
the commit where its first run fixed something.

**Three things to do, in order:**

1. Write the gate for your own project at capability granularity, run it, and
   count the false positives before telling anyone it exists. Predict the count
   first; this page's subject is that the prediction is usually zero and the
   answer usually is not.
2. Check your README's claims against reality. Mine said 72 tests and there
   were 119, and nothing had ever checked, which is the cheapest class of
   defect there is.
3. Find the last capability your team shipped and ask who wrote its first
   example. If the answer is the docs role, there is a transcription step in
   the pipeline, and that is the thing to propose removing.

**What makes it credible rather than decorative.** The gate exists, lives in
this guide's test suite, enumerates subcommands from the parser rather than
from a list, and its first run produced two fixes in the README. What is not
demonstrated is the partnership: this is a one-person repository, so no
engineering team has been persuaded of anything, and the claims about how a
proposal lands are reasoning from the gate's three wrong versions rather than
from organisational experience. The [demonstrated](../demonstrated.md) page
records that split.

## Related

- [Code-sample validation](code-sample-validation.md), what "tested documentation" needs underneath it
- [Documentation CI](documentation-ci.md), where a gate like this runs
- [Release readiness](release-readiness.md), the checklist this belongs on
- [Guided workflows](guided-workflows.md), the same standard encoded as a process
- [Publishing in public](publishing-in-public.md), the outward-facing half of this role
