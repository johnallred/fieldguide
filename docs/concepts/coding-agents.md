---
title: Documentation for coding agents
summary: Writing for a reader that pastes your example straight into a file and cannot ask whether it was meant to be complete.
diataxis: explanation
audience: developer
concept: coding-agents
tags: [ai, core]
---

# Documentation for coding agents

`core` · difficulty 2 · 4h

> Optimize documentation for search (SEO and GEO) and for AI assistants and coding agents through agentready, LLMdigestible content

> Source: intel posting, verbatim

**Prerequisites:** [Agent-ready content](agent-ready-content.md)

## What it is

Writing documentation for a reader that will take your code sample and put it
into a file. Not an assistant answering a question, and not an agent running a
multi-step task: a coding agent in someone's editor, reading your page to write
code with your library.

The distinguishing property is that **it acts on your examples directly and
cannot ask whether one was meant to be complete.**

## Why the job asks for it

Intel names this audience explicitly and separately from AI assistants:
"optimize documentation ... for AI assistants and coding agents". The
separation is correct and worth preserving, because the two want different
things from the same page.

An assistant wants to find the chunk that answers a question. A coding agent
wants to **copy a working example and get the imports right.** A page that
serves the first well can serve the second badly, and the usual failure is a
page full of excellent partial snippets.

On a Tuesday it is a support ticket with a strange shape. A developer reports
that the library does not work, and pastes code that looks like your
documentation. It is your documentation, from three different pages,
concatenated by an agent: the client construction from the quickstart, the
retry configuration from a how-to that assumed an existing client, and an
import line the agent inferred because none of the three snippets had one.
**Every fragment was correct and the combination never existed.**

## The golden path

Build a checker for the properties a coding agent needs, run it over realistic
samples, and fix a page that passes human review and fails this. Forty minutes.

**Step 1: four samples, all of which look fine to a person**

````bash
mkdir -p agentdocs-drill/docs && cd agentdocs-drill
cat > docs/quickstart.md <<'EOF'
---
title: Quickstart
---
# Quickstart

Create a client and send a request.

```python
from widget import WidgetClient

client = WidgetClient(api_key="sk-...")
print(client.infer("hello"))
```
EOF

cat > docs/retries.md <<'EOF'
---
title: Configure retries
---
# Configure retries

Set `retries` when constructing the client.

```python
client = WidgetClient(api_key="sk-...", retries=3)
```
EOF

cat > docs/batching.md <<'EOF'
---
title: Batch requests
---
# Batch requests

Pass a list instead of a string.

```python
results = client.infer_batch(["a", "b", "c"])
```
EOF

cat > docs/streaming.md <<'EOF'
---
title: Stream a response
---
# Stream a response

```python
for token in client.infer_stream("hello"):
    print(token, end="")
```
EOF
ls docs/
````

Every one of those is a reasonable snippet and would pass review. Three of the
four are unusable to something that cannot infer context.

**Step 2: the checker**

