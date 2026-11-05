---
title: Coverage
summary: Every concept this guide covers, where it came from, and whether it is written
  yet.
diataxis: placeholder
audience: new-user
generated: true
---


# Coverage

**106 of 106 concepts written.** 0 drafted, 0 planned.

Each row names the concept, the posting line that put it on this list, and how
strong that claim is. `quoted` is a verbatim phrase from a posting. `derived`
means the posting requires the thing but these are not its words. `adjacent`
means neither posting names it and the named work is impossible without it.

Read that last column as a confidence rating on the concept's right to your time.

## Where this list comes from

- **90 of 106** concepts are backed by at least one verbatim quote.
- Claims by provenance: 90 quoted, 4 derived, 12 adjacent.

A concept with no `quoted` claim is still here on an argument, and the argument
is printed next to it so you can reject it.

## Information and knowledge architecture

| Concept | Tier | Effort | Time | Status | Why it is on this list |
|---|---|---|---|---|---|
| [Content models](concepts/content-model.md) | core | practise it | 4h | :material-check: complete | *nvidia, quoted:* content modeling, taxonomy, and metadata |
| [Diátaxis](concepts/diataxis.md) | core | read it | 2h | :material-check: complete | *both, adjacent:* The dominant framework for documentation structure. Neither posting names it; both describe the problem it solves. |
| [Information architecture](concepts/information-architecture.md) | core | practise it | 4h | :material-check: complete | *nvidia, quoted:* Information architecture skills: content modeling, taxonomy, and metadata for both navigation and machine retrieval |
| [Knowledge architecture](concepts/knowledge-architecture.md) | core | build something | 6h | :material-check: complete | *nvidia, quoted:* Collaborate with documentation leads on knowledge architecture |
| [Metadata for navigation and retrieval](concepts/metadata.md) | core | practise it | 3h | :material-check: complete | *nvidia, quoted:* metadata for both navigation and machine retrieval |
| [Playbooks and decision guides](concepts/playbooks.md) | core | practise it | 4h | :material-check: complete | *nvidia, quoted:* Capture tribal knowledge from engineering, product, and operations, and turn it into playbooks, decision guides, and ... |
| [Taxonomy and controlled vocabularies](concepts/taxonomy.md) | core | practise it | 3h | :material-check: complete | *nvidia, quoted:* content modeling, taxonomy, and metadata |
| [Content lifecycle and governance](concepts/content-lifecycle.md) | supporting | practise it | 3h | :material-check: complete | *nvidia, quoted:* automate the content lifecycle with LLMs: drafting, updating, auditing |
| [Findability and search design](concepts/findability.md) | supporting | practise it | 3h | :material-check: complete | *intel, quoted:* makes documentation discoverable and usable by both developers and AI assistants |
| [Retiring content](concepts/content-retirement.md) | supporting | practise it | 3h | :material-check: complete | *nvidia, quoted:* use the data to decide what to build, fix, or retire |
| [Security guidance as encoded standard](concepts/security-documentation.md) | supporting | practise it | 3h | :material-check: complete | *nvidia, quoted:* Encode standards (user stories, release readiness, onboarding, security guidance) into templates, validators, and gui... |
| [Single-sourcing and content reuse](concepts/single-sourcing.md) | supporting | practise it | 3h | :material-check: complete | *both, adjacent:* Neither posting mentions single-sourcing. The mechanism behind every claim about scaling documentation across products. |
| [Style guides and terminology management](concepts/style-guide.md) | supporting | read it | 2h | :material-check: complete | *nvidia, quoted:* as comfortable in Git, CI, or Python as in a style guide |

## Docs-as-code toolchain

