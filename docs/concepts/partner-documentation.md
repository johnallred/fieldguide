---
title: Documentation for partners and internal teams
summary: One corpus serving three audiences with different access, different trust, and different consequences for a leak.
diataxis: explanation
audience: operator
concept: partner-documentation
tags: [craft, context]
---

# Documentation for partners and internal teams

`context` · difficulty 2 · 3h

> deliver Simulation Technology knowledge to developers, partners, internal teams, and the AI agents that increasingly sit between them and our documentation

> Source: nvidia posting, verbatim

**Prerequisites:** [Metadata for navigation and retrieval](metadata.md)

## What it is

Serving several audiences with different access rights out of one corpus:
public developers, contracted partners, internal teams, and now the agents
acting for each of them. The hard part is not writing differently for each. It
is that the same source tree has to produce different outputs, and a mistake
publishes something it should not.

## Why the job asks for it

It is the first sentence of the NVIDIA posting, and the list is deliberate:
developers, partners, internal teams, and AI agents. Later, among the partner
functions, "Partner Programs".

This is tagged `context` rather than `core` because you will not design the
access model, and most of it is someone else's policy. But being unaware of it
is how an audience field becomes a security boundary by accident. On a Tuesday
this shows up as a question with a non-obvious answer: this page explains a
scheduling behaviour using an example from a named studio's production. Which
outputs can it appear in?

The reason it belongs in the guide at all is the fourth audience. **An agent
inherits the access of whoever it acts for, and a retrieval corpus does not
inherit anything unless somebody built that.** A single vector index over all
four tiers, queried by an assistant, is an access-control failure waiting to
happen, and it is a new failure mode that the navigation-era version of this
problem did not have.

## The golden path

Build a corpus with three tiers and a publish step that physically cannot leak.
Thirty minutes.

**Step 1: declare the tier as a field, with a closed vocabulary**

```bash
mkdir -p partner-drill && cd partner-drill
mkdir -p docs
cat > docs/install.md <<'EOF'
---
title: Install the SDK
visibility: public
---
# Install the SDK
Run the installer.
EOF
cat > docs/certification.md <<'EOF'
---
title: Partner certification process
visibility: partner
---
# Partner certification process
Submit your build to the certification portal.
EOF
cat > docs/scheduling-internals.md <<'EOF'
---
title: Scheduler internals
visibility: internal
---
# Scheduler internals
The dispatcher uses a work-stealing queue. Studio A's 2026 production hit a
pathological case at 400 concurrent shots.
EOF
ls docs/
```

**Step 2: build the publish step as a whitelist, never a filter**

The direction matters more than anything else on this page.

```bash
cat > publish.py <<'PY'
"""Publish one visibility tier by COPYING what is allowed in.

The critical design decision is the direction. A filter that excludes
`internal` pages leaks a page whose field is missing, misspelled, or a value
nobody anticipated. A whitelist that includes only `public` pages leaks
nothing when a field is wrong: it fails closed, and the page is simply absent,
which someone notices.

That asymmetry is the whole reason this script is shaped this way. One
direction fails by over-publishing and the other by under-publishing, and only
one of those is recoverable.
"""
import shutil
import sys
from pathlib import Path

import yaml

# Who may see what. A tier sees its own content and everything less
# restricted, which is the only ordering assumption here.
TIERS = {
    "public": ["public"],
    "partner": ["public", "partner"],
    "internal": ["public", "partner", "internal"],
}


def main(tier: str, docs: Path, out: Path) -> int:
    allowed = TIERS.get(tier)
    if allowed is None:
        print(f"unknown tier {tier!r}; known: {sorted(TIERS)}", file=sys.stderr)
        return 2

    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    included, skipped, rejected = [], [], []
    for page in sorted(docs.glob("*.md")):
        text = page.read_text(encoding="utf-8")
        try:
            front = yaml.safe_load(text.split("---")[1]) or {}
        except Exception:
            rejected.append((page.name, "unparseable front matter"))
            continue

        visibility = front.get("visibility")
        if visibility is None:
            # Not silently skipped: a missing field is a content-model
            # violation and someone has to fix it.
            rejected.append((page.name, "no visibility field"))
            continue
        if visibility not in TIERS:
            rejected.append((page.name, f"unknown visibility {visibility!r}"))
            continue

        if visibility in allowed:
            shutil.copy2(page, out / page.name)
            included.append(page.name)
        else:
            skipped.append((page.name, visibility))

    print(f"tier {tier!r}: {len(included)} included, {len(skipped)} withheld, "
          f"{len(rejected)} rejected")
    for name in included:
        print(f"  include  {name}")
    for name, visibility in skipped:
        print(f"  withhold {name}  ({visibility})")
    for name, why in rejected:
        print(f"  REJECT   {name}  ({why})", file=sys.stderr)

    # A page nobody can classify blocks the build rather than leaking or
    # vanishing quietly.
    return 1 if rejected else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], Path("docs"), Path(f"site-{sys.argv[1]}")))
PY
python3 publish.py public
echo "---"
python3 publish.py partner
```

