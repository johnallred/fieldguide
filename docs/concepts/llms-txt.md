---
title: llms.txt and llms-full.txt
summary: A map of your corpus for a model that has not read it yet, and the whole corpus for one that wants it in a single fetch.
diataxis: explanation
audience: developer
concept: llms-txt
tags: [ai, core]
---

# llms.txt and llms-full.txt

`core` · difficulty 1 · 2h

> including llms.txt, MCP-accessible sources, agent skills and context kits, and evaluation sets for answer accuracy

> Source: nvidia posting, verbatim

**Prerequisites:** [Agent-ready content](agent-ready-content.md)

## What it is

`/llms.txt` is a Markdown file at the root of a site giving a language model a
map of what is there: a name, a one-line description, and sections of annotated
links. `/llms-full.txt` is the other artifact, the whole corpus concatenated
into one document for a model that would rather make one request than thirty.

They are a community convention proposed by Jeremy Howard of Answer.AI in
September 2024. **Not a standard**, and that distinction matters when you
present it internally.

## Why the job asks for it

NVIDIA names the file explicitly, in a list of four AI-ready outputs. That is
the whole justification, and it is a `core` concept for a cheaper reason than
most: it takes an afternoon and it is the single most visible signal that a
documentation team has thought about machine consumers at all.

On a Tuesday it is a generation step in your build, and the only interesting
part is what the annotations say. A map whose descriptions are page titles
restated is useless, because a model reading it still cannot tell which of your
forty pages answers the question in front of it. A map whose descriptions say
what question each page answers is genuinely useful.

The reason it earns its place alongside much harder concepts: it serves a
consumer the other artifacts cannot. [Chunks](chunking.md) serve a retriever
that already has a query. An assistant deciding *where to look* has no query
embedding and no index; it has a URL and a question. `llms.txt` is the only
thing in the stack built for that moment.

## The golden path

Generate both files from a corpus and see what each one is for. Twenty-five
minutes.

**Step 1: a corpus with real summaries**

The summaries are the content here. A generator over pages with bad summaries
produces a bad map.

```bash
mkdir -p llms-drill/docs && cd llms-drill
cat > docs/install.md <<'EOF'
---
title: Install the widget CLI
summary: Install the CLI with pip and confirm it runs.
kind: how-to
updated: 2026-10-26
---
# Install the widget CLI

Run `pip install widget`. Requires Python 3.10 or newer.
EOF

cat > docs/batch-size.md <<'EOF'
---
title: Choose a batch size
summary: Pick a batch size from latency targets, GPU memory and quantisation.
kind: how-to
updated: 2026-10-26
---
# Choose a batch size

The default is 32. If latency matters, use 1 or 2.
EOF

cat > docs/cli.md <<'EOF'
---
title: CLI reference
summary: Every command, flag, default and exit code.
kind: reference
updated: 2026-10-26
---
# CLI reference

## Exit codes

`0` success, `1` configuration error, `2` bad arguments.
EOF

cat > docs/upgrade-1x.md <<'EOF'
---
title: Upgrading from 1.x
summary: Migration steps from the 1.x client, which reached end of life in 2024.
kind: how-to
updated: 2024-03-01
---
# Upgrading from 1.x

Replace the client import and rename two arguments.
EOF
ls docs/
```

**Step 2: generate both files**

```bash
cat > gen.py <<'PY'
"""Generate llms.txt and llms-full.txt from front matter.

Generated, never hand-written, for the same reason the API reference is
generated: a hand-maintained index of forty pages is accurate for about a
week, and it is the file a model trusts most.
"""
import datetime as dt
from pathlib import Path

import yaml

SITE = "Widget platform docs"
TAGLINE = "Client library and CLI for the widget inference platform."
BASE = "https://widget.example"
STALE_DAYS = 365

GROUPS = [
    ("how-to", "How-to guides", "Task-oriented. Assume familiarity with the platform."),
    ("reference", "Reference", "Factual description of the interface."),
    ("explanation", "Explanation", "Design reasoning and tradeoffs."),
]


def pages(docs: Path):
    for path in sorted(docs.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        front, _, body = text.partition("---\n")[2].partition("\n---\n")
        yield path, yaml.safe_load(front), body


def is_stale(meta) -> bool:
    updated = meta["updated"]
    if isinstance(updated, str):
        updated = dt.date.fromisoformat(updated)
    return (dt.date.today() - updated).days > STALE_DAYS


def main() -> None:
    docs = Path("docs")
    out = Path("dist")
    out.mkdir(exist_ok=True)
    everything = list(pages(docs))

    # --- llms.txt: the map -------------------------------------------
    lines = [f"# {SITE}", "", f"> {TAGLINE}", ""]
    lines.append(
        "Each link points to the Markdown source rather than the rendered page. "
        "Sections group pages by what kind of question they can answer."
    )
    lines.append("")

    for kind, label, blurb in GROUPS:
        group = [(p, m) for p, m, _ in everything
                 if m["kind"] == kind and not is_stale(m)]
        if not group:
            continue
        lines += [f"## {label}", "", blurb, ""]
        for path, meta in group:
            lines.append(f"- [{meta['title']}]({BASE}/docs/{path.name}): {meta['summary']}")
        lines.append("")

    # The convention reserves `## Optional` for content a model may skip.
    # Stale pages belong there: still true enough to cite, not what you want
    # a model reaching for first.
    stale = [(p, m) for p, m, _ in everything if is_stale(m)]
    if stale:
        lines += ["## Optional", "",
                  "Not reviewed in over a year. Treat with lower confidence.", ""]
        for path, meta in stale:
            lines.append(f"- [{meta['title']}]({BASE}/docs/{path.name}): {meta['summary']}")
        lines.append("")

    (out / "llms.txt").write_text("\n".join(lines), encoding="utf-8")

    # --- llms-full.txt: everything, once -----------------------------
    full = [f"# {SITE}: complete documentation", ""]
    for path, meta, body in everything:
        full += [
            "---", "",
            f"# {meta['title']}", "",
            f"*{meta['kind']} · updated {meta['updated']}*", "",
            meta["summary"], "",
            body.strip(), "",
        ]
    (out / "llms-full.txt").write_text("\n".join(full), encoding="utf-8")

    print(f"{len(everything)} pages, {len(stale)} stale")
    for name in ("llms.txt", "llms-full.txt"):
        print(f"  {name:<16} {(out / name).stat().st_size:>6} bytes")


