"""Tests for the generated views and the page scaffold.

The views are the pages a reader trusts most, because an index looks
authoritative. That makes their failure modes expensive, and most of them are
silent: a link to a page that does not exist, a coverage row ticked for a
concept with no prose, a path page that renders in the wrong order.

The one test here that earns its keep more than the others is
`test_no_generated_page_links_to_a_nonexistent_page`. An earlier version of
`_link` was open-coded in five places and three of them forgot to check
whether the target existed, which produced a strict build full of dead
cross-references. A property test over every generated page catches that class
of mistake rather than the one instance of it.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from fieldguide.generate import (
    coverage_page,
    path_page,
    paths_index_page,
    placeholder_page,
    study_plan_page,
)
from fieldguide.registry import REQUIRED_SECTIONS, load_registry
from fieldguide.scaffold import ScaffoldError, new_concept_page, render_concept_page

REPO = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def registry():
    return load_registry(REPO / "concepts.yaml")


# A two-concept registry whose concepts are both `planned` and both inside a
# path. Placeholder behaviour used to be tested only against the real registry,
# which meant the tests skipped themselves as the curriculum filled in: by the
# time 97 of 106 concepts were written, "no planned concept is in a path" was
# true and two tests silently stopped testing anything. Coverage that decays as
# the project succeeds is worse than no coverage, because the green run looks
# identical either way.
SYNTHETIC = """
categories:
  ia: Information architecture
concepts:
  - id: alpha
    name: Alpha
    category: ia
    tier: core
    difficulty: 1
    time: 1h
    prerequisites: []
    demanded_by:
      - source: nvidia
        provenance: quoted
        quote: "we need alpha for the thing"
    status: planned
  - id: beta
    name: Beta
    category: ia
    tier: supporting
    difficulty: 2
    time: 2h
    prerequisites: [alpha]
    demanded_by:
      - source: intel
        provenance: derived
        quote: "beta follows from alpha"
    status: planned
paths:
  - id: short
    name: Short path
    audience: Anyone.
    summary: Two steps.
    concepts: [alpha, beta]
"""


@pytest.fixture(scope="module")
def planned_registry(tmp_path_factory):
    """A registry that always has a planned concept inside a path."""
    root = tmp_path_factory.mktemp("synthetic")
    path = root / "concepts.yaml"
    path.write_text(SYNTHETIC, encoding="utf-8")
    return load_registry(path)


def all_generated(registry) -> dict[str, str]:
    """Every generated page, keyed by its path relative to the docs root."""
    pages = {
        "coverage.md": coverage_page(registry),
        "study-plan.md": study_plan_page(registry),
        "paths/index.md": paths_index_page(registry),
    }
    for learning_path in registry.paths:
        pages[f"paths/{learning_path.id}.md"] = path_page(registry, learning_path.id)
    for concept in registry.concepts:
        if concept.status == "planned":
            pages[f"concepts/{concept.id}.md"] = placeholder_page(registry, concept.id)
    return pages


# --------------------------------------------------------------- the banner


@pytest.mark.parametrize("page", ["coverage.md", "study-plan.md", "paths/index.md"])
def test_generated_pages_warn_that_they_are_generated(registry, page):
    """A contributor who edits one by hand loses the work, so they get told first."""
    assert "Generated page" in all_generated(registry)[page]


def test_every_generated_page_carries_the_banner(registry):
    for name, text in all_generated(registry).items():
        assert "Generated page" in text, f"{name} has no generated-page banner"


# ---------------------------------------------------------------- the links


def test_no_generated_page_links_to_a_nonexistent_page(registry):
    """The regression test for the dead-cross-reference bug.

    Resolves every relative Markdown link in every generated page against the
    real docs tree. This is the check `mkdocs build --strict` performs, done
    here so the failure names the generator rather than the output.
    """
    docs = REPO / "docs"
    broken: list[str] = []
    for name, text in all_generated(registry).items():
        source_dir = (docs / name).parent
        for target in re.findall(r"\]\((?!https?://)([^)#]+?)(?:#[^)]*)?\)", text):
            if not (source_dir / target).resolve().exists():
                broken.append(f"{name} -> {target}")
    assert not broken, "dead links in generated pages:\n  " + "\n  ".join(broken)


def test_a_planned_concept_is_linked_and_marked(planned_registry):
    """A placeholder is navigable, and the reader knows before clicking."""
    planned = [c for c in planned_registry.concepts if c.status == "planned"]
    assert planned, "the synthetic registry must hold a planned concept"
    text = coverage_page(planned_registry)
    concept = planned[0]
    assert f"concepts/{concept.id}.md" in text
    assert "*(outline)*" in text


def test_a_written_concept_is_linked_without_a_marker(registry):
    written = [c for c in registry.concepts if c.status != "planned"]
    if not written:
        pytest.skip("nothing is written yet")
    text = coverage_page(registry)
    concept = written[0]
    assert f"[{concept.name}](concepts/{concept.id}.md)" in text


# ------------------------------------------------------------------ coverage


def test_coverage_counts_match_the_registry(registry):
    counts = registry.completion
    text = coverage_page(registry)
    assert f"**{counts['complete']} of {len(registry.concepts)} concepts written.**" in text


def test_coverage_lists_every_concept(registry):
    text = coverage_page(registry)
    for concept in registry.concepts:
        assert concept.name in text, f"{concept.id} missing from coverage"


def test_coverage_lists_every_category_that_has_concepts(registry):
    text = coverage_page(registry)
    for key, label in registry.categories.items():
        if registry.in_category(key):
            assert f"## {label}" in text


def test_coverage_prints_the_provenance_of_every_row(registry):
    """The guide's credibility rests on this being visible, not aggregated away."""
    text = coverage_page(registry)
    for concept in registry.concepts:
        demand = concept.demanded_by[0]
        assert f"*{demand.source}, {demand.provenance}:*" in text


