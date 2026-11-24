---
title: Content migration
summary: Moving a corpus from a wiki or CMS into docs-as-code without losing the pages people read, the links that point at them, or the readers who find them through search.
diataxis: explanation
audience: developer
concept: content-migration
tags: [ia, supporting]
---

# Content migration

`supporting` · difficulty 3 · 6h

> Moving a documentation corpus from a wiki or CMS into docs-as-code, deciding page by page what moves, merges or goes, and keeping every old link working.

**Prerequisites:** [Docs-as-code](docs-as-code.md), [Retiring content](content-retirement.md)

## What it is

Moving an existing body of documentation from one system to another, most
often from a wiki or CMS into a [docs-as-code](docs-as-code.md) repository.
It has three parts: an inventory and audit that decide what happens to every
page, a conversion that turns the old format into Markdown, and a redirect map
that keeps every old URL leading somewhere useful.

The conversion is the part people plan for and the easy part. A migration
usually fails on the other two: pages that should have been retired are
copied faithfully, and pages people still read disappear because nobody
mapped their URL.

## How this applies to your role

This matters because a move to docs-as-code is often the first large project in this kind
of work, and it is the one time every page in the corpus gets touched.

On a Tuesday it looks like this. The team has agreed to leave the wiki. Someone
runs a converter over the export on Friday, and on Monday the new site has
four hundred pages. Half are meeting notes, stale drafts and duplicates. The
others are full of leftover markup that renders as stray braces and tags. And
the old wiki is due to be switched off, which will break every bookmark, every
link in a support macro, and every search result readers use to find the docs.

The migration is also the cheapest moment to [retire
content](content-retirement.md). Every page needs a decision anyway, so
deciding "this one goes" costs nothing extra, and the corpus you start
maintaining is smaller than the one you left. A team that migrates
everything inherits every problem the old system had, now under version
control.

## The golden path

Audit a small migration's inventory and converted pages, find a retired page
people still read and the markup the converter left behind, fix both, and
produce the redirect map. About thirty-five minutes.

The audit is committed as `drills/migration_audit.py`, which holds every file
below and a test that keeps them identical to this page. The pages and traffic
are invented. The converted files stand in for what a converter such as
pandoc produces from a wiki export.

**Step 1: the inventory, with a decision for every page**

```bash
mkdir -p migration-drill/docs && cd migration-drill
cat > inventory.csv <<'DATA'
old_url,views_90d,decision,new
/display/DOCS/Getting+Started,1840,migrate,getting-started.md
/display/DOCS/Install+on+Linux,920,merge,getting-started.md
/display/DOCS/Retry+Settings,610,migrate,configure-retries.md
/display/DOCS/Retry+Settings+(old),12,retire,
/display/DOCS/API+Keys,455,retire,
/display/DOCS/Troubleshooting,380,migrate,troubleshooting.md
/display/DOCS/FAQ,700,merge,troubleshooting.md
/display/DOCS/2019+Offsite+Notes,3,retire,
DATA
```

**Step 2: the converted pages**

```bash
cat > docs/getting-started.md <<'DATA'
# Getting started

Install the client with `pip install widget-client`, then run `widget sync`.
DATA
cat > docs/configure-retries.md <<'DATA'
# Configure retries

{info}Retries count retries, not attempts.{info}

Set <span style="color:red">retries</span> on the client.
DATA
cat > docs/troubleshooting.md <<'DATA'
# Troubleshooting

If a request fails with 401, see [[API Keys]] or
[the key page](https://wiki.example.com/display/DOCS/API+Keys).
DATA
curl -sO https://raw.githubusercontent.com/johnallred/fieldguide/main/drills/migration_audit.py
```

**Step 3: audit the migration**

```bash
python3 migration_audit.py inventory.csv docs/
```

