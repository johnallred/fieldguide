---
title: Versioned documentation
summary: Publishing a site per release, and the duplication that nobody measures until it is large.
diataxis: how-to
audience: developer
concept: versioning
tags: [dac, supporting]
---

# Versioned documentation

`supporting` · difficulty 2 · 3h

!!! note "Not a quotation (adjacent)"
    Neither posting mentions versioned documentation. It is unavoidable for any
    platform that ships releases, which is both of these, so it is here on the
    grounds that the work requires it.

**Prerequisites:** [Choosing a static site generator](static-site-generators.md)

## What it is

Publishing more than one copy of the documentation, one per release, so a
reader on version 2.3 is not told how 2.4 behaves. In practice: a URL per
version, a switcher in the page, an alias such as `latest` or `stable`, and a
default that the bare domain redirects to.

The mechanism is simple. The consequences, which are what this page is about,
are a per-version duplication cost that is almost always larger than people
expect and a content problem that no tool solves.

## Why the job asks for it

It does not ask, and the banner says so. But both postings describe platforms
that ship releases, and documentation for a platform that ships releases needs
versioning the moment a reader can be on an older one.

The judgment being tested, if it comes up, is when *not* to version. Versioning
multiplies the corpus you maintain, and a team that versions everything from
day one ends up with five copies of a conceptual explanation that was never
version-specific, four of which are now wrong and none of which anybody is
updating.

## The golden path

Deploy two versions, then measure what you just published. About thirty
minutes, and the measurement is the interesting part.

**Step 1: a site and two releases**

````bash
mkdir -p ver-demo/docs && cd ver-demo
pip install --quiet mkdocs mike
git init -q && git config user.email d@e.f && git config user.name dev
printf 'site_name: W\n' > mkdocs.yml
printf '# Widget 2.3\n\nThe retry default is 3.\n' > docs/index.md
git add -A && git commit -qm init

mike deploy 2.3
printf '# Widget 2.4\n\nThe retry default is 5 (changed from 3).\n' > docs/index.md
mike deploy --update-aliases 2.4 latest
mike set-default latest
mike list
````

```
2.4 [latest]
2.3
```

Two versions, with `latest` pointing at 2.4.

**Step 2: look at what was published**

```bash
git ls-tree -r --name-only gh-pages | grep -E "index.html|versions.json|^latest"
```

```
2.3/index.html
2.4/index.html
index.html
latest
versions.json
```

A directory per version, a `versions.json` that feeds the switcher, a root
`index.html` that redirects, and `latest`. Check what `latest` actually is:

```bash
git ls-tree gh-pages latest
```

```
120000 blob 7208c218...	latest
```

Mode `120000` is a **symlink**. Aliases cost nothing, which is worth knowing
before someone proposes avoiding them to save space.

**Step 3: measure the duplication**

```bash
git ls-tree -r -l gh-pages | python3 -c "
import sys, collections
tot = collections.Counter(); files = collections.Counter()
for line in sys.stdin:
    p = line.split(maxsplit=4)
    if len(p) < 5 or not p[3].isdigit(): continue
    top = p[4].strip().split('/')[0] if '/' in p[4] else '(root)'
    tot[top] += int(p[3]); files[top] += 1
for k in sorted(tot):
    print(f'  {k:10} {files[k]:4} files  {tot[k]:>9} bytes')
"
```

```
  (root)        4 files       538 bytes
  2.3          31 files   1993207 bytes
  2.4          31 files   1993258 bytes
```

Two megabytes per version for a **one-page site**. Split it by kind:

```
  HTML content:       11591 bytes (0%)
  theme assets:     1981667 bytes (99%)
```

Ninety-nine per cent of each version is the theme: webfonts, CSS, JavaScript,
the search index runtime. The content is eleven kilobytes.

So versioning does not duplicate your documentation. **It duplicates your
theme.** Ten versions is twenty megabytes, of which nineteen point eight is the
same webfonts ten times over.

**Step 4: decide what that means**

For most projects: nothing. Twenty megabytes of static files is free, and the
sentence above is not an argument against versioning.

It matters in three places. Clone times for the publishing branch grow
linearly, and `gh-pages` with fifty versions becomes genuinely slow to fetch.
Deployment time grows with it. And a CDN caching per version sees no reuse
across versions, because the asset URLs differ by directory.

