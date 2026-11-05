---
title: Model Context Protocol
summary: A JSON-RPC interface that lets an agent call your documentation as tools instead of being handed a blob of text.
diataxis: explanation
audience: developer
concept: mcp
tags: [ai, core]
---

# Model Context Protocol

`core` · difficulty 3 · 5h

> Ways to stand out: experience building RAG pipelines, AI assistants, MCP servers, or agent skill and context libraries backed by documentation

> Source: nvidia posting, verbatim

**Prerequisites:** [Agent-ready content](agent-ready-content.md)

**Leads to:** [Agent skills and context kits](agent-skills.md), [Agentic workflows](agentic-workflows.md)

## What it is

A protocol for exposing data and capabilities to a language model as callable
tools. An MCP server declares what it can do, a client connects, and the model
decides when to call which tool with which arguments.

For documentation, it means an agent can *query* your corpus mid-task instead of
being given a pre-selected chunk of it. The difference matters: the agent gets
to decide what it needs, and to ask twice.

## Why the job asks for it

NVIDIA names it twice. Once in the AI-ready list, "MCP-accessible sources", and
once under ways to stand out, "MCP servers ... backed by documentation". That
repetition is a signal: they want the interface, not just the content.

The reason this is worth a `core` slot rather than being filed as a tool choice:
**it serves a consumer none of the other artifacts do.**
[llms.txt](llms-txt.md) serves a model that can fetch URLs.
[Chunks](chunking.md) serve a retriever that already has a query. An agent
working inside an editor, halfway through a task, needs neither of those. It
needs to ask a specific question, get a specific answer, and ask a follow-up,
with filters it chooses.

On a Tuesday this is the difference between two failure modes. With a flat
context dump, a coding agent gets 40,000 characters of your docs and uses the
wrong page because it was first. With an MCP server, the agent calls
`search_docs(query="batch size", diataxis="how-to")`, gets three chunks, and
if they are wrong it can call again with a different filter. **The second
system can recover from a bad first guess.**

## The golden path

Build a working MCP server over a documentation tree, dependency-free, and
drive it with handwritten JSON-RPC. Forty-five minutes.

**Step 1: a corpus with metadata worth filtering on**

```bash
mkdir -p mcp-drill/docs && cd mcp-drill
cat > docs/batch-size.md <<'EOF'
---
title: Choose a batch size
summary: Pick a batch size from latency targets, GPU memory and quantisation.
kind: how-to
audience: developer
---
# Choose a batch size

Set `batch_size`. The default is 32.

## If latency matters

Use 1 or 2. Batching at 32 adds roughly 200ms at p99.
EOF

cat > docs/why-batching.md <<'EOF'
---
title: Why batching helps throughput
summary: The reasoning behind batched inference and what it costs in latency.
kind: explanation
audience: developer
---
# Why batching helps throughput

A GPU is more efficient per item on a larger batch.

## What it costs

Every request waits for the batch to fill.
EOF

cat > docs/cli.md <<'EOF'
---
title: CLI reference
summary: Every command, flag, default and exit code.
kind: reference
audience: developer
---
# CLI reference

## Exit codes

`0` success, `1` configuration error, `2` bad arguments.
EOF
ls docs/
```

**Step 2: the server**

Three tools, JSON-RPC over stdio, no dependencies beyond PyYAML.

```bash
cat > server.py <<'PY'
#!/usr/bin/env python3
"""An MCP server exposing a documentation tree to an agent.

Deliberately dependency-free and small enough to read in one sitting. It
implements the subset of MCP a documentation server actually needs:
`initialize`, `tools/list` and `tools/call`.

The design decision worth noticing is the tool set. Three tools, not one:

  list_pages    the map. An agent with no idea what exists starts here.
  search_docs   the query, filterable by the kind of answer wanted.
  get_page      the full text, once the agent knows which page it needs.

A single `search` tool forces an agent to guess its query before it knows
what the corpus contains, which is the same mistake as serving only
llms.txt or only chunks.
"""
import json
import re
import sys
from pathlib import Path

import yaml

PROTOCOL_VERSION = "2024-11-05"
HEADING = re.compile(r"^(#{1,6}) +(.*?)\s*$")
FENCE = re.compile(r"^\s*(```|~~~)")

KINDS = ["tutorial", "how-to", "reference", "explanation"]

