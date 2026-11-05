# Backlog

All 106 concepts are written and every gate is green. This is what is still
worth doing, in priority order, with what "done" means for each.

It is in the repository rather than in a tracker on purpose. A corpus that
publishes its own gaps is making a checkable claim about its author's judgment,
which is the argument the [demonstrated](docs/demonstrated.md) page makes about
missing demonstrations and applies equally here.

**Status key:** `[ ]` not started · `[~]` in progress · `[x]` done · `[!]` blocked

---

## 1. `[x]` A learning path over measurement and automation

**Why first.** Path coverage was 69 of 106, and it is not evenly thin:

```
  meas    Measurement and feedback      1/7
  auto    Automation with Python        0/3
  dom     Domain context                0/6
```

Measurement and automation are the two categories the NVIDIA posting leans on
hardest, "measurable reductions in support load" and "Python proficiency to
automate content tasks, transform data, and integrate with APIs", and a reader
who arrives wanting exactly that has no curated route through either.

**Done when** a new path exists in `concepts.yaml` covering the seven
measurement concepts and the three automation ones in dependency order,
`fieldguide check` reports zero ordering violations, the generated page states
its assumed entry state before step 1, and path coverage is at least 79 of 106.

**Effort** about an hour. Registry edits; the page, the ordering check and the
entry-state paragraph are all generated.

**Done.** `prove-the-outcomes` exists: 10 steps, 37 hours, covering all three
automation concepts and all seven measurement ones, zero ordering violations,
and an entry state naming the five concepts it assumes from outside. Path
coverage went 69 to 84 of 106; measurement is 7/7 and automation 3/3.

---

## 2. `[x]` "How this would be demonstrated elsewhere" for the 10 model-blocked concepts

**Why.** Nine core concepts have no demonstration because this environment has
no model access and no network route to weights. Saying so is honest and leaves
a learner with nothing to do. A reader who cannot run the thing can still be
told what they would need, what they would run, and what they would see, which
turns an absence into a specification.

Concepts: `embeddings`, `vector-stores` (the embedding half),
`output-evaluation`, `prompting`, `llm-content-lifecycle`, `agent-skills`,
`ai-assistants`, `agentic-workflows`, `coding-agents`, `ai-trust-judgment`.

**Done when** each of those pages carries a `### How this would be demonstrated
elsewhere` subsection under *How to prove it*, stating: the environment
required, named concretely; the procedure, as commands or steps specific enough
to follow; the figures or behaviour a learner would observe, with rough
magnitudes and what each one would mean; and how they would know the
demonstration had failed rather than merely surprised them. The seven-section
contract is unchanged, since these are `###` under an existing section.

**Effort** half a day. The content is reasoning rather than measurement, so it
must be written as reasoning and marked as such.

**Done.** All ten pages carry the subsection, each opening by stating that
nothing on it was run here. Each gives the environment, the procedure, a table
of observations with rough magnitudes and what each one means, and a failure
signature so a learner can tell a broken setup from a surprising result. Ten is
the right count; the heading said nine and listed ten, because
`ai-trust-judgment` sits in the craft category while being blocked for the same
reason as the rest.

---

## 3. `[x]` The same, for the 6 concepts a repository cannot prove

**Why.** Six are not blocked by tooling; they are the wrong shape for a
repository to demonstrate at all. `demonstrations.yaml` already argues this in
its header and the argument should not be diluted. But "unprovable here" is not
the same as "unlearnable", and a learner deserves to know what practising these
actually looks like.

Concepts: `technical-writing`, `systems-mindset`, `docs-as-product`,
`sme-interviews`, `reading-code-to-verify`, `implementation-feedback`.

**Done when** each carries the same subsection, describing the setting in which
the skill is exercised, what a learner would do, what evidence of competence
looks like, and why that evidence cannot be committed to a repository. These
should be honest about being craft rather than mechanism.

**Effort** half a day.

---

## 4. `[x]` Triage the other 29 concepts with no demonstration entry

**Why.** Writing items 2 and 3 turned up a larger gap than either: 45 concepts
have no entry in `demonstrations.yaml`, and the 16 blocked ones are now
accounted for. The other 29 are a mix that has never been sorted:

| Likely class | Examples | What it needs |
|---|---|---|
| Demonstrable, already on this backlog | `sphinx`, `playbooks`, `guided-workflows`, `release-readiness` | Items 7, 9, 10 |
| Golden path executed but never recorded | `mdx`, `docusaurus`, `openapi`, `versioning`, `localization` | An entry, or an honest note that the run was not committed |
| Genuinely undemonstrated and demonstrable | `terminology-drift`, `docs-review`, `content-retirement` | A decision about whether to build it |
| Arguably out of scope for a repository | `user-stories`, `partner-documentation`, `working-with-engineers` | The item 3 treatment |

**Done when** every one of the 29 is in exactly one of those buckets, in a
single commit that either adds an entry, adds the subsection, or adds a backlog
line. The point is that the set is sorted, not that it is emptied.

**Effort** two hours of judgment, then whatever the buckets imply.

