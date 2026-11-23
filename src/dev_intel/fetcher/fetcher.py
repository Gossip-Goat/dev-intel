"""The only way scrapers reach the web.

Every request is checked against the domain allowlist and the site's robots.txt,
rate-limited per domain, and sent with an honest user agent. The fetcher never
logs in, solves CAPTCHAs or rotates IPs; a block is treated as a no.
"""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

import httpx

from dev_intel.config import Allowlist, FetcherSettings


class FetchRefused(Exception):
    """Raised when a URL may not be fetched. Never retried."""


@dataclass(frozen=True)
class FetchedDocument:
    url: str
    status_code: int
    content_type: str
    body: bytes
    sha256: str
    fetched_at: datetime


def _host(url: str) -> str:
    return (urlsplit(url).hostname or "").lower()


def _matches(host: str, domain: str) -> bool:
    domain = domain.lower()
    return host == domain or host.endswith("." + domain)


@dataclass
class Fetcher:
    settings: FetcherSettings
    allowlist: Allowlist
    client: httpx.Client | None = None
    clock: Callable[[], float] = time.monotonic
    sleep: Callable[[float], None] = time.sleep
    _last_request: dict[str, float] = field(default_factory=dict)
    _robots: dict[str, RobotFileParser] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.client is None:
            self.client = httpx.Client(
                headers={"User-Agent": self.settings.user_agent},
                timeout=self.settings.timeout_seconds,
                follow_redirects=False,
            )

    def check_allowed(self, url: str) -> None:
        host = _host(url)
        if urlsplit(url).scheme not in ("http", "https") or not host:
            raise FetchRefused(f"Not a web URL: {url}")
        for blocked in self.allowlist.blocked:
            if _matches(host, blocked.domain):
                raise FetchRefused(f"{host} is blocked: {blocked.reason}")
        if not any(_matches(host, a.domain) for a in self.allowlist.allowed):
            raise FetchRefused(f"{host} is not on the allowlist; review its terms first")
        if not self._robots_for(url).can_fetch(self.settings.user_agent, url):
            raise FetchRefused(f"robots.txt disallows {url}")

    def _robots_for(self, url: str) -> RobotFileParser:
        parts = urlsplit(url)
        key = f"{parts.scheme}://{parts.netloc}"
        if key not in self._robots:
            parser = RobotFileParser()
            self._wait_turn(_host(url))
            resp = self.client.get(f"{key}/robots.txt")
            if resp.status_code in (401, 403):
                parser.disallow_all = True
            elif resp.status_code >= 400:
                parser.allow_all = True
            else:
                parser.parse(resp.text.splitlines())
            self._robots[key] = parser
        return self._robots[key]

    def _wait_turn(self, host: str) -> None:
        last = self._last_request.get(host)
        if last is not None:
            wait = self.settings.min_seconds_between_requests - (self.clock() - last)
            if wait > 0:
                self.sleep(wait)
        self._last_request[host] = self.clock()

    def fetch(self, url: str) -> FetchedDocument:
        self.check_allowed(url)
        self._wait_turn(_host(url))
        resp = self.client.get(url)
        if resp.status_code in (403, 429):
            raise FetchRefused(f"{url} answered {resp.status_code}; backing off, not retrying")
        if 300 <= resp.status_code < 400:
            target = resp.headers.get("location", "")
            raise FetchRefused(f"{url} redirects to {target}; fetch the target explicitly so it is checked")
        body = resp.content
        return FetchedDocument(
            url=url,
            status_code=resp.status_code,
            content_type=resp.headers.get("content-type", ""),
            body=body,
            sha256=hashlib.sha256(body).hexdigest(),
            fetched_at=datetime.now(timezone.utc),
        )
