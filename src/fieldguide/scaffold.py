"""Generate a concept page that already satisfies the page contract.

The contract in `registry.REQUIRED_SECTIONS` is enforced in CI. Enforcement
alone makes the right way mandatory rather than easy, and the predictable
result is that contributors copy the nearest existing page and inherit its
shape along with its mistakes.

So the contract ships as a generator. `fieldguide new <concept-id>` reads the
concept out of the registry and writes a page with its seven headings, its front
matter, its prerequisites already cross-linked, and the posting quote that
justifies it already in place.

The prompts under each heading are not filler. Each one names the specific way
that section usually goes wrong.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .registry import STRUCTURAL_LABELS, Concept, Registry

#: Which labelled elements belong to which section, in the order they appear.
#: A scaffolded page arrives with the labels already written, so an author
#: fills them in rather than naming them, which is where variants come from.
SECTION_LABELS: dict[str, tuple[str, ...]] = {
    "The golden path": ("built",),
    "How to talk about it": ("competent-answer", "sharper-point", "tradeoff"),
    "How to prove it": ("artifact", "proof-tasks", "credibility"),
}


PROMPTS: dict[str, str] = {
    "What it is": """Define it in two sentences, for someone who has heard the
term in a meeting and not admitted they do not know it. No history, no
motivation, no list of benefits.

The failure mode here is writing the Wikipedia opening: a definition so
careful it is useless. Prefer the sentence you would actually say out loud.
""",
    "Why the job asks for it": """Connect it to the posting line above. What
does someone holding this role do on a Tuesday that requires this?

The failure mode is restating the quote. The quote is already printed; this
section earns its place by explaining the work behind it.
""",
    "The golden path": """The shortest real exercise that produces a working
result. Commands the reader can paste, with what they should see after each
one.

Three rules. It must start from a clean environment. It must end in something
observable, not in "you now understand". And you must have run it yourself, in
that order, on a machine with nothing pre-installed.
""",
    "Reference": """The facts worth looking up later: the vocabulary, the
options, the defaults, the gotchas. Tables beat prose here.

The failure mode is narrative. Nobody reads this section; they scan it.
""",
    "How to talk about it": """What a competent answer sounds like when an
interviewer asks about this, and what the follow-up question will be.

Include the tradeoff. Anyone can recite what a thing does; the signal is
knowing what it costs and when not to use it.
""",
    "How to prove it": """The artifact that demonstrates this without you
having to claim it: a repository, a file, a measured number, a commit.

Be specific enough to act on today. "Build a RAG pipeline" is not a proof;
"add an eval set of twenty questions and publish the recall figure" is.
""",
    "Related": """Four or five neighbouring concepts, each with a clause saying
why a reader would follow it from here. The prerequisites and dependents are
already computed above, so this section is for the lateral links the graph does
not know about.

The failure mode is a bare list of titles. "[Chunking](chunking.md)" tells a
reader nothing they could not guess; "[Chunking](chunking.md), why a corpus of
components is harder to retrieve from" tells them whether to click.
""",
}


class ScaffoldError(ValueError):
    """Raised when a page cannot be generated."""


@dataclass(frozen=True)
class NewPage:
    """A generated page, before anything is written to disk."""

    path: Path
    text: str


def render_concept_page(registry: Registry, concept_id: str) -> str:
    """Render a concept page skeleton from the registry.

    Everything the registry already knows is filled in, so the author writes
    prose and never retypes metadata that exists elsewhere.

    Raises:
        ScaffoldError: If the concept is not in the registry. A page outside
            the registry is an orphan, and `fieldguide check` would reject it,
            so the generator refuses to create one.
    """
    by_id = registry.by_id
    if concept_id not in by_id:
        raise ScaffoldError(
            f"{concept_id!r} is not in the registry. Add it to concepts.yaml first: "
            "a page with no concept fails `fieldguide check`."
        )
    concept: Concept = by_id[concept_id]

    tags = [concept.category, concept.tier]
    lines = [
        "---",
        f"title: {concept.name}",
        f"summary: 'TODO: one sentence on what {concept.name.lower()} is and why this role needs it.'",
        "diataxis: explanation",
        "audience: developer",
        f"concept: {concept.id}",
        f"tags: [{', '.join(tags)}]",
        "---",
        "",
        f"# {concept.name}",
        "",
        f"`{concept.tier}` · difficulty {concept.difficulty} · {concept.time}",
        "",
    ]

    for demand in concept.demanded_by:
        if demand.provenance == "quoted":
            lines += [
                f"> {demand.quote}",
                "",
                f"> Source: {demand.source} posting, verbatim",
                "",
            ]
        else:
            lines += [
                f"!!! note \"Not a quotation ({demand.provenance})\"",
                f"    {demand.quote}",
                "",
            ]

    if concept.prerequisites:
        links = ", ".join(
            f"[{by_id[p].name}]({p}.md)" for p in concept.prerequisites
        )
        # Taken from STRUCTURAL_LABELS rather than written here, so a new
        # page cannot invent a third wording the way this corpus did twice.
        lines += [f"{STRUCTURAL_LABELS['prerequisites']} {links}", ""]

    dependents = sorted(
        (c for c in registry.concepts if concept.id in c.prerequisites),
        key=lambda c: c.name,
    )
    if dependents:
        links = ", ".join(f"[{c.name}]({c.id}.md)" for c in dependents)
        lines += [f"{STRUCTURAL_LABELS['leads-to']} {links}", ""]

    for section in PROMPTS:
        lines += [f"## {section}", ""]
        lines += [f"<!-- {line}" if i == 0 else line
                  for i, line in enumerate(PROMPTS[section].strip().splitlines())]
        lines += ["-->", ""]
        # The labels this section must use, emitted rather than described. A
        # prompt that says "label the tasks" is how a corpus ends up with two
        # wordings; a line already carrying the right one is not.
        for key in SECTION_LABELS.get(section, ()):
            lines += [STRUCTURAL_LABELS[key], ""]

    return "\n".join(lines) + "\n"


def new_concept_page(registry: Registry, docs_dir: Path, concept_id: str) -> NewPage:
    """Build the page and work out where it goes. Writes nothing.

    Raises:
        ScaffoldError: If a page already exists. There is no `--force`:
            overwriting a draft to save a keystroke is not a good trade.
    """
    text = render_concept_page(registry, concept_id)
    path = docs_dir / "concepts" / f"{concept_id}.md"
    if path.exists():
        raise ScaffoldError(f"{path} already exists")
    return NewPage(path=path, text=text)


def write_page(page: NewPage) -> Path:
    """Write a generated page, creating its directory if needed."""
    page.path.parent.mkdir(parents=True, exist_ok=True)
    page.path.write_text(page.text, encoding="utf-8")
    return page.path
