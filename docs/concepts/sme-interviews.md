---
title: Extracting tribal knowledge
summary: Getting what an expert knows out of their head and into something other people can use without them.
diataxis: explanation
audience: developer
concept: sme-interviews
tags: [craft, core]
---

# Extracting tribal knowledge

`core` · difficulty 2 · 3h

> Turning documentation, standards, and tribal knowledge into tooling, templates, and self-service paths

> Source: nvidia posting, verbatim

**Leads to:** [Playbooks and decision guides](playbooks.md), [Working with engineers as sources](working-with-engineers.md)

## What it is

Getting what an expert knows out of their head and into a form other people can
use without them. Tribal knowledge is the subset of what a team knows that has
never been written down, usually because the people who have it do not
experience it as knowledge. It feels like common sense.

The work is an interview technique plus a judgement about what shape the result
should take, and the second part is where most of the value is.

## Why the job asks for it

NVIDIA names it twice. Once in the framing: "turning documentation, standards,
and tribal knowledge into tooling, templates, and self-service paths, so fewer
people have to ask how do I". Once as a responsibility: "Capture tribal
knowledge from engineering, product, and operations, and turn it into playbooks,
decision guides, and self-service paths".

Notice what the sentences have in common. Neither says "write it down". Both
specify an *output form*, and none of the forms is a page. That is the distinctive thing about this role, and the thing most technical
writers get wrong. The deliverable for tribal knowledge is often a template, a
validator, or a decision tree. The knowledge in question is usually a
judgement rather than a fact, and a page describing a judgement gets read once
and forgotten.

On a Tuesday it looks like this. A staff engineer is the only person who knows
which of four ways to configure a simulation is right for a given workload.
Three teams ask her every quarter. The naive output is a page titled
"Configuration options", which already exists and which nobody uses because it
lists the options without ranking them. The useful output is a decision guide:
four questions in order, each narrowing the choice, ending in one answer and the
reason. That is the same knowledge and a different artifact, and only one of
them stops the questions.

The second reason this matters: the knowledge is **the thing the role is
protecting against**. A platform whose operational knowledge lives in four
people's heads is one reorganisation away from losing it.

## The golden path

Run one extraction, on a real person, and produce something that is not a page.
Forty-five minutes including the conversation.

**Step 1: find the question, not the topic**

Topics produce overviews. Questions produce usable artifacts.

```bash
mkdir -p tribal-drill && cd tribal-drill
cat > scope.md <<'EOF'
BAD SCOPE      "Tell me about our deployment process."
               Produces a 2,000-word overview nobody reads.

GOOD SCOPE     "What do you get asked about deployment that you wish
               people could answer themselves?"
               Produces the three things that actually recur.

THE PIVOT      Do not ask what they know. Ask what they get interrupted
               about. Interruptions are the measurable shadow of tribal
               knowledge, and the expert can list them instantly.
EOF
cat scope.md
```

**Step 2: run the interview with the five questions**

```bash
cat > interview.md <<'EOF'
# Extraction interview, 30 minutes

1. WHAT RECURS
   "What do people ask you more than once a month?"
   -> the list. Pick one. Do not try to cover all of it.

2. THE DECISION
   "When someone asks that, what do you need to know before you can
   answer?"
   -> these become the questions in the decision guide, in this order.

3. THE WRONG ANSWER
   "What do people do when they guess? What goes wrong?"
   -> the failure modes. This is the half that never gets written down
   and the half that makes the artifact trustworthy.

4. THE EXCEPTION
   "When is the usual answer wrong?"
   -> the thing that will make your first draft embarrassing if you
   skip it. Always ask it.

5. THE TELL
   "How do you know, looking at a request, which case it is?"
   -> the signal. Often something they have never articulated, and
   usually the single most valuable sentence in the interview.
EOF
cat interview.md
```

**Step 3: write down what you heard, in their words, before you shape it**

Do this before designing the artifact. Shaping while listening loses the
exceptions.

```bash
cat > raw.md <<'EOF'
# Raw notes: batch size for inference workloads  (SME: A. Patel, 30 min)

RECURS      "Which batch size should I use" -- several times a month,
            from three teams.

DECISION    Needs to know: is latency user-facing? how much GPU memory?
            is the model quantised? is the traffic bursty?

WRONG       People copy the number from the tutorial (32). On a latency-
            sensitive endpoint that adds ~200ms p99. On a small GPU it
            OOMs at load, not at startup, so it passes smoke tests.

EXCEPTION   Quantised models tolerate much larger batches; the memory
            math is different and the tutorial number is far too low.

TELL        "If they mention a p99 target, it is latency-sensitive and
            the answer is almost always 1 or 2, whatever the memory
            allows."
EOF
cat raw.md
```

