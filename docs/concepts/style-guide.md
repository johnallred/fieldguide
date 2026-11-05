---
title: Style guides and terminology management
summary: "Splitting a style guide into the half a machine enforces and the half it cannot, and proving each rule fires."
diataxis: explanation
audience: developer
concept: style-guide
tags: [ia, supporting]
---

# Style guides and terminology management

`supporting` · difficulty 1 · 2h

!!! quote "Asked for by name"
    NVIDIA: "You're a writer who builds: as comfortable in Git, CI, or Python as in a style guide, and fluent with LLMs in daily work"

**Prerequisites:** [Taxonomy and controlled vocabularies](taxonomy.md)

**Leads to:** [Prose linting with Vale](prose-linting.md), [Security guidance as encoded standard](security-documentation.md)

## What it is

The agreed rules for how your documentation is written: terminology, voice,
person, capitalisation, how to format a command, when to use a note versus a
warning. In practice it is two documents wearing one name, and separating them
is most of the value.

One half is **mechanical**: terminology, deprecated words, heading case,
acronym expansion. A machine enforces it, and a machine should, because humans
are bad at it and it uses up the review attention that
[judgment](docs-review.md) needs. The other half is **editorial**: what to
explain, how much, in what order, when an example beats a paragraph. No linter
will ever check it.

## Why the job asks for it

NVIDIA's phrasing is "as comfortable in Git, CI, or Python as in a style
guide", which is a claim about range rather than about style guides
specifically. The expectation is that you can both write the rules and
implement them.

The thing that distinguishes experience here is knowing which rules are worth
encoding and being willing to say that most style guides are too long to be
used. A forty-page guide is a document people are told to read and do not. A
twelve-rule linter plus two pages of editorial guidance is a thing that
actually shapes a corpus.

## The golden path

Encode three classes of rule, then find out that one of them never fires.
About twenty-five minutes.

**Step 1: one rule per class of guidance**

````bash
mkdir -p style-demo/docs style-demo/styles/House && cd style-demo

cat > .vale.ini <<'EOF'
StylesPath = styles
MinAlertLevel = suggestion
[*.md]
BasedOnStyles = House
EOF

cat > styles/House/Terms.yml <<'EOF'
extends: substitution
message: "Use '%s' rather than '%s'"
level: error
swap:
  Widget CLI: widget
EOF

cat > styles/House/Passive.yml <<'EOF'
extends: existence
message: "Possible passive voice: '%s'"
level: warning
tokens:
  - '\b(is|are|was|were|be|been|being)\s+\w+ed\b'
EOF

cat > styles/House/SecondPerson.yml <<'EOF'
extends: existence
message: "Address the reader as 'you', not '%s'"
level: warning
tokens:
  - 'the user should'
  - 'one should'
EOF
````

Three classes: terminology as an error, voice as a warning, person as a
warning.

**Step 2: a page that violates all three**

````bash
cat > docs/a.md <<'EOF'
# Install

The Widget CLI is installed by the package manager.
The user should then run the setup command.
You can verify the result.
EOF

vale docs/a.md
````

```
 3:5   error    Use 'widget' rather than 'Widget CLI'   House.Terms
 3:16  warning  Possible passive voice: 'is installed'  House.Passive
✖ 1 error, 1 warning and 0 suggestions in 1 file.
```

Two findings. The page violates three rules.

**Step 3: work out which rule is broken**

`SecondPerson` did not fire, and line 4 is "The user should then run the setup
command", which is exactly what it was written to catch.

The rule's token is `the user should`, lowercase. Vale's `existence` is
**case-sensitive by default**, and the phrase occurs at the start of a
sentence, so the text is "The user should". The rule matched nothing.

```yaml
ignorecase: true
```

```
 4:1   warning  Address the reader as 'you', not 'The user should'  House.SecondPerson
✖ 1 error, 2 warnings and 0 suggestions in 1 file.
```

Now consider how you would have found that without looking. A rule that
matches nothing produces no output. Vale does not warn that a rule is never
satisfied, the build stays green, and the style guide claims a rule that is not
being enforced. **A silently dead rule is worse than no rule**, because it buys
false confidence.

The discipline that prevents it: every new rule ships with a fixture that
should fail, and you confirm it fails before you trust it. The same practice
the [custom linters](custom-linters.md) page arrives at, for the same reason.

Sentence-initial case is the specific trap to remember, because the phrases
style guides most want to ban, "The user should", "Simply", "Note that", "In
order to", overwhelmingly appear at the start of a sentence.

**What you built.** Three enforced rules, one near miss, and a rule about rules.

## Reference

### What goes in which half

