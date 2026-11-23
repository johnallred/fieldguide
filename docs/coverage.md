---
title: Coverage
summary: Every concept this guide covers, where it shows up in the work, and whether
  it is written yet.
diataxis: placeholder
audience: new-user
generated: true
---


# Coverage

**114 of 114 concepts written.** 0 drafted, 0 planned.

Each row names the concept and the day-to-day work that needs it.

## Where this list comes from

- **114 of 114** concepts name the work that needs them.

That line is printed next to each concept, so a reader can judge whether it
earns their time rather than taking the list on trust.

## Information and knowledge architecture

| Concept | Tier | Effort | Time | Status | Where it shows up in the work |
|---|---|---|---|---|---|
| [Content models](concepts/content-model.md) | core | practise it | 4h | :material-check: complete | Defining the types of content your team writes and the fields each one must carry. |
| [Diátaxis](concepts/diataxis.md) | core | read it | 2h | :material-check: complete | Deciding whether a page is a tutorial, a how-to, reference or explanation, and keeping it to one of them. |
| [Information architecture](concepts/information-architecture.md) | core | practise it | 4h | :material-check: complete | Deciding how content is modelled, classified and tagged so people can navigate it and machines can retrieve it. |
| [Knowledge architecture](concepts/knowledge-architecture.md) | core | build something | 6h | :material-check: complete | Working with documentation leads on how knowledge is organised across products, teams and sources. |
| [Metadata for navigation and retrieval](concepts/metadata.md) | core | practise it | 3h | :material-check: complete | Tagging content so navigation, search and AI retrieval can all find the right page. |
| [Playbooks and decision guides](concepts/playbooks.md) | core | practise it | 4h | :material-check: complete | Turning tribal knowledge from engineering, product and operations into playbooks and decision guides. |
| [Taxonomy and controlled vocabularies](concepts/taxonomy.md) | core | practise it | 3h | :material-check: complete | Agreeing the terms content is classified by, and keeping that vocabulary closed and consistent. |
| [Content lifecycle and governance](concepts/content-lifecycle.md) | supporting | practise it | 3h | :material-check: complete | Running content from draft to update to audit to retirement, increasingly with LLM help at each stage. |
| [Content migration](concepts/content-migration.md) | supporting | build something | 6h | :material-check: complete | Moving a documentation corpus from a wiki or CMS into docs-as-code, deciding page by page what moves, merges or goes,... |
| [Findability and search design](concepts/findability.md) | supporting | practise it | 3h | :material-check: complete | Making sure developers and AI assistants can both find and use the page they need. |
| [Retiring content](concepts/content-retirement.md) | supporting | practise it | 3h | :material-check: complete | Deciding what to retire, and removing it without breaking what links to it. |
| [Security guidance as encoded standard](concepts/security-documentation.md) | supporting | practise it | 3h | :material-check: complete | Encoding security guidance into templates, validators and workflows rather than static pages. |
| [Single-sourcing and content reuse](concepts/single-sourcing.md) | supporting | practise it | 3h | :material-check: complete | Writing a fact once and reusing it wherever it appears, so documentation scales across products. |
| [Style guides and terminology management](concepts/style-guide.md) | supporting | read it | 2h | :material-check: complete | Keeping voice and terminology consistent across many authors, and enforcing it in the same tools as code. |

## Docs-as-code toolchain

