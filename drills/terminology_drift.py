#!/usr/bin/env python3
"""Measuring terminology drift, and the reason the obvious measurement lies.

    python3 drills/terminology_drift.py

Reproduces the three states the `terminology-drift` page quotes: a naive
conformance count, the diagnosis of why it flatters, and the masked count that
corrects it. All four sample pages are the ones the page tells you to write,
and a test asserts they still are.

The finding is structural rather than incidental. A deprecated term is usually
the canonical term plus something: a hyphen, a suffix, a product word. So a
word-boundary search for the canonical term matches inside its own deprecated
forms, and counts drift as conformance. The worse the drift, the more the
measurement flatters, which is the opposite of what a metric is for.
"""

from __future__ import annotations

import re
import sys
import tempfile
from collections import Counter
from pathlib import Path

import yaml

#: The page's step-1 heredocs, verbatim and in order. A test asserts they match.
GLOSSARY = """\
terms:
  - canonical: widget
    deprecated: [Widget CLI, widget-cli, WidgetCLI]
  - canonical: data set
    deprecated: [dataset, data-set]
  - canonical: access token
    deprecated: [API key, apikey, auth token]
"""

PAGE_A = """\
# Install
Install widget, then create an access token.
"""

PAGE_B = """\
# Configure
Point the Widget CLI at your dataset. Use your API key.
"""

PAGE_C = """\
# Troubleshoot
If widget-cli fails, check the auth token and the data-set path.
"""

#: Step 5 rewrites two pages with `printf` rather than a heredoc, so these are
#: not part of the heredoc contract; they are checked by the output instead.
PAGE_B_FIXED = "# Configure\nPoint widget at your data set. Use your access token.\n"
PAGE_C_FIXED = (
    "# Troubleshoot\nIf widget fails, check the access token and the data set path.\n"
)


def measure(docs: Path, terms: list[dict], mask: bool) -> tuple[list, Counter]:
    """Count canonical and deprecated uses per term.

    With `mask=False` this is the measurement almost everyone writes first.
    With `mask=True` each deprecated form is blanked out of the text before the
    canonical term is counted, so a match inside a variant cannot be scored as
    conformance. That one difference is the whole page.
    """
    rows, per_page = [], Counter()
    for entry in terms:
        canon = entry["canonical"]
        # Longest first, so "API key" is consumed before any shorter variant.
        deprecated = sorted(entry["deprecated"], key=len, reverse=True)
        variants, conformant = Counter(), 0

        for page in sorted(docs.rglob("*.md")):
            text = page.read_text(encoding="utf-8")
            for bad in deprecated:
                pattern = re.compile(r"\b" + re.escape(bad) + r"\b")
                found = pattern.findall(text)
                if found:
                    variants[bad] += len(found)
                    per_page[page.relative_to(docs.parent).as_posix()] += len(found)
                if mask:
                    text = pattern.sub("\x00" * len(bad), text)
            conformant += len(re.findall(r"\b" + re.escape(canon) + r"\b", text, re.I))

        rows.append((canon, conformant, conformant + sum(variants.values()), variants))
    return rows, per_page


def report(rows: list, per_page: Counter, show_variants: bool = True) -> int:
    header = f"{'canonical':16} {'conformant':>10} {'total':>6} {'rate':>6}"
    print(header + ("  variants" if show_variants else ""))
    for canon, ok, total, variants in rows:
        rate = f"{100 * ok // total}%" if total else "n/a"
        line = f"{canon:16} {ok:>10} {total:>6} {rate:>6}"
        if show_variants:
            line += "  " + ", ".join(f"{k}({n})" for k, n in variants.most_common())
        print(line.rstrip())
    drifted = sum(sum(v.values()) for *_rest, v in rows)
    if show_variants and per_page:
        print()
        print("worst pages:", ", ".join(f"{p} ({n})" for p, n in per_page.most_common(3)))
    print(f"\n{'FAIL' if drifted else 'ok'}: {drifted} deprecated usage(s)")
    return 1 if drifted else 0


def why_it_flatters(docs: Path) -> None:
    """Step 3: print every match of the canonical term with its context."""
    pattern = re.compile(r"\bwidget\b", re.I)
    for page in sorted(docs.rglob("*.md")):
        text = page.read_text(encoding="utf-8")
        for match in pattern.finditer(text):
            window = text[max(0, match.start() - 12) : match.end() + 12]
            print(f"{page.relative_to(docs.parent).as_posix()}: ...{window!r}...")


def main() -> int:
    terms = yaml.safe_load(GLOSSARY)["terms"]
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        docs = root / "docs"
        docs.mkdir()
        for name, body in (("a.md", PAGE_A), ("b.md", PAGE_B), ("c.md", PAGE_C)):
            (docs / name).write_text(body, encoding="utf-8")

        print("step 2: the obvious measurement\n")
        naive_rows, naive_pages = measure(docs, terms, mask=False)
        report(naive_rows, naive_pages)

        print("\nstep 3: find out why\n")
        why_it_flatters(docs)

        print("\nstep 4: mask before you count\n")
        masked_rows, masked_pages = measure(docs, terms, mask=True)
        masked = report(masked_rows, masked_pages)

        print("\nstep 5: confirm it goes green\n")
        (docs / "b.md").write_text(PAGE_B_FIXED, encoding="utf-8")
        (docs / "c.md").write_text(PAGE_C_FIXED, encoding="utf-8")
        clean_rows, clean_pages = measure(docs, terms, mask=True)
        clean = report(clean_rows, clean_pages, show_variants=False)

    naive_widget = naive_rows[0][1]
    masked_widget = masked_rows[0][1]
    print(
        f"\nThe correction: {naive_widget} canonical uses of 'widget' become "
        f"{masked_widget} once its own variants stop counting as conformance."
    )
    ok = (masked, clean) == (1, 0) and naive_widget > masked_widget
    if not ok:
        print("\nunexpected: the naive count no longer flatters", file=sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
