"""Catch Markdown syntax this site's configuration cannot render.

Markdown is a family of dialects, not a format. CommonMark supports none of
tables, definition lists, strikethrough, footnotes or task lists; every one of
those is an extension, and implementations disagree about which they ship. The
consequence that matters here is the failure mode: unsupported syntax does not
raise an error. It is passed through as literal text, so `~~struck~~` reaches
the reader with the tildes still attached.

That is the same class of defect as the fence bug in `fences.py`, seen from a
different angle, and it needs the same remedy: compare the source against the
built HTML rather than reasoning about the source alone. A construct whose
markers survive verbatim into the output did not render.

This check is deliberately narrow. It tests a short list of constructs that are
easy to write by habit and are not enabled in this project's `mkdocs.yml`,
rather than trying to model every dialect.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from .fences import fence_spans, heredoc_body_lines
from .registry import DIATAXIS

#: Constructs that are plausible to type and that leave recognisable litter in
#: the output when the extension enabling them is absent. Each entry is a
#: source pattern plus a function that finds its unrendered remains in HTML.
CONSTRUCTS: dict[str, tuple[re.Pattern[str], re.Pattern[str]]] = {
    "strikethrough": (
        re.compile(r"~~(?P<inner>[^~\n]+)~~"),
        re.compile(r"~~[^~\n]+~~"),
    ),
    "task list": (
        re.compile(r"^\s*[-*]\s+\[(?P<inner>[ xX])\]\s"),
        re.compile(r"<li[^>]*>\s*\[[ xX]\]\s"),
    ),
}


#: Inline code spans, longest delimiter first so ``a`b`` is not split wrongly.
INLINE_CODE = re.compile(r"(?P<ticks>`+)(?P<body>.+?)(?P=ticks)")


def _strip_inline_code(line: str) -> str:
    """Blank out inline code spans, preserving length.

    Writing `` `~~struck~~` `` is displaying the syntax on purpose, not failing
    to render it, and the rendered HTML contains those characters either way.
    Only unquoted prose is evidence of a dialect mistake.

    >>> _strip_inline_code("say `~~x~~` here")
    'say         here'
    >>> len(_strip_inline_code("say `~~x~~` here")) == len("say `~~x~~` here")
    True
    """
    return INLINE_CODE.sub(lambda m: " " * len(m.group(0)), line)


def _prose_lines(path: Path) -> list[tuple[int, str]]:
    """Source lines outside code fences and outside inline code."""
    lines = path.read_text(encoding="utf-8").splitlines()
    spans = fence_spans(lines, heredoc_body_lines(lines))
    inside = {n for s in spans for n in range(s.open_line, s.close_line + 1)}
    return [
        (n, _strip_inline_code(line))
        for n, line in enumerate(lines, 1)
        if n not in inside
    ]


FRONT_MATTER = re.compile(r"^---\n(?P<body>.*?)\n---\n", re.S)


def front_matter_findings(docs: Path) -> list[str]:
    """Pages whose front matter is not valid YAML.

    MkDocs' metadata parser is more forgiving than YAML, so a page with an
    unquoted colon in a value builds cleanly and is unreadable to anything
    using a real YAML parser. This project shipped 46 such pages: the
    placeholder generator wrote ``summary: Outline only: <name> ...`` with
    f-strings, the colon started a mapping, and the meta description on every
    one of them silently fell back to the site default.

    Front matter is the machine-readable half of a page. A corpus that cannot
    be parsed is a corpus that cannot be filtered, chunked or retrieved, which
    makes this the cheapest AI-readiness check there is.
    """
    out: list[str] = []
    for page in sorted(docs.rglob("*.md")):
        match = FRONT_MATTER.match(page.read_text(encoding="utf-8"))
        if not match:
            continue
        try:
            data = yaml.safe_load(match.group("body"))
        except yaml.YAMLError as error:
            detail = str(error).splitlines()[0][:70]
            out.append(f"{page}: front matter is not valid YAML: {detail}")
            continue

        # Validate the one closed vocabulary that lives in front matter rather
        # than in the registry. Until this check existed, nothing read the
        # field, so a generator hardcoding one value went unnoticed across 53
        # pages. A vocabulary nobody checks is a vocabulary that is already
        # wrong.
        if isinstance(data, dict) and "diataxis" in data:
            value = data["diataxis"]
            if value not in DIATAXIS:
                out.append(
                    f"{page}: diataxis is {value!r}, which is not one of "
                    f"{list(DIATAXIS)}"
                )
    return out


def findings(docs: Path, site: Path) -> list[str]:
    """Constructs used in source whose markers survive into the built HTML.

    Reported only when both halves agree: the construct appears in the prose of
    a source page, and its litter appears in that page's rendered output. One
    without the other is not evidence, which keeps this from firing on a page
    that merely discusses the syntax inside a code sample.
    """
    out: list[str] = []
    for page in sorted(docs.rglob("*.md")):
        relative = page.relative_to(docs).with_suffix("")
        built = site / relative / "index.html"
        if relative.name == "index":
            built = site / relative.parent / "index.html"
        if not built.exists():
            continue
        html = built.read_text(encoding="utf-8")
        prose = _prose_lines(page)
        for name, (source_pattern, litter_pattern) in CONSTRUCTS.items():
            if not litter_pattern.search(html):
                continue
            for number, line in prose:
                if source_pattern.search(line):
                    out.append(
                        f"{page}:{number}: {name} is not enabled in this "
                        f"configuration, so it reaches the reader as literal "
                        f"text: {line.strip()[:48]!r}"
                    )
    return out