| Concept | Tier | Effort | Time | Status | Where it shows up in the work |
|---|---|---|---|---|---|
| [Choosing a static site generator](concepts/static-site-generators.md) | core | practise it | 3h | :material-check: complete | Choosing, configuring and living with the generator that turns your source into a site. |
| [Docs-as-code](concepts/docs-as-code.md) | core | read it | 2h | :material-check: complete | Running documentation through Git, CI builds, linting, link and sample checks, and automated publishing. |
| [Generated API reference](concepts/api-reference-generation.md) | core | practise it | 4h | :material-check: complete | Producing reference documentation from the code itself, so it assumes no prior context and stays current. |
| [Git authoring workflows for writers](concepts/git-authoring.md) | core | practise it | 4h | :material-check: complete | Writing in Git: branches, pull requests and review, in Markdown or RST, built by a static site generator. |
| [Markdown and its dialects](concepts/markdown.md) | core | read it | 2h | :material-check: complete | Writing in Markdown every day, and knowing which dialect your build pipeline actually speaks. |
| [MkDocs and Material](concepts/mkdocs.md) | core | practise it | 4h | :material-check: complete | Building and maintaining a documentation site on MkDocs with the Material theme. |
| [Sphinx](concepts/sphinx.md) | core | build something | 6h | :material-check: complete | Building and maintaining documentation with Sphinx, especially for Python projects. |
| [Diagrams as code](concepts/diagrams-as-code.md) | supporting | practise it | 3h | :material-check: complete | Keeping architecture and pipeline diagrams in the repository as text, reviewed like code and checked against the syst... |
| [Docusaurus](concepts/docusaurus.md) | supporting | practise it | 5h | :material-check: complete | Building and maintaining a documentation site on Docusaurus. |
| [Localization and translation pipelines](concepts/localization.md) | supporting | build something | 4h | :material-check: complete | Getting content translated and keeping translations in step with the source as it changes. |
| [MDX](concepts/mdx.md) | supporting | practise it | 3h | :material-check: complete | Authoring pages that mix Markdown with components, inside a docs-as-code workflow with CI. |
| [OpenAPI and REST reference](concepts/openapi.md) | supporting | practise it | 4h | :material-check: complete | Documenting any HTTP API from its contract, and keeping that contract and the reference in step. |
| [Versioned documentation](concepts/versioning.md) | supporting | practise it | 3h | :material-check: complete | Publishing documentation for more than one release at once, and keeping readers on the right version. |
| [reStructuredText](concepts/restructuredtext.md) | supporting | practise it | 3h | :material-check: complete | Maintaining docs written in reStructuredText, usually alongside a Sphinx build. |
| [Antora and AsciiDoc](concepts/antora.md) | context | practise it | 3h | :material-check: complete | Recognising and maintaining Antora and AsciiDoc sites you inherit; rarely the choice for a new one. |

## Quality automation and documentation CI

| Concept | Tier | Effort | Time | Status | Where it shows up in the work |
|---|---|---|---|---|---|
| [Building a doc test harness](concepts/doc-test-harness.md) | core | build something | 6h | :material-check: complete | Building a harness that runs documentation as tests, so broken pages fail the build. |
| [Code-sample validation](concepts/code-sample-validation.md) | core | build something | 5h | :material-check: complete | Proving every code sample in the docs still runs and still produces what the page says. |
| [Cold-start testing](concepts/coldstart-testing.md) | core | build something | 5h | :material-check: complete | Testing quickstarts from a clean environment, the way a new developer meets them. |
| [Documentation CI](concepts/documentation-ci.md) | core | practise it | 4h | :material-check: complete | Running automated checks on every documentation change before it merges. |
| [Freshness monitoring](concepts/freshness-monitoring.md) | core | practise it | 4h | :material-check: complete | Checking automatically that content is still current, and routing what is not to a human. |
| [GitHub Actions for docs](concepts/github-actions.md) | core | practise it | 4h | :material-check: complete | Writing and maintaining the CI workflows that build, check and publish your documentation. |
| [Link checking](concepts/link-checking.md) | core | read it | 2h | :material-check: complete | Catching broken links before readers do, in CI and on the published site. |
| [Prose linting with Vale](concepts/prose-linting.md) | core | practise it | 3h | :material-check: complete | Enforcing your style guide automatically with Vale, so reviews argue with a rule rather than a person. |
| [Accessibility checks](concepts/accessibility.md) | supporting | practise it | 3h | :material-check: complete | Making sure published content is usable by everyone, which applies to every page you ship. |
| [Detecting terminology drift](concepts/terminology-drift.md) | supporting | practise it | 3h | :material-check: complete | Detecting when the words in your docs drift away from the words in the product. |
| [Doctests and executable docstrings](concepts/doctests.md) | supporting | practise it | 2h | :material-check: complete | Keeping examples in docstrings executable, so they fail when the code changes. |
| [Preview deployments and publishing](concepts/preview-deployments.md) | supporting | practise it | 3h | :material-check: complete | Previewing every documentation change as a built site, and publishing it when it merges. |
| [Reviewing documentation](concepts/docs-review.md) | supporting | practise it | 3h | :material-check: complete | Reviewing documentation pull requests for accuracy, structure and style. |
| [Writing custom linters](concepts/custom-linters.md) | supporting | build something | 5h | :material-check: complete | Writing your own content checks when an off-the-shelf linter cannot express the rule. |

## Golden paths and developer onboarding

