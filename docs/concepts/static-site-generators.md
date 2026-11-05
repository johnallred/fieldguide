---
title: Choosing a static site generator
summary: The decision is about how much correctness the build checks, not about which syntax you prefer.
diataxis: explanation
audience: developer
concept: static-site-generators
tags: [dac, core]
---

# Choosing a static site generator

`core` · difficulty 2 · 3h

!!! quote "Asked for by name"
    NVIDIA: "static site generators (Sphinx, MkDocs, Docusaurus, or similar)"

**Prerequisites:** [Markdown and its dialects](markdown.md)

**Leads to:** [MkDocs and Material](mkdocs.md), [Sphinx](sphinx.md), [Docusaurus](docusaurus.md), [Antora and AsciiDoc](antora.md), [Versioned documentation](versioning.md)

## What it is

The tool that turns a tree of source files into a website. It decides your
[Markdown dialect](markdown.md), your navigation model, your theming, your
extension mechanism, and, least discussed and most important, **how much of
your corpus's correctness the build is willing to check**.

NVIDIA names three by name. The useful skill is not having a favourite, it is
being able to say what each one's build does and does not verify.

## Why the job asks for it

Because the choice is close to irreversible and it is usually made by whoever
set up the repository in week one.

Migrating a mature corpus between generators means rewriting every
tool-specific construct, remapping every URL, rebuilding the navigation model
and retraining contributors. People do not do it. So the generator you inherit
is the generator you have, and the valuable thing is to know its blind spots
well enough to close them with [CI gates](documentation-ci.md).

That framing is also the honest answer to "which would you choose". The
differences in syntax and theming are small and mostly taste. The differences
in what the build catches are large and measurable.

## The golden path

Build identical content in two generators and compare what each one is willing
to fail on. About thirty-five minutes.

**Step 1: the same three defects in both**

````bash
mkdir -p ssg/mk/docs ssg/sx/src && cd ssg

# MkDocs
printf 'site_name: W\n' > mk/mkdocs.yml
cat > mk/docs/index.md <<'EOF'
# Widget

