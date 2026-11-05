"""The criterion classifier, scored against a hand-labelled known answer.

This is the discipline the `assessment` page argues for and this guide had not
applied to its own weakest number. An audit script has the same defect profile
as the corpus it measures, so the only way to trust one is to score it against
a sample somebody labelled by hand, against a written definition, before the
script existed.

The number that came out of not doing that was 17 per cent, published as the
guide's worst figure. The classifier behind it was a keyword list containing
`against`, which matches "run it against a corpus you own" and states no
criterion at all, and it recognised none of the conditionals, predicted values
or author comparisons the corpus actually uses. The real rate was about a
third.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from fieldguide.audit import CRITERION

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "criterion_labels.json"


@pytest.fixture(scope="module")
def labels() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_the_fixture_describes_its_own_method(labels):
    """A labelled set with no written definition is one person's opinion."""
    assert len(labels["definition"].split()) >= 30
    assert "falsifiable" in labels["definition"]
    assert "held-out" in labels["method"]


def test_the_fixture_is_big_enough_and_balanced_enough_to_score_against(labels):
    rows = [row for sample in labels["samples"].values() for row in sample]
    positives = sum(1 for row in rows if row["criterion"])
    assert len(rows) >= 60, "too few labelled tasks to say anything"
    assert 0.2 < positives / len(rows) < 0.8, (
        "a fixture this lopsided cannot distinguish a classifier from a "
        "constant answer"
    )


@pytest.mark.parametrize("sample", ["A-tuned-on", "B-held-out"])
def test_the_classifier_scores_well_on_the_labelled_tasks(labels, sample):
    """Recall must be perfect; precision is allowed to be imperfect.

    The asymmetry is deliberate. A missed criterion understates the corpus and
    hides work that is already done, which is the failure that produced the
    17 per cent figure. A false positive overstates it, which is worse in
    principle, so it is bounded rather than forbidden: the two it allows are
    "expected-source pairs" and "read them out loud", both of which contain a
    criterion word in a sentence that is not one.
    """
    rows = labels["samples"][sample]
    tp = sum(1 for r in rows if r["criterion"] and CRITERION.search(r["task"]))
    fp = sum(1 for r in rows if not r["criterion"] and CRITERION.search(r["task"]))
    fn = sum(1 for r in rows if r["criterion"] and not CRITERION.search(r["task"]))

    assert fn == 0, (
        f"{sample}: the classifier misses {fn} hand-labelled criteria, which "
        "understates the corpus:\n  "
        + "\n  ".join(
            r["task"][:100] for r in rows if r["criterion"] and not CRITERION.search(r["task"])
        )
    )
    precision = tp / (tp + fp) if tp + fp else 0.0
    assert precision >= 0.85, f"{sample}: precision {precision:.2f} is too low"


def test_the_classifier_rejects_the_preposition_that_broke_the_old_one():
    """The specific regression, named.

    `against` was 16 of the old classifier's 53 matches and a criterion in
    none of them.
    """
    assert not CRITERION.search("Run the golden path against a real corpus. Twenty pages is enough.")
    assert not CRITERION.search("Write the owner table. Four rows is enough.")
    assert CRITERION.search("Predict the number before you run it.")
    assert CRITERION.search("If the answer is two, you have the drift.")
    assert CRITERION.search("On a client-rendered site the number is near zero.")


def test_every_core_page_states_at_least_one_criterion():
    """The outcome of the pass, asserted so it cannot quietly reverse.

    Only `core` pages are held to this. A forced criterion is worse than none,
    which the `assessment` page says, so the nine remaining pages without one
    are `supporting` and `context` and stay on the backlog rather than getting
    a sentence written to satisfy a test.
    """
    from fieldguide.audit import TASK_ITEM, TASK_LABEL
    from fieldguide.registry import load_registry

    root = Path(__file__).resolve().parent.parent
    registry = load_registry(root / "concepts.yaml")

    missing = []
    for concept in registry.concepts:
        if concept.status != "complete" or concept.tier != "core":
            continue
        text = (root / "docs" / concept.page).read_text(encoding="utf-8")
        label = TASK_LABEL.search(text)
        assert label, f"{concept.id} has no proof-task label"
        tail = text[label.end() :].split("**What makes it")[0]
        tasks = [" ".join(m.group(1).split()) for m in TASK_ITEM.finditer(tail)]
        if not any(CRITERION.search(task) for task in tasks):
            missing.append(concept.id)

    assert not missing, f"core pages whose three tasks state no criterion: {missing}"
