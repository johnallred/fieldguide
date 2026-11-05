---
title: Crawlability and the agent-ready front door
summary: Being fetchable and parseable at all, which is the precondition for every other machine-facing thing you build.
diataxis: explanation
audience: operator
concept: crawlability
tags: [ai, supporting]
---

# Crawlability and the agent-ready front door

`supporting` · difficulty 2 · 3h

> site navigation, and a crawlable, agent-ready front door

> Source: intel posting, verbatim

**Prerequisites:** [SEO for documentation](seo-for-docs.md)

## What it is

Making sure a machine can fetch your pages, follow your links, and find the
content in the response. The dull precondition underneath
[SEO](seo-for-docs.md), [GEO](geo.md), [llms.txt](llms-txt.md) and every
retrieval system: **none of them work on a page nobody can fetch.**

Intel's phrase "front door" is the useful part. It means there is an entry
point a machine arriving with no context can start from.

## Why the job asks for it

Intel names it in the role summary, alongside site navigation. It is listed as
something the role owns rather than as a qualification, which tells you it is
operational work: redirects, sitemaps, render modes, robots rules.

What makes this `supporting` rather than `core` is that it is mostly checks
rather than judgement. It earns a page because **it is the failure that makes
every other investment worthless**, and it is invisible from inside. Your
documentation site looks perfect in your browser, which is running JavaScript,
following your redirects, and already signed in.

On a Tuesday it is a discovery that invalidates a quarter. Somebody asks why
the assistant never cites the API reference. The reference is
client-rendered, so a fetch returns an empty `<div id="root">`. Every chunk, every
embedding and every llms.txt entry for those pages has been built from nothing.
**No error was raised anywhere** because an empty page is a valid page.

## The golden path

Build a crawlability audit over a site structure with the five common defects,
and see which ones are silent. Thirty-five minutes.

Committed as `drills/crawlability.py`, which runs the whole path in one go. It
writes the `crawl.py` below to a temporary directory and runs it as a
subprocess, so the code demonstrated is the code printed here; a test asserts
the two have not drifted apart.

**Step 1: a site with realistic problems**

```bash
mkdir -p crawl-drill/site/{docs,api} && cd crawl-drill

cat > site/docs/install.html <<'EOF'
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
EOF

cat > site/docs/configure.html <<'EOF'
<!doctype html>
<html lang="en"><head>
<title>Configure | Widget</title>
<meta name="description" content="Install the CLI with pip and confirm it runs.">
</head><body>
<h1>Configure the client</h1>
<p>Set <code>retries</code> and <code>batch_size</code> on the client.</p>
<p>See <a href="/docs/tuning/">tuning</a>.</p>
</body></html>
EOF

cat > site/api/reference.html <<'EOF'
<!doctype html>
<html lang="en"><head>
<title>API reference | Widget</title>
<meta name="description" content="Generated reference for every endpoint.">
</head><body>
<div id="root"></div>
<script src="/assets/app.js"></script>
</body></html>
EOF

cat > site/robots.txt <<'EOF'
User-agent: *
Disallow: /api/
Allow: /docs/
Sitemap: https://widget.example/sitemap.xml
EOF

cat > site/sitemap.xml <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://widget.example/docs/install/</loc><lastmod>2026-10-20</lastmod></url>
  <url><loc>https://widget.example/docs/legacy/</loc><lastmod>2024-01-01</lastmod></url>
</urlset>
EOF
find site -type f | sort
```

Five defects are in there, and only one of them, a dead link, is something a
reader would ever notice. They produce ten findings between them, for reasons
the audit output below makes clear.

**Step 2: the audit**

```bash
cat > crawl.py <<'PY'
"""Audit a built site for the things that stop a machine reading it.

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
PY
python3 crawl.py; echo "exit=$?"
```

