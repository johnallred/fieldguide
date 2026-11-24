"""The freshness monitor and the GitHub client it uses, without the network."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
github_api = importlib.import_module("github_api")
freshness = importlib.import_module("freshness")


class Fake:
    """A scripted transport: each call pops the next (status, headers, body)."""

    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, method, url, headers, body):
        self.calls.append((method, url, headers, body))
        status, headers_out, payload = self.responses.pop(0)
        return status, headers_out, json.dumps(payload).encode() if payload is not None else b""


def client(fake, **kw):
    return github_api.GitHub(token="t0ken", transport=fake, sleep=lambda s: None,
                             clock=lambda: 1000.0, **kw)


def test_it_authenticates():
    fake = Fake((200, {}, []))
    client(fake).get("/x")
    assert fake.calls[0][2]["Authorization"] == "Bearer t0ken"


def test_it_follows_link_headers_across_pages():
    fake = Fake((200, {"link": '<https://api.github.com/x?page=2>; rel="next"'}, [1, 2]),
                (200, {}, [3]))
    assert list(client(fake).paginate("/x", per_page=2)) == [1, 2, 3]
    assert fake.calls[1][1] == "https://api.github.com/x?page=2"


def test_it_waits_out_a_short_rate_limit_and_gives_up_on_a_long_one():
    short = Fake((403, {"x-ratelimit-remaining": "0", "x-ratelimit-reset": "1030"}, {}),
                 (200, {"x-ratelimit-remaining": "4999"}, {"ok": True}))
    api = client(short)
    assert api.get("/x") == {"ok": True}
    assert api.remaining == 4999
    long = Fake((403, {"x-ratelimit-remaining": "0", "x-ratelimit-reset": "9000"}, {}))
    with pytest.raises(github_api.RateLimited):
        client(long).get("/x")


def test_it_obeys_retry_after_and_retries_server_errors():
    fake = Fake((429, {"retry-after": "2"}, {}), (502, {}, None), (200, {}, {"ok": 1}))
    assert client(fake).get("/x") == {"ok": 1}
    assert len(fake.calls) == 3


def test_it_reuses_a_cached_response_on_304():
    fake = Fake((200, {"etag": '"abc"'}, {"v": 1}), (304, {}, None))
    api = client(fake)
    assert api.get("/x") == {"v": 1}
    assert api.get("/x") == {"v": 1}
    assert fake.calls[1][2]["If-None-Match"] == '"abc"'


def test_an_error_says_what_github_said():
    fake = Fake((404, {}, {"message": "Not Found"}))
    with pytest.raises(github_api.GitHubError, match="404.*Not Found"):
        client(fake).get("/x")


def test_every_demonstration_entry_is_read_with_its_note_line():
    text = (REPO / "demonstrations.yaml").read_text(encoding="utf-8")
    found = freshness.entries(text)
    assert len(found) == text.count("\n  - concept: ")
    lines = text.splitlines()
    assert all(lines[e["line"] - 1].startswith("    note: ") for e in found)


def test_a_reviewed_line_is_read():
    text = ("  - concept: a\n    project: fieldguide\n    artifact: x.py\n    extent: full\n"
            "    note: fine\n    reviewed: 2026-11-24\n")
    assert freshness.entries(text)[0]["reviewed"] == "2026-11-24"


def test_the_issue_is_opened_updated_and_closed():
    open_issue = {"number": 7, "body": "old", "labels": [{"name": "freshness"}]}
    created = Fake((200, {}, []), (201, {}, {"number": 8}))
    assert freshness.sync_issue(client(created), "body", True) == "opened #8"
    assert created.calls[1][0] == "POST"
    updated = Fake((200, {}, [open_issue]), (200, {}, {}))
    assert freshness.sync_issue(client(updated), "new", True) == "updated #7"
    closed = Fake((200, {}, [open_issue]), (200, {}, {}))
    assert freshness.sync_issue(client(closed), "", False) == "closed #7"
    assert json.loads(closed.calls[1][3])["state"] == "closed"
