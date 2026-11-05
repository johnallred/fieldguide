---
title: reStructuredText
summary: The markup with directives and cross-references, and the line between docutils and Sphinx.
diataxis: explanation
audience: developer
concept: restructuredtext
tags: [dac, supporting]
---

# reStructuredText

`supporting` · difficulty 2 · 3h

!!! quote "Asked for by name"
    NVIDIA: "Markdown/RST"

**Prerequisites:** [Markdown and its dialects](markdown.md)

**Leads to:** [Sphinx](sphinx.md)

## What it is

A plain-text markup language from the Python documentation world, older than
Markdown and considerably more capable. Its distinguishing features are
**directives**, which are block-level extensions, and **roles**, which are
inline ones, both of which take arguments and options. That extensibility is
what lets reStructuredText express a cross-reference to a Python function,
rather than a link to a URL you had to know.

The thing most people get wrong, including in interviews, is where
reStructuredText ends and [Sphinx](sphinx.md) begins. The golden path draws the
line precisely.

## Why the job asks for it

NVIDIA writes "Markdown/RST", and the reason is almost certainly that their
documentation estate includes Sphinx projects. Simulation, robotics and
graphics tooling is largely Python and C++, and Python API documentation has
been Sphinx territory for twenty years.

You are unlikely to be asked to start a new reStructuredText project. You are
quite likely to inherit one, be asked whether to migrate it, and be asked what
would be lost. Answering that well requires knowing which of the features are
the language and which are the tool, because the migration cost is entirely in
the second category.

## The golden path

Run one file through docutils, then through Sphinx, and find out which half of
"RST" is actually reStructuredText. About twenty-five minutes.

**Step 1: a file using the vocabulary people associate with RST**

````bash
mkdir -p rst-demo && cd rst-demo
cat > sample.rst <<'EOF'
Title
=====

.. note::
   A directive with a body.

.. versionadded:: 2.4
   The ``retry`` parameter.

See :ref:`configuring` and :py:func:`widget.retry`.

.. _configuring:

Configuring
-----------

.. code-block:: python
   :emphasize-lines: 2

   client = Client()
   client.retry(times=5)
EOF
````

A note admonition, a version annotation, two cross-reference roles, an internal
label, and a highlighted code block. This is what people mean when they say a
page is written in RST.

**Step 2: ask docutils, which is the reStructuredText implementation**

```bash
python3 -m docutils --report=2 sample.rst > out.html 2> err.txt
echo "exit=$?"
grep -cE "ERROR|WARNING" err.txt
head -8 err.txt
```

```
exit=0
4
sample.rst:7: (ERROR/3) Unknown directive type "versionadded".
sample.rst:10: (ERROR/3) Unknown interpreted text role "ref".
sample.rst:10: (ERROR/3) Unknown interpreted text role "py:func".
sample.rst:17: (ERROR/3) Error in "code-block" directive:
```

Four of the five constructs are unknown to reStructuredText itself. Only
`.. note::` is part of the language. `versionadded`, `ref`, `py:func` and
`code-block` are all **Sphinx**, not RST.

**Step 3: notice how docutils failed**

```bash
grep -o 'class="system-message[^"]*"' out.html | sort | uniq -c
grep -o 'Unknown directive type[^<]*' out.html | head -1
```

```
      4 class="system-message"
      4 class="system-message-title"
Unknown directive type &quot;versionadded&quot;.
```

Exit code 0, and the four errors are **rendered into the page** as
`system-message` blocks the reader can see. This is the same shape as the
[Markdown dialect](markdown.md) failure, with the volume turned up: instead of
quietly passing characters through, docutils publishes a visible error box. It
still does not fail the build.

**Step 4: ask Sphinx, with no extensions at all**

```bash
mkdir -p sx/src && cp sample.rst sx/src/index.rst
printf 'project = "demo"\nextensions = []\n' > sx/src/conf.py
sphinx-build -q -b html sx/src sx/out
echo "exit=$?"
grep -c "Unknown directive" sx/out/index.html
grep -c "versionadded" sx/out/index.html
```

```
exit=0
0
1
```

Everything resolves, with an empty `extensions` list. So all four constructs
come from Sphinx *core*, not from third-party extensions, which is the detail
that makes the boundary confusing: you do not opt into them, you get them by
using Sphinx at all.

**What you learned.** "RST" in common usage means reStructuredText plus
Sphinx's directive and role vocabulary. The language on its own is a structured
text format with admonitions and tables. Everything that makes it attractive
for API documentation is the tool.

## Reference

### Which half is which