**Step 4: choose the output form, then build it**

```bash
cat > choose.md <<'EOF'
Is the knowledge...        Then the artifact is...
-------------------------  ------------------------------------------
a fact                     a reference entry
a procedure                a how-to guide
a JUDGEMENT between        a DECISION GUIDE
  known options
a judgement that can be    a VALIDATOR or a default in the tooling
  computed from inputs
a sequence under pressure   a PLAYBOOK
a convention people        a TEMPLATE
  keep getting wrong
EOF
cat choose.md
```

This one is a judgement between known options, so it is a decision guide.

```bash
cat > decision-guide.md <<'EOF'
---
title: Choosing a batch size
summary: Four questions that determine the batch size for an inference workload.
diataxis: how-to
audience: developer
source: A. Patel, platform team, 2026-10
---

# Choosing a batch size

Do not copy the number from the tutorial. The tutorial uses 32 because it is
convenient for a demo, and it is wrong for most production workloads.

## 1. Is anything waiting on the response?

If a user or a caller is waiting, you are latency-sensitive. **Use 1 or 2.**

The tell: if you have a p99 target, the answer is almost always 1 or 2,
whatever memory allows. Batching at 32 on a latency-sensitive endpoint adds
roughly 200ms at p99.

If nothing is waiting, continue.

## 2. Is the model quantised?

If yes, the memory arithmetic is different and the tutorial's number is far
too low. Start at 64 and raise it while watching memory.

## 3. How much GPU memory do you have at peak, not at startup?

Size for peak. The common failure is an out-of-memory error under load rather
than at startup, which means it passes a smoke test and fails in production.

## 4. Is the traffic bursty?

Bursty traffic with a large batch size queues. Prefer a smaller batch and more
replicas.

## If you get this wrong

| Symptom | Likely cause |
|---|---|
| p99 latency far above p50 | Batch size too high for a latency-sensitive path |
| OOM under load, fine at startup | Sized for startup memory, not peak |
| Throughput lower than expected on a quantised model | Batch size too low |
EOF
wc -l decision-guide.md
```

**What you built.** A page that answers a recurring question in the order the
expert actually thinks about it, including the failure modes and the exception,
with the source and date recorded in the front matter.

The `source` field matters more than it looks. Tribal knowledge has a shelf
life, and a reader in two years needs to know who said this and when, so they
can go and ask whether it is still true. That one line is the difference between
a document and a captured claim.

## Reference

### The five questions, and what each one is for

| Question | Produces |
|---|---|
| What do people ask you more than once a month? | Scope, chosen by frequency rather than by topic |
| What do you need to know before you can answer? | The decision guide's questions, in order |
| What goes wrong when people guess? | Failure modes, which nobody writes down |
| When is the usual answer wrong? | The exception that saves your draft |
| How do you tell which case it is? | The signal, usually never articulated |

### Choosing the output form

| The knowledge is | The artifact is |
|---|---|
| A fact | A reference entry |
| A procedure | A how-to guide |
| A judgement between known options | A [decision guide](playbooks.md) |
| A judgement computable from inputs | A validator, or a better default in the tooling |
| A sequence executed under pressure | A [playbook](playbooks.md) |
| A convention people keep getting wrong | A [template](templates-scaffolding.md) |
| A number that drifts | A [freshness check](freshness-monitoring.md) on the page |

The fourth row is the one that distinguishes this role. If the judgement can be
computed, **the right output is code, not prose.** If the tutorial's batch size
is wrong for most workloads, the strongest fix is changing the default and
warning on the bad combination, and the page becomes an explanation of a safe
default rather than a warning about a dangerous one.

### Interview mechanics that matter

| Do | Why |
|---|---|
| 30 minutes, one question | An hour on a topic produces an overview |
| Record or take verbatim notes | Their phrasing is usually better than yours, especially the tell |
| Ask for the last time it happened | Concrete incidents surface exceptions; general questions do not |
| Write the draft, then have them correct it | Experts review well and compose badly |
| Send the draft within a day | Their context decays fast |
| Put their name and the date on it | Captured knowledge needs provenance |

### Failure modes

| Failure | What it looks like |
|---|---|
| Interviewing the topic | A 2,000-word overview that answers nothing specific |
| Capturing the answer, not the decision | "Use 16" with no account of when that is wrong |
| Skipping the exception | A guide that is confidently wrong for quantised models |
| Writing a page when the fix was a default | The questions keep coming because nobody reads the page |
| No provenance | In two years nobody knows whether it is still true |
| Interviewing one person | You have captured one person's opinion as doctrine |

