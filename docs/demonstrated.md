---
title: Demonstrated
summary: Which concepts have working code behind them, which file does the work, and
  which have none.
diataxis: placeholder
audience: new-user
generated: true
---


# Demonstrated

This guide is prose about how to do the work, and prose is cheap. This page
records which concepts are also *implemented* somewhere you can open, down to
the file that does the work.

**91 of 120 concepts have a demonstration**, 43 of them in full.
The rest of this page is the other side of that number, which is the half worth
reading.

## docpack

*Turns a documentation tree into retrieval-ready, agent-readable artifacts.*

A Python library and the documentation site that documents it, where the site is also the test corpus. Ten CI gates, 142 tests, a 20-case retrieval evaluation, an MCP server, and a cold-start harness that follows the quickstart from an empty virtual environment.

[https://johnallred.github.io/docpack/](https://johnallred.github.io/docpack/) · demonstrates 49 concepts

## fieldguide

*This guide, which validates its own curriculum and its own pages.*

The repository you are reading. It earns entries here only where it does the work rather than describing it: a two-part fence gate that compares fenced source against the rendered code blocks of the built HTML, and an accessibility property test over generated pages. The fence gate found 127 defects across seven pages that every other check had passed.

[https://johnallred.github.io/fieldguide/](https://johnallred.github.io/fieldguide/) · demonstrates 51 concepts

## coldlab

*Provisions a hands-on AWS lab, runs it, checks it and proves the teardown.*

A harness that deploys one lab with the AWS CDK, runs the commands the lab document tells a student to type, asserts on what AWS actually did, tears the stack down in a finally block and resolves every tagged ARN against its owning service. It runs nightly in GitHub Actions through an OIDC role and commits each run to a health record. One lab, one personal account and one region; account vending and a catalogue were deliberately not built.

[https://github.com/johnallred/coldlab](https://github.com/johnallred/coldlab) · demonstrates 3 concepts

## What is demonstrated

`full` means the concept is implemented as this guide describes it. `partial`
means something real is there and the concept page asks for more, and it is used
literally: `rag` is partial because the records are retrieval-ready and nothing
embeds them.

### Information and knowledge architecture

12 of 14.

| Concept | Extent | Repository | Artifact | What it does |
|---|---|---|---|---|
| [Content models](concepts/content-model.md) | :material-check-circle: full | [docpack](https://johnallred.github.io/docpack/) | `src/docpack/frontmatter.py` | Five required front-matter fields, two of them closed vocabularies, rejected in CI by `docpack docs --check`. |
| [Diátaxis](concepts/diataxis.md) | :material-check-circle: full | [docpack](https://johnallred.github.io/docpack/) | `docs/` | Four directories, one declared type per page, enforced rather than conventional. |
| [Information architecture](concepts/information-architecture.md) | :material-check-circle: full | [fieldguide](https://johnallred.github.io/fieldguide/) | `concepts.yaml` | All three decisions made and enforced: units with a closed vocabulary for category, tier and Diataxis type (120 concepts at version 0.2.0), a prerequisite DAG with a cycle check, and generated routes (ten paths in four groups, coverage, a topological study plan). No audience, so findability itself is unevidenced. |
| [Knowledge architecture](concepts/knowledge-architecture.md) | :material-check-circle: full | [fieldguide](https://johnallred.github.io/fieldguide/) | `concepts.yaml` | 120 concepts and 138 prerequisite edges as of version 0.2.0, acyclic and enforced, with a topological order driving the writing sequence. The audit found four supporting concepts carrying more of the graph than the average core concept, and three core concepts correctly isolated because craft skills are not prerequisites. |
| [Metadata for navigation and retrieval](concepts/metadata.md) | :material-check-circle: full | [docpack](https://johnallred.github.io/docpack/) | `src/docpack/pack.py` | Every chunk record carries the page's type, audience, summary, tags and review date, so a retriever can filter before ranking. |
| [Metadata for navigation and retrieval](concepts/metadata.md) | :material-circle-half-full: partial | [fieldguide](https://johnallred.github.io/fieldguide/) | `src/fieldguide/dialect.py` | Front matter must parse as YAML and `diataxis` must be in a closed vocabulary. Added after 46 pages shipped unparseable front matter and 53 claimed a page type a generator had hardcoded. |
| [Playbooks and decision guides](concepts/playbooks.md) | :material-check-circle: full | [fieldguide](https://johnallred.github.io/fieldguide/) | `drills/playbook.py` | A decision guide validated as a graph: dangling targets, dead-end options, orphaned outcomes, unreachable nodes and cycles reported as the looping path. Each class is injected and caught. Committing it found the page's step 4 had been trimmed to one line per class, hiding that two of the four injections cascade, so four defects produce six findings and a findings count is not a repair list. |
| [Taxonomy and controlled vocabularies](concepts/taxonomy.md) | :material-check-circle: full | [docpack](https://johnallred.github.io/docpack/) | `src/docpack/frontmatter.py` | `DIATAXIS_TYPES` and `AUDIENCES` as frozensets: adding a term is a code change and a review. |
| [Content migration](concepts/content-migration.md) | :material-circle-half-full: partial | [fieldguide](https://johnallred.github.io/fieldguide/) | `drills/migration_audit.py` | A migration inventory and its converted pages audited before switch-off: a retired page with 455 readers and no redirect, and six pieces of wiki residue, fixed in a second pass that lands 99.7 per cent of last quarter's traffic on a new page, plus the redirect map. The corpus is invented and no converter is run. |
| [Findability and search design](concepts/findability.md) | :material-circle-half-full: partial | [docpack](https://johnallred.github.io/docpack/) | `mcp_server/server.py` | `list_pages` and `search_docs` filterable by type and audience. No faceted human navigation. |
| [Findability and search design](concepts/findability.md) | :material-check-circle: full | [fieldguide](https://johnallred.github.io/fieldguide/) | `hooks/summary.py` | An audit of the search index found 72 of 73 page summaries absent from it; this hook gives the field three readers (page body, search index, meta description) and a CI step asserts the wiring, because the hook's unit tests pass either way. |
| [Security guidance as encoded standard](concepts/security-documentation.md) | :material-circle-half-full: partial | [fieldguide](https://johnallred.github.io/fieldguide/) | `drills/security_lint.py` | A five-rule linter over a quickstart with six planted problems, which finds five. The miss is the demonstration: the credential rule was case-sensitive and environment variables are uppercase, so it missed the commonest shape a secret takes in a shell sample. Tests pin both the findings and the samples to the page. No threat model, no review process, no real product. |
| [Single-sourcing and content reuse](concepts/single-sourcing.md) | :material-circle-half-full: partial | [docpack](https://johnallred.github.io/docpack/) | `hooks/seo.py` | One `summary` field feeds the meta description, Open Graph, JSON-LD, llms.txt and the retrieval snippet. Field-level reuse, not topic-level. |
| [Style guides and terminology management](concepts/style-guide.md) | :material-circle-half-full: partial | [docpack](https://johnallred.github.io/docpack/) | `styles/Showcase/Terms.yml` | The style guide exists only as enforced rules. There is no prose document for a human to read. |

### Docs-as-code toolchain

8 of 15.

| Concept | Extent | Repository | Artifact | What it does |
|---|---|---|---|---|
| [Choosing a static site generator](concepts/static-site-generators.md) | :material-circle-half-full: partial | [docpack](https://johnallred.github.io/docpack/) | `README.md` | Makes and backs the argument that the generator is the most replaceable part; the docs build unchanged against the stock theme. |
| [Choosing a static site generator](concepts/static-site-generators.md) | :material-circle-half-full: partial | [fieldguide](https://johnallred.github.io/fieldguide/) | `drills/generator_build.py` | An identical corpus built under bare MkDocs and bare Sphinx at three sizes, cold and warm. It found that the build-time figure quoted on two pages described CI rather than authoring and inverted above about 120 pages, since MkDocs rebuilds everything and Sphinx rebuilds what changed. Docusaurus is not in the comparison; re-measuring it needs an npm install this environment will not do. |
| [Docs-as-code](concepts/docs-as-code.md) | :material-check-circle: full | [docpack](https://johnallred.github.io/docpack/) | `.github/workflows/docs.yml` | The whole repository is the demonstration: page source, style rules, content model and pipeline all under review. |
| [Generated API reference](concepts/api-reference-generation.md) | :material-check-circle: full | [docpack](https://johnallred.github.io/docpack/) | `docs/reference/api.md` | mkdocstrings over the package, so the reference cannot drift from the signatures. |
| [Git authoring workflows for writers](concepts/git-authoring.md) | :material-check-circle: full | [docpack](https://johnallred.github.io/docpack/) | `.github/workflows/docs.yml` | Ten gates on every pull request, nine checks plus the cold start, each failing independently so one problem does not mask another. |
| [Markdown and its dialects](concepts/markdown.md) | :material-check-circle: full | [docpack](https://johnallred.github.io/docpack/) | `docs/` | Twelve pages of Markdown with YAML front matter, parsed by the library rather than only rendered. |
| [Markdown and its dialects](concepts/markdown.md) | :material-circle-half-full: partial | [fieldguide](https://johnallred.github.io/fieldguide/) | `src/fieldguide/dialect.py` | A gate for the dialect failure mode. A construct used in prose whose markers survive into the built HTML did not render; covers two constructs, not every dialect. |
| [MkDocs and Material](concepts/mkdocs.md) | :material-check-circle: full | [docpack](https://johnallred.github.io/docpack/) | `mkdocs.yml` | Material plus mkdocstrings, built with `--strict` from the first commit. |
| [Sphinx](concepts/sphinx.md) | :material-circle-half-full: partial | [fieldguide](https://johnallred.github.io/fieldguide/) | `drills/sphinx_autodoc.py` | Autodoc and napoleon pull a typed signature and its parameter docs out of real source, then the function is renamed and nitpicky plus -W turns the unresolvable cross-reference into exit 1. The mechanism is demonstrated; owning a Sphinx corpus is not, and the page says so: no custom extension, no theme fork, no intersphinx across teams. Needs sphinx and myst-parser, which this guide does not depend on. |
| [Diagrams as code](concepts/diagrams-as-code.md) | :material-circle-half-full: partial | [fieldguide](https://johnallred.github.io/fieldguide/) | `drills/diagram_drift.py` | A hand-drawn Mermaid pipeline diagram checked against the GitHub Actions workflow it describes: seven drifted edges and nodes and two missing text alternatives, then a diagram and description generated from the workflow that passes by construction. Parses a flowchart subset only and renders nothing. |

### Quality automation and documentation CI

16 of 17.

| Concept | Extent | Repository | Artifact | What it does |
|---|---|---|---|---|
| [Building a doc test harness](concepts/doc-test-harness.md) | :material-check-circle: full | [fieldguide](https://johnallred.github.io/fieldguide/) | `src/fieldguide/fences.py` | Two halves on purpose. The static half reads source and can be fooled by it; `fieldguide render` compares fenced source against the built HTML and found 127 defects the static checks had passed. |
| [Building a doc test harness](concepts/doc-test-harness.md) | :material-check-circle: full | [docpack](https://johnallred.github.io/docpack/) | `tests/test_doc_samples.py` | The extractor, the skip convention, and an assertion that the skip ratio stays under 25 percent. |
| [Code-sample validation](concepts/code-sample-validation.md) | :material-check-circle: full | [docpack](https://johnallred.github.io/docpack/) | `tests/test_doc_samples.py` | Extracts every Python block from the docs and executes it; `# docpack: skip` makes an exception visible and countable. That is the easier half, and for a while it was the only half: executing a sample proves it runs and says nothing about whether the output printed beside it is still what it prints. `tests/test_published_figures.py` closes that, re-deriving every figure the README and the retrieval page quote from live runs rather than duplicating them as constants, which is the same contract this guide's own drills are held to. |
| [Cold-start testing](concepts/coldstart-testing.md) | :material-check-circle: full | [docpack](https://johnallred.github.io/docpack/) | `scripts/coldstart.sh` | Fresh venv, installs the way a reader would, follows the tutorial literally, and asserts the exact output string the tutorial promises. |
| [Documentation CI](concepts/documentation-ci.md) | :material-check-circle: full | [docpack](https://johnallred.github.io/docpack/) | `.github/workflows/docs.yml` | Content model, links, tests, doc samples, retrieval quality, prose, strict build, and a generated-page wiring check. |
| [Freshness monitoring](concepts/freshness-monitoring.md) | :material-circle-half-full: partial | [docpack](https://johnallred.github.io/docpack/) | `src/docpack/frontmatter.py` | `PageMeta.is_stale` at 365 days, surfaced as a warning and as an `## Optional` section in llms.txt. A property, not a monitor. |
| [Freshness monitoring](concepts/freshness-monitoring.md) | :material-check-circle: full | [fieldguide](https://johnallred.github.io/fieldguide/) | `scripts/freshness.py` | A weekly monitor that compares each demonstration note with the file it describes: the note's date from git blame or a reviewed line, the file's last change from git here and the GitHub API for docpack and coldlab. It keeps one issue labelled freshness current. Its first run flagged 33 of 101 notes, and seven were really stale: two still said 106 concepts, one said seven paths, two carried old audit figures, and two docpack notes miscounted gates and jobs. |
| [GitHub Actions for docs](concepts/github-actions.md) | :material-check-circle: full | [docpack](https://johnallred.github.io/docpack/) | `.github/workflows/docs.yml` | Four jobs: the checks, a separate cold start so the slow check does not hold up fast feedback, then a build job and a deploy job, split so the deploy does not race its own upload. |
| [Link checking](concepts/link-checking.md) | :material-check-circle: full | [docpack](https://johnallred.github.io/docpack/) | `scripts/check_links.py` | Internal links and heading anchors, so a renamed heading fails the build rather than silently breaking a deep link. |
| [Prose linting with Vale](concepts/prose-linting.md) | :material-check-circle: full | [docpack](https://johnallred.github.io/docpack/) | `.vale.ini` | Vale with terminology errors blocking the build and style warnings advisory, because a build that fails on a hedge word teaches people to skip CI. |
| [Accessibility checks](concepts/accessibility.md) | :material-check-circle: full | [fieldguide](https://johnallred.github.io/fieldguide/) | `scripts/a11y_check.py` | A gate over every page of the built site, theme included: language, title, one h1, no skipped heading levels, image alt attributes, named and meaningful links, table headers and labelled form controls. Its first run found 11,102 empty, focusable links, one on every line of every code sample, put there by a highlighter setting; turning it off cleared them. An earlier audit had found seven path pages skipping h1 to h3, fixed in the generator and held by a property test. The mechanical floor, not a conformance claim. |
| [Detecting terminology drift](concepts/terminology-drift.md) | :material-circle-half-full: partial | [fieldguide](https://johnallred.github.io/fieldguide/) | `drills/terminology_drift.py` | Conformance measured against a glossary two ways, to show that the obvious way flatters: a word-boundary search for the canonical term matches inside its own deprecated variants, scoring drift as conformance, so widget reads 60% when the true figure is 33%. Masking variants before counting fixes it. Three pages, not a corpus, and no team or review process is involved. |
| [Doctests and executable docstrings](concepts/doctests.md) | :material-check-circle: full | [docpack](https://johnallred.github.io/docpack/) | `pyproject.toml` | `--doctest-modules` across the package, so every docstring example is executed. One broke a strict build and had to be rewritten. |
| [Lab publishing pipelines](concepts/lab-publishing.md) | :material-circle-half-full: partial | [coldlab](https://github.com/johnallred/coldlab) | `harness/publish.py` | The whole pipeline for one lab: extract.py gates the lab document, every run records the content version it tested, and publish.py promotes a version into published/ for learners after three consecutive passing runs on that exact content, run by the nightly workflow itself, with rollback and a status that tells an environment failure from a broken promotion. Partial until the first promotion is on record: runs before versioning carry no version, so it waits for three nightly runs. |
| [Lab publishing pipelines](concepts/lab-publishing.md) | :material-circle-half-full: partial | [fieldguide](https://johnallred.github.io/fieldguide/) | `drills/lab_publish.py` | A gate over a lab document using coldlab's directive syntax (five blocking problems: an unnamed step, a bare sleep, a reasonless exit exception, a download at lab time, a hardcoded partition and account), promotion counted per immutable version rather than per lab, and rollback separated from fix-forward by whether the content changed. The labs, versions and runs are invented; the real gates behind it are coldlab's extract.py and this guide's own deploy, which needs five gate jobs. No lab catalogue is published through such a pipeline here. |
| [Labs for isolated regions](concepts/isolated-region-labs.md) | :material-circle-half-full: partial | [fieldguide](https://johnallred.github.io/fieldguide/) | `drills/partition_audit.py` | A portability audit for partition, endpoint, region and account literals, downloads at lab time, and services a target region does not offer, with partition facts checked against AWS documentation and the SDK's partition data. Run over coldlab at d38115f it found the lab and its CDK infrastructure close to portable and the test tooling (hosted runners, a public OIDC provider, per-run installs) not. The target service list is invented, and nothing was deployed outside a commercial region. |
| [Learner sandbox guardrails](concepts/learner-sandbox-guardrails.md) | :material-circle-half-full: partial | [coldlab](https://github.com/johnallred/coldlab) | `harness/sandbox.py` | A learner role with an attached permissions boundary (bootstrap/learner-role.yaml), a requirement list of eight things a learner must do and ten they must never do, and a check that asks AWS's policy simulator about each line for the deployed role, plus the finding the simulator cannot see: learners run cdk deploy, which deploys through the CDK's default administrator execution role. The template is checked against the list offline; partial until the check has run against the deployed role, and there are still no real learners. |
| [Learner sandbox guardrails](concepts/learner-sandbox-guardrails.md) | :material-circle-half-full: partial | [fieldguide](https://johnallred.github.io/fieldguide/) | `drills/sandbox_guardrails.py` | Ten learner requests evaluated through an identity policy, a permissions boundary and an SCP with a simplified model of AWS's documented evaluation logic: the identity policy alone stops none of six forbidden requests, the boundary and SCP together stop four, and the two gaps (PassRole on everything, S3 on everything) are traced to their statements. coldlab's scoped CI role, region-denying organisation policy and forecast budget are read as real examples. Nothing calls AWS and no learner has used such a sandbox here. |
| [Preview deployments and publishing](concepts/preview-deployments.md) | :material-circle-half-full: partial | [docpack](https://johnallred.github.io/docpack/) | `.github/workflows/docs.yml` | Publishes to GitHub Pages on main, and regenerates the retrieval artifacts alongside the site. No per-pull-request preview. |
| [Writing custom linters](concepts/custom-linters.md) | :material-check-circle: full | [docpack](https://johnallred.github.io/docpack/) | `styles/Showcase/` | Four hand-written Vale rules (Hedging, Terms, HeadingCase, FutureTense), one of which caught the author's own hedge word in the README. |
| [Writing custom linters](concepts/custom-linters.md) | :material-check-circle: full | [fieldguide](https://johnallred.github.io/fieldguide/) | `src/fieldguide/fences.py` | A rule no pattern matcher can express, because it models shell heredocs to decide which fence markers are markup and which are data. |

### Golden paths and developer onboarding

9 of 9.

| Concept | Extent | Repository | Artifact | What it does |
|---|---|---|---|---|
| [Designing tutorials](concepts/tutorial-design.md) | :material-check-circle: full | [docpack](https://johnallred.github.io/docpack/) | `docs/tutorials/getting-started.md` | Five steps, nine code blocks, one route, no choices before first success; scripts/coldstart.sh runs it from an empty virtual environment and asserts the exact output it promises. |
| [Golden paths](concepts/golden-paths.md) | :material-check-circle: full | [docpack](https://johnallred.github.io/docpack/) | `docs/tutorials/getting-started.md` | Clean environment to four generated artifacts, with a deliberate failure step, verified by the cold-start harness on every push. |
| [Guided workflows](concepts/guided-workflows.md) | :material-check-circle: full | [fieldguide](https://johnallred.github.io/fieldguide/) | `src/fieldguide/release.py` | `fieldguide release-check`: seven named steps over this corpus, each returning a detail on success and a specific remedy on failure, with an explicit GATES set of exactly one, the registry parse every other step depends on. `drills/release_rounds.py` reproduces the round-trip measurement against the real command: four runs against two for the same three independent defects. |
| [Quickstarts that survive contact](concepts/quickstarts.md) | :material-check-circle: full | [docpack](https://johnallred.github.io/docpack/) | `scripts/coldstart.sh` | The quickstart is tested rather than hoped about, including the promise that an invalid content model is rejected. |
| [Sample walkthroughs](concepts/sample-walkthroughs.md) | :material-circle-half-full: partial | [fieldguide](https://johnallred.github.io/fieldguide/) | `drills/walkthrough_transclusion.py` | Five states with a real MkDocs build behind three of them: a copied block caught drifting, the same block transcluded by line range, the sample edited and the page following it, two lines inserted so the transclusion renders the wrong line while the build exits zero, and a named anchor surviving the same insertion. The silent failure is the finding; a string check cannot catch it, because nothing is quoted any more. |
| [Templates and scaffolding](concepts/templates-scaffolding.md) | :material-check-circle: full | [fieldguide](https://johnallred.github.io/fieldguide/) | `src/fieldguide/scaffold.py` | `fieldguide new` computes tags, the work line and both sets of graph links, and names a failure mode in every section prompt. CI asserts its output satisfies the validator for all planned concepts; a measurement showed the prompt comments were supplying 84 per cent of the 450-word gate, so word counts now exclude them. |
| [Templates and scaffolding](concepts/templates-scaffolding.md) | :material-check-circle: full | [docpack](https://johnallred.github.io/docpack/) | `src/docpack/scaffold.py` | `docpack new how-to --title ...` writes a conforming page; CI generates one of each type and validates it, so the generator cannot drift from the validator. |
| [Ephemeral lab environments](concepts/ephemeral-environments.md) | :material-circle-half-full: partial | [fieldguide](https://johnallred.github.io/fieldguide/) | `drills/lab_lifecycle.py` | The full lifecycle (provision, run the lab's own steps, assert, tear down in a finally block, resolve every tagged ARN against its owning service, record) runs in the companion repository coldlab against a real AWS account; this drill reads a dated snapshot of its record (five runs, to 2026-11-24T00:01Z) offline, traces the one flaky check to a misread exit code, sizes a 200-lab catalogue at 26.6 serial hours, and verifies a teardown three ways. It stops at one lab, one personal account and one region: account vending was deliberately not built, no catalogue exists, the record is days old, and cost per run was measured once, from usage times published prices: the CI runner costs about seventeen hundred times the AWS resources. |
| [Ephemeral lab environments](concepts/ephemeral-environments.md) | :material-circle-half-full: partial | [coldlab](https://github.com/johnallred/coldlab) | `harness/run.py` | The whole lifecycle against a real AWS account: deploy, run the lab document's own steps, assert, tear down in a finally block, verify the teardown three ways with every tagged ARN resolved against its service, and append the run to health/health.jsonl, with the summary in health/HEALTH.md generated from it. Partial because it is one lab in one personal account and region, with no account vending. |
| [Reproducible environments](concepts/reproducible-environments.md) | :material-circle-half-full: partial | [docpack](https://johnallred.github.io/docpack/) | `scripts/coldstart.sh` | A fresh virtual environment installed the way a reader would, which is level 2 of the five in the page's own table and the right level for a pure-Python project. It would not catch a system library or a platform difference. |
| [Sample applications and galleries](concepts/sample-apps.md) | :material-circle-half-full: partial | [fieldguide](https://johnallred.github.io/fieldguide/) | `drills/gallery_audit.py` | A four-entry gallery verified against its manifest, two entries failing in two different ways, plus a coverage table crossing what the samples teach against what readers ask. Committing it found the page's golden path was unreachable: it quoted a checker's output without printing the checker or the samples it ran. The ticket distribution is invented and the page says so; the arithmetic over it is real. |

### AI-ready content and agents

13 of 21.

| Concept | Extent | Repository | Artifact | What it does |
|---|---|---|---|---|
| [Agent-ready content](concepts/agent-ready-content.md) | :material-check-circle: full | [docpack](https://johnallred.github.io/docpack/) | `src/docpack/pack.py` | Three outputs for three consumers, with the argument for why one file serves none of them. |
| [Chunking strategies](concepts/chunking.md) | :material-check-circle: full | [docpack](https://johnallred.github.io/docpack/) | `src/docpack/chunk.py` | Heading-aware, fence-state tracking so a `#` comment inside a bash block is not a heading, and content-derived stable ids. |
| [Evaluating retrieval](concepts/retrieval-evaluation.md) | :material-check-circle: full | [docpack](https://johnallred.github.io/docpack/) | `evals/golden.yaml` | Twenty cases scored on hit@1, hit@3, MRR, routing accuracy and grounding, with a floor enforced in CI and the unflattering scores published. |
| [Generative engine optimization](concepts/geo.md) | :material-check-circle: full | [docpack](https://johnallred.github.io/docpack/) | `hooks/seo.py` | JSON-LD `TechArticle` carrying the Diátaxis type, so a crawler learns what kind of question the page can answer, not only its subject. |
| [Grounding and citation](concepts/grounding.md) | :material-circle-half-full: partial | [docpack](https://johnallred.github.io/docpack/) | `src/docpack/evaluate.py` | `grounded@1` checks the top chunk contains the terms an answer must cite. A floor on groundedness, not a citation mechanism. |
| [Model Context Protocol](concepts/mcp.md) | :material-check-circle: full | [docpack](https://johnallred.github.io/docpack/) | `mcp_server/server.py` | JSON-RPC over stdio, dependency-free, three tools, sharing the same retriever the evaluation scores so the eval measures what ships. |
| [RAG pipelines](concepts/rag.md) | :material-circle-half-full: partial | [docpack](https://johnallred.github.io/docpack/) | `src/docpack/pack.py` | Emits chunks with stable ids and filterable metadata. No embedding, no vector store, no retrieval loop; the README argues that is the replaceable part. |
| [Vector stores and hybrid search](concepts/vector-stores.md) | :material-circle-half-full: partial | [fieldguide](https://johnallred.github.io/fieldguide/) | `drills/vector_store.py` | An IVF index over 4000 hashed vectors in 64 dimensions, measuring what an approximate search costs: 0.548 recall@10 probing one cluster of 64, 0.988 probing eight while scanning 13% of the corpus, and slower than brute force past the knee. The vectors are hashed rather than learned, which preserves the recall and latency geometry exactly and preserves nothing about semantics, so the drill also measures what it cannot show and the page tabulates the boundary. |
| [llms.txt and llms-full.txt](concepts/llms-txt.md) | :material-check-circle: full | [docpack](https://johnallred.github.io/docpack/) | `src/docpack/pack.py` | `to_llms_txt` and `to_llms_full_txt`, generated from front matter and grouped by Diátaxis type, so the index cannot go stale. |
| [Crawlability and the agent-ready front door](concepts/crawlability.md) | :material-check-circle: full | [fieldguide](https://johnallred.github.io/fieldguide/) | `scripts/crawl_site.py` | The page's audit pointed at this guide's own published site: text without JavaScript, canonical, distinct descriptions, resolving links, sitemap agreement and llms.txt, as a gate on every build and again against the live site after each deploy. Its first real run found the guide had no llms.txt, now generated from the registry by a build hook, and that a project site under a path cannot have a robots.txt at all. drills/crawlability.py still runs the page's golden path over the planted-defect site. Search-engine indexing itself is not observed. |
| [Hallucination and guardrails](concepts/hallucination-guardrails.md) | :material-circle-half-full: partial | [fieldguide](https://johnallred.github.io/fieldguide/) | `drills/guardrails.py` | Four guardrail layers run against eight fluent answers, six of them wrong, producing the matrix of which layer catches which failure. The result worth having is a negative one: grounding passes a fabricated flag name as soon as real text surrounds it, so only a known-identifier list catches the convincing fabrications. No model, no retrieval and no live pipeline; the answers are written by hand to isolate the failure modes. |
| [SEO for documentation](concepts/seo-for-docs.md) | :material-check-circle: full | [docpack](https://johnallred.github.io/docpack/) | `hooks/seo.py` | Per-page meta description from the content model's `summary`, plus a CI step that fails if the hook is ever unregistered. |
| [Structured data and JSON-LD](concepts/structured-data.md) | :material-check-circle: full | [docpack](https://johnallred.github.io/docpack/) | `hooks/seo.py` | Open Graph, Twitter cards and JSON-LD, all derived from one required field rather than hand-written per page. |

### Measurement and feedback

7 of 7.

| Concept | Extent | Repository | Artifact | What it does |
|---|---|---|---|---|
| [Documentation analytics](concepts/docs-analytics.md) | :material-circle-half-full: partial | [docpack](https://johnallred.github.io/docpack/) | `src/docpack/evaluate.py` | Corpus-side instrumentation only. Every reader-side metric needs an audience this project does not have. |
| [Measuring AI answer quality](concepts/ai-answer-quality.md) | :material-circle-half-full: partial | [docpack](https://johnallred.github.io/docpack/) | `evals/golden.yaml` | grounded@1 and grounded@k over 20 cases, enforced in CI; the model half of answer quality is unmeasured. |
| [Repeat-question analysis](concepts/repeat-questions.md) | :material-circle-half-full: partial | [docpack](https://johnallred.github.io/docpack/) | `docs/explanation/evaluating-retrieval.md` | Two repeat failures diagnosed as vocabulary gaps and fixed in one sentence each, with the score movement recorded; frequency data is absent, so these are candidates rather than a ranked backlog. |
| [Support deflection](concepts/support-deflection.md) | :material-circle-half-full: partial | [docpack](https://johnallred.github.io/docpack/) | `evals/golden.yaml` | Deflection capability computed as answerable against findable, 20/20 and 13/20. Deflection achieved needs a ticket queue and a baseline, and has neither. |
| [Time to first success](concepts/time-to-first-success.md) | :material-circle-half-full: partial | [docpack](https://johnallred.github.io/docpack/) | `scripts/coldstart.sh` | Machine time from empty directory to asserted artifacts, 12.7s of which 11.6s is pip install; reader-side time is not instrumented. |
| [Search and query log analysis](concepts/search-log-analysis.md) | :material-circle-half-full: partial | [docpack](https://johnallred.github.io/docpack/) | `src/docpack/retrieve.py` | Structural findability measured against a hand-written golden set. No query log exists, which is the input the method actually wants. |
| [Turning developer feedback into changes](concepts/developer-feedback-loops.md) | :material-circle-half-full: partial | [docpack](https://johnallred.github.io/docpack/) | `src/docpack/cli.py` | `docpack search` and the reordered README exist because the first real reader could not tell what the library did while ten CI gates were green. Two events, not a practice. |

### Developer education and curriculum

14 of 14.

| Concept | Extent | Repository | Artifact | What it does |
|---|---|---|---|---|
| [Cognitive load in technical content](concepts/cognitive-load.md) | :material-circle-half-full: partial | [fieldguide](https://johnallred.github.io/fieldguide/) | `src/fieldguide/audit.py` | Sentence distribution, per-page maxima and the backward/forward/off-path link census, committed as a subcommand with a test fixture for each of the three fence-parsing bugs that preceded it. The loop is now closed rather than open: the corpus was measured, 59 pages carried a sentence over 45 words and six over 60, the worst were edited, and a test holds the ceiling at 55 so it cannot drift back. Two defects fell out of acting on it. The splitter did not treat a sentence ending in bold as a sentence ending, which accounted for as much of the improvement as the editing did, and the metric excluded list items, so a long sentence became compliant the moment somebody bulleted it; both are fixed and both are published beside the result. The effect on a reader is still unmeasured. Ceiling: no-audience. |
| [Instructional design for developers](concepts/instructional-design.md) | :material-circle-half-full: partial | [fieldguide](https://johnallred.github.io/fieldguide/) | `src/fieldguide/audit.py` | `fieldguide audit` prints the four structural commitments on demand: at version 0.2.0, 103/103 prerequisite lines and 120/120 durations, results and proof sections. Since then the commitments became enforceable rather than measurable: STRUCTURAL_LABELS declares the wording of all fourteen labelled elements, the scaffold emits them so a new page cannot invent a fifteenth, and the audit reports every repeated label nobody declared. That last check is the one that matters, because this page's own fix had standardised the label that surfaced and asserted that one string, which could not have found the three other variant pairs in use at the time. Ceiling: no-audience. |
| [Learner and task analysis](concepts/learner-task-analysis.md) | :material-circle-half-full: partial | [fieldguide](https://johnallred.github.io/fieldguide/) | `drills/task_analysis.py` | A task inventory with every step and decision attributed to an expert interview or an observation, crossed with tagged support tickets and a reader survey: the expert described 0 of 6 decisions, and 2 of 4 struggling tasks turned out to be product obstacles rather than teaching gaps. The tickets and survey are invented and the page says so; the arithmetic is real. |
| [Learning paths and curriculum](concepts/learning-paths.md) | :material-circle-half-full: partial | [fieldguide](https://johnallred.github.io/fieldguide/) | `src/fieldguide/generate.py` | Ten paths generated from the registry in four groups, ordering and grouping enforced in CI, the site menu tested against them, entry state computed; no reader has walked one. |
| [Learning science for developer education](concepts/learning-science.md) | :material-circle-half-full: partial | [fieldguide](https://johnallred.github.io/fieldguide/) | `drills/alignment_audit.py` | A tutorial audited against four learning-science principles (task first, constructive alignment, faded practice) before and after a redesign, 0/3 objectives aligned to 3/3, with both tutorials held identical to the page by a test. It measures structure only: no reader has been observed, so nothing shows the redesign teaches better. |
| [Assessment and checks for understanding](concepts/assessment.md) | :material-circle-half-full: partial | [fieldguide](https://johnallred.github.io/fieldguide/) | `src/fieldguide/audit.py` | 360 proof tasks measured across 120 pages at version 0.2.0, 94 per cent imperative and 39 per cent stating a success criterion. That second figure was published as 17 per cent for months and the classifier was wrong: it matched the preposition in "run it against a corpus you own" and recognised no conditional, predicted value or author comparison, so the guide's self-declared weakest number was about half the real one. It is now scored against sixty tasks hand-labelled before it was written, held in tests/fixtures/criterion_labels.json. The figure reached 40 after a pass that added a criterion to every core page that had none, and stood at 39 as later pages were added; the correction was worth more than the pass. It establishes that the instrument is well formed and nothing about whether anyone learns. Ceiling: no-audience. |
| [Demo design](concepts/demo-design.md) | :material-circle-half-full: partial | [fieldguide](https://johnallred.github.io/fieldguide/) | `drills/demo_check.py` | A demo script and its last rehearsal checked for a buried result, an overrun, author-only paths and variables, and live beats with no fallback: eleven findings, with the two rehearsal failures falling exactly on the two author-only beats, then a revision with none. The demo and rehearsal are invented; no audience reacted to anything. |
| [Developer advocacy](concepts/developer-advocacy.md) | :material-circle-half-full: partial | [fieldguide](https://johnallred.github.io/fieldguide/) | `tests/test_registry.py` | A docs gate at capability granularity, enumerating subcommands from the parser; the partnership half is undemonstrable in a one-person repository. |
| [Field enablement](concepts/field-enablement.md) | :material-circle-half-full: partial | [fieldguide](https://johnallred.github.io/fieldguide/) | `drills/field_enablement.py` | Readiness measured by teach-back rather than attendance (4 of 12 can deliver, partners at zero), field questions ranked into a self-service backlog with one resource to retire, and a product gap reported with counts by role. The roster and questions are invented, and no teach-back has been observed. |
| [LMS administration](concepts/lms-administration.md) | :material-circle-half-full: partial | [fieldguide](https://johnallred.github.io/fieldguide/) | `drills/lms_admin.py` | A drift check between a course's source and an export in the shape the Canvas modules API returns, plus a completion funnel and a per-section start rate. Its largest drop turns out to be an unpublished module, an administrative fault rather than a content one. No live LMS, and the learner data is invented; the page says both. |
| [Learning content standards](concepts/learning-content-standards.md) | :material-circle-half-full: partial | [fieldguide](https://johnallred.github.io/fieldguide/) | `drills/content_standards.py` | A SCORM manifest, xAPI statements and an LTI 1.3 launch checked against rules quoted from each specification: four defects found before upload, none after the fixes. Checked as files only; never run against a real LMS, LRS or LTI platform. |
| [Publishing in public](concepts/publishing-in-public.md) | :material-check-circle: full | [fieldguide](https://johnallred.github.io/fieldguide/) | `scripts/prepublication.py` | Both repositories are public with published sites, and the pre-publication gate exits 0 on both. The defining property, that a stranger can run it, was checked on 2026-11-24 with a clean clone from the public URL: 67 seconds to 244 passing tests here, 13 seconds to 142 in docpack. No stranger's reaction has been observed. |
| [Workshops and hands-on labs](concepts/workshops.md) | :material-circle-half-full: partial | [fieldguide](https://johnallred.github.io/fieldguide/) | `drills/workshop_arithmetic.py` | The arithmetic that decides what a workshop can cover, computed from the registry rather than quoted: a ten-concept path's hours, the share of it two hands-on hours buys, and how many concepts are short enough for one sitting. It found the page calling a thirty-four-hour path the shortest when a twenty-four-hour one existed. No room, no attendees, and the setup timings on that page remain one unverified run. |
| [Screencasts and video](concepts/screencasts.md) | :material-circle-half-full: partial | [fieldguide](https://johnallred.github.io/fieldguide/) | `drills/screencast_script.py` | A screencast script treated as a testable artifact: a beat that was never true, a clean pass once the tool gains the flag the narration promised, and the same script going stale when upstream rewords one line. Reports drift by timestamp, which is what makes a stale recording actionable. No camera, no voice, no edit. |

### Automation with Python

3 of 3.

| Concept | Extent | Repository | Artifact | What it does |
|---|---|---|---|---|
| [Integrating with APIs](concepts/api-integration.md) | :material-circle-half-full: partial | [docpack](https://johnallred.github.io/docpack/) | `tests/test_mcp_server.py` | A client driven against the MCP server found two defects where failure bypassed the isError flag, now fixed and covered by 14 tests; no networked, authenticated or rate-limited service is involved. |
| [Integrating with APIs](concepts/api-integration.md) | :material-check-circle: full | [fieldguide](https://johnallred.github.io/fieldguide/) | `scripts/github_api.py` | A GitHub REST client used every week by the freshness monitor: bearer-token authentication, pagination by Link header, waiting out or reporting a rate limit, obeying Retry-After, retrying server errors with backoff, ETag caching, and errors carrying GitHub's own message. Its first unauthenticated run met the 60-an-hour limit for real and stopped cleanly; nine tests drive every branch through a scripted transport. |
| [Python for content automation](concepts/python-for-content.md) | :material-check-circle: full | [docpack](https://johnallred.github.io/docpack/) | `src/docpack/` | Seven modules, 134 tests, operating on a documentation tree as data. |
| [Transforming content as data](concepts/content-data-transformation.md) | :material-check-circle: full | [docpack](https://johnallred.github.io/docpack/) | `src/docpack/pack.py` | A Markdown tree to JSONL, llms.txt and llms-full.txt, deterministically, so diffs stay small. Keeps 89, 5 and 99 per cent of source; the seven per cent round-trip gap resolves into relocated headings and blank lines. |

### Domain context

6 of 6.

| Concept | Extent | Repository | Artifact | What it does |
|---|---|---|---|---|
| [GPU computing and CUDA](concepts/gpu-computing.md) | :material-circle-half-full: partial | [fieldguide](https://johnallred.github.io/fieldguide/) | `drills/arithmetic_intensity.py` | Arithmetic intensity measured on a CPU, where the elementwise operations sit at the memory ceiling and a matmul reaches a hundred times the compute. The ratio argument transfers to a GPU and none of the numbers do; there is no GPU, CUDA, kernel or profiler here. |
| [Inference serving and microservices](concepts/inference-serving.md) | :material-circle-half-full: partial | [fieldguide](https://johnallred.github.io/fieldguide/) | `drills/inference_sweep.py` | A latency-throughput sweep on ONNX Runtime including queue wait, showing 14x throughput for 21x latency and a saturation knee past which batching is pure loss. CPU only, no server, no real traffic. |
| [OpenUSD and Omniverse](concepts/usd-omniverse.md) | :material-circle-half-full: partial | [fieldguide](https://johnallred.github.io/fieldguide/) | `drills/usd_composition.py` | Real USD composition with usd-core: an override leaving its base file untouched, the resolution order printed from the API, and the first-sublayer-wins ordering most newcomers get backwards. No Omniverse, Kit or production pipeline. |
| [Reading an AI software stack](concepts/ai-stack.md) | :material-circle-half-full: partial | [fieldguide](https://johnallred.github.io/fieldguide/) | `drills/onnx_compat.py` | The newest onnx writes IR 14 and the newest onnxruntime refuses it; four outcomes from one Relu across two version axes. The accelerator layers are read about, not run. |
| [Real-time and graphics systems](concepts/realtime-systems.md) | :material-circle-half-full: partial | [fieldguide](https://johnallred.github.io/fieldguide/) | `drills/deadline_sweep.py` | A deadline sweep where the median improves while a quarter of deadlines are missed, plus a variance measurement showing the miss count ranges 67 to 205 of 250 across runs. The statistics, not the systems work: no real-time kernel and no graphics pipeline. |
| [Robotics simulation, Isaac Sim and ROS](concepts/robotics-sim.md) | :material-circle-half-full: partial | [fieldguide](https://johnallred.github.io/fieldguide/) | `drills/frames.py` | REP 105's two frame guarantees simulated, showing odom drifting smoothly while map jumps 120 mm and invents 1.2 m/s of velocity. Not ROS, no simulator, no robot. |

### Ways of working

3 of 14.

| Concept | Extent | Repository | Artifact | What it does |
|---|---|---|---|---|
| [Release readiness for documentation](concepts/release-readiness.md) | :material-circle-half-full: partial | [fieldguide](https://johnallred.github.io/fieldguide/) | `src/fieldguide/release.py` | The gate exists, blocks, runs in CI and carries --report-only for the run-it-before-you-enforce-it advice. What it cannot demonstrate is the political half: the only author here is also the only reviewer, so no one else ever accepted the constraint, and the page says so rather than implying otherwise. |
| [Multi-platform parity](concepts/multi-platform-parity.md) | :material-circle-half-full: partial | [fieldguide](https://johnallred.github.io/fieldguide/) | `drills/parity_check.py` | A single-sourced page checked against a capability matrix and per-platform sample runs: four platform differences the page was silent on and two sample claims nobody had verified, then a measurement showing one platform's reader sees more platform-specific text than shared text, the point at which to split. Platforms and runs are invented; nothing calls a real cloud. |
| [Release notes and changelogs](concepts/release-notes.md) | :material-check-circle: full | [fieldguide](https://johnallred.github.io/fieldguide/) | `CHANGELOG.md` | A real changelog for this guide in Keep a Changelog form, held in CI by tests/test_changelog.py: only the six standard headings, ISO dates, versions descending with the newest equal to the package version, and every concept added since 0.1.0 named under Added. The coverage rule checks concepts rather than commits, because the guide's commits are not Conventional Commits; drills/release_notes.py still runs the page's commit-based check on invented commits. |

## What is not demonstrated

Coverage by category, including the categories at zero.

| Category | Demonstrated | Core concepts with nothing behind them |
|---|---|---|
| Information and knowledge architecture | 12/14 | 0 |
| Docs-as-code toolchain | 8/15 | 0 |
| Quality automation and documentation CI | 16/17 | 0 |
| Golden paths and developer onboarding | 9/9 | 0 |
| AI-ready content and agents | 13/21 | 8 |
| Measurement and feedback | 7/7 | 0 |
| Developer education and curriculum | 14/14 | 0 |
| Automation with Python | 3/3 | 0 |
| Domain context | 6/6 | 0 |
| Ways of working | 3/14 | 7 |

### Why the gaps are there

Every concept with no demonstration carries a recorded reason, and the build
fails on a concept that has neither. So this is a decision register rather
than a list of things nobody got to.

| Reason | Concepts | What it means |
|---|---|---|
| `declined` | 7 | demonstrating it would mean adopting a tool or process this project does not need |
| `needs-organisation` | 13 | the evidence is a process, a conversation or a decision in someone else's repository |
| `blocked` | 9 | needs a model, weights or hardware this environment does not have |

### What is demonstrated as far as it can be

A gap closes when somebody does the work. A ceiling does not, and the
difference is worth publishing: these concepts have a working mechanism and
a stated reason why no amount of further code reaches `full`.

| Reason | Concepts | Why it stops there |
|---|---|---|
| `no-audience` | 11 | the corpus-side half is built and measured; the reader-side half needs readers, and this project has none |
| `single-author` | 1 | the mechanism runs and gates; the half that needs another person to review or accept it cannot happen in a one-person project |

**`no-audience`:** [Assessment and checks for understanding](concepts/assessment.md), [Cognitive load in technical content](concepts/cognitive-load.md), [Demo design](concepts/demo-design.md), [Turning developer feedback into changes](concepts/developer-feedback-loops.md), [Documentation analytics](concepts/docs-analytics.md), [Instructional design for developers](concepts/instructional-design.md), [Learning paths and curriculum](concepts/learning-paths.md), [Learning science for developer education](concepts/learning-science.md), [Reproducible environments](concepts/reproducible-environments.md), [Sample applications and galleries](concepts/sample-apps.md), [Time to first success](concepts/time-to-first-success.md)

**`single-author`:** [Release readiness for documentation](concepts/release-readiness.md)

A guide that published only the first table would be the flattering half of
the truth. The gaps are where the judgement lives.

### Every core concept with no demonstration (15)

| Concept | Category | Reason |
|---|---|---|
| [Agent skills and context kits](concepts/agent-skills.md) | AI-ready content and agents | `blocked` |
| [Agentic workflows](concepts/agentic-workflows.md) | AI-ready content and agents | `blocked` |
| [Documentation for coding agents](concepts/coding-agents.md) | AI-ready content and agents | `blocked` |
| [Documentation-backed AI assistants](concepts/ai-assistants.md) | AI-ready content and agents | `blocked` |
| [Embeddings](concepts/embeddings.md) | AI-ready content and agents | `blocked` |
| [LLMs in the content lifecycle](concepts/llm-content-lifecycle.md) | AI-ready content and agents | `blocked` |
| [Output evaluation](concepts/output-evaluation.md) | AI-ready content and agents | `blocked` |
| [Prompting for content work](concepts/prompting.md) | AI-ready content and agents | `blocked` |
| [A systems mindset](concepts/systems-mindset.md) | Ways of working | `needs-organisation` |
| [Extracting tribal knowledge](concepts/sme-interviews.md) | Ways of working | `needs-organisation` |
| [Giving architecture owners implementation feedback](concepts/implementation-feedback.md) | Ways of working | `needs-organisation` |
| [Judging where AI can be trusted](concepts/ai-trust-judgment.md) | Ways of working | `blocked` |
| [Reading code to verify accuracy](concepts/reading-code-to-verify.md) | Ways of working | `needs-organisation` |
| [Technical writing as a craft](concepts/technical-writing.md) | Ways of working | `needs-organisation` |
| [Treating docs, setup and samples as one product](concepts/docs-as-product.md) | Ways of working | `needs-organisation` |
