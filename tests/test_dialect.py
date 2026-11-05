"""Tests for the Markdown dialect gate.

Markdown is a family of dialects. CommonMark supports none of tables,
definition lists, strikethrough, footnotes or task lists, and implementations
disagree about which extensions they ship. Unsupported syntax is not an error:
it is passed through as literal text, so `~~struck~~` reaches the reader with
the tildes attached.

These tests pin the two-sided rule that keeps the check honest. A finding needs
the construct in the source *and* its litter in the built HTML, so a page that
merely discusses the syntax inside a code sample does not fire it.
"""

from __future__ import annotations

from pathlib import Path

from fieldguide.dialect import FRONT_MATTER, findings, front_matter_findings


def build(tmp_path: Path, source: str, html: str) -> tuple[Path, Path]:
    """A one-page docs tree and a matching pretend build output."""
    docs, site = tmp_path / "docs", tmp_path / "site"
    docs.mkdir()
    (site / "page").mkdir(parents=True)
    (docs / "page.md").write_text(source, encoding="utf-8")
    (site / "page" / "index.html").write_text(html, encoding="utf-8")
    return docs, site


def test_strikethrough_that_survives_into_the_html_is_reported(tmp_path: Path) -> None:
    docs, site = build(
        tmp_path,
        "# P\n\nThis is ~~struck~~ text.\n",
        "<h1>P</h1><p>This is ~~struck~~ text.</p>",
    )
    found = findings(docs, site)
    assert len(found) == 1
    assert "strikethrough" in found[0]
    assert "literal" in found[0]


def test_strikethrough_that_rendered_is_not_reported(tmp_path: Path) -> None:
    """Same source, a configuration that supports it. Nothing to report."""
    docs, site = build(
        tmp_path,
        "# P\n\nThis is ~~struck~~ text.\n",
        "<h1>P</h1><p>This is <del>struck</del> text.</p>",
    )
    assert findings(docs, site) == []


def test_task_list_left_as_literal_brackets_is_reported(tmp_path: Path) -> None:
    docs, site = build(
        tmp_path,
        "# P\n\n- [ ] a task\n",
        "<h1>P</h1><ul><li>[ ] a task</li></ul>",
    )
    found = findings(docs, site)
    assert len(found) == 1
    assert "task list" in found[0]


def test_task_list_rendered_as_a_checkbox_is_not_reported(tmp_path: Path) -> None:
    docs, site = build(
        tmp_path,
        "# P\n\n- [ ] a task\n",
        '<h1>P</h1><ul><li><input type="checkbox" disabled> a task</li></ul>',
    )
    assert findings(docs, site) == []


def test_syntax_discussed_inside_a_code_fence_is_not_reported(tmp_path: Path) -> None:
    """A page explaining the syntax must not be flagged for using it.

    This is why the check reads source prose rather than the whole file: inside
    a fence, `~~struck~~` is an example, and the HTML will legitimately contain
    those characters.
    """
    docs, site = build(
        tmp_path,
        "# P\n\nSome dialects support this:\n\n```markdown\n~~struck~~\n```\n",
        "<h1>P</h1><pre><code>~~struck~~</code></pre>",
    )
    assert findings(docs, site) == []


def test_litter_in_html_without_the_source_construct_is_not_reported(
    tmp_path: Path,
) -> None:
    """Both halves must agree before anything is claimed."""
    docs, site = build(
        tmp_path,
        "# P\n\nOrdinary prose.\n",
        "<h1>P</h1><p>Ordinary prose.</p><p>~~from somewhere else~~</p>",
    )
    assert findings(docs, site) == []


def test_syntax_quoted_in_inline_code_is_not_reported(tmp_path: Path) -> None:
    """Showing the syntax on purpose is not a mistake.

    The page that explains this failure mode has to name `~~struck~~` in
    prose. Wrapped in backticks it is a deliberate display, and the HTML
    contains those characters either way, so only unquoted prose is evidence.
    """
    docs, site = build(
        tmp_path,
        "# P\n\nThe reader gets `~~struck~~` with the tildes attached.\n",
        "<h1>P</h1><p>The reader gets <code>~~struck~~</code> with the tildes.</p>",
    )
    assert findings(docs, site) == []


