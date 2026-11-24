"""The crawl audit run on this guide's own build, and the llms.txt it checks."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BASE = "https://example.test/guide/"


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


crawl = load("crawl_site", REPO / "scripts" / "crawl_site.py")

WORDS = " ".join(["word"] * 30)


def page(url: str, description: str, body: str = "") -> str:
    return (f'<html><head><meta name="description" content="{description}">'
            f'<link rel="canonical" href="{url}"></head>'
            f"<body><p>{WORDS}</p>{body}</body></html>")


def site(tmp_path: Path, pages: dict[str, str], llms: bool = True) -> Path:
    for relative, html in pages.items():
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(html, encoding="utf-8")
    urls = [BASE if Path(r).parent == Path(".") else f"{BASE}{Path(r).parent.as_posix()}/"
            for r in pages]
    (tmp_path / "sitemap.xml").write_text(
        "<urlset>" + "".join(f"<loc>{u}</loc>" for u in urls) + "</urlset>", encoding="utf-8")
    if llms:
        (tmp_path / "llms.txt").write_text(f"# Guide\n\n- [Home]({BASE})\n", encoding="utf-8")
    return tmp_path


def run(capsys, root: Path) -> tuple[int, str]:
    code = crawl.offline(root)
    out = capsys.readouterr()
    return code, out.out + out.err


def test_a_sound_site_passes(tmp_path, capsys):
    root = site(tmp_path, {
        "index.html": page(BASE, "home", '<a href="a/">a</a>'),
        "a/index.html": page(BASE + "a/", "page a", '<a href="../">home</a>'),
    })
    code, out = run(capsys, root)
    assert code == 0, out
    assert "ok: 2 pages, 0 problem(s)" in out


def test_each_defect_is_reported(tmp_path, capsys):
    root = site(tmp_path, {
        "index.html": page(BASE, "same", '<a href="missing/">x</a>'),
        "a/index.html": page(BASE + "elsewhere/", "same"),
    }, llms=False)
    code, out = run(capsys, root)
    assert code == 1
    for kind in ("dead-link", "wrong-canonical", "duplicate-description", "no-llms-txt"):
        assert kind in out, (kind, out)


def test_links_inside_code_samples_are_not_links(tmp_path, capsys):
    sample = '<pre><code>&lt;a href="/nowhere/"&gt; <a href="nowhere/">x</a></code></pre>'
    root = site(tmp_path, {"index.html": page(BASE, "home", sample)})
    code, out = run(capsys, root)
    assert code == 0, out


def test_the_real_llms_txt_lists_every_concept():
    import yaml

    llms = load("llms_hook", REPO / "hooks" / "llms.py")
    config = yaml.load((REPO / "mkdocs.yml").read_text(encoding="utf-8"), Loader=_loader())
    config["docs_dir"] = str(REPO / "docs")
    text = llms.build(config)
    from fieldguide.registry import load_registry

    registry = load_registry(REPO / "concepts.yaml")
    missing = [c.id for c in registry.concepts
               if f"{config['site_url']}concepts/{c.id}/" not in text]
    assert not missing, missing
    assert text.startswith(f"# {config['site_name']}\n\n> ")
    assert "\n## Optional\n" in text


def _loader():
    import yaml

    class Loader(yaml.SafeLoader):
        pass

    Loader.add_multi_constructor("", lambda loader, suffix, node: None)
    return Loader