**Done, and it grew.** The triage is now a validated `triage:` map in
`demonstrations.yaml` rather than a note, because an unvalidated register is
the thing this file exists to argue against. Every one of the 106 concepts is
either demonstrated or carries one of five reasons, and the build fails on a
concept that is neither, on an unknown reason, and on a concept that is both.
Two tests assert that those rules fire rather than merely pass today.

| Reason | Concepts | Meaning |
|---|---|---|
| `planned` | 0 | Empty. Was four; items 6, 7, 9 and 10 cleared it. Note item 8's `vector-stores` was triaged `blocked`, not `planned` |
| `declined` | 7 | Would mean adopting a second generator, markup language, release train or translation pipeline in a twelve-page project |
| `needs-organisation` | 13 | The evidence is a process, a conversation, or a decision in someone else's repository |
| `blocked` | 9 | Needs a model, weights or hardware this environment does not have. Was ten; item 8 showed `vector-stores` was only half blocked |

The `scratch` row is gone because item 5 emptied it. All eight of its concepts
have a committed drill.

Three concepts turned out to have a committed artifact already and got entries
instead of a reason: `reproducible-environments` against `coldstart.sh`,
`gpu-computing` against `drills/arithmetic_intensity.py`, and `assessment`
against `fieldguide audit`. The `gpu-computing` case was an outright
inconsistency, since the drill was committed while the page said no
demonstration existed.

Two other things came out of it. The `demonstrated` page's explanation of the
gaps was hardcoded prose claiming four categories were at zero when one is, so
it is now derived from the triage, and the test that had pinned the old
heading was pinning a measured count inside a sentence. And the seven
`needs-organisation` concepts that lacked the "demonstrated elsewhere"
subsection now have it, bringing that total to 23 pages, enforced by a check
driven off the register rather than off a hand-kept list.

---

## 5. `[x]` Commit or restate the 8 `scratch` measurements

**Why.** The triage's most actionable bucket, and the one that is a correctness
problem rather than a gap. Eight pages quote a figure from a measurement that
ran in a scratch directory and was never committed, so a reader cannot
reproduce it: `sample-walkthroughs`, `sample-apps`, `hallucination-guardrails`,
`workshops`, `screencasts`, `security-documentation`, `crawlability`,
`terminology-drift`.

Every other page in the corpus either cites a committed artifact or says
plainly that nothing was run. These eight sit in between, which is the one
position the project's own standard does not allow.

**Done.** All eight are committed as drills rather than restated, and the
`scratch` reason is retired: it is the one triage category that emptied out,
and leaving it at zero would make the register look like it still held work.
`drills/` went from six scripts to fourteen and `tests/test_drills.py` holds
the contract in both directions, so a drill that stops printing what its page
quotes fails, and so does a page that stops quoting what its drill prints.

Restating was the stated alternative and turned out to be the wrong one in
every case. Each of these pages had a golden path a reader could follow; what
was missing was not a weaker claim but the thing that checks the claim.

**What it found.** Six of the eight pages were wrong, and none of it was
visible from reading:

| Page | Defect |
|---|---|
| `workshops` | Called the 34-hour first-week path the guide's shortest. It stopped being shortest when the 24-hour `domain-context` path was added. The claim was prose, the answer was in `concepts.yaml`, nothing connected them |
| `security-documentation` | Quoted findings its own rule table could not produce; two reasons had been hand-trimmed |
| `crawlability` | Ran its audit twice and quoted no output either time, so the path had nothing to check against |
| `sample-apps` | Quoted a checker's output without printing the checker or the samples it ran, so the path was unreachable; one table's row order came from a set |
| `sample-walkthroughs` | Reported three quoted blocks where its walkthrough has two |
| `screencasts`, `terminology-drift`, `hallucination-guardrails` | Reproduced exactly |

Two of those are worth more than the fix. Publishing `crawlability`'s output
exposed a **false positive**: the no-JavaScript word count flags a sixteen-word
static page, because from the outside a short page and a client-rendered shell
are the same thing, a fetch that returns almost no words. That is the limit of
what a word count can know rather than a bug, and the page now says so beside
the finding, because a check whose false positives are unpublished gets
switched off the first time it annoys somebody.

And `workshops` corrected in the unflattering direction: two hands-on hours is
eight per cent of the guide's genuinely shortest path, not six per cent of the
one the page had picked. A stale superlative that makes your own argument
weaker when fixed is the kind worth looking for.

**The general lesson**, which is the one to tell an interviewer. A page that
quotes output makes two claims: that the code does this, and that this is what
the code does. Committing the code is the cheap half. Asserting that the page
and the code still agree is the half that finds defects, and it found six.

---

## 6. `[x]` Three demonstration entries for artifacts that already exist

**Why.** Three core concepts were recorded as undemonstrated and arguably were
not: `tutorial-design` against `docpack`'s tutorial, `sample-walkthroughs`
against the same tutorial read as a walkthrough, and
`information-architecture` against the registry and its validators.

**Done, two of three, and the third was a correction.** `tutorial-design` and
`information-architecture` both have `full` entries, against
`docs/tutorials/getting-started.md` and `concepts.yaml`.

