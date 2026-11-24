---
title: Release notes and changelogs
summary: Writing the record of what changed for the people who have to act on it, and checking it against the commits so nothing user-facing is missing and nothing internal leaks in.
diataxis: explanation
audience: developer
concept: release-notes
tags: [craft, supporting]
---

# Release notes and changelogs

`supporting` · difficulty 2 · 3h

> Writing what changed in each release for the people who have to act on it, and making sure the version number tells them how much.

**Prerequisites:** [Technical writing as a craft](technical-writing.md), [Release readiness for documentation](release-readiness.md)

## What it is

A **changelog** is the running record of notable changes, version by version,
kept in the repository. **Release notes** are the same information for one
release, written for the people upgrading: what is new, what changed, what
broke, and what to do about it.

Both are documentation with an unusually exact reader. Someone is about to
upgrade and wants to know one thing: will it break, and if so, what do they
change? Everything in a good entry serves that question.

## How this applies to your role

This matters because release notes are the page most likely to be read at the exact moment
a mistake is expensive, and the page most often generated from a commit log
and shipped unread.

On a Tuesday it looks like this. A release goes out as a minor version. Its
notes say "the retry argument is now `max_attempts`". A team upgrades because a
minor version should be safe, their nightly job starts failing, and the reason
is two facts nobody wrote down: the old argument was removed, not deprecated,
and the new one counts attempts rather than retries, so every value is off by
one. The commit that made the change was correctly marked as breaking. The
version number and the notes both lost that.

Release notes sit where [release readiness](release-readiness.md) and
[technical writing](technical-writing.md) meet. Generating a draft from
commits is automation, and worth doing. Deciding what a reader needs to know,
and checking the draft against the commits so nothing is lost on the way, is
the part that takes judgement and the part this page is about.

## The golden path

Group a commit log the way a generator would, write a draft that makes six
common mistakes, check it against the commits, and revise it until the check
is clean. About twenty-five minutes.

The check is committed as `drills/release_notes.py`, which holds all three
files below and a test that keeps them identical to this page. The commits are
invented for the exercise.

**Step 1: the commits since the last release**

```bash
mkdir -p notes-drill && cd notes-drill
cat > commits.txt <<'DATA'
# since 2.5.3
feat!: rename retries to max_attempts (#412)
feat(cli): add --dry-run to sync (#415)
fix: include the HTTP status in RetryExhausted (#418)
fix(auth): refresh tokens before expiry (#420)
refactor: extract backoff calculation (#421)
ci: cache pip downloads (#423)
docs: fix typo in quickstart (#424)
chore: bump requests to 2.32.3 (#425)
DATA
curl -sO https://raw.githubusercontent.com/johnallred/fieldguide/main/drills/release_notes.py
```

**Step 2: what a generator would publish**

```bash
python3 release_notes.py --raw commits.txt
```

```
feat
  rename retries to max_attempts (#412)
  add --dry-run to sync (#415)
fix
  include the HTTP status in RetryExhausted (#418)
  refresh tokens before expiry (#420)
refactor
  extract backoff calculation (#421)
ci
  cache pip downloads (#423)
docs
  fix typo in quickstart (#424)
chore
  bump requests to 2.32.3 (#425)
```

Eight entries, four of them about the build, a typo and a dependency. That is
what a changelog generated straight from commits looks like: accurate, and
written for whoever made the change rather than whoever has to upgrade.

**Step 3: a draft, checked against the commits**

```bash
cat > notes.md <<'DATA'
## [2.6.0] - 11/20/2026

### Improvements
- The retry argument is now `max_attempts`. (#412)
- `sync --dry-run` shows what would change. (#415)

### Fixed
- Tokens are refreshed before they expire. (#420)
- Extracted the backoff calculation into its own module. (#421)
DATA
python3 release_notes.py commits.txt notes.md
```

```
VERSION  2.5.3 -> 2.6.0 is a minor bump; the commits need major
DATE     11/20/2026 is not ISO 8601 (YYYY-MM-DD)
HEADING  'Improvements' is not a Keep a Changelog category
BREAKING #412 says what changed but not how to upgrade
MISSING  #418 (fix: include the HTTP status in RetryExhausted) is not in the notes
INTERNAL #421 (refactor) is in the notes
6 finding(s)
```

Six findings, and the first one is the expensive one. A breaking change shipped
as a minor version is a promise of safety the release does not keep. The draft
also mentions the breaking change without saying how to upgrade, drops a fix
readers will care about, includes a refactor nobody upgrading cares about, uses
a heading that is not a standard category, and writes the date in a format
that means different things in different countries.

**Step 4: revise and check again**

```bash
cat > notes.md <<'DATA'
## [3.0.0] - 2026-11-20

### Changed
- **Breaking:** `retries` is now `max_attempts`, and it counts attempts, not retries. To upgrade: rename the argument and add one, so `retries=3` becomes `max_attempts=4`. (#412)

### Added
- `sync --dry-run` shows what a sync would change without changing it. (#415)

### Fixed
- `RetryExhausted` now includes the HTTP status, so you can tell a rejection (429) from an outage (503). (#418)
- Tokens are refreshed before they expire, so long syncs no longer fail at the one-hour mark. (#420)
DATA
python3 release_notes.py commits.txt notes.md
```

