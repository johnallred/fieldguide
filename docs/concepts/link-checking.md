---
title: Link checking
summary: Failing the build on a dead cross-reference, including the anchors a strict build ignores.
diataxis: how-to
audience: developer
concept: link-checking
tags: [qa, core]
---

# Link checking

`core` · difficulty 1 · 2h

!!! quote "Asked for by name"
    Intel: "documentation CI, including link checking and coldstart testing of quickstarts"

**Prerequisites:** [Docs-as-code](docs-as-code.md)

## What it is

A build-time check that every cross-reference in the corpus resolves: internal
page links, heading anchors, and, separately and more awkwardly, external URLs.
A dead link becomes a failed pull request rather than a reader's dead end.

The reason it gets its own page rather than one line in
[documentation CI](documentation-ci.md) is that almost everyone implements the
easy half, ships it, and believes the problem is solved. The easy half is
missing files. The half that rots a corpus is missing anchors.

## Why the job asks for it

Intel names it directly. It is the cheapest gate in this entire category,
which is why it is difficulty 1 and why it is usually the first thing added
after a strict build.

The reason it matters more than its difficulty suggests is that deep links are
the links people actually use. An engineer sends a colleague
`configure.md#retry-behaviour`, not `configure.md`. Then someone rewords that
heading from "Retry behaviour" to "Retries and backoff" in an unrelated pull
request, and every deep link to it dies silently. The page is still there. The
build is still green. The link lands at the top of the page, and the reader has
to guess which of forty sections was meant.

Renaming a heading is the most common way a documentation site breaks its own
internal links, and it is invisible to every check that only looks for missing
files.

## The golden path

Prove that a strict build is not a link checker, then build the checker that
closes the gap. About twenty-five minutes.

**Step 1: a site with two defects, one of each kind**

````bash
mkdir -p linkcheck-demo/docs && cd linkcheck-demo
printf 'site_name: Link demo\ndocs_dir: docs\n' > mkdocs.yml

cat > docs/index.md <<'EOF'
# Home