`sample-walkthroughs` does not, and that was the right call. Reading a tutorial
as a walkthrough is not the same artifact: a walkthrough's job is to be read
rather than run, and the page asks for a drift check and a transclusion that
`docpack`'s tutorial does not have. It was triaged `scratch` instead, which put
it in item 5, where item 5 gave it a drill of its own:
`drills/walkthrough_transclusion.py`. Claiming it would have been the easy direction
to be wrong in.

---

## 7. `[x]` A `release-check` command, for `guided-workflows` and `release-readiness`

**Why.** Two core concepts want the same artifact and neither has it. The
`guided-workflows` page already specifies the design, including the explicit
`GATES` list and the finding that none of its three example steps actually
gated anything, and it admits that `fieldguide check` is a validator that
reports everything at once rather than walking anyone through anything.

**Done.** `fieldguide release-check` is seven named steps in
`src/fieldguide/release.py`, each returning a detail on success and raising
`Blocked` with a specific remedy on failure. It runs in CI as a ninth gate,
`tests/test_release.py` holds it to all three properties, and both concepts
now have register entries: `guided-workflows` as `full`,
`release-readiness` as `partial`.

`drills/release_rounds.py` reproduces the round-trip measurement against the
real command, by the page's own method: copy the repository, plant three
independent defects, fix exactly what each run reports, count the runs. **Four
against two**, the same ratio the toy workflow produced, because the ratio is a
property of the gating decision rather than of the workflow's size.

**What it found.** Three things, and the first is the one worth telling.

`GATES` is not empty here, and that is a better result than the page's.
Exactly one of seven steps gates: every other step calls `load_registry`, so a
registry that will not parse turns the remaining six into secondary failures
about a file none of them could read. The page's finding was that nothing
gated; the sharper finding is that gates are real and rare, and one in seven is
the honest number for a workflow of this shape.

The step named "the registry parses" caught the registry's own validation error
and not `yaml.YAMLError`, so the commonest way a registry fails to parse walked
straight past the step named after it. `test_a_broken_registry_stops_the_workflow`
caught that. A step's name is a claim about what it checks, and the two drift
apart as quietly as a figure on a page.

And `documentation-ci.md` had become arithmetically wrong. It said the guide
"had eight gates" and that the render gate was "a ninth", a figure with no way
to stay right once more gates were added. The story was about a blind spot and
did not need the count, so the count is gone and the workflow file is the
count.

**Where it stops.** `release-readiness` is `partial` rather than `full` on
purpose. The gate exists, blocks, and carries `--report-only` for the
run-it-before-you-enforce-it advice the page gives. What no solo repository can
demonstrate is the political half: the only author here is also the only
reviewer, so nobody else ever accepted the constraint. The page now says that
instead of implying otherwise.

---

## 8. `[x]` A vector-store drill, for `vector-stores`

**Why.** The concept is recorded as undemonstrated because real embeddings need
weights this environment cannot fetch. The *mechanics* do not: exact against
approximate search, recall against latency, and hybrid lexical-plus-vector
ranking can all be shown over deterministic hashed vectors, which is honest
about not being a real embedding model and still teaches the thing readers get
wrong.

**Done, with one of the three criteria refused.** `drills/vector_store.py`
builds an IVF index over 4000 hashed vectors in 64 dimensions and sweeps
`nprobe`:

```
  nprobe  scanned  recall@10  ms/query  speedup
       1       67     0.548      0.02    7.6x
       8      521     0.988      0.04    4.1x
      64     4000     1.000      0.44    0.4x
```

The concept moves out of `blocked` and into the register as `partial`. Recall
and `scanned` are identical on every run and pinned by a test; the milliseconds
are one machine and the page says so.

**The criterion I did not meet, and why that is the right answer.** "A hybrid
ranking beating either half" cannot be shown honestly with hashed vectors, and
the drill measures the failure rather than quietly dropping the goal:

```
  retriever  identifier     paraphrase     both
  lexical    1.000          0.135          0.568
  dense      0.880          0.000          0.440
  hybrid     0.935          0.065          0.500
```

Hybrid wins when its two halves fail on *different* queries, and the dense half
earns its share by knowing that "too much ram" and `memory` are related. A hash
function has learned nothing, so both halves fail on paraphrase and fusing them
produces a third thing that fails. The page now tabulates exactly which
properties survive the substitution: exact search, approximate recall loss and
the recall-latency curve do, because they are facts about the geometry of
points; semantic matching and therefore every quality comparison do not.

**Three findings came out of building it**, and the third is the best one.

*Past the knee, the approximate index is slower than brute force.* At `nprobe`
32 and 64 the speedup is 0.8x and 0.4x, because gathering candidates from
clusters costs more than the comparisons it saves. A store tuned to maximum
recall is a slower exact search with extra steps, and that is an easy place to
end up by raising `nprobe` until the complaints stop.

*The hashed stand-in accidentally reproduces the opposite of the lesson.* Dense
scores 0.880 on exact-identifier queries, nearly matching BM25, when being bad
at exact identifiers is the failure the page is about. Feature hashing sends
one token to one dimension, so a one-identifier query is a near-one-hot vector
and the "vector search" is a lexical lookup in disguise. A stand-in that
inverts the behaviour you are demonstrating is worse than no stand-in.

