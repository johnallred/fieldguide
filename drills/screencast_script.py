#!/usr/bin/env python3
"""A screencast script is a code sample with timestamps. Test it like one.

    python3 drills/screencast_script.py

Reproduces the three states the `screencasts` page quotes, in one run: a beat
that was never true, a clean pass after the tool gains the flag the narration
described, and the same script going stale when the tool's output changes.

Everything happens in a temporary directory; nothing is written beside this
file. The point of the `at` field is the failure message: it names which
seconds of video are wrong, which is the only thing that makes a stale
recording actionable rather than merely known.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = """\
title: Listing your widgets
beats:
  - at: "00:12"
    say: "First we list the widgets, and you should see three of them."
    run: "python3 widget.py"
    expect: "widgets: 3"
  - at: "00:41"
    say: "Now the same thing as JSON."
    run: "python3 widget.py --json"
    expect: '{"widgets": 3}'
"""

#: The tool as it stood when the script was written: no `--json`.
WIDGET_BEFORE = """\
import sys
def main(argv):
    print("widgets: 3")
    return 0
if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
"""

#: The flag implemented, so both beats are true.
WIDGET_WITH_FLAG = """\
import sys, json
def main(argv):
    if "--json" in argv:
        print(json.dumps({"widgets": 3}))
    else:
        print("widgets: 3")
    return 0
if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
"""

#: Upstream changes the human-readable line, as upstream does.
WIDGET_AFTER = WIDGET_WITH_FLAG.replace('print("widgets: 3")', 'print("3 widgets found")')


def parse_beats(text: str) -> list[dict[str, str]]:
    """Read the beats without a YAML dependency, so the drill needs nothing.

    The format is fixed and tiny: a `beats:` list of `- at:` items whose other
    keys are `say`, `run` and `expect`. A real implementation would use
    `yaml.safe_load`; this keeps the drill runnable on a bare interpreter.
    """
    beats: list[dict[str, str]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- at:"):
            beats.append({"at": stripped.split(":", 1)[1].strip().strip("\"'")})
        elif beats and ":" in stripped and not stripped.startswith("title:"):
            key, _, value = stripped.partition(":")
            if key in ("say", "run", "expect"):
                beats[-1][key] = value.strip().strip("\"'")
    return beats


def check(beats: list[dict[str, str]], cwd: Path) -> int:
    """Run every beat and report drift by timestamp. Returns an exit code."""
    bad = []
    for beat in beats:
        result = subprocess.run(
            beat["run"].split(), capture_output=True, text=True, timeout=30, cwd=cwd
        )
        got = result.stdout.strip()
        if beat["expect"] not in got:
            bad.append(f'  {beat["at"]}  expected {beat["expect"]!r}, got {got!r}')
    for line in bad:
        print("DRIFT" + line)
    print(f"{len(beats) - len(bad)}/{len(beats)} beats still match what the video shows")
    return 1 if bad else 0


def main() -> int:
    beats = parse_beats(SCRIPT)
    assert len(beats) == 2, f"expected 2 beats, parsed {len(beats)}"
    # The expectation is written with JSON's spacing, so compare like for like.
    beats[1]["expect"] = json.dumps({"widgets": 3})

    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        widget = work / "widget.py"

        print("step 2: the script as written, against the tool as it was")
        widget.write_text(WIDGET_BEFORE, encoding="utf-8")
        first = check(beats, work)
        print(f"exit={first}\n")

        print("step 3: implement the flag the narration described")
        widget.write_text(WIDGET_WITH_FLAG, encoding="utf-8")
        clean = check(beats, work)
        print(f"exit={clean}\n")

        print("step 4: upstream changes the human-readable output")
        widget.write_text(WIDGET_AFTER, encoding="utf-8")
        stale = check(beats, work)
        print(f"exit={stale}")

    print(
        "\nThe timestamp is the whole point: 00:12 says which four seconds of a\n"
        "recording are now wrong. The script can be fixed; the recording cannot,\n"
        "which is the argument about when video is worth its cost."
    )
    return 0 if (first, clean, stale) == (1, 0, 1) else 1


if __name__ == "__main__":
    sys.exit(main())
