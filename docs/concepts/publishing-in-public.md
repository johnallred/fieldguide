---
title: Publishing in public
summary: "Published work is the only evidence of this skillset a stranger can check without taking your word, and the most persuasive page in a repository is the one listing what it does not demonstrate."
diataxis: how-to
audience: developer
concept: publishing-in-public
tags: [edu, supporting]
---

# Publishing in public

`supporting` · difficulty 1 · 4h

!!! quote "Asked for by name"
    NVIDIA: "Open source contributions or published work on docs-as-code, AI-assisted documentation, or knowledge engineering"

## What it is

Putting work where a stranger can run it. The phrase in the posting is a
qualification requirement, and it is unusual among qualification requirements
in being verifiable: a reader can clone the thing and find out.

That property is the entire point, and it sets a bar that most published
portfolios do not clear. A repository that cannot be run is a claim. A
repository a stranger clones, installs and tests in five minutes is evidence.

## Why the job asks for it

Because nothing else in a hiring process can distinguish someone who has built
a documentation pipeline from someone who has read about one.

Every other signal is self-reported. A résumé asserts, an interview answer
describes, a reference agrees. Published work is the only artifact where the
assessment is performed by the reader rather than conveyed to them, which is
why NVIDIA lists it beside formal qualifications rather than under interests.

There is a second reason, specific to this field. Documentation work is mostly
invisible in its outcomes: when it succeeds, nothing happens, support volume
quietly fails to rise, and the credit accrues to the product. A public
repository is the one place the work itself is the object, rather than its
absent consequences.

## The golden path

Audit a repository for publication, discover the audit is mostly noise, and
fix the audit rather than the repository. About twenty-five minutes. This runs
against the two repositories behind this guide, which have not been published
yet, so every finding is real.

**Step 1: the obvious checks**

```python
PLACEHOLDERS = {
    "example-org URL":   re.compile(r"github\.com/example/"),
    "example.com":       re.compile(r"\bexample\.com\b"),
    "TODO or FIXME":     re.compile(r"\b(TODO|FIXME|XXX)\b"),
    "angle placeholder": re.compile(r"<your[- ]"),
    "unfilled year":     re.compile(r"Copyright \[|\[year\]|\[fullname\]"),
    "container path":    re.compile(r"/mnt/user-data|/home/claude|/tmp/claude"),
}
```

```
=== fieldguide            (142 files)
  example-org URL      9 hits in 4 files
  example.com          6 hits in 3 files
  TODO or FIXME        7 hits in 4 files
  angle placeholder  clean
  unfilled year      clean
  container path     clean

=== docpack               (42 files)
  example-org URL      1 hit
  example.com          2 hits
  TODO or FIXME        7 hits in 5 files
```

Twenty-two hits. The two useful results are the clean rows: no unfilled licence
fields, and no container paths, the second being the one that would have been
genuinely embarrassing.

**Step 2: read the hits, and find that four of twenty-two are real**

```
src/fieldguide/scaffold.py:101   summary: 'TODO: one sentence on ...'
docs/explanation/why-a-registry.md:23   "three paragraphs of `TODO`"
tests/test_scaffold.py:101       assert "TODO" in meta.summary
docs/concepts/crawlability.md    curl -s https://example.com/docs/page/
```

The TODO hits are a scaffold that deliberately *writes* TODO placeholders,
prose *about* TODO markers, and tests asserting the placeholder exists. The
`example.com` hits are a domain reserved by RFC 2606 for exactly this purpose,
so a sample command using it is correct and one using a real domain would not
be.

```
22 hits, 4 real: 82% noise
```

An audit whose output is 82 per cent noise is an audit nobody runs twice,
which is the same failure as a badly aimed [documentation
gate](developer-advocacy.md) and for the same reason.

**Step 3: the obvious fix makes it worse**

Add an allowlist of the files where a hit is legitimate:

```
not ready to publish, 9 finding(s):
  docs/concepts/mkdocs.md:63             site_url: https://example.github.io/widget/
  docs/concepts/preview-deployments.md:55   site_url: https://example.github.io/widget/
  docs/concepts/preview-deployments.md:91   sed -i 's|site_url:.*|...pr-123/|'
  ... four more in the same page ...
  mkdocs.yml:6                           site_url: https://example.github.io/fieldguide/
  mkdocs.yml:7                           repo_url: https://github.com/example/fieldguide
```