| Construct | reStructuredText | Sphinx |
|---|---|---|
| Section headers, lists, tables | Yes | |
| `.. note::`, `.. warning::` | Yes | |
| `.. image::`, `.. include::` | Yes | |
| Substitutions, `|name|` | Yes | |
| `.. code-block::` with options | | Yes |
| `:ref:`, `:doc:` | | Yes |
| `:py:func:`, `:py:class:` and the domains | | Yes |
| `.. versionadded::`, `.. deprecated::` | | Yes |
| `.. toctree::` | | Yes |
| `.. autodoc`, `automodule` | | Yes, an extension |

The second column is the migration cost. A corpus using only the first column
converts to Markdown almost mechanically. A corpus using domains and `toctree`
does not convert at all without choosing replacements.

### What it has that Markdown does not

| Feature | Why it matters |
|---|---|
| Typed cross-references | `:py:func:\`widget.retry\`` resolves to the right symbol and fails the build if it moves |
| A directive model | Extensions are first-class, not per-tool syntax hacks |
| Domains | Separate namespaces for Python, C++, JavaScript symbols |
| A real specification | docutils is the reference implementation, not one dialect of many |
| Substitutions and includes | Single-sourcing without a plugin |

The first row is the strongest argument for it and the one to cite. A
cross-reference to a symbol is checkable in a way that a Markdown link to a
generated anchor is not, which makes a large API corpus genuinely more
maintainable.

### What it costs

| Cost | Detail |
|---|---|
| Contributor friction | Directive syntax, indentation sensitivity, and inline markup rules that surprise people |
| Inline markup is fussy | Nested emphasis and adjacent punctuation need escapes |
| Smaller tooling ecosystem | Fewer editors, linters and preview tools than Markdown |
| Errors can be invisible | As step 3 shows, docutils renders errors into the page |
| Hiring | Most writers arrive knowing Markdown |

### If you have an RST corpus and want Markdown

| Option | Keeps | Loses |
|---|---|---|
| MyST in Sphinx | All directives, roles, domains, `toctree` | Nothing structural; contributors write Markdown |
| Convert with `pandoc` | Prose | Every Sphinx construct in the right column above |
| Rewrite into another generator | Nothing automatic | Cross-reference checking, domains |

MyST is almost always the right answer, and knowing that is worth more in an
interview than an opinion about which syntax is nicer. It lets a Sphinx project
accept Markdown without giving up the capability that made Sphinx worth using,
so the migration question stops being all-or-nothing.

## How to talk about it

**Lead with the boundary.** "Most of what people call RST is Sphinx. The
language gives you admonitions, tables and substitutions; `code-block`, `ref`,
the Python domain and `toctree` all come from Sphinx core. That matters because
the migration cost of an RST corpus is entirely in the Sphinx half."

**The follow-up is whether you would migrate**, and the strong answer is MyST
rather than a conversion. It lets contributors write Markdown inside a Sphinx
project, keeping typed cross-references and domains, which is the capability
nobody wants to lose and most conversions throw away.

**The tradeoff to volunteer.** Typed cross-references are the real feature, and
they are worth friction on an API corpus of any size, because a reference to a
symbol that moved becomes a build failure instead of a dead link. They are not
worth it for a dozen conceptual pages, where the directive syntax is pure cost
and Markdown is the right answer.

**One sharper point.** docutils exits zero and renders its errors into the
published page. So an RST project without `-W` or an equivalent has probably
shipped visible error boxes at some point, and checking for `system-message` in
built output is a two-minute audit that tends to find something.

## How to prove it

**The artifact.** Less about a repository than about being able to answer the
migration question concretely, with the two-column table above.

**Three things to do, in order:**

1. Run the golden path. The docutils-versus-Sphinx comparison is the part
   nobody has actually executed.
2. Grep any built RST site you can reach for `system-message`. Published errors
   are more common than you would expect.
3. Take ten pages of an RST corpus and classify every directive and role into
   language or tool. That classification *is* the migration estimate.

**What makes it credible rather than decorative.** Neither of this guide's
repositories uses reStructuredText, which is recorded on the
[demonstrated](../demonstrated.md) page. What travels instead is the boundary
itself: being the person in the room who knows that `code-block` is not
reStructuredText is a small thing that reliably signals first-hand experience.

## Related

- [Sphinx](sphinx.md), the tool that supplies most of what people call RST
- [Markdown and its dialects](markdown.md), the comparison everyone wants
- [Generated API reference](api-reference-generation.md), what the Python domain is for
- [Single-sourcing](single-sourcing.md), which RST substitutions and includes do natively