```
0 finding(s)
```

**What you built.** A release section with the right version for its changes,
every user-facing change in reader terms, a breaking change that says how to
upgrade, and a check that keeps the notes honest about the commits they
summarise.

## Reference

### Keep a Changelog, the categories

| Category | For |
|---|---|
| Added | New features |
| Changed | Changes to existing behaviour |
| Deprecated | Features that will be removed soon |
| Removed | Features removed in this release |
| Fixed | Bug fixes |
| Security | Vulnerabilities |

Its other conventions: an entry for every version, newest first, an
`Unreleased` section at the top that becomes the next release, ISO 8601 dates,
and a statement of whether the project follows Semantic Versioning.

### From commits to a version number

| Commit | Conventional Commits meaning | Semantic Versioning bump |
|---|---|---|
| `fix:` | Patches a bug | Patch |
| `feat:` | Adds a feature | Minor |
| `feat!:` or a `BREAKING CHANGE:` footer | An incompatible change | Major |
| Anything during `0.y.z` | Initial development | Anything may change |

### What makes an entry useful

| Instead of | Write | Because |
|---|---|---|
| "Refactored retry handling" | Nothing, if readers cannot see the change | Internal work is noise to someone upgrading |
| "Renamed retries" | What to change, with the before and after values | The reader needs an action, not a fact |
| "Various bug fixes" | Each fix, in terms of the symptom it removes | Readers search notes for the error they saw |
| "Improved performance" | What got faster, by how much, for whom | Unmeasured claims are not checkable |
| A list of pull request titles | Entries grouped by what the reader must do | The reader is deciding whether to upgrade |

### Generated notes, and where they stop

GitHub can generate release notes when a release is drafted: a list of merged
pull requests, the contributors, and a link to the full changelog. A
`.github/release.yml` file groups pull requests into categories by label, with
`*` as a catch-all, and excludes labels or authors. That is a good first draft
and a poor final one: it groups by label, not by what the reader must do, and
it uses pull request titles written for reviewers.

### Sources

Opened and checked on 2026-11-23:
[Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/),
[Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/),
[Semantic Versioning 2.0.0](https://semver.org/),
[GitHub: automatically generated release notes](https://docs.github.com/en/repositories/releasing-projects-on-github/automatically-generated-release-notes).

## Explaining it to your team

**How to explain it.** Lead with the reader's question. "Someone upgrading
wants to know whether this release breaks them and what to change if it does.
The version number answers the first half and the notes answer the second, so
both are checked against the commits before release: a breaking commit means a
major version and an upgrade instruction, every time."

**The follow-up is usually "why not just generate them".** Generate the draft,
and keep the check. A generator gets the facts right and the audience wrong:
it cannot tell a refactor from a feature by how a reader experiences it, and
it cannot write the upgrade instruction. The check makes sure editing a draft
never loses a fact the commits recorded.

**The tradeoff to name.** The check only knows what the commits say, so it
depends on commit discipline: a breaking change committed as `fix:` passes
every rule here and still breaks users. Conventional Commits only help if
review enforces them, which is a cost the engineering team carries, not the
documentation team.

**One sharper point.** The version number is the most widely read line of
documentation in a release. Many people never open the notes; they read
"2.6.0", conclude it is safe, and upgrade. Getting the bump wrong is a
documentation defect with a larger audience than any page in the docs.

## Putting it into practice

**The work product.** A changelog in Keep a Changelog form, release notes for
the next release written for the reader, and the drill's check running in CI
on every release branch.

**Three things to do, in order:**

1. Run the golden path, then run the check against the last release of a
   project you maintain. Expect at least one fix that never made the notes.
2. Add an `Unreleased` section to the changelog and require a line in it for
   every user-facing pull request, so the notes are written when the change is.
3. Make the version check block the release, so a breaking commit cannot ship
   under a minor version.

**How to tell it is working.** The drill above runs in this guide's test suite
and its output is the output quoted here. The guide also keeps a real
changelog, [`CHANGELOG.md`](https://github.com/johnallred/fieldguide/blob/main/CHANGELOG.md),
held by `tests/test_changelog.py` to this page's rules: Keep a Changelog
headings only, ISO dates, versions in descending order with the newest equal to
the package version, and an `Unreleased` section first. The coverage rule is
adapted to a curriculum: the guide's commits are not Conventional Commits, so
instead of checking every feature commit, the test checks that every concept
added since 0.1.0 is named under `Added`, which is the change a returning
reader most needs to find. In your own releases, the sign is that upgrade
questions after a release are about edge cases, not about changes the notes
never mentioned.

## Related

- [Release readiness for documentation](release-readiness.md), the gate this check belongs in
- [Technical writing as a craft](technical-writing.md), turning a commit subject into a reader's instruction
- [Versioned documentation](versioning.md), the docs half of a major version
- [Terminology drift](terminology-drift.md), when a renamed argument outlives its old name in the docs
- [Developer feedback loops](developer-feedback-loops.md), where upgrade problems surface after release