The mitigation, if you need one, is to prune old versions on a published policy
rather than to avoid aliases or to hand-manage assets:

```bash
mike delete 2.1 2.2
```

**What you built.** Two versions, a switcher, and the knowledge that the
per-version cost is your theme rather than your prose.

## Reference

### Tooling by generator

| Generator | Mechanism |
|---|---|
| MkDocs | `mike`, deploys a directory per version to `gh-pages` |
| Sphinx | Build per tag or branch, assembled by convention or `sphinx-multiversion` |
| Docusaurus | Built in: `npm run docusaurus docs:version 2.4` snapshots into the repository |
| Antora | Versions *are* branches; its model is version-first |

Docusaurus and Antora make this ordinary. The other two bolt it on, and the
difference shows up in whether a version is a directory in your source tree or
a build artifact.

### What to version and what not to

| Version it | Keep one copy |
|---|---|
| API reference | Conceptual explanation |
| Configuration options and defaults | Architectural overviews |
| Install and upgrade instructions | Contribution guides |
| Anything stating a default or a signature | Glossary and style guide |
| Tutorials that run real commands | Marketing and landing pages |

This table is the whole judgment. Versioning a page that was never
version-specific creates N copies that drift, and the drifted copies are worse
than no versioning at all because they carry a version number that implies
someone checked.

### Decisions to make once, and write down

| Decision | Common answer |
|---|---|
| What the bare domain shows | The latest stable release |
| Alias names | `latest` for newest, `stable` if they differ |
| Whether to publish pre-release docs | Yes, unlisted, behind an explicit URL |
| How long old versions live | Supported releases plus one |
| Whether old versions get fixes | Security and factual corrections only |
| Whether old versions are indexed | No; canonical to `latest` |

That last row is the one that gets missed and the one with the most visible
consequence. Without canonical tags pointing at the current version, search
engines index all of them and readers arrive on 2.1 through a search result. It
is the same mechanism as the [preview indexing](preview-deployments.md) problem
and the same two-line fix.

### The banner nobody adds

A reader who lands on an old version from a search result has no idea they have
done so. A version banner on every non-latest page, saying which version this
is and linking to the current one, costs a template change and prevents the
single most common versioned-docs support ticket.

## How to talk about it

**Lead with what to version rather than how.** "The mechanism is a directory
per release and a switcher, and every generator has it. The decision that
matters is what gets versioned: reference, defaults and install instructions
yes; conceptual explanation no, because five copies of an architecture overview
means four stale ones carrying a version number that implies somebody checked."

**The follow-up is often about cost**, and the measured answer is more
interesting than the guess. The duplication is almost entirely the theme, not
the content: I measured 99 per cent of each version as webfonts, CSS and
JavaScript, with eleven kilobytes of HTML. It matters for clone and deploy
times rather than for storage.

**The tradeoff to volunteer.** Versioning multiplies the maintenance surface
and gives you no mechanism for keeping the copies consistent. A fix to a
tutorial that applies to three supported versions is three pull requests, and
in practice it is one, applied to `latest`, with the other two quietly left
wrong. Anyone who says versioning is cheap has not maintained a correction
across four branches.

**One sharper point.** Old versions are indexable by default and will outrank
your current page for some queries, because they have had longer to accumulate
links. Canonical tags to the current version plus a banner on non-latest pages
is the fix, and almost nobody does either until a support ticket arrives.

## How to prove it

**The artifact.** A versioned site with aliases, a documented retirement
policy, canonical tags on old versions and a version banner.

**Three things to do, in order:**

1. Run the golden path and the measurement in step 3. The 99 per cent figure is
   the thing to quote.
2. On any versioned docs site you can reach, check whether old versions carry a
   canonical tag or a banner. Usually neither.
3. Write the two-column table above for a product you know. The disagreements
   about which column a page belongs in are the valuable part.

**What makes it credible rather than decorative.** Neither of this guide's
repositories is versioned, which the [demonstrated](../demonstrated.md) page
records, and for a single-version project versioning would be theatre. What
travels is the measurement and the judgment table: knowing that the cost is
theme duplication and that the hard part is deciding what not to version.

## Related

- [Choosing a static site generator](static-site-generators.md), which decides the mechanism
- [Content retirement](content-retirement.md), what to do with versions you stop supporting
- [Crawlability](crawlability.md), why old versions need canonical tags
- [Single-sourcing](single-sourcing.md), the alternative to copying a page per version