def test_coverage_escapes_pipes_so_the_table_survives(registry):
    """A quote containing a pipe would otherwise split a table cell."""
    text = coverage_page(registry)
    for line in text.splitlines():
        if line.startswith("| [") or line.startswith("| "):
            continue
    assert "\\|" in text or not any("|" in d.quote for c in registry.concepts for d in c.demanded_by)


def test_coverage_states_the_page_contract(registry):
    text = coverage_page(registry)
    for section in REQUIRED_SECTIONS:
        assert section in text


# --------------------------------------------------------------------- paths


def test_every_path_renders_its_concepts_in_registry_order(registry):
    for learning_path in registry.paths:
        text = path_page(registry, learning_path.id)
        positions = [
            text.index(f"## {i}. ") for i in range(1, len(learning_path.concepts) + 1)
        ]
        assert positions == sorted(positions), f"{learning_path.id} renders out of order"


def test_a_path_page_numbers_every_step(registry):
    learning_path = registry.paths[0]
    text = path_page(registry, learning_path.id)
    assert f"## {len(learning_path.concepts)}. " in text


def test_path_steps_do_not_skip_a_heading_level(registry):
    """Steps are `##`, directly under the page's `#` title.

    An accessibility pass over the built site found all seven path pages
    jumping h1 to h3, because the steps were `###` and nothing ever emitted an
    `##`. Screen reader users navigate by heading level, so the jump reads as a
    missing section rather than a numbered step.
    """
    for learning_path in registry.paths:
        text = path_page(registry, learning_path.id)
        levels = [
            len(line) - len(line.lstrip("#"))
            for line in text.splitlines()
            if line.startswith("#")
        ]
        assert levels, f"{learning_path.id} has no headings"
        assert levels[0] == 1, f"{learning_path.id} must open with an h1"
        for first, second in zip(levels, levels[1:]):
            assert second <= first + 1, (
                f"{learning_path.id} skips from h{first} to h{second}"
            )


