"""Parse and validate the concept registry.

`concepts.yaml` is the checklist for this project, and the reason it is a data
file rather than a list of Markdown checkboxes is that a checklist nobody can
verify is worse than no checklist: it reports completion it has not earned.

Everything here exists to make a specific lie impossible:

| The lie | What catches it |
|---|---|
| "covered" when no page exists | `missing_pages` |
| a page nobody planned, outside the model | `orphan_pages` |
| a concept marked `complete` that is a stub | `understuffed` |
| a learning path that teaches B before A | `path_order_violations` |
| a prerequisite chain that cannot be followed | `cycles` |
| a `quoted` claim with no quotation | schema validation |

The last one matters most to the integrity of the whole site. Every concept
claims a job posting asks for it. That claim is the argument for the concept
existing, and an unsourced version of it is just an assertion, so the schema
requires a provenance tag and a quote on every one.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import re

import yaml

#: Closed vocabulary. A concept's importance has to be one of these three,
#: because "important" with no scale attached is how a curriculum ends up with
#: forty equally weighted topics and no route through them.
TIERS = ("core", "supporting", "context")

#: Closed vocabulary. How a concept's claim on the reader's time is justified.
PROVENANCE = ("quoted", "derived", "adjacent")

#: Closed vocabulary. `complete` is a claim this module checks.
STATUSES = ("planned", "drafted", "complete")

#: Difficulty is an ordinal, not a number to average.
DIFFICULTIES = (1, 2, 3)

#: Closed vocabulary for a page's `diataxis` front-matter field, plus one value
#: the framework does not have.
#:
#: `placeholder` exists because the alternative was a lie. Every generated stub
#: in this repository used to declare `diataxis: reference`, hardcoded by the
#: generator, which made that value mean "not written yet" on 53 of 121 pages
#: while no hand-written page used it at all. Nothing read the field, so
#: nothing noticed. A required field that nothing consumes is a field that
#: drifts immediately and silently.
DIATAXIS = ("tutorial", "how-to", "reference", "explanation", "placeholder")

#: Sections every concept page must carry, in this order. This is the page
#: contract: the same questions answered in the same place every time, so a
#: reader skimming thirty pages learns the shape once.
#:
#: `Related` was added after the corpus was finished. 105 of 106 pages already
#: ended with one and a single page did not, which nothing noticed for the
#: length of the project: the contract enforced the sections it named, and this
#: was a convention instead. A convention that 105 pages keep is a requirement
#: nobody wrote down, and the reader meets the inconsistency either way.
REQUIRED_SECTIONS = (
    "What it is",
    "Why the job asks for it",
    "The golden path",
    "Reference",
    "How to talk about it",
    "How to prove it",
    "Related",
)

#: The exact wording of every recurring labelled element, and the section it
#: belongs to. One label per element, enforced by `test_structural_labels`.
#:
#: This exists because the corpus accumulated variants faster than anyone
#: noticed. It was written across several sittings, and each sitting invented
#: its own wording for elements the previous sitting had already named. Three
#: pairs were in use at once when they were finally swept for:
#:
#:   proof-task label    "Three things to do today:" on 70 pages against
#:                       "Three things to do, in order:" on 35, and one page
#:                       carrying a splice of the two
#:   sharper point       "One sharper point." on 47 against "A sharper point."
#:                       on 35, plus "One sharper point, and the best thing to
#:                       say here." on 5, which the first sweep missed because
#:                       it was looking for labels used ten times or more
#:   credibility         "What makes it credible rather than decorative." on
#:                       72 against "What makes it credible." on 34
#:
#: A reader meeting two wordings for one element does not read two
#: conventions, they read incoherence, and no spell-checker, linter or strict
#: build sees any of it. The only thing that catches a label variant is
#: counting labels, which is why the audit counts them and this constant is
#: what it counts against.
#:
#: Two of the three choices were decided on accuracy rather than on majority.
#: "in order" beat the more common "today" because the tasks genuinely are
#: ordered, with the first always being to run the golden path, while "today"
#: promises a scope some of these tasks do not have. "rather than decorative"
#: beat the shorter form because that clause is the section's whole argument.
STRUCTURAL_LABELS: dict[str, str] = {
    "prerequisites": "**Prerequisites:**",
    "leads-to": "**Leads to:**",
    "artifact": "**The artifact.**",
    "built": "**What you built.**",
    "tradeoff": "**The tradeoff to volunteer.**",
    "competent-answer": "**What a competent answer sounds like.**",
    "sharper-point": "**One sharper point.**",
    "credibility": "**What makes it credible rather than decorative.**",
    "proof-tasks": "**Three things to do, in order:**",
    # Sub-template labels. Each belongs to one family of pages rather than to
    # every page, and each is consistent within its family, so they are
    # declared rather than standardised. Declaring them is the point: the
    # audit reports every repeated bolded opener that is *not* in this dict,
    # so leaving a deliberate element undeclared buries the next accidental
    # one in a list of nine false positives.
    "demonstrated-need": "**What you need.**",
    "demonstrated-seen": "**What you would see.**",
    "demonstrated-do": "**What a learner would do.**",
    "demonstrated-run": "**What you would run.**",
    "demonstrated-failure": "**How you would know it had failed.**",
    "no-commit": "**Why it does not commit.**",
    "competence-evidence": "**What competence looks like.**",
    "skill-exercised": "**Where the skill is exercised.**",
    "depth-caveat": "**Be honest about the depth.**",
}

#: The three labels every written page must carry. The rest are optional by
#: design: a page with no prerequisites has no prerequisite line, and the
#: sub-template labels above belong to one family each.
UNIVERSAL_LABELS: frozenset[str] = frozenset({"artifact", "credibility", "proof-tasks"})

#: Wordings that were in use for the same elements and are no longer allowed.
#: Kept rather than deleted so a reintroduction fails with the history.
RETIRED_LABELS: dict[str, str] = {
    "**Three things to do today:**": "proof-tasks",
    "**Three things to do today, in order:**": "proof-tasks",
    "**A sharper point.**": "sharper-point",
    "**What makes it credible.**": "credibility",
    "**Read first:**": "prerequisites",
    "**One sharper point, and the best thing to say here.**": "sharper-point",
}

#: A `complete` page shorter than this is a stub wearing a label.
MIN_COMPLETE_WORDS = 450

#: HTML comments, which the scaffold uses to carry its per-section prompts.
HTML_COMMENT = re.compile(r"<!--.*?-->", re.S)


def prose_words(text: str) -> int:
    """Count words a reader would see, excluding HTML comments.

    The scaffold emits roughly 380 words, of which 289 are prompt text inside
    comments. Counting raw words meant a freshly scaffolded page was already
    84 per cent of the way to the 450-word `complete` threshold, so an author
    needed about 74 words of real prose to mark it finished. Excluding
    comments raises that to about 363, which is what the gate was for.

    The heading still counts; only the comment is removed.

    >>> prose_words("# T\\n\\n<!-- a long prompt here -->\\n\\nreal prose words")
    5
    """
    return len(HTML_COMMENT.sub(" ", text).split())


class RegistryError(ValueError):
    """Raised when the registry is malformed."""


@dataclass(frozen=True)
class Demand:
    """One job posting's claim on a concept.

    Attributes:
        source: `intel`, `nvidia`, or `both`.
        provenance: `quoted`, `derived`, or `adjacent`. See the module docstring.
        quote: The posting's words when `quoted`; the argument otherwise.
    """

    source: str
    provenance: str
    quote: str

    @property
    def is_evidence(self) -> bool:
        """True only for a verbatim quotation. Everything else is argument."""
        return self.provenance == "quoted"


@dataclass(frozen=True)
class Concept:
    """One studiable concept.

    Attributes:
        id: Stable kebab-case identifier, used in URLs and cross-references.
        name: Display name.
        category: Key into the registry's `categories` map.
        tier: One of `TIERS`.
        difficulty: 1 read it, 2 practise it, 3 build something non-trivial.
        time: Honest estimate to working competence, as a human string.
        prerequisites: Concept ids that come first.
        demanded_by: Why this concept earns a page.
        status: One of `STATUSES`.
    """

    id: str
    name: str
    category: str
    tier: str
    difficulty: int
    time: str
    prerequisites: tuple[str, ...]
    demanded_by: tuple[Demand, ...]
    status: str

    @property
    def page(self) -> str:
        """Path of this concept's page, relative to the docs root."""
        return f"concepts/{self.id}.md"

    @property
    def has_evidence(self) -> bool:
        """True when at least one posting quote backs this concept."""
        return any(d.is_evidence for d in self.demanded_by)


