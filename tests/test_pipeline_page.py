"""The pipeline diagram is the workflow, drawn: every job and every needs edge."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from fieldguide.generate import pipeline_page

REPO = Path(__file__).resolve().parent.parent
WORKFLOW = REPO / ".github" / "workflows" / "gates.yml"


def test_every_job_and_edge_is_in_the_diagram():
    text = WORKFLOW.read_text(encoding="utf-8")
    page = pipeline_page(text)
    diagram = re.search(r"```mermaid\n(.*?)```", page, re.S).group(1)
    jobs = yaml.safe_load(text)["jobs"]
    for job, spec in jobs.items():
        assert f'{job}["{spec.get("name", job)}"]' in diagram
        needs = spec.get("needs") or []
        for need in [needs] if isinstance(needs, str) else needs:
            assert f"{need} --> {job}" in diagram
    assert diagram.count(" --> ") == sum(
        len([s["needs"]] if isinstance(s.get("needs"), str) else s.get("needs") or [])
        for s in jobs.values())


def test_the_diagram_has_a_title_a_description_and_a_text_alternative():
    page = pipeline_page(WORKFLOW.read_text(encoding="utf-8"))
    assert "accTitle: " in page and "accDescr: " in page
    assert "| Job | Runs after | Named steps |" in page


def test_a_new_job_changes_the_page():
    """What `fieldguide build --check` relies on to fail CI when they drift."""
    text = WORKFLOW.read_text(encoding="utf-8")
    workflow = yaml.safe_load(text)
    workflow["jobs"]["extra"] = {"name": "Extra", "needs": "deploy", "runs-on": "x", "steps": []}
    changed = pipeline_page(yaml.safe_dump(workflow, sort_keys=False))
    assert 'extra["Extra"]' in changed and "deploy --> extra" in changed
    assert changed != pipeline_page(text)


def test_the_committed_page_is_current():
    committed = (REPO / "docs" / "explanation" / "pipeline.md").read_text(encoding="utf-8")
    assert committed == pipeline_page(WORKFLOW.read_text(encoding="utf-8"))
