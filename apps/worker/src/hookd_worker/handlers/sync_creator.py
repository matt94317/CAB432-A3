"""Fetch a creator's recent posts + metrics, match to campaigns by hashtag,
upsert into RDS (idempotent), then invalidate cache (US-13, US-14, US-17)."""