| Concept | Tier | Effort | Time | Status | Why it is on this list |
|---|---|---|---|---|---|
| [Choosing a static site generator](concepts/static-site-generators.md) | core | practise it | 3h | :material-check: complete | *nvidia, quoted:* static site generators (Sphinx, MkDocs, Docusaurus, or similar) |
| [Docs-as-code](concepts/docs-as-code.md) | core | read it | 2h | :material-check: complete | *both, quoted:* Build and run docs-as-code pipelines: Git authoring, CI/CD builds, linting, link and code-sample validation, and publ... |
| [Generated API reference](concepts/api-reference-generation.md) | core | practise it | 4h | :material-check: complete | *intel, quoted:* Write and maintain reference documentation, tutorials, and sample walkthroughs that assume no prior context |
| [Git authoring workflows for writers](concepts/git-authoring.md) | core | practise it | 4h | :material-check: complete | *both, quoted:* Hands-on docs-as-code experience: Git, pull request review, Markdown/RST, static site generators |
| [Markdown and its dialects](concepts/markdown.md) | core | read it | 2h | :material-check: complete | *both, quoted:* Markdown/RST (NVIDIA); Git, Markdown or MDX, and doc build pipelines (Intel) |
| [MkDocs and Material](concepts/mkdocs.md) | core | practise it | 4h | :material-check: complete | *nvidia, quoted:* static site generators (Sphinx, MkDocs, Docusaurus, or similar) |
| [Sphinx](concepts/sphinx.md) | core | build something | 6h | :material-check: complete | *nvidia, quoted:* static site generators (Sphinx, MkDocs, Docusaurus, or similar) |
| [Docusaurus](concepts/docusaurus.md) | supporting | practise it | 5h | :material-check: complete | *nvidia, quoted:* static site generators (Sphinx, MkDocs, Docusaurus, or similar) |
| [Localization and translation pipelines](concepts/localization.md) | supporting | build something | 4h | :material-check: complete | *both, adjacent:* Neither posting mentions localization. Included because a platform documentation role at Intel or NVIDIA scale eventu... |
| [MDX](concepts/mdx.md) | supporting | practise it | 3h | :material-check: complete | *intel, quoted:* Hands on experience with docs-as-code workflows and documentation CI, including Git, Markdown or MDX |
| [OpenAPI and REST reference](concepts/openapi.md) | supporting | practise it | 4h | :material-check: complete | *both, adjacent:* Neither posting mentions OpenAPI. The standard contract format for any HTTP surface you will document. |
| [Versioned documentation](concepts/versioning.md) | supporting | practise it | 3h | :material-check: complete | *both, adjacent:* Neither posting mentions versioned docs. Unavoidable for any platform that ships releases, which is both of these. |
| [reStructuredText](concepts/restructuredtext.md) | supporting | practise it | 3h | :material-check: complete | *nvidia, quoted:* Markdown/RST |
| [Antora and AsciiDoc](concepts/antora.md) | context | practise it | 3h | :material-check: complete | *nvidia, adjacent:* Covered only by 'or similar' in NVIDIA's list of generators. Worth recognising, rarely worth choosing new. |

## Quality automation and documentation CI

