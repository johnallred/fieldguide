---
title: OpenAPI and REST reference
summary: A valid spec and an accurate spec are different properties, and only one of them has a tool.
diataxis: how-to
audience: developer
concept: openapi
tags: [dac, supporting]
---

# OpenAPI and REST reference

`supporting` · difficulty 2 · 4h

!!! note "Not a quotation (adjacent)"
    Neither posting mentions OpenAPI. It is the standard contract format for
    any HTTP surface you will document, so it is here on the grounds that the
    work requires it even where the requisition does not say so.

**Prerequisites:** [Generated API reference](api-reference-generation.md)

## What it is

A machine-readable description of an HTTP API: paths, operations, parameters,
request and response schemas, authentication. From it you can generate
reference pages, client libraries, mock servers and request collections, which
is why it has become the default way to document REST.

The distinction this page is built on: **a spec can be valid and wrong.**
Validity is a property of the document and has good tooling. Accuracy is a
property of the relationship between the document and the running service, and
has almost none.

## Why the job asks for it

It does not, explicitly, and the banner says so. But reference documentation
for an HTTP surface is OpenAPI work in practice, and both postings ask for
reference documentation.

The reason it belongs in a documentation-engineering curriculum rather than an
API-design one is that the spec is a documentation artifact with the same decay
problem as any other page, plus one special property: because it is machine
readable, people assume it is machine *verified*. It usually is not. A spec in
a repository with a validator in CI feels trustworthy and may describe an API
that no longer exists.

## The golden path

Validate a spec, break it, fix it, and then discover the failure a validator
cannot see. About thirty-five minutes.

**Step 1: a small spec**

````bash
mkdir -p oas-demo && cd oas-demo
pip install --quiet openapi-spec-validator

cat > spec.yaml <<'EOF'
openapi: 3.1.0
info:
  title: Widget API
  version: "2.4.0"
paths:
  /widgets/{id}:
    get:
      operationId: getWidget
      summary: Fetch a widget
      parameters:
        - name: id
          in: path
          required: true
          schema: {type: string}
        - name: expand
          in: query
          schema: {type: boolean, default: false}
      responses:
        "200":
          description: The widget
          content:
            application/json:
              schema: {$ref: "#/components/schemas/Widget"}
        "404":
          description: Not found
components:
  schemas:
    Widget:
      type: object
      required: [id, name]
      properties:
        id: {type: string}
        name: {type: string}
        retries: {type: integer, default: 5}
EOF
````

**Step 2: validate it, then break a reference**

```bash
python3 -c "
from openapi_spec_validator import validate
import yaml
validate(yaml.safe_load(open('spec.yaml')))
print('spec is valid')
"
```

```
spec is valid
```

Now make the single most common editing mistake, a typo in a `$ref`:

```bash
sed -i 's|schemas/Widget"|schemas/Widgets"|' spec.yaml
python3 -c "
from openapi_spec_validator import validate
import yaml
try:
    validate(yaml.safe_load(open('spec.yaml')))
except Exception as e:
    print('INVALID:', str(e).splitlines()[0][:70])
"
```

```
INVALID: '/components/schemas/Widgets' does not exist within {'openapi': ...
```

Caught. Put a validator in CI and structural mistakes stop reaching anyone.
This is the easy half, and it is where most teams stop.

**Step 3: an implementation that has drifted**

Restore the `$ref` so the spec is valid again, then write the service the way
services actually end up:

```python
# app.py, the implementation
# drift: retries is 3 here and the spec says 5,
# and there is an extra field the spec never mentions
self.wfile.write(json.dumps(
    {"id": "w1", "name": "Widget One", "retries": 3, "beta": True}
).encode())
```

```bash
python3 app.py & sleep 1
curl -s http://127.0.0.1:8731/widgets/w1
```

```
{"id": "w1", "name": "Widget One", "retries": 3, "beta": true}
```

The spec is valid. The validator is happy. The documented API and the real API
disagree in two places, and nothing in the toolchain has noticed.

**Step 4: check the contract, not the document**

```python
# contract.py
import json
import urllib.request

import yaml

spec = yaml.safe_load(open("spec.yaml"))
schema = spec["components"]["schemas"]["Widget"]
documented = set(schema["properties"])
required = set(schema.get("required", []))

body = json.loads(urllib.request.urlopen(
    "http://127.0.0.1:8731/widgets/w1").read())
actual = set(body)

findings = []
for missing in sorted(required - actual):
    findings.append(f"required field absent from the response: {missing!r}")
for undocumented in sorted(actual - documented):
    findings.append(f"response field absent from the spec: {undocumented!r}")
for name, prop in schema["properties"].items():
    if "default" in prop and name in body and body[name] != prop["default"]:
        findings.append(
            f"{name!r}: spec default is {prop['default']}, "
            f"response has {body[name]}")

for f in findings:
    print(f"CONTRACT  {f}")
print(f"{'FAIL' if findings else 'ok'}: {len(findings)} mismatch(es)")
raise SystemExit(1 if findings else 0)
```

```
CONTRACT  response field absent from the spec: 'beta'
CONTRACT  'retries': spec default is 5, response has 3
FAIL: 2 mismatch(es)
exit=1
```

