---
title: Prose linting with Vale
summary: Enforcing the parts of a style guide a machine can check, and leaving the rest alone.
diataxis: how-to
audience: developer
concept: prose-linting
tags: [qa, core]
---

# Prose linting with Vale

`core` · difficulty 2 · 3h

!!! quote "Asked for by name"
    NVIDIA: "Content quality automation you've built, such as Vale or custom linters, doc test harnesses, or freshness monitoring"

**Prerequisites:** [Style guides](style-guide.md)

## What it is

A linter for prose. Vale reads Markdown, reStructuredText and a dozen other
formats, applies rules you write in YAML, and reports violations with a file,
line, column and severity, the same shape a compiler uses.

What it is really for is converting the mechanical half of a
[style guide](style-guide.md) from a document people are supposed to have read
into a check that runs. "Use *widget* rather than *Widget CLI*" stops being a
sentence in a wiki and becomes a failing build.

## Why the job asks for it

NVIDIA names Vale specifically, in the "ways to stand out" section, alongside
custom linters and doc test harnesses. That grouping tells you what they mean
by it: not that you have installed a linter, but that you have *built* content
quality automation.

The reason it matters on a large corpus is consistency at scale. One writer
with good judgment produces consistent prose. Thirty contributors across
engineering, product and support produce thirty dialects, and the terminology
drift that follows is what makes a documentation set feel untrustworthy even
when every individual page is correct. A linter is the only mechanism that
applies the same standard to a pull request from someone who has never read
your style guide.

The second reason is review bandwidth. A reviewer who spends their attention
on serial commas has none left for whether the procedure is correct. Automating
the mechanical layer is what makes human review about substance.

## The golden path

Build a two-rule house style, run it, and discover what actually controls
whether the build fails. About thirty minutes.

**Step 1: a config and two rules**

````bash
mkdir -p vale-demo/docs vale-demo/styles/House && cd vale-demo

cat > .vale.ini <<'EOF'
StylesPath = styles
MinAlertLevel = suggestion

[*.md]
BasedOnStyles = House
EOF

cat > styles/House/Hedging.yml <<'EOF'
extends: existence
message: "Avoid hedging: '%s'"
level: warning
ignorecase: true
tokens:
  - should be able to
  - probably
  - fairly simple
EOF

cat > styles/House/Terms.yml <<'EOF'
extends: substitution
message: "Use '%s' rather than '%s'"
level: error
ignorecase: false
swap:
  Widget CLI: widget
  dataset: data set
EOF
````

Note the direction of `swap`. The **key is the form you do not want** and the
value is the replacement. Getting this backwards is the most common Vale
mistake, and it fails silently: your rule simply never fires.

**Step 2: run it**

````bash
cat > docs/index.md <<'EOF'
# Getting started

You should be able to install the Widget CLI fairly easily.
Load the dataset, then run the command.
EOF

vale docs/
````

```
 3:5   warning  Avoid hedging: 'should be able to'   House.Hedging
 3:35  error    Use 'widget' rather than 'Widget CLI'  House.Terms
 4:10  error    Use 'data set' rather than 'dataset'    House.Terms
✖ 2 errors, 1 warning and 0 suggestions in 1 file.
```

Three findings, with severities you chose per rule.

**Step 3: check that it leaves code alone**

````bash
cat > docs/code.md <<'EOF'
# Example

```bash
# you should be able to run this
widget install --dataset foo
```
EOF

grep -c "should be able to" docs/code.md
vale docs/code.md
````

```
1
✔ 0 errors, 0 warnings and 0 suggestions in 1 file.
```

A `grep` finds the phrase in the code comment; Vale does not. Vale parses
Markdown rather than scanning lines, so fenced blocks, inline code and URLs are
excluded by default. This is the single biggest reason to use it instead of the
regex script you were about to write. A naive linter that fires inside code
samples gets switched off within a week.

**Step 4: find out what actually fails the build**

The intuitive assumption is that `--minAlertLevel` decides. Test it:

```bash
printf '# T\n\nThis is probably fine.\n' > docs/index.md
for lvl in suggestion warning error; do
  vale --minAlertLevel=$lvl docs/ >/dev/null 2>&1
  echo "warnings only, gate at $lvl -> exit=$?"
done

printf '# T\n\nInstall the Widget CLI.\n' > docs/index.md
vale --minAlertLevel=error docs/ >/dev/null 2>&1
echo "has an error, gate at error -> exit=$?"
```

```
warnings only, gate at suggestion -> exit=0
warnings only, gate at warning   -> exit=0
warnings only, gate at error     -> exit=0
has an error, gate at error      -> exit=1
```

**`minAlertLevel` controls what is displayed, not what fails.** Vale exits
non-zero if and only if at least one finding is at `error` level. So the
decision about what blocks a merge is made in each rule's `level:` field, in
the rule file, in version control, reviewable. Not in a CI flag.