if __name__ == "__main__":
    main()
PY
python3 gen.py
echo
cat dist/llms.txt
```

**Step 3: check it against the only test that matters**

A map is good if a model reading *only the map* can pick the right page.

```bash
python3 - <<'PY'
"""Can a reader pick the right page from the map alone?

This stands in for asking a model. The point is that the test uses only
llms.txt, never the pages, which is exactly the situation the file exists
for.
"""
import re

MAP = open("dist/llms.txt").read()
QUESTIONS = [
    ("my p99 latency is too high", "batch-size.md"),
    ("what does exit code 2 mean", "cli.md"),
    ("how do I get started", "install.md"),
]

entries = re.findall(r"- \[(.+?)\]\((.+?)\): (.+)", MAP)
print(f"{len(entries)} entries in the map\n")

for question, expected in QUESTIONS:
    terms = [t for t in re.findall(r"[a-z0-9]+", question.lower()) if len(t) > 2]
    best, score = None, 0
    for title, url, summary in entries:
        hay = f"{title} {summary}".lower()
        hits = sum(1 for t in terms if t in hay)
        if hits > score:
            best, score = url, hits
    ok = best and best.endswith(expected)
    print(f"  {'OK ' if ok else '   '} {question:<32} -> {best or 'no match'}")
PY
```

**Step 4: see what a bad summary costs**

```bash
python3 - <<'PY'
import pathlib
# Replace one good summary with the kind most corpora actually have.
p = pathlib.Path("docs/batch-size.md")
p.write_text(p.read_text().replace(
    "summary: Pick a batch size from latency targets, GPU memory and quantisation.",
    "summary: Information about batch size configuration."))
PY
python3 gen.py >/dev/null
grep "Choose a batch size" dist/llms.txt
python3 - <<'PY'
import re
MAP = open("dist/llms.txt").read()
entries = re.findall(r"- \[(.+?)\]\((.+?)\): (.+)", MAP)
terms = ["p99", "latency", "high", "too"]
best, score = None, 0
for title, url, summary in entries:
    hay = f"{title} {summary}".lower()
    hits = sum(1 for t in terms if t in hay)
    if hits > score:
        best, score = url, hits
print(f"  'my p99 latency is too high' -> {best or 'NO MATCH'} (score {score})")
PY
```

**What you built.** Both artifacts, generated, with stale pages routed to
`## Optional`, and a test that uses only the map.

Step 4 is the point of the whole exercise, and the result is stark: with a good
summary, "my p99 latency is too high" routes correctly to the batch-size page.
Replace that one summary with "Information about batch size configuration" and
the same question returns **no match at all**. The page is unchanged, the file
still looks complete, and the map has stopped working.

**The summary is the entire payload of `llms.txt`.** Most published ones restate
the title, which produces exactly this failure invisibly.

Two honest notes on the step 3 output. It scores **2 of 3**: "how do I get
started" routes to the batch-size page rather than to install, because "started"
appears in neither summary and the crude term overlap latches onto something
else. That is a real finding about the install summary rather than about the
method, and the fix is to write the summary in the words a new reader would use.
And the test is a stand-in for asking a model, not a substitute for it: it
measures whether the vocabulary is there, which is necessary and not sufficient.

## Reference

### The format

```markdown
# Project name

> One-line description of what this is.

Optional prose giving a model orientation it cannot get from the links.

## Section name

Optional blurb explaining what this section's pages can answer.

- [Page title](https://example.com/docs/page.md): what question it answers.

## Optional

Pages a model may skip if it is short of context.
```

