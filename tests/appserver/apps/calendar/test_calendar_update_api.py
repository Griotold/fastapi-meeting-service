# tests/appserver/apps/calendar/test_calendar_update_api.py

from fastapi import status
from fastapi.testclient import TestClient
import pytest
from appserver.apps.account.models import User
from appserver.apps.calendar.models import Calendar


@pytest.mark.parametrize("payload", [
    # topics만 변경
    {
        "topics": ["new_topic1", "new_topic2"],
    },
    # description만 변경
    {
        "description": "new description for testing",
    },
    # google_calendar_id만 변경
    {
        "google_calendar_id": "new_calendar_id_with_more_than_90_characters@group.calendar.google.com",
    },
    # 모두 변경
    {
        "topics": ["updated_topic"],
        "description": "completely new description",
        "google_calendar_id": "another_new_calendar_id_with_sufficient_length@group.calendar.google.com",
    },
])
async def test_사용자가_변경하는_항목만_변경되고_나머지는_기존_값을_유지한다(
        payload: dict,
        host_user: User,
        host_user_calendar: Calendar,
        client_with_auth: TestClient,
) -> None:
    response = client_with_auth.patch("/calendar", json=payload)
    
    assert response.status_code == status.HTTP_200_OK
    
    result = response.json()
    
    # 변경된 항목은 새 값으로
    if "topics" in payload:
        # 중복 제거 및 순서 유지 확인
        expected_topics = list(dict.fromkeys(payload["topics"]))
        assert result["topics"] == expected_topics
    else:
        # 변경 안 했으면 기존 값 유지
        assert result["topics"] == host_user_calendar.topics
    
    if "description" in payload:
        assert result["description"] == payload["description"]
    else:
        assert result["description"] == host_user_calendar.description
    
    if "google_calendar_id" in payload:
        assert result["google_calendar_id"] == payload["google_calendar_id"]
    else:
        assert result["google_calendar_id"] == host_user_calendar.google_calendar_id


async def test_주제는_하나_이상_있어야_한다(
        client_with_auth: TestClient,
        host_user_calendar: Calendar,
) -> None:
    payload = {
        "topics": [],  # 빈 리스트
    }
    
    response = client_with_auth.patch("/calendar", json=payload)
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


async def test_설명은_10글자_이상_입력해야_한다(
        client_with_auth: TestClient,
        host_user_calendar: Calendar,
) -> None:
    payload = {
        "description": "short",  # 10글자 미만
    }
    
    response = client_with_auth.patch("/calendar", json=payload)
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


async def test_구글_캘린더_ID는_항상_있어야_한다(
        client_with_auth: TestClient,
        host_user_calendar: Calendar,
) -> None:
    payload = {
        "google_calendar_id": "",  # 빈 문자열
    }
    
    response = client_with_auth.patch("/calendar", json=payload)
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


async def test_캘린더가_없으면_404_응답을_반환한다(
        host_user: User,
        client_with_auth: TestClient,
        db_session,
) -> None:
    # 캘린더 삭제 (fixture에서 생성된 캘린더 제거)
    from sqlmodel import select, delete
    stmt = delete(Calendar).where(Calendar.host_id == host_user.id)
    await db_session.execute(stmt)
    await db_session.commit()
    
    payload = {
        "description": "trying to update non-existent calendar",
    }
    
    response = client_with_auth.patch("/calendar", json=payload)
    
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_게스트_사용자는_캘린더를_변경할_수_없다(
        client_with_guest_auth: TestClient,
) -> None:
    payload = {
        "description": "guest trying to update",
    }
    
    response = client_with_guest_auth.patch("/calendar", json=payload)
    
    # 게스트는 캘린더가 없으므로 404 또는 403
    assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]


async def test_로그인하지_않은_사용자는_캘린더를_변경할_수_없다(
        client: TestClient,
) -> None:
    payload = {
        "description": "anonymous trying to update",
    }
    
    response = client.patch("/calendar", json=payload)
    
    # ✅ 422 또는 401 둘 다 허용 (FastAPI 동작 특성상)
    assert response.status_code in [
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_422_UNPROCESSABLE_ENTITY
    ]