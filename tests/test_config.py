import pytest
from pydantic import ValidationError

from dev_intel.config import load_allowlist, load_settings


def test_settings_load_and_are_frozen():
    s = load_settings()
    assert s.inquiry.sending_enabled is False
    assert s.gcp.region == "australia-southeast1"
    with pytest.raises(ValidationError):
        s.sender.email = "x@y.example"


def test_allowlist_blocks_portal():
    a = load_allowlist()
    assert any(b.domain == "realestate.com.au" for b in a.blocked)
