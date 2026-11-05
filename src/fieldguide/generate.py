"""Generate the pages that describe the corpus from the registry.

Three pages here are never hand-written: the coverage matrix, the learning
paths, and the study plan. All three are views over `concepts.yaml`.

The reason is the same reason the API reference is generated rather than typed.
A hand-maintained index of forty pages is accurate for about a week. It is
also the page a reader trusts most, because an index looks authoritative, so
its decay is more expensive than the decay of any single page it points at.
"""

from __future__ import annotations

import yaml

from .demos import CEILING_REASONS, TRIAGE_REASONS
from .registry import PROVENANCE, REQUIRED_SECTIONS, Registry, topological_order

TIER_BLURB = {
    "core": "You cannot do this job without it.",
    "supporting": "You will be asked to do it; it is not the centre of the role.",
    "context": "Enough to not be lost in the room.",
}

DIFFICULTY_LABEL = {1: "read it", 2: "practise it", 3: "build something"}


def _link(concept, prefix: str = "") -> str:
    """Link a concept, marking it when only a placeholder exists.

    Every concept has a page: `fieldguide build` writes a placeholder for one
    that is still `planned`. That is a deliberate choice over leaving the link
    dead. A placeholder is navigable, it carries the registry's metadata and
    the posting quote that justifies the concept, and it keeps the strict build
    green while the corpus is half written. A dead link does none of that and
    teaches readers to stop trusting the cross-references.

    The marker is not optional either: a reader who follows a link needs to
    know before they click whether prose is waiting for them.
    """
    suffix = " *(outline)*" if concept.status == "planned" else ""
    return f"[{concept.name}]({prefix}{concept.id}.md){suffix}"


def placeholder_page(registry: Registry, concept_id: str) -> str:
    """Render the placeholder shown for a concept that has no prose yet.

    It is a real page rather than an apology: the tier, the effort, the time
    estimate, the posting quote, and the position in the prerequisite graph are
    all known from the registry, and all of them are useful to someone deciding
    whether to wait for this page or go and learn it elsewhere.
    """
    by_id = registry.by_id
    concept = by_id[concept_id]

    out = [
        _front_matter(
            concept.name,
            f"Outline only: {concept.name} is on the curriculum and not written yet.",
            audience="developer",
        ),
        f"# {concept.name}\n",
        f"`{concept.tier}` · {DIFFICULTY_LABEL[concept.difficulty]} · {concept.time}\n",
        "!!! info \"Outline only\"",
        "    This concept is on the curriculum and the prose is not written yet.",
        "    Everything below comes from the registry, so it is accurate as far as it",
        "    goes. See [coverage](../coverage.md) for what is finished.",
        "",
    ]

    out.append("## Why it is on the curriculum\n")
    for demand in concept.demanded_by:
        if demand.provenance == "quoted":
            out += [f"> {demand.quote}", "", f"> Source: {demand.source} posting, verbatim", ""]
        else:
            out += [
                f"**Not a quotation ({demand.provenance}).** {demand.quote}",
                "",
            ]

    out.append(f"{TIER_BLURB[concept.tier]}\n")

    if concept.prerequisites:
        out.append("## Read first\n")
        for pid in sorted(concept.prerequisites, key=lambda p: by_id[p].name):
            out.append(f"- {_link(by_id[pid])}")
        out.append("")

    dependents = sorted(
        (c for c in registry.concepts if concept.id in c.prerequisites),
        key=lambda c: c.name,
    )
    if dependents:
        out.append("## Leads to\n")
        for dependent in dependents:
            out.append(f"- {_link(dependent)}")
        out.append("")

    containing = [p for p in registry.paths if concept.id in p.concepts]
    if containing:
        out.append("## Paths that include it\n")
        for learning_path in containing:
            position = learning_path.concepts.index(concept.id) + 1
            out.append(
                f"- [{learning_path.name}](../paths/{learning_path.id}.md), "
                f"step {position} of {len(learning_path.concepts)}"
            )
        out.append("")

    out += [
        "## What will be here\n",
        "The [page contract](../explanation/the-page-contract.md) applies to every",
        "concept page, so this one will answer, in order:\n",
    ]
    out += [f"{i}. {section}" for i, section in enumerate(REQUIRED_SECTIONS, 1)]
    out.append("")
    return "\n".join(out)


