---
title: Docusaurus
summary: A React documentation site with versioning and i18n built in, and 771 packages behind it.
diataxis: how-to
audience: developer
concept: docusaurus
tags: [dac, supporting]
---

# Docusaurus

`supporting` · difficulty 2 · 5h

!!! quote "Asked for by name"
    NVIDIA: "static site generators (Sphinx, MkDocs, Docusaurus, or similar)"

**Prerequisites:** [Choosing a static site generator](static-site-generators.md), [MDX](mdx.md)

## What it is

A React-based static site generator aimed specifically at documentation,
originally from Meta. Pages are [MDX](mdx.md), so prose can contain components,
and the things that are plugins or conventions elsewhere are first-class here:
[versioned docs](versioning.md), internationalisation, a blog, search
integration and a sidebar model.

It produces a React application that is pre-rendered to static HTML, and that
pre-rendering turns out to matter more than it sounds.

## Why the job asks for it

NVIDIA lists it third. In practice Docusaurus is what you find on product-facing
developer sites, especially where the documentation needs interactive pieces or
where the front-end team already lives in React.

The judgment being tested is whether you can weigh it honestly. It is the
strongest of the four on versioning and translation, which are the two features
teams most often discover they need after choosing a generator that makes them
hard. It is also the heaviest, and its content is the least portable.

## The golden path

Scaffold, build, and test what the build catches. About forty minutes, most of
it waiting for npm.

**Step 1: scaffold**

```bash
npx create-docusaurus@3.10.2 mysite classic --javascript --skip-install
cd mysite && npm install
```

Pass `--javascript` or the scaffolder prompts and hangs in CI. Then measure what
you just acquired:

```bash
du -sh node_modules && ls node_modules | wc -l
```

```
349M	node_modules
771
```

Seven hundred and seventy-one packages, 349 megabytes, for a documentation
site. That is not an argument against it, but it is a number worth saying out
loud when someone asks why the build is slower than MkDocs.

**Step 2: build**

```bash
npm run build
find build -name "*.html" | wc -l
```

```
[SUCCESS] Generated static files in "build".
28
```

28 pages in about 10 seconds. Per page that is the slowest of the three by a
wide margin, because it is compiling and pre-rendering a React application
rather than templating HTML.

This page used to put a MkDocs and a Sphinx figure beside that one, from a
measurement that ran once and was never committed.
`drills/generator_build.py` now builds an identical corpus under both, and the
comparison is more interesting than the numbers were:

```
  pages   mkdocs   sphinx cold   sphinx warm   warm vs mkdocs
    121     0.50          1.57          0.59   mkdocs 1.2x faster
    240     0.91          2.36          0.58   sphinx 1.6x faster
    480     1.94          4.10          0.65   sphinx 3.0x faster
```

One machine, one run, and the shape is the claim rather than the seconds. The
shape is that **MkDocs rebuilds everything every time and Sphinx rebuilds what
changed**, so MkDocs' time scales with the corpus and Sphinx's warm build is
almost flat. The two lines cross just above the corpus size the old figure
used, which is why that figure confirmed a conclusion the next data point
reverses.

The edit loop, which is what a writer experiences, says the same thing:

```
  one page edited in 121: mkdocs 0.53s, sphinx 0.59s  (mkdocs 1.1x faster)
  one page edited in 480: mkdocs 1.78s, sphinx 0.70s  (sphinx 2.5x faster)
```

Two things worth taking from this. **A build-time comparison has to say which
build**, because cold and warm are different questions: CI pays the cold number
on every run and an author pays the warm one forty times an afternoon. And a
ratio measured at one corpus size is not a property of the tools. The old
figure here was reproducible in direction, overstated in magnitude, and
describes a regime this guide's own corpus has nearly grown out of.

Docusaurus itself is not in that table. Re-measuring it needs an `npm install`
of a few hundred megabytes, so the 10 seconds above remains one unverified run
and is labelled as such rather than quietly standing beside two measured
numbers.

**Step 3: a broken link**

````bash
cat > docs/broken.md <<'EOF'
# Broken

See [the missing page](./nope.md).
EOF
npm run build; echo "exit=$?"
````

```
[WARNING] Markdown link with URL `./nope.md` in source file "docs/broken.md"
          (7:5) couldn't be resolved.
[ERROR] Error: Docusaurus found broken links!
  Note: it's possible to ignore broken links with the 'onBrokenLinks'
  Docusaurus configuration, and let the build pass.
exit=1
```

Fails **by default**, with no strict flag. That is a better default than MkDocs,
where `--strict` is opt-in, and the error message helpfully tells you the escape
hatch exists.

**Step 4: an undefined component, which is the interesting one**

````bash
rm docs/broken.md
cat > docs/undef.mdx <<'EOF'
# Undefined

