"""Turn a price list or brochure into typed rows with Claude."""
from __future__ import annotations

import base64

import anthropic

from dev_intel.config import ExtractionSettings
from dev_intel.extraction.schema import ExtractedDocument

PROMPT = """You are reading a property developer's price list or brochure.
Extract every lot that the document lists. Copy numbers exactly as printed; do not estimate.
If a value is not in the document, leave it null. Prices are Australian dollars.
Record the page each lot appears on."""


class ExtractionRefused(Exception):
    pass


def _document_block(data: bytes, media_type: str) -> dict:
    if media_type == "application/pdf":
        return {
            "type": "document",
            "source": {"type": "base64", "media_type": "application/pdf", "data": base64.standard_b64encode(data).decode()},
        }
    if media_type.startswith("image/"):
        return {
            "type": "image",
            "source": {"type": "base64", "media_type": media_type, "data": base64.standard_b64encode(data).decode()},
        }
    if media_type.startswith("text/"):
        return {"type": "text", "text": data.decode("utf-8", errors="replace")}
    raise ValueError(f"Unsupported media type for extraction: {media_type}")


def extract_document(
    data: bytes,
    media_type: str,
    settings: ExtractionSettings,
    client: anthropic.Anthropic | None = None,
) -> ExtractedDocument:
    client = client or anthropic.Anthropic()
    response = client.beta.messages.parse(
        model=settings.model,
        max_tokens=16000,
        output_config={"effort": settings.effort},
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        messages=[{"role": "user", "content": [_document_block(data, media_type), {"type": "text", "text": PROMPT}]}],
        output_format=ExtractedDocument,
    )
    if response.stop_reason == "refusal":
        raise ExtractionRefused("Model declined this document; send it to manual review")
    if response.parsed_output is None:
        raise ExtractionRefused(f"No structured output (stop_reason={response.stop_reason}); send to manual review")
    return response.parsed_output
