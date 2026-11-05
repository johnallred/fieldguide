---
title: Preview deployments and publishing
summary: Shipping the site, and giving reviewers a rendered page instead of a diff.
diataxis: how-to
audience: developer
concept: preview-deployments
tags: [qa, supporting]
---

# Preview deployments and publishing

`supporting` · difficulty 2 · 3h

!!! quote "Asked for by name"
    NVIDIA: "Build and run docs-as-code pipelines: Git authoring, CI/CD builds, linting, link and code-sample validation, and publishing"

**Prerequisites:** [GitHub Actions for docs](github-actions.md)

## What it is

Two related things that are usually built at once. **Publishing** is the job
that puts the built site somewhere readers can reach it when a change lands on
the default branch. **Preview deployments** build the site for a pull request
and give reviewers a URL, so review happens against a rendered page rather
than against Markdown in a diff.

Publishing is nearly free once a build exists. Previews are where the real
decisions are, and most of them are about permissions and search engines
rather than about building.

## Why the job asks for it

NVIDIA lists publishing as part of the pipeline. The reason it belongs in a
quality category rather than an infrastructure one is that previews are the
single most effective fix for the biggest objection to
[docs-as-code](docs-as-code.md): that non-engineer contributors and reviewers
cannot work in diffs.

A product manager asked to review a Markdown diff will approve it without
reading it. The same person given a link to the rendered page will find the
sentence that is wrong. Previews are what make review by non-engineers real,
and that is a documentation-quality outcome, not a deployment convenience.

## The golden path

Build a preview, discover what the production configuration leaks into it, and
fix the part that actually matters. About twenty-five minutes.

**Step 1: a site with a production URL**

````bash
mkdir -p preview-demo/docs && cd preview-demo
cat > mkdocs.yml <<'EOF'
site_name: Preview demo
site_url: https://example.github.io/widget/
theme:
  name: mkdocs
EOF
printf '# Home\n\nSee the [guide](guide.md).\n' > docs/index.md
printf '# Guide\n\nBack [home](index.md).\n' > docs/guide.md
mkdocs build -q
````

**Step 2: check the assumption everyone repeats**

The usual warning is that a site built for one base URL breaks when served
from another prefix. Test it rather than believing it:

```bash
grep -o 'href="[^"]*css[^"]*"' site/index.html | head -3
grep -c 'href="/' site/index.html
```

```
href="css/bootstrap.min.css"
href="css/fontawesome.min.css"
href="css/brands.min.css"
0
```

Relative paths, and zero absolute-root hrefs. The build is portable across
prefixes: you can serve this same output at `/pr-123/` and the CSS resolves.
The warning does not apply to MkDocs output, so do not spend your preview
budget solving it.

**Step 3: find what `site_url` does leak**

Rebuild as a preview and compare what is URL-dependent:

```bash
sed -i 's|site_url:.*|site_url: https://example.github.io/widget/pr-123/|' mkdocs.yml
mkdocs build -q -d site-pr

for d in site site-pr; do
  printf "%-8s " "$d"
  grep -o '<link rel="canonical" href="[^"]*"' $d/index.html | head -1
done
```

```
site     <link rel="canonical" href="https://example.github.io/widget/"
site-pr  <link rel="canonical" href="https://example.github.io/widget/pr-123/"
```

And the sitemap:

```bash
for d in site site-pr; do
  printf "%-8s " "$d"
  (gzip -dc $d/sitemap.xml.gz 2>/dev/null || cat $d/sitemap.xml) \
    | grep -o '<loc>[^<]*</loc>' | head -2 | tr '\n' ' '
  echo
done
```

```
site     <loc>https://example.github.io/widget/</loc> <loc>.../guide/</loc>
site-pr  <loc>https://example.github.io/widget/pr-123/</loc> <loc>.../pr-123/guide/</loc>
```

The preview is advertising itself. It declares its own canonical URL and ships
a sitemap inviting crawlers to index every page of a draft.

**Step 4: confirm nothing stops that**

```bash
for d in site site-pr; do
  printf "%-8s noindex=%s robots.txt=%s\n" "$d" \
    "$(grep -c 'noindex' $d/index.html)" \
    "$([ -f $d/robots.txt ] && echo yes || echo no)"
done
```

```
site     noindex=0 robots.txt=no
site-pr  noindex=0 robots.txt=no
```

No `noindex`, no `robots.txt`. A publicly reachable preview of unmerged
documentation is fully indexable, and it is competing with production for the
same queries while containing text nobody has approved.

**Step 5: fix the real problem**

```bash
mkdir -p overrides
cat > overrides/main.html <<'EOF'
{% extends "base.html" %}
{% block extrahead %}
  {% if config.extra.preview %}
    <meta name="robots" content="noindex, nofollow">
  {% endif %}
{% endblock %}
EOF
printf 'User-agent: *\nDisallow: /\n' > docs/robots.txt
echo "built previews now carry noindex when extra.preview is set"
```

