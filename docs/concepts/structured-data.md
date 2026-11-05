---
title: Structured data and JSON-LD
summary: Telling a machine what a page is and what kind of question it answers, in a format crawlers already parse.
diataxis: explanation
audience: developer
concept: structured-data
tags: [ai, supporting]
---

# Structured data and JSON-LD

`supporting` · difficulty 2 · 3h

!!! note "Not a quotation (derived)"
    Required by "a crawlable, agent-ready front door": the machine-readable half of SEO and GEO.

**Prerequisites:** [Metadata for navigation and retrieval](metadata.md)

## What it is

A block of JSON in the page's `<head>` describing what the page is, using a
vocabulary crawlers already understand. For documentation that means
`TechArticle`, with its title, description, modification date, and the facts a
machine cannot infer from prose.

It is the only place where your [content model](content-model.md) becomes
visible to something that fetches your HTML and does not run your search index.

## Why the job asks for it

Neither posting says "JSON-LD", which is why this is `derived`. Intel asks for
"a crawlable, agent-ready front door" and for content optimized "for search
(SEO and GEO) and for AI assistants and coding agents". Structured data is the
mechanism that makes a page's type machine-readable to a consumer that is not
your retriever.

What makes it `supporting` rather than `core` is that most of the benefit comes
from one small block generated from fields you already require. The work is an
afternoon, and then it is a build step.

On a Tuesday the reason it matters is narrower than SEO people claim. Your
[chunks](chunking.md) carry the page type because you put it there. Your
[MCP server](mcp.md) exposes it because you wrote the schema. **A crawler that
fetches the rendered page sees none of that**, because `diataxis: how-to` lives
in front matter that never reaches the HTML. So an external assistant reading
your site cannot tell a reference page from an explanation page, and that is the
single most useful distinction you have.

## The golden path

Generate JSON-LD from the content model, validate it, and show what a consumer
learns from it that the HTML alone does not say. Thirty minutes.

**Step 1: pages with a content model, and the HTML they would produce**

```bash
mkdir -p struct-drill/docs && cd struct-drill
cat > docs/rotate-key.md <<'EOF'
---
title: Rotate a signing key
summary: Replace a signing key with a one-hour overlap and no downtime.
diataxis: how-to
audience: operator
updated: 2026-10-20
tags: [keys, security]
---
# Rotate a signing key

Run `widget keys rotate`. The old key stays valid for one hour.
EOF

cat > docs/why-overlap.md <<'EOF'
---
title: Why keys overlap for an hour
summary: The reasoning behind a one-hour overlap window rather than instant cutover.
diataxis: explanation
audience: operator
updated: 2026-10-20
tags: [keys, security]
---
# Why keys overlap for an hour

An instant cutover breaks any deployment mid-rollout.
EOF

cat > docs/keys-reference.md <<'EOF'
---
title: Key management commands
summary: Every key subcommand with its flags, defaults and exit codes.
diataxis: reference
audience: developer
updated: 2026-10-20
tags: [keys, cli]
---
# Key management commands

## widget keys rotate

Exits 0 on success, 2 on invalid arguments.
EOF
ls docs/
```

Three pages on one subject, with three different jobs. A crawler sees three
pages about keys.

**Step 2: generate the block from the model**

```bash
cat > jsonld.py <<'PY'
"""Generate JSON-LD TechArticle blocks from the content model.

Every field comes from front matter the model already requires, which is the
whole design: nobody hand-writes structured data, so it cannot drift from the
page, and a page cannot ship without the fields the block needs.

The field doing the real work is `about`. Schema.org has no vocabulary for
"this is a how-to guide rather than an explanation", so the Diataxis type goes
in `about` as a readable statement of what kind of question the page can
answer. That is the one thing a crawler cannot infer from the prose.
"""
import json
from pathlib import Path

import yaml

BASE = "https://widget.example/docs"
SITE = "Widget platform"

#: What each page type can and cannot answer, stated for a machine.
ROLE = {
    "tutorial": "Tutorial: learning-oriented, assumes no prior context",
    "how-to": "How-to guide: task-oriented, gives steps for one goal",
    "reference": "Reference: factual description of the interface, no narrative",
    "explanation": "Explanation: design reasoning and tradeoffs, not instructions",
}

PROFICIENCY = {
    "new-user": "Beginner",
    "developer": "Expert",
    "operator": "Expert",
    "contributor": "Expert",
}


def block(meta, slug):
    url = f"{BASE}/{slug}/"
    return {
        "@context": "https://schema.org",
        "@type": "TechArticle",
        "headline": meta["title"],
        "description": meta["summary"],
        "url": url,
        "dateModified": str(meta["updated"]),
        "about": ROLE[meta["diataxis"]],
        "audience": {
            "@type": "Audience",
            "audienceType": meta["audience"],
        },
        "proficiencyLevel": PROFICIENCY[meta["audience"]],
        "keywords": ", ".join(meta.get("tags", [])),
        "isPartOf": {"@type": "WebSite", "name": SITE, "url": BASE},
        "inLanguage": "en",
    }


def head(meta, slug):
    """The whole machine-readable head, not only the JSON-LD."""
    url = f"{BASE}/{slug}/"
    tags = [
        f"<title>{meta['title']} | {SITE}</title>",
        f'<meta name="description" content="{meta["summary"]}">',
        f'<link rel="canonical" href="{url}">',
        f'<meta property="og:title" content="{meta["title"]}">',
        f'<meta property="og:description" content="{meta["summary"]}">',
        f'<meta property="og:type" content="article">',
        '<script type="application/ld+json">'
        + json.dumps(block(meta, slug), separators=(",", ":"))
        + "</script>",
    ]
    return "\n".join(tags)


def pages(root):
    for path in sorted(root.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        yield path, yaml.safe_load(text.split("---")[1])


if __name__ == "__main__":
    for path, meta in pages(Path("docs")):
        print(f"=== {path.name} ===")
        print(head(meta, path.stem))
        print()
PY
python3 jsonld.py
```