TOOLS = [
    {
        "name": "list_pages",
        "description": (
            "List every documentation page with its title, summary, kind and "
            "audience. Call this first to see what the corpus covers before searching."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {"kind": {"type": "string", "enum": KINDS}},
        },
    },
    {
        "name": "search_docs",
        "description": (
            "Keyword search across documentation sections. Filter by kind to get "
            "the right sort of answer: 'how-to' for instructions, 'reference' for "
            "exact values, 'explanation' for reasoning."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "kind": {"type": "string", "enum": KINDS},
                "limit": {"type": "integer", "default": 3},
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_page",
        "description": "Return the full Markdown of one page by its path.",
        "inputSchema": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
    },
]


def sections(body: str):
    """Split a page into (heading trail, text), ignoring fenced blocks."""
    trail, buffer, out, in_fence = [], [], [], False
    for line in body.splitlines():
        if FENCE.match(line):
            in_fence = not in_fence
            buffer.append(line)
            continue
        match = None if in_fence else HEADING.match(line)
        if match:
            if buffer:
                out.append((" > ".join(trail), "\n".join(buffer).strip()))
            buffer = []
            depth = len(match.group(1))
            trail = trail[: depth - 1] + [match.group(2)]
        else:
            buffer.append(line)
    if buffer:
        out.append((" > ".join(trail), "\n".join(buffer).strip()))
    return [(c, t) for c, t in out if t]


class DocsServer:
    def __init__(self, docs: Path) -> None:
        self.docs = docs
        self.pages = []
        for path in sorted(docs.glob("*.md")):
            text = path.read_text(encoding="utf-8")
            front, _, body = text.partition("---\n")[2].partition("\n---\n")
            self.pages.append((path, yaml.safe_load(front), body))

    # ------------------------------------------------------------ tools

    def list_pages(self, kind=None):
        rows = []
        for path, meta, _ in self.pages:
            if kind and meta.get("kind") != kind:
                continue
            rel = path.relative_to(self.docs).as_posix()
            rows.append(
                f"- `{rel}` [{meta['kind']}, {meta['audience']}] "
                f"**{meta['title']}**: {meta['summary']}"
            )
        return "\n".join(rows) if rows else "No pages match that filter."

    def search_docs(self, query, kind=None, limit=3):
        terms = [t for t in re.findall(r"[a-z0-9]+", query.lower()) if len(t) > 2]
        hits = []
        for path, meta, body in self.pages:
            if kind and meta.get("kind") != kind:
                continue
            rel = path.relative_to(self.docs).as_posix()
            for crumb, text in sections(body):
                # The heading trail and the summary are searched alongside the
                # text, because the reader's vocabulary is often only there.
                hay = f"{meta['title']} {meta['summary']} {crumb} {text}".lower()
                score = sum(hay.count(t) for t in terms)
                if score:
                    # The crumb already begins with the page's H1, so the
                    # title is not repeated here. Rendering both produces
                    # "Choose a batch size > Choose a batch size > ...",
                    # which wastes the agent's context on every result.
                    hits.append((
                        score,
                        f"## {crumb}\n"
                        f"source: {rel} ({meta['kind']}, for {meta['audience']})\n\n"
                        f"{text}",
                    ))
        hits.sort(key=lambda h: -h[0])
        if not hits:
            return f"No matches for {query!r}."
        return "\n\n---\n\n".join(text for _, text in hits[:limit])

    def get_page(self, path):
        target = (self.docs / path).resolve()
        # Path traversal guard. An agent is an untrusted caller: it will
        # eventually ask for ../../etc/passwd, not maliciously but because a
        # model guessed a path.
        if not target.is_relative_to(self.docs.resolve()):
            return "Error: path escapes the documentation tree."
        if not target.exists():
            available = ", ".join(
                p.relative_to(self.docs).as_posix() for p, _, _ in self.pages
            )
            return f"Error: no page at {path!r}. Available: {available}"
        return target.read_text(encoding="utf-8")

    # --------------------------------------------------------- dispatch

    def call_tool(self, name, args):
        if name == "list_pages":
            return self.list_pages(args.get("kind"))
        if name == "search_docs":
            return self.search_docs(
                args["query"], args.get("kind"), int(args.get("limit", 3))
            )
        if name == "get_page":
            return self.get_page(args["path"])
        raise KeyError(f"unknown tool: {name}")

    def handle(self, request):
        method, req_id = request.get("method"), request.get("id")
        if req_id is None:
            return None  # a notification

        def ok(result):
            return {"jsonrpc": "2.0", "id": req_id, "result": result}

        if method == "initialize":
            return ok({
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "widget-docs", "version": "0.1.0"},
            })
        if method == "tools/list":
            return ok({"tools": TOOLS})
        if method == "tools/call":
            params = request.get("params", {})
            try:
                text = self.call_tool(params["name"], params.get("arguments", {}))
            except Exception as exc:  # report to the client, never crash
                return ok({
                    "content": [{"type": "text", "text": f"Error: {exc}"}],
                    "isError": True,
                })
            return ok({"content": [{"type": "text", "text": text}], "isError": False})

        return {"jsonrpc": "2.0", "id": req_id,
                "error": {"code": -32601, "message": f"method not found: {method}"}}


