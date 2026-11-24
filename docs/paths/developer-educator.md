---
title: The developer educator
summary: Taking a developer from a clean environment to a working result, repeatably.
diataxis: placeholder
audience: new-user
generated: true
---


# The developer educator

**Who this is for.** Someone who owns developer onboarding, tutorials and curriculum.

Taking a developer from a clean environment to a working result, repeatably.

**24 concepts, roughly 103 hours.** The order matters:
each step assumes the ones above it.

**Assumed before step 1.** This path does not teach [Information architecture](../concepts/information-architecture.md), [Code-sample validation](../concepts/code-sample-validation.md), [Documentation CI](../concepts/documentation-ci.md), [Multi-platform parity](../concepts/multi-platform-parity.md), [Templates and scaffolding](../concepts/templates-scaffolding.md). Each step below repeats what it assumes.

## 1. [Treating docs, setup and samples as one product](../concepts/docs-as-product.md)

`core` · practise it · 3h

Treating setup, runnable samples and documentation as one product the developer experiences.

## 2. [Learning science for developer education](../concepts/learning-science.md)

`core` · practise it · 6h

Applying what research says about how people learn to every tutorial, lab and learning path you design.

## 3. [Learner and task analysis](../concepts/learner-task-analysis.md)

`core` · practise it · 5h

Finding out who your readers are and what they actually do before deciding what any tutorial, lab or course should teach.

Builds on, earlier in this path: Learning science for developer education.

## 4. [Instructional design for developers](../concepts/instructional-design.md)

`core` · practise it · 5h

Designing curriculum so a developer learns what they need, in the order they need it.

Builds on, earlier in this path: Learning science for developer education, Learner and task analysis.

## 5. [Cognitive load in technical content](../concepts/cognitive-load.md)

`core` · practise it · 3h

Cutting what a reader has to hold in their head, so they reach first success sooner.

Builds on, earlier in this path: Instructional design for developers.

## 6. [Diátaxis](../concepts/diataxis.md)

`core` · read it · 2h

Deciding whether a page is a tutorial, a how-to, reference or explanation, and keeping it to one of them.

Assumes, from outside this path: [Information architecture](../concepts/information-architecture.md).

## 7. [Designing tutorials](../concepts/tutorial-design.md)

`core` · practise it · 4h

Designing tutorials that teach by having the reader build something real.

Builds on, earlier in this path: Diátaxis.

## 8. [Golden paths](../concepts/golden-paths.md)

`core` · build something · 5h

Designing and maintaining the routes that take a developer from a clean environment to a working result.

Builds on, earlier in this path: Diátaxis.

## 9. [Quickstarts that survive contact](../concepts/quickstarts.md)

`core` · practise it · 3h

Writing quickstarts that still work when a new developer follows them cold.

Builds on, earlier in this path: Golden paths.

## 10. [Sample walkthroughs](../concepts/sample-walkthroughs.md)

`core` · practise it · 3h

Writing walkthroughs that explain a sample line by line, without drifting from the sample.

Builds on, earlier in this path: Designing tutorials.

## 11. [Reproducible environments](../concepts/reproducible-environments.md)

`supporting` · build something · 4h

Making sure every exercise starts from an environment a reader can recreate exactly.

Builds on, earlier in this path: Golden paths.

## 12. [Cold-start testing](../concepts/coldstart-testing.md)

`core` · build something · 5h

Testing quickstarts from a clean environment, the way a new developer meets them.

Builds on, earlier in this path: Reproducible environments.

Assumes, from outside this path: [Code-sample validation](../concepts/code-sample-validation.md).

## 13. [Ephemeral lab environments](../concepts/ephemeral-environments.md)

`supporting` · build something · 6h

Standing up a real cloud environment for every lab run, checking the lab against it, and proving the teardown left nothing running.

Builds on, earlier in this path: Reproducible environments, Cold-start testing.

## 14. [Lab publishing pipelines](../concepts/lab-publishing.md)

`supporting` · build something · 5h

Shipping hands-on labs through gates, versions and channels, so a broken lab is stopped before learners meet it and a published one can be pulled or rolled back.

Builds on, earlier in this path: Ephemeral lab environments.

Assumes, from outside this path: [Documentation CI](../concepts/documentation-ci.md).

## 15. [Labs for isolated regions](../concepts/isolated-region-labs.md)

`supporting` · build something · 5h

Making a lab that runs in one AWS partition run in another, including isolated regions with no route to the public internet.

Builds on, earlier in this path: Lab publishing pipelines.

Assumes, from outside this path: [Multi-platform parity](../concepts/multi-platform-parity.md).

## 16. [Learning paths and curriculum](../concepts/learning-paths.md)

`core` · build something · 5h

Sequencing content into structured learning paths a reader can follow start to finish.

Builds on, earlier in this path: Instructional design for developers, Diátaxis.

## 17. [LMS administration](../concepts/lms-administration.md)

`supporting` · practise it · 4h

Keeping the courses in a learning management system true to their source, enrolled correctly, and reporting completion you can act on.

Builds on, earlier in this path: Learning paths and curriculum.

## 18. [Learning content standards](../concepts/learning-content-standards.md)

`supporting` · practise it · 5h

Packaging courses and labs so any learning platform can launch them, and getting the tracking data back out in a form someone can use.

Builds on, earlier in this path: LMS administration.

## 19. [Assessment and checks for understanding](../concepts/assessment.md)

`supporting` · practise it · 3h

Checking that a learner actually learned: how you know the curriculum worked.

Builds on, earlier in this path: Instructional design for developers.

## 20. [Sample applications and galleries](../concepts/sample-apps.md)

`supporting` · build something · 6h

Building and maintaining the sample applications, and the gallery developers browse them from.

Builds on, earlier in this path: Sample walkthroughs.

Assumes, from outside this path: [Code-sample validation](../concepts/code-sample-validation.md).

## 21. [Demo design](../concepts/demo-design.md)

`supporting` · practise it · 3h

Building demos that show the result first, fit their slot, adapt to the audience, and still work when someone other than their author runs them.

Builds on, earlier in this path: Sample applications and galleries.

## 22. [Workshops and hands-on labs](../concepts/workshops.md)

`supporting` · practise it · 4h

Running hands-on workshops and labs, a standard developer-relations deliverable.

Builds on, earlier in this path: Learning paths and curriculum, Reproducible environments.

## 23. [Field enablement](../concepts/field-enablement.md)

`supporting` · practise it · 4h

Teaching the people who demo, sell and support the product until they can deliver without you, and turning what they hear into changes.

Builds on, earlier in this path: Workshops and hands-on labs, Demo design.

## 24. [Guided workflows](../concepts/guided-workflows.md)

`core` · build something · 5h

Replacing static instructions with workflows that guide a person through a standard.

Assumes, from outside this path: [Templates and scaffolding](../concepts/templates-scaffolding.md).
