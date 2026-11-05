---
title: MkDocs and Material
summary: The fastest route to a good documentation site, and the three checks you have to add yourself.
diataxis: how-to
audience: developer
concept: mkdocs
tags: [dac, core]
---

# MkDocs and Material

`core` · difficulty 2 · 4h

!!! quote "Asked for by name"
    NVIDIA: "static site generators (Sphinx, MkDocs, Docusaurus, or similar)"

**Prerequisites:** [Choosing a static site generator](static-site-generators.md)

## What it is

A Python static site generator that turns a directory of Markdown into a site,
plus **Material for MkDocs**, a theme so dominant that in practice "MkDocs"
usually means both. Material supplies navigation, search, admonitions, tabs,
code annotations and the visual design most people recognise as a modern docs
site.

It is the easiest of the generators to adopt and the one whose build checks the
least. Both halves of that sentence matter, and this page is mostly about the
second.

## Why the job asks for it

NVIDIA names it in a list of three. It is the most likely generator to appear
on a newer documentation project, because a usable site is about fifteen
minutes of work and the theme makes it look deliberate without a designer.

What distinguishes someone who has operated it from someone who has installed
it is knowing what its build does not verify. MkDocs will happily publish a
dead heading anchor and an unreachable page in its strictest mode, which is
measured below, so an MkDocs corpus of any size needs gates that an equivalent
Sphinx project would get for free.

## The golden path

Build a site, turn on the useful configuration, then find out what the build
still misses and what the theme costs. About thirty minutes.

**Step 1: a site**

````bash
mkdir -p mk-demo && cd mk-demo
python3 -m venv .venv && source .venv/bin/activate
pip install --quiet mkdocs mkdocs-material
mkdocs new .
mkdocs build --strict && ls site/
````

**Step 2: the configuration worth having on day one**

```yaml
# mkdocs.yml
site_name: Widget
site_url: https://example.github.io/widget/
theme:
  name: material
  features:
    - navigation.instant
    - navigation.tracking
    - content.code.copy
    - search.suggest

markdown_extensions:
  - admonition
  - attr_list
  - def_list
  - footnotes
  - tables
  - toc: {permalink: true}
  - pymdownx.highlight
  - pymdownx.superfences
  - pymdownx.details
  - pymdownx.tabbed: {alternate_style: true}

# Pages not in the nav are deliberate, not forgotten.
not_in_nav: |
  concepts/*.md
```

Set `site_url` from the start. It is what produces the canonical tag and the
sitemap, and adding it later means a reshuffle of both.

**Step 3: find the three things the build will not tell you**

````bash
cat > docs/index.md <<'EOF'
# Widget

