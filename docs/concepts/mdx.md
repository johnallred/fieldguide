---
title: MDX
summary: Markdown that compiles to JavaScript, which moves some failures from build time to render time.
diataxis: explanation
audience: developer
concept: mdx
tags: [dac, supporting]
---

# MDX

`supporting` · difficulty 2 · 3h

!!! quote "Asked for by name"
    Intel: "Hands on experience with docs-as-code workflows and documentation CI, including Git, Markdown or MDX, and doc build pipelines"

**Prerequisites:** [Markdown and its dialects](markdown.md)

**Leads to:** [Docusaurus](docusaurus.md)

## What it is

Markdown with JSX in it. You can import a component and use it as a tag inside
prose, which makes interactive examples, tabbed code blocks and live API
playgrounds possible in a documentation page.

The fact that matters more than the syntax: **MDX does not compile to HTML. It
compiles to a JavaScript module.** Everything else on this page follows from
that, including the one genuinely dangerous property.

## Why the job asks for it

Intel names it directly, as an alternative to Markdown. In practice that means
their documentation estate includes a React-based generator, almost certainly
[Docusaurus](docusaurus.md), and you would be maintaining pages that are
partly code.

The judgment being tested is whether you understand the costs. MDX is
genuinely better for a developer-facing site that needs interactive examples,
and it moves a class of error from your build into your reader's browser. An
engineer who has only read about it tends to describe the first half.

## The golden path

Compile six inputs and find out which ones MDX accepts. About twenty-five
minutes. Two of the failures are ordinary Markdown.

**Step 1: a compiler, and nothing else**

```bash
mkdir -p mdx-demo && cd mdx-demo
npm init -y >/dev/null
npm install @mdx-js/mdx@3.1.0
```

Note that `require('@mdx-js/mdx')` fails: the package is ESM-only, so the
examples below use `.mjs` and top-level `await`.

**Step 2: ask it about six inputs**

```javascript
// t.mjs
import { compile } from '@mdx-js/mdx'

const cases = {
  "undefined component": '# Hi\n\n<Note>body</Note>\n',
  "literal brace":       'Set it to {retry} in the config.\n',
  "less-than in prose":  'Use a value < 5 for safety.\n',
  "html comment":        '<!-- a note -->\n\nText.\n',
  "autolink-ish":        'Mail <a@b.com> for help.\n',
  "plain markdown":      '# Title\n\n| a | b |\n|---|---|\n| 1 | 2 |\n',
}
for (const [name, src] of Object.entries(cases)) {
  try {
    const out = String(await compile(src))
    console.log(`  OK    ${name.padEnd(22)} -> ${out.length} bytes of JS`)
  } catch (e) {
    console.log(`  FAIL  ${name.padEnd(22)} -> ${e.message.split('\n')[0].slice(0, 70)}`)
  }
}
```

```bash
node t.mjs
```

```
  OK    undefined component    -> 871 bytes of JS
  OK    literal brace          -> 514 bytes of JS
  OK    less-than in prose     -> 487 bytes of JS
  FAIL  html comment           -> Unexpected character `!` (U+0021) before name
  FAIL  autolink-ish           -> Unexpected character `@` (U+0040) in name
  OK    plain markdown         -> 648 bytes of JS
```

Read the two failures first. **An HTML comment is not valid MDX**, and neither
is an angle-bracket autolink. Both are ordinary, legal Markdown. If you migrate
a Markdown corpus to MDX, every `<!-- -->` in it breaks the build, and comments
are exactly the thing writers leave behind in draft pages.

Note also that "bytes of JS" is not a figure of speech. The output is a
JavaScript module, which is the point of step 3.

**Step 3: the dangerous one**

`<Note>body</Note>` compiled successfully, and `Note` was never defined or
imported. Look at what the compiler emitted:

```javascript
// t3.mjs
import { compile } from '@mdx-js/mdx'
const out = String(await compile('# Hi\n\n<Note>body</Note>\n'))
for (const line of out.split('\n')) {
  if (/Note|_missingMdxReference|components/.test(line)) {
    console.log('  ', line.trim().slice(0, 96))
  }
}
```

```
   const _components = {
   ...props.components
   }, {Note} = _components;
   if (!Note) _missingMdxReference("Note", true);
   children: [_jsx(_components.h1, {
   }), "\n", _jsx(Note, {
   function _missingMdxReference(id, component) {
```

The compiler succeeded and emitted a **runtime** guard. `_missingMdxReference`
throws when the page renders, not when it compiles. So compiling MDX is not
sufficient to know a page works.

**Step 4: find out whether that actually reaches readers**

The obvious conclusion is that a typo'd component produces a green build and a
page that crashes in the reader's browser. Test it rather than asserting it,
because it depends entirely on what your generator does after compiling.

Put the same undefined component into a [Docusaurus](docusaurus.md) site and
build:

````bash
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

Caught, with the component named. Docusaurus does static site generation, which
means it **renders every page during the build**, so the runtime guard fires at
build time after all.

So the honest statement is narrower than the obvious one. The compiler defers
the error; a generator that pre-renders converts it back into a build failure.
The risk is real for any pipeline that compiles MDX without rendering it, or
that renders only in the browser, and it is not a problem on a conventional
Docusaurus build.

**What you learned.** MDX rejects two common Markdown constructs outright, and
whether an undefined component is a build error or a reader-facing crash
depends on your generator rather than on MDX. Check which yours does rather
than assuming.

