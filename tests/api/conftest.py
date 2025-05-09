import pytest

from . import GetTestDB, client


@pytest.fixture
def mock_db_session(monkeypatch: pytest.MonkeyPatch):
    db_session = GetTestDB()
    monkeypatch.setattr("app.db.GetDB.__call__", lambda *args, **kwargs: db_session)
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