**Step 3: validate it, because a silently invalid block does nothing**

```bash
cat > validate.py <<'PY'
"""Check the generated blocks before publishing them.

Invalid structured data does not raise an error anywhere. It is ignored, and
the page looks fine, which is why this check exists at all.
"""
import json
import sys
from pathlib import Path

from jsonld import ROLE, block, pages

REQUIRED = ("@context", "@type", "headline", "description", "url", "dateModified")
MAX_DESCRIPTION = 160

failures = []
blocks = []

for path, meta in pages(Path("docs")):
    data = block(meta, path.stem)
    blocks.append((path.name, data))

    for field in REQUIRED:
        if not data.get(field):
            failures.append(f"{path.name}: missing {field}")
    if data["@context"] != "https://schema.org":
        failures.append(f"{path.name}: wrong @context")
    if len(data["description"]) > MAX_DESCRIPTION:
        failures.append(
            f"{path.name}: description {len(data['description'])} chars, "
            f"over {MAX_DESCRIPTION}"
        )
    if data["about"] not in ROLE.values():
        failures.append(f"{path.name}: `about` is not a known page role")
    try:
        json.dumps(data)
    except (TypeError, ValueError) as exc:
        failures.append(f"{path.name}: not serialisable: {exc}")

# The check that matters most: descriptions must differ. A site serving one
# site-wide description on every page is the commonest real failure, it looks
# completely fine, and it destroys every snippet and every link preview.
descriptions = {name: data["description"] for name, data in blocks}
if len(set(descriptions.values())) < len(descriptions):
    failures.append(
        f"only {len(set(descriptions.values()))} distinct descriptions "
        f"across {len(descriptions)} pages"
    )

for failure in failures:
    print(f"JSON-LD  {failure}", file=sys.stderr)
print(f"{'FAIL' if failures else 'ok'}: {len(blocks)} blocks, {len(failures)} problem(s)")
sys.exit(1 if failures else 0)
PY
python3 validate.py; echo "exit=$?"
```

**Step 4: show what a consumer learns from the block that the HTML does not say**

```bash
python3 - <<'PY'
import json
from pathlib import Path

from jsonld import block, pages

print("A crawler reading only the rendered prose sees three pages about keys.")
print("Reading the structured data, it can route a question:\n")

questions = [
    ("how do I rotate a key", "How-to guide"),
    ("why is there an overlap window", "Explanation"),
    ("what exit code does rotate return", "Reference"),
]

blocks = {path.stem: block(meta, path.stem) for path, meta in pages(Path("docs"))}

for question, wanted_role in questions:
    match = [
        slug for slug, data in blocks.items()
        if data["about"].startswith(wanted_role)
    ]
    print(f"  {question!r}")
    print(f"    wants: {wanted_role}")
    print(f"    page:  {match[0] if match else 'none'}")

print("\nThe `about` field is the routing signal. Nothing else in the HTML")
print("distinguishes these three pages by what kind of answer they support.")
PY
```

**What you built.** Generated JSON-LD, a validator including the
duplicate-description check, and a demonstration of the one field that carries
information nothing else in the HTML does.

## Reference

### The fields worth setting, and where each comes from

| Field | Source | Why |
|---|---|---|
| `@type: TechArticle` | the page type | The right schema.org type for developer docs |
| `headline` | `title` | What a crawler shows |
| `description` | `summary` | The snippet. Must be per-page |
| `url` | the page URL | Canonical identity |
| `dateModified` | `updated` | Freshness, which crawlers weight |
| **`about`** | **`diataxis`** | **What kind of question this answers. The one irreplaceable field** |
| `audience.audienceType` | `audience` | Who it is for |
| `proficiencyLevel` | derived from `audience` | A schema.org field that happens to fit |
| `keywords` | `tags` | Weak signal, free to emit |
| `isPartOf` | site config | Groups the corpus |

Every one is derived. **Nobody hand-writes a structured-data block**, for the
same reason nobody hand-writes an API reference.

### Why `about` carries the Diátaxis type

Schema.org has no field for "this is a how-to guide rather than an explanation
of the same subject". `TechArticle` has `proficiencyLevel` and
`dependencies`, and nothing for genre.

