#!/usr/bin/env python3
"""Auditing a site for the failures a browser hides, and what the audit finds.

    python3 drills/crawlability.py

Reproduces the `crawlability` page's golden path end to end: a site with five
planted defects, the audit run against it, the step-4 repairs, and the audit
run again. It writes the page's own `crawl.py` to a temporary directory and
runs it as a subprocess, so the code being demonstrated is the code the page
prints, not a paraphrase of it. A test asserts both are still identical.

Committing it found three things the page did not say.

The first: the page ran the audit twice and quoted no output either time. A
reader could follow every step and have nothing to compare their result
against, which is the whole purpose of a golden path.

The second: five planted defects produce ten findings. One defect can trip
several checks, and the client-rendered API reference trips three at once. The
page's "five defects" and the audit's "10 problem(s)" are both correct and
look like a contradiction, so the page now says why.

The third is a false positive, and it is the useful one. `docs/configure.html`
is static HTML with real prose, and the audit reports it as having too little
text without JavaScript, because it is sixteen words long and the threshold is
twenty. The check cannot tell a client-rendered shell from a genuinely short
page. That is a real limitation of the word-count heuristic, it was invisible
while no output was published, and it is now stated on the page beside the
finding.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

#: The page's step-1 heredocs: a site with five defects, four of them silent.
SITE_BEFORE: tuple[tuple[str, str], ...] = (
    ('site/docs/install.html', """\
<!doctype html>
<html lang="en"><head>
<title>Install | Widget</title>
<meta name="description" content="Install the CLI with pip and confirm it runs.">
<link rel="canonical" href="https://widget.example/docs/install/">
</head><body>
<h1>Install the CLI</h1>
<p>Run <code>pip install widget</code>. Requires Python 3.10 or newer.</p>
<p>Next: <a href="/docs/configure/">configure the client</a>, or see the
<a href="/api/reference/">API reference</a>.</p>
</body></html>
"""),
    ('site/docs/configure.html', """\
<!doctype html>
<html lang="en"><head>
<title>Configure | Widget</title>
<meta name="description" content="Install the CLI with pip and confirm it runs.">
</head><body>
<h1>Configure the client</h1>
<p>Set <code>retries</code> and <code>batch_size</code> on the client.</p>
<p>See <a href="/docs/tuning/">tuning</a>.</p>
</body></html>
"""),
    ('site/api/reference.html', """\
<!doctype html>
<html lang="en"><head>
<title>API reference | Widget</title>
<meta name="description" content="Generated reference for every endpoint.">
</head><body>
<div id="root"></div>
<script src="/assets/app.js"></script>
</body></html>
"""),
    ('site/robots.txt', """\
User-agent: *
Disallow: /api/
Allow: /docs/
Sitemap: https://widget.example/sitemap.xml
"""),
    ('site/sitemap.xml', """\
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://widget.example/docs/install/</loc><lastmod>2026-10-20</lastmod></url>
  <url><loc>https://widget.example/docs/legacy/</loc><lastmod>2024-01-01</lastmod></url>
</urlset>
"""),
)

#: The page's step-4 heredocs: the three files its repairs rewrite.
SITE_AFTER: tuple[tuple[str, str], ...] = (
    ('site/api/reference.html', """\
<!doctype html>
<html lang="en"><head>
<title>API reference | Widget</title>
<meta name="description" content="Every endpoint, parameter and response code for the widget API.">
<link rel="canonical" href="https://widget.example/api/reference/">
</head><body>
<h1>API reference</h1>
<h2>POST /infer</h2>
<p>Accepts <code>input</code> and optional <code>batch_size</code>. Returns 200
with a result, 400 on invalid input, 429 when rate limited.</p>
<div id="root"></div>
<script src="/assets/app.js"></script>
</body></html>
"""),
    ('site/robots.txt', """\
User-agent: *
Disallow: /assets/
Sitemap: https://widget.example/sitemap.xml
"""),
    ('site/docs/configure.html', """\
<!doctype html>
<html lang="en"><head>
<title>Configure | Widget</title>
<meta name="description" content="Set retries and batch_size on the widget client, with their defaults.">
<link rel="canonical" href="https://widget.example/docs/configure/">
</head><body>
<h1>Configure the client</h1>
<p>Set <code>retries</code> and <code>batch_size</code> on the client. The
defaults are 5 and 32 as of widget 2.6.</p>
</body></html>
"""),
)

#: The page's `crawl.py`, verbatim. A test asserts this still matches.
AUDIT_SOURCE = r'''"""Audit a built site for the things that stop a machine reading it.

