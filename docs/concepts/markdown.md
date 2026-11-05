---
title: Markdown and its dialects
summary: Markdown is a family, not a format, and unsupported syntax ships to the reader as literal text.
diataxis: explanation
audience: developer
concept: markdown
tags: [dac, core]
---

# Markdown and its dialects

`core` · difficulty 1 · 2h

!!! quote "Asked for by name"
    NVIDIA: "Markdown/RST"

    Intel: "Git, Markdown or MDX, and doc build pipelines"

**Prerequisites:** [Docs-as-code](docs-as-code.md)

**Leads to:** [MDX](mdx.md), [reStructuredText](restructuredtext.md), [Choosing a static site generator](static-site-generators.md)

## What it is

A family of plain-text markup dialects that mostly agree about headings,
emphasis and lists, and disagree about almost everything else. "Markdown" names
the family. What your build actually accepts is decided by the specific parser
your [static site generator](static-site-generators.md) uses and the set of
extensions you enabled.

The practical consequence, and the reason this page exists at difficulty 1, is
the failure mode. A parser that does not understand a construct does not raise
an error. It passes the characters through, so the reader gets `~~struck~~`
with the tildes attached.

## Why the job asks for it

Both postings name it, Intel alongside MDX and NVIDIA alongside RST, which
tells you the expectation is not "can you write Markdown" but "do you
understand that these are different dialects with different capabilities."

Nobody is testing whether you can write a heading. What matters on a real
corpus is knowing which constructs are safe to use, where the extension
configuration lives, and that a dialect mismatch is silent. On a corpus with
multiple contributors, somebody will write GitHub-flavoured syntax because
GitHub rendered it in the pull request description, and your site will publish
the raw characters.

## The golden path

Run one source file through five implementations and watch them disagree. About
twenty minutes.

**Step 1: a file using five commonly assumed features**

````bash
mkdir -p md-demo && cd md-demo
cat > sample.md <<'EOF'
# Title

A table:

| a | b |
|---|---|
| 1 | 2 |

Term
: A definition.

~~struck~~ and a footnote[^1].

[^1]: The note.

- [ ] a task
EOF
````

Tables, definition lists, strikethrough, footnotes, task lists. All five feel
like "Markdown".

**Step 2: ask five parsers**

```python
import markdown
import mistune
from markdown_it import MarkdownIt

src = open("sample.md").read()

feats = {
    "table":    lambda h: "<table" in h,
    "deflist":  lambda h: "<dl" in h,
    "strike":   lambda h: "<del" in h or "<s>" in h,
    "footnote": lambda h: "[^1]" not in h and ('href="#fn' in h or "<sup" in h),
    "taskbox":  lambda h: 'type="checkbox"' in h,
}
impls = {
    "python-markdown core":   markdown.markdown(src),
    "python-markdown +ext":   markdown.markdown(
        src, extensions=["tables", "def_list", "footnotes"]),
    "mistune":                mistune.html(src),
    "markdown-it commonmark": MarkdownIt("commonmark").render(src),
    "markdown-it gfm-like":   MarkdownIt("gfm-like", {"linkify": False}).render(src),
}
print(f"{'implementation':26}" + "".join(f"{n:10}" for n in feats))
for label, html in impls.items():
    print(f"{label:26}" + "".join(
        f"{('yes' if fn(html) else '-'):10}" for fn in feats.values()))
```

```
implementation            table     deflist   strike    footnote  taskbox
python-markdown core      -         -         -         -         -
python-markdown +ext      yes       yes       -         yes       -
mistune                   yes       -         yes       yes       -
markdown-it commonmark    -         -         -         -         -
markdown-it gfm-like      yes       -         yes       -         -
```

**No two rows are the same.** Five implementations, five answers, one source
file. CommonMark, the actual standard, supports none of the five features,
because every one of them is an extension. And task lists render nowhere by
default, including in the GitHub-flavoured configuration.

**Step 3: see what the failure looks like**

```python
for label, html in impls.items():
    print(f"{label:26} literal '[^1]' in output: {'[^1]' in html}")
```

```
python-markdown core       True
python-markdown +ext       False
mistune                    False
markdown-it commonmark     True
markdown-it gfm-like       True
```

Three of the five publish `[^1]` to the reader. Not an error, not a warning.
The characters are simply passed through, because to a parser without the
extension they are just text.

This is the whole argument for treating dialect as a configuration you know
rather than a detail you inherit.

**Step 4: ask what your own site accepts**

Run the same source through the exact extension list in your `mkdocs.yml`. For
this guide, the answer is:

```
table                yes
deflist              yes
footnote converted   yes
strike               -
taskbox              -
```

Then look at what the unsupported half becomes:

```html
<p>~~struck~~ and a footnote<sup id="fnref:1">...</sup>.</p>
<li>[ ] a task</li>
```

Two constructs that any contributor might reasonably type, shipping as
literal characters.

**Step 5: make it a gate**

The source alone cannot tell you this, so compare source against built HTML,
exactly as [the fence gate](doc-test-harness.md) does. A construct used in
prose whose markers survive into the output did not render:

