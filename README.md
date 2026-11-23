# dev-intel

Tracks what competing off-the-plan developments in South East Queensland and the Far North Coast of NSW are asking, before settlement data is published.

Four parts:

1. **Fetcher and sources** (`src/dev_intel/fetcher`, `sources/`): pulls from licensed feeds and allowlisted sites only, honouring robots.txt, rate limits and site terms.
2. **Inquiry agent** (`src/dev_intel/inquiry`): emails published sales contacts asking for price lists. Every email names the real sender and says it's market research. A disclosed research firm can be used for hard-to-reach projects. Nothing poses as a buyer.
3. **Extraction** (`src/dev_intel/extraction`): Claude reads price lists and brochures into typed rows, then plausibility checks send doubtful rows to review.
4. **Data lake** (`lake/`): raw files in S3, clean tables in Postgres (RDS), hosted in AWS Sydney, dated price observations, and an asked-vs-settled view.

Architecture and compliance decisions: see the design doc linked in the project.

## Compliance guardrails (in code, not prompts)

- Sender name, company, ABN, address and opt-out line are rendered from `config/settings.yaml` and checked on every draft.
- Drafts that claim or imply the sender is a buyer are rejected.
- Sending stays off until sender details are real, and every send needs the approver while `require_approval` is true.
- Caps: one open inquiry per development, five sends per agency per week, one follow-up. Opt-outs are suppressed permanently.
- The fetcher refuses domains not on `config/allowlist.yaml`, anything robots.txt disallows, and backs off on 403/429 without retrying.

Have a lawyer review the email templates before sending is switched on.

## Status

Phase 0 scaffold. Sender, mailbox and approver are placeholders. No paid data feeds yet.

## Development

```
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
pytest
```