def test_a_path_page_distinguishes_internal_from_external_prerequisites(registry):
    """"Builds on" means earlier in this path; "Assumes" means go read it first."""
    by_id = registry.by_id
    for learning_path in registry.paths:
        text = path_page(registry, learning_path.id)
        has_external = any(
            p not in learning_path.concepts
            for cid in learning_path.concepts
            for p in by_id[cid].prerequisites
        )
        if has_external:
            assert "Assumes, from outside this path" in text
            return
    pytest.skip("no path has an external prerequisite")


def test_a_path_page_states_its_entry_state_before_step_1(registry):
    """A reader deciding whether to commit forty hours needs it stated once, up front.

    Each step already discloses what it assumes, but that is scattered through
    the page and only readable after the decision to start has been made.
    """
    by_id = registry.by_id
    checked = 0
    for learning_path in registry.paths:
        assumed = {
            p
            for cid in learning_path.concepts
            for p in by_id[cid].prerequisites
            if p not in learning_path.concepts
        }
        if not assumed:
            continue
        checked += 1
        text = path_page(registry, learning_path.id)
        head, _, _ = text.partition("## 1. ")
        assert "**Assumed before step 1.**" in head
        for concept_id in assumed:
            assert f"({by_id[concept_id].page.replace('concepts/', '../concepts/')})" in head
    assert checked, "no path has an external prerequisite"


def test_the_paths_index_links_every_path(registry):
    text = paths_index_page(registry)
    for learning_path in registry.paths:
        assert f"]({learning_path.id}.md)" in text


def test_the_paths_index_reports_shared_concepts(registry):
    """A concept in several paths is load-bearing, and worth surfacing."""
    counts: dict[str, int] = {}
    for learning_path in registry.paths:
        for cid in learning_path.concepts:
            counts[cid] = counts.get(cid, 0) + 1
    if not any(n >= 3 for n in counts.values()):
        pytest.skip("no concept appears in three paths")
    assert "What every path shares" in paths_index_page(registry)


# ---------------------------------------------------------------- study plan


def test_the_study_plan_respects_prerequisites(registry):
    """The mechanical ordering must never put a concept before a dependency."""
    text = study_plan_page(registry)
    table = text.split("## Everything")[1]
    order = re.findall(r"^\| \d+ \| (?:\[)?([^\]|]+?)(?:\]\([^)]*\))? \|", table, re.M)
    index = {name.strip(): i for i, name in enumerate(order)}
    by_id = registry.by_id
    for concept in registry.concepts:
        for prerequisite in concept.prerequisites:
            before = index.get(by_id[prerequisite].name)
            after = index.get(concept.name)
            if before is None or after is None:
                continue
            assert before < after, (
                f"{concept.name} listed before its prerequisite "
                f"{by_id[prerequisite].name}"
            )


def test_the_study_plan_core_section_only_lists_core(registry):
    text = study_plan_page(registry)
    core_block = text.split("## Core only")[1].split("## Everything")[0]
    for concept in registry.of_tier("supporting") + registry.of_tier("context"):
        assert f" {concept.name} ·" not in core_block


# -------------------------------------------------------------- placeholders


def test_a_placeholder_carries_the_posting_quote(planned_registry):
    planned = [c for c in planned_registry.concepts if c.status == "planned"]
    assert planned, "the synthetic registry must hold a planned concept"
    concept = planned[0]
    text = placeholder_page(planned_registry, concept.id)
    assert concept.demanded_by[0].quote[:40] in text
    assert "Outline only" in text


def test_a_placeholder_lists_the_paths_that_include_it(planned_registry):
    checked = 0
    for learning_path in planned_registry.paths:
        for cid in learning_path.concepts:
            if planned_registry.by_id[cid].status == "planned":
                assert learning_path.name in placeholder_page(planned_registry, cid)
                checked += 1
    assert checked, "the synthetic registry must hold a planned concept in a path"


def test_a_placeholder_does_not_fake_the_page_contract(planned_registry):
    """It must not look finished. The contract sections are named, not used."""
    planned = [c for c in planned_registry.concepts if c.status == "planned"]
    assert planned, "the synthetic registry must hold a planned concept"
    text = placeholder_page(planned_registry, planned[0].id)
    for section in REQUIRED_SECTIONS:
        assert f"## {section}" not in text


