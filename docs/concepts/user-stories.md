---
title: User stories as a documentation standard
summary: Using the story format as a validator on documentation scope rather than as a planning ritual.
diataxis: explanation
audience: contributor
concept: user-stories
tags: [craft, supporting]
---

# User stories as a documentation standard

`supporting` · difficulty 1 · 2h

> Encode standards (user stories, release readiness, onboarding, security guidance) into templates

> Source: nvidia posting, verbatim

## What it is

The format "as a *role*, I want to *do something*, so that *outcome*", used here
as a constraint on documentation scope rather than as a planning artifact. A
page that cannot be stated as one story is usually more than one page.

## Why the job asks for it

NVIDIA lists it first among the standards to encode "into templates, validators,
and guided workflows rather than static documents". That placement is the
interesting part. User stories are normally a product-planning artifact, and
NVIDIA is asking for them as something a *template* enforces.

Read that way, the requirement makes sense. The story format is a cheap test for
the most common documentation defect, which is a page with no single reader in
mind. "As a developer, I want to configure retry behaviour, so that transient
upstream failures do not surface to my callers" is a page. "Retry and timeout
configuration and the connection pool" is three.

On a Tuesday it is a scoping conversation that takes ninety seconds instead of
twenty minutes. An engineer asks for a page about the inference server. You ask
who wants what, and it turns out there are two readers: an operator who wants to
size a deployment, and a developer who wants to send a request. Those are two
pages and neither was going to be well served by one.

This is tagged `supporting` rather than `core` because the underlying skill is
[Diátaxis](diataxis.md) and [content modelling](content-model.md); the story
format is a convenient front end to both. Worth two hours, not more.

## The golden path

Use the format as a validator on a real page set. Twenty minutes.

**Step 1: write the stories for pages that already exist**

```bash
mkdir -p story-drill && cd story-drill
cat > stories.md <<'EOF'
Try to state each existing page as exactly one story.

PAGE: "Inference server configuration"
  As an operator, I want to size a deployment, so that it handles peak load.
  As a developer, I want to send my first request, so that I know it works.
  As an operator, I want to tune batching, so that throughput improves.
  -> THREE stories. Three pages, or one page with three sections and a
     reader who has to filter.

PAGE: "Configure retry behaviour"
  As a developer, I want to configure retries, so that transient upstream
  failures do not reach my callers.
  -> ONE story. The page is correctly scoped.

PAGE: "Troubleshooting"
  As ... anyone, I want ... to fix whatever is broken, so that ... it works.
  -> NO story. The format fails here, and that is a real limit rather than
     a defect in the page. Troubleshooting is indexed by symptom, not by goal.
EOF
cat stories.md
```

**Step 2: make the test mechanical**

```bash
mkdir -p docs
cat > docs/retries.md <<'EOF'
---
title: Configure retry behaviour
diataxis: how-to
audience: developer
story:
  role: developer
  wants: configure retry behaviour
  so_that: transient upstream failures do not reach my callers
---
# Configure retry behaviour
EOF

cat > docs/inference-server.md <<'EOF'
---
title: Inference server configuration
diataxis: how-to
audience: operator
---
# Inference server configuration
EOF

cat > check_stories.py <<'PY'
"""Require a single, well-formed story on every how-to and tutorial page.

Reference and explanation pages are exempt: a reference page serves every
reader with a question, and demanding one role for it would be false.

The check is deliberately shallow. It cannot tell whether the story is
honest, only whether somebody was made to write one, which is most of the
value: the format's benefit is the thirty seconds of thought at authoring
time, not the stored text.
"""
import sys
from pathlib import Path

import yaml

NEEDS_STORY = {"how-to", "tutorial"}
AUDIENCES = {"new-user", "developer", "operator", "contributor"}


def main(docs: Path) -> int:
    failures = []
    for page in sorted(docs.glob("*.md")):
        front = yaml.safe_load(page.read_text(encoding="utf-8").split("---")[1]) or {}
        if front.get("diataxis") not in NEEDS_STORY:
            continue

        story = front.get("story")
        if not story:
            failures.append(f"{page.name}: a {front['diataxis']} page needs a story")
            continue
        for field in ("role", "wants", "so_that"):
            if not story.get(field):
                failures.append(f"{page.name}: story is missing {field!r}")
        if story.get("role") not in AUDIENCES:
            failures.append(
                f"{page.name}: story role {story.get('role')!r} is not a declared audience"
            )
        if story.get("role") != front.get("audience"):
            failures.append(
                f"{page.name}: story role {story.get('role')!r} disagrees with "
                f"audience {front.get('audience')!r}"
            )

    for failure in failures:
        print(f"STORY  {failure}", file=sys.stderr)
    print(f"{'FAIL' if failures else 'ok'}: {len(failures)} story problem(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(Path("docs")))
PY
python3 check_stories.py
```

**Step 3: split the page the check found**

```bash
cat > docs/size-a-deployment.md <<'EOF'
---
title: Size an inference deployment
diataxis: how-to
audience: operator
story:
  role: operator
  wants: size a deployment
  so_that: it handles peak load without over-provisioning
---
# Size an inference deployment
EOF
cat > docs/send-first-request.md <<'EOF'
---
title: Send your first inference request
diataxis: tutorial
audience: developer
story:
  role: developer
  wants: send a first request
  so_that: I know the server is working
---
# Send your first inference request
EOF
rm docs/inference-server.md
python3 check_stories.py
```