```bash
cat > agentcheck.py <<'PY'
"""Check code samples for the properties a coding agent needs.

Four checks. None of them is about quality; all are about whether a sample
survives being lifted out of its page.

  RUNNABLE   does it define the names it uses, or import them?
  LABELLED   if it is deliberately a fragment, does it say so?
  IMPORTS    are the library's own imports present?
  VERSIONED  does the page say which version this is for?

The LABELLED check is the important one and the cheapest. A fragment is
perfectly fine; an UNMARKED fragment is the defect, because an agent cannot
tell the difference and a reader can.
"""
import ast
import re
import sys
from pathlib import Path

LIBRARY = "widget"
FENCE = re.compile(r"```python\n(.*?)```", re.S)

#: Comment markers that say "this is deliberately partial".
FRAGMENT_COMMENTS = ("# fragment", "# continues from", "# assumes")


def is_marked(source):
    """True when the snippet declares itself partial.

    An ellipsis counts only as a STATEMENT on its own line. Matching `...`
    anywhere in the text treats `api_key="sk-..."` as a fragment marker,
    which silently exempted the page this checker was written to catch. That
    was a real bug in the first version of this checker, and it is the
    characteristic failure of substring matching over code.
    """
    if any(marker in source for marker in FRAGMENT_COMMENTS):
        return True
    return any(line.strip() == "..." for line in source.splitlines())


def samples(path):
    return FENCE.findall(path.read_text(encoding="utf-8"))


def undefined_names(source):
    """Names used but never bound or imported in this snippet.

    Uses the AST rather than a regex so that attribute access, function
    arguments and comprehension variables are handled correctly. Builtins
    are excluded.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return ["<syntax error>"]

    bound, used = set(), []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                bound.add((alias.asname or alias.name).split(".")[0])
        elif isinstance(node, ast.Name):
            if isinstance(node.ctx, (ast.Store, ast.Del)):
                bound.add(node.id)
            else:
                used.append(node.id)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            bound.add(node.name)
        elif isinstance(node, ast.arg):
            bound.add(node.arg)

    builtins = set(dir(__builtins__)) | {"print", "len", "range", "list", "dict"}
    return sorted({n for n in used if n not in bound and n not in builtins})


def check_page(path):
    text = path.read_text(encoding="utf-8")
    front = text.split("---")[1] if text.startswith("---") else ""
    findings = []

    for index, source in enumerate(samples(path), 1):
        label = f"{path.name} sample {index}"
        marked = is_marked(source)
        missing = undefined_names(source)

        if missing and not marked:
            findings.append((
                label, "unmarked-fragment",
                f"uses {missing} without defining or importing them, "
                "and is not marked as a fragment",
            ))
        if f"import {LIBRARY}" not in source and f"from {LIBRARY}" not in source:
            if not marked and missing:
                findings.append((label, "no-import",
                                 f"no {LIBRARY} import, so the agent will guess one"))
        if "version" not in front and "since" not in front:
            findings.append((label, "no-version",
                             "the page does not say which version this is for"))
    return findings


def main(root):
    total = 0
    for path in sorted(root.glob("*.md")):
        findings = check_page(path)
        total += len(findings)
        if findings:
            for label, kind, why in findings:
                print(f"AGENT-READY  {label}: {kind}: {why}", file=sys.stderr)
        else:
            print(f"ok  {path.name}")
    print(f"\n{'FAIL' if total else 'ok'}: {total} problem(s)")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1] if len(sys.argv) > 1 else "docs")))
PY
python3 agentcheck.py docs; echo "exit=$?"
```

**Step 3: fix the pages two ways, and see which check each fix satisfies**

There are two legitimate fixes and they are not interchangeable.

````bash
echo "--- fix A: make the sample self-contained ---"
cat > docs/retries.md <<'EOF'
---
title: Configure retries
version: "2.6"
---
# Configure retries

Set `retries` when constructing the client.

```python
from widget import WidgetClient

client = WidgetClient(api_key="sk-...", retries=3)
print(client.infer("hello"))
```
EOF

echo "--- fix B: keep it a fragment, and say so ---"
cat > docs/batching.md <<'EOF'
---
title: Batch requests
version: "2.6"
---
# Batch requests

Pass a list instead of a string.

```python
# continues from the quickstart; `client` is already constructed
results = client.infer_batch(["a", "b", "c"])
```
EOF

echo "--- and one left broken on purpose ---"
python3 agentcheck.py docs; echo "exit=$?"
````

**Step 4: the fix that scales, which is a different artifact entirely**

The checker catches unmarked fragments. It does not give an agent a complete,
tested starting point, and that is a separate thing worth having.

````bash
cat > docs/complete-example.md <<'EOF'
---
title: Complete working example
version: "2.6"
---
# Complete working example

Every snippet elsewhere in these docs is an excerpt from this file. If you
want something that runs, start here.

```python
from widget import WidgetClient

client = WidgetClient(
    api_key="sk-...",      # from the dashboard
    retries=3,             # see how-to/retries
    batch_size=1,          # see how-to/batching
)

# one request
print(client.infer("hello"))

# several requests
print(client.infer_batch(["a", "b", "c"]))

# streaming
for token in client.infer_stream("hello"):
    print(token, end="")
```
EOF
python3 agentcheck.py docs 2>&1 | grep -E "^ok|complete" ; echo
echo "A canonical complete example is one page an agent can always fall back to,"
echo "and it is testable by code-sample validation, so it cannot rot."
````

