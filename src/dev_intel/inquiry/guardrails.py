"""Checks every draft must pass before it can be queued or sent.

These run in code so that no prompt, template edit or model output can switch them off.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta

from dev_intel.config import InquirySettings, Settings, is_placeholder
from dev_intel.inquiry.templates import OPT_OUT_LINE, Draft

# Phrases that would misrepresent who is asking.
BUYER_CLAIMS = [
    r"\bI(?:'m| am) (?:a |an )?(?:buyer|purchaser|investor|first home buyer|owner[- ]occupier)\b",
    r"\b(?:my|our) (?:partner|wife|husband|family) and I\b",
    r"\bI(?:'m| am) (?:looking|hoping|wanting) to (?:buy|purchase|invest)\b",
    r"\binterested in (?:buying|purchasing)\b",
    r"\bfor (?:my|our) (?:new )?home\b",
]


class GuardrailViolation(Exception):
    pass


def check_identity(draft: Draft, settings: Settings) -> list[str]:
    problems: list[str] = []
    if draft.option == "A":
        s = settings.sender
        required = [s.name, s.company, s.abn, s.postal_address]
        if draft.from_address != s.email:
            problems.append("From address must be the configured sender")
    elif draft.option == "B":
        f = settings.research_firm
        if not f.enabled:
            problems.append("Research firm option is not enabled")
        required = [f.contact_name, f.name, f.abn, f.postal_address]
        if "on behalf of a client" not in draft.body:
            problems.append("Research firm emails must disclose they act for a client")
        if draft.from_address != f.email:
            problems.append("From address must be the configured research firm")
    else:
        return [f"Unknown option {draft.option!r}"]
    for item in required:
        if item not in draft.body:
            problems.append(f"Missing sender detail: {item}")
    if OPT_OUT_LINE not in draft.body:
        problems.append("Missing opt-out line")
    for pattern in BUYER_CLAIMS:
        if re.search(pattern, draft.body, flags=re.IGNORECASE):
            problems.append(f"Draft claims or implies being a buyer: /{pattern}/")
    return problems


@dataclass(frozen=True)
class SendHistory:
    open_inquiries_for_development: int
    sends_to_agency: tuple[datetime, ...]
    suppressed: bool


def check_limits(history: SendHistory, settings: InquirySettings, now: datetime) -> list[str]:
    problems: list[str] = []
    if history.suppressed:
        problems.append("Recipient has opted out or declined")
    if history.open_inquiries_for_development >= settings.max_open_per_development:
        problems.append("An inquiry for this development is already open")
    week_ago = now - timedelta(days=7)
    if sum(1 for t in history.sends_to_agency if t >= week_ago) >= settings.max_sends_per_agency_per_week:
        problems.append("Weekly cap for this agency reached")
    return problems


def check_can_send(draft: Draft, settings: Settings, history: SendHistory, now: datetime, approved_by: str | None) -> None:
    problems = check_identity(draft, settings) + check_limits(history, settings.inquiry, now)
    inq = settings.inquiry
    if not inq.sending_enabled:
        problems.append("Sending is disabled in config")
    sender_fields = settings.sender.model_dump().values() if draft.option == "A" else settings.research_firm.model_dump().values()
    if any(isinstance(v, str) and is_placeholder(v) for v in sender_fields):
        problems.append("Sender details are still placeholders")
    if inq.require_approval and not approved_by:
        problems.append(f"Needs approval from {inq.approver}")
    if problems:
        raise GuardrailViolation("; ".join(problems))
