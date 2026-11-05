---
title: Security guidance as encoded standard
summary: "Documentation samples get copy-pasted into production, so the security review belongs in CI rather than in a wiki page."
diataxis: how-to
audience: developer
concept: security-documentation
tags: [ia, supporting]
---

# Security guidance as encoded standard

`supporting` · difficulty 2 · 3h

!!! quote "Asked for by name"
    NVIDIA: "Encode standards (user stories, release readiness, onboarding, security guidance) into templates, validators, and guided workflows rather than static documents"

**Prerequisites:** [Style guides and terminology management](style-guide.md)

## What it is

Turning the security rules your documentation must follow into checks that run,
rather than a page telling authors to be careful. NVIDIA's bullet is explicit
about the preference: templates, validators and guided workflows **rather than
static documents**.

The specific problem is that documentation code samples are the most
copy-pasted code in any organisation. A sample is read as a recommendation, so
an insecure sample propagates the insecurity into every project that follows
the quickstart.

## Why the job asks for it

Because a documentation site is a distribution channel for patterns.

An engineer who writes `verify=False` in their own code has made a local
mistake. A documentation page that writes `verify=False` has made that mistake
in every project that follows it, with the authority of official guidance, for
as long as the page lives. The blast radius is the difference, and it is why
security guidance belongs on the list of standards worth encoding.

The second reason is in NVIDIA's own phrasing: you will "interface with
Security". A security team can give you a policy document. Converting that into
a validator is the part they cannot do for you, and arriving with one is a
much better opening than arriving with questions.

## The golden path

Write a linter for documentation samples, find out it misses one of the things
it was written to catch, and fix the quickstart it ran against. About thirty
minutes.

Committed as `drills/security_lint.py`, which walks all three states in one
run. A test asserts the drill still prints the findings quoted below, and
that its two sample quickstarts are the ones this page tells you to write.

**Step 1: a quickstart with six realistic problems**

````bash
mkdir -p sec-demo/docs && cd sec-demo
cat > docs/quickstart.md <<'MDEOF'
# Quickstart

Install and configure:

```bash
curl -sSL https://example.com/install.sh | sudo bash
export WIDGET_TOKEN=sk-live-abc123def456
```

Connect from Python:

```python
import requests
r = requests.get("https://api.example.com/widgets", verify=False)
client = Client(token="sk-live-abc123def456")
```

Grant access:

```bash
chmod 777 /etc/widget
aws s3api put-bucket-acl --bucket widgets --acl public-read
```
MDEOF
````

None of this is exotic. Every line appears in real documentation.

**Step 2: the rules, as data**

```python
RULES = [
    ("pipe-to-shell", re.compile(r"curl[^|\n]*\|\s*(sudo\s+)?(ba)?sh"),
     "piping a downloaded script into a shell teaches an unverifiable install"),
    ("tls-disabled", re.compile(r"verify\s*=\s*False|--insecure\b|InsecureSkipVerify"),
     "disabling certificate verification"),
    ("hardcoded-secret",
     re.compile(r"""(token|key|secret|password)\s*[=:]\s*["']?(sk-|pk_|AKIA)[A-Za-z0-9_-]{6,}"""),
     "a credential-shaped literal; use a placeholder or an env var"),
    ("world-writable", re.compile(r"chmod\s+(777|a\+rwx|o\+w)"),
     "world-writable permissions"),
    ("public-acl", re.compile(r"--acl\s+public-read|public-read-write"),
     "granting public access to a bucket"),
]
```

Each rule carries a name, a pattern and the reason, because a finding that does
not explain itself gets suppressed rather than fixed.

**Step 3: run it, and count carefully**

```bash
python3 seclint.py
```

