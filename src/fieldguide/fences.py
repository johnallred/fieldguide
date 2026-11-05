"""Fence structure checks for pages whose samples write Markdown.

Several golden paths in this guide are shell sessions that write a Markdown
file with a heredoc, and the file being written contains its own fenced code
block. Markdown has no idea it is looking at shell input. By CommonMark rules a
closing fence is the same character, at least as long as the opener, and
carries no info string, so the bare ``` *inside* the heredoc closes the outer
block early. Everything after it renders as prose, and some of it is dropped
from the page entirely.

Nothing else in this repository catches that. The tests pass, `fieldguide
check` passes, and `mkdocs build --strict` exits 0, because the build did
succeed. The page is simply wrong. This module is the gate for that class,
and it has two halves:

``fence_findings``
    Static. Reads the Markdown, models heredoc bodies as data rather than
    markup, and reports a span whose opener is not wide enough to contain the
    fences inside it.

``unrendered_samples``
    Dynamic, and the one that cannot be fooled. Compares fenced source lines
    against the ``<pre>`` content of the built page. Verified in both
    directions on this corpus: 127 findings before the fix, 0 after, over the
    same 4,394 fenced lines.

The static half exists for fast feedback; the dynamic half is the truth.
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from pathlib import Path

MARKER = re.compile(r"^(?P<indent> {0,3})(?P<ticks>`{3,}|~{3,})(?P<info>.*)$")
HEREDOC = re.compile(r"<<-?\s*'?(?P<word>[A-Za-z_][A-Za-z0-9_]*)'?\s*$")
PRE = re.compile(r"<pre\b.*?</pre>", re.S)
TAG = re.compile(r"<[^>]+>")
INTERESTING = re.compile(r"[A-Za-z0-9]{3,}")

# A source line short enough to collide by accident is not worth asserting on.
MIN_ASSERTABLE = 12


@dataclass(frozen=True)
class Span:
    """A fence block, by 1-indexed line numbers, with its opener's marker."""

    open_line: int
    close_line: int
    ticks: str


def heredoc_body_lines(lines: list[str]) -> set[int]:
    """1-indexed line numbers that are heredoc body, so data and not markup.

    >>> sorted(heredoc_body_lines(["cat > a.md <<'EOF'", "x", "EOF", "y"]))
    [2]
    """
    body: set[int] = set()
    index, total = 0, len(lines)
    while index < total:
        match = HEREDOC.search(lines[index])
        if not match:
            index += 1
            continue
        word = match.group("word")
        cursor = index + 1
        while cursor < total and lines[cursor].strip() != word:
            body.add(cursor + 1)
            cursor += 1
        index = cursor + 1
    return body


def fence_spans(lines: list[str], skip: set[int] | None = None) -> list[Span]:
    """Closed fence blocks, ignoring markers that are really heredoc data.

    >>> spans = fence_spans(["```py", "code", "```"])
    >>> (spans[0].open_line, spans[0].close_line, spans[0].ticks)
    (1, 3, '```')
    """
    skip = skip or set()
    spans: list[Span] = []
    open_line, open_ticks = None, ""
    for number, line in enumerate(lines, 1):
        if number in skip:
            continue
        match = MARKER.match(line)
        if not match:
            continue
        ticks, info = match.group("ticks"), match.group("info").strip()
        if open_line is None:
            open_line, open_ticks = number, ticks
        elif ticks[0] == open_ticks[0] and len(ticks) >= len(open_ticks) and not info:
            spans.append(Span(open_line, number, open_ticks))
            open_line, open_ticks = None, ""
    return spans


def unclosed_openers(lines: list[str], skip: set[int] | None = None) -> list[int]:
    """Line numbers of fences that are opened and never closed.

    >>> unclosed_openers(["```py", "code"])
    [1]
    >>> unclosed_openers(["```py", "code", "```"])
    []
    """
    skip = skip or set()
    spans = fence_spans(lines, skip)
    closed = {n for span in spans for n in (span.open_line, span.close_line)}
    inside = {n for span in spans for n in range(span.open_line, span.close_line + 1)}
    return [
        number
        for number, line in enumerate(lines, 1)
        if number not in skip
        and number not in inside
        and number not in closed
        and MARKER.match(line)
    ]


