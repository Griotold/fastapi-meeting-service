from sqlalchemy.ext.asyncio import AsyncSession
from appserver.apps.account.endpoints import signup
from appserver.apps.account.models import User
from fastapi.testclient import TestClient


# async def test_모든_입력_항목을_유효한_값으로_입력하면_계정이_생성된다(db_session: AsyncSession):
async def test_signup_with_valid_inputs_creates_account(
        client: TestClient,
        db_session: AsyncSession
):
    payload = {
        "username": "test",
        "email": "test@example.com",
        "display_name": "test",
        "password": "test테스트1234",
    }

    result = await signup(payload, db_session)

    assert isinstance(result, User)
    assert result.username == payload["username"]
    assert result.email == payload["email"]
    assert result.display_name == payload["display_name"]
    assert result.is_host is False

    response = client.get(f"/account/users/{payload['username']}")
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == payload["username"]
    assert data["email"] == payload["email"]
    assert data["display_name"] == payload["display_name"]
    assert data["is_host"] is False


