#!/usr/bin/env python3
"""Four guardrail layers against eight fluent answers, six of which are wrong.

    python3 drills/guardrails.py

Reproduces the matrix the `hallucination-guardrails` page publishes: which
layer catches which failure, and which failures a single layer would miss.

Like `drills/crawlability.py`, this stages the page's own files in a temporary
directory and runs the page's `run.py` as a subprocess, so the code being
demonstrated is the code the page prints rather than a second copy of it. A
test asserts all five files still match the page, and a second test parses the
page's results table and compares it to the matrix this run produces, so the
table cannot drift from the code that generates it.

The finding the matrix exists for: layer 2, the vocabulary check, is the only
one that catches a fabricated flag name once the fabrication is surrounded by
real text. Grounding passes `flag-camouflaged` and `flag-appended`, because one
invented identifier among several matching content words sits inside any
support threshold loose enough to permit paraphrase. A team with grounding and
no vocabulary list has a guardrail that catches the obvious fabrications and
waves through the convincing ones, which is the worse failure mode: it produces
confidence rather than coverage.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

#: The page's five heredocs, verbatim and in the order it writes them.
FILES: tuple[tuple[str, str], ...] = (
    ('context.json', r"""{
  "c3": "max_memory_gb caps the GPU memory the server will allocate. The default is 16.",
  "c6": "Pass --dry-run to preview changes without applying them.",
  "c1": "batch_size controls how many requests are grouped per forward pass. The default is 32."
}
"""),
    ('known.json', r"""{
  "flags": ["--dry-run", "--config", "--verbose", "max_memory_gb", "batch_size"],
  "versions": ["2.0", "2.2", "2.4", "2.6"]
}
"""),
    ('answers.json', r"""[
  {"label": "correct",
   "text": "Pass --dry-run to preview changes. [c6]"},
  {"label": "flag-bare",
   "text": "Pass --retry-budget to bound retries. [c6]"},
  {"label": "flag-camouflaged",
   "text": "Pass --retry-budget to preview changes without applying them. [c6]"},
  {"label": "flag-appended",
   "text": "max_memory_gb caps the GPU memory the server will allocate, and --memory-strict enforces it. [c3]"},
  {"label": "invented-number",
   "text": "max_memory_gb defaults to 24. [c3]"},
  {"label": "invented-version",
   "text": "This requires widget 3.1 or newer. [c3]"},
  {"label": "plausible-fusion",
   "text": "max_memory_gb defaults to 32. [c3]"},
  {"label": "evasive",
   "text": "Set the memory ceiling in the configuration file. [c3]"}
]
"""),
    ('guards.py', '"""Four guardrail layers, in increasing cost, each catching what the\nprevious one cannot.\n\nThe ordering is the design. A cheap deterministic check that runs on every\nanswer is worth more than an expensive check that runs on a sample, because\nthe cheap one cannot be skipped under deadline pressure.\n\n  1 GROUNDING    content words and numbers against the cited chunk\n  2 VOCABULARY   every flag and version against a KNOWN-GOOD list\n  3 SPECIFICITY  an answer that avoids the question rather than refusing\n  4 ABSTENTION   was a refusal available, and did the model take it\n\nLayer 2 is the one that catches the flag-name fabrication, and it is the one\nmost teams do not have, because it needs a list of real identifiers that\nnothing else in the pipeline requires.\n"""\nimport json\nimport re\n\nCITATION = re.compile(r"\\[(\\w+)\\]")\nFLAG = re.compile(r"(?<![\\w-])(--[a-z][a-z0-9-]*|[a-z][a-z0-9]*(?:_[a-z0-9]+)+)")\nVERSION = re.compile(r"\\bwidget (\\d+\\.\\d+)\\b", re.I)\nNUMBER = re.compile(r"\\b\\d+(?:\\.\\d+)?\\b")\n\nSTOP = {\n    "the", "a", "an", "to", "is", "are", "of", "in", "on", "for", "with",\n    "and", "or", "it", "its", "set", "pass", "without", "by", "this", "that",\n    "will", "can", "you", "your", "not", "from", "which", "default", "defaults",\n}\nSUPPORT_THRESHOLD = 0.6\n\n#: Phrases that describe an action without naming it. A model that cannot\n#: find the answer and will not refuse produces these.\nVAGUE = (\n    "in the configuration file", "in the settings", "as appropriate",\n    "the relevant", "accordingly", "as needed", "the appropriate",\n)\nREFUSAL = "i could not find this in the documentation"\n\n\ndef words(text):\n    return [\n        w for w in re.findall(r"[a-z0-9_-]+", text.lower())\n        if w not in STOP and len(w) > 1\n    ]\n\n\ndef guard_grounding(answer, context, known):\n    """Layer 1: is the claim supported by the chunk it cites?"""\n    findings = []\n    cited = CITATION.findall(answer)\n    body = CITATION.sub("", answer).strip()\n    if not cited:\n        return [("uncited", "no citation")]\n\n    source = " ".join(context.get(c, "") for c in cited)\n    source_words = set(words(source))\n    present = [w for w in words(body) if w in source_words]\n    ratio = len(present) / len(words(body)) if words(body) else 1.0\n    if ratio < SUPPORT_THRESHOLD:\n        findings.append(("unsupported", f"{ratio:.0%} of content words in {cited}"))\n\n    absent = set(NUMBER.findall(body)) - set(NUMBER.findall(source))\n    if absent:\n        findings.append(("ungrounded-number", f"{sorted(absent)} not in {cited}"))\n    return findings\n\n\ndef guard_vocabulary(answer, context, known):\n    """Layer 2: does every identifier and version actually exist?\n\n    This is the layer that catches a fabricated flag name. Grounding cannot:\n    a plausible flag is a single unmatched content word, which sits inside\n    any support threshold loose enough to allow paraphrase.\n    """\n    findings = []\n    body = CITATION.sub("", answer)\n    for flag in set(FLAG.findall(body)):\n        if flag not in known["flags"]:\n            findings.append(("unknown-identifier", f"{flag!r} is not a real flag"))\n    for version in set(VERSION.findall(body)):\n        if version not in known["versions"]:\n            findings.append(("unknown-version", f"widget {version} does not exist"))\n    return findings\n\n\ndef guard_specificity(answer, context, known):\n    """Layer 3: is the answer avoiding the question?"""\n    lowered = answer.lower()\n    if lowered.strip().startswith(REFUSAL):\n        return []\n    for phrase in VAGUE:\n        if phrase in lowered:\n            return [("evasive", f"says {phrase!r} instead of naming the thing")]\n    return []\n\n\ndef guard_abstention(answer, context, known):\n    """Layer 4: did it answer when it should have refused?\n\n    Heuristic and deliberately weak: if the answer names no identifier and no\n    number and is not a refusal, it has probably asserted something it could\n    not support. Reported as a warning, never as a hard failure.\n    """\n    body = CITATION.sub("", answer).lower()\n    if body.strip().startswith(REFUSAL):\n        return []\n    if not FLAG.search(body) and not NUMBER.search(body):\n        return [("unspecific", "no identifier or value; a refusal may have been correct")]\n    return []\n\n\nLAYERS = [\n    ("grounding", guard_grounding),\n    ("vocabulary", guard_vocabulary),\n    ("specificity", guard_specificity),\n    ("abstention", guard_abstention),\n]\n\n\ndef check(answer, context, known):\n    out = []\n    for name, layer in LAYERS:\n        for kind, why in layer(answer, context, known):\n            out.append((name, kind, why))\n    return out\n'),
    ('run.py', r"""import json