@dataclass(frozen=True)
class LearningPath:
    """An ordered route through a subset of the concepts."""

    id: str
    name: str
    audience: str
    summary: str
    concepts: tuple[str, ...]


@dataclass(frozen=True)
class Registry:
    """The whole registry, parsed and structurally valid."""

    categories: dict[str, str]
    concepts: tuple[Concept, ...]
    paths: tuple[LearningPath, ...]

    @property
    def by_id(self) -> dict[str, Concept]:
        return {c.id: c for c in self.concepts}

    def in_category(self, key: str) -> list[Concept]:
        """Concepts in one category, core first, then by name."""
        order = {tier: i for i, tier in enumerate(TIERS)}
        return sorted(
            (c for c in self.concepts if c.category == key),
            key=lambda c: (order[c.tier], c.name),
        )

    def of_tier(self, tier: str) -> list[Concept]:
        return [c for c in self.concepts if c.tier == tier]

    @property
    def completion(self) -> dict[str, int]:
        """Count of concepts by status."""
        return {s: sum(1 for c in self.concepts if c.status == s) for s in STATUSES}


# --------------------------------------------------------------------- parsing


def _require(raw: dict[str, Any], key: str, label: str) -> Any:
    if key not in raw:
        raise RegistryError(f"{label}: missing {key!r}")
    return raw[key]


