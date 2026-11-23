"""Approval queue states. Storage lives in the lake's inquiry table."""
from __future__ import annotations

from enum import Enum


class InquiryStatus(str, Enum):
    drafted = "drafted"            # passed identity checks, waiting for approval
    approved = "approved"
    rejected = "rejected"          # approver said no
    sent = "sent"
    replied = "replied"
    declined = "declined"          # agent said no; never contact again for this development
    unsubscribed = "unsubscribed"  # added to suppression list
    closed = "closed"              # no reply after the follow-up


class ReplyClass(str, Enum):
    sent_documents = "sent_documents"
    declined = "declined"
    question = "question"
    unsubscribe = "unsubscribe"
    other = "other"
