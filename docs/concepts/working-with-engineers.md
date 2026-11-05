---
title: Working with engineers as sources
summary: Getting accurate information from people whose job is not documentation, repeatedly, without becoming a burden.
diataxis: explanation
audience: developer
concept: working-with-engineers
tags: [craft, supporting]
---

# Working with engineers as sources

`core` · difficulty 2 · 3h

> Partner with Engineering, Product, Security, Developer Relations, and Partner Programs so every release ships documented, discoverable, and supportable

> Source: nvidia posting, verbatim

**Prerequisites:** [Extracting tribal knowledge](sme-interviews.md), [Reviewing documentation](docs-review.md)

## What it is

Getting accurate information from people whose job is not documentation,
repeatedly, over years, without becoming the person they avoid. It is the
ongoing relationship rather than the one-off interview.

The mechanics matter more than the rapport. A process that asks engineers for
the cheapest thing they can give is worth more than being well liked.

## Why the job asks for it

NVIDIA lists five partner functions by name and attaches an outcome to the
partnership: "so every release ships documented, discoverable, and
supportable". Intel's version is "Partner with engineering, product, and
developer advocates so each new capability ships with tested documentation."

Both are asking for the same thing, which is that documentation stops being a
thing that happens after a release and becomes a thing the release cannot ship
without. That is a relationship problem before it is a process problem.

On a Tuesday it is an asymmetry you have to design around. You need forty
minutes of a staff engineer's attention; she is on call, mid-migration, and has
three reviews waiting. Documentation is somewhere below all of it on her list,
and reasonably so. **Any process that depends on her prioritising your work
above hers will fail**, so the design constraint is to need less from her, not
to persuade her to care more.

The thing that changes this permanently is being useful to them first, and the
most reliable way is [reading the code yourself](reading-code-to-verify.md). A
writer who arrives with "the page says 30, the constructor says None, which is
right?" is asking for ten seconds. A writer who arrives with "can you explain
timeouts to me" is asking for forty minutes. Same page, same outcome, two
hundred times the cost.

## The golden path

Build the three mechanisms that make engineer time cheap, and measure the ask.
Thirty minutes.

**Step 1: price every way of asking**

```bash
mkdir -p source-drill && cd source-drill
cat > asks.md <<'EOF'
| How you ask                                  | Their cost | Reliability |
|-----------------------------------------------|------------|-------------|
| "Can you explain X to me?"                    | 40 min     | medium      |
| "Can you review this page?"                   | 15 min     | medium      |
| "Is this specific sentence right?"            | 2 min      | high        |
| "The docs say 30, the code says None. Which?" | 10 sec     | high        |
| A PR they only have to approve                | 30 sec     | high        |
| A CI failure naming the file and the line     | 0 min      | high        |

The last row is the goal. Every mechanism below moves an ask one row down.
EOF
cat asks.md
```

Note that the cheap asks are also the *more reliable* ones. An engineer
confirming a specific number is operating on knowledge they can check. An
engineer explaining a subsystem from memory is reconstructing.

**Step 2: a review request they can answer in two minutes**

The trick is to ask for accuracy only, and to mark exactly where you are
unsure.

```bash
cat > review-request.md <<'EOF'
# Review request: "Configure retry behaviour"

I am not asking about wording. Three claims to confirm or correct:

1. `retries=3` makes 4 total requests (retries exclude the initial attempt).
   -> correct / wrong: ___

2. The maximum is 10, enforced client-side.
   -> correct / wrong: ___

3. Backoff is exponential with no jitter.
   -> correct / wrong: ___

One thing I could not determine from the code:
   Does the retry budget reset per call or per session?  ___

Everything else is my problem. If all three are right, reply "all good".
EOF
cat review-request.md
```

**Step 3: a template that collects what you need at the moment they know it**

The cheapest information is captured when the engineer is already thinking about
the change, in a field they are already filling in.

```bash
cat > pr-template.md <<'EOF'
<!-- .github/pull_request_template.md, docs section -->

## Documentation

- [ ] No user-visible change
- [ ] Docs updated in this PR
- [ ] Docs issue filed: #____

If a default, limit, or error type changed, say so here. One line is enough;
we will write the page.

Changed defaults or limits:
EOF
cat pr-template.md
```

