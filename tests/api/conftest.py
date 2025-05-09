from unittest.mock import AsyncMock

import pytest

from . import TestSession, client


@pytest.fixture(autouse=True)
def mock_db_session(monkeypatch: pytest.MonkeyPatch):
    db_session = AsyncMock()
    db_session.__aenter__.return_value = TestSession
    db_session.__aexit__.return_value = None
    monkeypatch.setattr("app.db.GetDB", db_session)
    return db_session


@pytest.fixture
def access_token(mock_db_session) -> str:
    response = client.post(
        url="/api/admin/token",
        data={"username": "testadmin", "password": "testadmin", "grant_type": "password"},
    )
    return response.json()["access_token"]


@pytest.fixture
def disable_cache(monkeypatch: pytest.MonkeyPatch):
    def dummy_cached(*args, **kwargs):
        def wrapper(func):
            return func  # bypass caching

        return wrapper

    monkeypatch.setattr("app.settings.cached", dummy_cached)
