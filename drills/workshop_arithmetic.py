#!/usr/bin/env python3
"""How much of a learning path fits in a workshop. Computed, not estimated.

    python3 drills/workshop_arithmetic.py

The `workshops` page argues that a three-hour workshop covers about one step of
a ten-step path. That argument rests on three numbers: the hours in a path, the
hands-on time a room actually offers, and how many concepts are short enough to
finish in one sitting. All three come from `concepts.yaml`, so all three move
when the corpus does, and the page's version of them went stale once already.

It named the ten-concept `first-week` path as the guide's shortest. It was,
until the six-concept `domain-context` path was added and took the title by ten
hours. Nothing caught it: the claim was prose, the registry was data, and no
test connected them. This drill is that connection, and it prints the shortest
path by name so the superlative cannot drift again without the page failing.

The timing half of that page's golden path is deliberately not here. Installing
four packages and timing it needs a network and a stopwatch, and the answer is
different on every machine; the page states it as one measurement on one
machine, which is all it ever was.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from fieldguide.registry import load_registry  # noqa: E402

#: What a three-hour slot really offers once setup, questions and a break are
#: taken out. Generous rather than pessimistic: the argument does not need the
#: pessimistic version to hold.
HANDS_ON_HOURS = 2

#: A concept a workshop could plausibly finish in one sitting.
SITTING_HOURS = 3


def hours(time: str) -> int:
    """`4h` -> 4. The registry stores time as a string with a unit."""
    return int(time.rstrip("h"))


def main() -> int:
    registry = load_registry(Path(__file__).resolve().parent.parent / "concepts.yaml")
    by_id = {concept.id: concept for concept in registry.concepts}

    def total(path) -> int:
        return sum(hours(by_id[c].time) for c in path.concepts)

    first_week = next(p for p in registry.paths if p.id == "first-week")
    shortest = min(registry.paths, key=total)

    print("step 3: the arithmetic that kills most workshop plans\n")
    # Width comes from the data: the registry's longest name decides the
    # column, so adding a concept cannot quietly break the alignment.
    width = max(len(by_id[c].name) for c in first_week.concepts)
    for concept_id in first_week.concepts:
        concept = by_id[concept_id]
        print("  %-*s %2dh" % (width, concept.name, hours(concept.time)))
    print("  %*s %2dh" % (width, "total", total(first_week)))

    share = round(HANDS_ON_HOURS / total(first_week) * 100)
    short_enough = [c for c in registry.concepts if hours(c.time) <= SITTING_HOURS]

    print()
    print(
        "two hours against the %d-hour first-week path: %d%%"
        % (total(first_week), share)
    )
    print(
        "shortest path in the guide: %s, %d concepts, %dh (%d%%)"
        % (
            shortest.id,
            len(shortest.concepts),
            total(shortest),
            round(HANDS_ON_HOURS / total(shortest) * 100),
        )
    )
    print(
        "concepts in this corpus of %dh or less: %d/%d"
        % (SITTING_HOURS, len(short_enough), len(registry.concepts))
    )

    # A workshop covering "about one step" is the claim; check it is still the
    # right order of magnitude rather than asserting the exact percentage,
    # which is the page's job and the test's.
    steps = HANDS_ON_HOURS / (total(first_week) / len(first_week.concepts))
    print("\nsteps of that path a two-hour slot buys: %.1f" % steps)
    if steps > 2:
        print("note: a slot now buys more than two steps; the page overstates the squeeze")
    return 0


if __name__ == "__main__":
    sys.exit(main())
