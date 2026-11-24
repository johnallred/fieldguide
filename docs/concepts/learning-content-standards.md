---
title: Learning content standards
summary: SCORM, xAPI, cmi5 and LTI, what each one actually standardizes, and how to catch the defects an LMS or LRS will reject before you upload.
diataxis: explanation
audience: developer
concept: learning-content-standards
tags: [edu, supporting]
---

# Learning content standards

`supporting` · difficulty 2 · 5h

> Packaging courses and labs so any learning platform can launch them, and getting the tracking data back out in a form someone can use.

**Prerequisites:** [LMS administration](lms-administration.md)

## What it is

The specifications that let content built in one place run and report inside a
learning platform built by someone else. Four matter: **SCORM** packages a
course and defines how it talks to the LMS; **xAPI** records learning activity
as statements anywhere, not only in an LMS; **cmi5** uses xAPI for content an
LMS launches; and **LTI** launches an external tool, such as a hands-on lab,
from inside the LMS and can send a grade back.

They solve different problems, and most confusion about them comes from
treating them as competing versions of one thing.

## How this applies to your role

This matters because the course or lab you build is only useful if the platform can launch
it and report on it, and both of those are governed by these standards.

On a Tuesday it looks like this. A lab you built works perfectly from its own
URL. Delivered through the LMS, it fails for every learner, and the error says
only "invalid launch". Or a course package uploads, but the second lesson is
blank. Or completion reports show nobody passed, because the statements your
content sent were rejected and nothing told you. Each of those is a specific
rule in a specific standard, and each one is checkable before upload.

The second reason is choosing. Someone will ask whether the new labs should be
SCORM, xAPI or LTI. The answer depends on what the content is and what data
anyone needs, and it is a decision that is expensive to reverse once a
catalog is built around it.

## The golden path

Write a small SCORM package, three xAPI statements and an LTI launch, check
them against the rules each specification states, fix the four defects, and
check again. About thirty minutes, with no LMS needed.

The checker is committed as `drills/content_standards.py`, which holds every
file below and a test that keeps them identical to this page.

**Step 1: a SCORM package with two lessons, one of them missing**

```bash
mkdir -p pkg && cd pkg
cat > imsmanifest.xml <<'DATA'
<?xml version="1.0" encoding="UTF-8"?>
<manifest identifier="retries-course" version="1.0"
          xmlns="http://www.imsproject.org/xsd/imscp_rootv1p1p2"
          xmlns:adlcp="http://www.adlnet.org/xsd/adlcp_rootv1p2">
  <metadata>
    <schema>ADL SCORM</schema>
    <schemaversion>1.2</schemaversion>
  </metadata>
  <organizations default="org">
    <organization identifier="org">
      <title>Retries in the widget client</title>
      <item identifier="i1" identifierref="r1"><title>Configure retries</title></item>
      <item identifier="i2" identifierref="r2"><title>Diagnose an exhausted budget</title></item>
    </organization>
  </organizations>
  <resources>
    <resource identifier="r1" type="webcontent" adlcp:scormtype="sco" href="configure.html"/>
    <resource identifier="r2" type="webcontent" adlcp:scormtype="sco" href="diagnose.html"/>
  </resources>
</manifest>
DATA
printf '<h1>Configure</h1>\n' > configure.html
```

**Step 2: xAPI statements and an LTI launch**

```bash
cat > statements.json <<'DATA'
[
  {"actor": {"mbox": "mailto:ana@example.com"},
   "verb": {"id": "http://adlnet.gov/expapi/verbs/completed"},
   "object": {"id": "https://example.com/courses/retries/configure"}},
  {"actor": {"mbox": "mailto:raj@example.com",
             "account": {"homePage": "https://lms.example.com", "name": "raj"}},
   "verb": {"id": "http://adlnet.gov/expapi/verbs/passed"},
   "object": {"id": "https://example.com/courses/retries/diagnose"}},
  {"actor": {"mbox": "mailto:li@example.com"},
   "verb": {"id": "finished"},
   "object": {"id": "https://example.com/courses/retries/diagnose"}}
]
DATA
cat > launch.json <<'DATA'
{
  "https://purl.imsglobal.org/spec/lti/claim/message_type": "LtiResourceLinkRequest",
  "https://purl.imsglobal.org/spec/lti/claim/version": "1.3.0",
  "https://purl.imsglobal.org/spec/lti/claim/deployment_id": "retries-lab-1",
  "https://purl.imsglobal.org/spec/lti/claim/target_link_uri": "https://labs.example.com/retries",
  "https://purl.imsglobal.org/spec/lti/claim/resource_link": {"id": "lab-retries-01"},
  "sub": "a6d5c443-1f51-4783-ba1a-7686ffe3b54a"
}
DATA
cd ..
curl -sO https://raw.githubusercontent.com/johnallred/fieldguide/main/drills/content_standards.py
```