```
SEC  docs/quickstart.md:6:  pipe-to-shell: piping a downloaded script into a shell teaches an unverifiable install
SEC  docs/quickstart.md:14: tls-disabled: disabling certificate verification
SEC  docs/quickstart.md:15: hardcoded-secret: a credential-shaped literal; use a placeholder or an env var
SEC  docs/quickstart.md:21: world-writable: world-writable permissions
SEC  docs/quickstart.md:22: public-acl: granting public access to a bucket
FAIL: 5 finding(s)
```

Five findings. There are **two** hardcoded secrets in that page, on lines 7
and 15, and only line 15 was reported.

**Step 4: the miss**

```python
line = "export WIDGET_TOKEN=sk-live-abc123def456"
print(bool(re.search(pat, line)))        # False
print(bool(re.search(pat, line, re.I)))  # True
```

`WIDGET_TOKEN` is uppercase and the pattern's alternation is lowercase. The
rule was case-sensitive, and environment variables are conventionally
uppercase, so the rule missed the single most common way a credential appears
in a shell sample.

```python
re.compile(r"""(?i)(token|key|secret|password)\s*[=:]\s*...""")
```

```
SEC  docs/quickstart.md:6:  pipe-to-shell: piping a downloaded script into a shell teaches an unverifiable install
SEC  docs/quickstart.md:7:  hardcoded-secret: a credential-shaped literal; use a placeholder or an env var
SEC  docs/quickstart.md:14: tls-disabled: disabling certificate verification
SEC  docs/quickstart.md:15: hardcoded-secret: a credential-shaped literal; use a placeholder or an env var
SEC  docs/quickstart.md:21: world-writable: world-writable permissions
SEC  docs/quickstart.md:22: public-acl: granting public access to a bucket
FAIL: 6 finding(s)
```

This is the third time case sensitivity has silently disabled a rule in this
guide: once in a Vale rule on the [style guide](style-guide.md) page, and twice
here counting the rule and the finding it hid. For security rules it matters
more, because the failure mode is a green build on a page that teaches a
credential leak.

**Step 5: fix the documentation, which is the point**

````bash
cat > docs/quickstart.md <<'MDEOF'
# Quickstart

Install, verifying the download first:

```bash
curl -sSLO https://example.com/install.sh
sha256sum -c install.sh.sha256
bash install.sh
export WIDGET_TOKEN="$(cat ~/.config/widget/token)"
```

Connect from Python:

```python
import os
import requests

r = requests.get("https://api.example.com/widgets")
client = Client(token=os.environ["WIDGET_TOKEN"])
```

Grant access to the service account only:

```bash
chmod 750 /etc/widget
aws s3api put-bucket-acl --bucket widgets --acl private
```
MDEOF

python3 seclint.py; echo "exit=$?"
````

```
ok: 0 finding(s)
exit=0
```

Note what changed in the install step. The insecure version was shorter and
the secure version teaches verification, which is the real tradeoff: secure
samples are usually longer, and the pressure on a quickstart is always toward
brevity.

**What you built.** A gate that fails a build on a sample readers should not
copy, and a corrected quickstart.

## Reference

### Rules worth encoding

| Rule | Catches |
|---|---|
| Pipe-to-shell | `curl ... | sudo bash` installs |
| TLS verification disabled | `verify=False`, `--insecure`, `InsecureSkipVerify` |
| Credential-shaped literals | `sk-`, `pk_`, `AKIA`, long hex after a key-ish name |
| World-writable permissions | `chmod 777` |
| Public bucket or object ACLs | `--acl public-read` |
| Long-lived credentials where short-lived exist | A static key where OIDC is available |
| `latest` tags in a security context | Unpinned base images in a sample |
| Secrets in a URL | `https://user:pass@host` |

Use `(?i)` on all of them. Environment variables are uppercase, Go field names
are capitalised, and YAML keys vary.

### What this is not

| Not this | Why |
|---|---|
| A code scanner for the product | That is the security team's job on the real codebase |
| A substitute for threat modelling | It checks patterns, not design |
| A claim of security review | It is a floor; the pages may still advise badly |