Seven new false hits. The golden paths on those pages legitimately show
`site_url:` lines for a fictional `widget` project, and an allowlist cannot
anticipate that, because the next page to do the same thing is not in the list
yet.

**Step 4: scope by file role instead**

A placeholder URL is a defect when it is **this repository's own published
identity**, and illustration everywhere else. So read only the files that carry
that identity:

```python
OWN_CONFIG = ("mkdocs.yml", "pyproject.toml", "setup.cfg", "README.md", "LICENSE")
```

```
examined 143 files under fieldguide

not ready to publish, 2 finding(s):
  mkdocs.yml:6  placeholder URL in this repository's own identity
      site_url: https://example.github.io/fieldguide/
  mkdocs.yml:7  placeholder URL in this repository's own identity
      repo_url: https://github.com/example/fieldguide
exit=1
```

Two findings, both real: a published site whose canonical URL and whose "edit
this page" links point at an organisation that does not exist.

**Step 5: the transfer test, which settles the argument**

Run the same script, unchanged, against the other repository:

```
examined 42 files under docpack

not ready to publish, 9 finding(s):
  src/docpack/scaffold.py:255   summary = summary or f"TODO: one sentence ..."
  tests/test_scaffold.py:94     assert "TODO" not in text
  ... five more TODO hits ...
  mkdocs.yml:3                  placeholder URL in this repository's own identity
  mkdocs.yml:4                  placeholder URL in this repository's own identity
```

The role-scoped check travelled perfectly: two findings, both real, on a
repository it had never seen. The allowlist-scoped check did not travel at all,
producing seven false hits immediately, because the allowlist named
`fieldguide`'s paths.

That is the general lesson and it is not about publishing. **A check scoped by
what a file is for transfers; a check scoped by a list of exceptions is a
record of one repository's history.** The same distinction decided the
documentation gate on the [developer advocacy](developer-advocacy.md) page,
found independently, from the other direction.

**Step 6: the gate flags the page describing the gate**

Writing this page and re-running the script produced twelve findings, eleven of
them in this file: it quotes TODO markers while explaining them, and it quotes
the container-path pattern itself.

The pattern-definition case has a role-based answer, since a line that defines
a pattern is not a line leaking what the pattern matches, and one condition
fixes it everywhere. The TODO case does not. **TODO is simultaneously a marker
and a word**, so no property of a file distinguishes the scaffold that writes
placeholders, the tests asserting on them, and the four pages discussing them
from genuine unfinished work. The allowlist had reached four files and acquired
eleven new false hits the moment another page mentioned the subject.

So the check was deleted, with the reasoning left in the source:

```python
# A TODO check used to live here and has been removed, which is the most
# useful thing this script has to say.
#
# It cannot be scoped by role, because TODO is simultaneously a marker and
# a word. ... A TODO marker is better caught on the diff, by review, where
# the question "is this line new unfinished work" is answerable.
```

Deleting a check is an unpopular outcome and it was the right one. The three
that remain ask about a file's role rather than its vocabulary, and the proof
is the same script run on both repositories with nothing changed between them:

```
examined 143 files under fieldguide        examined 42 files under docpack
not ready to publish, 2 finding(s):        not ready to publish, 2 finding(s):
  mkdocs.yml:6  placeholder URL ...          mkdocs.yml:3  placeholder URL ...
  mkdocs.yml:7  placeholder URL ...          mkdocs.yml:4  placeholder URL ...
exit=1                                     exit=1
```

Two findings each, both real, zero noise, across a 143-file repository and a
42-file one. Those are the figures from the run that settled the argument, when
the URLs were still placeholders and both repositories were smaller; step 8 has
the current state.

**Step 7: what is left, and why it stays**

The two findings cannot be fixed here, because nobody knows the real URL until
the repository has a home. That is the correct outcome for a pre-publication
gate: it converts "remember to change the URL" into a command that exits 1, and
it is deliberately **not** in CI, because a check that fails every build until
publication day is a check people learn to ignore.

**Step 8: the findings close, and the roster was incomplete**

