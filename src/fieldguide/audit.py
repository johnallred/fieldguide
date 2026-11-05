"""Measurements this guide publishes about itself.

Several pages quote figures about the corpus: how many golden paths state a
duration, how many pages carry a sentence over 45 words, what fraction of proof
tasks say how a reader would know they succeeded. Those figures were produced
by scripts that lived nowhere, which fails the standard the drills in
`drills/` were held to: a number a reader cannot reproduce is a number they
have to take on trust.

So the measurements live here, behind `fieldguide audit`, and the pages cite
them. Running it on a changed corpus is also how the figures get caught when
they go stale, which has happened once already: every page written before the
corpus finished growing quoted a count from the corpus as it stood.

Three habits are deliberate, each learned by getting it wrong first:

- Code is never prose. Fenced blocks are removed with `fences.fence_spans`,
  which tracks marker length and skips heredoc bodies. A naive toggle agrees
  with it to 0.2 per cent across the corpus and is wrong on a fifth of pages.
- Headings are anchored. A page that quotes `## How to prove it` inside a code
  fence will split a `str.partition` in the wrong place, which it did.
- Markup is stripped before matching words. Classifying tasks by their opening
  verb put the rate at 54 per cent until the `**` was removed; it is 95.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from .fences import fence_spans, heredoc_body_lines
from .registry import RETIRED_LABELS, STRUCTURAL_LABELS, Registry

#: Front matter, which a reader never sees.
FRONT_MATTER = re.compile(r"^---\n.*?\n---\n", re.S)

#: HTML comments, which carry the scaffold's authoring prompts.
HTML_COMMENT = re.compile(r"<!--.*?-->", re.S)

#: A sentence boundary, allowing a closing quote or bracket after the stop.
#: Without the trailing character class, `."` is not an ending and two
#: sentences merge into one 86-word reading.
#: A sentence boundary: a terminator, any closing punctuation or markup, then
#: whitespace. The markup class is the correction. The first version allowed a
#: closing quote or bracket and nothing else, so a sentence ending in bold,
#: which is every one of this corpus's bolded labels, was never split from the
#: sentence after it. Three of the seven "sentences over 60 words" it reported
#: were two sentences with a `.**` between them.
SENTENCE = re.compile(r'(?<=[.!?])[\"”’\')\]*_`]*\s+')

#: Headings, list items and table rows are not prose and never form sentences.
NOT_PROSE = ("#", ">", "|", "!!!", "- ", "* ", "1.", "2.", "3.")

#: A bullet or numbered list marker at the start of a stripped line.
LIST_MARKER = re.compile(r"^(?:[-*+] |\d+\. )")

#: A duration, in any of the forms the corpus actually uses. Matched against
#: whitespace-normalised text, because "About thirty\nminutes" wraps.
DURATION = re.compile(
    r"\b(?:\d+|ten|fifteen|twenty|thirty|forty|fifty|sixty|ninety)"
    r"(?:-five)?[- ]?(?:minutes?|hour)",
    re.I,
)

#: The closing line of a golden path, which states what the exercise produced.
CLOSING_RESULT = re.compile(r"\*\*What you (?:built|learned)")

#: The proof-section task list. Three wordings are in use; see ADDITIONS.md.
TASK_LABEL = re.compile(r"^\*\*Three things to do[^*]*\*\*", re.M)
TASK_ITEM = re.compile(r"^\d+\.\s+(.*(?:\n   +.*)*)", re.M)

#: A bolded line-leading label, which is how every structural element in this
#: corpus is marked. Deliberately not anchored to a known list of wordings.
BOLD_OPENER = re.compile(r"\*\*[A-Z][^*]{2,70}?\.?:?\*\*")

EMPHASIS = re.compile(r"[*`]+")
INLINE_LINK = re.compile(r"\[([^\]]+)\]\([^)]+\)")
CONCEPT_LINK = re.compile(r"\]\(([a-z0-9-]+)\.md")

#: Openings that commit a reader to an action. A task that does not begin with
#: one is usually conditional ("If your corpus...") rather than defective.
IMPERATIVE = re.compile(
    r"^(?:Run|Measure|Count|Build|Write|Add|Take|Pick|Find|Open|Check|Audit|Point"
    r"|Delete|Replace|Try|Clone|Instrument|Generate|Convert|Tag|Plant|Grep|Export"
    r"|Time|Classify|Rewrite|Record|Put|Compute|Compare|Print|Parse|Set|Turn|Move"
    r"|Follow|Ask|Make|Report|Split|Pull|Send|Swap|Read|List|Diff|Stop|Keep|Give"
    r"|Label|Mark|Name|Sit|Watch|Walk|Pin|Drop|Wire|Hand|Choose|Look|Go|Do|Start"
    r"|Teach|Review|Trace|Sample|Spend|Redo|Use|Publish|Track|Install)\b"
)

#: A task states a success criterion when it says how the reader would know.
#: A task states a success criterion when it tells the learner something
#: falsifiable about the result: a value to compare theirs against, a
#: conditional test, or an instruction to predict before looking. Saying why
#: the task matters is not a criterion, and neither is an interpretation that
#: holds whatever the result turns out to be ("whatever it flags has been
#: wrong for a while" is true before the learner runs anything).
#:
#: The first version of this was a keyword list, and it included `against`.
#: Sixteen of its 53 matches were the preposition in "run it against a corpus
#: you own", which states no criterion at all, while it missed every
#: conditional, every predicted value and every comparison to a figure. It
#: reported 17 per cent for a corpus measuring about a third, and that figure
#: was published as the guide's own weakest number.
#:
#: This version is scored against `tests/fixtures/criterion_labels.json`, 60
#: tasks labelled by hand before it was written, in two samples: one used to
#: design these patterns and one held out and used once. It is not a parser
#: and it will miss phrasings nobody has written yet; two were found while
#: adding criteria to the corpus, "you will know X when Y" and "more than N
#: means M", both of which are listed below because they were misses first.
CRITERION = re.compile(
    r"""\bpredict\b|\bbefore you look\b|\bout loud\b|\bexpect(?:ed|s)?\b|\bassert\b|\bshould (?:be|see|fail|pass|drop|rise)\b|\bthe answer is\b|\bin mine\b|\bmine said\b|\bif\b[^.!?]{3,90}[,:]|\bif (?:it|that|yours|the \w+) (?:is|are|was|were) (?:above|below|under|over|not|more|less)\b|\bif not\b|\bif nobody\b|\bif none\b|\bif you find\b|\bif there (?:is|are)\b|\b(?:it|you) will (?:find|see|get|have|probably)\b|\b(?:usually|typically|in most|almost always|commonly|probably) [a-z]|\b(?:near zero|about \d|above \d|above about|under \d|a third again)\b|\bwatch (?:the|it|your)\b|\bseeing your own\b|\bopposite outcome\b|\bnot subtle\b|\bwhatever happens\b|\bto see whether\b|\bconfirm whether\b|\byou will know\b|\b(?:more|fewer|less) than [^.!?]{0,45}\bmeans\b""",
    re.I,
)

#: A task is assessable at all when it produces something inspectable.
ARTIFACT = re.compile(
    r"\b(?:file|repo|repository|script|page|report|commit|branch|diff|CI|manifest"
    r"|index|artifact|number|count|output|log|test|list|table|graph|queries|corpus"
    r"|site|sample)\b",
    re.I,
)


def heading(name: str) -> re.Pattern[str]:
    """An anchored `## ` heading.

    Anchored because `assessment.md` quotes `"## How to prove it"` inside a
    Python sample, and an unanchored search split that page at its own code.
    """
    return re.compile(rf"^## {re.escape(name)}$", re.M)


PROOF_HEADING = heading("How to prove it")
RELATED_HEADING = heading("Related")


def code_lines(lines: list[str]) -> set[int]:
    """The 1-indexed lines inside a fenced block, heredoc bodies included."""
    spans = fence_spans(lines, skip=heredoc_body_lines(lines))
    return {n for span in spans for n in range(span.open_line, span.close_line + 1)}


def prose_of(text: str) -> str:
    """The text a reader reads: no front matter, comments, code, or furniture.

    Non-prose lines become empty rather than disappearing, so a heading between
    two paragraphs still separates them instead of joining their sentences.
    """
    body = HTML_COMMENT.sub(" ", FRONT_MATTER.sub("", text))
    lines = body.splitlines()
    inside = code_lines(lines)
    kept = []
    for number, line in enumerate(lines, 1):
        if number in inside or line.strip().startswith(NOT_PROSE):
            kept.append("")
        else:
            kept.append(line)
    return "\n".join(kept)


def sentences(text: str) -> list[int]:
    """Word counts of every sentence a reader would read."""
    out = []
    for block in prose_of(text).split("\n\n"):
        for sentence in SENTENCE.split(" ".join(block.split())):
            words = len(sentence.split())
            if words >= 3:
                out.append(words)
    return out


def list_sentences(text: str) -> list[int]:
    """Word counts of sentences inside bullet and numbered list items.

    List items are excluded from the prose measurement, which is right: an
    item is not a paragraph and reads differently. But that exclusion is a
    hole in the per-page maximum sentence length, because a seventy-word
    sentence becomes compliant the moment somebody puts a hyphen in front of
    it, and the reader is no better off unless the content was genuinely a
    list.

    The first version of this measured each item's total words, which was the
    wrong instrument: the longest items in this corpus are proof tasks of four
    short sentences, and a 68-word item made of four sentences is not a
    readability problem. Sentences inside items are the comparable unit, so
    that is what this returns.
    """
    body = HTML_COMMENT.sub(" ", FRONT_MATTER.sub("", text))
    lines = body.splitlines()
    # Code is excluded the way prose excludes it, but list markers are kept,
    # which is why this cannot call `prose_of`: that blanks an item's first
    # line on purpose.
    inside = code_lines(lines)

    items: list[str] = []
    current: list[str] = []
    for number, line in enumerate(lines, 1):
        stripped = line.strip()
        if number in inside or not stripped:
            if current:
                items.append(" ".join(current))
                current = []
            continue
        if LIST_MARKER.match(stripped):
            if current:
                items.append(" ".join(current))
            current = [LIST_MARKER.sub("", stripped)]
        elif current and line.startswith(("  ", "\t")):
            current.append(stripped)
        elif current:
            items.append(" ".join(current))
            current = []
    if current:
        items.append(" ".join(current))

    out: list[int] = []
    for item in items:
        for sentence in SENTENCE.split(" ".join(item.split())):
            words = len(sentence.split())
            if words >= 3:
                out.append(words)
    return out


def proof_tasks(text: str) -> list[str]:
    """The proof section's numbered tasks, with markup and links stripped."""
    start, end = PROOF_HEADING.search(text), RELATED_HEADING.search(text)
    if not start or not end or end.start() < start.end():
        return []
    section = text[start.end() : end.start()]
    label = TASK_LABEL.search(section)
    if not label:
        return []
    tail = section[label.end() :].split("**What makes it")[0]
    return [
        EMPHASIS.sub("", INLINE_LINK.sub(r"\1", " ".join(m.group(1).split())))
        for m in TASK_ITEM.finditer(tail)
    ]