def _parse_demand(raw: Any, label: str) -> Demand:
    if not isinstance(raw, dict):
        raise RegistryError(f"{label}: each demanded_by entry must be a mapping")
    source = str(_require(raw, "source", label))
    provenance = str(_require(raw, "provenance", label))
    quote = str(_require(raw, "quote", label)).strip()

    if source not in ("intel", "nvidia", "both"):
        raise RegistryError(f"{label}: source must be intel, nvidia or both, got {source!r}")
    if provenance not in PROVENANCE:
        raise RegistryError(
            f"{label}: provenance must be one of {list(PROVENANCE)}, got {provenance!r}"
        )
    if not quote:
        # A concept's claim on the reader is the quote. Without one there is
        # nothing to check and nothing to argue with.
        raise RegistryError(f"{label}: quote must not be empty")
    return Demand(source=source, provenance=provenance, quote=quote)


def _parse_concept(raw: Any, index: int) -> Concept:
    if not isinstance(raw, dict):
        raise RegistryError(f"concepts[{index}]: must be a mapping")
    label = f"concepts[{index}] ({raw.get('id', 'no id')})"

    concept_id = str(_require(raw, "id", label))
    if concept_id != concept_id.lower() or " " in concept_id or "_" in concept_id:
        raise RegistryError(f"{label}: id must be lowercase kebab-case, got {concept_id!r}")

    tier = str(_require(raw, "tier", label))
    if tier not in TIERS:
        raise RegistryError(f"{label}: tier must be one of {list(TIERS)}, got {tier!r}")

    status = str(_require(raw, "status", label))
    if status not in STATUSES:
        raise RegistryError(f"{label}: status must be one of {list(STATUSES)}, got {status!r}")

    difficulty = _require(raw, "difficulty", label)
    if difficulty not in DIFFICULTIES:
        raise RegistryError(
            f"{label}: difficulty must be one of {list(DIFFICULTIES)}, got {difficulty!r}"
        )

    demands = _require(raw, "demanded_by", label)
    if not isinstance(demands, list) or not demands:
        raise RegistryError(f"{label}: demanded_by must be a non-empty list")

    return Concept(
        id=concept_id,
        name=str(_require(raw, "name", label)),
        category=str(_require(raw, "category", label)),
        tier=tier,
        difficulty=int(difficulty),
        time=str(_require(raw, "time", label)),
        prerequisites=tuple(str(p) for p in raw.get("prerequisites", ()) or ()),
        demanded_by=tuple(_parse_demand(d, label) for d in demands),
        status=status,
    )