Read the [install guide](install.md) first.
Then see [configuration options](install.md#configuration-options).
Then see [the tuning section](install.md#tuning).
And the [old FAQ](faq.md).
EOF

cat > docs/install.md <<'EOF'
# Install

## Configuration options

Set the values you need.
EOF
````

There are two dead references. `faq.md` does not exist. `install.md#tuning`
does not exist either, because `install.md` has no Tuning heading.

**Step 2: watch a strict build catch one and ignore the other**

```bash
mkdocs build --strict
```

```
WARNING - Doc file 'index.md' contains a link 'faq.md', but the target is not
          found among documentation files.
INFO    - Doc file 'index.md' contains a link 'install.md#tuning', but the doc
          'install.md' does not contain an anchor '#tuning'.
Aborted with 1 warnings in strict mode!
```

Read those two lines carefully. The missing **file** is a `WARNING`, and
`--strict` turns warnings into errors, so the build fails. The missing
**anchor** is an `INFO`. It is not a warning, so `--strict` does nothing with
it.

Remove only the missing-file link and build again:

````bash
cat > docs/index.md <<'EOF'
# Home

Read the [install guide](install.md) first.
Then see [configuration options](install.md#configuration-options).
Then see [the tuning section](install.md#tuning).
EOF

mkdocs build --strict
echo "exit=$?"
````

```
INFO    - Doc file 'index.md' contains a link 'install.md#tuning', but the doc
          'install.md' does not contain an anchor '#tuning'.
INFO    - Documentation built in 0.05 seconds
exit=0
```

Exit 0. The build passed. Now look at what it published:

```bash
grep -o 'href="install/#tuning"' site/index.html
grep -c 'id="tuning"' site/install/index.html
```

The dead anchor is in the shipped HTML, and there is no `id="tuning"` anywhere
in the page it points at. A strict build will ship that every day of the week.
This is the gap the rest of the page closes.

**Step 3: write the checker**

The useful version is about sixty lines, because it has to do two things MkDocs
does not: resolve anchors against the heading slugs a page actually generates,
and ignore link-shaped text inside code samples.

```python
# check_links.py
import re
import sys
import unicodedata
from pathlib import Path

LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
FENCE = re.compile(r"^\s*(```|~~~)")


def strip_fences(text):
    """Blank out fenced code, preserving line numbers so reports stay honest."""
    out, in_fence = [], False
    for line in text.splitlines():
        if FENCE.match(line):
            in_fence = not in_fence
            out.append("")
        else:
            out.append("" if in_fence else line)
    return "\n".join(out)


def slugify(title):
    text = unicodedata.normalize("NFKD", title)
    text = re.sub(r"[`*_\[\]()]", "", text)
    text = re.sub(r"[^\w\s-]", "", text).strip().lower()
    return re.sub(r"\s+", "-", text)


def anchors_of(path):
    body = strip_fences(path.read_text(encoding="utf-8"))
    return {slugify(m.group(2)) for line in body.splitlines()
            if (m := HEADING.match(line))}


def check(root):
    pages = sorted(root.rglob("*.md"))
    # Keyed by RESOLVED path, because link targets are resolved below.
    anchors = {p.resolve(): anchors_of(p) for p in pages}
    problems = []
    for page in pages:
        body = strip_fences(page.read_text(encoding="utf-8"))
        for n, line in enumerate(body.splitlines(), 1):
            for target in LINK.findall(line):
                if target.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                file_part, _, anchor = target.partition("#")
                dest = (page.parent / file_part).resolve()
                if dest.suffix != ".md":
                    continue
                if not dest.exists():
                    problems.append(f"{page}:{n}: missing file '{file_part}'")
                elif anchor:
                    # Three states, not two. See the note below.
                    if dest not in anchors:
                        anchors[dest] = anchors_of(dest)
                    if anchor not in anchors[dest]:
                        problems.append(
                            f"{page}:{n}: '{file_part}' has no anchor '#{anchor}'")
    return problems


if __name__ == "__main__":
    found = check(Path(sys.argv[1] if len(sys.argv) > 1 else "docs"))
    for p in found:
        print(f"LINK  {p}")
    print(f"{'FAIL' if found else 'ok'}: {len(found)} problem(s)")
    raise SystemExit(1 if found else 0)
```

```bash
python3 check_links.py docs/
```

```
LINK  docs/index.md:5: 'install.md' has no anchor '#tuning'
FAIL: 1 problem(s)
```

One finding, which is the real defect, on the corpus a strict build had just
declared clean.

**Step 4: fix it and confirm green**

```bash
printf '\n## Tuning\n\nAdjust as needed.\n' >> docs/install.md
python3 check_links.py docs/
echo "exit=$?"
```

```
ok: 0 problem(s)
exit=0
```

**What you built.** A gate that catches the failure mode a strict build is
structurally blind to. Add it as a separate CI step rather than folding it into
the build, so a dead anchor and a broken build are two different red lights.

## Reference

### What each tool actually covers

| Check | Missing page | Missing anchor | Fenced false positive | External URL |
|---|---|---|---|---|
| `mkdocs build --strict` | Fails | Logs `INFO`, ships it | Avoided | No |
| The script above | Fails | Fails | Avoided | No |
| `lychee`, `linkchecker` | Fails | Fails | Varies | Yes |
| `htmlproofer` (post-build) | Fails | Fails | Not applicable, reads HTML | Yes |

Checking rendered HTML instead of Markdown source is a legitimate alternative
and gets anchors right for free, because by then the `id` attributes exist. The
tradeoff is that failures report against built paths rather than source lines,
so the author has to translate back.

### The three states of a link target

This is the part that bites, and it bit the author of this page while writing
it. A target is not valid or invalid. It is valid, invalid, or **unknown**,
where unknown means the target exists but sits outside the tree you scanned.

| Collapse unknown into | You get | Consequence |
|---|---|---|
| Invalid | False positives | Noise, then someone turns the check off |
| Valid | False negatives | Silence, and the check is theater |

The first version of the script above keyed its anchor cache by relative path
and looked it up by resolved path, so every lookup missed. Because the default
was an empty set, *every anchor in the corpus* was reported dead. That was the
lucky failure, because it was loud. Had the default been "assume valid", the
same bug would have reported a clean corpus forever and nobody would have
looked.

A checker's unknown case must fail loudly or be handled explicitly. Never let
it default to passing.

### Why external links are a separate decision

| Property | Internal | External |
|---|---|---|
| Deterministic | Yes | No |
| Needs network | No | Yes |
| Can fail on someone else's outage | No | Yes |
| Belongs in a blocking gate | Yes | Usually not |

Blocking a pull request because a third-party site returned 503 teaches people
to re-run CI until it passes, which destroys the gate's credibility for the
internal checks too. Run external checks on a schedule, open an issue, and keep
them out of the merge path.

## How to talk about it

**Lead with the anchor gap**, because it is the part that shows you have run
this rather than read about it. "A strict MkDocs build fails on a missing page
but only logs an `INFO` for a missing heading anchor, so it ships dead deep
links. Renaming a heading is the most common way a site breaks its own links,
and it is exactly the case the build cannot see."

**The follow-up is usually about external links.** The answer that signals
experience is that you deliberately do not gate merges on them, and why:
non-determinism in a required check trains people to retry until green.

**The tradeoff to volunteer.** Slug generation is tool-specific. Your checker
reimplements the slug rules of your static site generator, and if those rules
drift your checker produces false reports. The honest mitigation is to
unit-test `slugify` against real headings from your own corpus. The better
long-term answer is to check rendered HTML, where the `id` attributes are
already decided.

**One sharper point.** The right failure granularity is the source line. A
report that says the site has a broken link is a chore; a report that says
`configure.md:84` points at an anchor that no longer exists is a fix. That is
why the script blanks fenced lines rather than deleting them: line numbers stay
true.

## How to prove it

**The artifact.** A repository with link checking as its own CI step, plus a
commit where that step caught something.

**Three things to do, in order:**

1. Run the golden path. Twenty-five minutes, and you will have personally
   watched a strict build publish a dead anchor.
2. Point the script at a docs site you already have. On any corpus more than a
   few months old it will find something, and the first finding is the argument
   you will use in the interview.
3. Write one unit test for `slugify` using the ugliest real heading in your
   corpus, something with backticks and punctuation. That test is what makes
   the checker trustworthy rather than approximately right.

**What makes it credible rather than decorative.** Anchors. A link checker that
only resolves file paths reimplements something the build already does. Being
able to say "mine catches renamed headings, and here is the pull request where
it did" is the whole difference.

## Related

- [Documentation CI](documentation-ci.md), where this becomes a gate
- [Code-sample validation](code-sample-validation.md), the same idea applied to examples instead of links
- [Writing custom linters](custom-linters.md), for when the rule you need does not exist yet
