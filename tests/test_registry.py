"""Tests for the registry model and its validators.

The tests at the bottom run against the real `concepts.yaml`, which makes the
suite a gate on the curriculum itself and not only on the code that reads it.
A contributor who adds a concept with a dangling prerequisite, or reorders a
learning path so it teaches a dependency too late, fails these.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from fieldguide.registry import (
    MIN_COMPLETE_WORDS,
    PROVENANCE,
    REQUIRED_SECTIONS,
    STATUSES,
    TIERS,
    RegistryError,
    find_cycles,
    load_registry,
    topological_order,
    validate_against_tree,
)

REPO = Path(__file__).resolve().parent.parent
REAL_REGISTRY = REPO / "concepts.yaml"
REAL_DOCS = REPO / "docs"

MINIMAL = """
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
        quote: "we need alpha"
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


def write(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "concepts.yaml"
    path.write_text(body, encoding="utf-8")
    return path


def mutate(body: str, old: str, new: str) -> str:
    assert old in body, f"fixture does not contain {old!r}"
    return body.replace(old, new, 1)


# ----------------------------------------------------------------- happy path


def test_a_minimal_registry_loads(tmp_path):
    registry = load_registry(write(tmp_path, MINIMAL))
    assert [c.id for c in registry.concepts] == ["alpha", "beta"]
    assert registry.by_id["beta"].prerequisites == ("alpha",)
    assert registry.paths[0].concepts == ("alpha", "beta")


def test_page_path_is_derived_from_the_id(tmp_path):
    """The page location is not a field, so it cannot disagree with the id."""
    registry = load_registry(write(tmp_path, MINIMAL))
    assert registry.by_id["alpha"].page == "concepts/alpha.md"


def test_completion_counts_every_status(tmp_path):
    registry = load_registry(write(tmp_path, MINIMAL))
    assert registry.completion == {"planned": 2, "drafted": 0, "complete": 0}
    assert set(registry.completion) == set(STATUSES)


def test_in_category_puts_core_first(tmp_path):
    registry = load_registry(write(tmp_path, MINIMAL))
    assert [c.id for c in registry.in_category("ia")] == ["alpha", "beta"]


def test_is_evidence_is_true_only_for_a_quotation(tmp_path):
    registry = load_registry(write(tmp_path, MINIMAL))
    assert registry.by_id["alpha"].has_evidence
    assert not registry.by_id["beta"].has_evidence


# ------------------------------------------------------- closed vocabularies


@pytest.mark.parametrize(
    ("old", "new", "match"),
    [
        ("tier: core", "tier: essential", "tier must be one of"),
        ("status: planned\n  - id: beta", "status: shipped\n  - id: beta", "status must be one of"),
        ("difficulty: 1", "difficulty: 7", "difficulty must be one of"),
        ("provenance: quoted", "provenance: vibes", "provenance must be one of"),
        ("source: nvidia", "source: google", "source must be intel, nvidia or both"),
        ("category: ia\n    tier: core", "category: xx\n    tier: core", "unknown category"),
    ],
)
def test_values_outside_a_closed_vocabulary_are_rejected(tmp_path, old, new, match):
    with pytest.raises(RegistryError, match=match):
        load_registry(write(tmp_path, mutate(MINIMAL, old, new)))


def test_an_id_that_is_not_kebab_case_is_rejected(tmp_path):
    """Ids appear in URLs and cross-references, so casing drift is expensive."""
    with pytest.raises(RegistryError, match="kebab-case"):
        load_registry(write(tmp_path, mutate(MINIMAL, "id: alpha", "id: Alpha_One")))


def test_an_empty_quote_is_rejected(tmp_path):
    """A concept's claim on the reader IS the quote. Without one there is nothing to check."""
    with pytest.raises(RegistryError, match="quote must not be empty"):
        load_registry(write(tmp_path, mutate(MINIMAL, 'quote: "we need alpha"', 'quote: ""')))


def test_demanded_by_may_not_be_empty(tmp_path):
    body = MINIMAL.replace(
        """    demanded_by:
      - source: nvidia
        provenance: quoted
        quote: "we need alpha"
""",
        "    demanded_by: []\n",
    )
    with pytest.raises(RegistryError, match="non-empty list"):
        load_registry(write(tmp_path, body))


# ----------------------------------------------------------- reference checks


def test_a_dangling_prerequisite_is_rejected(tmp_path):
    with pytest.raises(RegistryError, match="prerequisite 'gamma' is not a concept"):
        load_registry(write(tmp_path, mutate(MINIMAL, "prerequisites: [alpha]", "prerequisites: [gamma]")))


def test_a_self_prerequisite_is_rejected(tmp_path):
    with pytest.raises(RegistryError, match="its own prerequisite"):
        load_registry(write(tmp_path, mutate(MINIMAL, "prerequisites: [alpha]", "prerequisites: [beta]")))


def test_a_duplicate_concept_id_is_rejected(tmp_path):
    with pytest.raises(RegistryError, match="duplicate concept id"):
        load_registry(write(tmp_path, mutate(MINIMAL, "id: beta", "id: alpha")))


def test_a_path_referencing_an_unknown_concept_is_rejected(tmp_path):
    with pytest.raises(RegistryError, match="'gamma' is not a concept"):
        load_registry(write(tmp_path, mutate(MINIMAL, "concepts: [alpha, beta]", "concepts: [alpha, gamma]")))


def test_a_path_listing_a_concept_twice_is_rejected(tmp_path):
    with pytest.raises(RegistryError, match="lists a concept twice"):
        load_registry(write(tmp_path, mutate(MINIMAL, "concepts: [alpha, beta]", "concepts: [alpha, alpha]")))


def test_a_one_step_path_is_rejected(tmp_path):
    """A path with one concept is a link, not a route."""
    with pytest.raises(RegistryError, match="at least two concepts"):
        load_registry(write(tmp_path, mutate(MINIMAL, "concepts: [alpha, beta]", "concepts: [alpha]")))


# ------------------------------------------------------------- the graph


def test_a_prerequisite_cycle_is_rejected(tmp_path):
    """A cycle leaves a reader with nowhere to start, so it fails the load."""
    body = mutate(MINIMAL, "    prerequisites: []", "    prerequisites: [beta]")
    with pytest.raises(RegistryError, match="prerequisite cycle"):
        load_registry(write(tmp_path, body))


def test_find_cycles_is_empty_on_a_valid_graph(tmp_path):
    assert find_cycles(load_registry(write(tmp_path, MINIMAL))) == []


def test_topological_order_never_puts_a_concept_before_a_prerequisite(tmp_path):
    registry = load_registry(write(tmp_path, MINIMAL))
    order = topological_order(registry)
    assert order.index("alpha") < order.index("beta")


def test_topological_order_covers_every_concept(tmp_path):
    registry = load_registry(write(tmp_path, MINIMAL))
    assert sorted(topological_order(registry)) == ["alpha", "beta"]


def test_topological_order_is_stable(tmp_path):
    registry = load_registry(write(tmp_path, MINIMAL))
    assert topological_order(registry) == topological_order(registry)


# -------------------------------------------------- checks against the tree


def good_page(title: str = "Alpha") -> str:
    body = [f"---\ntitle: {title}\n---\n\n# {title}\n"]
    for section in REQUIRED_SECTIONS:
        body.append(f"## {section}\n\n" + "filler words here. " * 40)
    return "\n".join(body)


def test_a_planned_concept_with_no_page_is_not_an_error(tmp_path):
    """`planned` is the whole point of the status field."""
    registry = load_registry(write(tmp_path, MINIMAL))
    findings = validate_against_tree(registry, tmp_path / "docs")
    assert findings.ok
    assert findings.missing_pages == []


def test_a_drafted_concept_with_no_page_is_an_error(tmp_path):
    body = mutate(MINIMAL, "status: planned", "status: drafted")
    registry = load_registry(write(tmp_path, body))
    findings = validate_against_tree(registry, tmp_path / "docs")
    assert not findings.ok
    assert findings.missing_pages == ["alpha"]


def test_a_page_with_no_concept_is_an_orphan(tmp_path):
    registry = load_registry(write(tmp_path, MINIMAL))
    docs = tmp_path / "docs" / "concepts"
    docs.mkdir(parents=True)
    (docs / "not-a-concept.md").write_text(good_page(), encoding="utf-8")
    findings = validate_against_tree(registry, tmp_path / "docs")
    assert findings.orphan_pages == ["concepts/not-a-concept.md"]
    assert not findings.ok


def test_a_missing_required_section_is_reported_by_name(tmp_path):
    body = mutate(MINIMAL, "status: planned", "status: drafted")
    registry = load_registry(write(tmp_path, body))
    docs = tmp_path / "docs" / "concepts"
    docs.mkdir(parents=True)
    page = good_page().replace("## The golden path", "## Something else")
    (docs / "alpha.md").write_text(page, encoding="utf-8")
    findings = validate_against_tree(registry, tmp_path / "docs")
    assert ("alpha", "The golden path") in findings.missing_sections


def test_sections_out_of_contract_order_are_reported(tmp_path):
    """The contract is an order, not a set: a reader learns the shape once."""
    body = mutate(MINIMAL, "status: planned", "status: drafted")
    registry = load_registry(write(tmp_path, body))
    docs = tmp_path / "docs" / "concepts"
    docs.mkdir(parents=True)
    reversed_sections = "\n".join(
        f"## {s}\n\nwords. " for s in reversed(REQUIRED_SECTIONS)
    )
    (docs / "alpha.md").write_text(f"# Alpha\n\n{reversed_sections}", encoding="utf-8")
    findings = validate_against_tree(registry, tmp_path / "docs")
    assert findings.out_of_order_sections
    assert not findings.ok


def test_a_complete_page_that_is_too_short_is_rejected(tmp_path):
    """`complete` is a claim, so it is checked rather than trusted."""
    body = mutate(MINIMAL, "status: planned", "status: complete")
    registry = load_registry(write(tmp_path, body))
    docs = tmp_path / "docs" / "concepts"
    docs.mkdir(parents=True)
    stub = "# Alpha\n\n" + "\n".join(f"## {s}\n\nTODO\n" for s in REQUIRED_SECTIONS)
    (docs / "alpha.md").write_text(stub, encoding="utf-8")
    findings = validate_against_tree(registry, tmp_path / "docs")
    assert findings.understuffed
    assert findings.understuffed[0][0] == "alpha"
    assert findings.understuffed[0][1] < MIN_COMPLETE_WORDS


def test_a_long_enough_complete_page_passes(tmp_path):
    body = mutate(MINIMAL, "status: planned", "status: complete")
    registry = load_registry(write(tmp_path, body))
    docs = tmp_path / "docs" / "concepts"
    docs.mkdir(parents=True)
    (docs / "alpha.md").write_text(good_page(), encoding="utf-8")
    findings = validate_against_tree(registry, tmp_path / "docs")
    assert findings.understuffed == []
    assert findings.ok


def test_a_path_that_teaches_a_prerequisite_too_late_is_reported(tmp_path):
    registry = load_registry(write(tmp_path, mutate(MINIMAL, "concepts: [alpha, beta]", "concepts: [beta, alpha]")))
    findings = validate_against_tree(registry, tmp_path / "docs")
    assert findings.path_order_violations
    assert "beta comes before its prerequisite alpha" in findings.path_order_violations[0]


def test_a_prerequisite_outside_the_path_is_not_a_violation(tmp_path):
    """A path is a route through a subset, not a closure over one.

    A curated path is allowed to assume a concept it does not teach, and the
    generated page says so under "Assumes, from outside this path". Only a
    prerequisite that the path *does* teach, but teaches too late, is wrong.
    """
    gamma = """  - id: gamma
    name: Gamma
    category: ia
    tier: supporting
    difficulty: 2
    time: 1h
    prerequisites: [beta]
    demanded_by:
      - source: both
        provenance: adjacent
        quote: "gamma needs beta"
    status: planned
"""
    # Insert into the concepts list rather than appending, which would land
    # inside the `paths:` block.
    body = mutate(MINIMAL, "paths:", gamma + "paths:")
    # `gamma` depends on `beta`, and this path teaches gamma without beta.
    body = mutate(body, "concepts: [alpha, beta]", "concepts: [alpha, gamma]")
    registry = load_registry(write(tmp_path, body))
    findings = validate_against_tree(registry, tmp_path / "docs")
    assert findings.path_order_violations == []
    assert findings.ok


def test_unsourced_concepts_are_advisory_not_a_failure(tmp_path):
    """A derived claim is weaker evidence, not an error. The report says so."""
    registry = load_registry(
        write(tmp_path, MINIMAL.replace("status: planned", "status: drafted"))
    )
    docs = tmp_path / "docs" / "concepts"
    docs.mkdir(parents=True)
    for cid in ("alpha", "beta"):
        (docs / f"{cid}.md").write_text(good_page(cid), encoding="utf-8")
    findings = validate_against_tree(registry, tmp_path / "docs")
    assert any(f.startswith("beta") for f in findings.unsourced)
    assert findings.ok


def test_the_report_renders_a_clean_result(tmp_path):
    registry = load_registry(write(tmp_path, MINIMAL))
    assert "ok:" in validate_against_tree(registry, tmp_path / "docs").render()


# --------------------------------------------------------- the real registry


def test_the_real_registry_loads():
    registry = load_registry(REAL_REGISTRY)
    assert len(registry.concepts) >= 60
    assert len(registry.paths) >= 5


def test_the_real_registry_agrees_with_the_docs_tree():
    findings = validate_against_tree(load_registry(REAL_REGISTRY), REAL_DOCS)
    assert findings.ok, "\n" + findings.render()


def test_every_tier_is_represented_in_the_real_registry():
    registry = load_registry(REAL_REGISTRY)
    for tier in TIERS:
        assert registry.of_tier(tier), f"no concepts in tier {tier!r}"


def test_every_category_in_the_real_registry_has_concepts():
    """An empty category is a heading with nothing under it."""
    registry = load_registry(REAL_REGISTRY)
    for key, label in registry.categories.items():
        assert registry.in_category(key), f"category {label!r} ({key}) is empty"


def test_most_of_the_real_registry_is_backed_by_a_quotation():
    """The guide's credibility rests on this ratio, so it is a test.

    Not all of it: `derived` and `adjacent` entries are legitimate, and the
    coverage page prints which is which. But if most of the curriculum rested
    on the author's opinion rather than on the postings, the framing would be
    dishonest.
    """
    registry = load_registry(REAL_REGISTRY)
    quoted = sum(1 for c in registry.concepts if c.has_evidence)
    assert quoted / len(registry.concepts) >= 0.4


def test_every_provenance_value_is_used():
    """If nothing is ever `adjacent`, the distinction is decoration."""
    registry = load_registry(REAL_REGISTRY)
    used = {d.provenance for c in registry.concepts for d in c.demanded_by}
    assert used == set(PROVENANCE)


def test_the_real_paths_only_reference_written_or_planned_concepts():
    registry = load_registry(REAL_REGISTRY)
    known = set(registry.by_id)
    for learning_path in registry.paths:
        assert set(learning_path.concepts) <= known


def test_a_finished_page_marked_planned_is_reported(tmp_path):
    """`planned` is a claim, and it can be false.

    Every status check ran in one direction until two pages of 1,793 and 1,627
    words, each with all six required sections, sat in the corpus marked
    planned. The coverage matrix reported them as "(outline)" and
    `fieldguide check` exited 0, so the index understated the corpus and
    nothing said so.
    """
    from fieldguide.registry import (
        MIN_COMPLETE_WORDS,
        REQUIRED_SECTIONS,
        load_registry,
        validate_against_tree,
    )

    docs = tmp_path / "docs"
    (docs / "concepts").mkdir(parents=True)
    reg = load_registry(write(tmp_path, MINIMAL))

    planned = next(c for c in reg.concepts if c.status == "planned")
    body = "\n\n".join(f"## {s}\n\n" + "word " * 100 for s in REQUIRED_SECTIONS)
    (docs / planned.page).write_text(
        f"---\ntitle: X\n---\n\n# X\n\n{body}\n", encoding="utf-8"
    )
    # every other page a placeholder, so only this one is interesting
    for c in reg.concepts:
        page = docs / c.page
        if not page.exists():
            page.write_text("---\ntitle: Y\ngenerated: true\n---\n\n# Y\n", encoding="utf-8")

    findings = validate_against_tree(reg, docs)
    ids = [cid for cid, _n in findings.understated]
    assert planned.id in ids
    assert not findings.ok
    words = dict(findings.understated)[planned.id]
    assert words >= MIN_COMPLETE_WORDS


def test_every_shipped_subcommand_is_documented_where_a_reader_looks():
    """"Each new capability ships with tested documentation", at capability granularity.

    Symbol-level gates get this wrong in both directions. Requiring a docstring
    on every public function flags the five CLI handlers, which are the
    best-documented part of the package because they are documented as
    commands. Requiring every public symbol to be named in the prose flags
    internal plumbing whose public-ness is an artifact of Python's module
    system. The unit that matters is the shipped capability, and the surface
    that matters is everywhere a reader actually looks, which includes the
    README: searching only docs/ reported `fieldguide status` as undocumented
    when the README's quick start had always listed it.
    """
    import re

    from fieldguide.cli import build_parser

    root = Path(__file__).resolve().parent.parent
    subcommands = sorted(
        next(
            action.choices
            for action in build_parser()._actions
            if getattr(action, "choices", None) and isinstance(action.choices, dict)
        )
    )
    assert subcommands, "the CLI parser exposes no subcommands"

    surfaces = [root / "README.md"] + sorted((root / "docs").rglob("*.md"))
    prose = "\n".join(p.read_text(encoding="utf-8") for p in surfaces if p.exists())

    undocumented = [s for s in subcommands if not re.search(rf"fieldguide {s}\b", prose)]
    assert not undocumented, f"shipped but undocumented: {', '.join(undocumented)}"


def test_every_written_page_ends_with_a_related_section():
    """`Related` is in the contract because a convention 105 pages kept was not.

    The page contract enforced six named sections and a word count, and a
    seventh section that every page but one carried was a convention. The one
    page without it also ended mid-sentence, which is the connected point: a
    contract that checks for the presence of headings cannot tell whether the
    prose between them finishes.
    """
    import re

    root = Path(__file__).resolve().parent.parent
    registry = load_registry(root / "concepts.yaml")
    docs = root / "docs"

    missing, truncated = [], []
    for concept in registry.concepts:
        if concept.status != "complete":
            continue
        text = (docs / concept.page).read_text(encoding="utf-8")
        if not re.search(r"^## Related$", text, re.M):
            missing.append(concept.id)
        # A page ends with its Related list, so the last non-empty line is a
        # bullet. A prose line there means the page was cut off mid-section.
        last = [line for line in text.splitlines() if line.strip()][-1]
        if not last.lstrip().startswith(("-", "*", "|")):
            truncated.append((concept.id, last[-40:]))

    assert not missing, f"no Related section: {', '.join(missing)}"
    assert not truncated, f"page does not end on a list item: {truncated}"


def test_pages_that_state_the_corpus_size_state_it_correctly():
    """A page's own count of the corpus goes stale every time the corpus grows.

    This is the defect that survived longest in this project. Several pages
    said "this guide's own 82 written pages" in their credibility section, true
    when written and not reproducible by anyone who cloned the repository
    later, because the corpus reached 106. The historical figures inside a
    golden path are fine and are labelled as such; a present-tense claim about
    the corpus is not.

    Two denominators are legitimately in use, so both are accepted: the number
    of concepts, and the number of Markdown files under docs/.
    """
    import re

    root = Path(__file__).resolve().parent.parent
    registry = load_registry(root / "concepts.yaml")
    docs = root / "docs"

    concepts = len(registry.concepts)
    markdown_files = len(list(docs.rglob("*.md")))
    allowed = {concepts, markdown_files}

    claim = re.compile(r"this guide's own (\d+)(?: written)? pages")
    wrong = []
    for page in sorted(docs.rglob("*.md")):
        for match in claim.finditer(page.read_text(encoding="utf-8")):
            if int(match.group(1)) not in allowed:
                wrong.append((page.relative_to(docs).as_posix(), match.group(1)))

    assert not wrong, (
        "stale corpus-size claim; the corpus is %d concepts across %d files: %s"
        % (concepts, markdown_files, wrong)
    )

    # The phrase above was the only shape checked, and three pages drifted
    # past it while the tree reached 123: "all 121 pages", "a 121-page
    # corpus", "111 of 121 pages". Those are fixed, and this adds the one
    # further phrasing that can be checked without guessing.
    #
    # `prose_of` is what makes the rule workable: a figure inside a quoted
    # golden-path run is a record of one run and stays as printed, while a
    # sentence in prose is a present-tense claim and has to be true now.
    #
    # Two broader arms were tried and removed. "all N pages" and "of N pages"
    # match subset counts just as well as corpus counts, so they flagged
    # "the site default on all 46 pages" and a hypothetical 400-page corpus in
    # an interview answer, and the only way to keep them was a magnitude floor
    # chosen to exclude the inconvenient hits. That is the same mistake as the
    # frequency floor in the label sweep, so the arms are gone and the
    # limitation is written here: a stale subset-shaped count will not be
    # caught by this check, and the three it did catch were worth the trip.
    from fieldguide.audit import prose_of

    # The lookbehind matters: without it, "a 5,000-page corpus" on the
    # embeddings page matched as "000" and reported a corpus of zero.
    phrasing = re.compile(r"(?<![\d,])(\d{2,3})[- ]page corpus\b", re.I)

    #: (page, count) pairs that deliberately do not match the current corpus.
    #: A register rather than a cleverer pattern: the distinction that matters
    #: is tense, no regex reads tense, and naming the exceptions means a new
    #: drift fails while a deliberate one is documented. The same choice this
    #: file makes for blocked demonstrations and for retired labels.
    historical: dict[tuple[str, int], str] = {
        ("concepts/llm-content-lifecycle.md", 400): "someone else's corpus, in an interview answer",
    }
    # `("concepts/docs-analytics.md", 121)` was here and is gone. It was added
    # while the pattern still had the "all N pages" arm, which matched that
    # page's "the tree held 121 pages"; when that arm was removed for flagging
    # subset counts, the entry stopped protecting anything and became an
    # exemption the next real drift on that page would have inherited. The
    # arm below is what reported it, which is the only reason it was found:
    # a dead exemption is invisible from reading, because it looks exactly
    # like a live one.

    drifted = []
    for page in sorted(docs.rglob("*.md")):
        name = page.relative_to(docs).as_posix()
        for match in phrasing.finditer(prose_of(page.read_text(encoding="utf-8"))):
            stated = int(match.group(1))
            if stated in allowed or (name, stated) in historical:
                continue
            drifted.append((name, stated))

    assert not drifted, (
        "a page count in prose that is neither %d concepts nor %d files, and "
        "is not in the historical register above. Either restate it, move the "
        "figure into the quoted run it came from and say when it ran, or "
        "register it with a reason: %s" % (concepts, markdown_files, drifted)
    )

    # The register cannot rot either: an entry for a figure that has been
    # restated since is an exemption protecting nothing, and the next real
    # drift on that page would inherit it.
    stale_exemptions = []
    for (name, stated), reason in historical.items():
        page = docs / name
        if not page.exists():
            stale_exemptions.append((name, stated, "page is gone"))
            continue
        found = {
            int(m.group(1))
            for m in phrasing.finditer(prose_of(page.read_text(encoding="utf-8")))
        }
        if stated not in found:
            stale_exemptions.append((name, stated, "no longer stated"))
    assert not stale_exemptions, (
        f"historical register entries that protect nothing: {stale_exemptions}"
    )


#: Concepts that cannot be demonstrated in this project, with the reason.
#:
#: Two reasons only, and they are different in kind. `model` means the
#: demonstration needs a language model or downloadable weights, which this
#: environment has neither the access nor the network route for; that is a
#: tooling limit and would lift elsewhere. `craft` means the evidence is a
#: conversation, an accepted edit or a decision in someone else's repository,
#: so no environment would fix it.
#:
#: `vector-stores` used to be here and is not any more. Its mechanics turned
#: out to be demonstrable without a model after all: `drills/vector_store.py`
#: measures an approximate index's recall and latency over hashed vectors,
#: because that geometry does not depend on where the vectors came from. Its
#: page keeps a "how this would be demonstrated elsewhere" subsection anyway,
#: for the half that does need weights, which is the quality comparison. A
#: concept can be partly demonstrated and still owe the reader that section.
#:
#: A concept belongs here only when its demonstration is blocked. Plenty of
#: other concepts lack a `demonstrations.yaml` entry because nobody has built
#: the artifact yet, and those belong on the backlog instead: requiring an
#: explanation of how they *would* be demonstrated would be boilerplate in
#: place of the demonstration itself.
BLOCKED_DEMONSTRATIONS = {
    "embeddings": "model",
    "output-evaluation": "model",
    "prompting": "model",
    "llm-content-lifecycle": "model",
    "agent-skills": "model",
    "ai-assistants": "model",
    "agentic-workflows": "model",
    "coding-agents": "model",
    "ai-trust-judgment": "model",
    "technical-writing": "craft",
    "systems-mindset": "craft",
    "docs-as-product": "craft",
    "sme-interviews": "craft",
    "reading-code-to-verify": "craft",
    "implementation-feedback": "craft",
}


def test_a_blocked_concept_says_how_it_would_be_demonstrated():
    """"No demonstration" must leave a learner with something to do.

    A page that states its demonstration is impossible here and stops has told
    the reader the truth and given them nothing. Each of these carries a
    subsection naming the environment, the procedure, the figures a learner
    would observe, and how they would know the setup was broken rather than the
    result surprising.
    """
    import yaml

    root = Path(__file__).resolve().parent.parent
    registry = load_registry(root / "concepts.yaml")
    demonstrated = {
        entry["concept"]
        for entry in yaml.safe_load(
            (root / "demonstrations.yaml").read_text(encoding="utf-8")
        )["demonstrates"]
    }

    known = {c.id for c in registry.concepts}
    unknown = set(BLOCKED_DEMONSTRATIONS) - known
    assert not unknown, f"not concepts: {sorted(unknown)}"

    claimed = set(BLOCKED_DEMONSTRATIONS) & demonstrated
    assert not claimed, (
        "listed as blocked and also demonstrated, so one of the two is wrong: "
        f"{sorted(claimed)}"
    )

    heading = "### How this would be demonstrated elsewhere"
    missing = [
        cid
        for cid in sorted(BLOCKED_DEMONSTRATIONS)
        if heading not in (root / "docs" / registry.by_id[cid].page).read_text(
            encoding="utf-8"
        )
    ]
    assert not missing, f"blocked, with no account of how it would be shown: {missing}"


def test_every_unprovable_concept_says_how_it_would_be_shown():
    """The same obligation, driven by the triage rather than a list here.

    `BLOCKED_DEMONSTRATIONS` above predates the triage in
    `demonstrations.yaml` and is kept because it records *why* each one is
    blocked in a form a reader of this file can see. This check is the general
    one: anything the register marks `blocked` or `needs-organisation` owes the
    reader an account of how the skill would be demonstrated, because those are
    exactly the two reasons that no amount of work on this repository will fix.
    """
    from fieldguide.demos import load_demonstrations

    root = Path(__file__).resolve().parent.parent
    registry = load_registry(root / "concepts.yaml")
    demonstrations = load_demonstrations(root / "demonstrations.yaml", registry)

    owed = {
        cid
        for cid, reason in demonstrations.triage.items()
        if reason in ("blocked", "needs-organisation")
    }
    assert owed, "the register marks nothing unprovable, which cannot be right"

    heading = "### How this would be demonstrated elsewhere"
    missing = sorted(
        cid
        for cid in owed
        if heading not in (root / "docs" / registry.by_id[cid].page).read_text(
            encoding="utf-8"
        )
    )
    assert not missing, f"unprovable here, with no account of how it would be shown: {missing}"


def test_every_concept_is_demonstrated_or_has_a_recorded_reason():
    """The register's whole value is that nothing sits unexamined.

    A concept that is neither demonstrated nor triaged is one nobody has
    decided about, and before the triage existed there were twenty-nine of
    them, mixed together: some demonstrable and on the backlog, some
    deliberately declined, some measured in a scratch directory and never
    committed. Collapsing those into "no demonstration" is what made the gap
    register stop being read.

    The `scratch` reason has since been retired, because all eight concepts
    that carried it now have a committed drill. A triage category that empties
    out is the one good outcome a triage can have, and leaving it in place with
    a count of zero would make the register look like it still had work in it.
    """
    from fieldguide.demos import TRIAGE_REASONS, load_demonstrations

    root = Path(__file__).resolve().parent.parent
    registry = load_registry(root / "concepts.yaml")
    demonstrations = load_demonstrations(root / "demonstrations.yaml", registry)

    decided = set(demonstrations.by_concept) | set(demonstrations.triage)
    assert decided == set(registry.by_id)

    overlap = set(demonstrations.by_concept) & set(demonstrations.triage)
    assert not overlap, f"both demonstrated and triaged: {sorted(overlap)}"

    unknown = set(demonstrations.triage.values()) - set(TRIAGE_REASONS)
    assert not unknown, f"unknown triage reasons: {sorted(unknown)}"


def test_a_concept_left_undecided_fails_the_load(tmp_path):
    """The rule above has to actually fire, not merely pass today."""
    import pytest
    import yaml

    from fieldguide.demos import DemonstrationError, load_demonstrations

    root = Path(__file__).resolve().parent.parent
    registry = load_registry(root / "concepts.yaml")
    raw = yaml.safe_load((root / "demonstrations.yaml").read_text(encoding="utf-8"))

    dropped = sorted(raw["triage"])[0]
    del raw["triage"][dropped]
    path = tmp_path / "demonstrations.yaml"
    path.write_text(yaml.safe_dump(raw), encoding="utf-8")

    with pytest.raises(DemonstrationError, match="neither demonstrated nor triaged"):
        load_demonstrations(path, registry)


def test_a_concept_both_demonstrated_and_triaged_fails_the_load(tmp_path):
    import pytest
    import yaml

    from fieldguide.demos import DemonstrationError, load_demonstrations

    root = Path(__file__).resolve().parent.parent
    registry = load_registry(root / "concepts.yaml")
    raw = yaml.safe_load((root / "demonstrations.yaml").read_text(encoding="utf-8"))

    raw["triage"][raw["demonstrates"][0]["concept"]] = "planned"
    path = tmp_path / "demonstrations.yaml"
    path.write_text(yaml.safe_dump(raw), encoding="utf-8")

    with pytest.raises(DemonstrationError, match="also has a demonstration entry"):
        load_demonstrations(path, registry)


def test_every_structural_label_has_exactly_one_wording():
    """One wording per labelled element, across all 106 pages.

    This is the check that did not exist while the corpus carried three
    variant pairs at once. Nothing else could have caught them: a variant
    label is valid Markdown, spelled correctly, in the right section, and
    invisible to a strict build. The only instrument is counting labels.
    """
    from fieldguide.registry import RETIRED_LABELS, STRUCTURAL_LABELS

    pages = sorted((Path(__file__).resolve().parent.parent / "docs" / "concepts").glob("*.md"))
    assert pages, "no concept pages found"

    offenders: dict[str, list[str]] = {}
    for page in pages:
        text = page.read_text(encoding="utf-8")
        for retired, element in RETIRED_LABELS.items():
            if retired in text:
                offenders.setdefault(f"{retired} (use {STRUCTURAL_LABELS[element]})", []).append(
                    page.name
                )

    # Two pages quote the retired wordings as the data of their own golden
    # paths: `instructional-design` found the prerequisite variant and
    # `assessment` found the proof-task one, and a page whose measurement is
    # *about* a variant has to be able to print it. Named rather than
    # pattern-matched, because an exemption that matches a shape would
    # quietly cover the next page that reintroduces a variant for real.
    quoting_the_history = {"instructional-design.md", "assessment.md"}
    offenders = {
        label: [name for name in names if name not in quoting_the_history]
        for label, names in offenders.items()
    }
    offenders = {label: names for label, names in offenders.items() if names}

    assert not offenders, f"retired label wordings still in use: {offenders}"


def test_the_scaffold_emits_every_label_it_should():
    """A prompt that says "label the tasks" is how a corpus grows variants.

    The scaffold writes the labels out, so an author fills one in rather
    than naming it. This asserts it still does, for every element the
    section map claims.
    """
    from fieldguide.registry import STRUCTURAL_LABELS
    from fieldguide.scaffold import SECTION_LABELS, render_concept_page

    root = Path(__file__).resolve().parent.parent
    registry = load_registry(root / "concepts.yaml")
    text = render_concept_page(registry, registry.concepts[0].id)

    for section, keys in SECTION_LABELS.items():
        assert f"## {section}" in text, f"the scaffold no longer emits {section!r}"
        for key in keys:
            assert STRUCTURAL_LABELS[key] in text, (
                f"the scaffold no longer emits {STRUCTURAL_LABELS[key]!r} under {section!r}"
            )


def test_a_canonical_label_is_actually_used():
    """Declared is not used. A constant nothing reads is a comment.

    The floor is the declared one rather than a guessed fraction. Three
    labels are universal and must be on every written page; the rest are
    optional by design, so the only claim about them is that something uses
    them. An earlier version of this test used "a third of the pages" and
    passed `competent-answer` at 36 of 106 by one page, which is a threshold
    doing no work.
    """
    from fieldguide.registry import STRUCTURAL_LABELS, UNIVERSAL_LABELS

    pages = sorted((Path(__file__).resolve().parent.parent / "docs" / "concepts").glob("*.md"))
    texts = [page.read_text(encoding="utf-8") for page in pages]

    for key, label in STRUCTURAL_LABELS.items():
        used = sum(1 for text in texts if label in text)
        if key in UNIVERSAL_LABELS:
            assert used == len(pages), (
                f"{label!r} is universal but is missing from "
                f"{len(pages) - used} of {len(pages)} pages"
            )
        else:
            assert used >= 1, f"{label!r} is declared canonical and used nowhere"

    assert UNIVERSAL_LABELS <= set(STRUCTURAL_LABELS), "a universal label is not declared"


def test_the_audit_reports_undeclared_repeated_labels():
    """The instrument that finds variants nobody thought of.

    Counting declared labels only confirms what you already know. This
    corpus carried "One sharper point, and the best thing to say here." on
    five pages through a hand sweep that had looked for labels used ten or
    more times and pronounced it clean, so the audit now reports every
    repeated bolded opener it cannot account for.

    The assertion is that the list is empty, which is a claim about the
    corpus, and that the check can actually see something, which is a claim
    about the check. The second half matters more: a sweep that reports
    nothing because it looks nowhere is the failure this guide keeps finding.
    """
    from fieldguide.audit import BOLD_OPENER, audit
    from fieldguide.registry import RETIRED_LABELS, STRUCTURAL_LABELS

    root = Path(__file__).resolve().parent.parent
    result = audit(load_registry(root / "concepts.yaml"), root / "docs")

    repeated = {k: n for k, n in result.undeclared_labels.items() if n >= 3}
    assert not repeated, f"undeclared labels repeated across pages: {repeated}"

    # The check sees labels at all: every declared wording it would have
    # reported, had it not been declared, still matches its own pattern.
    for label in list(STRUCTURAL_LABELS.values()) + list(RETIRED_LABELS):
        assert BOLD_OPENER.match(label), (
            f"{label!r} would not be seen by the undeclared-label sweep"
        )


def test_no_page_carries_a_sentence_over_the_agreed_maximum():
    """The outcome of the long-sentence pass, as a contract.

    55 rather than 45. The corpus's longest sentence is 50 words and 27 pages
    still carry one over 45, so a 45 ceiling would fail today and a ceiling
    nobody meets is not a contract. 55 is five words of headroom above the
    worst case, which is enough to catch a regression and not enough to
    license one.

    `cognitive-load` argues the per-page maximum is the metric to act on
    rather than the mean, so the maximum is what this asserts.
    """
    from fieldguide.audit import SENTENCE, prose_of

    root = Path(__file__).resolve().parent.parent
    ceiling = 55
    offenders = []
    for page in sorted((root / "docs" / "concepts").glob("*.md")):
        text = page.read_text(encoding="utf-8")
        for block in prose_of(text).split("\n\n"):
            for sentence in SENTENCE.split(" ".join(block.split())):
                words = len(sentence.split())
                if words > ceiling:
                    offenders.append((words, page.name, sentence[:80]))

    assert not offenders, (
        f"sentences over {ceiling} words:\n  "
        + "\n  ".join(f"{n} words, {name}: {text}..." for n, name, text in offenders)
    )


def test_a_long_sentence_cannot_hide_inside_a_list_item():
    """The loophole in the metric above, closed.

    Excluding list items from the prose measurement is correct, and it means a
    long sentence becomes compliant the moment somebody puts a hyphen in front
    of it. Four of the five worst sentences in this corpus genuinely were
    lists and were converted to bullets, which is the right edit for a reader
    and also an edit that removes them from the measurement. Those two facts
    are independent, so both numbers are asserted.
    """
    from fieldguide.audit import list_sentences

    root = Path(__file__).resolve().parent.parent
    offenders = {}
    for page in sorted((root / "docs" / "concepts").glob("*.md")):
        inside = list_sentences(page.read_text(encoding="utf-8"))
        if inside and max(inside) > 45:
            offenders[page.name] = max(inside)

    assert not offenders, f"list items hiding sentences over 45 words: {offenders}"


def test_every_ceiling_is_declared_rather_than_left_in_a_note():
    """A ceiling stated only in prose is a ceiling nobody can check.

    Eleven entries say, in their own note, that what is missing is readers or
    a deployment. That was the whole content of the judgment this register
    used to leave implicit, and it was re-derived by hand every time somebody
    proposed promoting a concept. It is now data, and this asserts the data
    has not fallen behind the prose.

    The check runs the other way too: a concept whose note claims an audience
    gap and is not declared fails, so the next entry written in that shape
    cannot quietly skip the register.
    """
    from fieldguide.demos import load_demonstrations

    root = Path(__file__).resolve().parent.parent
    registry = load_registry(root / "concepts.yaml")
    demos = load_demonstrations(root / "demonstrations.yaml", registry)

    assert demos.ceilings, "no ceilings declared at all"

    full = {entry.concept for entry in demos.entries if entry.extent == "full"}
    phrases = ("needs readers", "no audience", "reader-side", "needs an audience")
    undeclared = set()
    for entry in demos.entries:
        if entry.concept in demos.ceilings or entry.concept in full:
            continue
        if any(phrase in entry.note.lower() for phrase in phrases):
            undeclared.add(entry.concept)

    assert not undeclared, (
        "these entries claim an audience gap in prose and are not in the "
        f"ceilings block: {sorted(undeclared)}"
    )


def test_a_ceiling_and_a_full_entry_cannot_coexist():
    """The rule that caught `findability` the first time it was listed.

    Its docpack entry is `partial` and says so, but its fieldguide entry is
    `full`: every page carries its own description with a gate proving it,
    which is the entire corpus-side half. A ceiling belongs to a concept
    rather than to one project's entry, so a concept with any `full` entry
    does not have one, and the loader refuses to record that it does.
    """
    import yaml

    from fieldguide.demos import DemonstrationError, load_demonstrations

    root = Path(__file__).resolve().parent.parent
    registry = load_registry(root / "concepts.yaml")
    raw = yaml.safe_load((root / "demonstrations.yaml").read_text(encoding="utf-8"))
    full = next(e["concept"] for e in raw["demonstrates"] if e["extent"] == "full")
    raw.setdefault("ceilings", {}).setdefault("no-audience", []).append(full)

    broken = Path(__file__).resolve().parent / "_ceiling_conflict.yaml"
    broken.write_text(yaml.safe_dump(raw), encoding="utf-8")
    try:
        with pytest.raises(DemonstrationError, match="contradicts a ceiling"):
            load_demonstrations(broken, registry)
    finally:
        broken.unlink()


#: Words this repository writes numbers as, in its own prose.
_NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
    "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16,
    "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20,
}


