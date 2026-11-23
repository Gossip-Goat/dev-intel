"""What Claude must return for a price list or brochure."""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class LotStatus(str, Enum):
    available = "available"
    held = "held"
    sold = "sold"
    unknown = "unknown"


class PropertyType(str, Enum):
    apartment = "apartment"
    townhouse = "townhouse"
    house_and_land = "house_and_land"
    land = "land"
    other = "other"


class ExtractedLot(BaseModel):
    lot_number: str = Field(description="Lot, unit or apartment number exactly as printed")
    stage: str | None = Field(None, description="Stage, building or release name if shown")
    property_type: PropertyType
    level: int | None = None
    bedrooms: float | None = None
    bathrooms: float | None = None
    car_parks: int | None = None
    internal_m2: float | None = None
    external_m2: float | None = Field(None, description="Balcony, courtyard or terrace area")
    land_m2: float | None = Field(None, description="Land area for house-and-land or land lots")
    price_aud: int | None = Field(None, description="Listed price in whole dollars; null if not shown")
    status: LotStatus = LotStatus.unknown
    source_page: int | None = Field(None, description="1-indexed page the row appears on")


class ExtractedDocument(BaseModel):
    development_name: str | None
    developer: str | None
    address: str | None
    suburb: str | None
    document_date: str | None = Field(None, description="Date printed on the document, ISO format, if any")
    incentives: list[str] = Field(default_factory=list, description="Rebates, rental guarantees, stamp duty offers")
    lots: list[ExtractedLot]
    notes: str | None = Field(None, description="Anything that affects how the prices should be read")