def _front_matter(title: str, summary: str, audience: str = "new-user") -> str:
    """Serialise front matter as YAML, rather than assembling it with f-strings.

    Assembling it by hand produced 46 pages of invalid YAML, because the
    generated summary reads `Outline only: <name> is ...` and an unquoted colon
    starts a mapping. MkDocs' own metadata parser is more forgiving than YAML,
    so the build stayed green while nothing that used a real YAML parser could
    read those pages, and their meta description silently fell back to the
    site default. `yaml.safe_dump` quotes whatever needs quoting.
    """
    data = {
        "title": title,
        "summary": summary,
        # `placeholder`, not `reference`. A generated stub has no Diataxis
        # type, because it has no content; claiming one made the field mean
        # "not written yet" on 44 per cent of the corpus.
        "diataxis": "placeholder",
        "audience": audience,
        "generated": True,
    }
    body = yaml.safe_dump(data, sort_keys=False, default_flow_style=False,
                          allow_unicode=True)
    return f"---\n{body}---\n\n"


def coverage_page(registry: Registry) -> str:
    """Render the coverage matrix: every concept, why it is here, and its status.

    This is the checklist the reader sees. It is a view of the registry rather
    than a copy of it, so a concept cannot be ticked here while its page is
    missing: `fieldguide check` fails the build first.
    """
    counts = registry.completion
    total = len(registry.concepts)
    done = counts["complete"]

    out = [
        _front_matter(
            "Coverage",
            "Every concept this guide covers, where it came from, and whether it is written yet.",
        ),
        "# Coverage\n",
        f"**{done} of {total} concepts written.** "
        f"{counts['drafted']} drafted, {counts['planned']} planned.\n",
        "Each row names the concept, the posting line that put it on this list, and how",
        "strong that claim is. `quoted` is a verbatim phrase from a posting. `derived`",
        "means the posting requires the thing but these are not its words. `adjacent`",
        "means neither posting names it and the named work is impossible without it.\n",
        "Read that last column as a confidence rating on the concept's right to your time.\n",
    ]

    evidence = sum(1 for c in registry.concepts if c.has_evidence)
    by_provenance = {
        p: sum(1 for c in registry.concepts for d in c.demanded_by if d.provenance == p)
        for p in PROVENANCE
    }
    out += [
        "## Where this list comes from\n",
        f"- **{evidence} of {total}** concepts are backed by at least one verbatim quote.",
        f"- Claims by provenance: "
        + ", ".join(f"{n} {p}" for p, n in by_provenance.items())
        + ".\n",
        "A concept with no `quoted` claim is still here on an argument, and the argument",
        "is printed next to it so you can reject it.\n",
    ]

    for key, label in registry.categories.items():
        group = registry.in_category(key)
        if not group:
            continue
        out.append(f"## {label}\n")
        out.append("| Concept | Tier | Effort | Time | Status | Why it is on this list |")
        out.append("|---|---|---|---|---|---|")
        for concept in group:
            demand = concept.demanded_by[0]
            mark = {"complete": ":material-check:", "drafted": ":material-pencil:"}.get(
                concept.status, ":material-circle-outline:"
            )
            link = _link(concept, "concepts/")
            quote = demand.quote.replace("|", "\\|")
            if len(quote) > 120:
                quote = quote[:117] + "..."
            out.append(
                f"| {link} | {concept.tier} | {DIFFICULTY_LABEL[concept.difficulty]} "
                f"| {concept.time} | {mark} {concept.status} "
                f"| *{demand.source}, {demand.provenance}:* {quote} |"
            )
        out.append("")

    out += [
        "## The page contract\n",
        "Every concept page answers the same seven questions in the same order, and CI",
        "rejects one that does not:\n",
    ]
    out += [f"{i}. **{section}**" for i, section in enumerate(REQUIRED_SECTIONS, 1)]
    out += [
        "",
        "That is a content model applied to a learning corpus rather than to a product's",
        "documentation. The payoff is that the thirtieth page costs a reader nothing to",
        "navigate, because they learned the shape on the first.\n",
    ]
    return "\n".join(out)


