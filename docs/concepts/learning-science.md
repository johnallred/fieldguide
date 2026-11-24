---
title: Learning science for developer education
summary: What research says about how people learn, reduced to the handful of results that change how a tutorial, lab or learning path is built.
diataxis: explanation
audience: developer
concept: learning-science
tags: [edu, core]
---

# Learning science for developer education

`core` · difficulty 2 · 6h

> Applying what research says about how people learn to every tutorial, lab and learning path you design.

**Leads to:** [Instructional design for developers](instructional-design.md), [Learner and task analysis](learner-task-analysis.md)

## What it is

The research on how people acquire skills, reduced to the few results that
change how you build a [tutorial](tutorial-design.md). Most of it fits in five ideas: start from a
whole task, show before asking, fade the support, align what you teach with
what you check, and make the reader retrieve rather than reread.

It is the theory under [instructional design](instructional-design.md). That
page turns learning into structural commitments a script can check; this page
is where those commitments come from, and what to do when two of them disagree.

## How this applies to your role

This matters because every tutorial you review is a set of claims about how people learn,
and without the research those claims get settled by taste.

On a Tuesday it looks like this. An engineer hands you a tutorial: three
paragraphs explaining how retries work, a paragraph on choosing a value, and
one exercise at the end. It is accurate. It also teaches in the order the
engineer understands the system rather than the order a newcomer can absorb
it, never says what the reader is building, gives them nothing to practice
until the end, and never checks whether they could diagnose the failure the
feature exists to handle. You can say "this does not work for learners", and
the engineer can say "it reads fine to me", and both are true.

Learning science is what turns that disagreement into something checkable.
"The objective about diagnosing an exhausted retry budget is never demonstrated,
practiced or checked" is not a style preference. Nor is "the first practice is
an unsupported problem, and novices learn more from a worked example first."
Each of those has decades of research behind it, and each changes the page.

The second reason is that developers are an unusual audience. Many of them
already know most of what a tutorial teaches, and some of the strongest
techniques for novices actively hurt experienced readers. Knowing that effect
by name is what stops a well-meant redesign from slowing down half your
audience.

## The golden path

Audit a tutorial against three principles, redesign it, audit it again, then
find out what the improved score cannot tell you. About thirty-five minutes.

The audit is committed as `drills/alignment_audit.py`, which also holds both
tutorials below, so a test keeps this page and the drill in step. The tutorials
mark their own structure in HTML comments: which of Merrill's phases each
section serves, which objective it serves, and what kind of practice it is.
Readers never see the comments; the script reads them.

**Step 1: a tutorial that is accurate and teaches badly**

```bash
mkdir -p ls-drill && cd ls-drill
cat > before.md <<'MDEOF'
---
objectives:
  O1: Configure retries on the client
  O2: Choose a retry count for a workload
  O3: Diagnose a retry budget that is exhausted
---
# Retries in the widget client

<!-- phase: demonstration; serves: O1 -->
## How retries work
The client retries failed requests with exponential backoff. Retries are
controlled by the `retries` argument, which counts retries rather than
attempts, so `retries=3` makes up to four requests. Backoff doubles from
200 ms. The maximum is 10. Historically the client did not retry at all.

<!-- phase: demonstration; serves: O2 -->
## Choosing a value
Callers waiting on a response want 1 or 2. Background jobs can use 3 to 5.
Upstreams that restart often justify up to 10, at the cost of blocking.

<!-- phase: application; serves: O1; practice: independent -->
## Exercise
Configure a client that survives a restarting upstream.
MDEOF
curl -sO https://raw.githubusercontent.com/johnallred/fieldguide/main/drills/alignment_audit.py
```

**Step 2: audit it**

```bash
python3 alignment_audit.py before.md
```

```
== before.md
phase words:  task 0  activation 0  demonstration 82  application 10  integration 0
total words: 92
task shown before demonstration: no
objective                                     demo  practice  check
  O1 Configure retries on the client           yes   yes   no
  O2 Choose a retry count for a workload       yes   no    no
  O3 Diagnose a retry budget that is exhausted no    no    no
aligned objectives: 0/3
practice sequence: independent
faded from worked to independent: no
```

Three findings, each a principle the page violates. The task never appears,
so nothing is problem-centred. No objective is demonstrated, practiced and
checked, so nothing is aligned, and the third objective is not taught at all
even though it is the reason retries exist. The only practice is an
unsupported problem, with no worked example before it.

**Step 3: redesign it, one principle per change**

