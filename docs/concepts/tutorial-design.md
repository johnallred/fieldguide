---
title: Designing tutorials
summary: "Measuring how long a tutorial leaves the reader without feedback, which is where its defects hide."
diataxis: how-to
audience: developer
concept: tutorial-design
tags: [gp, core]
---

# Designing tutorials

`core` · difficulty 2 · 4h

!!! quote "Asked for by name"
    Intel: "Write and maintain reference documentation, tutorials, and sample walkthroughs that assume no prior context"

**Prerequisites:** [Diátaxis](diataxis.md)

**Leads to:** [Sample walkthroughs](sample-walkthroughs.md)

## What it is

A lesson. The reader follows it to learn, and the working thing at the end is
evidence that they learned rather than the point of the exercise. That is what
separates it from a [quickstart](quickstarts.md), which optimises for the
working thing and teaches as little as it can get away with.

Intel's phrase is "assume no prior context", which is the hard constraint. The
design question this page is built on is narrower and measurable: **how long
does your tutorial leave the reader with no way to tell whether it is
working?**

## Why the job asks for it

Because a tutorial is where a reader decides whether the product is for them,
and because its failures are structural rather than stylistic.

The common structural failure is sequencing. An author who knows the
architecture builds it in architectural order: configuration module, then
domain logic, then the interface, then run it. That is how you would build it
if you already understood it, and it means the reader types for twenty minutes
before anything can possibly produce output. Every mistake they make in those
twenty minutes surfaces at once, at the end, attributed to the wrong place.

That is a measurable property, not a matter of taste, which is what the golden
path demonstrates.

## The golden path

Measure blind-run length on two tutorials, then watch what a long one hides.
About forty minutes.

**Step 1: the same tutorial, sequenced two ways**

The architectural ordering, eight steps, output only at the end:

````bash
mkdir -p tut-demo && cd tut-demo
cat > tut-bad.md <<'MDEOF'
# Build a sync tool

## Step 1
```bash
mkdir sync && cd sync
```
## Step 2
```bash
python3 -m venv .venv && source .venv/bin/activate
```
## Step 3
```bash
pip install widget click
```
## Step 4
```bash
mkdir src tests
```
## Step 5
```bash
cat > src/config.py <<'EOF'
DEFAULTS = {"retries": 5}
EOF
```
## Step 6
```bash
cat > src/sync.py <<'EOF'
from .config import DEFAULTS
def run(): return DEFAULTS
EOF
```
## Step 7
```bash
cat > src/cli.py <<'EOF'
import click
@click.command()
def main(): print(run())
EOF
```
## Step 8
```bash
python -m src.cli
```
```
{'retries': 5}
```
MDEOF
````

And the same lesson sequenced so that something runs immediately, then grows:
step 1 gets a working command-line tool that prints a message, step 2 adds the
configuration.

**Step 2: measure the blind run**

A step gives feedback when it shows expected output, which by this guide's
convention is an untagged fence alongside the commands:

```python
OPEN = re.compile(r"^```(\w*)\s*$", re.M)

def has_output_block(step):
    openers = OPEN.findall(step)[::2]   # fences alternate open/close
    return any(t == "" for t in openers)

fb = [has_output_block(s) for s in steps]
longest = cur = 0
for f in fb:
    cur = 0 if f else cur + 1
    longest = max(longest, cur)
```

```
tut-bad.md     steps= 8 feedback_at=[8] first=8 longest_blind_run=7
tut-good.md    steps= 2 feedback_at=[1, 2] first=1 longest_blind_run=0
```

Seven steps on faith against zero. The first number to care about is
`first`: the reader of the bad tutorial has no evidence anything works until
step 8.

**Step 3: follow the bad tutorial exactly and see what happens**

```bash
python -m src.cli; echo "exit=$?"
```

```
exit=0
```

Nothing. No output, no error, exit zero. The reader has done eight steps and
the tutorial's final command produces silence, so they cannot tell whether they
succeeded, mistyped something, or are looking at a broken tutorial.

The cause is that step 7 wrote a `click` command and no `if __name__ ==
"__main__"` guard, so `python -m` imports the module and exits.

**Step 4: add the guard, and find the next defect**

```bash
cat >> src/cli.py <<'EOF'
if __name__ == "__main__":
    main()
EOF
python -m src.cli
```

```
    def main(): print(run())
                      ^^^