Two independent controls, because either alone can be bypassed: a `noindex`
meta tag on every page, and a `robots.txt` that disallows everything. Set
`extra.preview` only in the preview job.

**What you built.** A preview that reviewers can read and search engines will
not index. That is the whole job, and the hard part was never the base URL.

## Reference

### What a preview costs you, by hosting choice

| Approach | Fork pull requests | Cleanup | Notes |
|---|---|---|---|
| GitHub Pages, one site | Not supported | N/A | One site per repo; no per-PR previews |
| Netlify or Cloudflare Pages | Supported, sandboxed | Automatic on merge | Purpose-built for this |
| Upload the build as a CI artifact | Works everywhere | Automatic expiry | Reviewer downloads a zip; no URL to click |
| Self-hosted per-PR subpath | Needs secrets | You build it | Where the permissions trap lives |

### The permissions trap

This is the one worth knowing cold. A workflow triggered by `pull_request`
from a fork gets **no secrets**, by design, so a deploy step in it cannot
authenticate. The tempting fix is `pull_request_target`, which does have
secrets.

| Trigger | Has secrets | Runs code from | Safe to deploy from |
|---|---|---|---|
| `pull_request` | No | The fork | Nothing to deploy with |
| `pull_request_target` | Yes | The base branch | Only if it never checks out the fork |
| `workflow_run` | Yes | The base branch | Yes, consuming an artifact |

`pull_request_target` that checks out the pull request's head and then runs a
build is remote code execution with your deploy credentials. The safe pattern
is two workflows: an untrusted one that builds and uploads an artifact with no
secrets, and a trusted `workflow_run` that downloads the artifact and publishes
it without ever executing contributor code.

### Publishing, which is the easy half

```yaml
permissions:
  contents: read

jobs:
  publish:
    if: github.ref == 'refs/heads/main'
    permissions:
      contents: read
      pages: write
      id-token: write
    steps:
      - uses: actions/checkout@v4
      - run: pip install -e ".[docs]"
      - run: mkdocs build --strict
      - uses: actions/configure-pages@v5
      - uses: actions/upload-pages-artifact@v3
        with:
          path: site
      - uses: actions/deploy-pages@v4
```

Read-only at the top, write only in this job, and gated on the default branch
so a pull request can never publish.

### What this guide actually does

`docpack` publishes to GitHub Pages on `main` and regenerates its retrieval
artifacts alongside the site. It has **no** per-pull-request preview, because
GitHub Pages hosts one site per repository and adding a real preview means
adding a second host. That is recorded as a partial demonstration rather than
written up as a complete one, which is the honest state.

## How to talk about it

**Lead with review, not deployment.** "Previews are how review by
non-engineers becomes real. A reviewer who is handed a Markdown diff approves
it; a reviewer handed a rendered page finds the wrong sentence. That is a
content-quality mechanism that happens to be implemented in CI."

**The follow-up you want is about forks**, because the answer separates people
who have shipped this from people who have read about it. Fork pull requests
get no secrets, `pull_request_target` has secrets but must never check out
contributor code, and the safe shape is build-without-secrets then publish from
a `workflow_run`.

**The tradeoff to volunteer.** Previews cost a second hosting target, a cleanup
story, and a small ongoing bill, and they are worth it in direct proportion to
how many of your reviewers are not engineers. On a repository where every
reviewer reads diffs comfortably, the CI-artifact approach gets most of the
value for none of the infrastructure.

**One sharper point.** Almost nobody adds `noindex` to their previews. The
default MkDocs preview ships a canonical tag pointing at itself and a sitemap
listing every draft page, so unapproved documentation ends up in search results
competing with the real thing. It is two lines to prevent, and noticing it is
the kind of detail that reads as having operated a real site rather than
configured one.

## How to prove it

**The artifact.** A repository that publishes on merge with least-privilege
permissions, plus either a working preview or an explicit written reason there
is none.

**Three things to do, in order:**

1. Run the golden path. Step 2 will save you time forever, because the base-URL
   worry is folklore for MkDocs output.
2. Check whether any preview you already run is indexable. Fetch a preview URL
   and grep for `noindex`. If it is missing, that is a real finding on a real
   site.
3. Write down, in your repository, why you do or do not have previews. The
   written reason is worth as much in an interview as the feature, because it
   shows the decision was made rather than skipped.

**What makes it credible rather than decorative.** A publish job that is gated
on the default branch and scoped with `permissions:`, and an answer to the fork
question that does not involve `pull_request_target` checking out the head.

## Related

- [GitHub Actions for docs](github-actions.md), where these jobs live
- [Reviewing documentation](docs-review.md), the human process previews serve
- [Crawlability](crawlability.md), the same indexing concerns on the production site
- [Documentation CI](documentation-ci.md), the gates that run before any of this
