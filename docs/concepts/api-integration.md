---
title: Integrating with APIs
summary: "Writing a client against a real server found three defects: two in the server, and the first one in the client, because the integrator read the wrong field."
diataxis: how-to
audience: developer
concept: api-integration
tags: [auto, core]
---

# Integrating with APIs

`core` · difficulty 2 · 4h

!!! quote "Asked for by name"
    NVIDIA: "Working proficiency in Python or similar to automate content tasks, transform data, and integrate with APIs"

**Prerequisites:** [Python for content automation](python-for-content.md)

## What it is

The third job in NVIDIA's sentence: making a program talk to a service it does
not control. In a documentation role those services are the ones holding
content and process, a CMS, a ticket tracker, a translation vendor, a
repository host, a search index, and increasingly the documentation platform is
itself the server, answering an agent.

The work divides unevenly. Calling an endpoint that behaves is twenty minutes.
Everything after that is deciding what the client does when the service
disagrees, and that is where integrations are actually written.

## Why the job asks for it

Because the content a documentation team needs is almost never in the
repository. It is in the issue tracker, the CMS, the analytics product and the
localisation vendor, and the only way to ask a question spanning two of them is
a program.

There is a second reason that is newer, and it is why this concept is `core`
rather than supporting: the documentation platform is now on the other side of
the line. An [MCP server](mcp.md) over a corpus is an API that other people's
agents integrate against, so a documentation engineer writes clients *and*
publishes one. The two halves teach each other, and the fastest way to learn
what a published API owes its consumers is to be a bad consumer of your own.

## The golden path

Write a client against a real server, deliberately misuse it, and see what the
integration has to survive. About thirty minutes. The target is the companion
repository's [MCP server](mcp.md), so there is no network and no credential
involved.

**Step 1: the smallest honest client**

JSON-RPC over stdio, which is a pipe, a line of JSON, and a line back:

```python
proc = subprocess.Popen([sys.executable, SERVER, "--docs", DOCS],
                        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE, text=True, bufsize=1)

def call(method, params=None, rid=[0]):
    rid[0] += 1
    req = {"jsonrpc": "2.0", "id": rid[0], "method": method}
    if params is not None:
        req["params"] = params
    proc.stdin.write(json.dumps(req) + "\n")
    proc.stdin.flush()
    line = proc.stdout.readline()
    return json.loads(line) if line else {"__dead__": True}
```

The `__dead__` branch is there from the first version, because the commonest
failure of a subprocess transport is the other end exiting, and `readline()` on
a closed pipe returns an empty string rather than raising.

```
initialize        -> {'name': 'docpack-docs', 'version': '0.3.0'}
tools/list        -> search_docs, get_page, list_pages

search_docs  {"query": "how do I make the chunks smaller"}         3300 chars
search_docs  {"query": "...", "diataxis": "how-to"}                4106 chars
list_pages   {}                                                    1815 chars
get_page     {"path": "how-to/pack-for-rag.md"}                    2253 chars
```

Four calls, four answers. By the usual standard the integration is finished.

**Step 2: misuse it on purpose**

The part worth writing is the next table: six requests a real client will
eventually make by accident.

```
  unknown method         rpc-error -32601 method not found: tools/frobnicate
  unknown tool           ok        Error: 'unknown tool: nope'
  missing argument       ok        Error: 'path'
  path outside the tree  ok        Error: path escapes the documentation tree.
  bad diataxis value     ok        No matches for 'x'.
  empty query            ok        No matches for ''.

still alive after all of that: True
```

The server survives everything, refuses the path traversal, and reports one
case as a protocol error. Five come back as **successful calls whose text
begins "Error:"**, which would mean a client can detect failure only by
string-matching prose.

That reading is wrong, and the mistake is the useful part of this page.

**Step 3: the first defect was in the client**

MCP reports a tool-level failure as a successful JSON-RPC response whose result
carries `isError: true`. The server was setting it. My client checked only for
a JSON-RPC `error` key, printed `ok` for everything else, and produced a table
that blamed the server for my own bug.

```
  unknown tool           TOOL-ERR  Error: 'unknown tool: nope'
  missing argument       TOOL-ERR  Error: 'path'
  path outside the tree  ok        Error: path escapes the documentation tree.
  bad diataxis value     ok        No matches for 'x'.
  empty query            ok        No matches for ''.
```

Worth dwelling on, because it is the characteristic integration bug and it is
not a coding mistake. The protocol has two error channels with different
meanings, the client implemented one, and every response was still structurally
valid. Nothing threw. The client was reading a field that does not carry the
answer, and the output looked like evidence.

