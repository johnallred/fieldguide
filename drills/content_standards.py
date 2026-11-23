#!/usr/bin/env python3
"""Check a SCORM package, xAPI statements and an LTI launch against their specs.

    python3 drills/content_standards.py              # embedded broken, then fixed
    python3 drills/content_standards.py pkg/         # a directory you wrote

The directory holds three files a reader writes by hand:

- imsmanifest.xml: a SCORM content package manifest. It must sit at the
  package root, and every resource it points to must exist.
- statements.json: xAPI statements. Each needs actor, verb and object; an
  Agent needs exactly one inverse functional identifier; a verb id is an IRI.
- launch.json: the claims from an LTI 1.3 resource link launch.

Each rule checked here is one the page quotes from the specification. These
are the defects an LMS import or an LRS rejects, found before upload.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import xml.etree.ElementTree as ET

MANIFEST = """\
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
"""

STATEMENTS = """\
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
"""

LAUNCH = """\
{
  "https://purl.imsglobal.org/spec/lti/claim/message_type": "LtiResourceLinkRequest",
  "https://purl.imsglobal.org/spec/lti/claim/version": "1.3.0",
  "https://purl.imsglobal.org/spec/lti/claim/deployment_id": "retries-lab-1",
  "https://purl.imsglobal.org/spec/lti/claim/target_link_uri": "https://labs.example.com/retries",
  "https://purl.imsglobal.org/spec/lti/claim/resource_link": {"id": "lab-retries-01"},
  "sub": "a6d5c443-1f51-4783-ba1a-7686ffe3b54a"
}
"""

STATEMENTS_FIXED = """\
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
"""

LAUNCH_FIXED = """\
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
"""

IFIS = ("mbox", "mbox_sha1sum", "openid", "account")
LTI = "https://purl.imsglobal.org/spec/lti/claim/"
REQUIRED_CLAIMS = ("message_type", "version", "deployment_id", "target_link_uri",
                   "resource_link", "roles")


def check_scorm(root: str) -> list[str]:
    path = os.path.join(root, "imsmanifest.xml")
    if not os.path.exists(path):
        return ["SCORM  imsmanifest.xml is not at the package root"]
    tree = ET.parse(path).getroot()
    ns = {"cp": tree.tag.split("}")[0].strip("{")}
    found = []
    resources = {r.get("identifier"): r for r in tree.iterfind(".//cp:resource", ns)}
    for item in tree.iterfind(".//cp:item", ns):
        ref = item.get("identifierref")
        if ref not in resources:
            found.append(f"SCORM  item {item.get('identifier')} points at missing resource {ref}")
    for rid, res in resources.items():
        href = res.get("href")
        if href and not os.path.exists(os.path.join(root, href)):
            found.append(f"SCORM  resource {rid}: {href} is not in the package")
    return found


def check_xapi(root: str) -> list[str]:
    with open(os.path.join(root, "statements.json"), encoding="utf-8") as handle:
        statements = json.load(handle)
    found = []
    for n, s in enumerate(statements, 1):
        for key in ("actor", "verb", "object"):
            if key not in s:
                found.append(f"xAPI   statement {n}: no {key}")
        ifis = [k for k in IFIS if k in s.get("actor", {})]
        if len(ifis) != 1:
            found.append(f"xAPI   statement {n}: actor has {len(ifis)} identifiers ({', '.join(ifis)}), needs exactly 1")
        verb = s.get("verb", {}).get("id", "")
        if ":" not in verb:
            found.append(f"xAPI   statement {n}: verb id '{verb}' is not an IRI")
    return found


def check_lti(root: str) -> list[str]:
    with open(os.path.join(root, "launch.json"), encoding="utf-8") as handle:
        claims = json.load(handle)
    found = [f"LTI    launch is missing the {name} claim"
             for name in REQUIRED_CLAIMS if LTI + name not in claims]
    if claims.get(LTI + "version") not in (None, "1.3.0"):
        found.append("LTI    version claim is not 1.3.0")
    if "sub" not in claims:
        found.append("LTI    no sub: only an anonymous launch may omit it")
    return found


def check(root: str) -> int:
    found = check_scorm(root) + check_xapi(root) + check_lti(root)
    for line in found:
        print(line)
    print(f"{len(found)} finding(s)")
    return len(found)


def write(root: str, files: dict[str, str]) -> None:
    for name, text in files.items():
        with open(os.path.join(root, name), "w", encoding="utf-8") as handle:
            handle.write(text)


def main() -> int:
    if len(sys.argv) > 1:
        return 1 if check(sys.argv[1]) else 0
    with tempfile.TemporaryDirectory() as root:
        write(root, {"imsmanifest.xml": MANIFEST, "statements.json": STATEMENTS,
                     "launch.json": LAUNCH, "configure.html": "<h1>Configure</h1>\n"})
        print("== before")
        check(root)
        write(root, {"statements.json": STATEMENTS_FIXED, "launch.json": LAUNCH_FIXED,
                     "diagnose.html": "<h1>Diagnose</h1>\n"})
        print("\n== after")
        remaining = check(root)
    return 1 if remaining else 0


if __name__ == "__main__":
    sys.exit(main())
