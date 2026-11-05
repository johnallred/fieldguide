---
title: Retiring content
summary: "Deleting a page without breaking the links to it, and why corpora only ever grow."
diataxis: how-to
audience: developer
concept: content-retirement
tags: [ia, supporting]
---

# Retiring content

`supporting` · difficulty 2 · 3h

!!! quote "Asked for by name"
    NVIDIA: "Measure outcomes such as time-to-first-success, support deflection, repeat questions, and AI answer quality, and use the data to decide what to build, fix, or retire"

**Prerequisites:** [Content lifecycle and governance](content-lifecycle.md)

## What it is

Removing a page from the corpus on purpose: deciding it should go, redirecting
its URL, and dealing with everything that pointed at it. NVIDIA lists retire
alongside build and fix as one of three outcomes of measurement, which is more
than most teams do, because most teams have no third option.

The mechanics are easy. The reason corpora only ever grow is not technical.

## Why the job asks for it

Because an unretired corpus degrades in a way that no amount of writing fixes.
Every stale page competes with a current one in search, dilutes
[retrieval](rag.md), and costs a reviewer attention. Past a certain size the
most valuable documentation work available is deletion, and nobody is
authorised to do it.

NVIDIA naming retirement as a measurement outcome is the important part. The
decision to retire needs evidence, which means it needs the
[measurement](docs-analytics.md) category to exist first, and it means the answer to
"can we delete this" stops being a matter of opinion.

## The golden path

Retire a page properly, then find the configuration that decides whether a
mistake is loud or silent. About twenty-five minutes.

**Step 1: a redirect**

````bash
mkdir -p retire-demo/docs && cd retire-demo
pip install --quiet mkdocs mkdocs-redirects

cat > mkdocs.yml <<'EOF'
site_name: R
plugins:
  - redirects:
      redirect_maps:
        old-guide.md: new-guide.md
EOF
printf '# New guide\n\nThe current content.\n' > docs/new-guide.md
printf '# Home\n\nSee the [new guide](new-guide.md).\n' > docs/index.md

python3 -m mkdocs build -q
````

**Step 2: see what the retired URL now serves**

```bash
python3 -c "
import re
from pathlib import Path
h = Path('site/old-guide/index.html').read_text()
print(re.search(r'<meta[^>]*refresh[^>]*>', h).group(0))
"
```

```
<meta http-equiv="refresh" content="0; url=../new-guide/">
```

A generated page containing a **client-side** meta refresh. Note what that is
not: it is not an HTTP 301. The distinction matters, because a 301 transfers
accumulated ranking signals to the new URL and a meta refresh is a weaker,
slower signal that search engines treat with more suspicion. On static hosting
this is often all you can do; if you control the server or the CDN, prefer a
real 301 and keep the meta refresh as the fallback.

**Step 3: point the redirect at nothing**

```bash
sed -i 's/new-guide.md$/gone.md/' mkdocs.yml
python3 -m mkdocs build 2>&1 | grep -i redirect
echo "exit=$?"
```

```
WARNING - Redirect target 'gone.md' does not exist!
exit=0
```

The plugin notices, declines to generate the redirect page, and the build
succeeds. So the retired URL becomes a hard 404 rather than a redirect to a
404, which is better than it could have been, and the build still exits zero.

**Step 4: make it loud**

```bash
python3 -m mkdocs build --strict >/dev/null 2>&1; echo "exit=$?"
```

```
exit=1
```

With `--strict`, a dangling redirect target fails the build. Measured
behaviour, all three cases:

| Case | Build | Result |
|---|---|---|
| Valid redirect | exit 0 | Meta refresh page generated |
| Dangling target | exit 0, with a warning | No page; retired URL 404s |
| Dangling target, `--strict` | exit 1 | Nothing ships |

**Step 5: deal with what pointed at the page**

The redirect handles external links. Internal references are a separate problem
and the one that is usually forgotten:

```bash
grep -rn "old-guide" docs/ | grep -v "^docs/old-guide"
```

Internal links should be **rewritten to the new target**, not left to bounce
through the redirect. A corpus whose internal links all pass through redirects
accumulates chains, and a chain eventually contains a broken hop that
[link checking](link-checking.md) cannot see, because each individual hop
resolves.

**What you built.** A retirement that redirects, a check that makes a mistaken
target fail, and a rule about internal links that keeps chains from forming.

## Reference

### The retirement checklist

| Step | Why |
|---|---|
| Decide, with evidence | Traffic, support deflection, repeat questions |
| Pick the successor, or accept there is none | A redirect needs a target |
| Rewrite internal links to the successor | Prevents redirect chains |
| Add the redirect | External links and bookmarks |
| Remove it from navigation and any index | Otherwise it is reachable and gone |
| Remove it from retrieval artifacts | A deleted page still in a vector store still answers |
| Note the retirement somewhere | So the decision is not relitigated annually |

The retrieval row is new and easy to miss. A page removed from the site but
still present in an index or an `llms.txt` keeps answering questions from
beyond the grave, and the answer looks authoritative.