| Concept | Tier | Effort | Time | Status | Why it is on this list |
|---|---|---|---|---|---|
| [Building a doc test harness](concepts/doc-test-harness.md) | core | build something | 6h | :material-check: complete | *nvidia, quoted:* Content quality automation you've built, such as Vale or custom linters, doc test harnesses, or freshness monitoring |
| [Code-sample validation](concepts/code-sample-validation.md) | core | build something | 5h | :material-check: complete | *intel, quoted:* link and code-sample validation |
| [Cold-start testing](concepts/coldstart-testing.md) | core | build something | 5h | :material-check: complete | *intel, quoted:* coldstart testing of quickstarts |
| [Documentation CI](concepts/documentation-ci.md) | core | practise it | 4h | :material-check: complete | *intel, quoted:* documentation CI |
| [Freshness monitoring](concepts/freshness-monitoring.md) | core | practise it | 4h | :material-check: complete | *nvidia, quoted:* with checks for freshness, code accuracy, and terminology drift, and human review where judgment matters |
| [GitHub Actions for docs](concepts/github-actions.md) | core | practise it | 4h | :material-check: complete | *both, derived:* CI/CD is named by both; GitHub Actions is the most common implementation of it. |
| [Link checking](concepts/link-checking.md) | core | read it | 2h | :material-check: complete | *intel, quoted:* link checking |
| [Prose linting with Vale](concepts/prose-linting.md) | core | practise it | 3h | :material-check: complete | *nvidia, quoted:* Content quality automation you've built, such as Vale or custom linters, doc test harnesses, or freshness monitoring |
| [Accessibility checks](concepts/accessibility.md) | supporting | practise it | 3h | :material-check: complete | *both, adjacent:* Neither posting mentions accessibility. Included because published content at either company is subject to it regardl... |
| [Detecting terminology drift](concepts/terminology-drift.md) | supporting | practise it | 3h | :material-check: complete | *nvidia, quoted:* checks for freshness, code accuracy, and terminology drift |
| [Doctests and executable docstrings](concepts/doctests.md) | supporting | practise it | 2h | :material-check: complete | *nvidia, quoted:* doc test harnesses |
| [Preview deployments and publishing](concepts/preview-deployments.md) | supporting | practise it | 3h | :material-check: complete | *nvidia, quoted:* and publishing |
| [Reviewing documentation](concepts/docs-review.md) | supporting | practise it | 3h | :material-check: complete | *nvidia, quoted:* Git, pull request review, Markdown/RST |
| [Writing custom linters](concepts/custom-linters.md) | supporting | build something | 5h | :material-check: complete | *nvidia, quoted:* Content quality automation you've built, such as Vale or custom linters |

## Golden paths and developer onboarding

| Concept | Tier | Effort | Time | Status | Why it is on this list |
|---|---|---|---|---|---|
| [Designing tutorials](concepts/tutorial-design.md) | core | practise it | 4h | :material-check: complete | *intel, quoted:* tutorial |
| [Golden paths](concepts/golden-paths.md) | core | build something | 5h | :material-check: complete | *intel, quoted:* Design and maintain golden paths and curriculum that take a developer from a clean environment to a working result |
| [Guided workflows](concepts/guided-workflows.md) | core | build something | 5h | :material-check: complete | *nvidia, quoted:* into templates, validators, and guided workflows rather than static documents |
| [Quickstarts that survive contact](concepts/quickstarts.md) | core | practise it | 3h | :material-check: complete | *intel, quoted:* coldstart testing of quickstarts |
| [Sample walkthroughs](concepts/sample-walkthroughs.md) | core | practise it | 3h | :material-check: complete | *intel, quoted:* sample walkthrough |
| [Templates and scaffolding](concepts/templates-scaffolding.md) | core | practise it | 3h | :material-check: complete | *nvidia, quoted:* encode standards into templates, validators, and guided workflows |
| [Reproducible environments](concepts/reproducible-environments.md) | supporting | build something | 4h | :material-check: complete | *intel, quoted:* take a developer from a clean environment to a working result |
| [Sample applications and galleries](concepts/sample-apps.md) | supporting | build something | 6h | :material-check: complete | *intel, quoted:* the sample-app gallery |

## AI-ready content and agents

