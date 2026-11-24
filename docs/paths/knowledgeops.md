---
title: The KnowledgeOps path
summary: Making a corpus answerable by machines, and knowing whether it worked.
diataxis: placeholder
audience: new-user
generated: true
---


# The KnowledgeOps path

**Who this is for.** Someone responsible for making a knowledge base usable by AI assistants and agents.

Making a corpus answerable by machines, and knowing whether it worked.

**17 concepts, roughly 83 hours.** The order matters:
each step assumes the ones above it.

**Assumed before step 1.** This path does not teach [Information architecture](../concepts/information-architecture.md), [Templates and scaffolding](../concepts/templates-scaffolding.md), [Documentation analytics](../concepts/docs-analytics.md). Each step below repeats what it assumes.

**Shared with other paths.** 7 of these steps, roughly 30 hours, also appear in another path. Each is marked below; if you have done it there, skip it here.

## 1. [Content models](../concepts/content-model.md)

`core` · practise it · 4h

Defining the types of content your team writes and the fields each one must carry.

Assumes, from outside this path: [Information architecture](../concepts/information-architecture.md).

Also in: [A working result in a weekend](prove-it.md), [The content architect](content-architect.md).

## 2. [Metadata for navigation and retrieval](../concepts/metadata.md)

`core` · practise it · 3h

Tagging content so navigation, search and AI retrieval can all find the right page.

Builds on, earlier in this path: Content models.

Also in: [The content architect](content-architect.md).

## 3. [Agent-ready content](../concepts/agent-ready-content.md)

`core` · practise it · 4h

Structuring knowledge so AI assistants and agents can use it as reliably as people can.

Builds on, earlier in this path: Content models, Metadata for navigation and retrieval.

## 4. [llms.txt and llms-full.txt](../concepts/llms-txt.md)

`core` · read it · 2h

Publishing machine-readable entry points to your docs, such as llms.txt, for AI tools to consume.

Builds on, earlier in this path: Agent-ready content.

Also in: [A working result in a weekend](prove-it.md).

## 5. [Documentation for coding agents](../concepts/coding-agents.md)

`core` · practise it · 4h

Making documentation usable by coding agents as well as by search engines and people.

Builds on, earlier in this path: Agent-ready content.

## 6. [Chunking strategies](../concepts/chunking.md)

`core` · build something · 5h

Splitting content into pieces a RAG system, internal assistant or agent can retrieve on their own.

Builds on, earlier in this path: Agent-ready content.

Also in: [A working result in a weekend](prove-it.md).

## 7. [Embeddings](../concepts/embeddings.md)

`core` · practise it · 4h

Turning content into vectors so it can be searched by meaning, the first step of any RAG pipeline.

Builds on, earlier in this path: Chunking strategies.

## 8. [Vector stores and hybrid search](../concepts/vector-stores.md)

`core` · build something · 5h

Storing and searching embedded content, alone or alongside keyword search: the retrieval half of RAG.

Builds on, earlier in this path: Embeddings.

## 9. [RAG pipelines](../concepts/rag.md)

`core` · build something · 8h

Building and maintaining pipelines that answer questions from your documentation.

Builds on, earlier in this path: Chunking strategies, Vector stores and hybrid search.

## 10. [Grounding and citation](../concepts/grounding.md)

`core` · practise it · 4h

Making AI answers cite and stay within the documentation they draw on.

Builds on, earlier in this path: RAG pipelines.

## 11. [Documentation-backed AI assistants](../concepts/ai-assistants.md)

`core` · build something · 8h

Building and feeding assistants that answer questions from your documentation.

Builds on, earlier in this path: RAG pipelines, Grounding and citation.

## 12. [Evaluating retrieval](../concepts/retrieval-evaluation.md)

`core` · build something · 6h

Building question sets that measure whether retrieval finds the right content.

Builds on, earlier in this path: RAG pipelines.

Also in: [A working result in a weekend](prove-it.md).

## 13. [Output evaluation](../concepts/output-evaluation.md)

`core` · build something · 6h

Measuring whether LLM output in your content workflows is accurate and usable.

Builds on, earlier in this path: Grounding and citation, Evaluating retrieval.

## 14. [Model Context Protocol](../concepts/mcp.md)

`core` · build something · 5h

Exposing documentation and tools to AI assistants through Model Context Protocol servers.

Builds on, earlier in this path: Agent-ready content.

Also in: [A working result in a weekend](prove-it.md).

## 15. [Agent skills and context kits](../concepts/agent-skills.md)

`core` · practise it · 4h

Packaging instructions and context so agents can do a task the way your team does it.

Builds on, earlier in this path: Model Context Protocol.

Assumes, from outside this path: [Templates and scaffolding](../concepts/templates-scaffolding.md).

## 16. [Agentic workflows](../concepts/agentic-workflows.md)

`core` · build something · 6h

Structuring content so agents can carry out multi-step tasks from it.

Builds on, earlier in this path: Model Context Protocol, Agent skills and context kits.

## 17. [Measuring AI answer quality](../concepts/ai-answer-quality.md)

`core` · build something · 5h

Measuring how often an AI assistant answers correctly from your documentation.

Builds on, earlier in this path: Output evaluation.

Assumes, from outside this path: [Documentation analytics](../concepts/docs-analytics.md).

Also in: [Prove the outcomes](prove-the-outcomes.md).
