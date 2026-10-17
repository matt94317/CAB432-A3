"""Storage interfaces. Services depend on these, not on a database.

The A3 database (RDS vs DynamoDB) is still being decided, so each repository has
an in-memory implementation for development and tests. Adding the real store
means writing one class per repository and wiring it in `hookd_api.deps`.
"""