<NoSuchComponent>body</NoSuchComponent>
EOF
npm run build; echo "exit=$?"
````

```
[ERROR] Error: Docusaurus static site generation failed for 1 paths:
  [cause]: Error: Expected component `NoSuchComponent` to be defined: you
           likely forgot to import, pass, or provide it.
      at _missingMdxReference (...)
exit=1
```

Caught, with the component named.

This is worth dwelling on, because it corrects the usual warning about MDX. The
MDX compiler itself only emits a *runtime* guard, so compiling a page proves
nothing. Docusaurus catches it anyway, because static site generation renders
every page during the build, which executes that guard. The pre-rendering is
what converts a reader-facing crash back into a build failure.

**What you built.** A site whose build fails on a broken link and on a missing
component, at the cost of 771 packages and the slowest per-page build of the
four.

## Reference

### What the build checks, measured

| Defect | Docusaurus `build` |
|---|---|
| Link to a missing page | Fails, by default |
| Link to a missing anchor | Fails, with `onBrokenAnchors` |
| Undefined MDX component | Fails, via pre-rendering |
| Page in no sidebar | Passes, unless configured |
| Malformed front matter | Fails |

The first three are a stronger default posture than MkDocs. Set
`onBrokenLinks: 'throw'` and `onBrokenAnchors: 'throw'` explicitly anyway, so
the behaviour is recorded rather than inherited.

### What is built in that is a project elsewhere

| Feature | Docusaurus | MkDocs | Sphinx |
|---|---|---|---|
| Versioned docs | Built in, a command | `mike` plugin | Build-per-version convention |
| Internationalisation | Built in, per-locale builds | Plugin, limited | `gettext` workflow |
| Blog | Built in | Plugin | Extension |
| Client-side search | Plugin, or Algolia | Built in | Built in |
| Interactive components | Native, [MDX](mdx.md) | No | No |

Versioning and i18n are the real differentiators. If you know you need either,
this is the generator that makes them ordinary rather than a project.

### What it costs

| Cost | Detail |
|---|---|
| Dependency surface | 771 packages, 349 MB, measured above |
| Build speed per page | Slowest of the four |
| Portability | Pages depend on your component library, not just the generator |
| Reviewer skills | Diffs contain JSX |
| Machine readability | Components are worse input to [chunking](chunking.md) than prose |
| Upgrade work | Major versions have required real migration effort |

### Choosing it

| Choose Docusaurus | Choose something else |
|---|---|
| You need versioned docs and translations | Neither is on the roadmap |
| The site needs interactive examples | The content is prose and samples |
| A React team maintains the site | Nobody on the team writes JavaScript |
| It is a product site, not a library reference | It is a Python or C++ API reference |

## How to talk about it

**Lead with what it makes ordinary.** "Docusaurus is the one where versioned
docs and internationalisation are features rather than projects, and where
pages can contain components. The price is a React toolchain: 771 packages in a
default install, and the slowest per-page build of the common generators."

**The follow-up is often a challenge about weight**, and the honest answer
concedes it with numbers and then says what it buys. If the project does not
need versioning, i18n, or components, the weight buys nothing and MkDocs is the
better choice.

**The tradeoff to volunteer.** Content portability. Pages written against your
component library cannot move to another generator without a rewrite, and that
coupling grows quietly as the component set grows. It is usually the right bet
for a product site with a long life and a front-end team, and it is a genuine
commitment rather than a default.

**One sharper point.** Docusaurus catches
undefined MDX components even though the MDX compiler does not, because static
site generation renders every page during the build. Most discussions of MDX
warn that component typos reach readers; that is true of the compiler and false
of this build. Knowing the difference shows you tested the pipeline rather than
read about the format.

## How to prove it

**The artifact.** A Docusaurus site with `onBrokenLinks` and `onBrokenAnchors`
set to throw explicitly, and a versioned docs directory if versioning is the
reason you chose it.

**Three things to do, in order:**

1. Run the golden path. Step 4 is the one to remember, because it contradicts
   the common warning about MDX.
2. Measure `du -sh node_modules` on any Docusaurus site you have. Quote the
   number rather than an adjective when weight comes up.
3. Check whether `onBrokenAnchors` is set on a site you maintain. Links are
   usually handled; anchors usually are not.

**What makes it credible rather than decorative.** Neither of this guide's
repositories uses Docusaurus, which the [demonstrated](../demonstrated.md) page
records. What travels is the measured comparison: fails on a broken link by
default where MkDocs needs `--strict`, catches a missing component where the
compiler alone cannot, and costs 771 packages and the slowest per-page build to
do it.

## Related

- [MDX](mdx.md), the authoring format, and the error distribution this page corrects
- [Choosing a static site generator](static-site-generators.md), the comparison
- [Versioned documentation](versioning.md), the feature that most often decides this
- [Localization and translation pipelines](localization.md), the other one
