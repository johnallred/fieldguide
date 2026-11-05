# Drills

Short, runnable scripts behind the measurements quoted on the concept pages.
Each one prints the figures the corresponding page cites, so a reader can check
a claim rather than trust it.

They live outside `src/fieldguide/` because they are not part of the package,
and most of them need a dependency the guide itself does not.

## Domain measurements

| Drill | Needs | Page |
|---|---|---|
| `vector_store.py` | `pip install numpy` | Vector stores and hybrid search |
| `generator_build.py` | `pip install sphinx` | Choosing a static site generator |
| `usd_composition.py` | `pip install usd-core` | OpenUSD and Omniverse |
| `inference_sweep.py` | `pip install onnx onnxruntime` | Inference serving |
| `onnx_compat.py` | `pip install onnx onnxruntime` | Reading an AI software stack |
| `deadline_sweep.py` | nothing | Real-time and graphics systems |
| `arithmetic_intensity.py` | `pip install numpy` | GPU computing and CUDA |
| `frames.py` | `pip install numpy` | Robotics simulation |

Two caveats the pages also state. `arithmetic_intensity.py` runs on a CPU and
demonstrates a GPU lesson by analogy: the ratio argument transfers and none of
the numbers do. `frames.py` simulates the frame properties that ROS REP 105
specifies; it is not ROS, and no robot or simulator is involved.

Timing output varies by machine, by a factor of three on the deadline sweep.
The figures quoted on those pages were measured on a 2-core Xeon with no GPU,
and the pages say so rather than presenting them as constants.

`vector_store.py` is the one in that table whose figures are partly constant:
its recall and scanned-vector columns are identical on every run and its
milliseconds are not, so its page quotes the first as fact and the second as
one machine. A test pins the constant columns.

## Golden paths, committed

| Drill | Needs | Page |
|---|---|---|
| `screencast_script.py` | nothing | Screencasts and video |
| `security_lint.py` | nothing | Documenting security |
| `workshop_arithmetic.py` | nothing | Workshops and live training |
| `terminology_drift.py` | `pyyaml` | Terminology drift |
| `crawlability.py` | nothing | Crawlability and indexability |
| `guardrails.py` | nothing | Hallucination guardrails |
| `gallery_audit.py` | `pyyaml` | Sample apps and galleries |
| `walkthrough_transclusion.py` | `mkdocs`, `pymdown-extensions` | Sample walkthroughs |
| `playbook.py` | `pyyaml` | Playbooks and decision guides |
| `sphinx_autodoc.py` | `pip install sphinx myst-parser` | Sphinx |

These ten are different in kind. Their pages are golden paths: a reader can
follow the steps and build the thing. But following them means retyping, and
nothing checked that the code printed in the page still produced the output
printed beside it. Eight of the ten quoted a run from a scratch directory that was
never committed, which is the defect `docpack` exists to prevent for in-page
samples and this guide had not prevented for its own.

So they are committed, their pages cite them, and `tests/test_drills.py` holds
the contract in both directions:

- the drill still prints the lines its page quotes, and
- the page still quotes the lines the drill prints, and
- where a drill lints or measures sample files, those files are byte-for-byte
  the ones the page tells the reader to create, and
- for `crawlability.py`, the audit it runs is byte-for-byte the script the page
  prints, because the drill writes that script out and runs it as a
  subprocess rather than reimplementing it, and
- for `guardrails.py`, the results table published on the page is parsed and
  compared cell by cell to the matrix a real run produces.

Each drill walks several states in one run and exits zero once it has proved
all of them, which is why `expect_exit` is part of the contract rather than
assumed.

## What committing them found

Writing a drill for a page that already had a golden path turned out to be an
audit of the page. Seven of the ten above were wrong in some way, and so was
one page from the domain table, which is why the list below has eleven rows for
ten drills. None of it was visible from reading, and none of it would have been
caught by running the drill alone: each defect needed the drill and the page
compared.

| Page | What was wrong |
|---|---|
| Workshops | Called a 34-hour path the guide's shortest; a 24-hour path had been added since. Correcting it made the argument stronger, since two hands-on hours is 8% of the real shortest rather than 6% |
| Documenting security | Quoted findings its own rule table could not produce; two reasons had been hand-trimmed to a shorter form |
| Crawlability | Ran its audit twice and quoted no output either time, so the golden path had nothing to check against. Publishing the output exposed a false positive: the no-JavaScript word count flags a 16-word static page, because from the outside that is indistinguishable from a client-rendered shell |
| Sample apps | Quoted a checker's output without printing the checker or the three sample programs it ran, so the path was unreachable. One table's row order came from a set's iteration order and could not be reproduced |
| Sample walkthroughs | Reported three quoted blocks where the walkthrough it tells you to write has two |
| Sphinx | Quoted a signature line with a real arrow where the extraction script prints `&#x2192;`, and claimed "six times slower cold" where a steady-state cold build measures about three times |
| Choosing a static site generator | Its build-time figure described CI rather than authoring, and inverts above about 120 pages: MkDocs rebuilds everything, Sphinx rebuilds what changed |
| Playbooks | Printed its validator in fragments and quoted output from a script that appears nowhere. Its step 4 had been trimmed to one line per defect class, hiding that two of four injections cascade: four defects produce six findings |
| Screencasts, terminology drift, hallucination guardrails | Reproduced exactly; no defect found |

The pattern is worth naming because it generalises. A page that quotes output
is making two claims, that the code does this and that this is what the code
does, and a reader can check neither without retyping the whole thing. The
cheap half of the fix is committing the code. The half that actually finds
defects is asserting that the page and the code still agree.
