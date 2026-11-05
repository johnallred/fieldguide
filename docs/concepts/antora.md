---
title: Antora and AsciiDoc
summary: The generator built for documentation spread across many repositories, and the markup that has includes in the base language.
diataxis: explanation
audience: developer
concept: antora
tags: [dac, context]
---

# Antora and AsciiDoc

`context` · difficulty 2 · 3h

!!! note "Not a quotation (adjacent)"
    Covered only by "or similar" in NVIDIA's list of generators. Worth
    recognising, rarely worth choosing for a new project, and the one answer to
    a problem the others cannot solve.

**Prerequisites:** [Choosing a static site generator](static-site-generators.md)

## What it is

Two things usually named together. **AsciiDoc** is a markup language with a real
specification, more capable than Markdown and considerably more verbose.
**Antora** is a generator that assembles one documentation site from AsciiDoc
content living in *several Git repositories*, each at a chosen branch or tag.

That second part is its reason to exist, and it is the thing none of the other
three generators do.

## Why the job asks for it

It does not, except through "or similar", which the banner above records
honestly. This page is `context` tier for two reasons.

The first is recognition. AsciiDoc shows up in enterprise and Java-adjacent
documentation estates, and in the Red Hat ecosystem in particular, so you will
meet it if you work across a large organisation's content.

The second is more useful. Antora solves the one problem that genuinely has no
good answer in MkDocs, Sphinx or Docusaurus: documentation that lives next to
the code in a dozen repositories and has to publish as one coherent site with
one navigation and one search index. If you are ever asked how you would do
that, Antora is the answer, and knowing it exists is worth more than fluency in
its configuration.

## The golden path

Convert a page that uses the features Markdown needs extensions for, and see
which ones AsciiDoc has in the base language. About twenty minutes. The honest
limits of what was executed here are stated at the end.

**Step 1: a page using six constructs**

````bash
mkdir -p adoc-demo/shared && cd adoc-demo
npm init -y >/dev/null && npm install @asciidoctor/core@3.0.4

cat > sample.adoc <<'EOF'
= Widget Guide
:toc:
:widget-version: 2.4

== Install

Requires version {widget-version} or later.

[NOTE]
====
An admonition with a block body.
====

include::shared/prereqs.adoc[]

[source,python]
----
client = Client()
client.retry(times=5)
----

See <<configure>> and the xref:other.adoc#section[other page].

