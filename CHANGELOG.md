# Changelog

What changed in each version of this guide, for someone deciding whether a
page they read before still says the same thing. The format is
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html), read for a
curriculum: a new concept or path is a minor version, and a removed or renamed
concept, which breaks links into the guide, would be a major one.

`tests/test_changelog.py` holds this file to the rules the
[release notes](docs/concepts/release-notes.md) page teaches: Keep a Changelog
headings only, ISO 8601 dates, versions in descending order, the newest one
equal to the package version, and every concept added since 0.1.0 named under
an `Added` heading.

## [Unreleased]

### Added

- A weekly freshness monitor (`scripts/freshness.py`) comparing each
  demonstration note with the file it describes, keeping one GitHub issue
  current, and the GitHub API client it uses (`scripts/github_api.py`).
- An optional `reviewed:` date on demonstration entries.
- An accessibility gate over every page of the built site (`scripts/a11y_check.py`).
- How this guide ships: the pipeline as a diagram, generated from the workflow
  file by `fieldguide build`.
- Two learning paths: Reference and releases, and Found by search and answer
  engines.
- A "Not on any path" section on the paths index, listing the concepts that
  are deliberately on no path and when to read them anyway.
- A Docusaurus build drill (`drills/docusaurus_build.py`), measuring
  Docusaurus 3.10.2 against MkDocs 1.6.1 on the same Markdown, cold and warm.

### Changed

- Freshness monitoring, API integration, accessibility, diagrams as code, the
  style guide and single-sourcing are recorded as fully demonstrated, the last
  two by `docpack`.
- The lab publishing and learner sandbox guardrails pages describe what
  `coldlab` now does: versioned promotion to learners on evidence, and a
  learner role tested against what a learner must and must never be able to do.

- Every concept is now on a learning path except MDX, Docusaurus and Antora.
  Twenty-two were on none, four of them core (Sphinx, prompting, LLM content
  lifecycle, GEO), and nineteen of those are now placed. The documentation engineer path is 18 steps and KnowledgeOps
  18, after the reference and discoverability concepts became their own paths.
- Each learning path marks the steps it shares with other paths and names
  them, and says up front how many steps and hours are shared, so a reader on
  a second path can skip what they have done.
- The Docusaurus page replaces its one unverified build time with that
  measurement, and says why MkDocs slows faster than linearly.

### Fixed

- 11,102 empty, focusable links, one on every line of every code sample, put
  there by the `anchor_linenums` highlighting setting.
- Seven demonstration notes the monitor found stale on its first run, including
  two that still described 106 concepts and one that counted seven paths.

## [0.2.0] - 2026-11-24

### Added

- Fourteen concepts:
- [Learning science for developer education](docs/concepts/learning-science.md)
- [Learner and task analysis](docs/concepts/learner-task-analysis.md)
- [LMS administration](docs/concepts/lms-administration.md)
- [Learning content standards](docs/concepts/learning-content-standards.md)
- [Diagrams as code](docs/concepts/diagrams-as-code.md)
- [Release notes and changelogs](docs/concepts/release-notes.md)
- [Content migration](docs/concepts/content-migration.md)
- [Multi-platform parity](docs/concepts/multi-platform-parity.md)
- [Demo design](docs/concepts/demo-design.md)
- [Field enablement](docs/concepts/field-enablement.md)
- [Ephemeral lab environments](docs/concepts/ephemeral-environments.md)
- [Lab publishing pipelines](docs/concepts/lab-publishing.md)
- [Labs for isolated regions](docs/concepts/isolated-region-labs.md)
- [Learner sandbox guardrails](docs/concepts/learner-sandbox-guardrails.md)
- The lab engineer learning path: building, testing, publishing and securing
  hands-on labs that run in real cloud accounts.
- `llms.txt`, generated from the registry on every build, as a front door for
  language models.
- A crawl audit of this guide's own site (`scripts/crawl_site.py`), as a gate
  on every build and against the live site after each deploy.
- `coldlab` as a third demonstrating project on the demonstrated page.
- This changelog.

### Changed

- Every concept page is written as a training manual for people doing the work:
  each says how the concept applies to your role and how to put it into
  practice, and each names the day-to-day work that needs it.
- Learning paths are grouped as where to start, by role, once the work is real,
  and background. The developer educator path, at 25 steps, was split, and its
  lab concepts became the lab engineer path.
- The demonstrated page lists every entry with the repository that holds it,
  rather than one entry per concept.
- Publishing in public and crawlability are recorded as fully demonstrated, now
  that both repositories and their sites are public.
- GitHub Actions moved to versions that run on Node 24.

### Removed

- Quotations left beneath seven concept headings by the earlier page format.

### Fixed

- "Leads to" lines on 31 pages that disagreed with the registry; a test now
  keeps both header lines in step with it.
- The site menu listed two learning paths in a different order from the index,
  and one under a different name.
- Pages deploys that intermittently found no site to publish, by deploying
  from a separate job.

## [0.1.0] - 2026-11-20

### Added

- 106 concepts across ten categories, each page holding the same seven
  sections and a golden path with commands and their output.
- Nine learning paths, coverage and a study plan generated from `concepts.yaml`.
- The demonstrated page, recording which concepts `docpack` and this guide
  implement, how far, and which they cannot.

[Unreleased]: https://github.com/johnallred/fieldguide/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/johnallred/fieldguide/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/johnallred/fieldguide/releases/tag/v0.1.0
