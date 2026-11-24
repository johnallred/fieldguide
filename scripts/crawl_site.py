#!/usr/bin/env python3
"""Audit this guide's own published site for what a crawler or an agent meets.

    python3 scripts/crawl_site.py site                   # the built site, offline
    python3 scripts/crawl_site.py --live URL             # the deployed site

The crawlability page's golden path audits an invented site with planted
defects. This is the same audit pointed at a real one: the MkDocs build that
GitHub Pages serves. The offline mode runs as a gate on every change, on the
files about to be published. The live mode runs after each deploy, against
what a crawler actually receives, because a build that is correct on disk can
still be served wrong.

Offline checks, per page:
  1. text present without running JavaScript
  2. a canonical link, pointing at the page's own URL
  3. a meta description, not shared with any other page
  4. every internal link resolves to a file in the build
and for the site:
  5. the sitemap lists exactly the pages served
  6. llms.txt exists and every URL it lists is served

Live checks: every sitemap URL, and llms.txt, answer 200, and each page's
canonical names the URL it was fetched from.

What it cannot check: robots.txt. A GitHub Pages project site is served under
a path (/fieldguide/), and crawlers read robots.txt only at the root of the
host, which belongs to the account's user site. A project site cannot block or
advertise anything through robots.txt; its sitemap has to be submitted to
search engines directly. That is reported once, as a note, not as a failure.
"""

from __future__ import annotations

import argparse
import posixpath
import re
import sys
import urllib.request
from pathlib import Path
from urllib.parse import urljoin, urlparse

TITLE = re.compile(r"<title>(.*?)</title>", re.S | re.I)
DESCRIPTION = re.compile(r'<meta\s+name="description"\s+content="(.*?)"', re.S | re.I)
CANONICAL = re.compile(r'<link\s+rel="canonical"\s+href="(.*?)"', re.I)
HREF = re.compile(r'<(?:a|link)\b[^>]*?\bhref="([^"]+)"', re.I)
#: Code samples. Their text is quoted HTML, so hrefs inside are not links.
PRE = re.compile(r"<pre\b.*?</pre>", re.S | re.I)
SCRIPT = re.compile(r"<(script|style)\b.*?</\1>", re.S | re.I)
TAG = re.compile(r"<[^>]+>")
LOC = re.compile(r"<loc>(.*?)</loc>")
LLMS_LINK = re.compile(r"\]\((https?://[^)\s]+)\)")

MIN_TEXT_WORDS = 20
#: Build directories that hold assets and the search index, not pages.
SKIP_DIRS = {"assets", "search"}


def site_url(root: Path) -> str:
    """The base URL, read from the build's own sitemap."""
    locs = LOC.findall((root / "sitemap.xml").read_text(encoding="utf-8"))
    home = min(locs, key=len)
    return home if home.endswith("/") else home + "/"


def pages(root: Path) -> list[Path]:
    """Every served page. MkDocs writes each one as <dir>/index.html."""
    return sorted(
        p for p in root.rglob("index.html")
        if not set(p.relative_to(root).parts) & SKIP_DIRS
    )


def url_for(root: Path, base: str, path: Path) -> str:
    parent = path.parent.relative_to(root).as_posix()
    return base if parent == "." else f"{base}{parent}/"


def visible_words(html: str) -> int:
    return len(TAG.sub(" ", SCRIPT.sub(" ", html)).split())


def resolves(root: Path, page: Path, href: str) -> bool:
    """Whether a relative link from a built page lands on a built file."""
    target = href.split("#", 1)[0].split("?", 1)[0]
    if not target:
        return True
    joined = posixpath.normpath(posixpath.join(page.parent.relative_to(root).as_posix(), target))
    candidate = root / joined
    return candidate.is_file() or (candidate / "index.html").is_file()


