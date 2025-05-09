import pytest

from . import GetTestDB, client


@pytest.fixture
def access_token():
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


@pytest.fixture
def patch_db(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("app.db.GetDB.__call__", lambda *args, **kwargs: GetTestDB)