def paths_index_page(registry: Registry) -> str:
    """Render the index of learning paths."""
    out = [
        _front_matter(
            "Learning paths",
            "Ordered routes through the concepts, for readers who want a curriculum rather than a reference.",
        ),
        "# Learning paths\n",
        "The [coverage matrix](../coverage.md) is a reference: it lists everything and",
        "assumes you know what you need. A path is the other thing a learner wants, which",
        "is somebody else's opinion about the order.\n",
        "Paths overlap on purpose. A concept that appears in four of them is load-bearing,",
        "and that is worth knowing before you pick where to start.\n",
    ]
    for learning_path in registry.paths:
        hours = _total_hours(registry, learning_path.concepts)
        out += [
            f"## [{learning_path.name}]({learning_path.id}.md)\n",
            f"*{learning_path.audience}*\n",
            f"{learning_path.summary}\n",
            f"{len(learning_path.concepts)} concepts, roughly {hours} hours.\n",
        ]

    counts: dict[str, int] = {}
    for learning_path in registry.paths:
        for concept_id in learning_path.concepts:
            counts[concept_id] = counts.get(concept_id, 0) + 1
    shared = sorted(
        (n, registry.by_id[cid].name, cid) for cid, n in counts.items() if n >= 3
    )
    if shared:
        out += [
            "## What every path shares\n",
            "Concepts that appear in three or more paths. If you only have a weekend,",
            "this is the list.\n",
            "| Concept | Paths |",
            "|---|---|",
        ]
        for n, _name, cid in sorted(shared, reverse=True):
            out.append(f"| {_link(registry.by_id[cid], '../concepts/')} | {n} |")
        out.append("")
    return "\n".join(out)


def path_page(registry: Registry, path_id: str) -> str:
    """Render one learning path as an ordered, annotated sequence."""
    learning_path = next(p for p in registry.paths if p.id == path_id)
    by_id = registry.by_id

    out = [
        _front_matter(learning_path.name, learning_path.summary),
        f"# {learning_path.name}\n",
        f"**Who this is for.** {learning_path.audience}\n",
        f"{learning_path.summary}\n",
        f"**{len(learning_path.concepts)} concepts, roughly "
        f"{_total_hours(registry, learning_path.concepts)} hours.** The order matters:",
        "each step assumes the ones above it.\n",
    ]

    # A path is a route through the graph, not a self-contained curriculum, so
    # steps may depend on concepts the path never teaches. Each step discloses
    # its own outside prerequisites below, but a reader deciding whether to
    # commit forty hours needs the entry state stated once, before step 1.
    # Measured across the seven paths, 27 step-prerequisite pairs point
    # outside their path, so this is not a corner case.
    assumed: list[str] = []
    for concept_id in learning_path.concepts:
        for prerequisite in by_id[concept_id].prerequisites:
            if prerequisite not in learning_path.concepts and prerequisite not in assumed:
                assumed.append(prerequisite)
    if assumed:
        names = ", ".join(_link(by_id[p], "../concepts/") for p in assumed)
        out.append(
            f"**Assumed before step 1.** This path does not teach {names}. "
            "Each step below repeats what it assumes.\n"
        )

    for position, concept_id in enumerate(learning_path.concepts, 1):
        concept = by_id[concept_id]
        inside = [p for p in concept.prerequisites if p in learning_path.concepts]
        outside = [p for p in concept.prerequisites if p not in learning_path.concepts]
        # `##`, not `###`. A path page's only other heading is its `#` title,
        # so `###` skips a level, which an accessibility check flags: screen
        # reader users navigate by heading level, and a jump from h1 to h3
        # reads as a missing section rather than a numbered step.
        out.append(f"## {position}. {_link(concept, '../concepts/')}\n")
        out.append(
            f"`{concept.tier}` · {DIFFICULTY_LABEL[concept.difficulty]} · {concept.time}\n"
        )
        out.append(f"{concept.demanded_by[0].quote}\n")
        if inside:
            names = ", ".join(by_id[p].name for p in inside)
            out.append(f"Builds on, earlier in this path: {names}.\n")
        if outside:
            names = ", ".join(_link(by_id[p], "../concepts/") for p in outside)
            out.append(f"Assumes, from outside this path: {names}.\n")

    return "\n".join(out)