See [the tuning bit](guide.md#tuning).
EOF
printf '# Guide\n\n## Setup\n\nContent.\n' > docs/guide.md
printf '# Orphan\n\nNobody links here.\n' > docs/orphan.md

mkdocs build --strict
echo "exit=$?"
````

```
exit=0
```

Two defects, strictest mode, exit 0. The anchor `#tuning` does not exist in
`guide.md`, and `orphan.md` is reachable from nowhere. The same content fails a
Sphinx build with `-W` on both counts.

The third gap is the one from [Markdown dialects](markdown.md): syntax outside
your extension list ships as literal characters.

So an MkDocs project needs three gates that are not optional:

| Gap | Gate |
|---|---|
| Dead heading anchors | [Link checking](link-checking.md) with anchor resolution |
| Unreachable pages | An orphan check against the nav plus `not_in_nav` |
| Unsupported syntax | A source-versus-HTML [dialect check](markdown.md) |

**Step 4: measure what the theme costs**

Same generator, same 121 pages, two configurations:

```
default theme, no extensions    0.6 s
Material theme, 12 extensions  16.0 s
```

Twenty-seven times slower. MkDocs has no incremental build, so every change
pays the full cost. At 121 pages that is sixteen seconds and tolerable; at a
thousand it is the reason your contributors stop running the build locally.

`mkdocs serve` mitigates it for authoring, because it rebuilds on change and
reloads, but CI pays full price every time.

**Step 5: the extension point people miss**

MkDocs hooks are plain Python functions in your repository, with no plugin
packaging:

```python
# hooks/seo.py
def on_page_context(context, page, config, nav):
    summary = page.meta.get("summary")
    if summary and not page.meta.get("description"):
        page.meta["description"] = summary
    return context
```

```yaml
hooks:
  - hooks/seo.py
```

That nine-line hook fixes a real defect: Material falls back to `site_description`
for the meta description unless a page sets `description` explicitly, so
per-page summaries in your front matter do nothing for
[search](seo-for-docs.md) until something maps them across. Hooks are the right
tool for anything site-specific; reach for a published plugin only when the
need is general.

**What you built.** A good-looking site in fifteen minutes, a list of exactly
three gates you now owe, and a measured reason to care about your theme.

## Reference

### What the build checks

| Defect | `mkdocs build --strict` |
|---|---|
| Link to a missing page | Fails |
| Link to a missing heading anchor | Logs `INFO`, publishes it |
| Page in no navigation | Passes |
| Unsupported Markdown construct | Passes, ships literal characters |
| Malformed YAML front matter | Fails |
| Missing nav target | Fails |

### Configuration that earns its place

| Setting | Why |
|---|---|
| `site_url` | Canonical tag and sitemap; painful to add later |
| `not_in_nav` | Makes deliberate omissions explicit instead of silent |
| `toc: {permalink: true}` | Gives readers linkable headings, which is what deep links need |
| `pymdownx.superfences` | Nested fences, which plain fences cannot express |
| `strict: true` in the config | So a local build matches CI without remembering the flag |
| `validation:` | Newer MkDocs can promote some `INFO` messages; check your version |

### Plugins worth knowing

| Plugin | Does |
|---|---|
| `mkdocstrings` | API reference from Python docstrings |
| `mike` | [Versioned](versioning.md) deployments |
| `mkdocs-redirects` | URL stability when pages move |
| `mkdocs-minify-plugin` | Smaller output |
| `mkdocs-git-revision-date-localized` | Page dates from Git, with the caveats on [freshness](freshness-monitoring.md) |

### Hooks versus plugins

| Use a hook | Use a plugin |
|---|---|
| The need is specific to this site | The need is general |
| It is under about a hundred lines | It has its own configuration surface |
| You want it reviewed with the docs | You want to publish it |

Hooks live in the repository and need no packaging, which makes them the right
default for one-off fixes. The whole mechanism is one `hooks:` key.

## How to talk about it

**Lead with the trade, not the features.** "MkDocs with Material is the fastest
way to a site people want to read, and its build checks less than Sphinx's. In
strict mode it still publishes dead heading anchors and unreachable pages, so
I add an anchor-resolving link checker, an orphan check and a dialect check. Three
gates, and then the easy adoption is a free win."

**The follow-up is often about scale.** Be specific: there is no incremental
build, and the theme dominates build time. Twenty-seven times on the same 121
pages in my own measurement, bare theme against Material plus a dozen
extensions. That is the number that decides whether contributors build locally.

**The tradeoff to volunteer.** Material's extensions are excellent and they
lock your content to it. Admonitions, content tabs and code annotations are all
Material-specific syntax, so a corpus that uses them heavily cannot move to
another generator without a rewrite. That is usually an acceptable bet, and it
should be a conscious one.

**One sharper point.** The hooks mechanism is underused. Most teams reach for a
plugin or live with the gap, when a nine-line function in the repository
solves it and gets reviewed alongside the content. The `description`
fallback above is a good example: a real SEO defect, fixed in nine lines,
with no dependency added.

## How to prove it

**The artifact.** An MkDocs site with the three compensating gates in CI, and
ideally one hook you wrote.

**Three things to do, in order:**

1. Run the golden path. Step 3 is the one that matters: exit 0 on two real
   defects.
2. Check whether your own site sets `site_url` and `not_in_nav`. Both are
   usually missing, and both are one line.
3. Time your build with and without your theme. Put the ratio in the README so
   the next person understands where the minutes go.

**What makes it credible rather than decorative.** This guide and `docpack` both
run on MkDocs with Material, and between them they carry a hand-written
anchor-and-heading link checker, a fence gate, a render gate, a dialect gate
and a `hooks/seo.py` that exists because the README once claimed something the
theme did not actually do. The compensating gates are the evidence, not the
site.

## Related

- [Choosing a static site generator](static-site-generators.md), the comparison this sits in
- [Link checking](link-checking.md), the first gate MkDocs makes you write
- [Markdown and its dialects](markdown.md), the third one
- [SEO for documentation](seo-for-docs.md), what the hook in step 5 fixes