*The first measurement was wrong, and the giveaway was a tautology failing.* It
reported 0.924 recall while probing every cluster, which is to say while doing
exactly what exact search does. An index cannot lose recall against itself, so
the number was measuring the measurement: `len(set(found) & set(truth)) / k`
breaks whenever scores tie, and this corpus ties constantly, so the identity of
the top ten was arbitrary among equals while the tenth-best *score* was not.
Scoring against the k-th best score fixes it. Any recall@k figure quoted
without saying how ties were handled now reads differently to me.

---

## 9. `[x]` A playbook drill, for `playbooks`

**Why.** A core `ia` concept with no demonstration. The page describes a
playbook as a validated decision graph, which is a small program: nodes,
outcomes, a check that every path terminates and that no node is unreachable.

**Done.** `drills/playbook.py` validates the page's own integration-failure
guide against five defect classes and injects each one to prove it is caught.
The concept is registered `full`.

| Defect | What a reader experiences |
|---|---|
| Orphaned outcome | Advice nobody can reach; usually the most interesting advice |
| Unreachable node | A question that has silently left the guide, taking its branch with it |
| Dangling target | "See the authentication section", which does not exist |
| Cycle | Being sent back to a question already answered |
| Dead-end option | An answer with no next step, so the reader is stuck |

Five rather than the page's four. The page checked that every *outcome* was
reachable and not that every *node* was, which is the same defect one level up
and the likelier one in a guide edited over a year: a question nobody can reach
is a branch of the expert's knowledge that has quietly left the playbook, and
it is harder to spot by reading than an orphaned outcome because an unreachable
node is well-formed on its own.

Cycles report the looping path, `symptom -> check-trigger -> check-auth ->
symptom`, because "there is a cycle" is not actionable.

**What it found.** Every figure the page quoted was correct, which by now is
the unusual outcome. Two things were missing rather than wrong.

The page printed its playbook in full and its validator in fragments, then
quoted the output of a `check_playbook.py` that appears nowhere on it. Same
shape as the `sample-apps` defect from item 5: a golden path whose output block
is unreachable.

And its step 4 had been trimmed to one line per defect class, which hid that
two of the four injections **cascade**. Breaking `check-trigger`'s `do` leaves
that option dangling and orphans `fix-schedule`, the only route to it.
Mistyping its `go` target breaks that edge and strands `check-auth`. So four
injected defects produce six findings, and two of the six vanish when the other
four are fixed.

That generalises past playbooks and is worth saying to anyone who plans work
from a scan: **a graph validator reports symptoms, and in a graph one broken
edge produces as many symptoms as there were properties depending on it.** The
repair list is always shorter than the findings list, and the only way to learn
how much shorter is to fix one and re-run. The page now prints every finding
each injection produces and says so.

---

## 10. `[x]` A Sphinx drill, for `sphinx`

**Why.** The build-time comparison quoted on the Docusaurus page, 121 pages in
0.6 seconds for MkDocs against 3.5 for Sphinx, was measured and never
committed, so the only figure in the corpus about Sphinx is unreproducible.

**Done, as two drills**, because the item turned out to contain two different
measurements filed under one figure.

`drills/generator_build.py` builds an identical corpus under bare MkDocs and
bare Sphinx at three sizes, cold and warm. `drills/sphinx_autodoc.py` runs the
`sphinx` page's own golden path: autodoc pulls a typed signature out of real
source, the function is renamed, and `nitpicky` with `-W` turns the
unresolvable cross-reference into exit 1. `sphinx` leaves `planned` for
`partial` and `static-site-generators` gains a second entry, so the register's
`planned` bucket is now empty.

Both need dependencies this guide does not have, so neither runs in the suite's
default pass; they sit with the other dependency-bound drills and their pages
say what they print.

**The finding, and it is the best one in this stretch.** The quoted figure
reproduces in direction, is overstated in magnitude, and **inverts** just above
the corpus size it was measured at:

```
  pages   mkdocs   sphinx cold   sphinx warm   warm vs mkdocs
    121     0.50          1.57          0.59   mkdocs 1.2x faster
    240     0.91          2.36          0.58   sphinx 1.6x faster
    480     1.94          4.10          0.65   sphinx 3.0x faster
```

MkDocs rebuilds everything on every run and Sphinx rebuilds what changed, so
MkDocs' time scales with the corpus and Sphinx's warm build is nearly flat. A
ratio measured at one corpus size is not a property of the tools, and this one
was measured at almost exactly the size where the lines cross. The edit loop
says the same: MkDocs wins it at 121 pages and loses it 2.5x at 480.

Three smaller corrections came with it.

The `sphinx` page had this comparison right, with the incremental row included,
and the `docusaurus` page carried the same measurement with that row dropped,
which is the row that reverses the conclusion. **The same figure on two pages,
and the shorter version was the misleading one.**

"Six times slower cold" became about three times. The 3.52 seconds was most
likely a first-ever build paying for imports not yet in the filesystem cache,
which a drill cannot reproduce on demand, so the page says that rather than
quietly publishing a lower number. CI pays the first number every run; a laptop
pays it once.