**What you built.** A checker for agent-readability, two kinds of fix, and a
canonical complete example.

On the four original pages it reports **10 problems across all four**, and
every one is invisible to human review:

| Page | Finding |
|---|---|
| `quickstart.md` | no version declared |
| `retries.md` | uses `WidgetClient` with no import, unmarked |
| `batching.md` | uses `client` with no definition, unmarked |
| `streaming.md` | uses `client` with no definition, unmarked |

After fix A on `retries.md` (self-contained) and fix B on `batching.md`
(marked fragment with a named prerequisite), both pass. `streaming.md` is left
broken on purpose so the checker still fails.

### The bug the checker found in itself

The first version of this checker treated `...` appearing anywhere as a
fragment marker. `retries.md` contains `api_key="sk-..."`, a redacted
placeholder, so **the checker silently exempted the exact page it was written to
catch.**

That is the characteristic failure of substring matching over code, and it is
why `undefined_names` uses an AST walk rather than a regex: an ellipsis counts
only as a statement on its own line. The fix moved `retries.md` from one finding
to three.

A checker that passes the case it was built for is the most dangerous kind,
because the green result is taken as evidence.

## Reference

### What a coding agent needs that a human reader does not

| Need | Why a human does not need it | Cost of omitting |
|---|---|---|
| Imports in the sample | They infer from the page's other samples | The agent guesses an import path |
| Names defined, or marked as assumed | They know `client` came from earlier | Code that references undefined names |
| An explicit fragment marker | A fragment is obvious to them | A fragment treated as complete |
| The version the sample is for | They are on the current page | An API that changed |
| One canonical complete example | They assemble mentally | Fragments concatenated into fiction |

### The two legitimate fixes, which are not interchangeable

| Fix | Use when | Cost |
|---|---|---|
| Make it self-contained | The sample is short | Repetition across pages |
| Mark it as a fragment and name its prerequisite | The setup is long or shared | The agent must follow the reference |

**Do both in different places.** A reference page's examples should be
self-contained; a how-to in the middle of a sequence should be a marked
fragment. The defect is the *unmarked* fragment, not the fragment.

### Markers worth standardising on

| Marker | Meaning |
|---|---|
| `# continues from <page>` | `client` and friends exist already |
| `# assumes <thing>` | A precondition the snippet does not create |
| `# fragment` | Deliberately partial, no claim of runnability |
| `# docpack: skip` | Excluded from [sample validation](code-sample-validation.md), with a reason |
| `...` on its own line | Elided code. Universally understood, including by models |

Pick one set and enforce it, because an agent pattern-matches on what it sees
and inconsistent markers are worse than none.

### "LLM-digestible", unpacked

Intel's phrase. It decomposes into things that are checkable:

| Property | Mechanism |
|---|---|
| Serve Markdown, not only rendered HTML | A build step; see [llms.txt](llms-txt.md) |
| Headings that state what is below them | [Chunking](chunking.md) depends on it |
| Samples that survive extraction | This page |
| Declared page type | [Content model](content-model.md), so a filter can route |
| Stable URLs | A moved page breaks every citation |
| No critical content in images | Diagrams need text equivalents |

The last row is often the biggest single loss in practice: an architecture
explained only in a diagram is invisible to every machine consumer and to
screen readers, which is the rare case where
[accessibility](accessibility.md) and agent-readiness want exactly the same
thing.

### What does not help

| Non-fix | Why |
|---|---|
| A separate corpus written for agents | Drifts from the human one within a quarter |
| Removing prose so the page is "cleaner" | The prose is what makes the chunk findable |
| More samples | Three unmarked fragments are worse than one complete example |
| An `llms.txt` alone | A map does not make a sample runnable |

## How to talk about it

**What a competent answer sounds like.** Lead with the concatenation failure,
because it is specific and nobody expects it. "A coding agent assembles from
several pages. Our retries page had `client = WidgetClient(..., retries=3)` with
no import, because every human reader knows `client` came from the quickstart. An
agent took that snippet, the batching snippet and an inferred import and
produced code that looked like our documentation and never existed anywhere in
it. So I check samples for undefined names with an AST walk, and either make
them self-contained or require an explicit fragment marker. The defect is the
unmarked fragment, not the fragment."

