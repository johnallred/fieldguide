"""Tests for the self-measurement behind `fieldguide audit`.

Every figure this module produces is quoted on a page, so a defect here
publishes a wrong number rather than raising. That has happened repeatedly in
this project, always the same way: a measurement of structured text that
treated it as lines. So the fixtures below are small and hand-counted, which is
the only check that catches this class.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from fieldguide.audit import audit, proof_tasks, prose_of, sentences
from fieldguide.registry import load_registry

REPO = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def real():
    registry = load_registry(REPO / "concepts.yaml")
    return audit(registry, REPO / "docs")


# ------------------------------------------------------- prose extraction


def test_front_matter_is_not_prose():
    text = "---\ntitle: X\nsummary: a b c d e\n---\n\nOne two three four.\n"
    assert prose_of(text).split() == ["One", "two", "three", "four."]


def test_a_fenced_block_is_not_prose():
    text = "Before here.\n\n```bash\nsudo rm everything important\n```\n\nAfter here.\n"
    words = prose_of(text).split()
    assert "sudo" not in words
    assert "Before" in words and "After" in words


def test_a_nested_fence_does_not_leak_shell_into_prose():
    """The bug this whole module is shaped around.

    A four-backtick block containing three-backtick blocks is what pages that
    document Markdown look like. A toggle closes on the inner marker and the
    rest of the block becomes prose, which once produced a 103-word
    "sentence" that was a shell session.
    """
    text = (
        "Intro sentence.\n\n"
        "````markdown\n"
        "```bash\n"
        "mkdir demo && cd demo\n"
        "```\n"
        "````\n\n"
        "Outro sentence.\n"
    )
    words = prose_of(text).split()
    assert "mkdir" not in words, "a nested fence leaked code into the prose"
    assert "Intro" in words and "Outro" in words


def test_a_heading_separates_sentences_rather_than_joining_them():
    text = "First one ends here\n\n## A heading\n\nSecond one starts here.\n"
    assert max(sentences(text)) < 8, "a heading joined two paragraphs"


def test_a_closing_quote_ends_a_sentence():
    """`."` was not an ending, which merged two sentences into an 86-word one."""
    text = 'He said "this is the end." Then a second sentence followed here.\n'
    assert len(sentences(text)) == 2


def test_tables_and_list_items_are_not_sentences():
    text = "| a | b |\n|---|---|\n| one | two |\n\n- a bullet item here\n\nReal prose here.\n"
    assert sentences(text) == [3]


# ------------------------------------------------------------ proof tasks


def test_proof_tasks_are_found_and_stripped_of_markup():
    text = (
        "## How to prove it\n\n"
        "**Three things to do today:**\n\n"
        "1. **Run** the thing and see.\n"
        "2. Measure [something](other.md) twice.\n"
        "3. Ask a person.\n\n"
        "**What makes it credible.** Not a task.\n\n"
        "## Related\n\n- [x](y.md)\n"
    )
    tasks = proof_tasks(text)
    assert len(tasks) == 3
    assert tasks[0].startswith("Run the thing")
    assert tasks[1] == "Measure something twice."


def test_a_quoted_heading_inside_a_fence_does_not_split_the_page():
    """`assessment.md` quotes `"## How to prove it"` in a Python sample.

    An unanchored search split that page at its own code sample and reported
    the page as having no proof section at all.
    """
    text = (
        "## The golden path\n\n"
        "```python\n"
        'section = text.partition("## How to prove it")[2]\n'
        "```\n\n"
        "## How to prove it\n\n"
        "**Three things to do today:**\n\n"
        "1. One task only.\n\n"
        "## Related\n\n- [x](y.md)\n"
    )
    assert proof_tasks(text) == ["One task only."]


# -------------------------------------------------- against the real corpus


def test_the_audit_runs_against_the_real_corpus(real):
    registry = load_registry(REPO / "concepts.yaml")
    assert real.pages == sum(1 for c in registry.concepts if c.status == "complete")
    assert real.sentence_words, "no prose was found in the corpus"
    assert real.tasks, "no proof tasks were found"


def test_every_structural_commitment_is_met(real):
    """The four commitments the instructional-design page claims."""
    assert real.commitments["prerequisites"] == real.needs_prerequisites
    for key in ("duration", "result", "proof", "related"):
        assert real.commitments[key] == real.pages, f"{key} is not universal"


def test_every_page_offers_exactly_three_proof_tasks(real):
    assert len(real.tasks) == real.pages * 3


def test_the_naive_fence_toggle_agrees_in_aggregate_and_is_still_wrong(real):
    """The finding on the python-for-content page, asserted.

    The toggle is within a fraction of a per cent of the parser across the
    whole corpus, which is why a sum is the worst instrument for finding a
    parsing bug.
    """
    toggled = real.word_counts["code removed, toggled"]
    parsed = real.word_counts["code and furniture removed"]
    assert toggled > parsed
    assert (toggled - parsed) / parsed < 0.01


def test_the_report_renders(real):
    text = real.render()
    assert "corpus:" in text and "proof tasks" in text
    assert str(real.pages) in text