```bash
cat > after.md <<'MDEOF'
---
objectives:
  O1: Configure retries on the client
  O2: Choose a retry count for a workload
  O3: Diagnose a retry budget that is exhausted
---
# Retries in the widget client

<!-- phase: task -->
## What you will build
A sync job that keeps running while its upstream restarts, and a log line
that tells you when it gave up and why.

<!-- phase: activation -->
## What you already know
You have seen a request fail and succeed when you ran it again by hand.
Retries are that, done by the client, with a pause that grows each time.

<!-- phase: demonstration; serves: O1; practice: worked -->
## Worked example: a client that retries
    client = WidgetClient(retries=3)   # up to 4 requests
    client.sync()                      # logs: retry 1/3 after 200 ms
`retries` counts retries, not attempts. Backoff doubles from 200 ms.

<!-- phase: demonstration; serves: O2 -->
## Choosing a value
Callers waiting on a response want 1 or 2. Background jobs can use 3 to 5.
Upstreams that restart often justify up to 10, at the cost of blocking.

<!-- phase: application; serves: O1, O2; practice: completion -->
## Your turn, with the start done
    client = WidgetClient(retries=____)   # a nightly background job
Fill the blank and run it. You should see `synced` after at most 3 retries.

<!-- phase: demonstration; serves: O3 -->
## When the budget runs out
The client logs `gave up after 3 retries: 503` and raises `RetryExhausted`.
The status code tells you whether the upstream was down or rejecting you.

<!-- phase: application; serves: O3; practice: independent -->
## On your own
Point the job at the flaky test upstream and read why it gave up.

<!-- phase: integration; serves: O1, O2, O3; check: O1, O2, O3 -->
## Check yourself, then change it
Without scrolling up: what does `retries=3` cost in requests, which value
would you pick for an interactive call, and what does `RetryExhausted: 429`
tell you? Then choose a value for a job in your own codebase.
MDEOF
```

| Change | Principle |
|---|---|
| "What you will build" comes first | Problem-centred: show the whole task before its parts |
| "What you already know" | Activation: connect to experience the reader has |
| A complete worked example before any exercise | Worked-example effect |
| A blank to fill, then an unsupported problem | Fading from worked example to independent practice |
| A section that teaches diagnosis | Alignment: every objective is taught |
| Questions answered "without scrolling up" | Retrieval practice, which also checks every objective |

**Step 4: audit the redesign**

```bash
python3 alignment_audit.py after.md
```

```
== after.md
phase words:  task 28  activation 34  demonstration 97  application 48  integration 42
total words: 249
task shown before demonstration: yes
objective                                     demo  practice  check
  O1 Configure retries on the client           yes   yes   yes
  O2 Choose a retry count for a workload       yes   yes   yes
  O3 Diagnose a retry budget that is exhausted yes   yes   yes
aligned objectives: 3/3
practice sequence: worked -> completion -> independent
faded from worked to independent: yes
```

Every objective is demonstrated, practiced and checked, the task leads, and
practice fades from worked to independent.

**Step 5: read what the score cannot see**

Two things, and both matter more than the score.

The redesign is 249 words against 92. For a reader who has never configured
retries that is the right trade. For a reader who has configured retries in
three other clients, it is 157 extra words of help they do not need, and the
research says the extra support can make experts learn *less*, not just more
slowly. That is the **expertise reversal effect**, and it argues for one more
change the audit cannot score: a line at the top that sends experienced
readers straight to "When the budget runs out".

And 3/3 is a fact about the page, not about any reader. Nothing in this
drill observed a person learning. It confirms the tutorial is *built* to teach
each objective; whether it does is a question for
[assessment](assessment.md) and [time to first success](time-to-first-success.md),
measured on people.

**What you built.** A tutorial redesigned against the principles in the table, an audit
that proves the structure changed, and a clear statement of the two things the
audit cannot measure: expertise reversal and learning itself.

## Reference

### The research results that change a tutorial

| Result | What the research found | What it changes |
|---|---|---|
| First principles of instruction | Learning is promoted when learners work on whole tasks, existing knowledge is activated, new knowledge is demonstrated, then applied with feedback, then integrated | Lead with the task; demonstrate before asking; end by applying it to the reader's own work |
| Constructive alignment | Outcomes are stated before teaching, and teaching and assessment are designed to serve them | Every objective needs a demonstration, a practice and a check |
| Worked examples and fading | Removing worked steps gradually, from a complete example to a full problem, improved near transfer over example-then-problem pairs | Worked example, then a blank to fill, then an unsupported problem |
| Expertise reversal | Techniques that help novices can lose their effect, or harm learning, for more experienced learners | Give experienced readers a route past the scaffolding |
| Testing effect | Tested students retained more after two days and a week than students who restudied, while restudying made them more confident | End with questions answered from memory, not a summary to reread |
| Multimedia principles | Cut [extraneous](cognitive-load.md) material, signal structure, keep words beside the thing they describe, segment, pre-train vocabulary | Fewer asides, headings that say what is below, code next to its explanation |

### What the research does not settle

| Caveat | Why it matters |
|---|---|
| Most studies used students in classrooms | Developers learning a tool at work differ in motivation, prior knowledge and time |
| Far transfer is weaker than near transfer | Fading helped near transfer reliably; its far-transfer results were inconsistent |
| Effects depend on the learner | Expertise reversal means no technique is right for every reader |
| A design check is not a learning measure | A page can satisfy every principle and still fail a reader |

