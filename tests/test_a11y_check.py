"""The accessibility gate over the built site: each rule, and the real build."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
a11y = importlib.import_module("a11y_check")

GOOD = ('<html lang="en"><head><title>Page</title></head><body><h1>Name</h1><h2>Part</h2>'
        '<p><a href="/x/">The install guide</a> <img src="a.png" alt=""></p>'
        '<table><tr><th>A</th></tr><tr><td>1</td></tr></table>'
        '<label for="q">Search</label><input id="q" type="text"></body></html>')


def findings(html: str) -> set[str]:
    page = a11y.Page()
    page.feed(html)
    page.close()
    return {kind for kind, _ in page.finish()}


def test_a_sound_page_passes():
    assert findings(GOOD) == set()


@pytest.mark.parametrize("change, kind", [
    (('lang="en"', ""), "lang"),
    (("<title>Page</title>", "<title></title>"), "title"),
    (("<h2>Part</h2>", "<h3>Part</h3>"), "heading-skip"),
    (("<h2>Part</h2>", "<h1>Part</h1>"), "one-h1"),
    (('alt=""', ""), "img-alt"),
    (("The install guide", ""), "link-name"),
    (("The install guide", "click here"), "link-vague"),
    (("<th>A</th>", "<td>A</td>"), "table-header"),
    (('<label for="q">Search</label>', ""), "input-label"),
])
def test_each_rule_catches_its_defect(change, kind):
    assert kind in findings(GOOD.replace(*change))


def test_an_empty_link_with_a_label_or_an_image_has_a_name():
    assert "link-name" not in findings(GOOD.replace("The install guide", "").replace(
        '<a href="/x/">', '<a href="/x/" aria-label="Install">'))
    assert "link-name" not in findings(GOOD.replace(
        "The install guide", '<img src="i.png" alt="Install">'))


def test_the_code_line_anchors_that_were_found_stay_gone():
    """anchor_linenums put an empty, focusable link on every code line: 11,102."""
    import yaml

    class Loader(yaml.SafeLoader):
        pass

    Loader.add_multi_constructor("", lambda loader, suffix, node: None)
    config = yaml.load((REPO / "mkdocs.yml").read_text(encoding="utf-8"), Loader=Loader)
    for entry in config["markdown_extensions"]:
        if isinstance(entry, dict) and "pymdownx.highlight" in entry:
            assert not (entry["pymdownx.highlight"] or {}).get("anchor_linenums")
