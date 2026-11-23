# The Field Guide

**A curriculum for documentation engineering, developer experience and
KnowledgeOps, built as an example of its own subject.**

A training manual for people already doing this work, whatever their title:
documentation engineer, developer education lead, content engineer,
KnowledgeOps, docs and learning experience, lab development engineer. The work
underneath those titles is largely the same. You design golden paths and
curriculum, run documentation CI and cold-start tests, model content and
metadata for navigation and machine retrieval, package knowledge for RAG and
agents, measure whether any of it worked, and automate the publishing, testing
and monitoring that keep it true.

Different titles, the same discipline, and no settled curriculum for it
anywhere. This is an attempt at one: **113 concepts, each with a golden path,
each naming the day-to-day work that needs it.**

---

## The part worth looking at first

A guide about information architecture that was itself a folder of
unstructured Markdown would be an argument against its own content. So the
curriculum is a validated data file and the pages describing it are generated
from that file.

| Claim the project makes | What stops it being a lie |
|---|---|
| This concept is covered | The page must exist unless status is `planned` |
| This page belongs here | Every page needs a registry entry; orphans fail |
| This concept is complete | A `complete` page under 450 words is rejected |
| Pages have a consistent shape | Seven required sections, in order, enforced |
| This learning path is teachable | No concept before a prerequisite the path also teaches |
| The prerequisite graph is followable | No cycles, no dangling references |
| The work needs this | Every concept needs a line naming that work |
| The index is current | CI regenerates the views and fails if a committed one is stale |

**Three of those caught real mistakes within minutes of being written**, which
is the honest argument for the machinery. Two learning paths taught a
prerequisite too late, and both turned out to be wrong dependencies rather than
wrong orders: link checking does not depend on documentation CI, because you
run a link checker on a tree long before you own a pipeline. The validator
reported a symptom in the paths and the bug was in the model, which is the
ordinary and useful experience of working with a schema.

A fourth found a bug in the validator itself. The unsourced-concept advisory
sat after the check that skips unwritten pages, so it only ever reported the
three concepts that had prose. It should have been reporting 42.

## Quick start

```bash
python3 -m pip install -e '.[dev,docs]'

fieldguide status                  # what is written, what is left, what is unblocked
fieldguide check                   # registry integrity and the page contract
fieldguide build                   # regenerate coverage, paths, placeholders
fieldguide build --check           # fail instead, for CI
fieldguide new diataxis            # exits 2: every concept already has a page
mkdocs build                       # the built site the next line reads
fieldguide render site             # every fenced sample reaches the built HTML as code
fieldguide audit                   # every figure the pages quote about the corpus
fieldguide release-check           # the release workflow, one named step at a time
python3 -m pytest -q                # 228 tests
mkdocs serve                       # read it; not run by the cold start, it never exits

python3 scripts/prepublication.py .   # before publishing, not in CI; see below
```

`prepublication.py` exits 0 on both repositories. It spent most of its life
exiting 1 on the placeholder `site_url` and `repo_url` in `mkdocs.yml`, which is
what the script is for: converting "remember to change the URL" into a command
that fails. Closing those findings exposed a seventh: the same placeholders sat
in `demonstrations.yaml`, which publishes both repository links on the generated
index, and that file was not in the set the check reads. The
[publishing in public](docs/concepts/publishing-in-public.md) page has the
reasoning, because scoping a check by a file's role is right and is only as
complete as your list of the files that carry it.

## Changing the curriculum

[`concepts.yaml`](concepts.yaml) is the source of truth for the concept list,
their metadata and prerequisites, and the ordered learning paths. Generated
pages such as the coverage matrix, study plan and path pages are rebuilt from
it; edit the registry rather than those generated files.

To change an existing concept, find its `id` in `concepts.yaml` and edit the
relevant fields. Keep its `id` stable because it is used in page URLs and links.
The comments at the top of the file describe the fields and allowed values.
Concept prose lives separately in `docs/concepts/<id>.md`; edit that file for
writing changes, not for registry metadata.

To add a concept, add an entry under `concepts:` with a unique kebab-case `id`,
its required metadata and a `status`. Add its page with
`fieldguide new <id>`, then write the seven sections described below. To change
a learning path, edit the ordered `concepts` list for that path under `paths:`.
Prerequisites must come before the concepts that depend on them.