Be precise about that last one in an interview. The gate catches a list of
known-bad patterns in samples. It does not mean the documentation gives secure
advice, and a page can pass every rule while recommending an insecure
architecture in prose.

### The other standards on NVIDIA's list

The bullet names four, and all four follow the same pattern:

| Standard | Static document | Encoded as |
|---|---|---|
| Security guidance | "Be careful with credentials" | The linter above |
| [Release readiness](release-readiness.md) | A checklist page | A CI gate per item |
| Onboarding | A "getting started for writers" page | A scaffold command plus local gates |
| [User stories](user-stories.md) | A template in a wiki | An issue template with required fields |

The move is identical each time: find the part of the standard that is a
rule, make it fail a build, and leave in writing only the part that needs
judgment. Which is the same split as the [style guide](style-guide.md).

### Working with a security team

| They give you | You turn it into |
|---|---|
| A policy document | A rule list, and questions about the ambiguous parts |
| An approved-patterns list | Templates and scaffolds that produce them by default |
| A finding on a doc page | A rule, so the class cannot return |
| A review requirement | A gate plus a named reviewer for what the gate cannot judge |

The third row is the one that compounds. A security finding on a single page is
worth fixing once; converted into a rule it is worth fixing forever, and that
conversion is the thing you are being hired to do rather than asked to do.

## How to talk about it

**Lead with blast radius.** "Documentation samples are the most copy-pasted
code in an organisation, and a sample reads as a recommendation. An engineer
writing `verify=False` has made a local mistake; a quickstart doing it has made
that mistake in every project that follows it, with official authority. So the
security rules go in CI rather than in a page asking authors to be careful."

**The follow-up is where the rules come from**, and the good answer is the
security team's own policy converted into patterns, plus every past finding on
a doc page turned into a rule so the class cannot return.

**The tradeoff to volunteer.** Secure samples are longer. Verifying a checksum
before running an installer is three lines where the insecure version is one,
and the pressure on a quickstart is always toward brevity because
[time to first success](time-to-first-success.md) is the metric. That tension
is real, and the honest resolution is that the quickstart gets the secure
version and the brevity is bought elsewhere, not by teaching a bad pattern.

**One sharper point.** Use case-insensitive patterns. My own rule for
credential literals was case-sensitive and missed
`export WIDGET_TOKEN=sk-live-...`, which is the single most common shape a
secret takes in a shell sample, because environment variables are uppercase by
convention. A security rule that silently matches nothing is worse than no rule,
and you only find out by writing a fixture that must fail.

## How to prove it

**The artifact.** A sample linter in CI with a named rule list, plus one
commit where it caught something in your own documentation.

**Three things to do, in order:**

1. Run the golden path, and count the findings before reading step 4.
2. Point the linter at a quickstart you own. Pipe-to-shell and credential
   literals are both common enough that you will probably find one.
3. Take the last security finding anyone raised about your documentation and
   write it as a rule.

**What makes it credible rather than decorative.** The linter is committed as
`drills/security_lint.py` and reproduces all three states in one run: five
findings against six planted problems, six once the rule is case-insensitive,
and none once the quickstart is actually repaired. A test asserts that the
drill still prints the lines quoted above, in both directions, so the figures
on this page cannot drift from the code that produces them.

What neither repository has is a security gate in its own CI, which the
[demonstrated](../demonstrated.md) page records: this is a linter with a
fixture, not a policy applied to a real corpus. What travels is the honest
account of the miss, which is the more useful half. Six problems planted, five
found, and the sixth hidden by a case-sensitivity bug in the rule written to
catch exactly that.

## Related

- [Style guides and terminology management](style-guide.md), the same mechanical-versus-editorial split
- [Writing custom linters](custom-linters.md), how to build the checks
- [Release readiness](release-readiness.md), another standard from the same bullet
- [Code-sample validation](code-sample-validation.md), which checks samples run rather than whether they are safe
