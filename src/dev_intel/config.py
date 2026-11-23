"""Loads fixed configuration. Settings are frozen so nothing at runtime can change the sender identity."""
from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict

CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"


class Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class Sender(Frozen):
    name: str
    role: str
    company: str
    abn: str
    email: str
    phone: str
    postal_address: str


class ResearchFirm(Frozen):
    enabled: bool
    name: str
    contact_name: str
    email: str
    abn: str
    postal_address: str


class InquirySettings(Frozen):
    sending_enabled: bool
    approver: str
    require_approval: bool
    max_open_per_development: int
    max_sends_per_agency_per_week: int
    follow_up_after_days: int
    max_follow_ups: int
    unsubscribe_honour_business_days: int


class FetcherSettings(Frozen):
    user_agent: str
    min_seconds_between_requests: float
    timeout_seconds: float


class ExtractionSettings(Frozen):
    model: str
    effort: str


class AwsSettings(Frozen):
    region: str
    raw_bucket: str


class Settings(Frozen):
    sender: Sender
    research_firm: ResearchFirm
    inquiry: InquirySettings
    fetcher: FetcherSettings
    extraction: ExtractionSettings
    aws: AwsSettings


class AllowedDomain(Frozen):
    domain: str
    terms_checked_on: str
    checked_by: str
    notes: str = ""


class BlockedDomain(Frozen):
    domain: str
    reason: str


class Allowlist(Frozen):
    allowed: tuple[AllowedDomain, ...] = ()
    blocked: tuple[BlockedDomain, ...] = ()


def _load(name: str, config_dir: Path) -> dict:
    with open(config_dir / name, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_settings(config_dir: Path = CONFIG_DIR) -> Settings:
    return Settings.model_validate(_load("settings.yaml", config_dir))


def load_allowlist(config_dir: Path = CONFIG_DIR) -> Allowlist:
    data = _load("allowlist.yaml", config_dir)
    return Allowlist(allowed=tuple(data.get("allowed") or ()), blocked=tuple(data.get("blocked") or ()))


def is_placeholder(value: str) -> bool:
    return "PLACEHOLDER" in value.upper() or "placeholder" in value.lower()