That last prompt is the whole mechanism. **One line at the moment of the change
is worth an hour of archaeology later**, and it is a smaller ask than a review.

**Step 4: the gate that removes the ask entirely**

```bash
mkdir -p docs
cat > docs/retries.md <<'EOF'
---
title: Configure retry behaviour
verified_against: widget.client.WidgetClient
verified_on: 2026-10-26
claims:
  retries_default: 3
  retries_max: 10
---
# Configure retry behaviour

Set `retries` on the client. The default is 3; the maximum is 10.
EOF

cat > check_claims.py <<'PY'
"""Compare documented numeric claims against the implementation.

This is the mechanism that converts a recurring human ask into a build
failure. Nobody has to remember to tell the docs team that a default
changed, because the build says so.
"""
import sys
from pathlib import Path

import yaml

# Stands in for `inspect.signature` against the real client. In a real repo
# this imports the module and reads the defaults.
ACTUAL = {"retries_default": 5, "retries_max": 10}


def main(page: Path) -> int:
    front = yaml.safe_load(page.read_text(encoding="utf-8").split("---")[1])
    claims = front.get("claims", {})

    failures = []
    for name, documented in claims.items():
        actual = ACTUAL.get(name)
        if actual is None:
            failures.append(f"{name}: documented {documented}, not found in the code")
        elif actual != documented:
            failures.append(f"{name}: documented {documented}, code says {actual}")

    for failure in failures:
        print(f"CLAIM DRIFT  {page.name}: {failure}", file=sys.stderr)
    print(f"{'FAIL' if failures else 'ok'}: {len(claims)} claims checked, "
          f"{len(failures)} drifted")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(Path("docs/retries.md")))
PY
python3 check_claims.py
```

**What you built.** Three mechanisms at descending cost, and one gate that costs
nothing. The gate is the one that matters: the engineer who changed the default
from 3 to 5 did not have to remember you existed, and the build told you anyway.

That is the same move as [the systems mindset](systems-mindset.md), applied to a
social dependency rather than a technical one, and it is the thing that makes
this relationship sustainable over years.

## Reference

### The escalation, cheapest first

| Mechanism | Their cost | Use when |
|---|---|---|
| A CI check on a documented claim | zero | The claim is numeric or structural |
| A docs field in the PR template | 10 seconds | Any user-visible change |
| A specific yes/no question | 2 minutes | You read the code and one thing is ambiguous |
| A marked-up review request | 5 minutes | A page with several claims |
| A 30-minute extraction interview | 30 minutes | [Tribal knowledge](sme-interviews.md), once per topic |
| An open-ended explanation | 40 minutes | You are new, and sparingly |

### How to ask for a review

| Do | Why |
|---|---|
| Ask for accuracy, not wording | Style is your job; they will not do it and should not |
| Mark the claims you are unsure about | Scopes the review to minutes |
| Say what you could not determine | Invites the one answer only they have |
| Offer "all good" as a valid reply | Lowers the floor on responding |
| Send a draft, not a request for information | Experts correct well and compose badly |

### Things that destroy the relationship

| Mistake | Effect |
|---|---|
| Asking to be taught what the code would have told you | You become the expensive channel |
| Asking for wording feedback | They disengage from the parts that matter |
| Open-ended "any thoughts?" requests | Unbounded, so deferred forever |
| Publishing an unreviewed claim as verified | Breaks trust once, permanently |
| Reporting their mistake to their manager | Never recoverable |
| Asking the same thing twice because you did not write it down | Signals their time is cheap |

### The partner functions NVIDIA names, and what each wants

| Function | What they need from docs | What they can give you |
|---|---|---|
| Engineering | Accuracy they did not have to write | Defaults, error paths, the exception |
| Product | A documented path at launch | Which capability matters, and when |
| Security | Guidance that does not teach a bad pattern | Review of anything about credentials or data |
| Developer Relations | Something to point at in a talk | Direct developer feedback |
| Partner Programs | Content partners can use externally | The partner-specific constraints |

