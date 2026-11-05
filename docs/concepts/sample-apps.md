---
title: Sample applications and galleries
summary: "A gallery is a list of promises, and the two ways it breaks are a sample that stopped working and a sample nobody needed."
diataxis: how-to
audience: developer
concept: sample-apps
tags: [gp, supporting]
---

# Sample applications and galleries

`supporting` · difficulty 3 · 6h

!!! quote "Asked for by name"
    Intel: "This role owns the developer first experience end to end across the Intel AI stack, including quickstarts, golden paths, reference documentation, tutorials, samples, and structured learning paths, by writing and maintaining developer documentation, the sample-app gallery, site navigation, and a crawlable, agent-ready front door"

**Prerequisites:** [Sample walkthroughs](sample-walkthroughs.md), [Code-sample validation](code-sample-validation.md)

## What it is

A set of complete, runnable applications, and an index that presents them.
Unlike a [code sample](code-sample-validation.md) in a page, a sample app is a
standalone project a reader can clone and run; unlike a
[walkthrough](sample-walkthroughs.md), it is not primarily there to be read.

Intel names the sample-app gallery as an owned artifact. The word that matters
is **gallery**, because it is the index that creates the obligations. A gallery
is a published list of promises: these things exist, they work, and they are
worth your time.

## Why the job asks for it

Because a gallery is where a corpus's maintenance debt becomes visible to
readers.

A documentation page that goes stale misleads whoever reads it. A sample app
that goes stale wastes an hour of someone's afternoon before failing, and they
conclude the product is broken rather than the sample. Then the gallery entry
that promised it is still sitting there, with a title and a description, in a
list that implies curation.

The quantity makes it worse. Forty samples, each with its own dependencies and
its own release cadence, is forty independent decay processes. Which is why
this is difficulty 3 and why it depends on
[code-sample validation](code-sample-validation.md): a gallery without
automated verification is a liability that grows.

## The golden path

Build a gallery with a manifest, verify every entry, then ask whether the
gallery covers anything readers need. About forty minutes. The second
measurement is the one that changes what you build.

Committed as `drills/gallery_audit.py`, and that is not a convenience here. The
page below shows the manifest in full and the checker in fragments, and quotes
output from a `check_gallery.py` whose source it never prints, against three
sample programs it never writes. The output block was unreachable: a reader
could follow every step and have nothing to run. The drill is the complete
version, the manifest in it is the one above, and a test holds the two
together.

One row order changed when it was committed. The three zero-ticket topics used
to be listed in the order a Python set happened to iterate them, which is to
say in no order at all; they are now in the order the manifest introduces them.
A table that cannot be regenerated is a screenshot with extra steps.

**Step 1: the gallery as a manifest, not a page**

````bash
mkdir -p gallery/samples/{hello,batch,stale} && cd gallery
cat > gallery.yaml <<'EOF'
samples:
  - id: hello
    title: Hello widget
    teaches: [install, first-call]
    entrypoint: samples/hello/main.py
    expect: "widgets: 3"
  - id: batch
    title: Batch requests
    teaches: [batching]
    entrypoint: samples/batch/main.py
    expect: "sent 2 batches"
  - id: stale
    title: Streaming responses
    teaches: [streaming]
    entrypoint: samples/stale/main.py
    expect: "streamed 10 chunks"
  - id: missing
    title: Webhooks
    teaches: [webhooks]
    entrypoint: samples/missing/main.py
    expect: "received 1 webhook"
EOF
````

The manifest is the gallery. The page that readers see is generated from it,
which means the index cannot list something the manifest does not describe, and
every claim in it is checkable. `teaches` and `expect` are the two fields that
make the rest of this page possible.

**Step 2: verify every entry**

```python
for s in gallery["samples"]:
    entry = Path(s["entrypoint"])
    if not entry.exists():
        problems.append(f"{s['id']}: entrypoint {entry} does not exist")
        continue
    r = subprocess.run([sys.executable, str(entry)],
                       capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        problems.append(f"{s['id']}: exited {r.returncode}")
    elif s["expect"] not in r.stdout:
        problems.append(f"{s['id']}: expected {s['expect']!r}, got {r.stdout.strip()!r}")
```

