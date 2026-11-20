# Concepts the newer postings ask for that the registry does not cover

Status: ready-for-human

Two postings read on 2026-11-19: a Lab Development Engineer role on a cloud
training team, and a platform enablement role for an LLM developer platform.
Both overlap the existing 106 heavily. Five things they ask for have no owner
in the registry.

## Method

Each candidate was checked against its nearest existing concept rather than
against the category names, then confirmed with a word-boundary search of
`docs/concepts/`. Two earlier searches gave false readings and were redone:
`intel` matches inside "intelligence", and `LMS` matches inside "overwhelms".

## The gaps

| # | Concept | Nearest existing | Why that one does not cover it |
|---|---|---|---|
| 01 | Ephemeral environment provisioning | `reproducible-environments` | That is isolation levels and pinning for testing docs. Nothing covers per-learner cloud infrastructure, teardown, or cost per run. `per-student`, `sandbox account`: 0 pages |
| 02 | Field enablement and coaching | `workshops`, `working-with-engineers` | Those design the session and the engineer relationship. Nothing covers teaching the people who deliver, or go-to-market partners. `enablement`, `seller`, `office hours`: 0 pages |
| 03 | Demo design | `sample-apps` | A gallery is clonable promises. A demo is performed, time-boxed, persona-targeted. No concept owns it |
| 04 | LMS administration and reporting | none | `\bLMS\b`: 0 pages. Canvas, Moodle, Blackboard: 0 pages |
| 05 | Multi-platform parity | `partner-documentation` | That is three audiences with different access. This is one product reached through a first-party API and several clouds, where auth, limits and behaviour differ |

## Explicitly not gaps

Checked and already owned, so do not add:

- Content ready on launch day: `release-readiness`
- Content-freshness automation: `freshness-monitoring`
- Track usage and retire: `docs-analytics` + `content-retirement`
- Tool use, MCP, agent skills: `mcp`, `agent-skills`, `agentic-workflows`
- AI coding tools in daily work: `coding-agents`
- Speaking and portfolio: `developer-advocacy`, `publishing-in-public`
- Lab flakiness: half-covered already in five pages including
  `coldstart-testing` and `reproducible-environments`. Fold flake-rate-as-signal
  into 01 rather than making it its own concept.

## Cost per concept

Not a registry edit. Each needs a `concepts.yaml` entry with the posting line
behind it, a page meeting the seven-section contract at 450+ words,
prerequisites that do not create a cycle, a slot in at least one path, a
`demonstrations.yaml` row, and the README's concept counts updated.

## Sequencing

01 waits on `coldlab`, which is its demonstration. Writing the concept before
the artifact exists would put an aspirational row in `demonstrations.yaml`,
which is the thing that page exists to prevent. 02 and 03 can be written now.
04 and 05 should land as `planned` until something demonstrates them.
