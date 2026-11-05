---
title: A systems mindset
summary: Fixing the condition that produced a defect rather than the defect, and knowing when not to.
diataxis: explanation
audience: developer
concept: systems-mindset
tags: [craft, core]
---

# A systems mindset

`core` · difficulty 2 · 2h

> A systems mindset: you fix the class of problem, not just the instance

> Source: nvidia posting, verbatim

**Leads to:** [Giving architecture owners implementation feedback](implementation-feedback.md), [Prioritizing documentation work](docs-prioritization.md)

## What it is

Treating a defect as evidence about the process that produced it. You fix the
broken link, and then you ask what allowed a broken link to reach a reader, and
you change that.

The second half is what makes it a mindset rather than a slogan: it includes
knowing when the answer is "nothing, this was genuinely a one-off", because
building a system for every instance is its own failure.

## Why the job asks for it

NVIDIA names it as a required trait and spells it out, which is unusual for a
soft requirement. The surrounding language explains why: "We build systems where
the right way is easier than the wrong way", and "turning documentation,
standards, and tribal knowledge into tooling, templates, and self-service paths,
so fewer people have to ask how do I".

Read those together and the role becomes clear. This is not a documentation job
with some automation attached. **It is a job whose output is mechanisms**, and
pages are one kind of mechanism among several.

On a Tuesday it is a fork in the road, several times a day. Someone reports that
a code sample in the quickstart no longer runs. The instance fix is five
minutes. The class fix is
[a test that executes every sample](code-sample-validation.md), which is an
afternoon and which means that specific report never happens again. Doing the
instance fix feels responsive and leaves you doing it again next quarter.

The reason it is tagged `core` rather than filed as attitude: it is the thing
that determines whether your backlog shrinks. A documentation team that only
does instance fixes has a backlog that grows with the product. A team that
converts recurring instances into gates has a backlog that grows with the
*novelty* of the product, which is much slower.

## The golden path

Take one instance, find its class, and build the smallest gate that closes it.
About thirty minutes.

**Step 1: the instance**

```bash
mkdir -p systems-drill && cd systems-drill
mkdir -p docs
cat > docs/install.md <<'EOF'
# Install

Run `pip install widget`.
EOF
cat > docs/configure.md <<'EOF'
# Configure

First, [install the widget](install.md). Then see the
[tuning guide](tuning.md) for performance options.
EOF
ls docs/
```

`tuning.md` does not exist. That is the instance. The instance fix is obvious:
create the page or remove the link.

**Step 2: ask the question that turns it into a class**

```bash
cat > analysis.md <<'EOF'
INSTANCE   A link in configure.md points to a page that does not exist.

Q: What allowed this to reach a reader?
A: Nothing checks whether internal links resolve.

CLASS      Any link to a nonexistent page, in any page, ever.

Q: What is the smallest thing that makes the class impossible?
A: A check that resolves every internal link, run before merge.

Q: What does the gate NOT cover?  (Ask this, always.)
A: External links. Anchors within a page. Links in generated output.
   Images. Redirects that resolve but go somewhere wrong.
EOF
cat analysis.md
```

That last question is the one people skip, and it is what separates a gate from
a false sense of security. A link checker that silently ignores anchors will
convince a team that links are handled.

**Step 3: build the gate**

```bash
cat > check_links.py <<'PY'
"""Fail if any internal Markdown link points at a file that does not exist."""
import re
import sys
from pathlib import Path

LINK = re.compile(r"\[[^\]]*\]\((?!https?://|mailto:)([^)#]+)(?:#[^)]*)?\)")

def main(root: Path) -> int:
    broken = []
    for page in sorted(root.rglob("*.md")):
        for target in LINK.findall(page.read_text(encoding="utf-8")):
            if not (page.parent / target).resolve().exists():
                broken.append(f"{page}: {target}")
    for item in broken:
        print(f"broken link  {item}", file=sys.stderr)
    print(f"{'FAIL' if broken else 'ok'}: {len(broken)} broken internal link(s)")
    return 1 if broken else 0

if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1] if len(sys.argv) > 1 else "docs")))
PY
python3 check_links.py docs
```