```bash
python3 check_gallery.py
```

```
GALLERY  stale: expected 'streamed 10 chunks', got 'streamed 8 chunks'
GALLERY  missing: entrypoint samples/missing/main.py does not exist
FAIL: 2/4 samples verified
exit=1
```

Two defect classes, and they are different in kind.

`stale` is **drift**: the sample runs and its behaviour changed, which only an
output assertion catches, exactly as on the
[code-sample validation](code-sample-validation.md) page. `missing` is worse:
a gallery entry with a title, a description and no code. Somebody listed a
sample they intended to write.

Half the gallery was a promise it could not keep, and the index gave no sign.

**Step 3: ask what the gallery covers**

A verified gallery can still be useless. Cross the `teaches` tags against what
readers ask about.

**The ticket counts below are invented**, because this project has no support
queue. They stand in for the one input this measurement cannot be run without,
and they are the shape such a distribution reliably has: a long head of
failure-mode questions and a tail of feature questions. Substitute your own
before drawing any conclusion from the arithmetic.

```python
covered = {t for s in gallery["samples"] for t in s["teaches"]}
#: Stand-in for a real support queue. Replace with yours.
asked_about = {"retries": 41, "auth": 33, "error-handling": 28,
               "pagination": 12, "batching": 6, "streaming": 3}
```

```
topic             in gallery  tickets
retries                    -       41
auth                       -       33
error-handling             -       28
pagination                 -       12
batching                 yes        6
streaming                yes        3
install                  yes        0
first-call               yes        0
webhooks                 yes        0

tickets about uncovered topics: 114 of 123
```

**On that stand-in distribution, 114 of 123 tickets concern topics with no
sample.** The gallery covers install, first call and webhooks, which generate
no tickets at all, and covers none of retries, auth, error handling or
pagination. The arithmetic is only as good as the input; what travels is the
shape, and the shape is not an accident.

That is the normal state of a gallery, and the reason is structural rather than
negligent. Samples get written when a feature ships, so the gallery documents
the **happy path of each feature** and nothing about the failure modes readers
hit in production. Retries and error handling are not features; they are what
happens when features meet reality, so nobody is assigned to demonstrate them.

**Step 4: what the two measurements tell you to do**

```
verified: 2/4
demand coverage: 9 of 123 tickets
```

Those numbers point in different directions, and both are actionable. The
verification failure says fix or delete two entries today. The coverage gap
says the next sample you write should be about retries, not about the feature
that shipped last week.

Deleting is the underrated half. A gallery of ten samples that all work and
cover the top three support topics beats forty where six are broken, and
`missing` should be removed from the manifest rather than left as an aspiration.

**What you built.** A manifest whose claims are checked, a verification run
that found half the gallery wanting, and a demand measurement that says what to
write next.

## Reference

### Sample app against the alternatives

| | In-page sample | Walkthrough | Sample app |
|---|---|---|---|
| Length | Lines | A page | A project |
| Read or run | Read | Read, then run | Run, then read |
| Dependencies | The docs build | The docs build | Its own |
| Decay rate | Slow | Slow | Fast, independently |
| Verified by | [Sample validation](code-sample-validation.md) | Same | Its own CI job |
| Right for | One API call | One task end to end | An architecture |

A sample app earns its cost when the thing being shown is a **shape**: how the
pieces fit, how configuration is layered, what a real project's structure looks
like. For anything smaller, an in-page sample is cheaper to maintain and
likelier to be read.

### The manifest fields that earn their place

| Field | Enables |
|---|---|
| `entrypoint` | Verification; without it the gallery cannot be checked |
| `expect` | Catching drift rather than only breakage |
| `teaches` | The coverage measurement in step 3 |
| `stack` or `requires` | Filtering, and a reproducibility check |
| `updated` or `verified` | [Freshness](freshness-monitoring.md), per sample |
| `status` | Permits a published "unmaintained" state |