**The follow-up is "does this not just mean repeating the setup everywhere",**
which is the real objection. The answer is that you choose per page type:
reference examples are self-contained because they are read in isolation, and a
how-to inside a sequence stays a marked fragment with a named prerequisite. Plus
one canonical complete example that every excerpt is drawn from, which is
[single-sourcing](single-sourcing.md) applied to code and is testable by
[sample validation](code-sample-validation.md) so it cannot rot.

**The tradeoff to volunteer.** Self-contained samples are more verbose and worse
for a human skimming a reference page, who now reads three lines of setup before
the one line they came for. There is a genuine conflict between the two
audiences on this specific point, and it does not fully resolve. Marking
fragments is the cheaper half of the answer and it costs nothing; making
everything self-contained costs readability and should be done selectively,
which means somebody has to decide per page.

**One sharper point.** The strongest observation is that **this failure mode was
always there and agents made it visible.** A junior developer copying from three
pages hit exactly the same problem, got stuck, and either asked or gave up
quietly, and neither outcome produced a bug report that named your
documentation. An agent does it at volume and the resulting code arrives in a
support ticket. So the agent-readability work is not a new requirement grafted
onto documentation, it is an old defect finally getting measured, which is the
same pattern as [RAG](rag.md) surfacing content gaps. That framing is both true
and much easier to fund.

## How to prove it

**The artifact.** The AST-based undefined-names checker in CI, plus a canonical
complete example that sample validation executes.

**Three things to do, in order:**

1. **Run the golden path.** The checker flagging three of four reasonable-looking
   pages is the demonstration, and the AST walk is what makes it more than a
   regex.
2. **Point it at a real library's documentation.** Yours, or an open-source
   project's. Count the unmarked fragments; in most corpora it is most of the
   samples, and that count is the finding.
3. **Write the canonical complete example** and make every other sample an
   excerpt from it. That is one page, it is tested, and it gives an agent
   somewhere correct to fall back to.

**What makes it credible rather than decorative.** Saying docs should be agent-friendly is a slogan. An
AST checker that distinguishes a marked fragment from an unmarked one, a stated
rule about which page types get self-contained samples, and a tested canonical
example demonstrates that you found the failure and built the gate.

### How this would be demonstrated elsewhere

No coding agent ran against this documentation. The claim this page makes, that
documentation written for a coding agent differs from documentation written for
a person in specific ways, is testable and was not tested here.

**What you need.** A coding agent with repository access, and a task whose
success is mechanically checkable: "add a page that passes the validator", "fix
the failing sample", "wire a new check into CI". Then two versions of your
documentation: the current one, and one with the specific changes this page
recommends.

**What you would run.** The same task, ten times against each documentation
variant, scoring by whether the resulting code passes the repository's own
gates. The documentation is the independent variable, which is the part people
get wrong: it is tempting to vary the prompt, and the prompt is not what you
control for your readers.

**What you would see.**

| Change to the documentation | Rough effect | What it tells you |
|---|---|---|
| Exact file paths instead of descriptions | large | Agents cannot browse like a person |
| The command and its expected output | large | Verification is what unblocks the next step |
| Stating what *not* to edit | large, and underrated | Generated files are the usual casualty |
| One worked example of the task | largest single gain | Same as for human readers |
| Conceptual explanation of why | small | The agent does not need to be persuaded |
| Prose polish, tone, hedging | none measurable | The thing writers spend time on |

The last two rows are the uncomfortable finding, and the reason this concept
is separate from ordinary technical writing. The effort that improves a page
for a person is close to orthogonal to the effort that improves it for an
agent, and a team can only find that out by measuring both.

**How you would know it had failed.** Identical pass rates between variants
usually means the agent never read the documentation, so check whether it
actually opened the files before concluding the content does not matter. A 100%
pass rate on both means the task is too easy. And if success depends on which
model you used more than on which documentation you supplied, the experiment is
measuring the model and has to be re-run with that held fixed.

## Related

- [Agent-ready content](agent-ready-content.md), the framing above this
- [Code-sample validation](code-sample-validation.md), what keeps the canonical example true
- [Crawlability and the agent-ready front door](crawlability.md), being reachable
- [Generative engine optimization](geo.md), the other half of Intel's bullet