And the `sphinx` page quoted its autodoc signature line with a real arrow where
the extraction script actually prints `&#x2192;`, because the script strips
tags and leaves entities alone. Trivial, with a non-trivial consequence: a
reader who follows the steps gets output that does not match what they were
promised and cannot tell whether the difference matters.

**Where it stops.** Running Sphinx in a drill is not owning a Sphinx corpus,
and the page now says which work is missing: no large `conf.py`, no custom
extension, no theme fork, no `intersphinx` across teams. Docusaurus is still
one unverified run, because re-measuring it needs an `npm install` of a few
hundred megabytes, and it is now labelled rather than left standing beside two
measured numbers.

---

## 11. `[x]` Standardise the proof-task label

**Why.** Three variants are still in use for one structural element:

```
  Three things to do today:            70
  Three things to do, in order:        35
  Three things to do today, in order:   1
```

This is the defect `instructional-design` and `assessment` both describe, from
two different directions, and neither fixed. The prerequisite label was
standardised when it was found; this one was recorded instead, because it
touches 36 pages.

**Done, and it was four variant pairs rather than one.** The `assessment` page
already says the lesson is to sweep every structural element at once rather
than to fix the one that surfaced, so that is what this did before changing
anything. The sweep found three pairs in use simultaneously:

| Element | Wordings found |
|---|---|
| Proof-task label | "today:" on 70, ", in order:" on 35, a splice of the two on 1 |
| Sharper point | "One sharper point." on 47, "A sharper point." on 35 |
| Credibility | "...rather than decorative." on 72, "What makes it credible." on 34 |

**Two of the three were decided against the majority**, which is the part worth
defending. "in order" beat the commoner "today" because the tasks genuinely
are ordered, with the first always being to run the golden path, while "today"
promises a scope that "compute grounded@k on a corpus you own" does not have.
"rather than decorative" beat the shorter form because that clause is the
section's entire argument. Standardising on the majority would have been less
work and would have made two pages' worth of claims slightly false across a
hundred.

**Then a fourth variant appeared, and it is the finding.** After the sweep
pronounced the corpus clean, `One sharper point, and the best thing to say
here.` turned out to be on five more pages. The sweep had filtered to labels
used ten or more times, so a five-page variant sat below the threshold of the
very instrument meant to find variants. **A frequency floor is a filter on what
you are willing to find.**

**What actually closes this**, as opposed to what standardises it:

- `STRUCTURAL_LABELS` in `registry.py` declares the exact wording of all
  fourteen labelled elements, with `RETIRED_LABELS` keeping the old wordings so
  a reintroduction fails with its own history attached.
- The scaffold emits the labels instead of prompting for them. A prompt that
  says "label the tasks" is how a corpus grows variants; a line already
  carrying the right one is not.
- `fieldguide audit` reports every repeated bolded opener that is **not**
  declared, which is the check that finds what nobody thought of. Counting
  declared labels only confirms what you already know. It surfaced nine
  undeclared repeated labels immediately; all nine turned out to be deliberate
  sub-templates and are now declared, so the list reads `none` and the next
  accidental one will not be buried among them.
- Three tests: no retired wording in use, the scaffold still emits each label,
  and the undeclared list is empty *and* the check can see labels at all.

Both pages that found this defect are updated to record what their own fix got
wrong. `instructional-design` standardised the label that surfaced and asserted
that one string in a test, which could not have found any of the other three.
**A fix applied to the instance is not applied to the class, and the way to
tell is whether the check you add afterwards could find a defect you had not
already found.**

---

## 12. `[x]` Raise the success-criterion rate above 17 per cent

**Why.** 53 of 318 proof tasks say how a learner would know the task worked.
The `assessment` page names the fix, predict-then-check, and prices it at one
clause. It is the number the guide calls its own weakest and it is cheap to
move.

**Done, and the number was wrong before any of it.** The item said "measured
with the same script", and the script was the problem.

### The instrument first

The `assessment` page calls 17 per cent the guide's weakest figure. The
classifier behind it was a keyword list containing `against`, and **16 of its
53 matches were the preposition** in "run it against a corpus you own", which
states no criterion at all. It also recognised none of the forms the corpus
actually uses: not conditionals ("if the answer is two, you have the drift"),
not predicted values ("on a client-rendered site the number is near zero"), not
comparisons to the author's own result ("mine said 72 tests and there were
119"). Wrong in both directions at once, with the net error running *against*
the guide.

So before editing anything, 60 tasks were hand-labelled against a written
definition: a criterion tells the learner something **falsifiable** about the
result, and saying why the task matters does not count. Two independent random
samples, sample B labelled before the classifier existed and used once as a
held-out check.

| | Rate |
|---|---|
| Old keyword classifier | 53/318 (17%) |
| Hand-labelled sample of 60 | 24/60 (40%) |
| Rewritten classifier, before the pass | 104/318 (33%) |
| Rewritten classifier, after the pass | 128/318 (40%) |

The rewritten classifier scores recall 1.00 and precision 1.00 on the held-out
sample, and recall 1.00 with precision 0.89 on the one it was designed against.
Recall is required to be perfect and precision is not, because a missed
criterion understates the corpus and hides work already done, which is exactly
how the 17 happened.

### Then the work