The repositories have a home, so the four placeholders are real URLs now and
both checks pass:

```
examined 173 files under fieldguide        examined 60 files under docpack
ready to publish                           ready to publish
exit=0                                     exit=0
```

Closing them found something, and it is the more interesting half of this
page's argument rather than a footnote to it.

**The script said "ready to publish" while two placeholder repository links sat
on a published page.** `demonstrations.yaml` carries each repository's own URL
in its `projects` block, the generated [demonstrated](../demonstrated.md) page
prints both as links, and that file was not in `OWN_CONFIG`. So the gate cleared
a repository whose own index pointed twice at an organisation that does not
exist.

Note the shape of that failure against the shape of the allowlist's. The
allowlist was wrong in principle: it scoped by a list of exceptions, so it could
not travel and could not anticipate the next page. Role-scoping is right in
principle and was wrong in fact, because **the roster of files that carry the
role was incomplete**, and nothing in the idea of role-scoping tells you when
you have finished enumerating the role. That is a quieter failure and an easier
one to make twice: the check looked principled, transferred perfectly to another
repository, and still missed two live defects.

So the sharpened lesson is narrower than step 5's. A check scoped by what a file
is for transfers, and it is only as complete as your list of what carries that
purpose, which is a judgement the scoping cannot make for you. The roster is
now six files, and the reason `demonstrations.yaml` is on it is written beside
it, because the next person to add a file that publishes an identity will not
think to look here.

**What you built.** A pre-publication gate at full precision on two
repositories, six revisions of it, one check deleted for being unscopeable, a
demonstrated transfer test, four findings held open until they could honestly be
closed, and then a seventh revision because closing them showed the gate had
been passing a repository it should have failed.

## Reference

### What a stranger checks in ninety seconds

| They look at | They conclude |
|---|---|
| Does the README say what this is, in one line | Whether to continue |
| Can I install and run it from the README alone | Whether it is real |
| Is there a test suite, and does it pass | Whether it is maintained |
| Is the CI badge green, or absent | Same, faster |
| Does the commit history look like work or like a dump | Whether it was built or assembled |
| Does it say what it does not do | Whether to trust the rest |

The last row is the one people leave out and the one that does the most work,
which is the subject of the next table.

### Honest limits as a feature

This guide publishes a [demonstrated](../demonstrated.md) page listing every
concept for which neither repository contains a working example. It is, on the
face of it, a page about what is missing.

| Without it | With it |
|---|---|
| Every claim is equally weighted | The reader knows which claims are evidenced |
| A reader who finds a gap finds a lie | A reader who finds a gap finds it already named |
| Trust collapses at the first gap | Trust survives, because the gaps are the author's own list |

A repository that states its limits is making a verifiable claim about its
author's judgment, and that is a stronger signal than any of the work itself.
It is also the cheapest page to write and the hardest to write honestly.

### What counts as published work

| Form | Evidence of | Effort |
|---|---|---|
| A runnable repository | Ability, maintenance, judgment | High |
| An upstream contribution that was merged | Ability to work in someone else's codebase | Medium, and gated by review |
| A written account of a real problem | Judgment, and that you can explain | Low to medium |
| A published site built by the thing | That the thing works | Low, once the repo exists |
| A talk recording | Communication | Medium |
| A list of technologies | Nothing | Low |

An upstream merge is the strongest single signal per unit of effort, because
somebody else's maintainer agreed. A repository of your own is the strongest
overall, because it shows the parts review never sees: what you chose to check,
what you chose to leave out, and whether you wrote down the limits.

### The README contract

| Section | Answers |
|---|---|
| One line at the top | What is this |
| Quick start, copy-pasteable | Can I run it |
| What it is for, honestly scoped | Should I |
| How it is organised | Where do I look |
| What it does not do | Can I trust the rest |
| Licence | May I |

Every claim in the quick start is a claim a stranger will test within two
minutes, which makes it the highest-risk prose in the repository. This guide's
README asserted 72 tests when there were 119, uncaught for the project's whole
life, until the [capability gate](developer-advocacy.md) read it.

### Before publishing anything