def _parse_path(raw: Any, index: int) -> LearningPath:
    if not isinstance(raw, dict):
        raise RegistryError(f"paths[{index}]: must be a mapping")
    label = f"paths[{index}] ({raw.get('id', 'no id')})"
    concepts = _require(raw, "concepts", label)
    if not isinstance(concepts, list) or len(concepts) < 2:
        raise RegistryError(f"{label}: a path needs at least two concepts")
    return LearningPath(
        id=str(_require(raw, "id", label)),
        name=str(_require(raw, "name", label)),
        audience=str(_require(raw, "audience", label)),
        summary=str(_require(raw, "summary", label)),
        concepts=tuple(str(c) for c in concepts),
    )


def load_registry(path: Path) -> Registry:
    """Parse the registry and check it is internally consistent.

    Structural validation only: field types, closed vocabularies, resolvable
    references, and an acyclic prerequisite graph. Checks that need the `docs/`
    tree live in `validate_against_tree`, so the registry can be loaded and
    reasoned about before any pages exist.

    Raises:
        RegistryError: On any structural problem, naming the offending entry.
    """
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise RegistryError(f"{path}: expected a mapping at the top level")

    categories = raw.get("categories") or {}
    if not isinstance(categories, dict) or not categories:
        raise RegistryError(f"{path}: categories must be a non-empty mapping")

    concept_list = raw.get("concepts") or []
    if not isinstance(concept_list, list) or not concept_list:
        raise RegistryError(f"{path}: concepts must be a non-empty list")

    concepts = tuple(_parse_concept(c, i) for i, c in enumerate(concept_list))
    paths = tuple(_parse_path(p, i) for i, p in enumerate(raw.get("paths") or []))

    seen: set[str] = set()
    for concept in concepts:
        if concept.id in seen:
            raise RegistryError(f"duplicate concept id {concept.id!r}")
        seen.add(concept.id)

    for concept in concepts:
        if concept.category not in categories:
            raise RegistryError(
                f"{concept.id}: unknown category {concept.category!r}; "
                f"known categories are {sorted(categories)}"
            )
        for prerequisite in concept.prerequisites:
            if prerequisite not in seen:
                raise RegistryError(
                    f"{concept.id}: prerequisite {prerequisite!r} is not a concept"
                )
            if prerequisite == concept.id:
                raise RegistryError(f"{concept.id}: concept is its own prerequisite")

    path_ids: set[str] = set()
    for learning_path in paths:
        if learning_path.id in path_ids:
            raise RegistryError(f"duplicate path id {learning_path.id!r}")
        path_ids.add(learning_path.id)
        for concept_id in learning_path.concepts:
            if concept_id not in seen:
                raise RegistryError(
                    f"path {learning_path.id!r}: {concept_id!r} is not a concept"
                )
        if len(set(learning_path.concepts)) != len(learning_path.concepts):
            raise RegistryError(f"path {learning_path.id!r}: lists a concept twice")

    registry = Registry(categories=dict(categories), concepts=concepts, paths=paths)

    cycles = find_cycles(registry)
    if cycles:
        raise RegistryError(
            "prerequisite cycle: " + " -> ".join(cycles[0]) + ". "
            "A cycle means no reader can start, so it is an error rather than a warning."
        )
    return registry


# ------------------------------------------------------------------ graph checks