| Mechanical, enforce it | Editorial, write it down |
|---|---|
| Canonical and deprecated terms | What a page should explain and what to link |
| Acronym expansion on first use | How much background a reader needs |
| Heading case | When an example beats a paragraph |
| Banned filler: "simply", "just", "obviously" | How to order a procedure |
| Product and feature name casing | When a warning is warranted |
| Code formatting conventions | Tone for an error message |
| Passive voice, as a warning | Whether a page should exist |

The split is also a split in medium. The mechanical half belongs in
`styles/`, in version control, reviewed as code. The editorial half belongs in
a short document, and short is the operative word.

### Rule levels

| Level | Use for | Why |
|---|---|---|
| Error, blocks the merge | Terminology, product names, deprecated terms | Not a matter of taste |
| Warning | Passive voice, person, sentence length | A reasonable contributor could disagree |
| Suggestion | Readability scores | Informational |

The test is whether a reasonable contributor could disagree. If they could, it
is a warning, because a build that fails on a defensible choice teaches people
that the pipeline is an obstacle. And recall from
[prose linting](prose-linting.md) that Vale's exit code tracks errors only, so
this decision lives in each rule file rather than in a CI flag.

### Traps in rule authoring

| Trap | Effect | Fix |
|---|---|---|
| Case sensitivity | Misses sentence-initial occurrences, which is most of them | `ignorecase: true` |
| Swap direction | `substitution` keys are the *bad* form; reversing it silently never fires | Test it |
| Over-broad tokens | Fires inside correct prose; people disable the rule | Narrow, then re-measure |
| No fixture | A dead rule is indistinguishable from a clean corpus | Ship a failing example |
| Rules about code | Vale excludes code by design | A [custom linter](custom-linters.md) |

Three of those five fail *silently*. That is the character of style automation:
the failure mode is not noise, it is quiet absence.

### Terminology management

| Artifact | Job |
|---|---|
| A glossary as data | The canonical term and its deprecated forms |
| A Vale `substitution` rule | Stops new drift, per pull request |
| A [drift measurement](terminology-drift.md) | Tells you how far the corpus already moved |
| A decision record per term | So the choice is not relitigated |

The glossary is the artifact and the rules are generated from it, not the other
way round. A corpus where the Vale rules *are* the glossary cannot answer "what
is the canonical term for X" without someone reading YAML.

### How long a style guide should be

| Length | Outcome |
|---|---|
| A page of editorial guidance plus linted rules | Used |
| Ten pages | Skimmed once at onboarding |
| Forty pages | Cited in arguments, never read |

If a rule can be enforced, enforce it and delete the prose about it. What
remains in writing should be only the part that needs human judgment, and that
is genuinely short.

## How to talk about it

**Lead with the split.** "A style guide is two documents. The mechanical half,
terminology, acronyms, heading case, belongs in a linter, because humans
enforce it badly and it consumes the review attention that judgment needs. The
editorial half, what to explain and in what order, can only be written down.
Most style guides fail because they mix the two and get long enough that nobody
reads either."

**The follow-up is how you know the rules work**, and the answer is fixtures. I
wrote three rules and one of them silently matched nothing, because Vale's
`existence` is case-sensitive by default and the banned phrase appears at the
start of a sentence. Nothing reported it. So every rule ships with an example
that must fail.

**The tradeoff to volunteer.** Encoding a rule makes it rigid. A terminology
rule banning "dataset" will flag a direct quotation from a third-party API
genuinely called `dataset`, so you need a suppression mechanism, and then you
have to watch how often it is used, because widespread suppression means the
rule is wrong rather than the prose.

**One sharper point.** The dangerous failure in style automation is silence,
not noise. Case sensitivity, a reversed substitution direction and an
over-narrow token all produce a rule that fires on nothing, and a corpus with
no findings looks identical to a corpus with no enforcement. A rule you have
not seen fail is a rule you should not count.

## How to prove it

**The artifact.** A `styles/` directory of rules you wrote, each with a
fixture, and a short editorial document that contains only what the rules
cannot.

**Three things to do, in order:**

1. Run the golden path. Step 3 is the point, and the trap generalises past
   Vale.
2. Take your current style guide and sort every rule into mechanical or
   editorial. The mechanical pile is your backlog; the editorial pile is your
   real style guide.
3. For every rule you already have, write a line that should fail and check it
   does. Expect at least one surprise.

**What makes it credible rather than decorative.** `docpack` carries four
hand-written Vale rules with terminology as errors and style as warnings, and
one of them caught the author's own hedge word in the README. That is the
story to tell: not that the rules exist, but that one fired on the person who
wrote it, which is the only proof that a rule is live.

## Related

- [Prose linting with Vale](prose-linting.md), the implementation
- [Taxonomy and controlled vocabularies](taxonomy.md), where canonical terms are decided
- [Detecting terminology drift](terminology-drift.md), measuring the corpus against the glossary
- [Security guidance as encoded standard](security-documentation.md), the same move for security rules
