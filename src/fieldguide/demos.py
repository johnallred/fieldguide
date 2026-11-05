"""Which concepts have a working demonstration, and where.

This guide is prose about how to do a job. `demonstrations.yaml` records which
of its concepts are also *implemented* somewhere a reader can open, down to the
file that does the work.

The module's job is mostly to stop that mapping becoming a lie. A claim that a
concept is demonstrated is the strongest claim this guide makes about itself,
so it gets the strictest validation: a concept id that does not exist fails the
build, and so does a duplicate entry or an unknown project key.

The generated page publishes the inverse as well. Four whole categories have no
demonstration at all, and that absence is the more informative half: it marks
the parts of the work that a repository cannot prove.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .registry import Registry

#: Closed vocabulary. `partial` means something real exists and the concept
#: page asks for more; it is not a hedge for "sort of".
EXTENTS = ("full", "partial")

#: Why a concept has no demonstration. Every undemonstrated concept carries one
#: of these, so "not demonstrated" is a decision on the record rather than an
#: absence nobody has looked at.
#:
#: The distinction that matters is between `declined` and the rest. Adopting
#: Sphinx, Antora, Docusaurus, MDX, reStructuredText, versioning and
#: localization in a twelve-page single-author project to demonstrate knowing
#: about them would be theatre, and the pages say so. That is a different
#: statement from "nobody has got to it", and collapsing the two is how a gap
#: register stops being read.
#: Why a demonstration can never reach `full` in this project, regardless of
#: how much more code is written. A ceiling is not a gap: a gap closes when
#: somebody does the work, and a ceiling does not.
#:
#: This exists because two concepts, `instructional-design` and
#: `cognitive-load`, kept being proposed for promotion as the mechanisms
#: behind them improved. The mechanisms did improve, twice. Neither promotion
#: was right, and arguing it per concept each time meant the reasoning lived
#: in nobody's head twice over. It also turned out not to be two concepts: a
#: dozen entries have the same ceiling for the same reason.
CEILING_REASONS = {
    "no-audience": (
        "the corpus-side half is built and measured; the reader-side half "
        "needs readers, and this project has none"
    ),
    "not-published": (
        "the mechanism runs and gates, but nothing is deployed, so no "
        "post-publication behaviour exists to observe"
    ),
}


TRIAGE_REASONS = {
    "planned": "demonstrable, and on the backlog to build",
    "declined": "demonstrating it would mean adopting a tool or process this project does not need",
    "needs-organisation": "the evidence is a process, a conversation or a decision in someone else's repository",
    "blocked": "needs a model, weights or hardware this environment does not have",
}


class DemonstrationError(ValueError):
    """Raised when the demonstration mapping is malformed or points at nothing."""


@dataclass(frozen=True)
class Project:
    """A companion repository that implements some of the curriculum."""

    key: str
    name: str
    tagline: str
    summary: str
    url: str


@dataclass(frozen=True)
class Demonstration:
    """One concept, implemented in one place.

    Attributes:
        concept: Concept id from `concepts.yaml`.
        project: Key into the projects map.
        artifact: The file or feature that does the work, specific enough to open.
        extent: `full` or `partial`.
        note: What the artifact actually does, in one line.
    """

    concept: str
    project: str
    artifact: str
    extent: str
    note: str

    @property
    def is_full(self) -> bool:
        return self.extent == "full"


@dataclass(frozen=True)
class Demonstrations:
    """The whole mapping, validated against a registry."""

    projects: dict[str, Project]
    entries: tuple[Demonstration, ...]
    triage: dict[str, str] = field(default_factory=dict)
    #: concept id -> ceiling reason, for entries that cannot reach `full`.
    ceilings: dict[str, str] = field(default_factory=dict)

    @property
    def by_concept(self) -> dict[str, Demonstration]:
        return {d.concept: d for d in self.entries}

    def covers(self, concept_id: str) -> bool:
        return concept_id in self.by_concept

    def coverage(self, registry: Registry, concept_ids: list[str]) -> tuple[int, int]:
        """Return (demonstrated, total) over some concepts."""
        return sum(1 for cid in concept_ids if self.covers(cid)), len(concept_ids)


def load_demonstrations(path: Path, registry: Registry) -> Demonstrations:
    """Parse the mapping and check every claim resolves.

    Args:
        path: The `demonstrations.yaml` file.
        registry: A loaded registry, used to validate concept ids.

    Raises:
        DemonstrationError: On an unknown concept id, an unknown project key, a
            duplicate entry, a bad extent, or a missing field. A concept id that
            no longer exists is the likeliest failure as the curriculum changes,
            and the one most worth failing loudly: a stale mapping silently
            under-reports what is implemented.
    """
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise DemonstrationError(f"{path}: expected a mapping at the top level")

    projects: dict[str, Project] = {}
    for key, value in (raw.get("projects") or {}).items():
        if not isinstance(value, dict):
            raise DemonstrationError(f"{path}: project {key!r} must be a mapping")
        for field in ("name", "tagline", "summary", "url"):
            if field not in value:
                raise DemonstrationError(f"{path}: project {key!r} is missing {field!r}")
        projects[key] = Project(
            key=key,
            name=str(value["name"]),
            tagline=str(value["tagline"]).strip(),
            summary=str(value["summary"]).strip(),
            url=str(value["url"]),
        )
    if not projects:
        raise DemonstrationError(f"{path}: no projects defined")

    known = set(registry.by_id)
    entries: list[Demonstration] = []
    seen: set[tuple[str, str]] = set()

    for index, item in enumerate(raw.get("demonstrates") or []):
        label = f"{path} demonstrates[{index}]"
        if not isinstance(item, dict):
            raise DemonstrationError(f"{label}: must be a mapping")
        for field in ("concept", "project", "artifact", "extent", "note"):
            if field not in item:
                raise DemonstrationError(f"{label}: missing {field!r}")

        concept = str(item["concept"])
        project = str(item["project"])
        extent = str(item["extent"])

        if concept not in known:
            raise DemonstrationError(
                f"{label}: {concept!r} is not a concept in the registry. "
                "A renamed or removed concept leaves a stale claim here, which "
                "under-reports what is implemented."
            )
        if project not in projects:
            raise DemonstrationError(
                f"{label}: unknown project {project!r}; known projects are {sorted(projects)}"
            )
        if extent not in EXTENTS:
            raise DemonstrationError(
                f"{label}: extent must be one of {list(EXTENTS)}, got {extent!r}"
            )
        if (concept, project) in seen:
            raise DemonstrationError(f"{label}: {concept!r} is already claimed by {project!r}")
        seen.add((concept, project))

        entries.append(
            Demonstration(
                concept=concept,
                project=project,
                artifact=str(item["artifact"]),
                extent=extent,
                note=str(item["note"]).strip(),
            )
        )

    if not entries:
        raise DemonstrationError(f"{path}: no demonstrations listed")

    demonstrated = {entry.concept for entry in entries}
    triage: dict[str, str] = {}
    raw_triage = raw.get("triage") or {}
    if not isinstance(raw_triage, dict):
        raise DemonstrationError(f"{path}: triage must be a mapping of concept id to reason")

    for concept, reason in raw_triage.items():
        label = f"{path} triage[{concept!r}]"
        if concept not in known:
            raise DemonstrationError(f"{label}: unknown concept id")
        if reason not in TRIAGE_REASONS:
            raise DemonstrationError(
                f"{label}: reason must be one of {sorted(TRIAGE_REASONS)}, got {reason!r}"
            )
        if concept in demonstrated:
            raise DemonstrationError(
                f"{label}: also has a demonstration entry, so one of the two is wrong"
            )
        triage[concept] = str(reason)

    # The point of the register: every concept is either demonstrated or has a
    # recorded reason why not. Without this, a new concept joins the curriculum
    # undemonstrated and unexamined, which is the state this file exists to end.
    ceilings: dict[str, str] = {}
    raw_ceilings = raw.get("ceilings") or {}
    if not isinstance(raw_ceilings, dict):
        raise DemonstrationError(
            f"{path}: ceilings must be a mapping of ceiling reason to concept ids"
        )
    for reason, concepts in raw_ceilings.items():
        if reason not in CEILING_REASONS:
            raise DemonstrationError(
                f"{path} ceilings[{reason!r}]: must be one of "
                f"{sorted(CEILING_REASONS)}"
            )
        if not isinstance(concepts, list):
            raise DemonstrationError(f"{path} ceilings[{reason!r}]: must be a list")
        for concept in concepts:
            if concept not in known:
                raise DemonstrationError(
                    f"{path} ceilings[{reason!r}]: {concept!r} is not a concept"
                )
            if concept not in demonstrated:
                raise DemonstrationError(
                    f"{path} ceilings[{reason!r}]: {concept!r} has no demonstration, "
                    "so it has a gap rather than a ceiling"
                )
            if any(e.concept == concept and e.extent == "full" for e in entries):
                raise DemonstrationError(
                    f"{path} ceilings[{reason!r}]: {concept!r} is recorded as "
                    "`full`, which contradicts a ceiling"
                )
            ceilings[concept] = str(reason)

    unexamined = sorted(set(known) - demonstrated - set(triage))
    if unexamined:
        raise DemonstrationError(
            f"{path}: neither demonstrated nor triaged, so nobody has decided: "
            f"{', '.join(unexamined)}"
        )

    return Demonstrations(
        projects=projects,
        entries=tuple(entries),
        triage=triage,
        ceilings=ceilings,
    )