```
CRAWL  api/reference.html: no-server-content: 4 words of text without running JavaScript
CRAWL  api/reference.html: robots-blocked: served at https://widget.example/api/reference/ but robots.txt disallows /api/
CRAWL  api/reference.html: no-canonical: no canonical link
CRAWL  docs/configure.html: no-server-content: 16 words of text without running JavaScript
CRAWL  docs/configure.html: no-canonical: no canonical link
CRAWL  docs/configure.html: dead-link: links to /docs/tuning/, not served
CRAWL  docs/configure.html, docs/install.html: duplicate-description: share one description: 'Install the CLI with pip and confirm it runs.'
CRAWL  sitemap.xml: sitemap-ghost: lists https://widget.example/docs/legacy/, not served
CRAWL  sitemap.xml: sitemap-missing: https://widget.example/api/reference/ is served but unlisted
CRAWL  sitemap.xml: sitemap-missing: https://widget.example/docs/configure/ is served but unlisted
FAIL: 3 pages, 10 problem(s)
exit=1
```

Ten findings from five defects, which is not a contradiction. One defect can
trip several checks: the client-rendered API reference is simultaneously
unreadable without JavaScript, blocked by `robots.txt` and missing a canonical,
so it accounts for three lines on its own. A findings list counts symptoms and
a repair list counts causes, and conflating the two is how a backlog ends up
three times longer than the work.

One line is a false positive, and it is worth more than the nine true ones.
`docs/configure.html` is static HTML with real prose; it is reported as having
too little text without JavaScript because it is sixteen words long and the
threshold is twenty. The check cannot distinguish a client-rendered shell from
a genuinely short page, because from the outside they look identical: both are
a fetch that returns almost no words.

That is not a bug to fix by raising the threshold. It is the limit of what a
word count can know, and the honest responses are to tune the threshold to the
corpus, exempt known-short pages by path, or treat the finding as a question
rather than a verdict. Publishing the audit without publishing its false
positive would have made the check look more decisive than it is, which is how
a check gets switched off the first time it annoys somebody.

**Step 3: see which failures a human could have noticed**

```bash
python3 - <<'PY'
TABLE = [
    ("no-server-content", "No", "The page renders perfectly in a browser"),
    ("robots-blocked",    "No", "Nothing on the page indicates it"),
    ("duplicate-description", "No", "Visible only by comparing two pages' source"),
    ("sitemap-ghost",     "No", "A sitemap entry for a page nobody visits"),
    ("sitemap-missing",   "No", "An unlisted page still works if linked"),
    ("dead-link",         "Yes", "A reader clicking it gets a 404"),
    ("no-canonical",      "No", "Invisible until duplicate URLs split your ranking"),
]
width = max(len(k) for k, _, _ in TABLE)
print(f"{'failure':<{width + 2}} {'noticed by a human?':<21} why")
print("-" * 86)
for kind, noticed, why in TABLE:
    print(f"{kind:<{width + 2}} {noticed:<21} {why}")
print()
print("Six of seven are silent. That ratio is the argument for the check.")
PY
```

**Step 4: fix them and watch the audit go quiet**

```bash
# 1. Server-render the reference, or prerender it at build time.
cat > site/api/reference.html <<'EOF'
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
EOF

# 2. Stop blocking the reference. Block the asset directory instead.
cat > site/robots.txt <<'EOF'
User-agent: *
Disallow: /assets/
Sitemap: https://widget.example/sitemap.xml
EOF

# 3 and 4. A real description, and a canonical, on configure.
cat > site/docs/configure.html <<'EOF'
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
EOF

# 5. The sitemap is generated from what is served, never hand-written.
python3 - <<'PY'
from pathlib import Path
ROOT, BASE = Path("site"), "https://widget.example"
urls = sorted(
    f"{BASE}/{p.relative_to(ROOT).with_suffix('').as_posix()}/"
    for p in ROOT.rglob("*.html")
)
body = "\n".join(
    f"  <url><loc>{u}</loc><lastmod>2026-10-26</lastmod></url>" for u in urls
)
(ROOT / "sitemap.xml").write_text(
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    f"{body}\n</urlset>\n"
)
print(f"generated sitemap with {len(urls)} url(s)")
PY

python3 crawl.py; echo "exit=$?"
```