def offline(root: Path) -> int:
    base = site_url(root)
    host_path = urlparse(base).path
    findings: list[tuple[str, str, str]] = []
    served: set[str] = set()
    descriptions: dict[str, list[str]] = {}

    for path in pages(root):
        html = path.read_text(encoding="utf-8")
        url = url_for(root, base, path)
        label = path.relative_to(root).as_posix()
        served.add(url)

        words = visible_words(html)
        if words < MIN_TEXT_WORDS:
            findings.append((label, "no-server-content", f"{words} words without JavaScript"))

        canonical = CANONICAL.search(html)
        if not canonical:
            findings.append((label, "no-canonical", "no canonical link"))
        elif canonical.group(1) != url:
            findings.append((label, "wrong-canonical", f"canonical is {canonical.group(1)}"))

        description = DESCRIPTION.search(html)
        if not description or not description.group(1).strip():
            findings.append((label, "no-description", "no meta description"))
        else:
            descriptions.setdefault(description.group(1), []).append(label)

        for href in set(HREF.findall(PRE.sub(" ", html))):
            if href.startswith(("http:", "https:", "mailto:", "#", "data:", "//")):
                continue
            if href.startswith("/"):
                if not href.startswith(host_path):
                    findings.append((label, "root-link", f"{href} leaves the project site"))
                    continue
                href = posixpath.relpath(href, posixpath.dirname(host_path + label))
            if not resolves(root, path, href):
                findings.append((label, "dead-link", f"links to {href}, not in the build"))

    for text, where in descriptions.items():
        if len(where) > 1:
            findings.append((", ".join(where[:3]), "duplicate-description",
                             f"{len(where)} pages share {text[:40]!r}"))

    listed = set(LOC.findall((root / "sitemap.xml").read_text(encoding="utf-8")))
    for url in sorted(listed - served):
        findings.append(("sitemap.xml", "sitemap-ghost", f"lists {url}, not served"))
    for url in sorted(served - listed):
        findings.append(("sitemap.xml", "sitemap-missing", f"{url} is served but unlisted"))

    llms = root / "llms.txt"
    if not llms.is_file():
        findings.append(("llms.txt", "no-llms-txt", "no llms.txt for agents to start from"))
    else:
        for link in sorted(set(LLMS_LINK.findall(llms.read_text(encoding="utf-8")))):
            if link.startswith(base) and link not in served and not (
                    root / link[len(base):]).is_file():
                findings.append(("llms.txt", "llms-dead-link", f"lists {link}, not served"))

    for label, kind, why in findings:
        print(f"CRAWL  {label}: {kind}: {why}", file=sys.stderr)
    print(f"note: robots.txt is not checked; a project site under {host_path} cannot "
          "serve one at the host root, so its sitemap is submitted directly")
    print(f"{'FAIL' if findings else 'ok'}: {len(served)} pages, {len(findings)} problem(s)")
    return 1 if findings else 0


def fetch(url: str) -> tuple[int, str]:
    request = urllib.request.Request(url, headers={"User-Agent": "fieldguide-crawl-check"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status, response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as error:
        return error.code, ""


def live(base: str) -> int:
    base = base if base.endswith("/") else base + "/"
    findings = []
    status, sitemap = fetch(urljoin(base, "sitemap.xml"))
    if status != 200:
        print(f"FAIL: sitemap.xml answered {status}")
        return 1
    urls = LOC.findall(sitemap)
    for url in urls:
        status, html = fetch(url)
        if status != 200:
            findings.append((url, f"answered {status}"))
            continue
        canonical = CANONICAL.search(html)
        if not canonical or canonical.group(1) != url:
            findings.append((url, f"canonical is {canonical.group(1) if canonical else 'missing'}"))
    status, _ = fetch(urljoin(base, "llms.txt"))
    if status != 200:
        findings.append((urljoin(base, "llms.txt"), f"answered {status}"))
    for url, why in findings:
        print(f"LIVE  {url}: {why}", file=sys.stderr)
    print(f"{'FAIL' if findings else 'ok'}: {len(urls)} sitemap URLs and llms.txt fetched, "
          f"{len(findings)} problem(s)")
    return 1 if findings else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("site", nargs="?", default="site", help="the built site directory")
    parser.add_argument("--live", metavar="URL", help="audit the deployed site instead")
    args = parser.parse_args(argv)
    return live(args.live) if args.live else offline(Path(args.site))


if __name__ == "__main__":
    sys.exit(main())