**Step 3: check all three**

```bash
python3 content_standards.py pkg/
```

```
SCORM  resource r2: diagnose.html is not in the package
xAPI   statement 2: actor has 2 identifiers (mbox, account), needs exactly 1
xAPI   statement 3: verb id 'finished' is not an IRI
LTI    launch is missing the roles claim
4 finding(s)
```

Four defects, one per rule. The manifest points at a lesson that is not in the
package, which is the blank second lesson. The second statement identifies its
learner twice, which an LRS must reject. The third uses a plain word where the
specification requires an IRI. The launch has no `roles` claim, which LTI 1.3
requires even when the list is empty.

**Step 4: fix them**

```bash
printf '<h1>Diagnose</h1>\n' > pkg/diagnose.html
cat > pkg/statements.json <<'DATA'
[
  {"actor": {"mbox": "mailto:ana@example.com"},
   "verb": {"id": "http://adlnet.gov/expapi/verbs/completed"},
   "object": {"id": "https://example.com/courses/retries/configure"}},
  {"actor": {"account": {"homePage": "https://lms.example.com", "name": "raj"}},
   "verb": {"id": "http://adlnet.gov/expapi/verbs/passed"},
   "object": {"id": "https://example.com/courses/retries/diagnose"}},
  {"actor": {"mbox": "mailto:li@example.com"},
   "verb": {"id": "http://adlnet.gov/expapi/verbs/completed"},
   "object": {"id": "https://example.com/courses/retries/diagnose"}}
]
DATA
cat > pkg/launch.json <<'DATA'
{
  "https://purl.imsglobal.org/spec/lti/claim/message_type": "LtiResourceLinkRequest",
  "https://purl.imsglobal.org/spec/lti/claim/version": "1.3.0",
  "https://purl.imsglobal.org/spec/lti/claim/deployment_id": "retries-lab-1",
  "https://purl.imsglobal.org/spec/lti/claim/target_link_uri": "https://labs.example.com/retries",
  "https://purl.imsglobal.org/spec/lti/claim/resource_link": {"id": "lab-retries-01"},
  "https://purl.imsglobal.org/spec/lti/claim/roles": [
    "http://purl.imsglobal.org/vocab/lis/v2/membership#Learner"
  ],
  "sub": "a6d5c443-1f51-4783-ba1a-7686ffe3b54a"
}
DATA
python3 content_standards.py pkg/
```

```
0 finding(s)
```

**What you built.** A SCORM package an LMS can import, statements an LRS will
accept, a launch an LTI tool can verify, and a checker that finds all four
defects before upload instead of after learners report them.

## Reference

### What each standard does

| Standard | Standardizes | Tracking goes to | Best for |
|---|---|---|---|
| SCORM 1.2 | A zipped package and a JavaScript API between content and LMS | The LMS, through a fixed data model | Self-paced courses in any LMS |
| SCORM 2004 | The same, plus separate completion and success, and sequencing | The LMS | Courses needing branching or sequencing rules |
| xAPI | Statements of the form actor, verb, object | A Learning Record Store (LRS), anywhere | Activity outside an LMS: labs, apps, simulations |
| cmi5 | How an LMS launches content and how that content uses xAPI | An LRS, with LMS launch rules | Modern LMS-launched courses |
| LTI 1.3 | A secure launch of an external tool, plus services such as grades | The tool, and grades back to the LMS | Hands-on labs and tools hosted elsewhere |

### The rules the checker enforces, and a few more

| Standard | Rule |
|---|---|
| SCORM | The manifest is `imsmanifest.xml`, at the root of the package |
| SCORM 1.2 | The API is `LMSInitialize("")` and `LMSFinish("")`; status is one element, `cmi.core.lesson_status` |
| SCORM 2004 | The API is `Initialize("")` and `Terminate("")`; `cmi.completion_status` and `cmi.success_status` are separate |
| SCORM | `cmi.suspend_data` holds 4096 characters in 1.2, 64000 in 2004 3rd and 4th editions |
| xAPI | A statement must have actor, verb and object |
| xAPI | An Agent has exactly one identifier: `mbox`, `mbox_sha1sum`, `openid` or `account` |
| xAPI | A verb id is an IRI, and one IRI means one thing |
| cmi5 | The course structure file in a package is `cmi5.xml` |
| cmi5 | Its defined verbs are launched, initialized, completed, passed, failed, abandoned, waived, terminated and satisfied |
| cmi5 | An AU's moveOn is Passed, Completed, CompletedAndPassed, CompletedOrPassed or NotApplicable |
| LTI 1.3 | Launch is an OpenID Connect login, and the launch message is a signed JWT (`id_token`) |
| LTI 1.3 | A resource link launch needs message_type `LtiResourceLinkRequest`, version `1.3.0`, deployment_id, target_link_uri, resource_link with an id, and roles |
| LTI | Grades go back through Assignment and Grade Services: line items, write-only scores, read-only results |

