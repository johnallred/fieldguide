"""CHANGELOG.md held to the rules the release-notes page teaches.

The page's drill checks an invented release section against invented commits.
This is the same discipline applied to the guide's own changelog, with the one
rule that matters most adapted to a curriculum: every concept added since the
first version must be named under an `Added` heading, so a reader can find
out what is new without diffing the registry.
"""

from __future__ import annotations

import re
from pathlib import Path

from fieldguide.registry import load_registry

REPO = Path(__file__).resolve().parent.parent
TEXT = (REPO / "CHANGELOG.md").read_text(encoding="utf-8")

#: Keep a Changelog 1.1.0's six kinds of change, and nothing else.
KINDS = {"Added", "Changed", "Deprecated", "Removed", "Fixed", "Security"}
RELEASE = re.compile(r"^## \[(\d+)\.(\d+)\.(\d+)\] - (\S+)$", re.M)
#: How many concepts 0.1.0 had. Every concept beyond these was added later and
#: must be named in the changelog.
FIRST_RELEASE_CONCEPTS = 106


def releases():
    return [((int(a), int(b), int(c)), date) for a, b, c, date in RELEASE.findall(TEXT)]


def test_it_keeps_an_unreleased_section_first():
    headings = re.findall(r"^## (.+)$", TEXT, re.M)
    assert headings[0] == "[Unreleased]"


def test_dates_are_iso_8601():
    bad = [d for _, d in releases() if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", d)]
    assert not bad, bad


def test_the_newest_version_comes_first_and_is_the_package_version():
    versions = [v for v, _ in releases()]
    assert versions == sorted(versions, reverse=True)
    # A regex rather than tomllib, which needs Python 3.11 and this project
    # supports 3.10.
    package = re.search(r'^version = "([^"]+)"', (REPO / "pyproject.toml").read_text(
        encoding="utf-8"), re.M).group(1)
    assert ".".join(map(str, versions[0])) == package


def test_only_keep_a_changelog_headings():
    found = set(re.findall(r"^### (.+)$", TEXT, re.M))
    assert found <= KINDS, found - KINDS


def test_every_concept_added_since_the_first_release_is_named():
    added = set()
    for section in re.split(r"^### ", TEXT, flags=re.M)[1:]:
        heading, _, body = section.partition("\n")
        if heading.strip() == "Added":
            added |= set(re.findall(r"docs/concepts/([\w-]+)\.md", body))
    registry = load_registry(REPO / "concepts.yaml")
    ids = {c.id for c in registry.concepts}
    assert added <= ids, f"named but not in the registry: {sorted(added - ids)}"
    assert len(ids) - FIRST_RELEASE_CONCEPTS == len(added), (
        f"{len(ids) - FIRST_RELEASE_CONCEPTS} concepts were added since 0.1.0 and "
        f"the changelog names {len(added)}; add the new ones under Added"
    )