**Step 5: so what is the gate**

If your generator pre-renders, the build is your render check and you need
nothing extra. If it does not, you need one: a production build plus a crawl of
the output, or a check that every component referenced in the corpus exists in
your library. The question to answer for your own pipeline is simply whether
`build` renders pages or only compiles them.

## Reference

### What MDX buys

| Capability | Why you would want it |
|---|---|
| Components in prose | Tabs, interactive examples, API playgrounds |
| Imports | Share a snippet or a diagram across pages |
| Expressions and props | Inject version numbers or config at build time |
| Full React ecosystem | Charts, embeds, live editors |

### What it costs

| Cost | Detail |
|---|---|
| Component errors defer to render | The compiler passes them; only a pre-rendering generator catches them |
| Two Markdown constructs break | HTML comments and angle-bracket autolinks |
| The corpus is now code | Reviewers need to read JSX; linting is a JS concern |
| Toolchain weight | Node, a bundler, and a dependency tree to maintain |
| Machine readability drops | A page full of components is hard to [chunk](chunking.md) |
| Portability | Pages are tied to your component library, not just a generator |

The machine-readability cost deserves attention in an AI-ready corpus. A
retrieval pipeline that reads your source gets `<Tabs><TabItem ...>` rather
than prose, and one that reads your HTML gets whatever the component rendered.
Either way, content expressed as components is harder to
[make agent-ready](agent-ready-content.md) than content expressed as text.

### Migrating Markdown to MDX

| Construct | Fate |
|---|---|
| `<!-- comment -->` | Build error; convert to `{/* comment */}` |
| `<a@b.com>` autolink | Build error; write a normal link |
| Raw HTML with attributes | Often needs JSX attribute names, `className` not `class` |
| `{` in prose | Usually fine in MDX 3, historically not |
| Unclosed HTML tags | Build error; JSX requires closure |

The first two are the ones that will actually bite you, and both are verified
above rather than inherited from a migration guide.

### When to choose it

| Choose MDX | Stay on Markdown |
|---|---|
| The site needs interactive examples | The content is prose and code samples |
| You already run a React site | You have no JavaScript toolchain |
| A component replaces copy-pasted boilerplate on many pages | Pages are mostly unique |
| Your audience is front-end developers | Your audience is anyone else |

## How to talk about it

**Lead with the compilation target.** "MDX compiles to a JavaScript module
rather than to HTML, and that is the root of everything. It buys components in
prose, and it makes an undefined component a render-time error rather than a
compile-time one."

**The follow-up is how you would gate it**, and this is where the obvious
answer is wrong. The compiler emits a runtime guard, so compiling is not
enough; but Docusaurus does static site generation, so it renders every page
during the build and the error comes back as a build failure naming the
component. I verified both halves. The gate you need therefore depends on your
generator: if it pre-renders, the build *is* your render check, and if it does
not, you need a crawl of the output or a component-reference check against your
library.

**The tradeoff to volunteer.** Components reduce duplication and increase
coupling. Every page using `<Tabs>` is now tied to your component library, so
a refactor of that component is a change to hundreds of pages, and the pages
cannot move to another generator without a rewrite. On a corpus you expect to
keep for a decade, that is a real bet.

**The correction worth volunteering.** The widely repeated claim is that MDX
turns component typos into reader-facing crashes. That is true of the compiler
and false of a normal Docusaurus build, which pre-renders and fails. Saying so
unprompted is a better signal than repeating the scare, because it shows you
tested the pipeline rather than the format.

**One sharper point.** An MDX corpus is harder to make machine-readable. Source
consumers see JSX instead of prose, HTML consumers see whatever rendered, and
both are worse inputs to [chunking](chunking.md) than plain Markdown. If the
same organisation is asking for both MDX and agent-ready content, that tension
is worth naming out loud, because it is real and most people miss it.

## How to prove it

**The artifact.** Less a repository than a demonstrated understanding of the
failure distribution. If you do build something, the valuable piece is the
component-reference check.

**Three things to do, in order:**

1. Run the golden path. Steps 2 and 3 are both surprises, and step 3 is the
   one to remember.
2. Grep a Markdown corpus for `<!--`. That count is the size of your MDX
   migration's first obstacle.
3. On any MDX site you can reach, find out whether CI renders the pages or only
   compiles them. If it only compiles, undefined components reach readers.

**What makes it credible rather than decorative.** Neither of this guide's
repositories uses MDX, which the [demonstrated](../demonstrated.md) page
records. What travels is the pair of measurements and the correction between them. The
compiler emits `if (!Note) _missingMdxReference("Note", true)`, a runtime
guard, so compiling proves nothing. A Docusaurus build of the same page exits
1 with `Expected component 'NoSuchComponent' to be defined`, because static
site generation renders every page. Both are checkable in minutes, and
the correction between them is the point: the first measurement supported the
claim that an undefined component reaches readers, and the second showed that
is false for any generator that pre-renders. The page says what the compiler
does and what a build does, separately, because conflating them is how the
wrong advice gets published.

## Related

- [Markdown and its dialects](markdown.md), what MDX extends and what it breaks
- [Docusaurus](docusaurus.md), the generator whose build catches the component error
- [Chunking strategies](chunking.md), why a corpus of components is harder to retrieve from
- [Agent-ready content](agent-ready-content.md), the cost MDX imposes on machine readers
- [Code-sample validation](code-sample-validation.md), the check that compiling alone does not give you 