def fence_findings(path: Path) -> list[str]:
    """Report fence structure that will render wrongly.

    The defect condition is precise: inside a span whose opener is N
    characters, a heredoc-data marker that is bare and at least N characters
    long will close that span early. A heredoc-data marker carrying an info
    string cannot close anything, so it is harmless on its own.
    """
    lines = path.read_text(encoding="utf-8").splitlines()
    skip = heredoc_body_lines(lines)
    findings: list[str] = []

    for number in unclosed_openers(lines, skip):
        findings.append(f"{path}:{number}: fence opened here is never closed")

    for span in fence_spans(lines, skip):
        width = len(span.ticks)
        for number in range(span.open_line + 1, span.close_line):
            if number not in skip:
                continue
            match = MARKER.match(lines[number - 1])
            if not match:
                continue
            inner, info = match.group("ticks"), match.group("info").strip()
            if not info and len(inner) >= width:
                findings.append(
                    f"{path}:{number}: a bare {len(inner)}-character fence inside the "
                    f"{width}-character block opened at line {span.open_line} closes it "
                    f"early; widen the opener and its closer to "
                    f"{'`' * (len(inner) + 1)}"
                )

    # An empty code block is almost always the same mistake seen from the other
    # side: a page meant to *display* fence markers wrapped them in a fence of
    # equal width, so the parser produced a run of empty blocks with the real
    # content stranded as prose between them. That is structurally legal, which
    # is why neither the check above nor the render comparison notices it. The
    # author of this module made the mistake three times in one day.
    for span in fence_spans(lines, skip):
        body = [
            line
            for line in lines[span.open_line : span.close_line - 1]
            if line.strip()
        ]
        if not body:
            findings.append(
                f"{path}:{span.open_line}: empty code block; if this was meant to "
                f"display fence markers, widen the wrapper to "
                f"{'`' * (len(span.ticks) + 1)}"
            )
    return findings


def fenced_source_lines(path: Path) -> list[tuple[int, str]]:
    """Fenced lines worth asserting on, as (line number, text)."""
    lines = path.read_text(encoding="utf-8").splitlines()
    skip = heredoc_body_lines(lines)
    out: list[tuple[int, str]] = []
    for span in fence_spans(lines, skip):
        for number in range(span.open_line + 1, span.close_line):
            text = lines[number - 1].strip()
            if (
                len(text) >= MIN_ASSERTABLE
                and INTERESTING.search(text)
                and not MARKER.match(text)
            ):
                out.append((number, text))
    return out


def rendered_code(html_path: Path) -> str:
    """The text content of every ``<pre>`` on a built page.

    >>> import tempfile, pathlib
    >>> d = pathlib.Path(tempfile.mkdtemp())
    >>> _ = (d / "p.html").write_text("<p>no</p><pre><code>a &gt; b</code></pre>")
    >>> rendered_code(d / "p.html")
    'a > b'
    """
    raw = html_path.read_text(encoding="utf-8")
    blocks = [TAG.sub("", block) for block in PRE.findall(raw)]
    return html.unescape("\n".join(blocks))


#: Tab stop the highlighter expands to. Pygments writes a tab out as spaces to
#: the next multiple of eight, so a source line containing a literal tab never
#: matches the rendered line byte for byte. Tabs in samples are legitimate (a
#: Makefile recipe requires one), so the comparison expands both sides rather
#: than rejecting the line.
TAB_SIZE = 8


def unrendered_samples(docs: Path, site: Path) -> list[str]:
    """Fenced source lines that did not survive into a ``<pre>`` on the page."""
    findings: list[str] = []
    for page in sorted(docs.rglob("*.md")):
        relative = page.relative_to(docs).with_suffix("")
        built = site / relative / "index.html"
        if relative.name == "index":
            built = site / relative.parent / "index.html"
        if not built.exists():
            continue
        body = rendered_code(built).expandtabs(TAB_SIZE)
        for number, text in fenced_source_lines(page):
            if text.expandtabs(TAB_SIZE) not in body:
                findings.append(
                    f"{page}:{number}: fenced line is not code on the built "
                    f"page: {text[:58]!r}"
                )
    return findings