### Evaluation levels, and the documentation version of each

The Kirkpatrick model names four levels of training outcome: reaction,
learning, behavior and results.

| Level | Classic measure | Documentation equivalent |
|---|---|---|
| Reaction | Satisfaction survey | Page feedback, "was this helpful" |
| Learning | Test after training | A retrieval check, a [cold-start run](coldstart-testing.md) |
| Behavior | Changed practice on the job | The reader uses the feature correctly in their own code |
| Results | Business outcome | [Support deflection](support-deflection.md), [time to first success](time-to-first-success.md) |

The testing effect is a warning about the first row: readers who reread feel
more confident and remember less, so reaction is the level most likely to
mislead you.

### Sources

Opened and checked on 2026-11-23:

- Merrill, M. D. (2002). First principles of instruction. *Educational Technology Research and Development*, 50(3), 43–59. Principles as summarized by [MIT Open Learning](https://openlearning.mit.edu/first-principles-instruction).
- Biggs, J. Constructive alignment in university teaching. *HERDSA Review of Higher Education*, 1. [PDF](https://www.tru.ca/__shared/assets/herdsa33493.pdf).
- Renkl, A., Atkinson, R. K., Maier, U. H., & Staley, R. (2002). From example study to problem solving: Smooth transitions help learning. *The Journal of Experimental Education*, 70(4), 293–315.
- Kalyuga, S., Ayres, P., Chandler, P., & Sweller, J. (2003). The expertise reversal effect. *Educational Psychologist*, 38(1), 23–31. [Record](https://ro.uow.edu.au/edupapers/136).
- Roediger, H. L., & Karpicke, J. D. (2006). Test-enhanced learning. *Psychological Science*, 17(3), 249–255. [PubMed](https://pubmed.ncbi.nlm.nih.gov/16507066/).
- Mayer, R. E. *Multimedia Learning* (3rd ed.). Cambridge University Press. [Contents](https://assets.cambridge.org/97811071/87504/toc/9781107187504_toc.pdf).
- Kirkpatrick four-level evaluation model, in *Encyclopedia of Evaluation* (SAGE). [Entry](https://sk.sagepub.com/ency/edvol/embed/evaluation/chpt/kirkpatrick-fourlevel-evaluation-model).

## Explaining it to your team

**How to explain it.** Lead with a finding, not a framework. "Novices learn
more from a worked example than from an unsupported exercise, so the first
thing a reader does should be follow a complete example, then fill a blank,
then solve one alone. And every objective at the top of a tutorial needs a
demonstration, a practice and a check, or it is a promise the page does not
keep." Two sentences, both checkable, neither a matter of taste.

**The follow-up is usually "this makes tutorials longer".** It does, and the
answer is to say so and then say who pays. The redesign above nearly triples
the length. Novices get a page they can learn from; experienced readers get
scaffolding they do not need, and the research says that can hurt them. So the
cost is real, and the fix is a route around it, not a shorter page for
everyone.

**The tradeoff to name.** The research is mostly from classrooms, with
students, on school subjects, and its effect sizes do not transfer to
developers learning a tool at work as cleanly as the citations suggest. Treat
the principles as strong defaults with a known direction, and measure your own
readers before you claim a result.

**One sharper point.** The testing effect is the one to raise in a review,
because it inverts a metric the team already trusts. Readers who reread feel
more confident and remember less, so a page that ends with a summary scores
well on "was this helpful" and teaches worse than a page that ends with three
questions. Satisfaction is evidence about the reader's mood, not their memory.

## Putting it into practice

**The work product.** A real tutorial from your corpus, marked up with phases,
objectives and practice types, audited before and after a redesign, with an
expert route added and a retrieval check at the end.

**Three things to do, in order:**

1. Run the golden path, then mark up one real tutorial you maintain and audit
   it. Expect at least one objective that is promised and never practiced.
2. Replace the closing summary of one tutorial with three questions answered
   from memory. Record how often readers get them right.
3. Add a one-line route for experienced readers to the tutorial with the most
   scaffolding. Check its [analytics](docs-analytics.md) a month later to see how many take it.

**How to tell it is working.** The drill above runs in this guide's test suite
and its output is the output quoted here, so the structural half is
demonstrated. The learning half is not: no reader has been observed, so nothing
here shows a redesigned tutorial teaches better, and the
[demonstrated](../demonstrated.md) page records the concept as partial on that
basis. In your own corpus, the sign is a delayed retrieval check that more
readers pass after a redesign than before.

## Related

- [Instructional design for developers](instructional-design.md), the structural commitments this theory produces
- [Cognitive load in technical content](cognitive-load.md), the working-memory side of the same research
- [Assessment and checks for understanding](assessment.md), how to find out whether the design worked
- [Designing tutorials](tutorial-design.md), where worked examples and fading are applied
- [Learning paths and curriculum](learning-paths.md), alignment at the scale of a whole path
- [Learner and task analysis](learner-task-analysis.md), where the objectives in the drill come from
