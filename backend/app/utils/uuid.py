"""UUIDv7 utility for primary key generation."""

from __future__ import annotations

from uuid import UUID

from uuid_utils import uuid7


def generate_uuid7() -> UUID:
    """Generate a UUIDv7 (time-sortable)."""
    return uuid7()