### When not to redirect

| Situation | Do this instead |
|---|---|
| No successor exists | A 410 Gone, or a tombstone page explaining the removal |
| The content was wrong, not outdated | Say so on the tombstone; a silent redirect looks evasive |
| The page documented a removed feature | Point at the migration path, not the nearest page |
| It is one of many pages merged into one | Redirect to the anchor, not just the page |

Redirecting to a vaguely related page is worse than a 404. A reader who lands
somewhere that does not answer their question and shows no sign of knowing
what they asked has had their time wasted twice.

### Why corpora only grow

| Obstacle | Reality |
|---|---|
| Nobody owns deletion | Authoring has owners; removal usually does not |
| It feels like destroying work | Git has it forever; this fear is unfounded and real |
| Someone might need it | Possibly, and the measurement tells you |
| It might break a link | Solved, and it is the stated reason more often than the real one |
| No policy exists | So every deletion is a negotiation |

The fix is a written policy that makes deletion the default outcome for pages
meeting stated criteria, so that removal needs no new argument each time. That
is governance, not tooling, which is why this page sits downstream of
[content lifecycle](content-lifecycle.md).

### Evidence that justifies retirement

| Signal | Threshold worth discussing |
|---|---|
| Page views | Near zero over a full release cycle |
| Search exits | People find it and immediately leave |
| Support tickets citing it | Readers are being misled by it |
| Its subject no longer exists | Automatic candidate |
| Its [freshness](freshness-monitoring.md) queue age | Perpetually overdue and never claimed |

The last row is the useful one in practice. A page that has been in the review
queue for four quarters without an owner claiming it is a page nobody is
willing to maintain, and that is the evidence.

## How to talk about it

**Lead with why it does not happen.** "The mechanics of retirement are a
redirect and a link rewrite. The reason corpora only grow is that authoring has
owners and deletion does not, so every removal is a fresh negotiation. The fix
is a written policy that makes deletion the default for pages meeting stated
criteria."

**The follow-up is usually about breaking links**, and it is worth naming as
the stated reason more often than the real one. Redirects solve the external
case; internal links get rewritten rather than bounced, because chains
accumulate a broken hop that link checking cannot see.

**The tradeoff to volunteer.** Redirects are not free: each one is a permanent
entry in a map that grows forever, and after a few years the redirect map is
its own maintenance problem with chains and loops in it. Periodically
collapsing chains and dropping redirects for URLs that have had no traffic for
years is real work that nobody schedules.

**One sharper point.** A retired page still in a retrieval index keeps
answering questions. The site has deleted it, the vector store has not, and the
answer arrives with a citation to a URL that now 404s. Retirement has to reach
the retrieval artifacts, and that step is missing from essentially every
retirement checklist written before 2023.

## How to prove it

**The artifact.** A retirement that happened: a redirect, the internal links
rewritten in the same commit, and a written policy that authorised it.

**Three things to do, in order:**

1. Run the golden path. Step 3 and step 4 together are the point: the mistake
   is silent unless you have `--strict`.
2. Find your lowest-traffic page and try to retire it. Whatever blocks you is
   the actual obstacle, and it is probably not technical.
3. Check whether anything in your retrieval pipeline would notice a deleted
   page. Usually nothing does.

**What makes it credible rather than decorative.** Neither of this guide's
repositories has retired anything, which the [demonstrated](../demonstrated.md)
page records, and a project with no readers has no retirement evidence to act
on. What travels is the measured behaviour of the mechanism and the
retrieval-index point, which is the part of the checklist most teams are
currently missing.

### How this would be demonstrated elsewhere

A project with no readers has nothing to retire, so the mechanism here is
measured and the decision is not. Retirement is mostly a political act and the
evidence is that somebody agreed to lose something.

**What you need.** A corpus old enough to contain pages nobody should read,
and the authority to remove them. The second is the scarce one.

**What a learner would do.** Find the five oldest pages in a corpus you own,
check whether each still describes a thing that exists, and then try to delete
one. Record what happened: who objected, on what grounds, and what the
compromise was.

**What you would see.**

| Outcome | What it means |
|---|---|
| Deleted with a redirect | The healthy case, and the rarest |
| Marked deprecated instead | The usual compromise; now you maintain it forever |
| Kept because someone links to it | The link is the argument; check whether anyone follows it |
| Kept because removing it feels risky | The real reason, and it is not a documentation reason |
| Nobody could say who owns it | The finding worth reporting |

The last row is what the exercise usually produces, and it is more useful than
the deletion: a page nobody owns is a page nobody will update either.

**Why it does not commit.** A deletion leaves no artifact except an absence and
a redirect. The judgment, that this page cost more than it was worth, is a
conversation, and the strongest available evidence is a redirect map with a
reason beside each entry.

## Related

- [Content lifecycle and governance](content-lifecycle.md), which authorises this
- [Freshness monitoring](freshness-monitoring.md), the queue that identifies candidates
- [Link checking](link-checking.md), and why redirect chains defeat it
- [Crawlability](crawlability.md), the search-engine side of removing a URL
