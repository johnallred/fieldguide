"""Tests for the fence structure gate.

The defect these cover shipped in this repository: seven pages whose golden
paths write Markdown with a heredoc had their outer code block closed early by
a bare fence inside the heredoc. The pages built cleanly and rendered wrongly,
with some samples demoted to prose and others dropped from the page entirely.

Each test below is written against a reconstruction of that exact shape rather
than against an abstraction of it, so a regression fails for the real reason.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from fieldguide.fences import (
    fence_findings,
    fence_spans,
    fenced_source_lines,
    heredoc_body_lines,
    rendered_code,
    unclosed_openers,
    unrendered_samples,
)

# The defect, minimised: a bash sample that writes a Markdown file containing
# its own fenced block. The inner bare ``` closes the outer ```bash.
BROKEN = textwrap.dedent(
    """\
    # Page

    ```bash
    cat > docs/good.md <<'EOF'
    # Rotate a key

    ```bash
    widget keys rotate
    ```
    EOF

    echo "this line is now prose"
    ```
    """
)

# The same sample, with the outer fence widened so it can contain the inner.
FIXED = BROKEN.replace("```bash\ncat >", "````bash\ncat >").replace(
    'echo "this line is now prose"\n```', 'echo "this line is now prose"\n````'
)


def write(tmp_path: Path, name: str, text: str) -> Path:
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def test_heredoc_body_is_data_not_markup() -> None:
    lines = BROKEN.splitlines()
    body = heredoc_body_lines(lines)
    # The inner ```bash and ``` live inside the heredoc, so they are shell data.
    assert lines[6].strip() == "```bash"
    assert 7 in body
    assert 9 in body
    # The outer fence is not.
    assert 3 not in body


def test_broken_nesting_is_reported(tmp_path: Path) -> None:
    findings = fence_findings(write(tmp_path, "broken.md", BROKEN))
    assert findings, "the early-closing inner fence must be reported"
    assert "closes it early" in findings[0]
    assert "````" in findings[0], "the finding must say how wide to make it"


def test_widened_fence_is_accepted(tmp_path: Path) -> None:
    assert fence_findings(write(tmp_path, "fixed.md", FIXED)) == []


def test_inner_fence_with_an_info_string_cannot_close(tmp_path: Path) -> None:
    """A closing fence carries no info string, so ```bash alone is harmless."""
    text = "```bash\ncat > a.md <<'EOF'\n```bash\nx\nEOF\n```\n"
    findings = fence_findings(write(tmp_path, "info.md", text))
    assert findings == []


def test_display_of_fence_markers_in_an_equal_width_wrapper_is_reported(
    tmp_path: Path,
) -> None:
    """The same mistake from the other side, which renders as empty blocks.

    A page that wants to *show* fence markers must wrap them in a wider fence.
    Wrapping them in an equal-width one is structurally legal and produces a
    run of empty code blocks with the real content stranded as prose, which
    neither the nesting check nor the render comparison can see.
    """
    text = "# P\n\n```\n```\nchain exit=1\n```\n```\n"
    findings = fence_findings(write(tmp_path, "display.md", text))
    assert len(findings) == 2, "both empty blocks should be reported"
    assert "empty code block" in findings[0]
    assert "````" in findings[0], "the finding must say how wide to make it"


def test_widened_wrapper_can_display_fence_markers(tmp_path: Path) -> None:
    text = "# P\n\n````text\n```\nchain exit=1\n```\n````\n"
    assert fence_findings(write(tmp_path, "display-ok.md", text)) == []


def test_unclosed_opener_is_reported(tmp_path: Path) -> None:
    findings = fence_findings(write(tmp_path, "open.md", "# P\n\n```python\nx = 1\n"))
    assert len(findings) == 1
    assert "never closed" in findings[0]


def test_spans_ignore_heredoc_markers() -> None:
    lines = FIXED.splitlines()
    spans = fence_spans(lines, heredoc_body_lines(lines))
    assert len(spans) == 1, "the heredoc's inner fences must not open a span"
    assert spans[0].ticks == "````"