#: The exact sentences in which this repository states one of those counts, and
#: which count each states. Precise rather than broad on purpose: the first
#: version scanned for "<number> <noun>" anywhere and reported six findings,
#: four of which were "Two learning paths taught a prerequisite too late" and
#: "Write twenty questions with their expected source pages" — prose that
#: contains a number and a noun and makes no claim about either collection. A
#: check that cries wolf gets switched off the first time it annoys somebody,
#: which is the lesson the `crawlability` page draws about its own false
#: positive.
#:
#: It still found two places a careful read had missed, both of them the kind
#: of place a read misses: a table cell and a front-matter summary.
CLAIM_PATTERNS = (
    (r"same (\w+) questions", "sections"),
    (r"all (\w+) headings", "sections"),
    (r"(\w+) required sections", "sections"),
    (r"one of its\s+(\w+)\s+sections", "sections"),
    (r"write the (\w+) sections", "sections"),
    (r"with its (\w+) headings", "sections"),
    (r"GENERATED: (\w+) learning paths", "paths"),
    (r"^\s*(\w+) \[learning paths\]", "paths"),
    (r"(\d+) concepts, (\d+) paths", "concepts-and-paths"),
)


def test_the_prose_cannot_contradict_the_contract_it_describes():
    """The repository's own documentation must agree with its own constants.

    This exists because it did not. `Related` was promoted to the seventh
    enforced section the day a page turned up without one, and "six" survived
    in seven places afterwards: both front doors' numbered lists, a table row,
    the page-contract explainer's front-matter summary AND its enforcement
    list (while its own opening paragraph said seven), the `fieldguide new`
    success message, and the scaffold's docstring. Every one described a
    contract the code had stopped enforcing, and nothing could see it, because
    a wrong number written as a word is valid prose that spell-checks clean.

    The learning-path count had done the same thing: "seven" outlived the
    addition of two more paths, in three places.
    """
    import re

    from fieldguide.registry import REQUIRED_SECTIONS

    root = Path(__file__).resolve().parent.parent
    registry = load_registry(root / "concepts.yaml")
    truth = {
        "sections": len(REQUIRED_SECTIONS),
        "paths": len(registry.paths),
        "concepts": len(registry.concepts),
    }

    files = [
        root / "README.md",
        root / "docs" / "index.md",
        root / "docs" / "explanation" / "the-page-contract.md",
        root / "docs" / "explanation" / "why-a-registry.md",
        root / "src" / "fieldguide" / "cli.py",
        root / "src" / "fieldguide" / "scaffold.py",
    ]

    def as_number(token: str) -> int | None:
        if token.isdigit():
            return int(token)
        return _NUMBER_WORDS.get(token.lower())

    wrong, checked = [], 0
    for path in files:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for pattern, kind in CLAIM_PATTERNS:
            for match in re.finditer(pattern, text, re.I | re.M):
                if kind == "concepts-and-paths":
                    pairs = (("concepts", match.group(1)), ("paths", match.group(2)))
                else:
                    pairs = ((kind, match.group(1)),)
                for subject, token in pairs:
                    claimed = as_number(token)
                    if claimed is None:
                        continue
                    checked += 1
                    if claimed != truth[subject]:
                        wrong.append(
                            f"{path.name}: {match.group(0).strip()!r} claims "
                            f"{claimed} {subject}, but there are {truth[subject]}"
                        )

    assert checked >= 8, (
        f"only {checked} claims matched, so this check has stopped looking at "
        "the prose it is supposed to police"
    )
    assert not wrong, "prose disagrees with the code:\n  " + "\n  ".join(wrong)