**Step 3: prove it fails closed**

```bash
cat > docs/oops.md <<'EOF'
---
title: Unclassified page
---
# Unclassified page
Something nobody set a visibility on.
EOF
python3 publish.py public; echo "exit=$?"

cat > docs/typo.md <<'EOF'
---
title: Typo page
visibility: publc
---
# Typo page
EOF
python3 publish.py public; echo "exit=$?"
test -f site-public/typo.md && echo "LEAKED" || echo "not published: fails closed"
```

**What you built.** A publish step that blocks on any page it cannot classify
and publishes only what it was told to. Both the missing field and the
misspelled value produce a build failure and an absent page, never a leak.

The misspelling case is the one to notice. `visibility: publc` under a filter
design would not match `internal` and would therefore be published. Under the
whitelist it matches nothing and is withheld. **Same typo, opposite outcome.**

## Reference

### The four audiences and what each changes

| Audience | Access | What changes in the content |
|---|---|---|
| Public developers | Anyone | No customer names, no unreleased features, no internal URLs |
| Partners | Contract | Certification, co-marketing, early access. Often under NDA |
| Internal teams | Employment | Runbooks, incident history, named customers, roadmap |
| Agents | Whatever their principal has | Nothing, and that is the problem |

### The agent row, in detail

This is the part that is genuinely new and the part worth raising.

| Mechanism | Access-aware by default? |
|---|---|
| A published site per tier | Yes, by URL |
| Navigation and search within a site | Yes, same boundary |
| A single vector index over the whole corpus | **No** |
| [llms.txt](llms-txt.md) | No, unless generated per tier |
| An [MCP server](mcp.md) over the source tree | **No**, unless it filters per caller |

The two bolded rows are where the leak happens. An assistant indexed over
everything will answer a public developer's question with an internal chunk,
fluently and with no indication that it should not have. The fix is one index
per tier, or a filter applied at query time with the caller's tier as a hard
constraint, which is the same
[filter-before-ranking](metadata.md) argument the rest of this guide makes for
quality reasons, here for a much less forgiving one.

### Whitelist versus filter

| Design | A missing field | A misspelled value | Fails by |
|---|---|---|---|
| Include only allowed tiers | withheld | withheld | under-publishing |
| Exclude restricted tiers | **published** | **published** | over-publishing |

Only one of those failure modes can be undone.

### What is out of scope for you

Worth saying plainly, since this is `context` tier:

- The access model itself is legal and policy work.
- NDA terms, and what partner content may contain, are Partner Programs' call.
- Authentication for a partner portal is platform engineering's.
- Whether a customer can be named is a commercial question.

Your job is that the content model carries the distinction, the publish step
fails closed, and the retrieval layer respects it.

## How to talk about it

**What a competent answer sounds like.** Lead with the whitelist and the agent
problem. "Visibility is a required field with a closed vocabulary, and the
publish step copies in what is allowed rather than filtering out what is not, so
a missing or misspelled value withholds the page instead of publishing it. The
part I would want to check at a company with partners is the retrieval layer: a
single index over all tiers will answer a public question with internal content,
and nothing about that failure is visible."