def test_unclosed_openers_is_empty_for_balanced_input() -> None:
    lines = FIXED.splitlines()
    assert unclosed_openers(lines, heredoc_body_lines(lines)) == []


def test_rendered_code_unescapes_and_strips_tags(tmp_path: Path) -> None:
    page = write(
        tmp_path,
        "p.html",
        '<p>prose &amp; more</p><pre><code><span>pip</span> install &quot;x&gt;=2&quot;'
        "</code></pre>",
    )
    body = rendered_code(page)
    assert 'pip install "x>=2"' in body
    assert "prose & more" not in body, "only <pre> content counts as code"


def test_fenced_source_lines_skips_trivia(tmp_path: Path) -> None:
    text = "```python\nx\n# a comment that is long enough to assert on\n```\n"
    lines = fenced_source_lines(write(tmp_path, "t.md", text))
    texts = [t for _n, t in lines]
    assert "x" not in texts, "a one-character line collides by accident"
    assert any("long enough" in t for t in texts)


def test_unrendered_samples_catches_a_demoted_block(tmp_path: Path) -> None:
    """The dynamic half: source says code, the built page says prose."""
    docs, site = tmp_path / "docs", tmp_path / "site"
    docs.mkdir()
    (site / "guide").mkdir(parents=True)
    write(docs, "guide.md", "```bash\nwidget keys rotate --force\n```\n")
    # A page that rendered the sample as a paragraph rather than a <pre>.
    (site / "guide" / "index.html").write_text(
        "<p>widget keys rotate --force</p>", encoding="utf-8"
    )
    findings = unrendered_samples(docs, site)
    assert len(findings) == 1
    assert "not code on the built page" in findings[0]


def test_a_tab_in_a_sample_is_not_a_false_positive(tmp_path: Path) -> None:
    """The highlighter expands tabs; the comparison must not punish that.

    A literal tab is legitimate in a sample, and required in a Makefile
    recipe. Pygments writes it out as spaces to the next multiple of eight, so
    an exact byte comparison reported a Makefile line and a `du -sh` output
    line as missing from their own pages.
    """
    docs, site = tmp_path / "docs", tmp_path / "site"
    docs.mkdir()
    (site / "guide").mkdir(parents=True)
    write(docs, "guide.md", "```make\ncheck:\n\tmkdocs build --strict\n```\n")
    (site / "guide" / "index.html").write_text(
        "<pre><code>check:\n        mkdocs build --strict</code></pre>",
        encoding="utf-8",
    )
    assert unrendered_samples(docs, site) == []


def test_a_genuinely_missing_tabbed_line_is_still_caught(tmp_path: Path) -> None:
    """Expanding tabs must not blunt the check into uselessness."""
    docs, site = tmp_path / "docs", tmp_path / "site"
    docs.mkdir()
    (site / "guide").mkdir(parents=True)
    write(docs, "guide.md", "```make\ncheck:\n\tmkdocs build --strict\n```\n")
    (site / "guide" / "index.html").write_text(
        "<pre><code>check:</code></pre>", encoding="utf-8"
    )
    findings = unrendered_samples(docs, site)
    assert len(findings) == 1
    assert "mkdocs build --strict" in findings[0]


def test_unrendered_samples_passes_when_the_block_is_code(tmp_path: Path) -> None:
    docs, site = tmp_path / "docs", tmp_path / "site"
    docs.mkdir()
    (site / "guide").mkdir(parents=True)
    write(docs, "guide.md", "```bash\nwidget keys rotate --force\n```\n")
    (site / "guide" / "index.html").write_text(
        "<pre><code>widget keys rotate --force</code></pre>", encoding="utf-8"
    )
    assert unrendered_samples(docs, site) == []


@pytest.mark.parametrize("name", ["prompting", "chunking", "coding-agents"])
def test_real_pages_are_sound(name: str) -> None:
    """The pages that carried the defect stay fixed."""
    page = Path("docs") / "concepts" / f"{name}.md"
    if not page.exists():
        pytest.skip(f"{page} not present")
    assert fence_findings(page) == []