def find_cycles(registry: Registry) -> list[list[str]]:
    """Return prerequisite cycles, as lists of concept ids.

    Depth-first search with a recursion stack. A cycle in a prerequisite graph
    is not a stylistic problem: it tells a reader to learn A before B and B
    before A, which leaves them with nowhere to begin.
    """
    by_id = registry.by_id
    cycles: list[list[str]] = []
    state: dict[str, int] = {}  # 0 unvisited, 1 on stack, 2 done

    def walk(node: str, stack: list[str]) -> None:
        state[node] = 1
        stack.append(node)
        for nxt in by_id[node].prerequisites:
            if state.get(nxt, 0) == 0:
                walk(nxt, stack)
            elif state.get(nxt) == 1:
                cycles.append(stack[stack.index(nxt):] + [nxt])
        stack.pop()
        state[node] = 2

    for concept in registry.concepts:
        if state.get(concept.id, 0) == 0:
            walk(concept.id, [])
    return cycles


def topological_order(registry: Registry) -> list[str]:
    """Concept ids in an order that never puts a concept before a prerequisite.

    Ties break on name, so the output is stable across runs and diffs stay
    small.
    """
    by_id = registry.by_id
    order: list[str] = []
    visited: set[str] = set()

    def walk(node: str) -> None:
        if node in visited:
            return
        visited.add(node)
        for nxt in sorted(by_id[node].prerequisites, key=lambda i: by_id[i].name):
            walk(nxt)
        order.append(node)

    for concept in sorted(registry.concepts, key=lambda c: c.name):
        walk(concept.id)
    return order


# ------------------------------------------------------- checks against the tree


@dataclass
class Findings:
    """Everything wrong, gathered rather than raised.

    One report beats failing on the first problem: a contributor who renamed a
    file wants the whole list, not six consecutive red builds.
    """

    missing_pages: list[str] = field(default_factory=list)
    orphan_pages: list[str] = field(default_factory=list)
    understuffed: list[tuple[str, int]] = field(default_factory=list)
    missing_sections: list[tuple[str, str]] = field(default_factory=list)
    out_of_order_sections: list[str] = field(default_factory=list)
    path_order_violations: list[str] = field(default_factory=list)
    unsourced: list[str] = field(default_factory=list)
    #: Pages that satisfy the whole contract while the registry still says
    #: `planned`. The mirror image of `missing_pages`, and the case this
    #: validator was blind to: two finished pages of 1,793 and 1,627 words sat
    #: in the corpus labelled "(outline)" in the coverage matrix, with `check`
    #: exiting 0, because every status check only ran in one direction.
    understated: list[tuple[str, int]] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(
            [
                self.missing_pages,
                self.orphan_pages,
                self.understuffed,
                self.missing_sections,
                self.out_of_order_sections,
                self.path_order_violations,
                self.understated,
            ]
        )

    def render(self) -> str:
        """Format the findings for a terminal or a CI log."""
        out: list[str] = []

        def section(title: str, rows: list[str]) -> None:
            if rows:
                out.append(f"{title}:")
                out.extend(f"  {row}" for row in rows)
                out.append("")

        section(
            "concepts with no page (status says otherwise)",
            [f"{cid}  expected docs/concepts/{cid}.md" for cid in self.missing_pages],
        )
        section(
            "pages with no concept in the registry",
            [f"{page}  add it to concepts.yaml or delete it" for page in self.orphan_pages],
        )
        section(
            "marked complete but too short to be",
            [f"{cid}  {n} words, minimum is {MIN_COMPLETE_WORDS}" for cid, n in self.understuffed],
        )
        section(
            "marked planned but the page satisfies the contract",
            [
                f"{cid}  {n} words and every required section; set status to "
                f"drafted or complete"
                for cid, n in self.understated
            ],
        )
        section(
            "pages missing a required section",
            [f"{cid}  no '## {sec}'" for cid, sec in self.missing_sections],
        )
        section("pages with sections out of contract order", self.out_of_order_sections)
        section("learning paths that teach a concept before its prerequisite",
                self.path_order_violations)
        section(
            "concepts with no verbatim posting quote (advisory, not a failure)",
            self.unsourced,
        )

        if self.ok:
            out.append("ok: registry and docs tree agree")
        return "\n".join(out).rstrip()



