from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from dev_intel.config import load_settings
from dev_intel.inquiry.guardrails import GuardrailViolation, SendHistory, check_can_send, check_identity, check_limits
from dev_intel.inquiry.templates import own_company_inquiry, research_firm_inquiry

NOW = datetime(2026, 11, 23, tzinfo=timezone.utc)
CLEAN = SendHistory(open_inquiries_for_development=0, sends_to_agency=(), suppressed=False)


@pytest.fixture
def settings():
    return load_settings()


@pytest.fixture
def real_settings(settings):
    sender = settings.sender.model_copy(update={
        "name": "Sam Lee", "company": "Acme Developments Pty Ltd", "abn": "12 345 678 901",
        "email": "research@acme.example", "phone": "07 0000 0000", "postal_address": "1 Example St, Brisbane QLD",
        "role": "Market Research",
    })
    inquiry = settings.inquiry.model_copy(update={"sending_enabled": True})
    return settings.model_copy(update={"sender": sender, "inquiry": inquiry})


def draft_a(s):
    return own_company_inquiry(s.sender, "sales@agency.example", "Alex", "Riverside Towers")


def test_template_a_passes_identity(settings):
    assert check_identity(draft_a(settings), settings) == []


def test_buyer_claim_rejected(settings):
    d = draft_a(settings)
    d = replace(d, body=d.body.replace("Would you be willing", "I'm a first home buyer. Would you be willing"))
    assert any("buyer" in p for p in check_identity(d, settings))


def test_looking_to_buy_rejected(settings):
    d = draft_a(settings)
    d = replace(d, body=d.body + "\nI'm looking to buy in the area.")
    assert any("buyer" in p for p in check_identity(d, settings))


def test_missing_opt_out_rejected(settings):
    d = draft_a(settings)
    d = replace(d, body=d.body.split("If you'd prefer")[0])
    assert "Missing opt-out line" in check_identity(d, settings)


def test_from_address_must_match(settings):
    d = replace(draft_a(settings), from_address="someone@else.example")
    assert any("From address" in p for p in check_identity(d, settings))


def test_research_firm_disabled_by_default(settings):
    d = research_firm_inquiry(settings.research_firm, "sales@agency.example", "Alex", "Riverside Towers")
    assert "Research firm option is not enabled" in check_identity(d, settings)


def test_research_firm_must_disclose_client(settings):
    firm = settings.research_firm.model_copy(update={"enabled": True})
    s = settings.model_copy(update={"research_firm": firm})
    d = research_firm_inquiry(firm, "sales@agency.example", "Alex", "Riverside Towers")
    assert check_identity(d, s) == []
    d = replace(d, body=d.body.replace("on behalf of a client", "for ourselves"))
    assert any("disclose" in p for p in check_identity(d, s))


def test_placeholders_block_sending(settings):
    s = settings.model_copy(update={"inquiry": settings.inquiry.model_copy(update={"sending_enabled": True})})
    with pytest.raises(GuardrailViolation, match="placeholders"):
        check_can_send(draft_a(s), s, CLEAN, NOW, approved_by="Approver")


def test_sending_disabled_by_default(settings):
    with pytest.raises(GuardrailViolation, match="disabled"):
        check_can_send(draft_a(settings), settings, CLEAN, NOW, approved_by="Approver")


def test_needs_approval(real_settings):
    with pytest.raises(GuardrailViolation, match="approval"):
        check_can_send(draft_a(real_settings), real_settings, CLEAN, NOW, approved_by=None)


def test_real_approved_draft_can_send(real_settings):
    check_can_send(draft_a(real_settings), real_settings, CLEAN, NOW, approved_by="Approver")


def test_limits(settings):
    inq = settings.inquiry
    assert check_limits(replace(CLEAN, suppressed=True), inq, NOW)
    assert check_limits(replace(CLEAN, open_inquiries_for_development=1), inq, NOW)
    recent = tuple(NOW - timedelta(days=i) for i in range(5))
    assert check_limits(replace(CLEAN, sends_to_agency=recent), inq, NOW)
    old = tuple(NOW - timedelta(days=10 + i) for i in range(5))
    assert check_limits(replace(CLEAN, sends_to_agency=old), inq, NOW) == []
