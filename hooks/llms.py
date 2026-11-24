"""Write llms.txt into the built site: a map of the guide for language models.

The `llms-txt` page argues that a corpus should publish one, generated from
data it already holds so it cannot go stale. This guide did not, and the
crawlability audit of its own published site (`scripts/crawl_site.py`) said
so. This hook closes that, the same way the page recommends: the file is
built from `concepts.yaml` and each page's own `summary`, on every build, and
written next to the site it describes.

Sections follow the convention: one line saying what the guide is, a short
orientation, a section per category of concept with each link's question, and
`## Optional` for pages a model can skip.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from fieldguide.registry import load_registry


def _summary(docs: Path, relative: str) -> str:
    text = (docs / relative).read_text(encoding="utf-8")
    if not text.startswith("---"):
        return ""
    front = yaml.safe_load(text.split("---", 2)[1]) or {}
    return " ".join(str(front.get("summary", "")).split())


def _item(base: str, docs: Path, relative: str, title: str) -> str:
    url = base + relative.removesuffix("index.md").removesuffix(".md")
    url = url if url.endswith("/") else url + "/"
    summary = _summary(docs, relative)
    return f"- [{title}]({url})" + (f": {summary}" if summary else "")


def build(config) -> str:
    docs = Path(config["docs_dir"])
    base = config["site_url"]
    registry = load_registry(docs.parent / "concepts.yaml")

    lines = [
        f"# {config['site_name']}",
        "",
        f"> {' '.join(str(config.get('site_description') or '').split())}",
        "",
        "Each concept page has the same seven sections, including a golden path with "
        "commands to run and their output, and a list of what it does not prove. "
        "Learning paths order the concepts for a role.",
        "",
        "## Start here",
        "",
        _item(base, docs, "index.md", "Start here"),
        _item(base, docs, "paths/index.md", "Learning paths"),
        _item(base, docs, "demonstrated.md", "Demonstrated"),
        _item(base, docs, "coverage.md", "Coverage"),
        "",
        "## Learning paths",
        "",
    ]
    lines += [_item(base, docs, f"paths/{p.id}.md", p.name) for p in registry.paths]
    for key, label in registry.categories.items():
        concepts = registry.in_category(key)
        if not concepts:
            continue
        lines += ["", f"## {label}", ""]
        lines += [_item(base, docs, f"concepts/{c.id}.md", c.name) for c in concepts]
    lines += [
        "",
        "## Optional",
        "",
        _item(base, docs, "study-plan.md", "Everything in order"),
        _item(base, docs, "explanation/why-a-registry.md", "Why a registry"),
        _item(base, docs, "explanation/the-page-contract.md", "The page contract"),
        _item(base, docs, "explanation/provenance.md", "Provenance"),
        "",
    ]
    return "\n".join(lines)


def on_post_build(config) -> None:
    Path(config["site_dir"], "llms.txt").write_text(build(config), encoding="utf-8")
