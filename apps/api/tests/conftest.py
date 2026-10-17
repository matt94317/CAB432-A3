"""Shared API test fixtures."""

import pytest
from fastapi.testclient import TestClient

from hookd_api.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