**The follow-up is likely about the single-source argument**, meaning why not
keep internal content in a separate repository entirely. That is a legitimate
design and often the right one. The honest comparison: separate repositories
make a leak nearly impossible and make reuse nearly impossible too, so the same
procedure gets written twice and drifts. One tree with a visibility field keeps
content reusable and makes the publish step safety-critical. Which is right
depends on how much content genuinely spans tiers, and on whether you trust the
gate. For a corpus where most internal content is runbooks and incident history,
separate repositories are usually simpler.

**The tradeoff to volunteer.** A visibility field makes every author make a
security-adjacent decision while writing, and most authors are not equipped to
make it. The field defaults to nothing on purpose, so an unclassified page blocks
the build, but that means an author can be stopped by a question they cannot
answer. The mitigation is a default by directory with an explicit override, so
the common case needs no decision, and it is a real weakening of the model in
exchange for authors not being blocked.

**One sharper point.** The strongest thing to say is that **publishing a corpus for
retrieval converts an information-architecture field into an access-control
boundary**, and almost nobody notices the moment it happens. An `audience` field
used for navigation is a convenience; the same field used to partition a vector
index is a security control, and it was designed as the former. Raising that
distinction unprompted is the most valuable thing on this page, and at a company
with partner programs and simulation customers under NDA it is a live concern
rather than a hypothetical.

## How to prove it

**The artifact.** The whitelist publish step plus the failing cases. It is forty
lines and it demonstrates a design instinct that is hard to claim otherwise.

**Three things to do, in order:**

1. **Run the golden path**, including both failure cases. The typo case is the
   demonstration: same input, opposite outcome depending on the direction of the
   logic.
2. **Audit one retrieval layer for tier awareness.** If you have access to any
   corpus with internal content and any search or assistant over it, check
   whether the index is partitioned. The answer is usually no, and reporting it
   is a genuinely useful finding.
3. **Write the one-paragraph note** on why an IA field became an access control
   when the corpus was indexed. Short, specific, and it is the kind of
   observation that gets remembered.

**What makes it credible rather than decorative.** Multi-audience documentation is a common claim. A
publish step that fails closed, with a demonstrated typo case, and a stated
concern about the retrieval layer, is concrete and shows you have thought about
the failure rather than the feature.

### How this would be demonstrated elsewhere

Multi-audience publishing needs more than one audience. This repository has one
corpus and no partners, so the mechanism can be built and the consequences
cannot be observed.

**What you need.** Two audiences with different entitlements, and content that
must not cross between them. A partner tier and a public tier is the usual
shape.

**What a learner would do.** Build the publish step so it fails closed: a page
with no audience field does not publish anywhere, rather than publishing
everywhere. Then plant a page tagged for partners only, run the public build,
and confirm it is absent.

**What you would see.**

| Test | Expected | Why it matters |
|---|---|---|
| A partner page in the public build | Absent | The basic case |
| A page with no audience field | Build fails | Fail closed, never open |
| A partner page's heading in the public search index | Absent | The leak people miss |
| A public page linking to a partner page | Build fails | The other leak people miss |
| A partner term in a public page's prose | Nothing catches it | The honest limit |

Rows three and four are the ones to design for, because a build that filters
pages while leaking their titles into a shared index has told the public
exactly what it is not allowed to see. Row five is why this needs a reviewer as
well as a gate.

**Why it does not commit.** The gate commits and the stakes do not. The
demonstration that matters is a year of publishing without a leak, and that is
an absence of incidents in someone else's organisation.

## Related

- [Metadata for navigation and retrieval](metadata.md), where the field lives
- [Taxonomy and controlled vocabularies](taxonomy.md), why the value set is closed
- [MCP](mcp.md) and [RAG pipelines](rag.md), the layers that need to respect it
- [Security guidance as encoded standard](security-documentation.md), the adjacent concern