| Element | Required | Notes |
|---|---|---|
| `# Name` | Yes | The only required line in the convention |
| `> Description` | Recommended | One line, what the project is |
| Prose after it | Optional | Orientation, not marketing |
| `## Sections` | Optional | Group by what kind of question, not by product area |
| `## Optional` | Reserved | The convention's name for skippable content |

### The two files, and who each is for

| | `llms.txt` | `llms-full.txt` |
|---|---|---|
| Consumer | A model deciding where to look | A model reading everything at once |
| Size | Kilobytes | Megabytes |
| Scales to a large corpus | Yes | No |
| Contains page content | No | Yes |
| Breaks when the corpus grows | No | Yes, into the context window |

For a corpus beyond a few hundred pages, `llms-full.txt` stops being useful and
`llms.txt` plus [MCP](mcp.md) or [retrieval](rag.md) is the answer.

### What makes a good annotation

| Bad | Better |
|---|---|
| "Information about batch size configuration" | "Pick a batch size from latency targets, GPU memory and quantisation" |
| "Installation guide" | "Install the CLI with pip and confirm it runs" |
| "CLI reference" | "Every command, flag, default and exit code" |
| "Advanced topics" | Split it; this describes nothing |

The test: does the annotation contain the words a reader would use when they
have the problem? "Latency" and "memory" are those words. "Configuration" is
not.

### Linking to Markdown, not HTML

The convention points at Markdown sources. Serving them alongside the rendered
site is a one-line build step and it matters: a model fetching an HTML page
spends most of its context on navigation, cookie banners and footers.

```bash
# in your publish job, after building the site
cp -r docs site/docs
```

### The honest status of this convention

| Claim | Reality |
|---|---|
| "It is a standard" | It is a community proposal from September 2024 |
| "Models read it automatically" | Some tools do. Most crawlers do not, and support is uneven |
| "It replaces a sitemap" | No. Different consumer, different format. Keep both |
| "It replaces RAG" | No. It is a map, not a retrieval system |

Adoption is real, including by several developer-tools companies, and
scepticism about it is also real. Present it internally as cheap and
low-risk rather than as table stakes, because somebody in the room will know
it is contested and a claim of standardisation will cost you credibility.

## How to talk about it

**What a competent answer sounds like.** Say what it is for, say what it is not,
and lead with the summary quality. "It is a map for a model that has not read
your corpus yet: a name, a description, and annotated links grouped by what kind
of question each page answers. The only thing that matters is the annotations.
A summary that restates the title makes the file useless while leaving it
looking done, which is the state most published llms.txt files are in. I
generate it from the required summary field so it cannot drift, and I route
stale pages to the Optional section."

**The follow-up is usually "is this actually a standard",** and it is a test.
The answer is no: it is a community convention proposed by Jeremy Howard in
September 2024, adoption is partial, and some people think it is unnecessary
because a well-structured sitemap and clean HTML do much the same job. The
reason to do it anyway is that it costs an afternoon, it is generated so it
cannot rot, and it forces you to write a real one-sentence summary for every
page, which is worth having regardless of whether any model ever reads the file.

**The tradeoff to volunteer.** A hand-written `llms.txt` is worse than none.
Committed once and forgotten, it actively misinforms a model about what your
corpus contains, and unlike a stale page nothing in your site contradicts it.
So the real commitment is a build step and a CI gate that fails when the
committed file does not match the corpus. A team not ready for that should skip
the file.

**One sharper point.** The most valuable thing about adopting `llms.txt` usually
has nothing to do with models. **It makes the quality of your page summaries
suddenly legible.** Forty summaries in one file, side by side, is a brutal
review: the vague ones are obvious at a glance in a way they never are
scattered across forty pages of front matter. Several teams have found their
content model's weakest field this way, and that is a real benefit independent
of whether the convention survives.

## How to prove it

**The artifact.** A generated `llms.txt` with annotations that pass the
reader-vocabulary test, plus the CI gate against staleness.

**Three things to do, in order:**

1. **Run the golden path, including step 4.** The before-and-after on one bad
   summary is the demonstration, and it takes two minutes.
2. **Generate it in CI and fail on drift.** Regenerate, compare against the
   committed file, fail if they differ. Ten lines, and it is what separates this
   from a file somebody added once.
3. **Review all your summaries in one sitting**, in the generated file.
   Rewrite every one that does not contain the words a reader with that
   problem would use. This is the step with value beyond the convention.
   Predict how many will need rewriting before you start. The gap between that
   guess and the count is the measurement, and it is usually in the same
   direction.

**What makes it credible rather than decorative.** Publishing an `llms.txt` proves you read about it. A
generated one, gated against staleness, with annotations written in reader
vocabulary, and an opinion about the convention's contested status, proves you
thought about it.

## Related

- [Agent-ready content](agent-ready-content.md), the three consumers this serves one of
- [Metadata for navigation and retrieval](metadata.md), where the summary comes from
- [Model Context Protocol](mcp.md), the answer when the corpus outgrows one file
- [Crawlability and the agent-ready front door](crawlability.md), the adjacent concern