**What you built.** A check that fails when a task page has no single reader,
and a page set where the split was forced by the format rather than argued
about. The cross-check between `story.role` and `audience` is the part worth
keeping: it catches a page that declares one audience and tells a story about
another, which is a reliable sign the page is serving two.

## Reference

### The format, and what each part constrains

| Part | Constrains | Failure if vague |
|---|---|---|
| As a *role* | Who the page is for | A page written for everyone, filtered by nobody |
| I want to *do something* | The page's scope, one goal | Scope creep into adjacent tasks |
| So that *outcome* | Whether the goal is worth documenting | A page about a capability nobody needs |

The third part is the one people skip and the one that catches the worst waste.
If you cannot finish "so that", the page may be documenting something because it
exists rather than because anyone needs it.

### Where the format applies and where it does not

| Page type | Story? | Why |
|---|---|---|
| How-to guide | Yes, exactly one | The reader arrived with a goal |
| Tutorial | Yes, one, and the author owns it | The reader has no goal yet |
| Reference | No | Serves every reader with a question |
| Explanation | No | The reader wants understanding, not a task |
| Troubleshooting | No | Indexed by symptom rather than by goal |

Demanding a story on a reference page produces a fake one, which is worse than
none: it trains authors to satisfy the field rather than to think.

### Honest limits

| Limit | Consequence |
|---|---|
| The check verifies presence, not honesty | An author can write a vague story to pass |
| The format is weak for troubleshooting | Two whole page types are exempt |
| It is a planning artifact borrowed into docs | Teams that dislike agile ritual will resist the name |
| One story per page is sometimes wrong | A genuinely shared task across two roles |

The last row is real. "As a developer or an operator, I want to read the logs"
is a legitimate single page, and the strict one-role rule would split it
pointlessly. A good check warns rather than blocks on that case.

## How to talk about it

**What a competent answer sounds like.** Frame it as a scope test, not as a
planning practice, because that is what distinguishes the documentation use from
the product-management use. "I require a story on how-to and tutorial pages, and
I cross-check the role against the declared audience. It is a cheap test for the
commonest defect, which is a page with two readers. The inference server page
turned out to be three stories, so it became two pages and a reference."

**The follow-up is likely to be sceptical**, some version of "is this not
bureaucracy?" Agree partly. The honest position: the value is in the ninety
seconds of thought at authoring time, and the stored field is mostly a way to
make that thinking non-optional. If a team already scopes pages well, the field
is overhead. It earns its place on a corpus with many authors of varying
experience, which is exactly the NVIDIA situation.

**The tradeoff to volunteer.** This is a required field, and every required
field is friction on every contributor forever. On a corpus of twenty pages with
one author it is pure cost. It also invites gaming: an author who wants to ship
writes a vague story, the check passes, and now there is a field full of noise
that a later reader might trust. That failure is worse than not having the
field, which is why this is `supporting` and why the check should be scoped to
the two page types where the format actually fits.

**One sharper point.** The useful insight is that **the story format and
[Diátaxis](diataxis.md) are checking the same thing from different directions.**
Diátaxis asks what kind of page this is; the story asks who wants what. A page
that fails one usually fails the other, and the story version is easier to
explain to an engineer who has never heard of Diátaxis and is not going to read
a framework. Using it as the friendly front end to a stricter model underneath
is a genuinely practical move.

## How to prove it

**The artifact.** The check, scoped to the right page types, plus one page you
split because the format forced it.

**Three things to do, in order:**

1. **Write stories for ten existing pages.** Twenty minutes. Count how many
   need more than one; in most corpora it is a third or more, and that number is
   the finding.
2. **Add the field and the check** to a real repository, exempting reference and
   explanation. The exemptions are what make it credible.
3. **Split one page** because the stories forced it, and link the before and
   after. The split is the evidence; the field is just the prompt.

**What makes it credible rather than decorative.** User stories are a well-worn format and claiming to
use them signals nothing. Using them as a validator on documentation scope, with
the two page types where they do not apply explicitly exempted, shows you have
thought about the format's limits rather than adopted it.

### How this would be demonstrated elsewhere

The format is trivial to show and the discipline is not. Writing user stories
proves nothing; using them to refuse scope is the skill, and refusal needs
someone to refuse.

**What you need.** A documentation request from someone who wants more than the
reader needs.

**What a learner would do.** Take a documentation task as it arrived, write the
reader's story for it, and then list what the task asked for that the story
does not justify. Take that list to whoever asked.

**What you would see.**

| Outcome | What it means |
|---|---|
| Scope agreed down | The story did its work |
| Scope defended with a different reader | Good: now you have two stories, both written |
| Scope defended with "it should be complete" | The format has found an unstated goal |
| A page type the story cannot describe | The format's limit, and worth writing down |

The last row matters most and is where most advocacy for this format stops. A
reference page has no user story worth writing: nobody reads a parameter table
as a journey. Knowing which page types the format does not fit is the evidence
that you use it rather than recite it.

**Why it does not commit.** The story commits; the conversation where it
changed somebody's mind does not. The nearest available artifact is a scope
decision recorded with its story beside it, in a tracker rather than a
repository.

## Related

- [Diátaxis](diataxis.md), the stricter model underneath
- [Content models](content-model.md), where the field lives
- [Templates and scaffolding](templates-scaffolding.md), how the prompt reaches an author
- [Designing tutorials](tutorial-design.md), where the author owns the goal instead