One clause added to the best-suited task on each of the 22 `core` pages that
genuinely had none, chosen by that rule rather than by picking. 33 per cent to
40 per cent, and every `core` page now states at least one criterion, asserted
by `tests/test_criterion.py`.

Nine pages still have none and are staying that way for now: all `supporting`
or `context`. A forced criterion is worse than none, which the page says, and
writing a sentence to satisfy a test is the thing this backlog item would have
become if the rule had been "every page".

**The correction was worth more than the work.** The pass moved the rate seven
points; fixing the instrument moved it sixteen. That is an uncomfortable result
on a page about assessment and it is the one worth telling.

### What makes it stick

- `tests/fixtures/criterion_labels.json` holds all 60 labelled tasks with the
  definition and method beside them. The task text is frozen there on purpose:
  it is the known answer, so it must not move when the corpus does.
- `tests/test_criterion.py` scores the classifier against it every run, asserts
  the specific `against` regression cannot come back, and checks the fixture is
  balanced enough to distinguish a classifier from a constant answer.
- Two clauses written during the pass were **invisible to the classifier the
  moment they were written**: "you will know the gate is wired when..." and
  "more than roughly one suppression per ten pages means...". Both are
  criteria, both are now patterns, and both arrived as misses. A classifier for
  something this open-ended is permanently incomplete, which is the argument
  for scoring it against labels instead of trusting it.

---

## 13. `[x]` A domain-context learning path

**Why.** `dom` is 0 of 6. Lower priority than item 1 because these are
`context`-tier concepts for a reader who needs to follow a conversation rather
than ship, so search may genuinely serve them better than a curated route.
Worth doing only if it reads as a route rather than as a list.

**Done when** either the path exists and coverage reaches 85 of 106, or a short
note in `docs/paths/index.md` explains why domain context deliberately has no
path. The second outcome is a legitimate result.

**Effort** an hour.

**Done.** `domain-context` exists: 6 steps, 24 hours, all six concepts, zero
ordering violations, and no outside prerequisites at all, which is what a
`context`-tier path should look like. Coverage reached 84 rather than the 85 the
criterion guessed at, because the criterion was written before the path was.

---

## 14. `[x]` The long-sentence editing pass

**Why.** 59 of 106 pages carry a sentence over 45 words and 6 carry one over
60. `cognitive-load` identifies the per-page maximum as the metric to act on
and prices the worst cases at an afternoon.

**Done.** No sentence in the corpus exceeds 50 words, and a test holds the
ceiling at 55.

```
                                  before   after the fix   after editing
sentences over 45 words              111             56              33
pages whose longest exceeds 45        59             43              27
pages whose longest exceeds 60         6              5               0
longest sentence in the corpus        71             71              50
```

**The middle column is the finding.** The item said "measured with the same
script", and for the third item in a row the script was part of the problem.

The sentence boundary was a terminator followed by an optional closing quote or
bracket, then whitespace. This corpus ends dozens of sentences in **bold**, so
`.**` was never a boundary and every bolded sentence was silently joined to the
one after it. Three of the six "sentences over 60 words" were two sentences
with a `.**` between them. Widening the class to include markup took the
over-45 count from 111 to 56 without touching a word of prose.

Both columns are published on the page for that reason: showing only the
editing would make an afternoon's work look twice as effective as it was.

**A second defect, in the metric rather than the measurement.** List items are
excluded from the prose count, which is right, and is also a loophole: a
70-word sentence becomes compliant the moment somebody puts a hyphen in front
of it. Four of the five worst sentences here genuinely *were* lists, and
bulleting them is the right edit for a reader. It is also an edit that removes
them from the metric rather than improving them, and those two facts are
independent.

So the audit now reports the longest sentence *inside* list items beside the
prose figure, and a test asserts no item hides a sentence over 45 words. None
does, which is worth knowing rather than assuming.

The first version of that measurement counted each item's *total* words and
reported an 81-word item, which turned out to be four short sentences in a
proof task and not a readability problem at all. Sentences inside items are the
comparable unit; item length is not.

**Where it stops.** 27 pages still carry a sentence between 46 and 50 words,
and they are staying. Most are dense colon-enumerations that read better than
their word count suggests, and the remaining edits start trading clarity for a
number. The ceiling in the test is 55 rather than 45 for the same reason: a
contract nobody meets is not a contract.

---

## 15. `[x]` Demonstration entries for `instructional-design` and `cognitive-load`

**Why.** Both are recorded as undemonstrated on the grounds that they are
properties of a corpus rather than modules. That was true when written and is
now arguable: the seven-section contract, the prerequisite graph, the
`prose_words` gate and the drills are mechanisms, and they are in the
repository.

**Done, and the premise was stale.** Both already had `partial` entries by the
time this came up, so the real question was whether items 11, 12 and 14 had
earned a promotion to `full`. They had not, and the useful part was working out
why not in a way that does not have to be re-derived next time.

**The answer is that this is not a two-concept question.** Eleven entries
claimed, in their own prose, that what was missing was readers or a deployment.
That judgment was being re-litigated per concept because it lived in notes
rather than in the register, so it is now data:

