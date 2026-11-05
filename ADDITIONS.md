# Additions

Everything identified by the consistency audit of 2026-10-27, ordered highest
to lowest priority. Priority is value divided by effort, not size.

The corpus is complete at 106 of 106 pages. Nothing on this list is a gap in
coverage; these are improvements to navigation, evidence and prose quality,
plus one item that is blocked on a decision only the author can make.

**Status key:** `[ ]` not started · `[~]` in progress · `[x]` done

---

## P1 Navigation: two new learning paths

Path coverage is the largest structural gap. Three categories are almost
unreachable by any curated route, and two of them are what the source postings
lean on hardest.

```
  meas    Measurement and feedback    1/7
  auto    Automation with Python      0/3
  dom     Domain context              0/6
```

- [x] **A1. A measurement-and-automation path.** The seven measurement
  concepts plus the three automation ones, in dependency order. Registry edits
  only; the page, the ordering check and the computed entry state all come
  free. Takes path coverage from 69/106 to 78/106. (Done: 8 paths, 10 steps, 37 hours, `prove-the-outcomes`.)
- [x] **A2. A domain-context path.** The six `dom` concepts, which have a
  natural order (`ai-stack` and `inference-serving` before the rest). Takes
  coverage to 84/106. (Done: 9 paths, 6 steps, 24 hours, `domain-context`. meas, auto and dom are now 7/7, 3/3 and 6/6.)

Deliberately **not** doing: a path over the eight pathless `dac` concepts.
They are mutually exclusive tool choices rather than steps, and a path listing
all of them would misrepresent how anyone works.

---

## P2 Evidence: demonstration entries for artifacts that already exist

Five core concepts were listed here as recorded-undemonstrated while an
artifact that demonstrates them already existed. Checking each against its own
page's definition resolved that differently: two were real bookkeeping gaps and
are fixed, one was wrong, and two turned out to need an artifact after all. The
lesson is the project's usual one, that a gap found by reasoning needs checking
before it is acted on.

- [x] **B1. `tutorial-design`** against `docpack/docs/tutorials/getting-started.md`,
  which `scripts/coldstart.sh` executes from an empty virtual environment with
  three assertions on its promised output. (Done: entry added, `extent: full`,
  page corrected. The blind-run count is zero and the page says so.)
- [x] **B3. `information-architecture`** against `concepts.yaml`: 106 units, a
  closed vocabulary for category, tier and Diátaxis type, a prerequisite DAG
  with a cycle check, and every route generated. (Done: entry added,
  `extent: full`, page corrected. The third IA decision, whether readers find
  things, stays unevidenced because there are no readers.)
- [-] **B2. `sample-walkthroughs`: rejected.** Checked against the page's own
  definition and it does not hold. A walkthrough "explains a sample that
  already exists" and "the reader does not build anything"; docpack's tutorial
  has the reader build, and its three how-to pages are task recipes. Neither is
  a walkthrough, and the page's existing claim that no demonstration exists is
  correct. Left alone.
- [x] **B4. `instructional-design`** and **B5. `cognitive-load`.** Unblocked
  by C5 and done. Both now point at `src/fieldguide/audit.py` with
  `extent: partial`, and both credibility paragraphs were rewritten to state
  the split that `partial` means: the instrument is demonstrated, the effect on
  a reader is not. Core concepts with no demonstration: 25 at the start of this
  list, 15 now.

---

## P3 Evidence: new artifacts that can be built in this environment

Four concepts can be demonstrated honestly here and are not.

- [ ] **C1. A `release-check` guided workflow.** Demonstrates
  `guided-workflows` and `release-readiness` with one artifact. The
  guided-workflows page already specifies the design, including the explicit
  `GATES` list and the finding that none of its three steps actually gated
  anything, and that page currently admits `fieldguide check` is a validator
  rather than a workflow.
- [ ] **C2. A playbook drill.** A validated decision graph: nodes, outcomes,
  a check that every outcome is reachable and every node terminates.
  Demonstrates `playbooks`.
- [ ] **C3. A vector-store drill.** Exact against approximate search, and
  hybrid lexical-plus-vector ranking, over deterministic hashed vectors.
  Demonstrates the *mechanics* of `vector-stores` without model weights, and
  must say plainly that no real embeddings are involved.
