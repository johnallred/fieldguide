---
title: Git authoring workflows for writers
summary: How prose is wrapped decides whether diffs are readable and whether two writers conflict.
diataxis: how-to
audience: developer
concept: git-authoring
tags: [dac, core]
---

# Git authoring workflows for writers

`core` · difficulty 2 · 4h

!!! quote "Asked for by name"
    NVIDIA: "Hands-on docs-as-code experience: Git, pull request review, Markdown/RST, static site generators (Sphinx, MkDocs, Docusaurus, or similar), and CI/CD"

    Intel: "Hands on experience with docs-as-code workflows and documentation CI, including Git, Markdown or MDX, and doc build pipelines"

**Prerequisites:** [Docs-as-code](docs-as-code.md)

**Leads to:** [Reviewing documentation](docs-review.md)

## What it is

The practices that make Git work for prose rather than merely tolerate it.
Branch and review conventions, commit granularity, and, most consequentially,
**how you wrap lines**, because Git's unit is the line and a paragraph is not
one.

Both postings name Git. The thing worth knowing is not `git rebase`. It is that
a formatting decision almost nobody makes deliberately determines whether your
diffs are reviewable and whether two writers editing one page collide.

## Why the job asks for it

Because the objection to [docs-as-code](docs-as-code.md) is always the same:
that it does not work for people whose job is writing. Most of the time the
complaint is correct, and the cause is not Git. It is that the repository was
set up by engineers who hard-wrapped the prose at 80 columns, so every edit
produces a diff that looks like a rewrite and every concurrent edit produces a
conflict.

Fix the wrapping and most of the objection dissolves. That is a cheap,
high-leverage thing to know, and it is invisible until someone measures it.

## The golden path

Measure what line wrapping does to a diff and to a merge. About thirty
minutes, and the second result is the one to remember.

**Step 1: the same paragraph, wrapped two ways**

````bash
mkdir -p git-prose && cd git-prose
git init -q

python3 - <<'PY'
import textwrap
from pathlib import Path

para = ("The retry setting controls how many times the client attempts an "
        "operation before giving up. The default is five attempts. Each "
        "attempt waits longer than the last, multiplied by the backoff "
        "factor. Set it to one to disable retries entirely.")

Path("wrapped.md").write_text("# Retries\n\n" + textwrap.fill(para, 80) + "\n")

sentences = [s.strip() for s in para.split(". ") if s.strip()]
Path("perline.md").write_text(
    "# Retries\n\n" + "\n".join(s.rstrip(".") + "." for s in sentences) + "\n")
PY

git add -A && git commit -qm base
````

Identical content. One file wrapped at 80 columns, one with a line per
sentence.

**Step 2: insert a clause, and re-wrap as an editor would**

```bash
# the edit: a qualifying clause early in the paragraph
# wrapped.md is re-flowed to 80 columns afterwards; perline.md is not
git diff --numstat
```

```
  wrapped.md   +5   -4   lines
  perline.md   +1   -1   lines
```

One inserted clause. Nine changed lines in the hard-wrapped file, two in the
other. The re-wrap cascaded through every line of the paragraph, so a reviewer
sees the whole paragraph rewritten and has to find the actual change by reading.

The sentence-per-line diff shows exactly the sentence that changed.

**Step 3: the result that settles it**

Two writers, two branches, editing **different sentences** of the same
paragraph. One changes "The default is five attempts." and the other changes
"Set it to one to disable retries entirely."

```bash
git merge a-wrapped
```

```
Auto-merging wrapped.md
CONFLICT (content): Merge conflict in wrapped.md
Automatic merge failed
```

```bash
git merge a-perline
```

```
Auto-merging perline.md
  merged cleanly
```

**Hard-wrapped prose made two writers conflict over edits that did not
overlap.** With one sentence per line, Git resolved it without a human.

That is not a small ergonomic preference. On a page several people maintain, it
is the difference between a workflow that works and one that produces a
conflict every week and teaches writers that Git is hostile.

**Step 4: write the convention down**

```bash
cat > .gitattributes <<'EOF'
# Prose diffs: word-level, so a reviewer sees the changed words.
*.md diff=markdown
EOF

git config diff.markdown.wordRegex '[^[:space:]]'
git diff --word-diff=color -- perline.md | tail -3
```

`.gitattributes` is committed and applies to everyone; the `diff.markdown`
driver is local config, so document it in your contributing guide or ship it in
a setup script. Word diffs make even a re-wrapped paragraph legible, which is
the mitigation when you inherit a hard-wrapped corpus and cannot reflow it
today.

**What you built.** A measured reason to adopt one sentence per line, and a
fallback for corpora you cannot change.