`teaches` is the one most galleries omit and the one that makes the gallery
analysable. Without it you cannot answer whether the gallery covers anything,
only whether it runs.

### How galleries actually fail

| Failure | Cause | Detected by |
|---|---|---|
| A sample no longer runs | Dependency or API change | Running it in CI |
| A sample runs and lies | Behaviour drifted | An output assertion |
| A listed sample does not exist | Someone listed an intention | Entrypoint check |
| The gallery covers nothing readers need | Samples follow feature launches | The demand measurement |
| Forty samples, six broken | No per-sample ownership | All of the above, plus retirement |
| Each sample pins differently | No shared environment policy | [Reproducible environments](reproducible-environments.md) |

### Running them in CI without the bill

| Strategy | Cost |
|---|---|
| Every sample on every pull request | Prohibitive past a handful |
| Nightly, all samples | Good default; failures open issues |
| On pull request, only samples touching changed paths | Fast and partial |
| Weekly, with dependency updates | Catches upstream drift specifically |
| Smoke only: it starts and exits 0 | Cheap, and misses drift |

Nightly plus output assertions is the usual right answer. Smoke testing a
gallery is the common choice and it catches only the first failure row above.

### Retiring a sample

A gallery needs a documented way to remove an entry, or it only grows.
[Retirement](content-retirement.md) applies: remove it from the manifest, leave
a redirect if it had a URL, and say why. A sample marked unmaintained in a
gallery is more honest than one quietly broken, and far more honest than one
listed and absent.

## How to talk about it

**Lead with the gallery as a promise list.** "A sample app that goes stale
costs a reader an hour and they conclude the product is broken, not the sample.
So the gallery is a manifest rather than a page: each entry declares an
entrypoint, an expected output and what it teaches, the page is generated from
it, and CI runs every one."

**The follow-up is coverage, and this is the stronger half.** A verified gallery
can still be useless. Crossing the `teaches` tags against support volume on my
own worked example puts 114 of 123 tickets on topics with no sample. I should
be clear that those ticket counts are invented, since I have no support queue;
the reason to expect that shape is structural. Samples get written when
features ship, so a gallery documents each feature's happy path and nothing
about retries, auth or error handling. Those are not features,
so nobody is assigned to demonstrate them.

**The tradeoff to volunteer.** Every sample is an independent maintenance
commitment with its own dependency tree, and the honest consequence is that the
right number of samples is much smaller than teams want. Ten that work and
cover the top support topics beat forty with six broken, and getting from forty
to ten means deleting, which needs a retirement policy nobody wants to write.

**One sharper point.** The entrypoint check is the cheapest finding in this
whole area. A gallery entry with a title, a description and no code is the
easiest thing in the world to create, because the index and the implementation
live in different places. One `Path.exists()` per entry catches it, and on an
old gallery it usually catches something.

## How to prove it

**The artifact.** A gallery driven by a manifest, a CI job that runs every
entry and asserts its output, and a coverage measurement against support
volume.

**Three things to do, in order:**

1. Run the golden path. Step 2's entrypoint check takes a minute to write and
   finds real things.
2. Tag your existing samples with what they teach, then rank your support
   topics by volume. The gap is your backlog, and it will not look like your
   roadmap.
3. Pick the oldest sample nobody has verified and run it. Whatever happens is
   information.

**What makes it credible rather than decorative.** Neither of this guide's
repositories ships a sample gallery, which the
[demonstrated](../demonstrated.md) page records; `docpack` validates samples
embedded in its own documentation, which is the in-page case rather than this
one. What travels is one real measurement and one method: half the gallery was
unverifiable, which the entrypoint and output checks found, and the coverage
cross-tabulation is a method whose ticket counts here are invented and have to
come from your own queue.

## Related

- [Sample walkthroughs](sample-walkthroughs.md), the readable form of the same material
- [Code-sample validation](code-sample-validation.md), the verification this depends on
- [Reproducible environments](reproducible-environments.md), what each sample has to declare
- [Support deflection](support-deflection.md), the demand signal from step 3