| Check | Why it bites |
|---|---|
| No container or local paths | Reveals the machine, breaks every copy-paste |
| Licence has a real name and year | A repository without one is unusable, politely |
| Own `repo_url` and `site_url` are real | Edit links and canonical URLs point at nothing |
| The README's commands exist | The first thing anyone runs |
| The README's numbers are current | They go stale silently |
| No credentials, in any file or any commit | History is public too |
| A clean clone passes its own tests | [Cold-start testing](coldstart-testing.md), applied to yourself |

## How to talk about it

**Lead with verifiability.** "Published work is the only part of an application
where the assessment is done by the reader instead of conveyed to them. A
repository that cannot be run is a claim; one a stranger clones and tests in
five minutes is evidence, and that is a much higher bar than a portfolio
usually clears."

**The follow-up is what you would check before publishing, and the useful
answer is about the checker.** My first pre-publication audit produced
twenty-two hits across two repositories, four of them real: the rest were a
scaffold that deliberately writes TODO placeholders, prose about TODO markers,
and `example.com`, which RFC 2606 reserves for exactly that use. Eighty-two per
cent noise, and an audit that noisy is one nobody runs twice.

**The part worth telling in full.** The fix that looked obvious, an allowlist
of files where a hit is fine, made it worse: seven new false hits, because
golden paths legitimately show `site_url:` lines for a fictional project.
Scoping by file role instead, a placeholder URL is a defect only in the
repository's own identity files, took it to two findings, both real. Then I ran
it unchanged against the second repository: the role-scoped check transferred
perfectly, the allowlist-scoped one produced seven false hits on first contact.
A check scoped by what a file is for travels; a check scoped by exceptions is a
record of one repository's history.

**And the ending, which is the part I would volunteer.** Writing the page about
the script made the script fail on the page, eleven times, because the page
quotes the markers it explains. One of those had a role-based fix. The TODO
check did not, because TODO is simultaneously a marker and a word, so no
property of a file separates deliberate placeholders from unfinished work. I
deleted the check and left the reasoning in the source. Three checks remain and
they produce two findings on a 143-file repository and two on a 42-file one,
both real, with nothing changed between the runs.

**The counterintuitive point, and the best thing to say here.** The most
persuasive page in a published repository is the one listing what it does not
demonstrate. Mine names every concept with no working example in either
codebase. Without that page a reader who finds a gap has found a lie and stops
trusting everything; with it, they find the gap already named by the author, and
the remaining claims get stronger rather than weaker. It is the cheapest page to
write and the hardest to write honestly.

**The tradeoff to volunteer.** Published work is expensive and its payoff is
unpredictable: the repository took far longer than the writing it supports, and
most readers will look at it for ninety seconds. If the goal were only to pass
a hiring filter, a smaller artifact with one genuinely working demonstration
would be the better investment. The reason to build the larger one is that the
act of making every claim checkable is what found the defects, and that part
was not optional.

## How to prove it

**The artifact.** A pre-publication script in your own repository, run against
a second repository to see whether its checks are about file roles or about
your history.

**Three things to do, in order:**

1. Grep your repository for your own machine's paths before anything else.
   Predict whether you will find any; this guide found none and that was the
   only genuinely reassuring result in the first run.
2. Write the page that says what your work does not demonstrate. If it is
   difficult to write, that difficulty is the information, and the page is worth
   more than the next feature.
3. Check every number in your README against reality. Mine claimed 72 tests
   against an actual 119, stale for the project's entire life, and nothing had
   ever looked.

**What makes it credible rather than decorative.** `scripts/prepublication.py`
is in this repository, runs on it and on `docpack`, and currently exits 1 with
two findings: the placeholder `site_url` and `repo_url` in `mkdocs.yml`, which
stay open until the repositories have real homes. Neither repository has been
published, so the claims above about what a stranger concludes in ninety
seconds are reasoning about readers rather than observation of them, and the
[demonstrated](../demonstrated.md) page records this concept as having the
gate but not the audience.

## Related

- [Developer advocacy](developer-advocacy.md), where the same scoping lesson appears from the other side
- [Cold-start testing](coldstart-testing.md), the check a stranger performs by accident
- [Documentation CI](documentation-ci.md), why this gate deliberately sits outside it
- [Reproducible environments](reproducible-environments.md), what makes a clone runnable
- [Screencasts and video](screencasts.md), the published form with the worst maintenance profile