So the type goes in `about` as a readable sentence. That is a slight misuse of
the field and it is the best available option, because the alternative is
losing the single most useful fact about a page at the HTML boundary. Worth
saying out loud rather than pretending the vocabulary fits.

### Types other than TechArticle

| Type | Use for |
|---|---|
| `TechArticle` | The default for developer documentation |
| `HowTo` | A page with discrete numbered steps; supports `step` |
| `APIReference` | Generated API reference, as a subtype of TechArticle |
| `FAQPage` | A page of genuine question-and-answer pairs |
| `SoftwareApplication` | A product landing page, not a docs page |
| `BreadcrumbList` | Navigation position, emitted alongside |

`HowTo` is tempting and usually not worth it: the step markup is laborious and
the gain over `TechArticle` plus a good `about` is small. `FAQPage` has been
abused enough that search engines discount it.

### What to validate, and why each check exists

| Check | Catches |
|---|---|
| Required fields present | A block missing `headline` is ignored silently |
| `@context` is exactly `https://schema.org` | A typo makes the block inert |
| Description length under 160 | Truncated snippets |
| `about` is a known role | A typo in the type, which defeats the point |
| JSON serialises | A date object that was never going to render |
| **Descriptions differ across pages** | **The commonest real failure** |

**The last row is the one to build first.** A site serving its site-wide
description on every page looks completely correct in a browser, passes every
other check, and destroys every search snippet and every link preview. It is
also the default behaviour of several static site generators unless you wire the
per-page field through, which is a mistake this guide made in its companion
project and only caught by looking at the rendered HTML.

### Honest limits

| Claim | Reality |
|---|---|
| "It improves rankings" | Not directly. It affects how results are displayed and parsed |
| "Assistants read it" | Some do; coverage is uneven and undocumented |
| "`about` is the right field for genre" | It is the least wrong field available |
| "Rich results are guaranteed" | No. Eligibility, not entitlement |
| "More schema is better" | Invalid or irrelevant markup is ignored at best |

Present it internally as cheap, generated, and useful for parsing rather than
as a ranking lever, because the ranking claim is overstated everywhere and
someone in the room will know it.

## How to talk about it

**What a competent answer sounds like.** Lead with the boundary problem, which is
the documentation-specific insight. "The page type is the most useful field in
our content model, and it stops existing at the HTML boundary: front matter does
not reach a crawler. So I generate a `TechArticle` block from the required
fields and put the Diátaxis type in `about` as a readable sentence, since
schema.org has no genre field. It is a slight misuse of `about` and the
alternative is losing the distinction entirely. All of it is generated, and the
check I care about most is that descriptions differ across pages, because a
site-wide description on every page looks fine and destroys every snippet."

**The follow-up is "does any of this actually do anything",** and it deserves a
straight answer rather than a defence. Structured data is not a ranking factor;
it affects display eligibility and makes a page parseable without a crawler
guessing from prose. The honest reason to do it is that it costs an afternoon,
it is generated so it cannot rot, and it forces per-page descriptions, which is
worth having regardless. If someone wants a ranking promise, they should not get
one.

**The tradeoff to volunteer.** This is a second representation of facts that
already exist in front matter, and a second representation can drift. Generating
it removes most of that risk and not all: a change to the content model needs a
corresponding change here, and nothing fails if you forget. Hence the validator,
and hence keeping the block minimal. A sprawling structured-data block with
fifteen fields is fifteen chances to drift for a benefit nobody has measured.

**One sharper point.** The strongest observation is that **structured data is where
you find out whether your content model survives contact with the outside
world.** Every field you cannot map onto a public vocabulary is a field only
your own tooling can use, and that is fine for `audience` and genuinely awkward
for page genre, which is your most valuable facet. Noticing that the thing you
most want to tell a machine has no standard way to say it is a more interesting
position than listing schema.org types, and it is the sort of gap a
`KnowledgeOps` role is being hired to notice.

## How to prove it

**The artifact.** A generated block in a build step, with the validator, and
specifically the distinct-descriptions check.

**Three things to do, in order:**

1. **Run the golden path.** Step 4 is the demonstration: three pages on one
   subject, routed by `about`, which nothing else in the HTML supports.
2. **Check a real site for the duplicate-description failure.** Fetch three
   pages of any documentation site and compare their meta descriptions. It is
   two minutes and the hit rate is high.
3. **Generate the block from front matter and gate it.** Not hand-written, with
   the validator in CI. That is the difference between structured data and a
   snippet somebody pasted into a template once.

**What makes it credible rather than decorative.** Listing schema.org types proves nothing. A generated
block, a validator whose first check is that descriptions differ, and an
articulated reason for putting the page genre in `about` demonstrates that you
thought about what a machine can and cannot learn from your HTML.

## Related

- [SEO for documentation](seo-for-docs.md), the human-facing half
- [Generative engine optimization](geo.md), the assistant-facing half
- [Crawlability and the agent-ready front door](crawlability.md), being fetched at all
- [Metadata for navigation and retrieval](metadata.md), where the fields come from
