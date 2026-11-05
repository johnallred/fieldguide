---
title: Content models
summary: "A schema for your content, judged by the specific lies it makes impossible."
diataxis: explanation
audience: developer
concept: content-model
tags: [ia, core]
---

# Content models

`core` · difficulty 2 · 4h

!!! quote "Asked for by name"
    NVIDIA: "Information architecture skills: content modeling, taxonomy, and metadata for both navigation and machine retrieval"

**Prerequisites:** [Information architecture](information-architecture.md)

**Leads to:** [Taxonomy and controlled vocabularies](taxonomy.md), [Metadata for navigation and retrieval](metadata.md), [Content lifecycle and governance](content-lifecycle.md), [Single-sourcing and content reuse](single-sourcing.md)

## What it is

A schema for your content: what kinds of page exist, what fields each kind
carries, which of those fields are required, and which draw from a
[closed vocabulary](taxonomy.md). In a docs-as-code project it usually lives in
front matter plus a validator.

The way to judge one is not by how elegant the schema is. It is by asking **what
specific lies it makes impossible**, and then checking that each of those lies
actually fails a build. The golden path does exactly that, twelve times.

## Why the job asks for it

NVIDIA lists content modeling first in its information architecture
requirement, ahead of taxonomy and metadata, which is the right order: the
model is the thing the other two attach to.

The reason it is engineering rather than documentation theory is that a model
without a validator is a convention, and conventions decay silently. Every
corpus has a style guide saying how pages should be structured. Very few can
tell you which pages currently violate it.

It is also the foundation of everything in the
[AI-ready](agent-ready-content.md) category. Filtering retrieval by page type,
chunking by section, assembling an `llms.txt` by audience: all of those read
fields. If the fields are optional, inconsistent or unparseable, none of it
works, and the failure looks like a bad retriever rather than a bad schema.

## The golden path

Take a real content model and attack it. Twelve defects, one at a time, and
check what survives. About forty minutes.

**Step 1: the model under test**

This guide's own registry is a content model with a validator. Its closed
vocabularies and its page contract:

```python
TIERS      = ("core", "supporting", "context")
PROVENANCE = ("quoted", "derived", "adjacent")
STATUSES   = ("planned", "drafted", "complete")

REQUIRED_SECTIONS = (
    "What it is", "Why the job asks for it", "The golden path",
    "Reference", "How to talk about it", "How to prove it",
)
MIN_COMPLETE_WORDS = 450
```

Plus structural rules: every concept needs at least one `demanded_by` entry,
prerequisites must resolve to real concepts, and the prerequisite graph must be
acyclic.

**Step 2: attack the vocabularies and the graph**

Mutate a copy of the registry, once per defect, and record where each is
caught:

```python
def attempt(label, mutate):
    data = copy.deepcopy(base)
    mutate(data)
    Path("mutated.yaml").write_text(yaml.safe_dump(data, sort_keys=False))
    try:
        registry = load_registry(Path("mutated.yaml"))
    except RegistryError as e:
        print(f"  CAUGHT at parse  {label}")
        return
    findings = validate_against_tree(registry, Path("docs"))
    print(f"  {'CAUGHT at check' if not findings.ok else 'MISSED'}  {label}")
```

```
  CAUGHT at parse  tier outside the vocabulary
  CAUGHT at parse  status outside the vocabulary
  CAUGHT at parse  provenance outside the vocabulary
  CAUGHT at parse  prerequisite that does not exist
  CAUGHT at parse  prerequisite cycle
  CAUGHT at parse  duplicate concept id
  CAUGHT at parse  concept with no demanded_by
```

Seven for seven, all at parse time, with messages that name the offender:

```
concepts[5] (metadata): tier must be one of ['core', 'supporting', 'context']
prerequisite cycle: content-model -> metadata -> content-model
duplicate concept id 'metadata'
```

**Step 3: attack the page contract**

The remaining defects are about the relationship between the registry and the
files, so they are caught later, by a validator that reads both:

```
  CAUGHT check  complete concept, page deleted
  CAUGHT check  complete page truncated below 450 words
  CAUGHT check  complete page missing a required section
  CAUGHT check  an orphan page with no concept
```

Four for four. Note the last one: a page nobody registered is as much a model
violation as a registry entry with no page. A model that only validates in one
direction lets the corpus grow pages that no index knows about.

**Step 4: find the defect the model did not cover**

Twelve caught is a good result, and it is not the interesting part. The
interesting part is what was missing from the list.

Parse the front matter of every page with a real YAML parser:

```python
for p in sorted(Path("docs").rglob("*.md")):
    m = re.match(r"^---\n(.*?)\n---\n", p.read_text(), re.S)
    if not m:
        continue
    try:
        yaml.safe_load(m.group(1))
    except yaml.YAMLError as e:
        bad.append(p)
```

```
front matter parses: 75 pages
front matter INVALID: 46 pages
```

Forty-six of 121 pages had front matter that **no YAML parser could read**. The
placeholder generator assembled it with f-strings, so the generated summary
read `summary: Outline only: Measuring AI answer quality is ...` and the
unquoted colon started a mapping.

Every check above passed on that corpus. The build passed too, because MkDocs'
own metadata parser is more forgiving than YAML. The visible consequence was
silent:

```
meta description: A validated curriculum for documentation engineering, ...
```

The page's own `summary` was unreadable, so the description fell back to the
site default on all 46 pages.

