"""A small GitHub REST client that behaves the way a networked integration must.

The api-integration page lists what separates a script that worked once from
an integration: authentication, pagination, rate limits, retries and errors a
caller can act on. This client is used by `scripts/freshness.py`, so every one
of those is exercised against the real API on a schedule, not in a sketch.

- Authentication: a token from the environment (`GITHUB_TOKEN` in Actions) is
  sent as a bearer token. Without one it still works, at 60 requests an hour.
- Pagination: `paginate` follows the `Link: rel="next"` header rather than
  guessing page numbers, because GitHub decides the page size it honours.
- Rate limits: a 403 or 429 with no requests remaining waits until the reset
  time if that is short, and raises `RateLimited` with the reset time if not;
  a secondary limit's `Retry-After` is obeyed.
- Retries: a 5xx or a dropped connection is retried with backoff, three times.
- Conditional requests: a response's ETag is remembered and sent back, and a
  304 is served from the cache. GitHub does not count 304s against the limit.
- Errors: anything else raises `GitHubError` with the status and GitHub's own
  message, so a caller can tell "not found" from "not allowed".

Standard library only. `transport` is injectable so the tests can drive every
branch without the network.
"""

from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Callable, Iterator

API = "https://api.github.com"
NEXT = re.compile(r'<([^>]+)>;\s*rel="next"')

#: (method, url, headers, body) -> (status, headers, body bytes)
Transport = Callable[[str, str, dict, bytes | None], tuple[int, dict, bytes]]


class GitHubError(Exception):
    def __init__(self, status: int, message: str, url: str):
        super().__init__(f"{status} from {url}: {message}")
        self.status, self.message, self.url = status, message, url


class RateLimited(GitHubError):
    def __init__(self, reset: int, url: str):
        super().__init__(403, f"rate limit exhausted until {reset}", url)
        self.reset = reset


def urllib_transport(method: str, url: str, headers: dict, body: bytes | None):
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status, {k.lower(): v for k, v in response.headers.items()}, response.read()
    except urllib.error.HTTPError as error:
        return error.code, {k.lower(): v for k, v in error.headers.items()}, error.read()


class GitHub:
    def __init__(self, token: str | None = None, transport: Transport = urllib_transport,
                 sleep: Callable[[float], None] = time.sleep, max_wait: float = 120,
                 clock: Callable[[], float] = time.time):
        self.token = token if token is not None else os.environ.get("GITHUB_TOKEN")
        self.transport, self.sleep, self.max_wait, self.clock = transport, sleep, max_wait, clock
        self.etags: dict[str, tuple[str, object, dict]] = {}
        self.remaining: int | None = None

    def _headers(self, url: str, method: str) -> dict:
        headers = {"Accept": "application/vnd.github+json",
                   "X-GitHub-Api-Version": "2022-11-28",
                   "User-Agent": "fieldguide-freshness"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        if method == "GET" and url in self.etags:
            headers["If-None-Match"] = self.etags[url][0]
        return headers

    def request(self, method: str, path: str, params: dict | None = None,
                body: dict | None = None) -> tuple[object, dict]:
        url = path if path.startswith("http") else API + path
        if params:
            url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
        data = json.dumps(body).encode() if body is not None else None
        for attempt in range(4):
            try:
                status, headers, raw = self.transport(method, url, self._headers(url, method), data)
            except OSError:
                if attempt == 3:
                    raise
                self.sleep(2 ** attempt)
                continue
            if "x-ratelimit-remaining" in headers:
                self.remaining = int(headers["x-ratelimit-remaining"])
            if status == 304 and url in self.etags:
                _, cached, cached_headers = self.etags[url]
                return cached, cached_headers
            if status in (403, 429) and "retry-after" in headers:
                self.sleep(float(headers["retry-after"]))
                continue
            if status in (403, 429) and headers.get("x-ratelimit-remaining") == "0":
                reset = int(headers.get("x-ratelimit-reset", "0"))
                wait = reset - self.clock()
                if wait > self.max_wait or attempt == 3:
                    raise RateLimited(reset, url)
                self.sleep(max(wait, 0) + 1)
                continue
            if status >= 500 and attempt < 3:
                self.sleep(2 ** attempt)
                continue
            payload = json.loads(raw) if raw else None
            if status >= 400:
                message = payload.get("message", "") if isinstance(payload, dict) else ""
                raise GitHubError(status, message, url)
            if method == "GET" and "etag" in headers:
                self.etags[url] = (headers["etag"], payload, headers)
            return payload, headers
        raise GitHubError(0, "retries exhausted", url)

    def get(self, endpoint: str, **params) -> object:
        return self.request("GET", endpoint, params or None)[0]

    def paginate(self, endpoint: str, **params) -> Iterator[dict]:
        url: str | None = endpoint
        first = True
        while url:
            payload, headers = self.request("GET", url, (params or None) if first else None)
            first = False
            yield from payload or []
            match = NEXT.search(headers.get("link", ""))
            url = match.group(1) if match else None