@dataclass
class Audit:
    """Every figure this guide publishes about itself."""

    pages: int = 0
    commitments: Counter = field(default_factory=Counter)
    needs_prerequisites: int = 0
    prerequisite_labels: Counter = field(default_factory=Counter)
    task_labels: Counter = field(default_factory=Counter)
    #: element -> {wording: pages}, over every label in STRUCTURAL_LABELS and
    #: every wording retired for it. Counting all of them at once is the
    #: lesson the `assessment` page drew and this audit did not act on for a
    #: while: it reported variants for the two elements somebody had already
    #: noticed, which is the shape of audit that confirms what you knew.
    label_wordings: dict = field(default_factory=dict)
    #: (section, wording) -> pages, for bolded openers nobody declared.
    undeclared_labels: Counter = field(default_factory=Counter)
    tasks: list[str] = field(default_factory=list)
    sentence_words: list[int] = field(default_factory=list)
    longest_sentence: dict[str, int] = field(default_factory=dict)
    #: Word counts of list items, which the prose measurement excludes.
    #: Measured anyway, because excluding them makes the per-page maximum
    #: sentence length trivially gameable: a 70-word sentence becomes
    #: compliant the moment somebody puts a hyphen in front of it, and the
    #: reader is no better off unless the content was genuinely a list. The
    #: metric cannot tell the difference, so both numbers are published.
    longest_list_sentence: dict[str, int] = field(default_factory=dict)
    links: dict[str, int] = field(default_factory=dict)
    path_links: Counter = field(default_factory=Counter)
    code_blocks: int = 0
    code_block_lines: int = 0
    word_counts: dict[str, int] = field(default_factory=dict)

    def render(self) -> str:
        out = [f"\n  corpus: {self.pages} complete pages\n"]

        out.append("  structural commitments")
        out.append(
            "    prerequisites stated   %3d/%-3d" % (
                self.commitments["prerequisites"], self.needs_prerequisites)
        )
        for key, label in (
            ("duration", "duration stated"),
            ("result", "closing result"),
            ("proof", "proof section"),
            ("related", "related section"),
        ):
            out.append("    %-22s %3d/%-3d" % (label, self.commitments[key], self.pages))
        # The per-element variant counts that used to sit here, one for
        # prerequisites and one for proof tasks, are superseded by the sweep
        # below. They reported the two elements somebody had already noticed,
        # and the proof-task one had started counting the historical wordings
        # that `assessment.md` quotes as data, so it read "2 variants" for a
        # corpus with one.
        out.append("\n  structural labels")
        for element in sorted(self.label_wordings):
            wordings = self.label_wordings[element]
            used = {w: n for w, n in wordings.items() if n}
            flag = "" if len(used) <= 1 else "   <- %d wordings" % len(used)
            summary = ", ".join("%s %d" % (w.strip("*"), n) for w, n in sorted(used.items()))
            out.append("    %-22s %s%s" % (element, summary or "unused", flag))

        words = self.sentence_words
        ordered = sorted(words)
        over = [n for n in self.longest_sentence.values() if n > 45]
        repeated = {k: n for k, n in self.undeclared_labels.items() if n >= 3}
        if repeated:
            out.append("    undeclared, 3+ pages")
            for (section, wording), count in sorted(repeated.items(), key=lambda kv: -kv[1]):
                out.append("      %3d  %-48s %s" % (count, wording.strip("*"), section))
        else:
            out.append("    undeclared, 3+ pages   none")

        out.append("\n  prose")
        out.append("    sentences              %d" % len(words))
        out.append("    mean, median           %.1f, %d words"
                   % (sum(words) / len(words), ordered[len(ordered) // 2]))
        out.append("    over 45 words          %d (%.1f%%)"
                   % (len([n for n in words if n > 45]),
                      100 * len([n for n in words if n > 45]) / len(words)))
        worst = max(self.longest_sentence, key=self.longest_sentence.get)
        out.append("    longest per page       mean %.0f, max %d (%s)"
                   % (sum(self.longest_sentence.values()) / len(self.longest_sentence),
                      self.longest_sentence[worst], worst))
        out.append("    pages with a 45+ one   %d/%d" % (len(over), self.pages))
        if self.longest_list_sentence:
            inside = self.longest_list_sentence
            worst_item = max(inside, key=inside.get)
            over_in_lists = [c for c, n in inside.items() if n > 45]
            out.append("    in list items: longest mean %.0f, max %d (%s)"
                       % (sum(inside.values()) / len(inside), inside[worst_item], worst_item))
            out.append("                   45+ on   %d/%d pages"
                       % (len(over_in_lists), self.pages))

        busiest = max(self.links, key=self.links.get)
        total = sum(self.path_links.values())
        out.append("\n  cross-references")
        out.append("    concepts linked/page   mean %.1f, max %d (%s)"
                   % (sum(self.links.values()) / len(self.links),
                      self.links[busiest], busiest))
        if total:
            unread = self.path_links["forward"] + self.path_links["off-path"]
            out.append("    on a path: backward    %d" % self.path_links["backward"])
            out.append("               forward     %d" % self.path_links["forward"])
            out.append("               off-path    %d" % self.path_links["off-path"])
            out.append("    pointing at unread     %.0f%%" % (100 * unread / total))

        out.append("\n  proof tasks")
        out.append("    tasks                  %d" % len(self.tasks))
        for label, pattern in (("naming an artifact", ARTIFACT),
                               ("stating a criterion", CRITERION),
                               ("beginning imperative", IMPERATIVE)):
            n = sum(1 for task in self.tasks if pattern.search(task))
            if pattern is IMPERATIVE:
                n = sum(1 for task in self.tasks if pattern.match(task))
            out.append("    %-22s %d/%d (%.0f%%)"
                       % (label, n, len(self.tasks), 100 * n / len(self.tasks)))

        out.append("\n  code")
        out.append("    fenced blocks          %d" % self.code_blocks)
        out.append("    lines of code/output   %d" % self.code_block_lines)

        truth = self.word_counts["code and furniture removed"]
        out.append("\n  what counts as prose, five ways")
        for label, count in self.word_counts.items():
            out.append("    %-28s %7d  %+5.1f%%"
                       % (label, count, 100 * (count - truth) / truth))

        return "\n".join(out) + "\n"


def audit(registry: Registry, docs: Path) -> Audit:
    """Measure the corpus. Every figure here is quoted on some page."""
    result = Audit()
    complete = [c for c in registry.concepts if c.status == "complete"]
    result.pages = len(complete)
    ids = {c.id for c in registry.concepts}
    texts = {c.id: (docs / c.page).read_text(encoding="utf-8") for c in complete}

    # Every declared label and every wording retired for it, swept together.
    # Two pages quote the retired wordings as the data of their own golden
    # paths, so they are excluded from the count rather than from the corpus.
    quoting_the_history = {"instructional-design", "assessment"}
    for element, canonical in STRUCTURAL_LABELS.items():
        wordings = {canonical: 0}
        wordings.update(
            {retired: 0 for retired, owner in RETIRED_LABELS.items() if owner == element}
        )
        for concept in complete:
            if concept.id in quoting_the_history:
                page = texts[concept.id]
                for wording in wordings:
                    wordings[wording] += 1 if wording == canonical and wording in page else 0
                continue
            for wording in wordings:
                if wording in texts[concept.id]:
                    wordings[wording] += 1
        result.label_wordings[element] = wordings

    # The check that finds what nobody has thought of. Counting declared
    # labels confirms what you already know; the variants that survive are
    # the ones nobody declared, so any bolded opener repeated across pages in
    # a contract section is reported whether or not it is in the register.
    #
    # This is how "One sharper point, and the best thing to say here." was
    # caught, on 5 pages, after a hand sweep for labels used 10 or more times
    # had declared the corpus clean. A frequency floor is a filter on what you
    # are willing to find.
    declared = set(STRUCTURAL_LABELS.values()) | set(RETIRED_LABELS)
    for section in ("How to talk about it", "How to prove it"):
        for concept in complete:
            text = texts[concept.id]
            if f"## {section}" not in text:
                continue
            body = text.split(f"## {section}", 1)[1].split("\n## ", 1)[0]
            for line in body.splitlines():
                match = BOLD_OPENER.match(line.strip())
                if match and match.group(0) not in declared:
                    result.undeclared_labels[(section, match.group(0))] += 1

    for concept in complete:
        text = texts[concept.id]
        flat = re.sub(r"\s+", " ", text)

        if concept.prerequisites:
            result.needs_prerequisites += 1
            if "**Prerequisites:**" in text:
                result.commitments["prerequisites"] += 1
        for label in re.findall(r"^\*\*(Prerequisites:|Read first:)\*\*", text, re.M):
            result.prerequisite_labels[label] += 1
        if DURATION.search(flat):
            result.commitments["duration"] += 1
        if CLOSING_RESULT.search(text):
            result.commitments["result"] += 1
        if PROOF_HEADING.search(text):
            result.commitments["proof"] += 1
        if RELATED_HEADING.search(text):
            result.commitments["related"] += 1

        words = sentences(text)
        if words:
            result.sentence_words += words
            result.longest_sentence[concept.id] = max(words)

        in_lists = list_sentences(text)
        if in_lists:
            result.longest_list_sentence[concept.id] = max(in_lists)

        result.links[concept.id] = len(
            {m for m in CONCEPT_LINK.findall(text) if m in ids and m != concept.id}
        )

        label = TASK_LABEL.search(text)
        if label:
            result.task_labels[label.group(0)] += 1
        result.tasks += proof_tasks(text)

        lines = text.splitlines()
        spans = fence_spans(lines, skip=heredoc_body_lines(lines))
        result.code_blocks += len(spans)
        result.code_block_lines += sum(
            span.close_line - span.open_line - 1 for span in spans
        )

    targets = {
        cid: {m for m in CONCEPT_LINK.findall(text) if m in ids and m != cid}
        for cid, text in texts.items()
    }
    for learning_path in registry.paths:
        position = {c: i for i, c in enumerate(learning_path.concepts)}
        for step in learning_path.concepts:
            for target in targets.get(step, ()):
                if target not in position:
                    result.path_links["off-path"] += 1
                elif position[target] > position[step]:
                    result.path_links["forward"] += 1
                else:
                    result.path_links["backward"] += 1

    # The five-way count. Each row removes one thing the previous row counted.
    naive_fence = re.compile(r"^(?: {0,3})(?:`{3,}|~{3,})")

    def toggled(text: str) -> int:
        body = HTML_COMMENT.sub(" ", FRONT_MATTER.sub("", text))
        kept, inside = [], False
        for line in body.splitlines():
            if naive_fence.match(line):
                inside = not inside
                continue
            if not inside:
                kept.append(line)
        return len(" ".join(kept).split())

    def parsed(text: str) -> int:
        body = HTML_COMMENT.sub(" ", FRONT_MATTER.sub("", text))
        lines = body.splitlines()
        inside = code_lines(lines)
        return len(
            " ".join(l for i, l in enumerate(lines, 1) if i not in inside).split()
        )

    result.word_counts = {
        "whole file": sum(len(t.split()) for t in texts.values()),
        "front matter removed": sum(
            len(FRONT_MATTER.sub("", t).split()) for t in texts.values()
        ),
        "comments removed too": sum(
            len(HTML_COMMENT.sub(" ", FRONT_MATTER.sub("", t)).split())
            for t in texts.values()
        ),
        "code removed, toggled": sum(toggled(t) for t in texts.values()),
        "code and furniture removed": sum(parsed(t) for t in texts.values()),
    }
    return result
