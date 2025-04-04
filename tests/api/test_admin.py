from tests.api import client


def test_base():
    response = client.get("/")
    assert response.status_code == 200


def test_admin_login():
    """Test that the admin login route is accessible."""

    response = client.post(
        "/api/admin/token", data={"username": "testadmin", "password": "testadmin", "grant_type": "password"}
    )
    assert response.status_code == 200