After editing, run:

```bash
fieldguide check
fieldguide build
python3 -m pytest -q
```

Commit the regenerated files with your registry change. `fieldguide build --check`
verifies generated pages are current without rewriting them; CI runs that check.

## How it is organised

```
concepts.yaml            the curriculum: 113 concepts, 9 paths, the checklist
src/fieldguide/
  registry.py              the model and every validator
  generate.py              coverage, paths, study plan, placeholders
  scaffold.py              the page contract, as a generator
  cli.py                   check, build, new, status
docs/
  index.md                 three ways in
  coverage.md              GENERATED: every concept and the line behind it
  study-plan.md            GENERATED: topological sort of all 113
  paths/                   GENERATED: nine learning paths
  concepts/                113 pages, all written
  explanation/             why a registry, the page contract, provenance
drills/                  nineteen runnable scripts behind figures the pages quote
tests/                   221 tests, including tests against the real registry
                         (228 with the src/ doctests pytest also collects)
.github/workflows/       nine gates on every pull request, plus the deploy
```

## The page contract

Every concept page answers the same seven questions in the same order, and CI
rejects one that does not:

1. **What it is**, in two sentences, for someone who heard the term in a
   meeting and did not admit they were lost.
2. **How this applies to your role**, describing the work behind the concept
   and what it looks like on an ordinary Tuesday.
3. **The golden path**: the shortest real exercise producing a working result,
   from a clean environment, ending in something observable.
4. **Reference**: facts worth looking up later. Tables, not narrative.
5. **Explaining it to your team**, including the tradeoff, because reciting
   what a thing does is not the useful part.
6. **Putting it into practice**: the work product, the next tasks, and how to
   tell it is working.
7. **Related**: the lateral links the prerequisite graph does not know about,
   each with a clause saying why a reader would follow it from here.

`Related` was a convention for most of this corpus's life and is now the
seventh enforced section. It was promoted the day a page turned up without one,
which is also the day that page was found to end mid-sentence.

That is a content model applied to a learning corpus. The payoff is that the
thirtieth page costs a reader nothing to navigate, because they learned the
shape on the first.

## Provenance, and the limitation behind it

Every concept prints a line naming the work that needs it, on its own page and
on every row of the coverage matrix.

The scope comes from descriptions of this work across several kinds of teams.
Some concepts are named directly in that work; others are here because the
named work is impossible without them, and their lines say so in those terms
rather than overstating it. The list is one person's judgement, made visible so
a reader can disagree with it. See [Provenance](docs/explanation/provenance.md)
for how it was checked.

## Status

**113 of 113 concepts written**, across all ten categories, in dependency order
so every page links backwards to something that exists. `fieldguide status`
prints the breakdown by category and tier.

Every golden path has been executed, including the steps that are supposed to
fail, and where a claim could not be executed honestly the page says so instead
of implying otherwise. Three cases are worth naming, because they set the
standard for the rest:

- The six `context`-tier domain pages had no corpus of their own to measure, so
  all six ship a runnable drill in [`drills/`](drills/). Two of those drills are
  honest substitutes rather than the real thing: the GPU one measures arithmetic
  intensity on a CPU, where the ratio argument transfers and none of the numbers
  do, and the robotics one simulates the two frame properties ROS REP 105
  specifies rather than running ROS. Both pages open with a banner saying so.
- [`demonstrations.yaml`](demonstrations.yaml) records, per concept, which of
  the two repositories demonstrates it and how far, including the concepts
  neither one demonstrates at all.
- Sixteen concepts cannot be demonstrated here, ten because they need a model
  and six because the evidence is a conversation in someone else's repository.
  Each of those pages says what environment the demonstration needs, what you
  would run, what you would see and how you would know the setup was broken, so
  the gap is a specification rather than an absence. A test enforces it.
- Measurements that vary between runs are reported with their variance rather
  than as a single figure. The real-time drill's deadline-miss count ranges
  from 67 to 205 out of 250 on a shared machine, and the page says so.

What is still worth doing is in [`BACKLOG.md`](BACKLOG.md), in priority
order, including the items that are deliberately not being done.

MIT licensed.