def main() -> int:
    server = DocsServer(Path(sys.argv[1] if len(sys.argv) > 1 else "docs"))
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            continue
        response = server.handle(request)
        if response is not None:
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
PY
echo "server written"
```

**Step 3: drive it by hand, which is how you debug it**

```bash
cat > session.jsonl <<'EOF'
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}
{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}
{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"list_pages","arguments":{}}}
{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"search_docs","arguments":{"query":"latency","kind":"how-to"}}}
{"jsonrpc":"2.0","id":5,"method":"tools/call","params":{"name":"search_docs","arguments":{"query":"latency","kind":"explanation"}}}
{"jsonrpc":"2.0","id":6,"method":"tools/call","params":{"name":"get_page","arguments":{"path":"../../../etc/passwd"}}}
{"jsonrpc":"2.0","id":7,"method":"tools/call","params":{"name":"nonexistent","arguments":{}}}
EOF

python3 server.py docs < session.jsonl | python3 -c "
import json, sys
for line in sys.stdin:
    r = json.loads(line)
    print(f\"--- id {r['id']} ---\")
    if 'error' in r:
        print('  JSON-RPC error:', r['error']['message']); continue
    result = r['result']
    if 'serverInfo' in result:
        print('  initialized:', result['serverInfo'])
    elif 'tools' in result:
        print('  tools:', [t['name'] for t in result['tools']])
    else:
        flag = ' [isError]' if result.get('isError') else ''
        print(f\"  content{flag}:\")
        for line2 in result['content'][0]['text'].splitlines()[:6]:
            print('   ', line2)
    print()
"
```

**Step 4: the thing that makes this worth building**

Compare ids 4 and 5 in the output above. Same query, different `kind`, different
answer: the how-to filter returns the instruction, the explanation filter returns
the reasoning. **An agent can choose which kind of answer it needs**, and change
its mind. That is not available from a flat context dump, and it is the entire
argument for the interface.

Then look at id 6 and id 7. The traversal attempt returns an error string rather
than a file, and the unknown tool returns `isError` rather than killing the
server. An agent is an untrusted, unreliable caller and the server has to assume
it.

**What you built.** A server an agent can actually navigate: a map before a
search, errors returned as results rather than as crashes, and a traversal
attempt that fails safely instead of serving a file outside the corpus.

## Reference

### The protocol surface a docs server needs

| Method | Purpose | Required |
|---|---|---|
| `initialize` | Handshake, declares capabilities and protocol version | Yes |
| `tools/list` | What this server can do, with JSON Schema per tool | Yes |
| `tools/call` | Invoke a tool, return content blocks | Yes |
| `resources/list`, `resources/read` | Expose documents as addressable resources | Optional |
| `prompts/list`, `prompts/get` | Reusable prompt templates | Optional |

Tools are enough for a documentation server. Resources are an alternative model
where the client browses rather than queries, and for a large corpus querying
wins.

### Tool design, which is where the quality is

| Rule | Why |
|---|---|
| Three tools: map, search, fetch | An agent that cannot list first has to guess its query |
| Put the filter vocabulary in the enum | The model sees the valid values and uses them |
| Say in the description *when* to use each filter | "how-to for instructions, reference for exact values" |
| Return the source path with every result | The agent needs to cite, and the human needs to verify |
| Return an error string, never raise | A crash ends the session; a message lets the agent retry |
| Keep responses small | Every result consumes the agent's context |

The third row is the highest-leverage thing on this page. **The tool
description is a prompt.** `"Filter by kind"` tells a model nothing;
`"'how-to' for instructions, 'reference' for exact values"` tells it how to
choose, and measurably changes which filter it picks.

### MCP against the alternatives

| Approach | Agent can query | Agent can filter | Scales | Needs a running process |
|---|---|---|---|---|
| Paste docs into context | No | No | No | No |
| [llms.txt](llms-txt.md) | Fetches, cannot query | No | Partly | No |
| [RAG endpoint](rag.md) | Yes | If you built it | Yes | Yes |
| MCP server | Yes | Yes, declaratively | Yes | Yes |

MCP and RAG are not alternatives. A production docs MCP server usually *wraps*
retrieval: the tool is the interface, the retrieval is the implementation.

### Security, because an agent is an untrusted caller

| Risk | Mitigation |
|---|---|
| Path traversal in `get_page` | Resolve and check `is_relative_to`, as above |
| Leaking restricted content | Filter by the caller's tier; see [partner documentation](partner-documentation.md) |
| Unbounded responses | Cap `limit`, cap returned length |
| Prompt injection from page content | Treat page text as data; never let it instruct the server |
| Crash as denial of service | Catch everything in `tools/call` |

The third and fifth are the ones people skip, and the first is the one that
actually gets attempted, usually by accident.

## How to talk about it

**What a competent answer sounds like.** Lead with the consumer and the recovery
property. "MCP serves an agent working mid-task, which llms.txt and a chunk dump
do not. It calls `search_docs` with a kind filter, gets three results, and if
they are wrong it calls again with a different filter. A flat context dump cannot
recover from a bad first guess. I expose three tools, a map, a search and a
fetch, because an agent that cannot list the corpus first has to guess its query
before it knows what exists."

**The follow-up is "how does the model know which filter to use",** and the
answer is the thing most people miss: **the tool description is a prompt.**
Writing `"'how-to' for instructions, 'reference' for exact values,
'explanation' for reasoning"` instead of `"filter by kind"` changes the model's
behaviour, because that text is what it reads when deciding. Tool descriptions
are documentation written for a model, which is a genuinely nice thing to point
out in a documentation interview.

**The tradeoff to volunteer.** An MCP server is a running process with an
operational burden that a static file does not have: it has to be deployed,
monitored, versioned and secured, and it only helps clients that speak MCP.
`llms.txt` is a file on a web server that works with anything that can fetch a
URL. For a corpus where most consumption is a model fetching pages, the file is
the better investment. MCP earns its cost when agents are doing multi-step work
against your docs, which is exactly NVIDIA's "agentic workflows" and is not
every situation.

**One sharper point.** The strongest observation is that **MCP makes your content
model externally visible, and therefore externally tested.** The `kind` enum
appears in the tool schema, so a model's filter choices become a measurable
signal about whether your taxonomy makes sense. If agents consistently pick
`reference` for questions your corpus answers in `how-to` pages, that is
evidence about your [content model](content-model.md) that no internal review
would produce. Treating the MCP schema as a probe into your information
architecture is a more sophisticated position than treating it as a delivery
mechanism.

## How to prove it

**The artifact.** A working server, driven by a committed JSON-RPC session file,
including the traversal attempt and the unknown-tool call. The error cases are
what distinguish it from a tutorial copy.

**Three things to do, in order:**

1. **Run the golden path.** Keep `session.jsonl`: a committed transcript showing
   initialize, list, two filtered searches and two failures is a two-minute
   demonstration and proves it runs.
2. **Write the tool descriptions twice.** Once as `"filter by kind"`, once as
   the guidance version, and connect it to a real client to see whether the
   filter choices change. That is a small experiment nobody does.
3. **Add the tier filter** from [partner documentation](partner-documentation.md)
   if the corpus has restricted content. An MCP server over a mixed-visibility
   corpus with no per-caller filtering is an access-control hole, and noticing
   that is worth more than the server itself.

**What makes it credible rather than decorative.** Standing up an MCP server from a template proves
little. One with three deliberately chosen tools, descriptions written as
prompts, a path-traversal guard, errors returned rather than raised, and a
committed transcript demonstrates that you designed it.

## Related

- [Agent skills and context kits](agent-skills.md), the instructions that go alongside
- [Agentic workflows](agentic-workflows.md), what agents do with this
- [llms.txt and llms-full.txt](llms-txt.md), the cheaper artifact for a different consumer
- [RAG pipelines](rag.md), what a production server wraps