def _headings_outside_fences(text: str) -> dict[str, int]:
    """Map each `## ` heading to its line number, ignoring fenced code blocks.

    The naive version of this used `text.find("## Heading")`, which is the
    same bug the chunking page is about: a `## ` line inside a fenced block is
    content, not structure. Several concept pages in this guide embed Markdown
    samples containing `##` headings, so a validator that cannot tell the
    difference reports phantom sections and mis-orders the real ones.

    Only the FIRST occurrence of a heading is recorded, which is what the
    order check wants.

    Example:
        >>> text = chr(10).join([
        ...     "## Real",
        ...     "",
        ...     "```",
        ...     "## Inside a fence",
        ...     "```",
        ...     "",
        ...     "## Also real",
        ... ])
        >>> sorted(_headings_outside_fences(text))
        ['Also real', 'Real']
    """
    out: dict[str, int] = {}
    in_fence = False
    for number, line in enumerate(text.splitlines()):
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if stripped.startswith("## "):
            out.setdefault(stripped[3:].strip(), number)
    return out


def validate_against_tree(registry: Registry, docs_dir: Path) -> Findings:
    """Check the registry against the pages that actually exist.

    Args:
        registry: A loaded registry.
        docs_dir: Root of the documentation tree.

    Returns:
        Findings. Call `.ok` for pass or fail and `.render()` for the report.
    """
    findings = Findings()
    concepts_dir = docs_dir / "concepts"

    for concept in registry.concepts:
        # Provenance is a property of the registry entry, so it is checked
        # before anything about the page. Putting it after the `planned` skip
        # meant only already-written concepts were ever reported, which made
        # the advisory useless on a mostly-unwritten corpus.
        if not concept.has_evidence:
            findings.unsourced.append(f"{concept.id}  ({concept.demanded_by[0].provenance})")

        page = docs_dir / concept.page
        if not page.exists():
            # A planned concept is allowed to have no page yet; that is the
            # point of the status field. Anything further along is not.
            if concept.status != "planned":
                findings.missing_pages.append(concept.id)
            continue

        text = page.read_text(encoding="utf-8")

        if concept.status == "planned":
            # The page should be a generated placeholder, and the contract
            # governs prose, so there is normally nothing to check. But
            # `planned` is itself a claim, and it can be false: a finished page
            # whose status was never updated is reported in the coverage matrix
            # as "(outline)", which understates the corpus.
            #
            # This ran in one direction only until two pages of 1,793 and
            # 1,627 words, with every required section present, sat labelled
            # planned while `check` exited 0.
            words = prose_words(text)
            has_all = all(s in _headings_outside_fences(text) for s in REQUIRED_SECTIONS)
            if has_all and words >= MIN_COMPLETE_WORDS:
                findings.understated.append((concept.id, words))
            continue

        headings = _headings_outside_fences(text)
        positions: list[int] = []
        for required in REQUIRED_SECTIONS:
            index = headings.get(required)
            if index is None:
                findings.missing_sections.append((concept.id, required))
            else:
                positions.append(index)

        if len(positions) == len(REQUIRED_SECTIONS) and positions != sorted(positions):
            findings.out_of_order_sections.append(
                f"{concept.id}  sections present but not in contract order"
            )

        if concept.status == "complete":
            words = prose_words(text)
            if words < MIN_COMPLETE_WORDS:
                findings.understuffed.append((concept.id, words))

    if concepts_dir.is_dir():
        known = {c.id for c in registry.concepts}
        for page in sorted(concepts_dir.glob("*.md")):
            if page.stem not in known:
                findings.orphan_pages.append(f"concepts/{page.name}")

    by_id = registry.by_id
    for learning_path in registry.paths:
        seen: set[str] = set()
        for concept_id in learning_path.concepts:
            for prerequisite in by_id[concept_id].prerequisites:
                # A prerequisite outside the path is fine: a path is a route
                # through a subset, not a closure. Teaching one *after* the
                # concept that needs it is not.
                if prerequisite in learning_path.concepts and prerequisite not in seen:
                    findings.path_order_violations.append(
                        f"{learning_path.id}: {concept_id} comes before its "
                        f"prerequisite {prerequisite}"
                    )
            seen.add(concept_id)

    return findings
