"""Command line interface for the field guide.

    fieldguide check          validate the registry against the docs tree
    fieldguide build          regenerate coverage, paths, and the study plan
    fieldguide new CONCEPT    scaffold a page that satisfies the contract
    fieldguide status         what is written, what is left, what to do next
    fieldguide render SITE    assert every fenced sample is code on the page
    fieldguide release-check  walk the release workflow, step by step

`check` is the gate. `build` is the generator. Both run in CI, and `build`
runs with `--check` there so a pull request that changes the registry without
regenerating the views fails instead of shipping a stale index.

`render` is the gate a strict build cannot be: it runs after `mkdocs build`
and compares fenced source against the `<pre>` content of the built page. It
exists because seven pages in this repository once shipped with code samples
demoted to prose, or dropped outright, while every other check passed.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .audit import audit
from .demos import DemonstrationError, load_demonstrations
from .dialect import findings as dialect_findings
from .dialect import front_matter_findings
from .fences import fence_findings, fenced_source_lines, unrendered_samples
from .generate import (
    coverage_page,
    demonstrated_page,
    path_page,
    paths_index_page,
    placeholder_page,
    study_plan_page,
)
from .release import STEPS, Context, release_check
from .registry import (
    RegistryError,
    load_registry,
    validate_against_tree,
)
from .scaffold import ScaffoldError, new_concept_page, write_page

DEFAULT_REGISTRY = Path("concepts.yaml")
DEFAULT_DOCS = Path("docs")


DEFAULT_DEMOS = Path("demonstrations.yaml")


def _common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--docs", type=Path, default=DEFAULT_DOCS)
    parser.add_argument("--demos", type=Path, default=DEFAULT_DEMOS)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="fieldguide", description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("check", help="Validate the registry against the docs tree")
    _common(check)
    check.add_argument(
        "--strict-sources",
        action="store_true",
        help="Also fail when a concept has no verbatim posting quote",
    )

    build = sub.add_parser("build", help="Regenerate the pages derived from the registry")
    _common(build)
    build.add_argument(
        "--check",
        action="store_true",
        help="Fail if a generated page is out of date instead of rewriting it",
    )

    new = sub.add_parser("new", help="Scaffold a concept page")
    _common(new)
    new.add_argument("concept", help="Concept id, as it appears in the registry")
    new.add_argument("--dry-run", action="store_true", help="Print instead of writing")

    status = sub.add_parser("status", help="Show progress and suggest what to write next")
    _common(status)

    audit_cmd = sub.add_parser(
        "audit", help="Measure the corpus: every figure the pages quote about it"
    )
    _common(audit_cmd)

    release = sub.add_parser(
        "release-check", help="Walk the release workflow, one named step at a time"
    )
    _common(release)
    release.add_argument(
        "--report-only",
        action="store_true",
        help="Print the record and exit 0 even when steps block",
    )
    release.add_argument(
        "--everything-gates",
        action="store_true",
        help="Stop at the first blocked step, the way a break-on-failure loop does",
    )

    render = sub.add_parser(
        "render", help="Assert every fenced sample renders as code on the built site"
    )
    _common(render)
    render.add_argument(
        "site",
        type=Path,
        nargs="?",
        default=Path("site"),
        help="Built site directory (default: site)",
    )

    return parser


def cmd_check(args: argparse.Namespace) -> int:
    registry = load_registry(args.registry)
    # Validated here as well as at build time, so a stale concept id in the
    # demonstration map fails `check` rather than waiting for a regeneration.
    demos = load_demonstrations(args.demos, registry)
    findings = validate_against_tree(registry, args.docs)
    print(findings.render())
    print(
        f"ok: {len(demos.entries)} demonstrations resolve to real concepts "
        f"across {len(demos.projects)} project(s)"
    )

    # Fence structure, which nothing else here can see. A golden path that
    # writes Markdown with a heredoc can close its own code block early, and
    # the result is a green build and a wrong page.
    fences = [f for page in sorted(args.docs.rglob("*.md")) for f in fence_findings(page)]
    if fences:
        print(f"\nFAIL: {len(fences)} fence problem(s)", file=sys.stderr)
        for finding in fences:
            print(f"  {finding}", file=sys.stderr)
        return 1
    print("ok: fence structure is sound in every page")

    # Front matter is the machine-readable half of a page, and MkDocs' own
    # metadata parser is more forgiving than YAML, so an unparseable page
    # builds cleanly and is invisible to every retrieval tool.
    front = front_matter_findings(args.docs)
    if front:
        print(f"\nFAIL: {len(front)} page(s) with unparseable front matter", file=sys.stderr)
        for finding in front:
            print(f"  {finding}", file=sys.stderr)
        return 1
    print("ok: every page's front matter parses as YAML")

    if not findings.ok:
        return 1
    if args.strict_sources and findings.unsourced:
        print(f"\nFAIL: {len(findings.unsourced)} concepts have no verbatim quote", file=sys.stderr)
        return 1
    return 0


def cmd_build(args: argparse.Namespace) -> int:
    registry = load_registry(args.registry)

    targets: dict[Path, str] = {
        args.docs / "coverage.md": coverage_page(registry),
        args.docs / "study-plan.md": study_plan_page(registry),
        args.docs / "paths" / "index.md": paths_index_page(registry),
        args.docs / "demonstrated.md": demonstrated_page(
            registry, load_demonstrations(args.demos, registry)
        ),
    }
    for learning_path in registry.paths:
        targets[args.docs / "paths" / f"{learning_path.id}.md"] = path_page(
            registry, learning_path.id
        )

    # A placeholder for every concept with no prose yet, so the prerequisite
    # graph is navigable and the strict build stays green while the corpus is
    # half written. A hand-written page is never touched: only a `planned`
    # concept gets one, and setting status past `planned` hands the file to its
    # author permanently.
    for concept in registry.concepts:
        if concept.status != "planned":
            continue
        page = args.docs / concept.page
        if page.exists() and "generated: true" not in page.read_text(encoding="utf-8"):
            continue
        targets[page] = placeholder_page(registry, concept.id)

    stale: list[Path] = []
    for path, text in targets.items():
        current = path.read_text(encoding="utf-8") if path.exists() else None
        if current == text:
            continue
        if args.check:
            stale.append(path)
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    if args.check:
        if stale:
            print("FAIL: generated pages are out of date:", file=sys.stderr)
            for path in stale:
                print(f"  {path}", file=sys.stderr)
            print("\nRun `fieldguide build` and commit the result.", file=sys.stderr)
            return 1
        print(f"ok: {len(targets)} generated pages are up to date")
        return 0

    print(f"built {len(targets)} pages from {args.registry}")
    return 0


def cmd_new(args: argparse.Namespace) -> int:
    registry = load_registry(args.registry)
    try:
        page = new_concept_page(registry, args.docs, args.concept)
    except ScaffoldError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.dry_run:
        print(f"# would write {page.path}")
        print(page.text, end="")
        return 0

    path = write_page(page)
    print(f"created {path}")
    print("next: write the seven sections, then set status to drafted in concepts.yaml")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    registry = load_registry(args.registry)
    counts = registry.completion
    total = len(registry.concepts)
    done = counts["complete"]

    bar_width = 40
    filled = round(bar_width * done / total) if total else 0
    print(f"\n  [{'#' * filled}{'.' * (bar_width - filled)}]  {done}/{total} complete\n")
    for status in ("complete", "drafted", "planned"):
        print(f"  {status:<9} {counts[status]:>3}")

    print("\n  by category")
    for key, label in registry.categories.items():
        group = registry.in_category(key)
        if not group:
            continue
        finished = sum(1 for c in group if c.status == "complete")
        print(f"    {label:<42} {finished:>2}/{len(group)}")

    print("\n  by tier")
    for tier in ("core", "supporting", "context"):
        group = registry.of_tier(tier)
        finished = sum(1 for c in group if c.status == "complete")
        print(f"    {tier:<12} {finished:>2}/{len(group)}")

    # What to write next: an unwritten concept whose prerequisites are all
    # done. Writing in dependency order means every page can link backwards to
    # something that exists, which is what keeps a corpus navigable while it is
    # still half built.
    by_id = registry.by_id
    ready = [
        c
        for c in registry.concepts
        if c.status != "complete"
        and all(by_id[p].status == "complete" for p in c.prerequisites)
    ]
    order = {"core": 0, "supporting": 1, "context": 2}
    ready.sort(key=lambda c: (order[c.tier], c.difficulty, c.name))

    if ready:
        print("\n  ready to write (prerequisites are done)")
        for concept in ready[:8]:
            print(f"    {concept.id:<28} {concept.tier:<11} {concept.time}")
    else:
        print("\n  nothing is unblocked; every remaining concept waits on another")

    blocked = [c for c in registry.concepts if c.status != "complete" and c not in ready]
    if blocked:
        print(f"\n  {len(blocked)} concepts still blocked by an unwritten prerequisite")
    print()
    return 0


def cmd_render(args: argparse.Namespace) -> int:
    if not args.site.exists():
        print(
            f"error: {args.site} does not exist; run `mkdocs build` first",
            file=sys.stderr,
        )
        return 2

    findings = unrendered_samples(args.docs, args.site)
    checked = sum(
        len(fenced_source_lines(page)) for page in sorted(args.docs.rglob("*.md"))
    )
    for finding in findings:
        print(f"RENDER  {finding}", file=sys.stderr)

    # The same principle applied to inline syntax rather than code blocks:
    # an unsupported Markdown construct is passed through as literal text, so
    # its markers survive into the HTML the reader receives.
    dialect = dialect_findings(args.docs, args.site)
    for finding in dialect:
        print(f"DIALECT {finding}", file=sys.stderr)

    if findings or dialect:
        print(
            f"\nFAIL: {checked} fenced lines checked, {len(findings)} are not code "
            f"on the built page; {len(dialect)} unsupported construct(s) reach "
            f"the reader as literal text",
            file=sys.stderr,
        )
        return 1
    print(
        f"ok: {checked} fenced lines checked, every one renders as code; "
        f"no unsupported Markdown construct reaches the reader"
    )
    return 0


def cmd_audit(args: argparse.Namespace) -> int:
    """Print the measurements the pages quote about the corpus.

    These were loose scripts until the figures went stale: every page written
    before the corpus finished growing quoted a count from the corpus as it
    stood. A number a reader cannot reproduce is a number they have to take on
    trust, which is the opposite of what this guide argues for.
    """
    registry = load_registry(args.registry)
    print(audit(registry, args.docs).render())
    return 0


def cmd_release_check(args: argparse.Namespace) -> int:
    """Walk the release workflow and print the record it produces.

    The exit code is the point of the command, so `--report-only` exists for
    the advice the `release-readiness` page gives about introducing a gate:
    run it in report-only mode for a few releases, keep the numbers, and
    propose the gate with data rather than on principle.
    """
    context = Context(
        root=Path.cwd(), registry=args.registry, docs=args.docs, demos=args.demos
    )
    run = release_check(context, everything_gates=args.everything_gates)
    print(run.render(len(STEPS)))
    if args.report_only and not run.ok:
        print("\nreport-only: exiting 0 so this can run before it blocks")
        return 0
    return 0 if run.ok else 1


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return {
            "check": cmd_check,
            "build": cmd_build,
            "new": cmd_new,
            "status": cmd_status,
            "render": cmd_render,
            "audit": cmd_audit,
            "release-check": cmd_release_check,
        }[args.command](args)
    except RegistryError as exc:
        print(f"registry error: {exc}", file=sys.stderr)
        return 2
    except DemonstrationError as exc:
        print(f"demonstration map error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