def study_plan_page(registry: Registry) -> str:
    """Render a single dependency-respecting order through every concept.

    The paths above are curated. This is the mechanical answer: a topological
    sort of the whole graph, for a reader who wants everything and does not
    want to think about sequencing.
    """
    by_id = registry.by_id
    order = topological_order(registry)
    core = [cid for cid in order if by_id[cid].tier == "core"]

    out = [
        _front_matter(
            "The whole thing, in order",
            "Every concept in a dependency-respecting order, for readers who want the complete route.",
        ),
        "# The whole thing, in order\n",
        "The [learning paths](paths/index.md) are curated and opinionated. This page is",
        "the mechanical alternative: a topological sort of the prerequisite graph, so no",
        "concept appears before something it depends on.\n",
        "It is longer and less useful than a path. It is here because a complete ordering",
        "is the thing a reader asks for once they have decided to do all of it, and",
        "because generating it proves the graph has no cycles.\n",
        f"## Core only ({len(core)} concepts)\n",
        "The shortest complete route. Skip this at your peril and skip everything else",
        "without much cost.\n",
    ]
    for position, concept_id in enumerate(core, 1):
        concept = by_id[concept_id]
        out.append(f"{position}. {_link(concept, 'concepts/')} · {concept.time}")
    out.append("")

    out.append(f"## Everything ({len(order)} concepts)\n")
    out.append("| # | Concept | Category | Tier | Time |")
    out.append("|---|---|---|---|---|")
    for position, concept_id in enumerate(order, 1):
        concept = by_id[concept_id]
        out.append(
            f"| {position} | {_link(concept, 'concepts/')} | {registry.categories[concept.category]} "
            f"| {concept.tier} | {concept.time} |"
        )
    out.append("")
    return "\n".join(out)


def _total_hours(registry: Registry, concept_ids: tuple[str, ...]) -> int:
    """Sum the time estimates of some concepts, rounded to whole hours.

    Estimates are strings like `4h`, `45m`, `90m`. Anything unparseable counts
    as zero rather than raising, because a bad estimate should not fail a build
    over a number that was never precise.
    """
    by_id = registry.by_id
    minutes = 0
    for concept_id in concept_ids:
        raw = by_id[concept_id].time.strip().lower()
        try:
            if raw.endswith("h"):
                minutes += int(float(raw[:-1]) * 60)
            elif raw.endswith("m"):
                minutes += int(raw[:-1])
        except ValueError:
            continue
    return round(minutes / 60)