| Concept | Tier | Effort | Time | Status | Why it is on this list |
|---|---|---|---|---|---|
| [Agent skills and context kits](concepts/agent-skills.md) | core | practise it | 4h | :material-check: complete | *nvidia, quoted:* agent skills and context kits |
| [Agent-ready content](concepts/agent-ready-content.md) | core | practise it | 4h | :material-check: complete | *nvidia, quoted:* Make knowledge AI-ready |
| [Agentic workflows](concepts/agentic-workflows.md) | core | build something | 6h | :material-check: complete | *nvidia, quoted:* structure and package content for RAG, internal assistants, and agentic workflows |
| [Chunking strategies](concepts/chunking.md) | core | build something | 5h | :material-check: complete | *nvidia, quoted:* structure and package content for RAG, internal assistants, and agentic workflows |
| [Documentation for coding agents](concepts/coding-agents.md) | core | practise it | 4h | :material-check: complete | *intel, quoted:* Optimize documentation for search (SEO and GEO) and for AI assistants and coding agents through agentready, LLMdigest... |
| [Documentation-backed AI assistants](concepts/ai-assistants.md) | core | build something | 8h | :material-check: complete | *nvidia, quoted:* structure and package content for RAG, internal assistants, and agentic workflows |
| [Embeddings](concepts/embeddings.md) | core | practise it | 4h | :material-check: complete | *nvidia, derived:* Required by any RAG pipeline, and NVIDIA names RAG pipelines twice. |
| [Evaluating retrieval](concepts/retrieval-evaluation.md) | core | build something | 6h | :material-check: complete | *nvidia, quoted:* evaluation sets for answer accuracy |
| [Generative engine optimization](concepts/geo.md) | core | practise it | 3h | :material-check: complete | *intel, quoted:* documentation optimized for SEO and GEO |
| [Grounding and citation](concepts/grounding.md) | core | practise it | 4h | :material-check: complete | *nvidia, quoted:* prompting, retrieval and grounding, output evaluation |
| [LLMs in the content lifecycle](concepts/llm-content-lifecycle.md) | core | build something | 6h | :material-check: complete | *nvidia, quoted:* automate the content lifecycle with LLMs: drafting, updating, auditing |
| [Model Context Protocol](concepts/mcp.md) | core | build something | 5h | :material-check: complete | *nvidia, quoted:* Ways to stand out: experience building RAG pipelines, AI assistants, MCP servers |
| [Output evaluation](concepts/output-evaluation.md) | core | build something | 6h | :material-check: complete | *nvidia, quoted:* prompting, retrieval and grounding, output evaluation |
| [Prompting for content work](concepts/prompting.md) | core | practise it | 3h | :material-check: complete | *nvidia, quoted:* Practical experience applying LLMs to content workflows (prompting, retrieval and grounding, output evaluation) |
| [RAG pipelines](concepts/rag.md) | core | build something | 8h | :material-check: complete | *nvidia, quoted:* Ways to stand out: experience building RAG pipelines, AI assistants, MCP servers |
| [Vector stores and hybrid search](concepts/vector-stores.md) | core | build something | 5h | :material-check: complete | *nvidia, derived:* The retrieval half of a RAG pipeline, which NVIDIA names as a way to stand out. |
| [llms.txt and llms-full.txt](concepts/llms-txt.md) | core | read it | 2h | :material-check: complete | *nvidia, quoted:* including llms.txt, MCP-accessible sources, agent skills and context kits, and evaluation sets for answer accuracy |
| [Crawlability and the agent-ready front door](concepts/crawlability.md) | supporting | practise it | 3h | :material-check: complete | *intel, quoted:* site navigation, and a crawlable, agent-ready front door |
| [Hallucination and guardrails](concepts/hallucination-guardrails.md) | supporting | build something | 4h | :material-check: complete | *nvidia, quoted:* sound judgment about where AI can be trusted |
| [SEO for documentation](concepts/seo-for-docs.md) | supporting | practise it | 3h | :material-check: complete | *intel, quoted:* documentation optimized for SEO and GEO |
| [Structured data and JSON-LD](concepts/structured-data.md) | supporting | practise it | 3h | :material-check: complete | *intel, derived:* Required by 'a crawlable, agent-ready front door': the machine-readable half of SEO and GEO. |

## Measurement and feedback