```
RETIRED  /display/DOCS/API+Keys (455 views) has no redirect
RESIDUE  configure-retries.md: raw HTML <span style="color:red">
RESIDUE  configure-retries.md: raw HTML </span>
RESIDUE  configure-retries.md: wiki macro {info}
RESIDUE  configure-retries.md: wiki macro {info}
RESIDUE  troubleshooting.md: wiki link [[API Keys]]
RESIDUE  troubleshooting.md: old host link wiki.example.com
7 finding(s); 4450/4920 views (90.4%) land on a new page
```

The first finding is the costly one. The API keys page was marked for
retirement, but 455 people read it last quarter, and switching off the wiki
would leave every one of them at a dead link. The rest is residue: wiki markup
the converter could not translate, which would render on the new site as
literal braces and tags, and two links that still point at a page on a host
that is about to disappear.

**Step 4: fix the decision and the residue**

```bash
cat > inventory.csv <<'DATA'
old_url,views_90d,decision,new
/display/DOCS/Getting+Started,1840,migrate,getting-started.md
/display/DOCS/Install+on+Linux,920,merge,getting-started.md
/display/DOCS/Retry+Settings,610,migrate,configure-retries.md
/display/DOCS/Retry+Settings+(old),12,retire,
/display/DOCS/API+Keys,455,migrate,api-keys.md
/display/DOCS/Troubleshooting,380,migrate,troubleshooting.md
/display/DOCS/FAQ,700,merge,troubleshooting.md
/display/DOCS/2019+Offsite+Notes,3,retire,
DATA
cat > docs/api-keys.md <<'DATA'
# API keys

Create a key in the console, deploy it, then revoke the old one.
DATA
cat > docs/configure-retries.md <<'DATA'
# Configure retries

!!! note
    Retries count retries, not attempts.

Set `retries` on the client.
DATA
cat > docs/troubleshooting.md <<'DATA'
# Troubleshooting

If a request fails with 401, see [API keys](api-keys.md).
DATA
python3 migration_audit.py inventory.csv docs/
```

```
0 finding(s); 4905/4920 views (99.7%) land on a new page
```

The remaining 0.3 per cent is two pages nobody reads: an old version of a page
and some meeting notes. They are retired without a redirect, which is the
right outcome for content with no readers.

**Step 5: the redirect map**

```bash
python3 migration_audit.py --redirects inventory.csv
```

```
/display/DOCS/Getting+Started  ->  /getting-started/
/display/DOCS/Install+on+Linux  ->  /getting-started/
/display/DOCS/Retry+Settings  ->  /configure-retries/
/display/DOCS/API+Keys  ->  /api-keys/
/display/DOCS/Troubleshooting  ->  /troubleshooting/
/display/DOCS/FAQ  ->  /troubleshooting/
```

Every old URL that people use goes straight to its final page, including the
two merged pages, which point at the page that absorbed them rather than at a
home page. Load this into the old host's server-side rules, or into the new
site's redirect plugin, before the wiki is switched off.

**What you built.** An inventory with a decision for every page, a converted
corpus free of the old system's markup, a redirect map covering 99.7 per cent
of last quarter's traffic, and a check that blocks the switch-off until all
three are true.

## Reference

### The three decisions

| Decision | When | What happens to the old URL |
|---|---|---|
| Migrate | The page is read and still true | Redirect to its new page |
| Merge | It overlaps a page that is being kept | Redirect to the page that absorbed it |
| Retire | Nobody reads it, or it is wrong and not worth fixing | Gone, or redirected if people still arrive at it |

The inventory is a list of every page you have; the audit decides what each one
is worth. Do both before converting anything.

### Conversion residue to look for

| Residue | Looks like on the new site | Usual fix |
|---|---|---|
| Raw HTML from styling | Tags, or styling the theme cannot honour | Replace with Markdown or an admonition |
| Wiki macros | Literal `{info}`, `{code}` and friends | Map each macro to the generator's equivalent |
| Wiki links | Literal `[[Page Name]]` | Rewrite to a relative Markdown link |
| Links to the old host | Working until the switch-off, then dead | Rewrite to the new page |
| Attachments and images | Broken images | Copy into the repository and relink |
| Tables from rich editors | Garbled or flattened | Rebuild by hand; converters handle these worst |

