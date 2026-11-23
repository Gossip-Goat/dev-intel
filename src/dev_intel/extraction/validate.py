"""Plausibility checks. Rows that fail go to the review queue, not the lake."""
from __future__ import annotations

from dataclasses import dataclass

from dev_intel.extraction.schema import ExtractedDocument, ExtractedLot, PropertyType

# Wide bounds that catch extraction slips (a dropped zero, a price in the area column),
# not market judgements. Tune once real data is flowing.
MIN_PRICE_AUD = 100_000
MAX_PRICE_AUD = 50_000_000
MIN_RATE_PER_M2 = 2_000
MAX_RATE_PER_M2 = 60_000


@dataclass(frozen=True)
class Issue:
    lot_number: str
    problem: str


def check_lot(lot: ExtractedLot) -> list[Issue]:
    issues: list[Issue] = []
    if lot.price_aud is not None and not (MIN_PRICE_AUD <= lot.price_aud <= MAX_PRICE_AUD):
        issues.append(Issue(lot.lot_number, f"price {lot.price_aud} outside {MIN_PRICE_AUD}-{MAX_PRICE_AUD}"))
    if lot.property_type == PropertyType.apartment and lot.price_aud and lot.internal_m2:
        rate = lot.price_aud / lot.internal_m2
        if not (MIN_RATE_PER_M2 <= rate <= MAX_RATE_PER_M2):
            issues.append(Issue(lot.lot_number, f"price per internal m2 {rate:.0f} looks wrong"))
    if lot.internal_m2 is not None and lot.internal_m2 <= 0:
        issues.append(Issue(lot.lot_number, "internal area must be positive"))
    return issues


def check_document(doc: ExtractedDocument) -> list[Issue]:
    issues: list[Issue] = []
    seen: set[tuple[str | None, str]] = set()
    for lot in doc.lots:
        key = (lot.stage, lot.lot_number)
        if key in seen:
            issues.append(Issue(lot.lot_number, "duplicate lot number in the same stage"))
        seen.add(key)
        issues.extend(check_lot(lot))
    if not doc.lots:
        issues.append(Issue("-", "no lots found"))
    return issues
