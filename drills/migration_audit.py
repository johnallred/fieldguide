#!/usr/bin/env python3
"""Audit a wiki-to-docs-as-code migration before the old site is switched off.

    python3 drills/migration_audit.py                              # embedded samples
    python3 drills/migration_audit.py inventory.csv docs/          # your migration
    python3 drills/migration_audit.py --redirects inventory.csv    # the redirect map

inventory.csv lists every old page with its traffic, a decision (migrate,
merge or retire) and, where there is one, the new page it goes to. docs/ holds
the converted Markdown. Four checks:

- every migrated or merged page has a destination that exists;
- no retired page that people still read is left without a redirect;
- no converted page still carries markup from the old system: raw HTML,
  Confluence-style `{macro}` tags, `[[wiki links]]`, or links to the old host;
- how much of the old traffic still lands somewhere.

The pages and their traffic are invented for the exercise.
"""

from __future__ import annotations

import csv
import io
import os
import re
import sys
import tempfile

OLD_HOST = "wiki.example.com"
READ = 100  # 90-day views above which a retired page still needs a redirect

INVENTORY = """\
old_url,views_90d,decision,new
/display/DOCS/Getting+Started,1840,migrate,getting-started.md
/display/DOCS/Install+on+Linux,920,merge,getting-started.md
/display/DOCS/Retry+Settings,610,migrate,configure-retries.md
/display/DOCS/Retry+Settings+(old),12,retire,
/display/DOCS/API+Keys,455,retire,
/display/DOCS/Troubleshooting,380,migrate,troubleshooting.md
/display/DOCS/FAQ,700,merge,troubleshooting.md
/display/DOCS/2019+Offsite+Notes,3,retire,
"""

GETTING_STARTED = """\
# Getting started

Install the client with `pip install widget-client`, then run `widget sync`.
"""

CONFIGURE_RETRIES = """\
# Configure retries

{info}Retries count retries, not attempts.{info}

Set <span style="color:red">retries</span> on the client.
"""

TROUBLESHOOTING = """\
# Troubleshooting

If a request fails with 401, see [[API Keys]] or
[the key page](https://wiki.example.com/display/DOCS/API+Keys).
"""

INVENTORY_FIXED = INVENTORY.replace(
    "/display/DOCS/API+Keys,455,retire,",
    "/display/DOCS/API+Keys,455,migrate,api-keys.md")

API_KEYS = """\
# API keys

Create a key in the console, deploy it, then revoke the old one.
"""

CONFIGURE_RETRIES_FIXED = """\
# Configure retries

!!! note
    Retries count retries, not attempts.

Set `retries` on the client.
"""

TROUBLESHOOTING_FIXED = """\
# Troubleshooting

If a request fails with 401, see [API keys](api-keys.md).
"""

RESIDUE = [
    ("raw HTML", re.compile(r"</?(?:span|div|font|table|br)\b[^>]*>", re.I)),
    ("wiki macro", re.compile(r"\{(?:info|note|warning|code|panel|toc)[^}]*\}")),
    ("wiki link", re.compile(r"\[\[[^\]]+\]\]")),
    ("old host link", re.compile(re.escape(OLD_HOST))),
]


def rows(inventory_text: str) -> list[dict]:
    return list(csv.DictReader(io.StringIO(inventory_text)))


def audit(inventory_text: str, docs: str) -> int:
    pages = rows(inventory_text)
    found = []
    for p in pages:
        if p["decision"] in ("migrate", "merge"):
            if not os.path.exists(os.path.join(docs, p["new"])):
                found.append(f"MISSING  {p['old_url']} -> {p['new']}: no such page")
        elif int(p["views_90d"]) >= READ and not p["new"]:
            found.append(f"RETIRED  {p['old_url']} ({p['views_90d']} views) has no redirect")
    for name in sorted(os.listdir(docs)):
        text = open(os.path.join(docs, name), encoding="utf-8").read()
        for label, pattern in RESIDUE:
            for match in pattern.findall(text):
                found.append(f"RESIDUE  {name}: {label} {match}")
    total = sum(int(p["views_90d"]) for p in pages)
    kept = sum(int(p["views_90d"]) for p in pages if p["new"])
    for line in found:
        print(line)
    print(f"{len(found)} finding(s); {kept}/{total} views ({100 * kept / total:.1f}%) land on a new page")
    return len(found)


def redirects(inventory_text: str) -> None:
    for p in rows(inventory_text):
        if p["new"]:
            print(f"{p['old_url']}  ->  /{p['new'][:-3]}/")


def write(docs: str, files: dict[str, str]) -> None:
    for name, text in files.items():
        with open(os.path.join(docs, name), "w", encoding="utf-8") as handle:
            handle.write(text)


def main() -> int:
    args = sys.argv[1:]
    if args[:1] == ["--redirects"]:
        with open(args[1], encoding="utf-8") as handle:
            redirects(handle.read())
        return 0
    if len(args) == 2:
        with open(args[0], encoding="utf-8") as handle:
            return 1 if audit(handle.read(), args[1]) else 0
    with tempfile.TemporaryDirectory() as docs:
        write(docs, {"getting-started.md": GETTING_STARTED,
                     "configure-retries.md": CONFIGURE_RETRIES,
                     "troubleshooting.md": TROUBLESHOOTING})
        print("== first pass")
        audit(INVENTORY, docs)
        write(docs, {"api-keys.md": API_KEYS,
                     "configure-retries.md": CONFIGURE_RETRIES_FIXED,
                     "troubleshooting.md": TROUBLESHOOTING_FIXED})
        print("\n== second pass")
        remaining = audit(INVENTORY_FIXED, docs)
        print("\n== redirects")
        redirects(INVENTORY_FIXED)
    return 1 if remaining else 0


if __name__ == "__main__":
    sys.exit(main())