- [x] **C5. Commit the corpus audit as `fieldguide audit`.** Done, and it
  found something. `src/fieldguide/audit.py`, wired into the CLI, documented in
  the README because the capability gate requires it, with 13 tests in
  `tests/test_audit.py` whose fixtures pin the three measurement bugs that
  preceded it: the nested fence that leaked a shell session into the prose, the
  wrapped duration, and the heading matched inside a code sample.

  The finding: the committed tool disagreed with the figures the five pages had
  published, because the two new paths from A1 and A2 changed the link census
  and later edits moved the word counts. All five pages are reconciled to the
  tool's output, which is the point of committing it. A figure that only a
  discarded script can produce is not reproducible, however carefully it was
  measured.
- [ ] **C4. A Sphinx drill.** The build-time comparison quoted on the
  Docusaurus page was measured and never committed, so commit it:
  `sphinx-build` with `-W` and `nitpicky`, against the same corpus as MkDocs.
  Demonstrates `sphinx`.

---

## P4 Evidence: specify the demonstrations this environment cannot run

For every core concept that stays undemonstrated, add a block under **How to
prove it** saying what a demonstration would consist of elsewhere, what
environment it needs, and what a learner would actually see. The point is to
turn an absence into a specification: a reader should finish knowing how they
would work with the concept and what the result would look like, even though
no output is shown here.

Each block answers four questions in this order: what you would need, what you
would do, what you would see, and what would tell you it had failed.

### Blocked on a model or on weights (9)

- [ ] **D1.** `prompting`, `output-evaluation`, `llm-content-lifecycle`
- [ ] **D2.** `ai-assistants`, `agentic-workflows`, `coding-agents`
- [ ] **D3.** `agent-skills`, `ai-trust-judgment`, `embeddings`

### Not provable by a repository, by nature (6)

These need a person, a team or a working relationship. The block describes the
activity and its observable result rather than a command.

- [ ] **D4.** `technical-writing`, `systems-mindset`, `docs-as-product`
- [ ] **D5.** `sme-interviews`, `reading-code-to-verify`, `implementation-feedback`

---

## P5 Quality: defects the audit quantified but did not fix

- [x] **E1. Standardise the proof-task label.** Done, and it was three
  elements rather than one. Sweeping every structural element at once, which
  is what `assessment` says the lesson is, found the proof-task label plus two
  more pairs (`One sharper point.` against `A sharper point.`, and the two
  credibility wordings), and then a fourth variant on five pages that a
  frequency floor had hidden. All nine labelled elements are now declared in
  `STRUCTURAL_LABELS`, the scaffold emits them, and `fieldguide audit` reports
  every repeated bolded opener that is not declared, so the next one surfaces
  without anybody sweeping.
- [x] **E2. Raise the success-criterion rate.** Done, and the first thing it
  found was that 53 of 318 was wrong. The classifier matched the preposition
  `against` and recognised no conditional, predicted value or author
  comparison, so the guide's self-declared weakest number was about half the
  real one. Sixty hand-labelled tasks put the true rate near 40 per cent of a
  sample where the old instrument saw 17. A pass then added one clause to the
  best-suited task on all 22 `core` pages that genuinely had none, taking the
  measured corpus rate from 33 to 40 per cent, and the labelled set is frozen
  as a fixture the classifier is scored against on every run.
- [x] **E3. The six pages with a sentence over 60 words.** Done; there are now
  none, and a test holds the ceiling at 55. Three of the six were two
  sentences joined by a splitter that did not treat `.**` as a boundary.
- [x] **E4. The 59 pages with a sentence over 45 words.** Down to 27, and
  stopping there on purpose: the rest are dense colon-enumerations that read
  better than their word count suggests, and further edits trade clarity for a
  number.

---

## P6 Blocked on a decision

- [ ] **F1. The four placeholder URLs.** `site_url` and `repo_url` in each
  `mkdocs.yml`, plus a hardcoded fallback in
  `docpack/.github/workflows/docs.yml` and the two project URLs in
  `demonstrations.yaml`. Needs a GitHub account name and a decision on the
  repository names. `scripts/prepublication.py` exits 1 until this is done.

---

## Explicitly out of scope

- **Upgrading the 11 `partial` core demonstrations to `full`.** All five
  measurement concepts are among them, and the limit is an audience rather
  than code. No amount of work in this repository changes it.
- **A path over the `dac` alternatives.** See P1.
- **Real embeddings, a real GPU, a real robot, a real simulator.** Recorded as
  absent on the pages that need them; P4 specifies what they would show.