def test_every_demonstration_names_a_file_that_exists():
    """The register's artifact paths are checked, not just its concept ids.

    `load_demonstrations` validates that every entry names a real concept, a
    known project and one of two extents. It has never checked the one field a
    reader actually follows: the path. Eighty-four entries name a file, every
    path was typed by hand, and a rename would leave the honesty centrepiece
    of this portfolio pointing at nothing while every gate stayed green.

    The companion repository's half can only be checked when it is checked out
    beside this one, so it is skipped rather than guessed at. Saying which
    half was verified is the point of the register.
    """
    from fieldguide.demos import load_demonstrations

    root = Path(__file__).resolve().parent.parent
    registry = load_registry(root / "concepts.yaml")
    demos = load_demonstrations(root / "demonstrations.yaml", registry)

    siblings = {"fieldguide": root, "docpack": root.parent / "docpack"}
    missing, skipped = [], 0
    for entry in demos.entries:
        base = siblings.get(entry.project)
        if base is None or not base.is_dir():
            skipped += 1
            continue
        if not (base / entry.artifact).exists():
            missing.append(f"{entry.project}/{entry.artifact} ({entry.concept})")

    assert not missing, (
        "demonstration entries naming a file that is not there:\n  "
        + "\n  ".join(sorted(missing))
    )
    local = [e for e in demos.entries if e.project == "fieldguide"]
    assert len(local) >= 20, (
        f"only {len(local)} local entries, so this check has stopped covering "
        "the register it is supposed to cover"
    )
