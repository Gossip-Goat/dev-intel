import httpx
import pytest

from dev_intel.config import AllowedDomain, Allowlist, BlockedDomain, load_settings
from dev_intel.fetcher.fetcher import Fetcher, FetchRefused

ROBOTS = "User-agent: *\nDisallow: /private/\n"


def make_fetcher(handler, allowed=("dev.example",)):
    settings = load_settings().fetcher
    allowlist = Allowlist(
        allowed=tuple(AllowedDomain(domain=d, terms_checked_on="2026-11-23", checked_by="test") for d in allowed),
        blocked=(BlockedDomain(domain="realestate.com.au", reason="terms"),),
    )
    client = httpx.Client(transport=httpx.MockTransport(handler), headers={"User-Agent": settings.user_agent})
    sleeps = []
    f = Fetcher(settings=settings, allowlist=allowlist, client=client, clock=lambda: 0.0, sleep=sleeps.append)
    return f, sleeps


def site(request):
    if request.url.path == "/robots.txt":
        return httpx.Response(200, text=ROBOTS)
    if request.url.path == "/blocked":
        return httpx.Response(403)
    return httpx.Response(200, content=b"%PDF-1.4", headers={"content-type": "application/pdf"})


def test_fetches_allowed_page():
    f, _ = make_fetcher(site)
    doc = f.fetch("https://dev.example/price-list.pdf")
    assert doc.status_code == 200 and len(doc.sha256) == 64


def test_subdomain_of_allowed_domain():
    f, _ = make_fetcher(site)
    f.fetch("https://www.dev.example/brochure.pdf")


def test_refuses_unlisted_domain():
    f, _ = make_fetcher(site)
    with pytest.raises(FetchRefused, match="allowlist"):
        f.fetch("https://other.example/x")


def test_refuses_blocked_domain_even_if_allowed():
    f, _ = make_fetcher(site, allowed=("realestate.com.au",))
    with pytest.raises(FetchRefused, match="blocked"):
        f.fetch("https://www.realestate.com.au/new-homes")


def test_honours_robots():
    f, _ = make_fetcher(site)
    with pytest.raises(FetchRefused, match="robots"):
        f.fetch("https://dev.example/private/list.pdf")


def test_backs_off_on_403():
    f, _ = make_fetcher(site)
    with pytest.raises(FetchRefused, match="403"):
        f.fetch("https://dev.example/blocked")


def test_rate_limits_same_host():
    f, sleeps = make_fetcher(site)
    f.fetch("https://dev.example/a")
    f.fetch("https://dev.example/b")
    assert sleeps and all(s > 0 for s in sleeps)
