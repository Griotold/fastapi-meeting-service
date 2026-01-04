from fastapi import status
from fastapi.testclient import TestClient
from appserver.apps.account.models import User

def test_내_정보_조회(client_with_auth: TestClient, host_user: User):
    response = client_with_auth.get("/account/@me")

    data = response.json()
    assert response.status_code == status.HTTP_200_OK

    response_keys = frozenset(data.keys())
    expected_keys = frozenset(["username", "display_name", "is_host", "email", "created_at", "updated_at"])

    assert response_keys == expected_keys