| Concept | Tier | Effort | Time | Status | Why it is on this list |
|---|---|---|---|---|---|
| [Documentation analytics](concepts/docs-analytics.md) | core | practise it | 4h | :material-check: complete | *intel, quoted:* Instrument documentation analytics and convert findings into improvements to docs, samples, and tooling |
| [Measuring AI answer quality](concepts/ai-answer-quality.md) | core | build something | 5h | :material-check: complete | *nvidia, quoted:* AI answer quality |
| [Repeat-question analysis](concepts/repeat-questions.md) | core | practise it | 3h | :material-check: complete | *nvidia, quoted:* repeat questions |
| [Support deflection](concepts/support-deflection.md) | core | practise it | 3h | :material-check: complete | *nvidia, quoted:* Measurable reductions in support load or onboarding time through self-service knowledge systems |
| [Time to first success](concepts/time-to-first-success.md) | core | practise it | 3h | :material-check: complete | *nvidia, quoted:* measure time-to-first-success, support deflection, repeat questions, and AI answer quality |
| [Search and query log analysis](concepts/search-log-analysis.md) | supporting | practise it | 3h | :material-check: complete | *nvidia, adjacent:* Not named. The input that turns a hand-written evaluation set into a representative one. |
| [Turning developer feedback into changes](concepts/developer-feedback-loops.md) | supporting | practise it | 3h | :material-check: complete | *intel, quoted:* Ability to translate developer feedback into documentation, samples, and product improvements |

## Developer education and curriculum

| Concept | Tier | Effort | Time | Status | Why it is on this list |
|---|---|---|---|---|---|
| [Cognitive load in technical content](concepts/cognitive-load.md) | core | practise it | 3h | :material-check: complete | *intel, adjacent:* Not named. The mechanism behind every claim about reaching first success in minutes. |
| [Instructional design for developers](concepts/instructional-design.md) | core | practise it | 5h | :material-check: complete | *intel, quoted:* Design and maintain golden paths and curriculum that take a developer from a clean environment to a working result |
| [Learning paths and curriculum](concepts/learning-paths.md) | core | build something | 5h | :material-check: complete | *intel, quoted:* structured learning paths |
| [Assessment and checks for understanding](concepts/assessment.md) | supporting | practise it | 3h | :material-check: complete | *intel, adjacent:* Not named. The counterpart to cold-start testing: how you know the curriculum worked. |
| [Developer advocacy](concepts/developer-advocacy.md) | supporting | practise it | 3h | :material-check: complete | *intel, quoted:* Partner with engineering, product, and developer advocates so each new capability ships with tested documentation |
| [Publishing in public](concepts/publishing-in-public.md) | supporting | read it | 4h | :material-check: complete | *nvidia, quoted:* Open source contributions or published work on docs-as-code, AI-assisted documentation, or knowledge engineering |
| [Workshops and hands-on labs](concepts/workshops.md) | supporting | practise it | 4h | :material-check: complete | *both, adjacent:* Neither posting mentions workshops. A standard developer-relations deliverable. |
| [Screencasts and video](concepts/screencasts.md) | context | practise it | 4h | :material-check: complete | *both, adjacent:* Neither posting mentions video. A common secondary deliverable in developer-relations roles. |

## Automation with Python

| Concept | Tier | Effort | Time | Status | Why it is on this list |
|---|---|---|---|---|---|
| [Integrating with APIs](concepts/api-integration.md) | core | practise it | 4h | :material-check: complete | *nvidia, quoted:* automate content tasks, transform data, and integrate with APIs |
| [Python for content automation](concepts/python-for-content.md) | core | practise it | 5h | :material-check: complete | *nvidia, quoted:* Working proficiency in Python or similar to automate content tasks, transform data, and integrate with APIs |
| [Transforming content as data](concepts/content-data-transformation.md) | core | practise it | 4h | :material-check: complete | *nvidia, quoted:* Working proficiency in Python or similar to automate content tasks, transform data, and integrate with APIs |

## Domain context