See [the tuning bit](guide.md#tuning).
EOF
printf '# Guide\n\n## Setup\n\nContent.\n' > mk/docs/guide.md
printf '# Orphan\n\nNobody links here.\n' > mk/docs/orphan.md

# Sphinx, with MyST so the source is also Markdown
cat > sx/src/conf.py <<'EOF'
project = "W"
extensions = ["myst_parser"]
EOF
cat > sx/src/index.md <<'EOF'
# Widget

See [the tuning bit](guide.md#tuning).

```{toctree}
guide
```
EOF
printf '# Guide\n\n## Setup\n\nContent.\n' > sx/src/guide.md
printf '# Orphan\n\nNobody links here.\n' > sx/src/orphan.md
````

Two defects: a link to `guide.md#tuning` where `guide.md` has no Tuning
heading, and a page in no navigation at all.

**Step 2: ask both builds, in their strictest mode**

```bash
( cd mk && python3 -m mkdocs build --strict >/dev/null 2>&1; echo "mkdocs --strict exit=$?" )
sphinx-build -q -W -b html sx/src sx/out >/dev/null 2>&1; echo "sphinx -W  exit=$?"
```

```
mkdocs --strict exit=0
sphinx -W  exit=1
```

```
WARNING: local id not found in doc 'guide': 'tuning' [myst.xref_missing]
WARNING: document isn't included in any toctree [toc.not_included]
```

MkDocs's strictest mode passes a corpus with a dead heading anchor and an
unreachable page. Sphinx fails on both, and names them.

This is the measured version of the gap that
[link checking](link-checking.md) exists to close: the custom anchor checker on
that page is necessary on MkDocs and redundant on Sphinx.

**Step 3: measure what the stricter build costs**

121 generated pages, same content in both:

```
mkdocs,  cold build          0.58 s
sphinx,  cold build          3.52 s
sphinx,  incremental rebuild 0.75 s
```

Sphinx is roughly six times slower cold, because it builds an intermediate
doctree that makes cross-reference resolution possible. That doctree is also
what gives it incremental rebuilds, which MkDocs does not have.

**Step 4: find out what actually dominates build time**

Same generator, same 121 pages, two configurations:

```
mkdocs, default theme, no extensions    0.6 s
mkdocs, Material theme, 12 extensions  16.0 s
```

Twenty-seven times slower, with the generator held constant. **Your theme and
extension set matter far more to build time than your choice of generator.**
Anyone comparing generators on speed without holding the theme constant is
measuring the wrong thing.

**What you learned.** The real axis is how much the build verifies, the real
cost of verification is a doctree and some seconds, and the headline speed
numbers people quote are mostly about themes.

## Reference

### What each build checks, measured

| Defect | MkDocs `--strict` | Sphinx `-W` |
|---|---|---|
| Link to a missing page | Fails | Fails |
| Link to a missing heading anchor | **Passes** | Fails |
| Page in no navigation | **Passes** | Fails |
| Reference to a missing symbol | Fails, with `mkdocstrings` autorefs | Fails, with domains |
| Duplicate label | No such concept | Fails |

The second and third rows are what you have to replace with your own gates on
MkDocs. The fourth row needs a tool that collects symbols: Sphinx natively,
or MkDocs with `mkdocstrings` and its `[text][symbol]` references, which are
checked. Plain Markdown links to generated anchors are not.

### The four, in one table

| | MkDocs | Sphinx | Docusaurus | Antora |
|---|---|---|---|---|
| Source | Markdown | RST, or Markdown via MyST | MDX | AsciiDoc |
| Runtime | Python | Python | Node | Node |
| Cross-reference checking | Pages only | Pages, anchors, symbols | Pages | Pages, across repos |
| Versioning | A plugin | A convention plus builds | Built in | Built in, first-class |
| Multi-repository | No | No | No | Yes, its reason to exist |
| Interactive components | No | No | Yes | No |
| Setup cost | Lowest | Medium | Medium | Highest |
| Best at | Getting good fast | API correctness | Product sites | Many repos, one site |

### Choosing, honestly

| Situation | Choice |
|---|---|
| A library's API docs, Python or C++ | [Sphinx](sphinx.md) |
| A product site with interactive examples | [Docusaurus](docusaurus.md) |
| Documentation spread over many repositories | [Antora](antora.md) |
| Anything else, and you want to be productive today | [MkDocs](mkdocs.md) |
| You inherited one | Keep it, and close its gaps with gates |

The last row is the most common real situation and the best interview answer.

### What you will have to build yourself, by choice

| On MkDocs | On Sphinx |
|---|---|
| Anchor checking | Little; the build covers it |
| Orphan page detection | Little |
| Versioned docs, via a plugin | A build-per-version convention |
| A content model validator | A content model validator |
| Sample execution | Sample execution |

Both still need [sample validation](code-sample-validation.md) and
[cold-start testing](coldstart-testing.md). No generator checks whether your
quickstart works.

## How to talk about it

**Lead with correctness, not syntax.** "The difference that matters is how much
the build verifies. MkDocs in strict mode ships a dead heading anchor and an
unreachable page; Sphinx with `-W` fails on both and also fails on a reference
to a symbol that moved. So the choice is really about how much of the gate
suite you are going to write yourself."

**The follow-up is usually about speed**, and the honest answer corrects the
premise. Sphinx is slower cold and has incremental rebuilds, but holding the
generator constant and swapping a bare theme for Material and a dozen
extensions cost twenty-seven times more than the generator choice did. Theme
weight dominates.

**The tradeoff to volunteer.** Sphinx's correctness comes from a doctree, and
the doctree is also its difficulty: `conf.py` is a Python program, errors are
reported in its own vocabulary, and contributors meet directives before they
meet their first page. MkDocs is dramatically easier to adopt, and you pay for
that later in gates you write yourself. Both are defensible; pretending one is
simply better is the tell.

**One sharper point.** Migration between generators effectively does not
happen, so this reads like a high-stakes decision and mostly is not one: you
will inherit a choice. The valuable skill is auditing what your generator's
build does *not* check and closing those specific gaps, which is a concrete
thing to have done and a much better interview answer than a preference.

## How to prove it

**The artifact.** A table like step 2's for the generator you actually use,
with the gaps you closed and how.

**Three things to do, in order:**

1. Run the golden path. Step 2 takes ten minutes and the result surprises most
   people who use MkDocs daily.
2. Put a dead heading anchor into your own corpus and confirm whether your
   build catches it. If not, you have just identified your first gate.
3. Time your build with your theme and again with the default theme. The ratio
   tells you where your build minutes actually go.

**What makes it credible rather than decorative.** This guide runs on MkDocs
with Material, and it has a hand-written anchor checker, a fence gate and a
render gate precisely because the build does not cover them. Being able to say
"I chose this generator and here are the three checks I added to compensate" is
the answer that demonstrates judgment rather than preference.

## Related

- [MkDocs and Material](mkdocs.md), the fastest path to a good site
- [Sphinx](sphinx.md), the strictest build and the API reference story
- [Docusaurus](docusaurus.md), when the site needs components
- [Documentation CI](documentation-ci.md), where you close your generator's gaps
