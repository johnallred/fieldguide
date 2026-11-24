#!/usr/bin/env python3
"""Measure whether the field can deliver without you, and what it keeps asking.

    python3 drills/field_enablement.py                                    # embedded samples
    python3 drills/field_enablement.py roster.csv questions.csv resources.csv

Field enablement teaches the people who demo, sell and support, not the end
audience. Three inputs:

- roster.csv: each person's role and how far they got: attended the training,
  practised delivering with feedback, and passed a teach-back (delivered the
  demo back, unassisted, to someone who checked it).
- questions.csv: what the field asked in office hours and channels, tagged by
  topic, by kind (`knowledge` if a person did not know, `product` if the
  product could not do it), and by the self-service resource that answered it,
  if any.
- resources.csv: the self-service resources and how often they were opened.

The report answers three questions: who can deliver without you, which topics
self-service does not cover, and what the field is telling product. The people,
questions and resources are invented for the exercise.
"""

from __future__ import annotations

import csv
import io
import sys
from collections import Counter, defaultdict

ROSTER = """\
person,role,attended,practised,teach_back
se1,SE,yes,yes,pass
se2,SE,yes,yes,pass
se3,SE,yes,yes,pass
se4,SE,yes,yes,fail
se5,SE,yes,no,-
ae1,AE,yes,yes,pass
ae2,AE,yes,no,-
ae3,AE,yes,no,-
ae4,AE,yes,no,-
p1,partner,yes,yes,fail
p2,partner,yes,no,-
p3,partner,yes,no,-
"""

QUESTIONS = """\
person,topic,kind,resource
se5,retries,knowledge,configure-retries
ae2,retries,knowledge,configure-retries
ae3,retries,knowledge,configure-retries
p2,retries,knowledge,-
ae4,retries,knowledge,configure-retries
p3,retries,knowledge,-
se4,retries,knowledge,configure-retries
ae2,retries,knowledge,configure-retries
ae1,pricing,knowledge,-
ae3,pricing,knowledge,-
ae4,pricing,knowledge,-
p1,pricing,knowledge,-
p2,pricing,knowledge,-
se1,auth,knowledge,auth-guide
p3,auth,knowledge,auth-guide
ae2,auth,knowledge,auth-guide
se2,batch on cloud-b,product,-
se3,batch on cloud-b,product,-
ae1,batch on cloud-b,product,-
p1,batch on cloud-b,product,-
"""

RESOURCES = """\
name,topic,views_30d
configure-retries,retries,140
retry-faq,retries,0
auth-guide,auth,60
"""


def table(text: str) -> list[dict]:
    return list(csv.DictReader(io.StringIO(text)))


def report(roster_text: str, questions_text: str, resources_text: str) -> None:
    roster, questions, resources = map(table, (roster_text, questions_text, resources_text))
    total = len(roster)

    print("step 1: who can deliver without you")
    for label, test in (("attended the training", lambda r: r["attended"] == "yes"),
                        ("practised with feedback", lambda r: r["practised"] == "yes"),
                        ("passed a teach-back", lambda r: r["teach_back"] == "pass")):
        print(f"  {label:<26} {sum(1 for r in roster if test(r)):>2}/{total}")
    roles = defaultdict(lambda: [0, 0])
    for r in roster:
        roles[r["role"]][1] += 1
        roles[r["role"]][0] += r["teach_back"] == "pass"
    print("  by role: " + ", ".join(f"{role} {n}/{of}" for role, (n, of) in roles.items()))
    print()

    print("step 2: what the field asks, and whether self-service answers it")
    print("  topic               questions  answered  action")
    knowledge = [q for q in questions if q["kind"] == "knowledge"]
    by_topic = Counter(q["topic"] for q in knowledge)
    for topic, n in by_topic.most_common():
        answered = sum(1 for q in knowledge if q["topic"] == topic and q["resource"] != "-")
        if answered == 0:
            action = "write a resource"
        elif answered < n:
            action = "point the field at it"
        else:
            action = "covered"
        print(f"  {topic:<20}{n:>6}{answered:>9}/{n:<3}  {action}")
    used = Counter(q["resource"] for q in questions)
    for res in resources:
        if int(res["views_30d"]) == 0 and not used[res["name"]]:
            print(f"  unused resource: {res['name']} (0 views, answered nothing): merge or retire")
    print()

    print("step 3: what the field is telling product")
    product = Counter(q["topic"] for q in questions if q["kind"] == "product")
    for topic, n in product.most_common():
        role_of = {r["person"]: r["role"] for r in roster}
        asked = {role_of[q["person"]] for q in questions
                 if q["kind"] == "product" and q["topic"] == topic}
        who = [role for role in roles if role in asked]
        print(f"  {topic}: {n} questions, from {', '.join(who)}")


def main() -> int:
    if len(sys.argv) == 4:
        report(*(open(path, encoding="utf-8").read() for path in sys.argv[1:]))
    else:
        report(ROSTER, QUESTIONS, RESOURCES)
    return 0


if __name__ == "__main__":
    sys.exit(main())