Reading that table as five different asks rather than one is most of
[release readiness](release-readiness.md).

## How to talk about it

**What a competent answer sounds like.** Lead with the cost reduction, not the
rapport. "I stopped asking engineers to explain things and started asking them
to confirm specific claims, after reading the code first. A review went from
forty minutes to two. Then I put the numeric claims in front matter and added a
check comparing them against the signatures, so for those the ask went to zero
and the build tells me when a default changes."

**The follow-up is about the engineer who will not respond,** and it is the real
question. The honest answer has layers. First, make the ask smaller: a two-minute
yes/no gets answered when a review request does not. Second, go where they
already are, which usually means a comment on their pull request rather than a
message in a channel. Third, publish with the gap marked: a page that says "the
retry budget's scope is unconfirmed" is better than a page that guesses, and it
is often what finally prompts a correction. What does not work is escalation,
which buys one response and costs the relationship.

**The tradeoff to volunteer.** Every mechanism that reduces the ask shifts work
onto you. Reading the code before asking is slower for you and faster for them.
Writing the draft first means you write things that turn out to be wrong. That
trade is correct, because your time is the cheaper resource and because the
alternative is a documentation process that stalls whenever someone is on call,
but it does mean the honest version of this job involves doing more of the work
than the org chart suggests.

**One sharper point.** The strongest version is that **you are not trying to make
engineers care about documentation.** That is the trap, and it is where most
documentation advocacy goes. You are trying to make the correct thing cost them
nothing: a field in a template they already fill in, a check that fails without
anyone's attention, a question answerable in ten seconds. Caring is not a
mechanism. Saying that plainly is unusual and it is exactly what NVIDIA's
"systems where the right way is easier than the wrong way" means when applied
to people.

## How to prove it

**The artifact.** A pull request template with a docs field, or a claim-checking
gate, plus one marked-up review request. Small artifacts, specific, and they
demonstrate the design instinct rather than the social skill.

**Three things to do, in order:**

1. **Rewrite a review request you have sent** into the three-claim form above.
   Ten minutes, and the difference is immediately visible.
2. **Add a docs section to a PR template** in any repository you can touch,
   with the "changed defaults or limits" prompt. That one line is the highest
   ratio of value to effort on this page.
3. **Build the claim gate.** Put one numeric claim in front matter and check it
   against the code. It is twenty lines and it is the thing that proves you
   think about this structurally rather than socially.

**What makes it credible rather than decorative.** Everyone says they collaborate well with engineers.
A PR template diff, a two-minute review request, and a check that fails when a
default drifts are three things an interviewer can look at, and together they
make a much more specific claim than any description of your working style.

### How this would be demonstrated elsewhere

This is the concept most thoroughly removed by a single-author repository.
Everything about it is the behaviour of two parties, and here there is one.

**What you need.** Engineers who own code you document, and enough standing
that a request of yours costs them something they will still pay.

**What a learner would do.** Make the smallest possible ask three times and
measure the response. A two-minute review request with the specific question
attached, not "please review". Then record whether it came back, how fast, and
whether the answer was usable.

**What you would see.**

| The ask | Typical response | Why |
|---|---|---|
| "Please review this page" | Slow, or never | It is an unbounded request |
| "Is this default still 30 seconds?" | Fast, and usable | Bounded, checkable, cheap to answer |
| "I documented this and it took four paragraphs; is the design right?" | Engaged | It arrives as an observation, not an opinion |
| A PR that fixes the code's docstring | Merged | You did the work |

The pattern is that an engineer's willingness tracks how specific the ask is,
not how important you say it is. The fourth row is the strongest move available
and the one documentation people use least.

**Why it does not commit.** The artifact is a merged pull request in a
repository you do not own and a response time in someone's review queue. What a
repository of your own can show is the habit's residue: checks that encode a
question an engineer answered once, so nobody has to ask again.

## Related

- [Reading code to verify accuracy](reading-code-to-verify.md), what makes the ask cheap
- [Extracting tribal knowledge](sme-interviews.md), the one-off deep version
- [Release readiness](release-readiness.md), making documentation part of shipping
- [Freshness monitoring](freshness-monitoring.md), where claim checking scales to
