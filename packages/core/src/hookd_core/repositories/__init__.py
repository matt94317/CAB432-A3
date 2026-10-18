"""Storage interfaces. Services depend on these, not on a database.

They live in hookd_core because the API and the sync worker both use them: the
worker upserts posts and the API reads them.

Each repository has two implementations, built by `hookd_core.storage`:
- DynamoDB (`dynamodb.py`): the A3 store, one table shared by every service
- In-memory: tests and quick local runs; per process, so not shared

After A3 the plan is to move back to RDS PostgreSQL: add SQL implementations of
these protocols and a STORAGE option for them. Services don't change.
"""