**Step 5: fix the cause, not the pages**

```python
def _front_matter(title, summary, audience="new-user"):
    data = {"title": title, "summary": summary, "diataxis": "reference",
            "audience": audience, "generated": True}
    body = yaml.safe_dump(data, sort_keys=False, default_flow_style=False)
    return f"---\n{body}---\n\n"
```

```
front matter parses: 118   invalid: 3
```

The remaining three were hand-written pages with the same mistake, including
this one's own summary. Quote them, and add the check so the class cannot
return:

```
ok: every page's front matter parses as YAML
```

**What you learned.** A content model is judged by the lies it prevents, and
the useful question about any model is which lie is still possible. This one
prevented twelve and was blind to the thirteenth, which was the one that
mattered most for machine readability.

## Reference

### The parts of a content model

| Part | Example here | Enforced by |
|---|---|---|
| Page types | `diataxis: tutorial / how-to / reference / explanation` | Closed vocabulary |
| Required fields | `title`, `summary`, `diataxis`, `audience` | Parse-time check |
| Closed vocabularies | `tier`, `status`, `provenance` | Membership test |
| Relationships | `prerequisites`, acyclic | Graph check |
| Structural contract | Six required sections, 450 words | File check |
| Both-directions coverage | No page without a concept, no concept without a page | File check |
| Serialisation validity | Front matter parses as YAML | The check added in step 5 |

The last row is the one most models omit, and it is the cheapest of all of
them.

### Where each class of defect is caught

| Caught at | Defects |
|---|---|
| Parse | Vocabulary violations, dangling references, cycles, duplicates, missing required fields |
| Validation against files | Status disagreeing with reality, contract violations, orphan pages |
| Build | Nothing structural; the build is not your content model |
| Never, without the step 5 check | Front matter that is not valid YAML |

### How to write the model down

| Option | Good for | Cost |
|---|---|---|
| A data file plus a validator | A corpus with structure worth enforcing | You write the validator |
| JSON Schema on front matter | Standard tooling, editor integration | Awkward for cross-page rules |
| A linter with custom rules | Teams already running Vale | Rules are per-field, not relational |
| A documented convention | Nothing; it decays | Zero to write, high to maintain |

Cross-page rules are the deciding factor. A schema validates one page at a
time, so prerequisite resolution, cycle detection and orphan detection need
code. That is why this guide's model is a Python module rather than a JSON
Schema.

### Designing one for a real corpus

| Question | Why it matters |
|---|---|
| What page types exist, really? | Count what you have before inventing categories |
| Which fields would change a reader's path? | Those belong in navigation |
| Which fields would filter a retrieval query? | Those belong in [metadata](metadata.md) |
| What is required versus optional? | An optional field is absent half the time, so nothing can depend on it |
| What vocabulary is closed? | Open vocabularies drift; see [taxonomy](taxonomy.md) |
| What relationships exist between pages? | These need code, not a schema |

The fourth row is the one with teeth. A field that is optional is a field your
pipeline cannot rely on, so "optional metadata" is usually a decision not to
use it for anything.

## How to talk about it

**Lead with lies, not schemas.** "I judge a content model by the specific lies
it makes impossible. On this guide's own registry I could not mark a concept
complete without a page, could not add a prerequisite that does not exist,
could not create a cycle, and could not ship a complete page under 450 words or
missing a required section. Twelve defect classes, each one a failing build."

**The follow-up is about contributor friction**, and the honest answer is that
every required field is a tax and the right number is small. Four required
fields that everything depends on beats twelve that half the corpus omits,
because an optional field cannot be built on.

**The tradeoff to volunteer.** Cross-page rules need code, which means your
content model becomes software you maintain, with its own tests and its own
bugs. My own validator had a counting bug that double-reported demonstrations
and a generator that emitted invalid YAML for 38% of the corpus. A model with a
validator is better than a convention, and it is not free.

**One sharper point.** Front matter is the
machine-readable half of a page, and almost nobody checks that it parses.
MkDocs' metadata parser is more forgiving than YAML, so a page with an
unquoted colon builds cleanly and is invisible to every tool that uses a real
parser. I shipped 46 such pages. That check is four lines and it is the
cheapest AI-readiness work available, because a corpus that cannot be parsed
cannot be filtered, chunked or retrieved.

## How to prove it

**The artifact.** A content model with a validator, plus the list of defects it
catches, each with a test.

**Three things to do, in order:**

1. Run step 4 against a corpus you own. Parse every page's front matter with a
   real YAML parser and count the failures. This finds something surprisingly
   often.
2. Write down the lies your current model prevents. If the list is short or you
   cannot name one, you have a convention rather than a model.
3. Pick the most consequential lie that is still possible and make it fail. One
   check, with a test that proves it fires.

**What makes it credible rather than decorative.** `docpack` validates five
required front-matter fields, two of them closed vocabularies, rejected by
`docpack docs --check`. This guide's registry adds the relational rules a
per-page schema cannot express. The part worth discussing in an interview is
step 4: the model that caught twelve things and missed the thirteenth, and how
the thirteenth was found.

## Related

- [Taxonomy and controlled vocabularies](taxonomy.md), where the closed vocabularies come from
- [Metadata for navigation and retrieval](metadata.md), which fields exist and who reads them
- [Information architecture](information-architecture.md), the discipline this sits inside
- [Agent-ready content](agent-ready-content.md), which depends entirely on this working
