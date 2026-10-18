"""Storage interfaces. Services depend on these, not on a database.

They live in hookd_core because the API and the sync worker both use them: the
worker upserts posts and the API reads them.

The A3 database (RDS vs DynamoDB) is still being decided, so each repository has
an in-memory implementation for development and tests. In-memory stores are
per process, so the API and worker can't share data until the real store exists.
Adding it means writing one class per repository and wiring it in `hookd_api.deps`
and `hookd_worker.main`.
"""
