---
title: Accessibility checks
summary: Automating the subset of accessibility a machine can judge, on the built HTML rather than the source.
diataxis: how-to
audience: developer
concept: accessibility
tags: [qa, supporting]
---

# Accessibility checks

`supporting` · difficulty 2 · 3h

!!! note "Not a quotation (adjacent)"
    Neither posting mentions accessibility. It is here because published
    documentation at either company is subject to it regardless, and because
    the automatable part costs an afternoon.

**Prerequisites:** [Documentation CI](documentation-ci.md)

## What it is

A CI gate over the **built HTML** that catches the mechanically detectable
accessibility defects: images without alternative text, heading levels that
skip, link text that means nothing out of context, tables with no header cells,
a page with no declared language.

The emphasis on built HTML matters. Accessibility is a property of what the
browser receives, and a Markdown source file cannot tell you whether your
theme emitted a `lang` attribute or what heading level a generated page landed
on.

## Why the job asks for it

It does not, and this page says so in its own banner. It is on the curriculum
for two reasons.

The first is that documentation at a large company is published content subject
to the same obligations as the rest of the site, whether or not a job posting
mentions it. Nobody writes "must not ship inaccessible pages" in a requisition,
and everybody expects it.

The second is that the automatable subset overlaps almost exactly with things
that are *also* correctness problems for other readers. A heading structure
that skips levels breaks screen reader navigation, and it also breaks your
table of contents, your [chunking](chunking.md) for retrieval, and any tool
that infers document structure from headings. Alternative text is what a
retrieval system indexes for an image. The accessibility fix and the
machine-readability fix are frequently the same fix, which is the honest
argument for doing it even where it is not asked for.

## The golden path

Write five checks, run them over a real site, and fix what they find. About
thirty minutes. This one found a genuine defect in this guide.

**Step 1: the checks**

Operating on built HTML with BeautifulSoup, scoped to the content region so the
theme's own chrome is not under test:

```python
# a11y.py
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup

VAGUE = {"click here", "here", "read more", "this", "link", "more"}


def audit(site: Path) -> dict[str, list[str]]:
    issues: dict[str, list[str]] = {}
    for page in sorted(site.rglob("index.html")):
        soup = BeautifulSoup(page.read_text(encoding="utf-8"), "html.parser")
        main = soup.find("article") or soup

        for img in main.find_all("img"):
            if not img.get("alt"):
                issues.setdefault("img-no-alt", []).append(str(page))

        levels = [int(h.name[1]) for h in main.find_all(re.compile(r"^h[1-6]$"))]
        for first, second in zip(levels, levels[1:]):
            if second > first + 1:
                issues.setdefault("heading-skip", []).append(
                    f"{page} (h{first}->h{second})")
                break

        for link in main.find_all("a"):
            if link.get_text(strip=True).lower() in VAGUE:
                issues.setdefault("vague-link-text", []).append(
                    f"{page}: {link.get_text(strip=True)!r}")

        for table in main.find_all("table"):
            if not table.find("th"):
                issues.setdefault("table-no-header", []).append(str(page))

        if not soup.find("html", attrs={"lang": True}):
            issues.setdefault("no-lang", []).append(str(page))
    return issues


if __name__ == "__main__":
    found = audit(Path(sys.argv[1] if len(sys.argv) > 1 else "site"))
    for name, hits in sorted(found.items(), key=lambda kv: -len(kv[1])):
        print(f"  {name:18} {len(hits):4}   e.g. {hits[0][:78]}")
    print(f"{'FAIL' if found else 'ok'}: {sum(len(v) for v in found.values())} issue(s)")
    raise SystemExit(1 if found else 0)
```

**Step 2: run it over this guide's own site**

```bash
mkdocs build -q
python3 a11y.py site
```

One run, when the built site held 121 pages. The counts move as pages are
added; the ratio between theme defects and content defects is the finding and
does not.

```
pages scanned: 121
  heading-skip          7   e.g. site/paths/content-architect/index.html (h1->h3)
```

Seven pages. No missing alt text, no vague links, every table has headers,
every page declares a language, because the theme handles those. One real
defect, in content this guide generates itself.

**Step 3: look at what it found**

```
paths/content-architect   h1->h3
    h1: 'The content architect'
    h3: '1. Information architecture'
```

Every learning path page jumps straight from its title to an `h3`. The
generator emitted `### 1. Concept` for each step and never emitted an `h2` at
all, so there is no second level for the third to sit under.

A sighted reader does not notice: the steps look like a numbered list of
sections. A screen reader user navigating by heading hears a jump from level
one to level three, which conventionally means a section was skipped, and has
to work out whether they missed something.

**Step 4: fix the generator, not the pages**

```python
# in path_page(), one character
out.append(f"## {position}. {_link(concept, '../concepts/')}\n")
```

```bash
fieldguide build && mkdocs build -q && python3 a11y.py site
```

```
heading-skip pages after the fix: 0
```

