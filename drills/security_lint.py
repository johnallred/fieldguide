#!/usr/bin/env python3
"""A security linter for documentation samples, and the rule that missed one.

    python3 drills/security_lint.py

Reproduces what the `security-documentation` page quotes: a quickstart with six
realistic problems, a linter that finds five, the reason it missed the sixth,
and a clean run after both the rule and the quickstart are fixed.

The miss is the point. The rule was case-sensitive and environment variables
are conventionally uppercase, so it missed the single most common way a
credential appears in a shell sample. A linter's own blind spot is worth more
than its catch list, because the catch list is what you expected.
"""

from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path

#: The page's step-1 heredoc, verbatim: six problems, every one of which
#: appears in real documentation. A test asserts this still matches the page,
#: in both directions, so neither can be edited without the other.
QUICKSTART_BAD = """\
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
"""

QUICKSTART_FIXED = """\
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
"""

def rules(case_insensitive: bool) -> list[tuple[str, re.Pattern[str], str]]:
    """The page's RULES block, verbatim, with one knob: the credential rule's case.

    A rule that does not explain itself gets suppressed rather than fixed, so
    each carries a name, a pattern and a reason the author of the sample can
    act on without asking what the linter meant.
    """
    flag = "(?i)" if case_insensitive else ""
    return [
        ("pipe-to-shell", re.compile(r"curl[^|\n]*\|\s*(sudo\s+)?(ba)?sh"),
         "piping a downloaded script into a shell teaches an unverifiable install"),
        ("tls-disabled", re.compile(r"verify\s*=\s*False|--insecure\b|InsecureSkipVerify"),
         "disabling certificate verification"),
        ("hardcoded-secret",
         re.compile(flag + r"""(token|key|secret|password)\s*[=:]\s*["']?(sk-|pk_|AKIA)[A-Za-z0-9_-]{6,}"""),
         "a credential-shaped literal; use a placeholder or an env var"),
        ("world-writable", re.compile(r"chmod\s+(777|a\+rwx|o\+w)"),
         "world-writable permissions"),
        ("public-acl", re.compile(r"--acl\s+public-read|public-read-write"),
         "granting public access to a bucket"),
    ]


def lint(docs: Path, case_insensitive: bool) -> int:
    findings = []
    for path in sorted(docs.rglob("*.md")):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for name, pattern, reason in rules(case_insensitive):
                if pattern.search(line):
                    rel = path.relative_to(docs.parent).as_posix()
                    # The number field is padded so the rule names line up;
                    # an unaligned findings list is read as noise.
                    findings.append(f"SEC  {rel}:{str(number) + ':':<4}{name}: {reason}")
    for finding in findings:
        print(finding)
    if findings:
        print(f"FAIL: {len(findings)} finding(s)")
    else:
        print("ok: 0 finding(s)")
    return 1 if findings else 0


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        docs = root / "docs"
        docs.mkdir()
        page = docs / "quickstart.md"

        print("step 3: run the linter against six planted problems\n")
        page.write_text(QUICKSTART_BAD, encoding="utf-8")
        strict = lint(docs, case_insensitive=False)

        print(
            "\nFive, and six were planted. The missing one is the `export` line:\n"
            "`WIDGET_TOKEN` is uppercase and the pattern's alternation was lowercase,\n"
            "so the rule missed the commonest shape a credential takes in a shell\n"
            "sample. Case sensitivity, in a rule written to catch exactly that.\n"
        )

        print("step 4: the same quickstart, with the rule case-insensitive\n")
        fixed_rule = lint(docs, case_insensitive=True)

        print("\nstep 5: and the quickstart actually repaired\n")
        page.write_text(QUICKSTART_FIXED, encoding="utf-8")
        clean = lint(docs, case_insensitive=True)
        print(f"exit={clean}")

    ok = (strict, fixed_rule, clean) == (1, 1, 0)
    if not ok:
        print("\nunexpected: the three states did not come out 1, 1, 0", file=sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