```
generated sitemap with 3 url(s)
ok: 3 pages, 0 problem(s)
exit=0
```

Note how the dead link was repaired: the rewritten `configure.html` drops the
link to `/docs/tuning/` rather than creating the page. That is a legitimate fix
and a different decision from the one the finding implies, which is worth being
explicit about. An audit tells you a link is dead. It cannot tell you whether
the answer is to write the missing page or to stop promising it, and that
choice belongs to whoever owns the content.

Fixing `configure.html` also silenced its `no-server-content` finding, because
the repair happened to push the page over twenty words. The false positive went
away for the wrong reason, which is exactly how a flaky check earns misplaced
confidence.

**What you built.** An audit for the failures that leave a site looking correct,
and a generated sitemap that cannot disagree with what is served.

## Reference

### The failures, and which are silent

| Failure | Noticed by a human? | Consequence |
|---|---|---|
| Client-rendered content | **No** | Every chunk, embedding and llms.txt entry built from nothing |
| Blocked by `robots.txt` | **No** | The page is excluded from everything that respects it |
| Duplicate meta descriptions | **No** | Every snippet and link preview destroyed |
| Sitemap lists pages not served | **No** | Crawl budget spent on 404s |
| Served pages missing from the sitemap | **No** | Slower discovery of new pages |
| Missing canonical | **No** | Duplicate URLs split your own ranking |
| Dead internal link | Yes | A 404 |

**Six of seven are silent**, which is why this is a check rather than a review
item.

### The render-mode problem, which is the big one

| Render mode | A fetch without JavaScript sees |
|---|---|
| Static HTML | everything |
| Server-rendered | everything |
| Prerendered at build time | everything |
| Client-rendered | **an empty div** |
| Client-rendered with a prerender service | depends on the user agent, which is fragile |

A generated API reference is the page most likely to be client-rendered and the
page most valuable to a retrieval system, which is an unfortunate coincidence
worth checking for specifically.

The test is one command:

```bash
curl -s https://example.com/docs/page/ | python3 -c "
import re, sys
html = sys.stdin.read()
text = re.sub(r'<[^>]+>', ' ', re.sub(r'<(script|style)\b.*?</\1>', ' ', html, flags=re.S|re.I))
print(len(text.split()), 'words without JavaScript')"
```

### robots.txt, which is where people block themselves

| Pattern | Effect |
|---|---|
| `Disallow: /api/` | Blocks your API reference. Very common accident |
| `Disallow: /` on a staging host | Correct, and catastrophic if the config ships to production |
| Blocking `/assets/` | Usually fine; may block images from image search |
| `Allow:` with no `Disallow:` | Does nothing. A no-op people treat as permission |
| No robots.txt at all | Everything is allowed. Often the right answer |

`robots.txt` is a crawling directive, not an access control and not a
noindex. A disallowed URL can still appear in results if linked elsewhere, and
disallowing a page prevents a crawler from *reading* the `noindex` you put on
it, which is the classic way a page you wanted removed stays listed forever.

### Sitemaps, generated

| Rule | Why |
|---|---|
| Generate from what is served | A hand-maintained sitemap is wrong within a month |
| Include `lastmod`, accurately | A `lastmod` of today on every page is ignored as noise |
| Exclude redirects and non-canonical URLs | They waste crawl budget |
| Reference it from `robots.txt` | The only discovery mechanism that needs no submission |
| Split above 50,000 URLs | The per-file limit |

### The front door, in Intel's sense

A machine arriving with no context needs somewhere to start:

