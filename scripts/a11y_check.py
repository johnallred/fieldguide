#!/usr/bin/env python3
"""Check the built site for the accessibility defects a machine can find.

    python3 scripts/a11y_check.py site

The accessibility page says the check belongs on the built HTML, because that
is what a browser and a screen reader receive: Markdown cannot show whether
the theme declared a language or where a generated heading landed. This runs
over every page of the build, theme included, as a gate in CI.

Per page:
  lang         the <html> element declares a language
  title        a non-empty <title>
  one-h1       exactly one h1, so the page has one name
  heading-skip no heading level skipped on the way down (h2 to h4)
  img-alt      every <img> has an alt attribute (empty is fine: decorative)
  link-name    every link has a name: text, an aria-label, a title, or an
               image with alt text
  link-vague   no link whose whole text is "here", "click here", "read more"
               or "link", which says nothing out of context
  table-header every table has at least one <th>
  input-label  every visible form control has a label, an aria-label or a title

What it cannot check is most of what accessibility is: contrast in practice,
keyboard order, whether alt text describes the image, whether the prose makes
sense read aloud. Passing this is the floor, not a claim of conformance.
"""

from __future__ import annotations

import sys
from html.parser import HTMLParser
from pathlib import Path

VAGUE = {"here", "click here", "read more", "more", "link", "this link"}
SKIP_DIRS = {"assets", "search"}
LABELLED = ("aria-label", "aria-labelledby", "title")


class Page(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.lang = None
        self.title = ""
        self.in_title = False
        self.headings: list[int] = []
        self.findings: list[tuple[str, str]] = []
        self.link: dict | None = None
        self.tables: list[bool] = []
        self.label_for: set[str] = set()
        self.controls: list[dict] = []
        self.in_label = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "html":
            self.lang = a.get("lang")
        elif tag == "title":
            self.in_title = True
        elif len(tag) == 2 and tag[0] == "h" and tag[1] in "123456":
            self.headings.append(int(tag[1]))
        elif tag == "img":
            if "alt" not in a:
                self.findings.append(("img-alt", f"img {a.get('src', '?')} has no alt"))
            if self.link is not None and a.get("alt"):
                self.link["text"] += " " + a["alt"]
        elif tag == "a" and "href" in a:
            named = any(a.get(k) for k in LABELLED)
            self.link = {"href": a["href"], "text": "", "named": named}
        elif tag == "table":
            self.tables.append(False)
        elif tag == "th" and self.tables:
            self.tables[-1] = True
        elif tag == "label":
            self.in_label += 1
            if a.get("for"):
                self.label_for.add(a["for"])
        elif tag in ("input", "select", "textarea") and a.get("type") not in ("hidden", "submit", "button", "reset"):
            self.controls.append({"id": a.get("id"), "named": any(a.get(k) for k in LABELLED)
                                  or self.in_label > 0, "name": a.get("name") or a.get("id") or tag})

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        elif tag == "a" and self.link is not None:
            text = " ".join(self.link["text"].split())
            if not text and not self.link["named"]:
                self.findings.append(("link-name", f"link to {self.link['href']} has no name"))
            elif text.lower().strip(".:") in VAGUE:
                self.findings.append(("link-vague", f"link to {self.link['href']} says only {text!r}"))
            self.link = None
        elif tag == "table" and self.tables:
            if not self.tables.pop():
                self.findings.append(("table-header", "a table has no header cells"))
        elif tag == "label":
            self.in_label -= 1

    def handle_data(self, data):
        if self.in_title:
            self.title += data
        if self.link is not None:
            self.link["text"] += data

    def finish(self) -> list[tuple[str, str]]:
        found = list(self.findings)
        if not self.lang:
            found.append(("lang", "<html> declares no language"))
        if not self.title.strip():
            found.append(("title", "no <title>"))
        h1 = self.headings.count(1)
        if h1 != 1:
            found.append(("one-h1", f"{h1} h1 elements"))
        for before, after in zip(self.headings, self.headings[1:]):
            if after > before + 1:
                found.append(("heading-skip", f"h{before} is followed by h{after}"))
        for control in self.controls:
            if not control["named"] and control["id"] not in self.label_for:
                found.append(("input-label", f"form control {control['name']} has no label"))
        return found


def audit(root: Path) -> list[tuple[str, str, str]]:
    findings = []
    for path in sorted(root.rglob("*.html")):
        if set(path.relative_to(root).parts) & SKIP_DIRS:
            continue
        page = Page()
        page.feed(path.read_text(encoding="utf-8"))
        page.close()
        label = path.relative_to(root).as_posix()
        findings += [(label, kind, why) for kind, why in page.finish()]
    return findings


def main(argv: list[str] | None = None) -> int:
    root = Path((argv if argv is not None else sys.argv[1:] or ["site"])[0])
    pages = [p for p in root.rglob("*.html") if not set(p.relative_to(root).parts) & SKIP_DIRS]
    findings = audit(root)
    for label, kind, why in findings:
        print(f"A11Y  {label}: {kind}: {why}", file=sys.stderr)
    print(f"{'FAIL' if findings else 'ok'}: {len(pages)} pages, {len(findings)} problem(s)")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