Each check corresponds to a failure that leaves the site looking correct in a
browser. That is the property they share and the reason they need a check at
all: a human cannot find these by looking.
"""
import re
import sys
from pathlib import Path

ROOT = Path("site")
BASE = "https://widget.example"

TITLE = re.compile(r"<title>(.*?)</title>", re.S | re.I)
DESCRIPTION = re.compile(r'<meta\s+name="description"\s+content="(.*?)"', re.S | re.I)
CANONICAL = re.compile(r'<link\s+rel="canonical"\s+href="(.*?)"', re.I)
LINK = re.compile(r'href="(/[^"#?]*)"')
#: Text outside script, style and tags. What a fetch without JavaScript sees.
SCRIPT = re.compile(r"<(script|style)\b.*?</\1>", re.S | re.I)
TAG = re.compile(r"<[^>]+>")

MIN_TEXT_WORDS = 20


def url_for(path):
    """Map a built file to the URL it is served at."""
    return f"{BASE}/{path.relative_to(ROOT).with_suffix('').as_posix()}/"


def visible_text(html):
    return TAG.sub(" ", SCRIPT.sub(" ", html))


def robots_rules(path):
    disallow = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.lower().startswith("disallow:"):
            value = line.split(":", 1)[1].strip()
            if value:
                disallow.append(value)
    return disallow


def sitemap_urls(path):
    return set(re.findall(r"<loc>(.*?)</loc>", path.read_text(encoding="utf-8")))


def main():
    pages = sorted(ROOT.rglob("*.html"))
    findings = []

    disallow = robots_rules(ROOT / "robots.txt")
    listed = sitemap_urls(ROOT / "sitemap.xml")
    served = {url_for(p) for p in pages}

    descriptions = {}
    for path in pages:
        html = path.read_text(encoding="utf-8")
        url = url_for(path)
        label = path.relative_to(ROOT).as_posix()

        # 1. Content present without JavaScript. The silent one.
        words = len(visible_text(html).split())
        if words < MIN_TEXT_WORDS:
            findings.append((label, "no-server-content",
                             f"{words} words of text without running JavaScript"))

        # 2. Blocked by robots while being a real documentation page.
        for rule in disallow:
            if url.replace(BASE, "").startswith(rule):
                findings.append((label, "robots-blocked",
                                 f"served at {url} but robots.txt disallows {rule}"))

        # 3. Canonical present.
        if not CANONICAL.search(html):
            findings.append((label, "no-canonical", "no canonical link"))

        # 4. Description present and distinct.
        match = DESCRIPTION.search(html)
        if not match:
            findings.append((label, "no-description", "no meta description"))
        else:
            descriptions.setdefault(match.group(1), []).append(label)

        # 5. Internal links resolve to something served.
        for href in set(LINK.findall(html)):
            target = href.rstrip("/")
            candidates = {
                ROOT / f"{target.lstrip('/')}.html",
                ROOT / target.lstrip("/") / "index.html",
            }
            if not any(c.exists() for c in candidates) and not href.startswith("/assets"):
                findings.append((label, "dead-link", f"links to {href}, not served"))

    for text, where in descriptions.items():
        if len(where) > 1:
            findings.append((", ".join(where), "duplicate-description",
                             f"share one description: {text[:46]!r}"))

    # 6. Sitemap agrees with what is served.
    for url in sorted(listed - served):
        findings.append(("sitemap.xml", "sitemap-ghost", f"lists {url}, not served"))
    for url in sorted(served - listed):
        findings.append(("sitemap.xml", "sitemap-missing", f"{url} is served but unlisted"))

    for label, kind, why in findings:
        print(f"CRAWL  {label}: {kind}: {why}", file=sys.stderr)
    print(f"{'FAIL' if findings else 'ok'}: {len(pages)} pages, {len(findings)} problem(s)")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
'''


def write(root: Path, files: tuple[tuple[str, str], ...]) -> None:
    for name, body in files:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")


def audit(root: Path) -> int:
    """Run the page's audit the way the page runs it, and show both streams.

    `crawl.py` prints findings to stderr and its verdict to stdout, which is
    the right split for a CI gate and an awkward one for a transcript. They
    are interleaved here in the order the reader sees them in a terminal.
    """
    result = subprocess.run(
        [sys.executable, "crawl.py"], cwd=root, capture_output=True, text=True, timeout=60
    )
    sys.stdout.write(result.stderr)
    sys.stdout.write(result.stdout)
    print(f"exit={result.returncode}")
    return result.returncode


def regenerate_sitemap(root: Path) -> None:
    """Step 5 of the repairs: generate the sitemap from what is served."""
    site, base = root / "site", "https://widget.example"
    urls = sorted(
        f"{base}/{p.relative_to(site).with_suffix('').as_posix()}/"
        for p in site.rglob("*.html")
    )
    body = "\n".join(
        f"  <url><loc>{u}</loc><lastmod>2026-10-26</lastmod></url>" for u in urls
    )
    (site / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{body}\n</urlset>\n",
        encoding="utf-8",
    )
    print(f"generated sitemap with {len(urls)} url(s)")


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "crawl.py").write_text(AUDIT_SOURCE, encoding="utf-8")

        write(root, SITE_BEFORE)
        print("step 2: the audit, against five planted defects\n")
        dirty = audit(root)

        print("\nstep 4: fix them and watch the audit go quiet\n")
        write(root, SITE_AFTER)
        regenerate_sitemap(root)
        print()
        clean = audit(root)

    ok = (dirty, clean) == (1, 0)
    if not ok:
        print("\nunexpected: the audit did not go from failing to clean", file=sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