It fails, naming the file and the target.

**Step 4: confirm the gate works in both directions**

A gate you have only seen fail is half-tested. The dangerous failure is a gate
that passes when it should not.

```bash
printf '# Tuning\n\nSet the batch size.\n' > docs/tuning.md
python3 check_links.py docs

# And now the case the gate does NOT cover, which you wrote down in step 2.
cat >> docs/configure.md <<'EOF'

See [the batch size section](tuning.md#batch-size).
EOF
python3 check_links.py docs
echo "^ passed, but #batch-size does not exist. Known gap, not a surprise."
```

**What you built.** A gate that makes one class of defect impossible, plus a
written record of what it does not cover. The record is the deliverable that
distinguishes this from enthusiasm: you now know that anchors are unchecked, so
when an anchor breaks nobody concludes the link checker is broken, and the next
increment is obvious.

## Reference

### The four questions, in order

| Question | Purpose |
|---|---|
| What allowed this to reach a reader? | Finds the missing gate rather than the bad actor |
| What is the smallest thing that closes the class? | Prevents building a platform to fix a typo |
| What does the gate not cover? | Stops false confidence, names the next increment |
| Is this class worth a gate at all? | The brake. Some instances are genuinely singular |

### Instance and class, worked examples

| Instance | Class | The gate |
|---|---|---|
| A broken link | Any unresolvable internal link | [Link checking](link-checking.md) |
| A sample that no longer runs | Any sample drifting from the API | [Code-sample validation](code-sample-validation.md) |
| A quickstart that fails on a clean machine | Any undeclared dependency | [Cold-start testing](coldstart-testing.md) |
| A page using "repo" where the glossary says "repository" | Terminology drift | [Prose linting](prose-linting.md) |
| A page with no owner and no review date | Unmaintainable content | [Content model](content-model.md) with a required `updated` |
| A page nobody can find | Structure invisible to search | [Metadata](metadata.md) and [findability](findability.md) |
| The same question in support three times | Missing self-service path | [Repeat-question analysis](repeat-questions.md) |
| A release shipped undocumented | Docs outside the definition of done | [Release readiness](release-readiness.md) |

That table is most of what both postings are asking for, which is why this page
is short and the others are long.

### When the instance fix is correct

Worth stating plainly, because this mindset has a failure mode:

- **The class has one member.** A typo in a page title is a typo.
- **The gate would cost more than the defects.** A linter for a three-page site.
- **You do not understand the class yet.** Two instances is not a pattern;
  building a gate on a guess produces a gate people route around.
- **The gate would be unreliable.** A check that fails spuriously trains people
  to ignore red builds, which is worse than no check. This is the big one.
- **The real fix belongs to someone else.** If the class is "the API changes
  without warning", a documentation gate is a workaround and the conversation
  belongs with engineering.

### The strongest version of the idea

A gate catches a defect after someone makes it. The better move, where it is
available, is to make the defect **unrepresentable**: a
[closed vocabulary](taxonomy.md) means an invalid page type cannot be written
down, not merely that it is caught. A [generator](templates-scaffolding.md)
means a conforming page is the path of least resistance.

NVIDIA's phrase for this is "systems where the right way is easier than the
wrong way", and it is a stronger claim than validation. Validation makes the
right way mandatory, which is a different and more annoying thing.

## How to talk about it

**What a competent answer sounds like.** Tell a two-level story with a number.
"A reader reported a broken sample. I fixed it, then wrote a test that extracts
and executes every Python block in the docs. It found four more that day.
Then I added a skip marker with an assertion that skips stay under a quarter of
the samples, because an escape hatch with no limit becomes the default."

That third sentence is the signal. It shows you expect your own mechanism to be
worked around and designed for it.

**The follow-up is "when have you over-engineered this",** and an interviewer
who asks it is testing for judgement rather than enthusiasm. Have a real answer.
The most common honest one in this field is a linter rule too aggressive for its
corpus, producing dozens of warnings everyone learned to ignore, which left the
corpus worse than before because now there was a check that meant nothing.