## Reference

### Wrapping styles

| Style | Diff on a small edit | Concurrent edits | Authoring feel |
|---|---|---|---|
| Hard wrap at 80 | Whole paragraph | Conflicts, measured above | Familiar to engineers |
| One sentence per line | One line | Merges cleanly | Odd for a day, then invisible |
| One clause per line | One line, more lines overall | Merges cleanly | Fussy |
| No wrapping, one long line | One line, unreadable in a terminal | Merges, but conflicts are total | Fine in a wrapping editor |

One sentence per line is the standard answer, sometimes called semantic line
breaks. The cost is that the raw file looks ragged; the benefit is measured in
steps 2 and 3.

### Commit and branch conventions that suit prose

| Practice | Why, for documentation |
|---|---|
| One page or one topic per pull request | Reviewers read prose serially, not in parallel |
| Commit message says what changed for the reader | "Clarify retry default" beats "update docs" |
| Branch per change, not per person | A long-lived personal branch guarantees conflicts |
| Squash on merge | The history that matters is the published change |
| Change code and its page in one pull request | The atomicity that makes docs-as-code worth it |

The last row is the one to defend. Splitting a behaviour change and its
documentation into two pull requests reintroduces exactly the drift the
workflow exists to prevent.

### What actually stops non-engineers contributing

| Obstacle | Mitigation |
|---|---|
| Unreadable prose diffs | Semantic line breaks, word diffs |
| Conflicts on concurrent edits | Semantic line breaks |
| No local toolchain | Web editing in GitHub or GitLab for small fixes |
| Reviewing Markdown instead of pages | [Preview deployments](preview-deployments.md) |
| Git itself | Real, and smaller than people assume once the above are fixed |

Git is usually blamed and is usually the smallest of these. The first two are
formatting decisions and the next two are tooling; all four are fixable without
asking anybody to learn rebasing.

### Things to put in the repository

```
.gitattributes        # diff driver for prose, and binary markers
.github/
  PULL_REQUEST_TEMPLATE.md   # the judgment questions, per docs-review
CONTRIBUTING.md       # wrapping convention, how to run the gates locally
```

The wrapping convention belongs in writing. It is the one rule that is
invisible, consequential, and impossible to infer from the existing files once
somebody has broken it.

## How to talk about it

**Lead with the measurement, not the practice.** "The thing that decides
whether Git works for writers is line wrapping. I measured it: one inserted
clause in a hard-wrapped paragraph changed nine lines against two, and two
writers editing different sentences of the same paragraph conflicted when it
was hard-wrapped and merged cleanly with one sentence per line."

**The follow-up is what to do about an existing hard-wrapped corpus**, and the
answer is not a mass reflow on day one, because that destroys `git blame` for
every page. Set the convention for new and edited content, use word diffs
meanwhile, and reflow a page when you are substantially rewriting it anyway.

**The tradeoff to volunteer.** Semantic line breaks make the source look
ragged and make some editors' formatting commands actively harmful, since a
"reflow paragraph" keystroke undoes it silently. You need the convention
documented and ideally a lint rule, or it decays one well-meaning editor at a
time.

**One sharper point.** Git is the usual scapegoat for documentation
contribution problems and is rarely the cause. Diff legibility and merge
conflicts are formatting decisions; reviewing rendered pages is a preview
deployment. Fix those three and the residual difficulty of Git for an
occasional contributor is a web editor and one page of instructions.

## How to prove it

**The artifact.** A repository with a documented wrapping convention, a
`.gitattributes` prose diff driver, and a pull request template that asks the
judgment questions rather than the mechanical ones.

**Three things to do, in order:**

1. Run the golden path, especially step 3. A conflict over non-overlapping
   edits is the most persuasive thing in this category.
2. Check how an existing docs repository you have is wrapped, and write the
   convention into `CONTRIBUTING.md` either way.
3. Set up the word-diff driver and read one recent prose diff with it. If your
   corpus is hard-wrapped, the difference is immediate.

**What makes it credible rather than decorative.** Numbers. "Semantic line
breaks produce better diffs" is a preference; "one inserted clause changed nine
lines against two, and the hard-wrapped version conflicted where the other
merged cleanly" is a measurement, and it takes half an hour to reproduce on any
corpus.

## Related

- [Docs-as-code](docs-as-code.md), the workflow this makes liveable
- [Reviewing documentation](docs-review.md), what reviewers do with these diffs
- [Preview deployments and publishing](preview-deployments.md), reviewing pages instead of diffs
- [Documentation CI](documentation-ci.md), the gates a contributor runs before pushing