### Choosing

| If the content is | Prefer | Because |
|---|---|---|
| A self-paced course for an LMS you do not control | SCORM 1.2 | It imports almost everywhere; its limits are known |
| A course whose data you want outside the LMS | cmi5 | LMS launch with xAPI data you own |
| A hands-on lab in its own environment | LTI 1.3 | The lab stays where it runs; the LMS launches it and gets a grade |
| Activity with no LMS at all | xAPI | Statements from anything to an LRS |

### Sources

Opened and checked on 2026-11-23:

- [xAPI specification, data](https://github.com/adlnet/xAPI-Spec/blob/master/xAPI-Data.md): statement requirements, inverse functional identifiers, verbs.
- [cmi5 specification](https://github.com/AICC/CMI-5_Spec_Current/blob/quartz/cmi5_spec.md): relationship to xAPI, defined verbs, moveOn values, `cmi5.xml`.
- [LTI 1.3 core specification](https://www.imsglobal.org/spec/lti/v1p3) and [Assignment and Grade Services 2.0](https://www.imsglobal.org/spec/lti-ags/v2p0), 1EdTech.
- Rustici Software, [SCORM run-time reference](https://scorm.com/scorm-explained/technical-scorm/run-time/run-time-reference/) and [SCORM glossary](https://scorm.com/scorm-explained/scorm-resources/glossary/).

## Explaining it to your team

**How to explain it.** Lead with what each one is for. "SCORM is a package an
LMS plays. xAPI is a record of what someone did, stored anywhere. cmi5 is the
modern way for an LMS to play content and keep xAPI records. LTI is how an LMS
opens a tool that lives somewhere else, such as a lab, and gets a grade back.
They are not versions of each other."

**The follow-up is usually "should we move everything to xAPI".** Usually not
all at once. SCORM 1.2 is old and limited, and it is also the format every LMS
imports without argument. Move content whose data you need outside the LMS,
and leave the rest until there is a reason.

**The tradeoff to name.** Standards buy portability and cost you control. A SCORM
package can only report what its data model allows, and an LTI tool keeps the
detail of what learners did in the tool, not the LMS. Anything richer means
running an LRS or building the reporting yourself, which is real
infrastructure with real cost.

**One sharper point.** The defects that hurt are silent. An LRS rejecting a
statement, or a manifest pointing at a missing file, does not show an error to
the person who built the content; it shows up weeks later as a report where
nobody passed. A check like the golden path's belongs in CI for every package
and every statement template, the same way [code-sample
validation](code-sample-validation.md) belongs in documentation CI.

## Putting it into practice

**The work product.** A checker in CI that validates every course package,
statement template and launch configuration before it ships, and a written
decision about which standard each kind of content uses.

**Three things to do, in order:**

1. Run the golden path, then run the checker against one real package you
   maintain. Expect at least one resource the manifest names that is not in the
   zip, or one statement template with two identifiers.
2. Write the one-page decision: which standard for courses, which for labs,
   which for activity outside the LMS, and why.
3. Add the checker to the pipeline that builds your packages, so a defect fails
   the build instead of a learner.

**How to tell it is working.** The drill above runs in this guide's test suite
and its output is the output quoted here. It checks files against rules quoted
from the specifications; it has not been run against a real LMS, LRS or LTI
platform, so the [demonstrated](../demonstrated.md) page records the concept as
partial. In your own work, the sign is that package imports and statement
uploads stop failing in production because they fail in CI first.

## Related

- [LMS administration](lms-administration.md), the platform these packages are delivered through
- [Code-sample validation](code-sample-validation.md), the same check-before-ship habit for documentation
- [Documentation CI](documentation-ci.md), where the checker belongs
- [Assessment and checks for understanding](assessment.md), what the tracked scores are supposed to mean
- [Reproducible environments](reproducible-environments.md), the lab half of what LTI launches
