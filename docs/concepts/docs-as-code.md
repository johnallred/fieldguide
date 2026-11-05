---
title: Docs-as-code
summary: "Treating documentation as source: same repository, same review, same CI, same release."
diataxis: explanation
audience: developer
concept: docs-as-code
tags: [dac, core]
---

# Docs-as-code

`core` · difficulty 1 · 2h

!!! note "Not a quotation (derived)"
    Both postings describe documentation built, reviewed and shipped like software.

**Leads to:** [Code-sample validation](code-sample-validation.md), [Documentation CI](documentation-ci.md), [Generated API reference](api-reference-generation.md), [Git authoring workflows for writers](git-authoring.md), [Link checking](link-checking.md), [Markdown and its dialects](markdown.md)

## What it is

Documentation kept in the same version control as the code, written in plain
text, reviewed through pull requests, and built and published by CI. The
opposite is documentation kept in a CMS, a wiki, or a shared drive, edited
through a web form, and published by someone clicking a button.

It is a workflow decision rather than a tooling decision, though it forces a
long chain of tooling decisions afterwards.

## Why the job asks for it

Neither posting uses the phrase. Both describe its consequences, which is more
telling: Intel asks for Git authoring, CI/CD builds, linting, link validation
and publishing as separate bullets, and NVIDIA asks for standards encoded into
validators. Those are all things you can only do to documentation that lives in
a repository.

The practical reason this matters on a Tuesday is **drift**. Documentation
stored away from the code it describes has no mechanism connecting the two. An
engineer changes a function signature and the page describing it stays correct
in the CMS forever, because nothing in the engineer's workflow ever touched it.

Docs-as-code does not solve drift. It creates the *opportunity* to solve drift,
by putting the page in the same diff as the change, in front of the same
reviewer, gated by the same pipeline. Everything else in this guide's
[quality automation](../coverage.md) category is built on that opportunity, and
none of it is possible without this step first.

The second reason is contribution. An engineer who will never log into a
documentation portal will fix a typo in a Markdown file if the fix is a
three-line pull request in a repository they already have cloned.

## The golden path

Build a documentation site from nothing, publish it, and see the publish
happen automatically. About twenty minutes.

**Step 1: a repository with documentation in it**

```bash
mkdir docs-as-code-demo && cd docs-as-code-demo
git init -q
python3 -m venv .venv && source .venv/bin/activate
pip install --quiet mkdocs
mkdocs new .
```

You now have `mkdocs.yml` and `docs/index.md`. That is the whole structure.

```bash
ls -R
```

**Step 2: see it build**

```bash
mkdocs build --strict
ls site/
```

`--strict` turns warnings into errors. Use it from the first build, not later:
a project that accumulated five hundred warnings before anyone turned it on
never turns it on.

**Step 3: break it on purpose, and watch the build catch it**

```bash
cat >> docs/index.md <<'EOF'

See the [installation guide](install.md) for details.
EOF

mkdocs build --strict
```

It fails, naming the missing target. That failure is the entire argument for
docs-as-code in one line: a dead link is now a build error rather than a
reader's problem. Fix it by creating the page:

```bash
printf '# Installation\n\nRun the installer.\n' > docs/install.md
mkdocs build --strict
```

**Step 4: put it under review and under CI**

```bash
mkdir -p .github/workflows
cat > .github/workflows/docs.yml <<'EOF'
name: docs
on: [push, pull_request]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install mkdocs
      - run: mkdocs build --strict
EOF

printf 'site/\n.venv/\n' > .gitignore
git add -A && git commit -qm "Documentation site with a strict build in CI"
git log --oneline
```

**What you built.** Documentation in version control, with a build that fails
on a broken link, running on every push. Every other automated gate in this
guide, from [prose linting](prose-linting.md) to
[cold-start testing](coldstart-testing.md), is another step in that workflow
file.

## Reference

### What moves into the repository