NameError: name 'run' is not defined
```

A second defect: step 7's `cli.py` never imports `run` from `sync.py`. And
behind it sits a third, which only surfaces after that one is fixed, because
`config.py` as written would be imported for a name it does define but
`sync.py` imports under a different spelling in the typo variant of this
exercise.

**Three independent defects, stacked across seven unverified steps, and the
first symptom was silence.** Any one of them would have been obvious the moment
the reader ran something. The sequencing is what let them accumulate.

**Step 5: the rule that follows**

Order the tutorial so that something observable happens as early as possible,
and keep the blind run short:

| Metric | Target |
|---|---|
| Steps before first observable output | 1 |
| Longest run of steps with no output | 1, or 2 at most |
| Final step produces something | Always; silence is not success |

The reordering is not cosmetic. The good version reaches a working
command-line tool in step 1 and then *changes* it in step 2, which is more
work to write and strictly better to follow, because every defect is
attributable to the step that introduced it.

**What you built.** A measurement that turns tutorial sequencing from a
stylistic preference into a number, and a demonstration of what the number
predicts.

## Reference

### Tutorial against its neighbours

| | Tutorial | [Quickstart](quickstarts.md) | How-to | [Walkthrough](sample-walkthroughs.md) |
|---|---|---|---|---|
| Goal | Learning | Working, fast | One task done | Understanding existing code |
| Reader builds | Yes, incrementally | Minimal | Nothing new | Nothing |
| Explanation | Essential | Almost none | Brief | Essential |
| Detours | If they teach | Never | No | Not applicable |
| Length | As long as the lesson | Shortest possible | One task | One sample |

### Design rules that hold up

| Rule | Why |
|---|---|
| Something runs in step 1 | See the golden path |
| Every step is verifiable | So defects are attributable |
| One new idea per step | Two ideas per step means an ambiguous failure |
| Build up, do not reveal | A finished file dropped in teaches nothing |
| The reader types, you explain | Not the other way round |
| Nothing unexplained | "Assume no prior context" |
| State the time and the result up front | So the reader can decide to start |

The "build up, do not reveal" rule is where architectural ordering comes from
and where it goes wrong. Building up is right; building up in the order *you*
would build it is not, because that order defers running anything.

### What to cut

| Cut | Where it goes |
|---|---|
| Alternatives and platform variants | A how-to |
| Why the design is the way it is | An explanation |
| Every option on every command | Reference |
| Error handling the lesson does not need | A later tutorial |
| Production concerns | An operations guide |

A tutorial that handles errors properly is a tutorial nobody finishes. Say that
you are deliberately omitting it, and link where it is covered.

### Testing a tutorial

| Check | Catches |
|---|---|
| [Cold-start test](coldstart-testing.md) | Undeclared dependencies, missing steps |
| Output assertion per step | The silent-success failure in step 3 |
| Blind-run measurement | Sequencing that hides defects |
| A reader who does not know the product | Everything else, and nothing else can |

The last row is irreplaceable. Blind-run length tells you where defects *can*
hide; only a real learner tells you whether the explanation lands.

## How to talk about it

**Lead with the measurement.** "The structural failure in tutorials is
sequencing. An author who knows the architecture builds it in architectural
order, so the reader types for twenty minutes before anything can produce
output. I measure the longest run of steps with no observable result: on an
eight-step tutorial written that way it was seven, and three independent
defects were hiding in it with silence as the only symptom."

**The follow-up is the difference from a quickstart**, and the answer is the
goal: a tutorial optimises for learning and may take a longer route if the
detour teaches; a quickstart optimises for working and teaches as little as it
can. Merging them produces a page too long to be one and too thin to be the
other.

**The tradeoff to volunteer.** Keeping the blind run short costs you
refactoring inside the tutorial: the good version builds a working thing in
step 1 and then rewrites part of it in step 2, which is more words and feels
less elegant than building the final structure once. Some readers notice and
object. It is still right, because attributable failure is worth more than
elegance in a document whose readers are guaranteed to make mistakes.

**One sharper point.** Silence is not success. A tutorial whose final command
produces no output cannot tell the reader anything, and it will hide real
defects indefinitely: mine exited zero with three bugs in it. Every step that
runs something should show what the reader will see, and the final step most of
all.

## How to prove it

**The artifact.** A tutorial with output shown at every step, a cold-start
test, and a measured blind-run length.

**Three things to do, in order:**

1. Run the blind-run measurement over a tutorial you own. Anything above 2 is
   worth reordering.
2. Follow your own tutorial in a fresh environment and note the first point at
   which you could tell it was working. That number is the one readers feel.
3. Check that your final step produces output. Silent final steps are common
   and they make the whole tutorial unfalsifiable.

**What makes it credible rather than decorative.** `docpack`'s
`docs/tutorials/getting-started.md` is the demonstration, recorded on the
[demonstrated](../demonstrated.md) page: five steps, nine code blocks, one
route, no choice offered before first success, with `scripts/coldstart.sh`
running the whole thing in a fresh virtual environment and asserting the exact
output it promises. What is missing is a reader: the blind-run count is zero. The number is the claim worth
making, because it is checkable by anyone who disagrees.

## Related

- [Diátaxis](diataxis.md), which separates this from the other three types
- [Quickstarts that survive contact](quickstarts.md), the page this is often confused with
- [Sample walkthroughs](sample-walkthroughs.md), the inverse: explaining code that exists
- [Cold-start testing](coldstart-testing.md), what verifies the steps