Two unit tests failed on that change, because they asserted `### 1. `. They
were right to fail, and updating them is part of the fix. A third test now
asserts the property rather than the string:

```python
def test_path_steps_do_not_skip_a_heading_level(registry):
    for learning_path in registry.paths:
        levels = [...]
        assert levels[0] == 1
        for first, second in zip(levels, levels[1:]):
            assert second <= first + 1
```

Asserting the property means the next person who changes the heading level for
a good reason gets told about the consequence, rather than being blocked by a
test that hardcoded the old answer.

**What you built.** A gate over the built site, and a generated corpus with a
heading structure a screen reader can navigate.

## Reference

### What automation can and cannot judge

| Machine-checkable | Needs a human |
|---|---|
| Missing `alt` attribute | Whether the alt text is *useful* |
| Heading levels skipping | Whether the heading structure reflects meaning |
| Link text from a vague list | Whether link text makes sense in context |
| Colour contrast ratios | Whether colour is the only carrier of meaning |
| Missing form labels | Whether the reading order is sensible |
| No `lang` attribute | Whether a diagram's content is available another way |

Automated tools are usually reckoned to cover something like a third of
accessibility criteria. Treat the gate as a floor that stops regressions, never
as a claim of compliance, and say so in that order when asked.

### Where the defects come from in a docs site

| Source | Typical defect | Fix lives in |
|---|---|---|
| The theme | Contrast, focus states, landmarks, `lang` | Theme config or an override |
| Generated pages | Heading structure, as above | The generator |
| Authors | Missing alt text, vague link text | A lint rule and review |
| Diagrams and screenshots | No text alternative | Authoring guidance, and a check that flags images with no alt |
| Code samples | Nothing much; `<pre>` is fine | Not a concern |

Scoping the audit to the content region rather than the whole page keeps theme
defects out of your authors' failure reports. Audit the theme once, separately,
and fix it upstream.

### The checks worth having, in order of value

| Check | Why first |
|---|---|
| Heading structure | Breaks navigation, chunking and the table of contents at once |
| Image alternative text | The only text a retriever has for an image |
| Link text | Screen reader users often navigate by a list of links alone |
| Table headers | Without `th`, a data table is an unlabelled grid |
| `lang` attribute | One line, changes pronunciation for every page |

The first two pay for themselves outside accessibility, which is what makes
them easy to get funded.

### Tools, when you can install them

`axe-core`, `pa11y` and `lighthouse` cover far more than the five checks above
and should be preferred where the environment allows. The hand-rolled version
earns its place in two situations: a build environment with no Node available,
and a defect class specific to your own generated output, which is exactly the
case here. A general tool would have found the heading skip too; writing it
yourself is how you learn which of its findings matter.

## How to talk about it

**Lead with the overlap, not the obligation.** "The automatable subset of
accessibility overlaps almost exactly with machine readability. Heading
structure that skips levels breaks screen reader navigation and also breaks
chunking for retrieval; alt text is the only thing a retriever can index for an
image. So I run it as a CI gate on the built HTML, and the same fixes improve
both."

**The follow-up is whether this means the site is accessible**, and the only
honest answer is no. Automated checks cover roughly a third of the criteria.
Say that number, say the gate is a regression floor, and say that a real
assessment involves assistive technology and users.

**The tradeoff to volunteer.** The checks run on built HTML, which means they
need a build before they can run, and they report against built paths rather
than source lines. An author gets a failure pointing at
`site/paths/content-architect/index.html` and has to work out that the cause is
a generator template. That indirection is the cost of auditing the artifact
that actually reaches the reader, and it is worth paying, but it needs a
mapping back to source to be usable at scale.

**One sharper point.** Scope the audit to the content region. A gate that
reports theme defects on every page in the corpus tells your authors that
accessibility is
a wall of noise they cannot fix, and it will be switched off. Audit the theme
once, fix it upstream, and let the recurring gate cover only what authors and
generators control.

## How to prove it

**The artifact.** A CI step that audits built HTML, plus a commit where it
caught something and the fix went into a generator or template rather than into
individual pages.

**Three things to do, in order:**

1. Run the golden path over a docs site you own. Heading skips are extremely
   common in generated content and nobody is looking.
2. When it finds something, fix it where it is generated. A fix applied to
   output is a fix that regresses.
3. Convert the finding into a property test rather than a string assertion, so
   the next change is informed rather than blocked.

**What makes it credible rather than decorative.** Neither of this guide's
repositories demonstrated accessibility checking before this page was written,
which is recorded on the [demonstrated](../demonstrated.md) page. What exists
now is better evidence than a tool in a workflow file: a check that found seven
real defects in generated output, a one-character fix in the generator, two
unit tests that correctly failed, and a property test so it cannot come back.

## Related

- [Documentation CI](documentation-ci.md), where this gate runs
- [Chunking](chunking.md), which depends on the same heading structure
- [Markdown and its dialects](markdown.md), where heading levels are authored
- [Preview deployments and publishing](preview-deployments.md), the built artifact under audit