| Concept | Tier | Effort | Time | Status | Where it shows up in the work |
|---|---|---|---|---|---|
| [Designing tutorials](concepts/tutorial-design.md) | core | practise it | 4h | :material-check: complete | Designing tutorials that teach by having the reader build something real. |
| [Golden paths](concepts/golden-paths.md) | core | build something | 5h | :material-check: complete | Designing and maintaining the routes that take a developer from a clean environment to a working result. |
| [Guided workflows](concepts/guided-workflows.md) | core | build something | 5h | :material-check: complete | Replacing static instructions with workflows that guide a person through a standard. |
| [Quickstarts that survive contact](concepts/quickstarts.md) | core | practise it | 3h | :material-check: complete | Writing quickstarts that still work when a new developer follows them cold. |
| [Sample walkthroughs](concepts/sample-walkthroughs.md) | core | practise it | 3h | :material-check: complete | Writing walkthroughs that explain a sample line by line, without drifting from the sample. |
| [Templates and scaffolding](concepts/templates-scaffolding.md) | core | practise it | 3h | :material-check: complete | Encoding team standards into templates and scaffolds, so the right shape is the default. |
| [Reproducible environments](concepts/reproducible-environments.md) | supporting | build something | 4h | :material-check: complete | Making sure every exercise starts from an environment a reader can recreate exactly. |
| [Sample applications and galleries](concepts/sample-apps.md) | supporting | build something | 6h | :material-check: complete | Building and maintaining the sample applications, and the gallery developers browse them from. |

## AI-ready content and agents

| Concept | Tier | Effort | Time | Status | Where it shows up in the work |
|---|---|---|---|---|---|
| [Agent skills and context kits](concepts/agent-skills.md) | core | practise it | 4h | :material-check: complete | Packaging instructions and context so agents can do a task the way your team does it. |
| [Agent-ready content](concepts/agent-ready-content.md) | core | practise it | 4h | :material-check: complete | Structuring knowledge so AI assistants and agents can use it as reliably as people can. |
| [Agentic workflows](concepts/agentic-workflows.md) | core | build something | 6h | :material-check: complete | Structuring content so agents can carry out multi-step tasks from it. |
| [Chunking strategies](concepts/chunking.md) | core | build something | 5h | :material-check: complete | Splitting content into pieces a RAG system, internal assistant or agent can retrieve on their own. |
| [Documentation for coding agents](concepts/coding-agents.md) | core | practise it | 4h | :material-check: complete | Making documentation usable by coding agents as well as by search engines and people. |
| [Documentation-backed AI assistants](concepts/ai-assistants.md) | core | build something | 8h | :material-check: complete | Building and feeding assistants that answer questions from your documentation. |
| [Embeddings](concepts/embeddings.md) | core | practise it | 4h | :material-check: complete | Turning content into vectors so it can be searched by meaning, the first step of any RAG pipeline. |
| [Evaluating retrieval](concepts/retrieval-evaluation.md) | core | build something | 6h | :material-check: complete | Building question sets that measure whether retrieval finds the right content. |
| [Generative engine optimization](concepts/geo.md) | core | practise it | 3h | :material-check: complete | Making documentation the source AI-generated answers draw on and cite. |
| [Grounding and citation](concepts/grounding.md) | core | practise it | 4h | :material-check: complete | Making AI answers cite and stay within the documentation they draw on. |
| [LLMs in the content lifecycle](concepts/llm-content-lifecycle.md) | core | build something | 6h | :material-check: complete | Using LLMs to draft, update and audit content, with human review where judgement matters. |
| [Model Context Protocol](concepts/mcp.md) | core | build something | 5h | :material-check: complete | Exposing documentation and tools to AI assistants through Model Context Protocol servers. |
| [Output evaluation](concepts/output-evaluation.md) | core | build something | 6h | :material-check: complete | Measuring whether LLM output in your content workflows is accurate and usable. |
| [Prompting for content work](concepts/prompting.md) | core | practise it | 3h | :material-check: complete | Writing prompts for drafting, rewriting and checking content, and knowing where they fail. |
| [RAG pipelines](concepts/rag.md) | core | build something | 8h | :material-check: complete | Building and maintaining pipelines that answer questions from your documentation. |
| [Vector stores and hybrid search](concepts/vector-stores.md) | core | build something | 5h | :material-check: complete | Storing and searching embedded content, alone or alongside keyword search: the retrieval half of RAG. |
| [llms.txt and llms-full.txt](concepts/llms-txt.md) | core | read it | 2h | :material-check: complete | Publishing machine-readable entry points to your docs, such as llms.txt, for AI tools to consume. |
| [Crawlability and the agent-ready front door](concepts/crawlability.md) | supporting | practise it | 3h | :material-check: complete | Making sure crawlers and agents can reach and read every page, starting from the front door. |
| [Hallucination and guardrails](concepts/hallucination-guardrails.md) | supporting | build something | 4h | :material-check: complete | Catching and limiting AI answers that are confident and wrong. |
| [SEO for documentation](concepts/seo-for-docs.md) | supporting | practise it | 3h | :material-check: complete | Making documentation rank for the searches developers actually run. |
| [Structured data and JSON-LD](concepts/structured-data.md) | supporting | practise it | 3h | :material-check: complete | Adding machine-readable markup so search engines and AI tools understand what a page is. |