**Step 5: be honest about which of those findings is sound**

The two findings are not equally valid, and pretending otherwise would be the
kind of thing this guide is written against.

The `beta` finding is a real contract issue: the service returns a field no
reader could know about, so anyone writing against the documentation is working
from an incomplete picture.

The `retries` finding is a **heuristic, and strictly a false positive**. In
OpenAPI, `default` describes what to assume when a value is *absent*, not what
a response must contain. A response legitimately carrying `3` violates nothing.
What it does tell you is that the documentation and the implementation disagree
about the normal value, which is usually worth a human look, so the check is
useful as a warning and wrong as an error.

Keep it, and keep it out of the blocking set.

**What you built.** A validator for the document and a contract check for the
relationship, plus a clear view of which findings are facts and which are
hints.

## Reference

### Two different properties, two different tools

| Property | Question | Tooling |
|---|---|---|
| Validity | Is this a well-formed OpenAPI document? | Good: `openapi-spec-validator`, `spectral` |
| Style | Does it follow our conventions? | Good: `spectral` with a ruleset |
| Accuracy | Does the service behave like this? | Poor, and usually hand-rolled |
| Completeness | Is every endpoint described? | Poor; compare routes to paths |
| Example validity | Do the examples satisfy their schemas? | Available, rarely enabled |

Rows three and four are where real documentation defects live, and they are the
two with no off-the-shelf answer. That asymmetry is the single most useful thing
to know about OpenAPI in a documentation role.

### How the spec gets written, and what each approach costs

| Approach | Drift risk | Notes |
|---|---|---|
| Hand-written spec | Highest | Nothing connects it to the code |
| Generated from code annotations | Low for shape | Follows the implementation, so it documents bugs faithfully |
| Spec-first, code generated from it | Lowest | Strongest guarantee, biggest process change |
| Generated from tests or traffic | Low for reality | Describes what happens, not what is intended |

Generated-from-code is the common middle. Its weakness is worth naming: if the
implementation is wrong, the spec documents the wrong behaviour with total
confidence.

### What to put in CI

| Gate | Blocking | Why |
|---|---|---|
| Spec validates | Yes | Deterministic, cheap, catches `$ref` typos |
| Spec passes the style ruleset | Yes | `operationId` present, descriptions non-empty |
| Every route has a path in the spec | Yes | Completeness, and easy if you can enumerate routes |
| Examples validate against their schemas | Yes | Catches examples nobody checked |
| Contract check against a live service | No | Needs a running service; a queue, not a gate |

### Generating documentation from it

| Tool | Produces |
|---|---|
| Redoc, Swagger UI, Scalar | A reference site from the spec |
| `widdershins` | Markdown, for embedding in an existing site |
| Prism | A mock server from the spec, useful in tutorials |
| OpenAPI Generator | Client libraries in many languages |

The mock server is underrated for documentation work. It lets a
[quickstart](quickstarts.md) be followed, and
[cold-start tested](coldstart-testing.md), before the real service is
available or without credentials.

## How to talk about it

**Lead with the two properties.** "A spec can be valid and wrong. Validity has
good tooling and catches `$ref` typos and missing descriptions. Accuracy, which
is whether the service actually behaves like the document, has almost none, so
that is the check I write: compare a live response against the schema and
report fields in one and not the other."

**The follow-up is how you would keep them in sync**, and the honest answer
ranks the options: generated-from-code removes shape drift but faithfully
documents bugs; spec-first is the strongest guarantee and the biggest process
change; hand-written is what most teams have and is the worst of the three.

**The tradeoff to volunteer.** A contract check needs a running service, which
means it cannot be a merge gate without a test environment that is itself
reliable. Gating merges on a check that depends on a deployed service is how you
get a team that reruns CI until it passes. So it belongs on a schedule, or in a
post-deploy step, producing a queue rather than a red build.

**One sharper point.** Be careful what you call a violation. Comparing a spec
`default` against a live response value looks like a contract check and is not
one: `default` describes what to assume when a field is absent. It is still a
useful signal that the docs and the service disagree about the normal case, so
it belongs in the warning set, and knowing the difference is the kind of
precision that distinguishes someone who has built one of these from someone
who has configured a validator.

## How to prove it

**The artifact.** A repository with spec validation and a style ruleset in CI,
plus a contract check that runs somewhere and produces findings.

**Three things to do, in order:**

1. Run the golden path. Step 3 is the point: a valid spec and a drifted service.
2. Put `openapi-spec-validator` in CI for a spec you own. It takes ten minutes
   and usually finds something.
3. Write the field-set comparison from step 4 against one real endpoint. The
   first undocumented field you find is your evidence.

**What makes it credible rather than decorative.** Neither of this guide's
repositories documents an HTTP API, which the [demonstrated](../demonstrated.md)
page records. What travels is the distinction and the measurement behind it: a
spec that validates cleanly while the service returns an undocumented field,
and the honest note that one of the two findings is a heuristic rather than a
violation.

## Related

- [Generated API reference](api-reference-generation.md), the same problem for a library
- [Content models](content-model.md), schema validation applied to prose
- [Cold-start testing](coldstart-testing.md), where a mock server from the spec helps
- [Documentation CI](documentation-ci.md), which of these gates block a merge