**The tradeoff to volunteer.** Every gate is permanent friction on everyone who
contributes afterwards, and the people who pay it are not the people who
benefited from it. A check that saves you an hour a quarter and costs eleven
contributors thirty seconds a day is a net loss that will never show up in any
metric you look at. Gates need the same scrutiny as features, including the
question of what to remove, which is why
[retiring content](content-retirement.md) and retiring checks are the same
discipline.

**One sharper point.** The highest-leverage version of this mindset is applied to
**social** problems, not technical ones. "An engineer rewrote a page badly" has
a class, and the class fix is usually a template or a review checklist rather
than a conversation. Most documentation people apply systems thinking to
pipelines and instance thinking to humans. Saying that out loud is unusual and
it is the thing NVIDIA's "collaborative style" bullet is circling.

## How to prove it

**The artifact.** A commit pair: the instance fix, and the gate that closes its
class. In the same history, visible as two commits.

**Three things to do, in order:**

1. **Run the golden path, then find a real instance.** Any project. Fix it,
   then write the smallest gate. Twenty lines is fine; the point is not the
   sophistication.
2. **Write down what the gate does not cover, in the gate.** A comment or a
   README line. This is the cheapest credibility available on this page,
   because almost nobody does it and it is immediately recognisable as the work
   of someone who has been burned.
3. **Find one gate to remove.** A check that has never caught anything, or
   whose warnings everyone ignores. Removing it is the same skill pointed the
   other way, and it is the harder half to demonstrate. If you cannot find a
   check that has never caught anything, you have either a young pipeline or
   no record of what your gates catch, and the second is the more common
   answer.

**What makes it credible rather than decorative.** "I think in systems" is a claim anyone can make. A
repository where you can point at the red build, the fix, and the gate that
followed is not. The strongest version includes a gate you later deleted.

### How this would be demonstrated elsewhere

A repository can hold the output of this thinking and not the thinking. What
would demonstrate it is a record of decisions and their consequences, which is
a thing you accumulate rather than build.

**Where the skill is exercised.** In the choice to fix a class rather than an
instance. In noticing that two unrelated-looking failures share a cause. In
declining to add a check because the check would be ignored.

**What a learner would do.** Take the last five defects you fixed, in anything,
and for each write down the instance you fixed and the class it belonged to.
Then ask which of the five you closed at the class level. Most people find one.
That ratio is the measurement, and it is available today without any tooling.

Then do the inverse on something you own: find a check that fires often and ask
what it is really telling you. A link checker that reports twenty dead links a
month is not a link problem, it is a publishing problem, and the systems answer
is to find out what keeps breaking them.

**What competence looks like.**

| Evidence | Why it carries weight |
|---|---|
| A fix whose commit message names the class | The class was seen, not just the bug |
| A check added after a defect, in the same change | The instinct is present, not retrofitted |
| A check *removed* because it was noise | Harder than adding, and rarer |
| Two problems diagnosed as one cause | The actual skill |
| A deliberate decision not to automate | Judgment rather than reflex |

**What this guide can point at instead.** The closest thing to evidence here is
the pattern in its own history. A prerequisite label was standardised and
asserted in a test rather than corrected on one page. A word-count gate was
re-derived after a generator was added. A fence parser was written after three
naive versions returned plausible wrong numbers. A `Related` section was
promoted from convention to contract once one page was found without it. Each
of those is an instance closed as a class, and the record of them is the
nearest a repository gets.

**Why it is still not a demonstration.** Those decisions are visible in
hindsight and the reasoning is not. A reader cannot tell from the commit whether
the class was seen at the time or found later during an audit, and in at least
two of those four cases it was found later. Saying so is the only honest version
of this page.

## Related

- [Giving architecture owners implementation feedback](implementation-feedback.md), this applied upward
- [Templates and scaffolding](templates-scaffolding.md), making the right way easier
- [Prioritizing documentation work](docs-prioritization.md), choosing which class to close
- [Documentation CI](documentation-ci.md), where the gates live
