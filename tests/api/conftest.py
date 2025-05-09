from unittest.mock import MagicMock

import pytest

from . import GetTestDB, client


@pytest.fixture
def mock_db_session(monkeypatch: pytest.MonkeyPatch):
    db_session = GetTestDB()
    mock_getdb = MagicMock(return_value=db_session)
    monkeypatch.setattr("app.db.GetDB", mock_getdb)
    return mock_getdb


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