```python
CONSTRUCTS = {
    "strikethrough": (re.compile(r"~~[^~\n]+~~"), re.compile(r"~~[^~\n]+~~")),
    "task list": (re.compile(r"^\s*[-*]\s+\[[ xX]\]\s"),
                  re.compile(r"<li[^>]*>\s*\[[ xX]\]\s")),
}
```

Both halves have to agree: the construct in the source *and* its litter in the
HTML. Requiring both is what stops the check firing on a page that explains the
syntax inside a code sample.

```bash
fieldguide render
```

```
ok: 5147 fenced lines checked, every one renders as code; no unsupported
Markdown construct reaches the reader
```

**What you built.** Knowledge of which dialect your site actually speaks, and a
gate that fails when someone writes outside it.

## Reference

### What is in the base layer, and what is an extension

| Construct | CommonMark | Usually an extension |
|---|---|---|
| Headings, emphasis, lists, links, code | Yes | |
| Fenced code blocks | Yes | |
| Tables | No | Yes, everywhere |
| Footnotes | No | Yes |
| Definition lists | No | Yes |
| Strikethrough | No | GFM, and some others |
| Task lists | No | GFM, and a separate extension elsewhere |
| Admonitions and callouts | No | Highly tool-specific |
| Includes and transclusion | No | Tool-specific, often a plugin |
| Front matter | No | Convention, handled before parsing |

Front matter is worth singling out: it is not Markdown at all. It is a YAML
block that the generator strips before the parser sees the file, which is why
its rules differ from everything else on this page.

### The dialects you will meet

| Dialect | Where | Notable |
|---|---|---|
| CommonMark | The specification | Strict, small, unambiguous |
| GFM | GitHub, and much tooling | Tables, strikethrough, task lists, autolinks |
| Python-Markdown | MkDocs, Material | Extension ecosystem, including PyMdown |
| MyST | Sphinx with `myst-parser` | Markdown with reStructuredText's directive power |
| MDX | Docusaurus and friends | Markdown plus JSX; see [MDX](mdx.md) |
| AsciiDoc | Antora | Not Markdown; a different language with a real spec |

### Choosing what to allow

| Decision | Recommendation |
|---|---|
| Which extensions | The fewest that cover your content, chosen deliberately |
| Where it is recorded | In the generator config, in version control, reviewed |
| How contributors learn it | A short authoring guide, plus a gate that catches mistakes |
| GFM compatibility | Worth it if contributors draft in GitHub comments |
| Raw HTML | Allow sparingly; it breaks other renderers and most AI pipelines |

The last row matters more than it used to. Raw HTML inside Markdown is opaque
to anything that consumes your source rather than your HTML, including
[chunking](chunking.md) and [llms.txt](llms-txt.md) generation. A corpus with
heavy inline HTML is markedly harder to make [agent-ready](agent-ready-content.md).

## How to talk about it

**Lead with the failure mode, not the feature list.** "Markdown is a family of
dialects, and the thing that bites is that an unsupported construct is not an
error. The parser passes the characters through, so `~~struck~~` reaches the
reader with the tildes on it. So I treat the extension list as a configuration
I know, and I gate on it."

**The follow-up is usually about contributor experience.** The honest answer is
that contributors will write GFM, because GitHub rendered it in the pull
request they just opened, and the mitigations are a short authoring guide, a
sensible extension set that includes the common GFM constructs, and a check
that catches the rest.

**The tradeoff to volunteer.** Every extension you enable is a construct that
will not render elsewhere. Content written against Material's admonitions
cannot move to Docusaurus without a rewrite, and the more extensions you adopt
the more your corpus is locked to one generator. Portability and expressiveness
are genuinely opposed here, and the right answer depends on whether you expect
to migrate.

**One sharper point.** Front matter is not Markdown. It is stripped before
parsing, which is why its failures look different: a malformed YAML block can
take out the whole page rather than one construct, and it needs a
[content model](content-model.md) validator rather than a Markdown gate.

## How to prove it

**The artifact.** A documented extension set plus a check that fails when
somebody writes outside it.

**Three things to do, in order:**

1. Run the golden path. The five-row table is the thing to internalise: no two
   implementations agree.
2. Run your own site's extension list over the sample file and write down the
   answer. Most teams cannot tell you whether their site supports footnotes.
3. Grep your corpus for `~~` and `- [ ]` outside code fences. If you find any,
   they are shipping as literal characters right now.

**What makes it credible rather than decorative.** `src/fieldguide/dialect.py`
is the gate from step 5, with seven tests covering both directions, including
the case that keeps it honest: a page discussing the syntax inside a fence must
not be flagged for using it. This guide's own corpus is clean, which the test
asserts rather than assumes.

## Related

- [MDX](mdx.md), Markdown plus components, and the costs that come with it
- [reStructuredText](restructuredtext.md), the alternative with directives and a real spec
- [Choosing a static site generator](static-site-generators.md), which decides your dialect
- [Content models](content-model.md), which validates the front matter Markdown never sees