# ------------------------------------------------------------------ scaffold


def test_the_scaffold_emits_every_required_section_in_order(registry):
    text = render_concept_page(registry, registry.concepts[0].id)
    positions = [text.index(f"## {s}") for s in REQUIRED_SECTIONS]
    assert positions == sorted(positions)


def test_the_scaffold_fills_in_what_the_registry_already_knows(registry):
    concept = next(c for c in registry.concepts if c.prerequisites and c.has_evidence)
    text = render_concept_page(registry, concept.id)
    assert f"title: {concept.name}" in text
    assert f"concept: {concept.id}" in text
    assert concept.tier in text
    # One label for one structural element. The corpus carried both
    # "Read first" and "Prerequisites" for this, depending on whether a
    # page was scaffolded or hand-written, which reads as incoherence.
    assert "**Prerequisites:**" in text
    assert "Read first" not in text
    assert concept.demanded_by[0].quote[:30] in text


def test_the_scaffold_refuses_a_concept_not_in_the_registry(registry):
    """A page with no concept is an orphan, which `check` rejects. Refuse early."""
    with pytest.raises(ScaffoldError, match="not in the registry"):
        render_concept_page(registry, "quantum-blockchain-synergy")


def test_the_scaffold_will_not_overwrite_an_existing_page(registry):
    written = next(c for c in registry.concepts if c.status == "complete")
    with pytest.raises(ScaffoldError, match="already exists"):
        new_concept_page(registry, REPO / "docs", written.id)


def test_the_scaffold_marks_a_derived_claim_as_not_a_quotation(registry):
    concept = next(c for c in registry.concepts if not c.has_evidence)
    text = render_concept_page(registry, concept.id)
    assert "Not a quotation" in text


def test_the_scaffold_quotes_verbatim_claims_as_blockquotes(registry):
    concept = next(c for c in registry.concepts if c.has_evidence)
    text = render_concept_page(registry, concept.id)
    assert "posting, verbatim" in text


# ------------------------------------------------------- the demonstration map


@pytest.fixture(scope="module")
def demos(registry):
    from fieldguide.demos import load_demonstrations

    return load_demonstrations(REPO / "demonstrations.yaml", registry)


def test_every_demonstration_names_a_real_concept(registry, demos):
    """The likeliest failure as the curriculum changes, and the worst one.

    A stale concept id silently under-reports what is implemented, which is the
    opposite of the error the page exists to prevent.
    """
    known = set(registry.by_id)
    for entry in demos.entries:
        assert entry.concept in known, f"{entry.concept} is not a concept"


def test_an_unknown_concept_in_the_map_is_rejected(registry, tmp_path):
    from fieldguide.demos import DemonstrationError, load_demonstrations

    path = tmp_path / "demos.yaml"
    path.write_text(
        "projects:\n"
        "  x:\n"
        "    name: X\n"
        "    tagline: T\n"
        "    summary: S\n"
        "    url: https://example.test\n"
        "demonstrates:\n"
        "  - concept: not-a-real-concept\n"
        "    project: x\n"
        "    artifact: a.py\n"
        "    extent: full\n"
        "    note: n\n",
        encoding="utf-8",
    )
    with pytest.raises(DemonstrationError, match="not a concept in the registry"):
        load_demonstrations(path, registry)


def test_an_unknown_project_key_is_rejected(registry, tmp_path):
    from fieldguide.demos import DemonstrationError, load_demonstrations

    path = tmp_path / "demos.yaml"
    path.write_text(
        "projects:\n"
        "  x:\n"
        "    name: X\n"
        "    tagline: T\n"
        "    summary: S\n"
        "    url: https://example.test\n"
        "demonstrates:\n"
        f"  - concept: {registry.concepts[0].id}\n"
        "    project: nope\n"
        "    artifact: a.py\n"
        "    extent: full\n"
        "    note: n\n",
        encoding="utf-8",
    )
    with pytest.raises(DemonstrationError, match="unknown project"):
        load_demonstrations(path, registry)