Pandoc reads HTML, MediaWiki and Jira or Confluence wiki markup and writes
Markdown, for example `pandoc -f html -t gfm page.html -o page.md`. Its manual
warns that converting from a format richer than its Markdown is expected to
lose something, which is why the residue check exists.

### Redirects

| Rule | Why |
|---|---|
| Map every old URL to its final destination | Chains slow readers down and lose ranking signal |
| Use server-side permanent redirects (301 or 308) where possible | Client-side redirects are the fallback, not the plan |
| Never send many old pages to one unrelated page | A home page is not an answer to "where did this go?" |
| Keep redirects for at least a year, ideally indefinitely | Old links live in bookmarks, tickets and other people's pages |
| Update internal links to the new URLs | Redirects are for outsiders, not for your own pages |

For MkDocs sites without control over the server, the `mkdocs-redirects`
plugin writes a static page at each old path that sends readers to the new
one. That is a client-side redirect, so treat it as the fallback the table
describes.

### Sources

Opened and checked on 2026-11-23:
[Google Search Central: site moves with URL changes](https://developers.google.com/search/docs/crawling-indexing/site-move-with-url-changes),
[pandoc user's guide](https://pandoc.org/MANUAL.html),
[mkdocs-redirects](https://github.com/mkdocs/mkdocs-redirects),
[Nielsen Norman Group: content inventory and auditing](https://www.nngroup.com/articles/content-audits/).

## Explaining it to your team

**How to explain it.** Lead with traffic, not page counts. "We have eight
pages, but what matters is that 4,920 visits a quarter land on them. Every
decision is about where those readers end up. Retire what nobody reads, merge
what overlaps, and give every page people still use a redirect, so switching
off the wiki breaks nobody's bookmark."

**The follow-up is usually "can we just migrate everything and clean up
later".** You can, and later rarely comes. Every page that crosses the
migration unexamined is a page someone now maintains under version control,
with review and CI on every change. Deciding before converting costs one
column in a spreadsheet; deciding afterwards costs a pull request per page.

**The tradeoff to name.** A thorough inventory and audit is slow, and the
pressure to show the new site working pushes against it. For a small corpus,
converting first and auditing in the new repository is fine. The order
matters most when the corpus is large, the old site has outside traffic, or
the switch-off date is fixed.

**One sharper point.** The redirect map is the part of a migration readers
experience, and the part least often reviewed. A converter's mistakes are
visible on the new site and get fixed; a missing redirect is invisible to the
team and fails silently for every reader who arrives from a search result, a
support ticket or someone else's page.

## Putting it into practice

**The work product.** An inventory of a real corpus with traffic and a decision
per page, a residue check run over the converted output, and a redirect map
loaded before the old system goes away.

**Three things to do, in order:**

1. Run the golden path, then export the page list and 90-day traffic for a
   real wiki space. Expect a large share of its pages to have almost no views.
2. Convert three pages with pandoc and run the residue check on them. Write
   down every residue type it finds before converting the rest.
3. Build the redirect map and confirm, after the switch-off, that a sample of
   old URLs from last quarter's analytics still land on the right page.

**How to tell it is working.** The drill above runs in this guide's test suite
and its output is the output quoted here. The corpus is invented and the drill
does not run a converter, so the [demonstrated](../demonstrated.md) page
records the concept as partial. In a real migration, the sign is that
not-found errors from old URLs stay flat after the switch-off.

## Related

- [Retiring content](content-retirement.md), the third decision, in more depth
- [Docs-as-code](docs-as-code.md), where the migrated corpus ends up
- [Link checking](link-checking.md), for the internal links the migration rewrites
- [Crawlability](crawlability.md), the search side of moving URLs
- [Content models](content-model.md), the structure to convert into rather than out of