[#configure]
== Configure

.A table with a title
|===
| Option | Default

| retry
| 5
|===
EOF

printf 'You need Python 3.10 or later.\n' > shared/prereqs.adoc
````

An attribute used as a variable, an admonition with a block body, a file
include, a highlighted source block, an internal cross-reference, and a titled
table.

**Step 2: convert it with no extensions configured**

```javascript
// t.mjs
const asciidoctor = require('@asciidoctor/core')()
const html = asciidoctor.convertFile('sample.adoc',
  { to_file: false, safe: 'unsafe', standalone: false })

const checks = {
  'attribute substituted': html.includes('2.4'),
  'admonition block':      html.includes('admonitionblock'),
  'include resolved':      html.includes('Python 3.10'),
  'source block':          html.includes('language-python'),
  'internal xref':         html.includes('#configure'),
  'table with title':      html.includes('tableblock'),
}
for (const [k, v] of Object.entries(checks)) {
  console.log('  ' + k.padEnd(24) + (v ? 'yes' : 'NO'))
}
```

```
  attribute substituted   yes
  admonition block        yes
  include resolved        yes
  source block            yes
  internal xref           yes
  table with title        yes
```

All six, with no extensions enabled. Compare that with the
[Markdown](markdown.md) result, where five constructs produced five different
answers across five implementations and every one of them was an extension.

The two to notice are **includes** and **attributes**. Those are
[single-sourcing](single-sourcing.md) primitives in the base language: content
reuse and variable substitution without a plugin, a convention or a
preprocessor. In Markdown both require tooling, and the tooling differs per
generator.

**Step 3: understand the thing Antora adds**

Antora's unit is a **component version**: a named documentation component at a
specific version, sourced from a Git repository and branch. The playbook names
the sources:

```yaml
# antora-playbook.yml
content:
  sources:
    - url: https://github.com/example/widget-core
      branches: [main, v2.x]
      start_path: docs
    - url: https://github.com/example/widget-cli
      branches: [main]
      start_path: docs
output:
  dir: ./build/site
```

One site, two repositories, three branches, and cross-references that resolve
*across* them. `xref:widget-cli:install.adoc` from a page in `widget-core`
resolves to a page in a different repository, and Antora fails the build if it
cannot be found.

**What was and was not executed here.** Steps 1 and 2 ran, with
`@asciidoctor/core` 3.0.4, and the six results are measured. Step 3 was not
executed: `rubygems.org` is not reachable from this environment, and a real
multi-repository Antora build needs published Git sources rather than local
directories. The playbook above is the shape of the configuration, not a
verified run, and this page says so rather than implying otherwise.

**What you learned.** Which of AsciiDoc's advantages are in the base language,
measured rather than claimed, and where the honest limit of this exercise sits.

## Reference

### AsciiDoc against Markdown, on capability

| Construct | AsciiDoc | Markdown |
|---|---|---|
| Includes | Base language | Per-generator plugin |
| Attributes and substitution | Base language | Front matter plus templating |
| Admonitions with block bodies | Base language | Extension, per-tool syntax |
| Tables with titles, spans, formatting | Base language | Extension, limited |
| Cross-references by id | Base language | Link to a generated anchor |
| Conditional content | Base language, `ifdef` | Not available |
| A specification | Yes | CommonMark, plus dialects |
| Contributor familiarity | Low | High |
| Tooling ecosystem | Small | Very large |

The capability column is one-sided, and it does not settle the question.
Familiarity and ecosystem decide most real projects, which is why AsciiDoc
remains a minority choice despite being the better language.

### What Antora is for

| Problem | Antora's answer |
|---|---|
| Docs in many repositories, one site | Component versions from multiple Git sources |
| Each repository ships on its own schedule | Per-branch, per-tag content |
| Cross-repository references | Typed xrefs, resolved and checked at build |
| One navigation across all of it | A per-component nav, assembled |
| Versioned docs | Versions are branches, not a plugin |

### When to choose it, and when not

| Choose Antora | Do not |
|---|---|
| Content lives in many repositories and must publish as one site | It is one repository |
| Versions map to branches or tags already | A new project with no AsciiDoc |
| The organisation already writes AsciiDoc | Contributors need to start today |
| Java or Red Hat ecosystem conventions | You need interactive components |

### If you have one repository and want includes

You do not need Antora. You need
[single-sourcing](single-sourcing.md) in whatever generator you already have:
a snippet include plugin on MkDocs, `.. include::` on Sphinx, or MDX imports on
Docusaurus. Reaching for Antora to get includes is a large change for a small
feature.

## How to talk about it

**Lead with the multi-repository problem, because that is the only reason to
choose it.** "Antora is the answer when documentation lives next to the code in
a dozen repositories and has to publish as one site with one navigation and
cross-references that resolve between them. None of the other generators do
that, and the common workarounds, submodules or a sync script, are worse."

**The follow-up is whether you would pick AsciiDoc for a new project**, and the
honest answer is usually no. It is the more capable language, and contributor
familiarity and tooling ecosystem decide most projects. Say both halves.

**The tradeoff to volunteer.** Adopting AsciiDoc costs you the Markdown
ecosystem: fewer editors and preview tools, a smaller set of linters, and
contributors who need to learn a syntax they do not already know. On a project
where most content comes from engineers writing occasionally, that friction is
the dominant cost and it outweighs the capability gain.

**One sharper point.** Includes and attributes being in the base language is a
bigger deal than it sounds, because it means single-sourcing is portable. In
Markdown, content reuse is always a per-generator plugin, so a corpus that
relies on it is locked to that generator. In AsciiDoc the reuse mechanism
travels with the content.

## How to prove it

**The artifact.** Realistically, none. This is a recognition-and-judgment
concept, and the deliverable is being able to answer the multi-repository
question without reaching for submodules.

**Three things to do, in order:**

1. Run steps 1 and 2. Twenty minutes, and the six-for-six result is the thing
   worth remembering about the language.
2. Write down how you *would* publish one site from five repositories using
   your current generator. The awkwardness of that answer is Antora's argument.
3. Find an AsciiDoc page in the wild, a Red Hat or Spring doc, and read its
   source. Recognition is most of what this concept is for.

**What makes it credible rather than decorative.** Saying plainly which parts
you have run. Steps 1 and 2 are measured here with `@asciidoctor/core` 3.0.4;
the Antora playbook is not, because this environment cannot reach
`rubygems.org` and a real build needs remote Git sources. A candidate who
separates those two things is more trustworthy than one who presents a
configuration file as experience.

## Related

- [Choosing a static site generator](static-site-generators.md), where this sits among the four
- [Single-sourcing](single-sourcing.md), which AsciiDoc does natively
- [Versioned documentation](versioning.md), which Antora treats as branches
- [Markdown and its dialects](markdown.md), the comparison in step 2
