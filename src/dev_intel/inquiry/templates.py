"""Inquiry emails. Identity lines come from config and are rendered by code, not by a model."""
from __future__ import annotations

from dataclasses import dataclass

from dev_intel.config import ResearchFirm, Sender

OPT_OUT_LINE = "If you'd prefer not to receive research requests from us, reply \"unsubscribe\" and we won't contact you again."


@dataclass(frozen=True)
class Draft:
    to: str
    from_address: str
    subject: str
    body: str
    option: str  # "A" (own company) or "B" (disclosed research firm)


def own_company_inquiry(sender: Sender, to: str, agent_name: str, development: str) -> Draft:
    body = f"""Hi {agent_name},

I'm {sender.name}, {sender.role} at {sender.company}. We're a property developer, and we're researching current pricing for new projects in the area as part of our market research.

Would you be willing to share the current price list and brochure for {development}? I understand if you'd rather not share these with another developer.

Thanks for considering it.

{sender.name}
{sender.role}, {sender.company}
ABN {sender.abn}
{sender.postal_address}
{sender.phone} | {sender.email}

{OPT_OUT_LINE}
"""
    return Draft(to=to, from_address=sender.email, subject=f"Market research request: {development} price list", body=body, option="A")


def research_firm_inquiry(firm: ResearchFirm, to: str, agent_name: str, development: str) -> Draft:
    body = f"""Hi {agent_name},

I'm {firm.contact_name} from {firm.name}. We're carrying out market research on behalf of a client in the property development industry.

Would you be willing to share the current price list and brochure for {development}? The information is used for internal market analysis only.

Thanks for considering it.

{firm.contact_name}
{firm.name}
ABN {firm.abn}
{firm.postal_address}
{firm.email}

{OPT_OUT_LINE}
"""
    return Draft(to=to, from_address=firm.email, subject=f"Market research request: {development} price list", body=body, option="B")