def test_unquoted_syntax_beside_a_quoted_mention_is_still_reported(
    tmp_path: Path,
) -> None:
    """Stripping inline code must not hide a real mistake on the same line."""
    docs, site = build(
        tmp_path,
        "# P\n\nWrite `~~this~~` but I typed ~~that~~ by mistake.\n",
        "<h1>P</h1><p>Write <code>~~this~~</code> but I typed ~~that~~.</p>",
    )
    found = findings(docs, site)
    assert len(found) == 1
    assert "strikethrough" in found[0]


def test_the_real_corpus_is_clean() -> None:
    """No page in this guide uses syntax its own configuration cannot render."""
    docs, site = Path("docs"), Path("site")
    if not site.exists():
        import pytest

        pytest.skip("site not built")
    assert findings(docs, site) == []


# ------------------------------------------------------- front matter as YAML


def test_unquoted_colon_in_front_matter_is_reported(tmp_path: Path) -> None:
    """The defect that shipped on 46 pages of this corpus.

    The placeholder generator assembled front matter with f-strings, so
    `summary: Outline only: <name> ...` put an unquoted colon in a value and
    started a mapping. MkDocs built it cleanly because its metadata parser is
    more forgiving than YAML, and the meta description on all 46 pages
    silently fell back to the site default.
    """
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "p.md").write_text(
        "---\ntitle: X\nsummary: Outline only: X is not written yet.\n---\n\n# X\n",
        encoding="utf-8",
    )
    found = front_matter_findings(docs)
    assert len(found) == 1
    assert "not valid YAML" in found[0]


def test_quoted_colon_in_front_matter_is_accepted(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "p.md").write_text(
        '---\ntitle: X\nsummary: "Outline only: X is not written yet."\n---\n\n# X\n',
        encoding="utf-8",
    )
    assert front_matter_findings(docs) == []


def test_a_page_with_no_front_matter_is_not_reported(tmp_path: Path) -> None:
    """Absent front matter is a content-model question, not a parse error."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "p.md").write_text("# X\n\nNo front matter at all.\n", encoding="utf-8")
    assert front_matter_findings(docs) == []


def test_the_real_corpus_front_matter_all_parses() -> None:
    docs = Path("docs")
    if not docs.exists():
        import pytest

        pytest.skip("docs tree not present")
    assert front_matter_findings(docs) == []


def test_a_diataxis_value_outside_the_vocabulary_is_reported(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "p.md").write_text(
        "---\ntitle: X\ndiataxis: refrence\n---\n\n# X\n", encoding="utf-8"
    )
    found = front_matter_findings(docs)
    assert len(found) == 1
    assert "not one of" in found[0]


def test_placeholder_is_a_legitimate_diataxis_value(tmp_path: Path) -> None:
    """A generated stub has no Diataxis type, and must not claim one.

    Every generated page in this repository declared `diataxis: reference`,
    hardcoded, so that value meant "not written yet" on 53 of 121 pages while
    no hand-written page used it. Nothing read the field, so nothing noticed.
    """
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "p.md").write_text(
        "---\ntitle: X\ndiataxis: placeholder\n---\n\n# X\n", encoding="utf-8"
    )
    assert front_matter_findings(docs) == []


def test_no_generated_page_claims_a_diataxis_type_it_has_not_earned() -> None:
    """Regression guard for the corpus itself."""
    import yaml

    docs = Path("docs")
    if not docs.exists():
        import pytest

        pytest.skip("docs tree not present")
    for page in sorted(docs.rglob("*.md")):
        match = FRONT_MATTER.match(page.read_text(encoding="utf-8"))
        if not match:
            continue
        data = yaml.safe_load(match.group("body")) or {}
        if data.get("generated"):
            assert data.get("diataxis") == "placeholder", (
                f"{page} is generated but claims diataxis={data.get('diataxis')!r}"
            )