| Artifact | Where it lives | Reviewed by |
|---|---|---|
| Page source | `docs/*.md` | Pull request |
| Navigation and site config | `mkdocs.yml`, `docusaurus.config.js` | Pull request |
| Style rules | `.vale.ini`, `styles/` | Pull request |
| The build and publish pipeline | `.github/workflows/` | Pull request |
| Content model and templates | Front-matter schema, scaffolding | Pull request |

### The vocabulary

| Term | Meaning |
|---|---|
| Single source of truth | One canonical location per fact, with everything else referencing it |
| Drift | Documentation and implementation disagreeing, silently |
| Gate | A check that can fail a pull request |
| Strict build | Warnings treated as errors |
| Preview deployment | A built copy of the site for one pull request, so reviewers read rendered pages |
| Docs-adjacent code | Scripts in the docs repo that validate, generate or package content |

### What it is commonly confused with

| Not the same as | Difference |
|---|---|
| Markdown | An authoring format. You can keep Markdown in a wiki and get none of this |
| Static site generators | A build tool. Necessary, not sufficient |
| Having docs on GitHub | Storage is not review, and review is not CI |
| Writing docs in the code | That is docstrings and [generated reference](api-reference-generation.md), one part of a larger corpus |

## How to talk about it

**What a competent answer sounds like.** Lead with drift and with gates, not
with Git. "Documentation in the repository means a page can be in the same pull
request as the change it describes, and it means I can fail a build on a dead
link or an example that no longer runs. Those two things are most of what keeps
a corpus from rotting."

**The follow-up you will get is about non-engineer contributors**, and it is
the real objection. A technical writer without Git, a product manager who wants
to fix a sentence, a support engineer with a correction. If you answer that
everyone should learn Git, you have failed the question.

Better answer: name the actual mitigations and be honest that they are partial.
Web-based editing in GitHub or GitLab handles a typo without a local clone.
Preview deployments let a reviewer read the rendered page rather than a diff.
A CMS that commits to the repository behind the scenes is a real option for
large writing teams. And some organisations genuinely should not do this: if
most of your content is authored by people whose job is not software, the
workflow tax is real and a content management system may win.

**The tradeoff to volunteer.** Docs-as-code moves the cost of documentation
from publishing time to authoring time. Publishing becomes free and automatic;
authoring now requires a toolchain, a review cycle, and a green build. That
trade is overwhelmingly worth it for developer documentation, where the
audience and the authors both live in repositories. It is much less obviously
right for marketing content or end-user help centres, and claiming otherwise in
an interview signals that you have only worked on one kind of documentation.

**One sharper point if you want to show depth.** Docs-as-code is often sold as
"engineers will contribute to the docs now". They mostly will not. What
actually changes is that *you* can automate quality, and that a change to the
code and a change to its documentation can be made atomic. Pitch it on the
automation, not on the contributions, because the contribution promise is the
one that disappoints.

## How to prove it

**The artifact.** A public repository whose documentation build is a CI gate,
not a convenience. The specific thing a reviewer looks for is a workflow file
with `--strict` in it and more than one check in the job.

**Three things to do, in order:**

1. Run the golden path above and push it. Fifteen minutes, and you now have a
   repository where a dead link fails CI. That alone is further than most docs
   sites get. You will know the gate is wired when a deliberately broken link
   turns the build red and fixing it turns it green. A build that stays green
   either way is reading something other than the exit code.
2. Add [link checking](link-checking.md) and
   [prose linting](prose-linting.md) as separate jobs. Separate, so a broken
   link does not mask a style failure.
3. Open one pull request that changes a code file and its documentation page
   together, and link to it. That diff *is* the argument, and it is more
   convincing than any description of the workflow.

**What makes it credible rather than decorative.** A repository where the docs
build is green and nothing would fail if the content were wrong proves you can
install MkDocs. A repository with a check that has *caught* something, visible
in the history as a red build followed by a fix, proves the gate does work.
Keep that commit; it is the most useful thing in the project.

## Related

- [Git authoring workflows for writers](git-authoring.md), the half of this that is about people rather than pipelines
- [Documentation CI](documentation-ci.md), what to put in the workflow file
- [Markdown and its dialects](markdown.md), what you will be authoring in