That is better than it first sounds. It means "does this block the build" is a
property of the rule, decided once, visible to everyone, rather than an
argument someone passes in a workflow.

**Step 5: set the levels deliberately**

```bash
sed -i 's/^level: warning/level: warning   # advisory: hedging is a judgment call/' styles/House/Hedging.yml
sed -i 's/^level: error/level: error     # blocking: terminology is not negotiable/' styles/House/Terms.yml
echo "terminology blocks, hedging advises"
```

**What you built.** A house style that is executable, where terminology errors
stop a merge and stylistic suggestions do not, and where the line between the
two is a reviewable field in a rule file.

## Reference

### The rule types worth knowing

| `extends` | Use it for | Example |
|---|---|---|
| `existence` | Banned words or phrases | Hedging, "simply", "just" |
| `substitution` | One term replaced by another | Product name casing, "data set" |
| `occurrence` | Too many or too few per scope | At most one exclamation mark per file |
| `repetition` | The same word twice in a row | "the the" |
| `consistency` | Either spelling, but not both | "acknowledgement" vs "acknowledgment" |
| `conditional` | B must appear if A does | An acronym must be expanded once |
| `capitalization` | Heading case | Sentence case in `##` headings |
| `readability` | Grade-level scores | Flesch-Kincaid thresholds |
| `spelling` | Dictionary plus your own vocabulary | Product vocabulary |

`consistency` and `conditional` are the two that are hard to replicate with a
regex script, and they are the ones worth reaching for when someone asks what
Vale gives you that `grep` does not.

### What to make an error and what to leave as a warning

| Error, blocks the merge | Warning, advisory only |
|---|---|
| Product and feature names | Hedging and filler |
| Expanding an acronym on first use | Sentence length |
| Banned legal or security phrasing | Passive voice |
| Deprecated terminology | Readability scores |
| Spelling of API identifiers | Heading capitalization, early on |

The test is whether a reasonable contributor could disagree. If they could,
it is a warning, because a build that fails on a defensible stylistic choice
teaches people that the pipeline is an obstacle. Terminology is not a matter
of taste, so it blocks.

### Severity semantics, exactly

| Level | Displayed by default | Fails the build |
|---|---|---|
| `suggestion` | With `MinAlertLevel = suggestion` | No |
| `warning` | With `warning` or lower | No |
| `error` | Always | Yes |

### Where the rules live

```
.vale.ini             # config: StylesPath, which styles apply to which files
styles/
  House/              # your rules, in version control, reviewed
    Hedging.yml
    Terms.yml
  write-good/         # third-party packages, installed by `vale sync`
```

Keep your own rules in a directory named after your organization rather than
scattering them into a vendored style, so `vale sync` cannot overwrite them.

## How to talk about it

**Lead with the division of labour.** "A prose linter handles the mechanical
half of the style guide so human review can be about whether the procedure is
correct. Terminology, acronym expansion and deprecated names block the build.
Passive voice and sentence length are warnings."

**The follow-up is usually a challenge about whether this annoys writers**, and
the answer is yes, if you set the levels wrong. Say that explicitly. A linter
that fails builds over defensible choices gets disabled, and the mitigation is
that only non-negotiable rules are errors.

**The tradeoff to volunteer.** Every rule is a guess about intent, and some
fire on correct prose. A terminology rule banning "dataset" will flag a direct
quotation from a third-party API that is genuinely called `dataset`. You need
an escape hatch, Vale's `<!-- vale off -->` comments, and the moment you have
an escape hatch you need to watch how often it is used, because widespread
suppression means the rule is wrong rather than the prose.

**One sharper point.** `minAlertLevel` does not control whether Vale fails;
the exit code tracks errors only. That means the blocking decision lives in
each rule file under version control instead of in a CI flag, which is the
right place for it. Knowing that distinction is a reliable signal of having
operated Vale rather than installed it.

## How to prove it

**The artifact.** A `styles/` directory of rules you wrote, with levels set
deliberately, and at least one rule that caught something real.

**Three things to do, in order:**

1. Run the golden path, especially step 4. The exit-code behaviour is not what
   most people assume.
2. Write one `substitution` rule for a term your own project gets wrong, and
   run it over your existing docs. The first real finding is your evidence.
3. Count the suppression comments in any corpus you already lint. A high count
   is a finding about the rules, not about the writers. More than roughly one
   suppression per ten pages means the rule is wrong rather than the prose,
   and the fix belongs in the rule.

**What makes it credible rather than decorative.** `docpack` runs Vale with
terminology errors blocking the build and style warnings advisory, and one of
its four hand-written rules caught the author's own prose. The rule that caught
you is the one to talk about: it proves the gate works on the person who wrote
it.

## Related

- [Writing custom linters](custom-linters.md), for the rules Vale cannot express
- [Detecting terminology drift](terminology-drift.md), the corpus-wide version of the terminology rule
- [Style guides](style-guide.md), the document this automates part of
- [Documentation CI](documentation-ci.md), where the gate runs