def demonstrated_page(registry: Registry, demonstrations) -> str:
    """Render the map of which concepts are implemented, and which are not.

    Both halves are the point. The overlap tells a reader where to go to see a
    concept working. The absence tells them which parts of this job a repository
    cannot prove, which is the more useful fact and the one a portfolio is
    tempted to leave out.
    """
    by_concept = demonstrations.by_concept
    total = len(registry.concepts)
    covered = len(by_concept)
    # Distinct concepts, not entries. A concept demonstrated in two
    # repositories has two entries, and the sentence below says "of them",
    # meaning of the covered concepts. Counting entries here double-counted
    # those and was invisible while every concept had exactly one entry.
    full = len({d.concept for d in demonstrations.entries if d.is_full})

    out = [
        _front_matter(
            "Demonstrated",
            "Which concepts have working code behind them, which file does the work, and which have none.",
        ),
        "# Demonstrated\n",
        "This guide is prose about how to do a job, and prose is cheap. This page",
        "records which concepts are also *implemented* somewhere you can open, down to",
        "the file that does the work.\n",
        f"**{covered} of {total} concepts have a demonstration**, {full} of them in full.",
        "The rest of this page is the other side of that number, which is the half worth",
        "reading.\n",
    ]

    for project in demonstrations.projects.values():
        count = sum(1 for d in demonstrations.entries if d.project == project.key)
        out += [
            f"## {project.name}\n",
            f"*{project.tagline}*\n",
            f"{project.summary}\n",
            f"[{project.url}]({project.url}) · demonstrates {count} concepts\n",
        ]

    out += [
        "## What is demonstrated\n",
        "`full` means the concept is implemented as this guide describes it. `partial`",
        "means something real is there and the concept page asks for more, and it is used",
        "literally: `rag` is partial because the records are retrieval-ready and nothing",
        "embeds them.\n",
    ]

    for key, label in registry.categories.items():
        group = registry.in_category(key)
        hits = [c for c in group if c.id in by_concept]
        if not hits:
            continue
        out += [
            f"### {label}\n",
            f"{len(hits)} of {len(group)}.\n",
            "| Concept | Extent | Artifact | What it does |",
            "|---|---|---|---|",
        ]
        for concept in hits:
            demo = by_concept[concept.id]
            mark = ":material-check-circle:" if demo.is_full else ":material-circle-half-full:"
            note = demo.note.replace("|", "\\|")
            out.append(
                f"| {_link(concept, 'concepts/')} | {mark} {demo.extent} "
                f"| `{demo.artifact}` | {note} |"
            )
        out.append("")

    # The inverse, by category, so the empty categories are impossible to miss.
    out += [
        "## What is not demonstrated\n",
        "Coverage by category, including the categories at zero.\n",
        "| Category | Demonstrated | Core concepts with nothing behind them |",
        "|---|---|---|",
    ]
    for key, label in registry.categories.items():
        group = registry.in_category(key)
        if not group:
            continue
        hits = sum(1 for c in group if c.id in by_concept)
        gaps = sum(1 for c in group if c.tier == "core" and c.id not in by_concept)
        out.append(f"| {label} | {hits}/{len(group)} | {gaps} |")
    out.append("")

    # Derived from the triage rather than written, because the prose that used
    # to stand here named four categories at zero and there is now one. A
    # hand-written explanation of a measured state goes stale the moment the
    # state moves, which is the defect this whole file exists to prevent.
    zero = [
        label
        for key, label in registry.categories.items()
        if registry.in_category(key)
        and not any(c.id in by_concept for c in registry.in_category(key))
    ]
    out += [
        "### Why the gaps are there\n",
        "Every concept with no demonstration carries a recorded reason, and the build",
        "fails on a concept that has neither. So this is a decision register rather",
        "than a list of things nobody got to.\n",
        "| Reason | Concepts | What it means |",
        "|---|---|---|",
    ]
    for reason, meaning in TRIAGE_REASONS.items():
        count = sum(1 for value in demonstrations.triage.values() if value == reason)
        if count:
            out.append(f"| `{reason}` | {count} | {meaning} |")
    out.append("")

    if demonstrations.ceilings:
        out += [
            "### What is demonstrated as far as it can be" + chr(10),
            "A gap closes when somebody does the work. A ceiling does not, and the",
            "difference is worth publishing: these concepts have a working mechanism and",
            "a stated reason why no amount of further code reaches `full`." + chr(10),
            "| Reason | Concepts | Why it stops there |",
            "|---|---|---|",
        ]
        for reason, meaning in CEILING_REASONS.items():
            listed = sorted(c for c, r in demonstrations.ceilings.items() if r == reason)
            if listed:
                out.append(f"| `{reason}` | {len(listed)} | {meaning} |")
        out.append("")
        for reason in CEILING_REASONS:
            listed = sorted(c for c, r in demonstrations.ceilings.items() if r == reason)
            if not listed:
                continue
            names = ", ".join(
                f"[{registry.by_id[c].name}](concepts/{c}.md)" for c in listed
            )
            out += [f"**`{reason}`:** {names}", ""]
    if zero:
        joined = ", ".join(zero)
        out += [
            f"The category at zero is {joined}, and that is not an oversight.",
            "Technical writing, reading code to verify accuracy, knowing where an LLM can",
            "be trusted, giving an architecture owner useful implementation feedback: these",
            "show up in prose and in how someone behaves in a review, not in a file. Each of",
            "those pages carries an account of how the skill would be demonstrated instead.\n",
        ]
    out += [
        "A portfolio that published only the first table would be the flattering half of",
        "the truth. The gaps are where the interview happens.\n",
    ]

    core_gaps = [
        c for c in registry.concepts if c.tier == "core" and c.id not in by_concept
    ]
    out += [
        f"### Every core concept with no demonstration ({len(core_gaps)})\n",
        "| Concept | Category | Reason |",
        "|---|---|---|",
    ]
    for concept in sorted(core_gaps, key=lambda c: (registry.categories[c.category], c.name)):
        reason = demonstrations.triage.get(concept.id, "unrecorded")
        out.append(
            f"| {_link(concept, 'concepts/')} | {registry.categories[concept.category]} "
            f"| `{reason}` |"
        )
    out.append("")
    return "\n".join(out)
