from sqlalchemy.ext.asyncio import AsyncSession
from appserver.apps.account.endpoints import signup
from appserver.apps.account.models import User
from fastapi.testclient import TestClient
import pytest
from pydantic import ValidationError
from appserver.apps.account.exceptions import DuplicatedUsernameError, DuplicatedEmailError
from appserver.apps.account.schemas import SignupPayload

# 1. 유효성 검증 테스트
@pytest.mark.parametrize(
    "username",
    [
        "0123456789012345678901234567890123456789012345678901234567890123456789",
        12345678,
        "x"
    ]
)
async def test_사용자명이_유효하지_않으면_사용자명이_유효하지_않다는_메시지를_담은_오류를_일으킨다(
        db_session: AsyncSession,
        username: str
):
    payload = {
        "username": username,
        "email": "test@example.com",
        "display_name": "test",
        "password": "test테스트1234",
        "password_again": "test테스트1234",  # 추가!
    }

    with pytest.raises(ValidationError):
        SignupPayload(**payload)  # signup 호출 전에 검증

# 2. 중복 username 테스트
async def test_계정_ID가_중복되면_중복_계정_ID_오류를_일으킨다(
        db_session: AsyncSession
):
    payload = {
        "username": "test",
        "email": "test@example.com",
        "display_name": "test",
        "password": "test테스트1234",
        "password_again": "test테스트1234",  # 추가!
    }
    await signup(SignupPayload(**payload), db_session)

    payload["email"] = "test2@example.com"  # @ 추가!
    with pytest.raises(DuplicatedUsernameError):
        await signup(SignupPayload(**payload), db_session)

# 3. 중복 email 테스트
async def test_이메일_주소가_중복되면_중복_이메일_오류를_일으킨다(db_session: AsyncSession):
    payload = {
        "username": "test",
        "email": "test@example.com",
        "display_name": "test",
        "password": "test테스트1234",
        "password_again": "test테스트1234",  # 추가!
    }
    await signup(SignupPayload(**payload), db_session)

    payload["username"] = "test2"
    with pytest.raises(DuplicatedEmailError):
        await signup(SignupPayload(**payload), db_session)

# 4. display_name 자동생성 테스트
@pytest.mark.parametrize(
    "payload",
    [
        {
            "username": "test",
            "email": "test@example.com",
            "password": "test테스트1234",
            "password_again": "test테스트1234",  # 추가!
        },
        {
            "username": "test",
            "email": "test@example.com",
            "password": "test테스트1234",
            "password_again": "test테스트1234",  # 추가!
            "display_name": "",
        },
    ]
)
async def test_표시명을_입력하지_않으면_무작위_문자열_8글자로_대신한다(
    db_session: AsyncSession,
    payload
):
    user = await signup(SignupPayload(**payload), db_session)
    assert isinstance(user.display_name, str)
    assert len(user.display_name) == 8

async def test_비밀번호가_일치하지_않으면_오류를_일으킨다(db_session: AsyncSession):
    payload = {
        "username": "test",
        "email": "test@example.com",
        "display_name": "test",
        "password": "test테스트1234",
        "password_again": "test테스트5678",  # 다른 비밀번호!
    }

    with pytest.raises(ValidationError) as exc_info:
        SignupPayload(**payload)
    
    # 에러 메시지 확인 (선택사항)
    assert "비밀번호가 일치하지 않습니다" in str(exc_info.value)