## Measurement and feedback

| Concept | Tier | Effort | Time | Status | Where it shows up in the work |
|---|---|---|---|---|---|
| [Documentation analytics](concepts/docs-analytics.md) | core | practise it | 4h | :material-check: complete | Instrumenting documentation and turning what the data shows into fixes to docs, samples and tooling. |
| [Measuring AI answer quality](concepts/ai-answer-quality.md) | core | build something | 5h | :material-check: complete | Measuring how often an AI assistant answers correctly from your documentation. |
| [Repeat-question analysis](concepts/repeat-questions.md) | core | practise it | 3h | :material-check: complete | Finding the questions people keep asking, and fixing the content that keeps causing them. |
| [Support deflection](concepts/support-deflection.md) | core | practise it | 3h | :material-check: complete | Measuring how much support load and onboarding time self-service content removes. |
| [Time to first success](concepts/time-to-first-success.md) | core | practise it | 3h | :material-check: complete | Measuring how long a new developer takes to reach a working result, and shortening it. |
| [Search and query log analysis](concepts/search-log-analysis.md) | supporting | practise it | 3h | :material-check: complete | Reading what people search for, so evaluation sets and fixes reflect real questions. |
| [Turning developer feedback into changes](concepts/developer-feedback-loops.md) | supporting | practise it | 3h | :material-check: complete | Turning developer feedback into changes to documentation, samples and the product. |

## Developer education and curriculum

| Concept | Tier | Effort | Time | Status | Where it shows up in the work |
|---|---|---|---|---|---|
| [Cognitive load in technical content](concepts/cognitive-load.md) | core | practise it | 3h | :material-check: complete | Cutting what a reader has to hold in their head, so they reach first success sooner. |
| [Instructional design for developers](concepts/instructional-design.md) | core | practise it | 5h | :material-check: complete | Designing curriculum so a developer learns what they need, in the order they need it. |
| [Learner and task analysis](concepts/learner-task-analysis.md) | core | practise it | 5h | :material-check: complete | Finding out who your readers are and what they actually do before deciding what any tutorial, lab or course should te... |
| [Learning paths and curriculum](concepts/learning-paths.md) | core | build something | 5h | :material-check: complete | Sequencing content into structured learning paths a reader can follow start to finish. |
| [Learning science for developer education](concepts/learning-science.md) | core | practise it | 6h | :material-check: complete | Applying what research says about how people learn to every tutorial, lab and learning path you design. |
| [Assessment and checks for understanding](concepts/assessment.md) | supporting | practise it | 3h | :material-check: complete | Checking that a learner actually learned: how you know the curriculum worked. |
| [Developer advocacy](concepts/developer-advocacy.md) | supporting | practise it | 3h | :material-check: complete | Working with engineering, product and advocates so each new capability ships with tested documentation. |
| [LMS administration](concepts/lms-administration.md) | supporting | practise it | 4h | :material-check: complete | Keeping the courses in a learning management system true to their source, enrolled correctly, and reporting completio... |
| [Learning content standards](concepts/learning-content-standards.md) | supporting | practise it | 5h | :material-check: complete | Packaging courses and labs so any learning platform can launch them, and getting the tracking data back out in a form... |
| [Publishing in public](concepts/publishing-in-public.md) | supporting | read it | 4h | :material-check: complete | Publishing your documentation tooling and work openly, and doing it safely. |
| [Workshops and hands-on labs](concepts/workshops.md) | supporting | practise it | 4h | :material-check: complete | Running hands-on workshops and labs, a standard developer-relations deliverable. |
| [Screencasts and video](concepts/screencasts.md) | context | practise it | 4h | :material-check: complete | Producing short videos that show a task, and keeping them accurate as the product changes. |

## Automation with Python

| Concept | Tier | Effort | Time | Status | Where it shows up in the work |
|---|---|---|---|---|---|
| [Integrating with APIs](concepts/api-integration.md) | core | practise it | 4h | :material-check: complete | Connecting your content tooling to other systems through their APIs. |
| [Python for content automation](concepts/python-for-content.md) | core | practise it | 5h | :material-check: complete | Using Python to automate content tasks, transform data and call APIs. |
| [Transforming content as data](concepts/content-data-transformation.md) | core | practise it | 4h | :material-check: complete | Treating content as data: parsing, reshaping and generating it with scripts. |