```
| Reason          | Concepts | Why it stops there                            |
| `no-audience`   |    9     | corpus-side half built and measured; the      |
|                 |          | reader-side half needs readers, and this      |
|                 |          | project has none                              |
| `not-published` |    2     | the mechanism runs and gates, but nothing is  |
|                 |          | deployed, so there is no post-publication     |
|                 |          | behaviour to observe                          |
```

The register now has four states rather than three, and the fourth is the one
it took longest to say out loud: demonstrated, undecided (which the loader
refuses), **triaged** (a gap, which closes when somebody does the work) and
**ceilinged** (demonstrated as far as it can be here).

A gap and a ceiling look identical in a coverage percentage and are completely
different things to say to an interviewer. "Nobody has built it yet" invites
the obvious follow-up. "The corpus-side half is built, measured and gated, and
the reader-side half needs readers I do not have" is a statement about the
limits of the evidence, which is more defensible and considerably harder to
write.

**The validator earned its keep immediately.** Listing a concept as ceilinged
requires it to have a demonstration (a concept with none has a gap, not a
ceiling) and to have no `full` entry anywhere. That second rule rejected
`findability` on the first run: its `docpack` entry is `partial` and says so,
but its `fieldguide` entry is `full`, because every page carries its own
description with a gate proving it. **A ceiling belongs to a concept, not to
one project's entry**, and a concept with any `full` entry does not have one.
That distinction was not in my head before the check refused the data.

Two tests hold it: the declared list cannot fall behind the notes in either
direction, and the `full`-plus-ceiling contradiction cannot be recorded.

**The two notes are stronger, which is the part that was actually asked for.**
`instructional-design` now cites the label contract and the undeclared-label
sweep from item 11, including the admission that its own earlier fix asserted
one string and could not have found the three other variant pairs in use at the
time. `cognitive-load` cites a closed loop rather than an instrument: measured,
edited, re-measured, gated at 55 words, with both defects that fell out of
acting on it. And `assessment`'s note no longer quotes 17 per cent.

---

## 17. `[x]` The documentation-consistency pass

**Why.** Items 5 to 15 changed drill counts, gate counts, triage categories and
several measured figures, and the repositories' own front doors were never
re-read against them. A corpus that publishes a page about stale figures should
not have stale figures on its README.

**Done.** Fourteen corrections across both repositories, and one new check.

**The worst class: the page contract.** `Related` became the seventh enforced
section the day a page turned up without one, and the number **six** survived
in seven places afterwards:

| Where | What it said |
|---|---|
| `README.md` numbered list | "the same six questions" |
| `README.md` capability table | "Six required sections, in order, enforced" |
| `docs/index.md` numbered list | "the same six questions" |
| `docs/index.md` | "A page missing one of its six sections fails the build" |
| `the-page-contract.md` front matter | "Six required sections in a fixed order" |
| `the-page-contract.md` check list | "all six headings are present" |
| `fieldguide new` success message | "write the six sections" |
| `scaffold.py` docstring | "a page with its six headings" |

Every one described a contract the code had stopped enforcing. The
page-contract explainer managed to say "seven questions" in its opening
paragraph and "all six headings" ninety lines later, in the same file.

The learning-path count had done the same thing: two paths were added by items
1 and 13, and "seven" survived in three places, including the one-line tree in
the README that is the first thing anybody reads.

**The other corrections.** `drills/` described as six scripts rather than
nineteen. The claim that five of the six domain pages ship a drill and the
sixth does not, when all six now do. `drills/README.md` claiming eight of ten
drills found a defect, when it is seven of ten plus one page from the other
table, which is why its own list had eleven rows for ten drills. ADDITIONS
still saying 21 core concepts lack a demonstration.

**What stops it recurring.** `test_the_prose_cannot_contradict_the_contract_it_describes`
reads the claim out of the prose and compares it to `REQUIRED_SECTIONS` and the
registry, across six files. A wrong number written as a word is valid prose
that spell-checks clean and renders correctly, so proofreading was never going
to find these; counting was.

The first version of that check scanned for "<number> <noun>" anywhere and
reported six findings, four of which were sentences like "Two learning paths
taught a prerequisite too late" and "Write twenty questions with their expected
source pages". **A check that cries wolf gets switched off**, which is the
lesson the `crawlability` page draws about its own false positive, so the
patterns are now an explicit list of the sentences that make the claim. It also
asserts it matched at least eight claims, so it cannot pass by looking nowhere.

The narrowed version still found two the hand sweep had missed, both in the
places a read skips: a table cell and a front-matter summary.

**One dead exemption.** The corpus-size test keeps a register of figures that
deliberately do not match the current corpus, and its own rot check reported
that the `docs-analytics` entry protected nothing: it was added while the
pattern had a broader arm, and when that arm was removed for flagging subset
counts, the entry became an exemption the next real drift on that page would
have inherited. **A dead exemption is invisible from reading, because it looks
exactly like a live one.**

**docpack needed nothing**, which is worth saying because it was checked rather
than assumed. Its 12 pages, 85 chunks, three artifact sizes, 134 tests, ten
gates and all five evaluation figures were verified against a live run and
match character for character.

---

## 18. `[x]` What the fieldguide work implied for docpack

**Why.** The two repositories are siblings and the register spans both, so a
pass over one is not finished until the other has been checked against it.

