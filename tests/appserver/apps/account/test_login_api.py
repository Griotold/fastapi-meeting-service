from fastapi import status
from fastapi.testclient import TestClient
from appserver.apps.account.schemas import LoginPayload
from appserver.apps.account.models import User

async def test_로그인_성공(host_user: User, client: TestClient):
    payload = LoginPayload.model_validate(
        {
            "username": host_user.username,
            "password": "testtest"
        }
    )

    response = client.post("/account/login", json=payload.model_dump())

    assert response.status_code == status.HTTP_200_OK