## How to talk about it

**What a competent answer sounds like.** Name the output form and why you chose
it. "An engineer was being asked monthly which batch size to use. The page that
existed listed the options without ranking them, so I built a decision guide
with the four questions she actually asks, in order, plus the failure modes and
the quantised-model exception. Then I argued for changing the tutorial's default,
because the real problem was that the demo number was being copied into
production."

That last move is what separates this from note-taking.

**The follow-up is about experts who will not talk to you**, or who talk and
then never review the draft. The honest answer is that a thirty-minute meeting
about one recurring question is an easy ask and a one-hour meeting about a topic
is not, so scope is your main lever. Beyond that: write the draft wrong on
purpose and send it, because experts who will not compose will happily correct,
and a wrong draft generates a faster response than a request for information.

**The tradeoff to volunteer.** Extraction takes the expert's time, and the people
with the most tribal knowledge are the most interrupted people on the team. You
are asking for the scarcest resource in the building to reduce demand on itself,
which is a good trade and an unobvious one. The way to make it land is to lead
with the interruption count rather than with documentation: "you get asked this
three times a month, let me take thirty minutes and make it stop."

**One sharper point.** Tribal knowledge is tribal for a *reason*, and the reason
is usually that it is a judgement with exceptions, which is genuinely hard to
write down and easy to write down badly. A confidently wrong decision guide is
worse than no guide, because people follow it. This is why question four exists
and why provenance is non-negotiable. Saying that demonstrates you understand
why the knowledge was not already written down, which is a more sophisticated
position than assuming nobody got round to it.

## How to prove it

**The artifact.** A decision guide with a named source and a date, for a question
that genuinely recurred. Not an overview.

**Three things to do, in order:**

1. **Run one extraction on a real person.** Thirty minutes, one recurring
   question, the five questions above. Produce something that is not a page if
   the knowledge is not a fact.
2. **Count the interruptions before and after.** Ask the expert, a month later,
   whether the question stopped. That number is the whole argument, and it is
   what NVIDIA means by "measurable reductions in support load".
3. **Find one case where the answer was code.** A judgement that could be a
   default, a warning, or a validator. Propose it. Being the documentation person
   who argues for changing a default rather than documenting it is memorable.

**What makes it credible rather than decorative.** Everyone in this field says they interview subject
matter experts. A decision guide with four ordered questions, an exception, a
failure table and a named source is specific enough to be checked, and "she
stopped getting asked" is the only outcome that matters.

### How this would be demonstrated elsewhere

The artifact this produces is a page, and a page does not reveal how it was
obtained. What would demonstrate the skill is the gap between what an expert
said and what they knew, which only exists in the room.

**What you need.** An engineer who knows something undocumented, thirty
minutes, and a prepared set of questions. No tooling. The scarce resource is the
engineer's attention, which is why the preparation is the skill.

**What a learner would do.** Pick something in your own product that is
undocumented because it is "obvious", and interview whoever knows it, using
questions that cannot be answered abstractly:

```
What breaks most often, and what does the person do first?
Walk me through the last time this went wrong.
What do you know that is not written down anywhere?
What does everyone get wrong when they first use this?
If I changed this, what would you be worried about?
```

Then write the page, send it back, and count the corrections. The count is the
measurement: a first draft from a good interview comes back with factual
corrections, and one from a bad interview comes back rewritten.

**What competence looks like.**

| Evidence | Why it carries weight |
|---|---|
| A page the expert approved with few edits | The interview captured the right things |
| A documented failure mode nobody had written | You got tacit knowledge, not a restatement |
| A second interview that was shorter | You learned what to ask |
| An expert who volunteers things afterwards | The hardest signal to fake |
| A question you stopped asking, and why | The questions improve or they are a script |

**Why it does not commit to a repository.** The page commits; the interview does
not. A reader cannot tell whether a well-documented failure mode came from an
engineer, from reading the source, or from a support ticket, and those represent
very different skills. The one piece of evidence that would distinguish them,
the correction count on the first draft, lives in a review thread.

**The adjacent thing that is demonstrable.** Reading the source to verify what
you were told is a separate concept, [reading code to
verify](reading-code-to-verify.md), and the combination is what makes either
trustworthy: an interview tells you where to look, and the code tells you
whether the memory was right.

## Related

- [Playbooks and decision guides](playbooks.md), the output forms
- [Working with engineers as sources](working-with-engineers.md), the ongoing relationship
- [Repeat-question analysis](repeat-questions.md), finding what to extract without asking
- [Templates and scaffolding](templates-scaffolding.md), when the answer is a template