**Done.** Three things, and the first is the one worth telling.

**docpack had the item-5 defect, in the repository that exists to prevent it.**
`tests/test_doc_samples.py` extracts every Python block from the docs and
executes it, which is real and was the only half. Executing a sample proves it
runs; it says nothing about whether the output printed beside it is still what
it prints. So the README could have promised "packed 12 pages into 85 chunks"
indefinitely after either number moved, and the gate that exists to keep
documentation honest would have stayed green, because the command still exited
zero.

`tests/test_published_figures.py` closes it, with eight tests that re-derive
the figures from live runs rather than duplicating them as constants: the pack
line, the chunk count read off the artifact by a second route, the three
artifact sizes to the significant figure the README actually prints, the five
retrieval scores on the evaluation page, the gate count, and the test count.
A constant in a test is a second place to update, and the second place is the
one that rots.

It found the README's test count was 134 against 142 collected, which is the
same figure that rotted four times in the fieldguide this session.

**Two of my own checks were wrong before the documentation was.** The gate
count filtered out any step whose name began with `Generate`, meaning to skip
the publish job's "Generate AI-readable artifacts", and it swallowed the
quality job's "Generated pages pass validation" with it: nine gates reported
for a workflow with ten, failing against a correct README. A prefix match on a
human-written label is a guess; the job a step belongs to is a fact, so it now
parses the YAML. The second was a case mismatch against prose that capitalises
the first count and not the second.

**The register's `code-sample-validation` entry was overstated.** It claimed
`full` on the strength of executing samples. It is defensible now and the note
says both halves, including which one was missing.

**And nothing verified the register's paths at all.** `load_demonstrations`
checks that every entry names a real concept, a known project and one of two
extents, and never checked the one field a reader follows. Eighty-four entries
name a file, every path was typed by hand across this whole backlog, and a
rename would have left the honesty centrepiece of the portfolio pointing at
nothing with every gate green. Now checked for the local half, and skipped
rather than guessed for the sibling, because saying which half was verified is
the entire point of the register.

**What did not need changing.** docpack has no prose measurement, so it never
had the `.**` sentence-splitter bug. Its 12 pages, 85 chunks, three artifact
sizes, ten gates and all five evaluation figures were already correct, which is
now asserted rather than spot-checked.

---

## 16. `[x]` The four placeholder URLs

**Was blocked on a decision only the author can make.** `scripts/prepublication.py`
exits 1 until `site_url` and `repo_url` are real in both repositories, which is
what it is for.

**Done.** The repositories are
`github.com/johnallred/fieldguide` and `github.com/johnallred/docpack`, and both
gates now report `ready to publish`. Seven lines changed:

| File | What it was |
|---|---|
| `fieldguide/mkdocs.yml` | `site_url` and `repo_url` |
| `docpack/mkdocs.yml` | `site_url` and `repo_url` |
| `fieldguide/demonstrations.yaml` | both project URLs, printed as links on the generated index |
| `docpack/.github/workflows/docs.yml` | the `--site-url` fallback used when the Pages step gives none |
| `fieldguide/docs/concepts/ai-answer-quality.md` | the cross-link into docpack's published evaluation page |

Four teaching uses of `example.github.io` stay exactly as they are: the
`widget` project in the MkDocs and preview-deployment golden paths is fictional
on purpose, and `example.github.io` is the right domain for a sample precisely
because it resolves to nothing.

**The finding, and it is an inversion of this project's usual one.** The gate
reported `ready to publish` while two placeholder repository links sat on a
published page. `demonstrations.yaml` carries each repository's own URL and the
generated `demonstrated` page prints both as links, and that file was not in
`OWN_CONFIG`.

The `publishing-in-public` page argues, at length and correctly, that scoping a
check by a file's **role** beats scoping it by an allowlist of exceptions,
because the role-scoped version transfers to another repository unchanged and
the allowlist cannot. That argument survives. What it does not cover is that
role-scoping is only as complete as the roster of files you decide carry the
role, and **nothing in the idea tells you when you have finished enumerating
it**. That is a quieter failure than the allowlist's: the check looked
principled, transferred perfectly, and still missed two live defects.

The script now reads six files instead of five, with the reason
`demonstrations.yaml` is among them written beside it, and the page has a step 8
making the narrower claim.

**And the backlog was right where the script was wrong**, which is worth
admitting on a project whose whole argument is that measurement beats prose.
This item, written weeks ago by hand, listed the `demonstrations.yaml` project
URLs explicitly. The automated check did not know about them. A hand-kept list
of what needs doing was more complete than the gate meant to replace it, for
exactly as long as nobody re-read the two against each other.

---

## Explicitly not doing

| Not doing | Why |
|---|---|
| A path over the `dac` toolchain category, 6/14 | The pathless ones are mutually exclusive generator choices; a path listing all of them would misrepresent how anyone works |
| Upgrading the 11 `partial` core demonstrations | Most need an audience rather than more code, and a corpus with no readers cannot buy one |
| Demonstrating the 9 model-blocked concepts here | Items 2 covers them honestly instead |
| A FAQ page for repeat questions | `repeat-questions` argues against it specifically |