**Step 4: now the two real defects**

With the flag read correctly, two rows are genuinely wrong.

A rejected path traversal reports `isError: false` while its text says "Error:".
The flag and the prose disagree, the flag is the documented thing to check, and
so a careful client is told that a refused security-relevant lookup succeeded.
The cause is that `get_page` returned an error *string* instead of raising,
bypassing the handler that sets the flag:

```python
if not target.is_relative_to(self.docs_dir.resolve()):
    return "Error: path escapes the documentation tree."    # before
    raise ToolError("path escapes the documentation tree")  # after
```

And an unknown filter value came back as "No matches", indistinguishable from a
question the corpus genuinely cannot answer. A typo in an enum and an empty
result set are different answers and were the same response:

```python
if diataxis is not None and diataxis not in DIATAXIS_TYPES:
    raise ToolError(f"unknown diataxis type {diataxis!r}; expected one of ...")
```

The third row, `Error: 'path'`, was a bare `KeyError` whose `str()` is the key
name, so the message named the problem without stating it.

```
  unknown method         rpc-error -32601 method not found: tools/frobnicate
  unknown tool           TOOL-ERR  Error: unknown tool: nope; expected one of search_docs, ...
  missing argument       TOOL-ERR  Error: get_page requires a 'path' argument
  path outside the tree  TOOL-ERR  Error: path escapes the documentation tree
  bad diataxis value     TOOL-ERR  Error: unknown diataxis type 'nonsense'; expected one of ...
  empty query            ok        No matches for ''.
```

One channel, actionable messages, and the single remaining `ok` is a real empty
result.

**Step 5: the finding that only appeared in a test**

Writing the test for that empty result produced a surprise. A query of apparent
gibberish returned four confident matches, because BM25 tokenises "zzzqqq no
such term anywhere" and matches on `term` and `anywhere`. A genuinely empty
result needs out-of-vocabulary tokens throughout.

```python
#: Genuinely out of vocabulary. "no such term anywhere" matches on `term`.
call(server, "search_docs", {"query": "zzzqqq wwwvvv xxxyyy"})
```

So an integrator cannot use an empty result set to detect a bad query. Empty is
rare, and the normal failure of a search API is a **confident low-relevance
match**: a client branching on `if not results` has written a branch that
practically never runs, against a silent failure that happens constantly.

**What you built.** A working client, a misuse table, one client bug that
produced false evidence, two server defects fixed so failure travels on one
channel, and fourteen tests that assert on the flag rather than the prose.

## Reference

### What to write before the happy path works

| Concern | Why first |
|---|---|
| The transport dying | A closed pipe returns empty, it does not raise |
| A timeout on every call | The default in most clients is to wait forever |
| Which field means failure | See step 3; there is usually more than one |
| Retry policy, and what is safe to retry | A retried write is a duplicate |
| What a partial result looks like | Pagination truncates silently |
| Logging the request, not only the error | An error without its request is unactionable |

### The two error channels, in any protocol

| Channel | Means | Example |
|---|---|---|
| Transport or protocol | The request was not understood | HTTP 400, JSON-RPC `error` |
| Application or tool | Understood, and the answer is a failure | `isError: true`, a 200 with `"status": "failed"` |

Nearly every real API has both, they are easy to confuse, and confusing them
produces a client that works until something goes wrong. The question to settle
before writing any client: *which field do I branch on, and what does the other
one mean when it disagrees?*

### Failure modes a client has to handle

| Mode | Detected by | Usually forgotten |
|---|---|---|
| The service is down | A timeout | No |
| The service is slow | A timeout you set | Yes |
| Authentication expired mid-run | A 401 on call 400 of 900 | Yes |
| Rate limited | 429, or silence | Yes |
| A partial page of results | Comparing count to total | Yes |
| An enum value it does not know | Only if the server checks | Yes, on both sides |
| A confident wrong answer | Nothing; only a human | Always |
| The response shape changed | A schema check | Yes |

The last four are the ones that cost a day, and three of them are a server
choosing to be permissive where it should have refused.

### Publishing an API, learned from consuming one

| Obligation | Because |
|---|---|
| One error channel, used consistently | A client can only branch on one |
| A flag, not prose, for failure | Text is for humans; flags are for code |
| Messages naming the fix, not the symptom | `Error: 'path'` names a key, not a problem |
| Reject unknown enum values | A typo otherwise returns a plausible empty set |
| Refuse by raising, not by returning text | Any other path bypasses the flag |
| List what you accept, in the error | Saves the client reading the schema |
| A test per failure mode, asserting the flag | They regress silently |