| Artifact | Serves |
|---|---|
| `/` with real links | A crawler following links |
| `/sitemap.xml` | A crawler that wants the full list |
| [`/llms.txt`](llms-txt.md) | A model choosing where to look |
| [`/llms-full.txt`](llms-txt.md) | A model wanting one fetch |
| Markdown sources beside the HTML | A model that would rather not parse your nav |
| [`robots.txt`](crawlability.md) permitting the docs | Everything above |

Serving the Markdown next to the rendered site is one line in a publish job and
removes the render-mode problem entirely for consumers that prefer it.

### Things worth checking that this audit does not

| Check | Why it needs a live site |
|---|---|
| Response status codes | A build cannot tell you about a 500 |
| Redirect chains | More than one hop loses signal |
| `Content-Type` correctness | Markdown served as `application/octet-stream` is unreadable |
| Time to first byte | Crawl rate is budget-limited |
| Pages behind auth | Return 200 with a login page, so they look fine |

The last one is the nastiest in enterprise documentation: an authenticated page
returns a login form with a 200 status, so a crawler indexes the login page and
a retrieval system embeds it.

## How to talk about it

**What a competent answer sounds like.** Lead with the silence. "The failures
here are almost all invisible from a browser. The one that cost us a quarter was
a client-rendered API reference: a fetch returned an empty div, so every chunk
and every embedding for those pages was built from nothing and nothing raised an
error, because an empty page is a valid page. So I audit the built site for text
present without JavaScript, pages blocked by their own robots.txt, duplicate
descriptions, and a sitemap that disagrees with what is served. The sitemap is
generated, never hand-written."

**The follow-up is usually "is this not an SEO job",** and the honest answer is
that the work overlaps and the stakes changed. Being unfetchable used to cost
you search traffic, which somebody else measured. It now also silently poisons
your retrieval corpus, your llms.txt and your assistant, and those are yours.
The check belongs with whoever owns the machine-facing artifacts, which in both
these postings is this role.

**The tradeoff to volunteer.** An audit over a built site is a second CI job on
output that already passed its own tests, and it will produce findings that are
deliberate: a page genuinely excluded, a description shared between two
near-identical generated pages. So it needs an allowlist, and an allowlist
decays into a list of things nobody reviews. The honest version is to keep the
checks few and loud rather than many and warning-level, which means accepting
that this audit will not be comprehensive.

**One sharper point.** The strongest observation is that **every machine-facing
investment in this guide is multiplied by zero if the page is not fetchable**,
and crawlability is the only one of them with no visible symptom. Chunking
badly degrades retrieval; being unfetchable eliminates it, quietly, for a
subset of pages that nobody enumerates. So this unglamorous audit should be the
*first* thing built, before llms.txt or embeddings or an assistant, and it
almost never is, because the other things are more interesting to work on. That
ordering argument is worth making to a lead who is being asked to fund a RAG
pipeline.

## How to prove it

**The artifact.** The audit in CI over the built site, plus a generated sitemap
and the one-line no-JavaScript text check.

**Three things to do, in order:**

1. **Run the one-line check against a real documentation site.** `curl` it and
   count words without JavaScript. On a client-rendered site the number is near
   zero, and that is a two-minute finding.
2. **Read a real `robots.txt`** and check whether it blocks anything you want
   retrieved. `Disallow: /api/` is common and usually an accident.
3. **Generate the sitemap from the build output** and diff it against the
   committed one. The difference is a list of ghosts and omissions nobody knew
   about.

**What makes it credible rather than decorative.** Mentioning sitemaps and robots.txt is table stakes.
A built-site audit whose first check is text-without-JavaScript, a count of how
many of its findings are invisible to a human, and the argument that this
should precede the interesting work demonstrates that you have been burned by
the silent version.

## Related

- [SEO for documentation](seo-for-docs.md), what crawlability is a precondition for
- [llms.txt and llms-full.txt](llms-txt.md), the front door for models
- [Generative engine optimization](geo.md), what extracts once you can be read
- [Preview deployments and publishing](preview-deployments.md), where this check runs