def test_a_bad_extent_is_rejected(registry, tmp_path):
    from fieldguide.demos import DemonstrationError, load_demonstrations

    path = tmp_path / "demos.yaml"
    path.write_text(
        "projects:\n"
        "  x:\n"
        "    name: X\n"
        "    tagline: T\n"
        "    summary: S\n"
        "    url: https://example.test\n"
        "demonstrates:\n"
        f"  - concept: {registry.concepts[0].id}\n"
        "    project: x\n"
        "    artifact: a.py\n"
        "    extent: sort-of\n"
        "    note: n\n",
        encoding="utf-8",
    )
    with pytest.raises(DemonstrationError, match="extent must be one of"):
        load_demonstrations(path, registry)


def test_every_demonstration_names_a_specific_artifact(registry, demos):
    """"See the repository" is not a demonstration. A path a reader can open is."""
    for entry in demos.entries:
        assert entry.artifact, f"{entry.concept} has no artifact"
        assert entry.artifact.strip() != "", entry.concept
        assert "/" in entry.artifact or "." in entry.artifact, (
            f"{entry.concept} artifact {entry.artifact!r} is not a path or file"
        )


def test_every_demonstration_explains_itself(registry, demos):
    for entry in demos.entries:
        assert len(entry.note.split()) >= 5, f"{entry.concept} note is too thin"


def test_the_demonstrated_page_publishes_the_gaps_as_well(registry, demos):
    """Publishing only the overlap would be the flattering half of the truth."""
    from fieldguide.generate import demonstrated_page

    text = demonstrated_page(registry, demos)
    assert "## What is not demonstrated" in text
    core_gaps = [
        c for c in registry.concepts
        if c.tier == "core" and not demos.covers(c.id)
    ]
    assert f"Every core concept with no demonstration ({len(core_gaps)})" in text

    # The explanation of the gaps is derived from the triage, not written. An
    # earlier version of this test asserted the heading "Why four categories
    # are at zero", which pinned a measured count inside prose: the count fell
    # to one and both the page and the test were wrong together.
    assert "### Why the gaps are there" in text
    for concept in core_gaps:
        assert demos.triage[concept.id] in text, (
            f"{concept.id} appears as a gap with no reason beside it"
        )
    for concept in core_gaps:
        assert concept.name in text, f"{concept.id} missing from the gap table"


def test_the_demonstrated_page_counts_match_the_map(registry, demos):
    from fieldguide.generate import demonstrated_page

    text = demonstrated_page(registry, demos)
    # Both numbers count distinct CONCEPTS, because the sentence reads
    # "N of 106 concepts have a demonstration, M of them in full". Counting
    # entries was indistinguishable from this until a concept gained a second
    # demonstration in a second repository, and then it over-reported.
    covered = len({d.concept for d in demos.entries})
    full = len({d.concept for d in demos.entries if d.is_full})
    assert f"**{covered} of {len(registry.concepts)} concepts have a demonstration**" in text
    assert f"{full} of them in full" in text


def test_demonstration_counts_never_exceed_the_concepts_they_describe(
    registry, demos
):
    """A concept demonstrated twice must not be counted twice.

    This is the regression guard for the bug above: entries outnumber concepts
    as soon as any concept is implemented in more than one repository, so any
    count phrased as "of them" has to deduplicate.
    """
    from fieldguide.generate import demonstrated_page

    covered = len({d.concept for d in demos.entries})
    full = len({d.concept for d in demos.entries if d.is_full})
    full_entries = sum(1 for d in demos.entries if d.is_full)

    assert full <= covered <= len(registry.concepts)

    text = demonstrated_page(registry, demos)
    if full_entries > full:
        # Duplicates exist, so the two candidate numbers differ and the page
        # must publish the deduplicated one.
        assert f"{full} of them in full" in text
        assert f"{full_entries} of them in full" not in text


def test_the_demonstrated_page_names_its_actual_sources(registry, demos):
    """Its banner must not claim a single source when it has two."""
    from fieldguide.generate import demonstrated_page

    text = demonstrated_page(registry, demos)
    assert "demonstrations.yaml" in text
    assert "concepts.yaml" in text