## Domain context

| Concept | Tier | Effort | Time | Status | Where it shows up in the work |
|---|---|---|---|---|---|
| [GPU computing and CUDA](concepts/gpu-computing.md) | context | practise it | 4h | :material-check: complete | Documenting software that runs on GPUs, well enough to follow the engineers who build it. |
| [Inference serving and microservices](concepts/inference-serving.md) | context | practise it | 4h | :material-check: complete | Documenting how models are served as microservices, and the agent tooling around them. |
| [OpenUSD and Omniverse](concepts/usd-omniverse.md) | context | practise it | 4h | :material-check: complete | Documenting tools built on OpenUSD and Omniverse. |
| [Reading an AI software stack](concepts/ai-stack.md) | context | practise it | 4h | :material-check: complete | Running and validating AI samples, which means reading the software stack under them. |
| [Real-time and graphics systems](concepts/realtime-systems.md) | context | practise it | 4h | :material-check: complete | Documenting graphics, simulation and real-time systems, where timing is part of correctness. |
| [Robotics simulation, Isaac Sim and ROS](concepts/robotics-sim.md) | context | practise it | 4h | :material-check: complete | Documenting robotics simulation with Isaac Sim and ROS. |

## Ways of working

| Concept | Tier | Effort | Time | Status | Where it shows up in the work |
|---|---|---|---|---|---|
| [A systems mindset](concepts/systems-mindset.md) | core | practise it | 2h | :material-check: complete | Fixing the class of problem rather than the single instance in front of you. |
| [Extracting tribal knowledge](concepts/sme-interviews.md) | core | practise it | 3h | :material-check: complete | Getting tribal knowledge out of experts' heads and into tooling, templates and self-service paths. |
| [Giving architecture owners implementation feedback](concepts/implementation-feedback.md) | core | practise it | 3h | :material-check: complete | Telling architecture owners what works, breaks and scales, so content models and AI-readiness patterns improve. |
| [Judging where AI can be trusted](concepts/ai-trust-judgment.md) | core | practise it | 4h | :material-check: complete | Deciding where AI output can be trusted and where a human must check it. |
| [Reading code to verify accuracy](concepts/reading-code-to-verify.md) | core | practise it | 5h | :material-check: complete | Reading code and APIs to verify a page is accurate, and writing examples that work. |
| [Release readiness for documentation](concepts/release-readiness.md) | core | practise it | 4h | :material-check: complete | Making documentation part of what "ready to release" means, enforced rather than remembered. |
| [Technical writing as a craft](concepts/technical-writing.md) | core | practise it | 8h | :material-check: complete | Writing developer documentation a reader can act on without asking you a question. |
| [Treating docs, setup and samples as one product](concepts/docs-as-product.md) | core | practise it | 3h | :material-check: complete | Treating setup, runnable samples and documentation as one product the developer experiences. |
| [Multi-platform parity](concepts/multi-platform-parity.md) | supporting | build something | 4h | :material-check: complete | Documenting one product that developers reach through a first-party API and several cloud platforms, so each reader l... |
| [Prioritizing documentation work](concepts/docs-prioritization.md) | supporting | practise it | 3h | :material-check: complete | Using data to decide what to build, fix or retire next. |
| [Release notes and changelogs](concepts/release-notes.md) | supporting | practise it | 3h | :material-check: complete | Writing what changed in each release for the people who have to act on it, and making sure the version number tells t... |
| [User stories as a documentation standard](concepts/user-stories.md) | supporting | read it | 2h | :material-check: complete | Turning user stories into a documentation standard that templates can enforce. |
| [Working with engineers as sources](concepts/working-with-engineers.md) | supporting | practise it | 3h | :material-check: complete | Working with engineering, product, security and partner teams so every release ships documented. |
| [Documentation for partners and internal teams](concepts/partner-documentation.md) | context | practise it | 3h | :material-check: complete | Delivering knowledge to developers, partners, internal teams and the AI agents between them. |

## The page contract

Every concept page answers the same seven questions in the same order, and CI
rejects one that does not:

1. **What it is**
2. **How this applies to your role**
3. **The golden path**
4. **Reference**
5. **Explaining it to your team**
6. **Putting it into practice**
7. **Related**

That is a content model applied to a learning corpus rather than to a product's
documentation. The payoff is that the thirtieth page costs a reader nothing to
navigate, because they learned the shape on the first.