| Concept | Tier | Effort | Time | Status | Why it is on this list |
|---|---|---|---|---|---|
| [GPU computing and CUDA](concepts/gpu-computing.md) | context | practise it | 4h | :material-check: complete | *nvidia, quoted:* Documentation experience in graphics, simulation, robotics, or real-time systems |
| [Inference serving and microservices](concepts/inference-serving.md) | context | practise it | 4h | :material-check: complete | *intel, quoted:* including inference microservices and the agentic toolkit |
| [OpenUSD and Omniverse](concepts/usd-omniverse.md) | context | practise it | 4h | :material-check: complete | *nvidia, quoted:* familiarity with USD, Omniverse, Isaac Sim, or ROS |
| [Reading an AI software stack](concepts/ai-stack.md) | context | practise it | 4h | :material-check: complete | *intel, quoted:* Python literacy sufficient to run and validate AI samples, with working familiarity with the AI software stack |
| [Real-time and graphics systems](concepts/realtime-systems.md) | context | practise it | 4h | :material-check: complete | *nvidia, quoted:* Documentation experience in graphics, simulation, robotics, or real-time systems |
| [Robotics simulation, Isaac Sim and ROS](concepts/robotics-sim.md) | context | practise it | 4h | :material-check: complete | *nvidia, quoted:* Documentation experience in graphics, simulation, robotics, or real-time systems; familiarity with USD, Omniverse, Is... |

## Ways of working

| Concept | Tier | Effort | Time | Status | Why it is on this list |
|---|---|---|---|---|---|
| [A systems mindset](concepts/systems-mindset.md) | core | practise it | 2h | :material-check: complete | *nvidia, quoted:* A systems mindset: you fix the class of problem, not just the instance |
| [Extracting tribal knowledge](concepts/sme-interviews.md) | core | practise it | 3h | :material-check: complete | *nvidia, quoted:* Turning documentation, standards, and tribal knowledge into tooling, templates, and self-service paths |
| [Giving architecture owners implementation feedback](concepts/implementation-feedback.md) | core | practise it | 3h | :material-check: complete | *nvidia, quoted:* sharing implementation feedback (what works, breaks, and scales) to refine content models, information architecture, ... |
| [Judging where AI can be trusted](concepts/ai-trust-judgment.md) | core | practise it | 4h | :material-check: complete | *nvidia, quoted:* sound judgment about where AI can be trusted |
| [Reading code to verify accuracy](concepts/reading-code-to-verify.md) | core | practise it | 5h | :material-check: complete | *nvidia, quoted:* Enough technical depth to read code and APIs, verify accuracy, and write working examples |
| [Release readiness for documentation](concepts/release-readiness.md) | core | practise it | 4h | :material-check: complete | *nvidia, quoted:* Encode standards (user stories, release readiness, onboarding, security guidance) into templates, validators, and gui... |
| [Technical writing as a craft](concepts/technical-writing.md) | core | practise it | 8h | :material-check: complete | *intel, quoted:* Strong technical writing and information architecture skills for developer documentation |
| [Treating docs, setup and samples as one product](concepts/docs-as-product.md) | core | practise it | 3h | :material-check: complete | *intel, quoted:* Treats setup, runnable samples, and docs as one product |
| [Prioritizing documentation work](concepts/docs-prioritization.md) | supporting | practise it | 3h | :material-check: complete | *nvidia, quoted:* use the data to decide what to build, fix, or retire |
| [User stories as a documentation standard](concepts/user-stories.md) | supporting | read it | 2h | :material-check: complete | *nvidia, quoted:* Encode standards (user stories, release readiness, onboarding, security guidance) into templates |
| [Working with engineers as sources](concepts/working-with-engineers.md) | supporting | practise it | 3h | :material-check: complete | *nvidia, quoted:* Partner with Engineering, Product, Security, Developer Relations, and Partner Programs so every release ships documen... |
| [Documentation for partners and internal teams](concepts/partner-documentation.md) | context | practise it | 3h | :material-check: complete | *nvidia, quoted:* deliver Simulation Technology knowledge to developers, partners, internal teams, and the AI agents that increasingly ... |

## The page contract

Every concept page answers the same seven questions in the same order, and CI
rejects one that does not:

1. **What it is**
2. **Why the job asks for it**
3. **The golden path**
4. **Reference**
5. **How to talk about it**
6. **How to prove it**
7. **Related**

That is a content model applied to a learning corpus rather than to a product's
documentation. The payoff is that the thirtieth page costs a reader nothing to
navigate, because they learned the shape on the first.