from guards import LAYERS, check

context = json.load(open("context.json"))
known = json.load(open("known.json"))
answers = json.load(open("answers.json"))

for answer in answers:
    findings = check(answer["text"], context, known)
    verdict = "PASS" if not findings else "REJECT"
    print(f"{verdict:<7} [{answer['label']}] {answer['text']}")
    for layer, kind, why in findings:
        print(f"        {layer}/{kind}: {why}")
    print()

print("=" * 68)
print("which layer caught each failure, and which layers alone would miss it")
print("=" * 68)
header = f"{'answer':<30}" + "".join(f"{n[:9]:>11}" for n, _ in LAYERS)
print(header)
print("-" * len(header))
for answer in answers:
    row = f"{answer['label']:<30}"
    for name, layer in LAYERS:
        hit = layer(answer["text"], context, known)
        row += f"{('CAUGHT' if hit else '-'):>11}"
    print(row)
"""),
)


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for name, body in FILES:
            (root / name).write_text(body, encoding="utf-8")

        result = subprocess.run(
            [sys.executable, "run.py"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=60,
        )
        sys.stdout.write(result.stdout)
        if result.stderr:
            sys.stderr.write(result.stderr)

    if result.returncode != 0:
        print("unexpected: the page's run.py failed", file=sys.stderr)
        return 1

    # The matrix is the deliverable, so fail loudly if the two rows the page's
    # argument rests on stop behaving the way the page says they do.
    lines = result.stdout.splitlines()
    rows = {
        line.split()[0]: line.split()[1:]
        for line in lines
        if line and not line.startswith((" ", "-", "=", "PASS", "REJECT", "answer"))
    }
    for label in ("flag-camouflaged", "flag-appended"):
        row = rows.get(label)
        if row is None:
            print(f"unexpected: no row for {label}", file=sys.stderr)
            return 1
        grounding, vocabulary = row[0], row[1]
        if (grounding, vocabulary) != ("-", "CAUGHT"):
            print(
                f"unexpected: {label} is now {grounding}/{vocabulary} rather than "
                "passing grounding and failing vocabulary, which is the page's "
                "entire argument",
                file=sys.stderr,
            )
            return 1

    print("\nThe two rows the page's argument rests on still behave as it says:")
    print("a camouflaged fabrication passes grounding and only vocabulary stops it.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