Every row came from being a bad consumer of this server for twenty minutes.

### Where credentials live

| Approach | Verdict |
|---|---|
| Environment variable, read once | Fine |
| A secrets manager | Better, where one exists |
| A config file outside the repository | Acceptable |
| In the repository, encrypted | No; the history is forever |
| Hardcoded for a quick script | Becomes permanent within a week |

An integration script's credentials end up in CI eventually, so write it as
though they already are: read from the environment, fail loudly when absent,
and never log request headers.

### Rate limits and bulk work

| Pattern | Use |
|---|---|
| Sequential with a small sleep | A few hundred calls; honest and slow |
| Respecting `Retry-After` | Always, when the server sends it |
| Exponential backoff with jitter | Anything unattended |
| Checkpointing to disk per batch | Any job over a few minutes |
| Concurrency | Last; it multiplies every other failure mode |

The checkpoint is the one that pays. A four-hour extraction that dies at hour
three having written nothing is the most expensive mistake available here, and
appending JSONL as you go prevents it.

## How to talk about it

**Lead with where the work actually is.** "Calling an endpoint that behaves is
twenty minutes. The integration is everything after: which field means failure,
what is safe to retry, what a partial result looks like. I write the
transport-died branch and the timeout before the happy path, because a closed
pipe returns empty rather than raising."

**Then the story, which is worth telling precisely because it does not
flatter.** I wrote a client against an MCP server I also maintain, and produced
a table showing five failure modes reported as successes. The server was
correct: MCP signals a tool failure as a successful response carrying
`isError: true`, my client checked only the JSON-RPC error key, and my output
looked like evidence against the server. That is the characteristic integration
bug. Two error channels with different meanings, the client implementing one,
nothing throwing, every response structurally valid.

**Then what was genuinely wrong, which reading the right field exposed.** Two
defects. A refused path traversal reported success while its text said "Error:",
because that branch returned an error string instead of raising and so bypassed
the flag. And an unknown filter value returned "No matches", making a typo in an
enum indistinguishable from a question the corpus cannot answer. Both are a
server being permissive where it should refuse, and both are now tests that
assert on the flag rather than the prose.

**One sharper point.** A search API almost never returns nothing. Writing the
test for an empty result, my gibberish query matched four chunks because BM25
tokenised it and hit on `term` and `anywhere`. So a client branching on
`if not results` has a branch that practically never runs, and the real
failure, a confident low-relevance match, has no branch at all. That is why
retrieval needs [evaluation](retrieval-evaluation.md) rather than error
handling.

**The tradeoff to volunteer.** All of this was learned against a local server
with no auth, no network and no rate limit, which is the easiest integration
there is. It taught the contract questions well and taught nothing about
credentials expiring mid-run, pagination over a moving dataset, or a vendor
whose staging and production behaviour differ. Those need the real service, and
I would not claim them from a stdio pipe.

## How to prove it

**The artifact.** A client of yours with a misuse table, and whichever end you
control fixed so that failure travels on one channel.

**Three things to do, in order:**

1. Take an API you already integrate with and establish which field means
   failure and what the other does when they disagree. Predict first; this page
   exists because I got that wrong on a server I maintain.
2. Send your client six deliberately malformed requests and tabulate the
   replies. Twenty minutes, and it will find something.
3. Add a checkpoint to the longest extraction script you own. It prevents the
   most expensive failure in this area and the fix is an append.

**What makes it credible rather than decorative.** The client is a short script driving `docpack`'s `mcp_server/server.py` over
stdio. The two server defects are fixed in that file with the reasoning left
in comments. `tests/test_mcp_server.py` holds fourteen tests asserting on
`isError` rather than on message text, including one that a bad filter value
is distinguishable from an empty result. What is absent is any integration over a network: no
authentication, no rate limiting, no pagination, no third-party service. The
operational half of this concept is reasoned about rather than demonstrated, and
the [demonstrated](../demonstrated.md) page records it as partial on that basis.

## Related

- [Python for content automation](python-for-content.md), the proficiency underneath
- [Transforming content as data](content-data-transformation.md), what usually crosses the boundary
- [MCP](mcp.md), the server integrated against here
- [Retrieval evaluation](retrieval-evaluation.md), why a search client cannot rely on error handling
- [Security documentation](security-documentation.md), where credential handling gets enforced
