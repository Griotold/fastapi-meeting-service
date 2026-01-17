from datetime import time
import pytest
from fastapi import status
from fastapi.testclient import TestClient
import calendar

@pytest.mark.usefixtures("host_user_calendar")
async def test_호스트_사용자는_유효한_타임슬롯_정보를_제출하여_타임슬롯을_생성할_수_있다(
    client_with_auth: TestClient,
):
    payload = {
        "start_time": time(10, 0).isoformat(),
        "end_time": time(11, 0).isoformat(),
        "weekdays": [calendar.MONDAY, calendar.TUESDAY, calendar.WEDNESDAY],
    }

    response = client_with_auth.post("/time-slots", json=payload)

    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.usefixtures("host_user_calendar")
async def test_유효하지_않은_타임슬롯_정보로_생성하려_하면_HTTP_422_응답을_한다(
    client_with_auth: TestClient,
):
    payload = {
        "start_time": time(11, 0).isoformat(),
        "end_time": time(10, 0).isoformat(),
        "weekdays": [calendar.MONDAY, calendar.TUESDAY, calendar.WEDNESDAY],
    }

    response = client_with_auth.post("/time-slots", json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

# 장식자는 함수에서 가까운 쪽부터 실행이 된다.
@pytest.mark.parametrize("weekdays", [
    [-1, 0, 1, 2, 3, 4, 5, 6],
    [1, 2, 3, 4, 5, 6, 7]
])
@pytest.mark.usefixtures("host_user_calendar")
async def test_요일_값은_월_화_수_목_금_토_일_순이며_각_요일_값은_0부터_시작한다(
    client_with_auth: TestClient,
    weekdays: list[int],
):
    payload = {
        "start_time": time(10, 0).isoformat(),
        "end_time": time(11, 0).isoformat(),
        "weekdays": weekdays,
    }

    response = client_with_auth.post("/time-slots", json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

@pytest.mark.parametrize("start_time, end_time, weekdays, expected_status_code", [
    # 겹치지 않는 경우 - 시간대가 완전히 다름
    (time(9, 0), time(10, 0), [calendar.MONDAY], status.HTTP_201_CREATED),  # 10시 이전
    (time(11, 0), time(12, 0), [calendar.MONDAY], status.HTTP_201_CREATED),  # 10시 이후
    (time(8, 0), time(9, 0), [calendar.TUESDAY], status.HTTP_201_CREATED),  # 완전히 이전
    
    # 겹치는 경우 (같은 요일, 시간 겹침)
    (time(10, 0), time(11, 0), [calendar.MONDAY], status.HTTP_422_UNPROCESSABLE_ENTITY),  # 완전히 동일
    (time(10, 30), time(11, 30), [calendar.MONDAY], status.HTTP_422_UNPROCESSABLE_ENTITY),  # 부분 겹침 (뒤)
    (time(9, 30), time(10, 30), [calendar.MONDAY], status.HTTP_422_UNPROCESSABLE_ENTITY),  # 부분 겹침 (앞)
    (time(10, 15), time(10, 45), [calendar.MONDAY], status.HTTP_422_UNPROCESSABLE_ENTITY),  # 완전 포함
    (time(9, 0), time(12, 0), [calendar.MONDAY], status.HTTP_422_UNPROCESSABLE_ENTITY),  # 기존 시간대 포함
    
    # 겹치지 않는 경우 (다른 요일)
    (time(10, 0), time(11, 0), [calendar.THURSDAY], status.HTTP_201_CREATED),  # 같은 시간, 다른 요일
    (time(10, 30), time(11, 30), [calendar.FRIDAY], status.HTTP_201_CREATED),  # 겹치는 시간, 다른 요일
    (time(9, 0), time(12, 0), [calendar.SATURDAY, calendar.SUNDAY], status.HTTP_201_CREATED),  # 포함하는 시간, 다른 요일들
])
@pytest.mark.usefixtures("host_user_calendar")
async def test_겹치는_시간대가_있는_경우_HTTP_422_응답을_한다(
    client_with_auth: TestClient,
    start_time: time,
    end_time: time,
    weekdays: list[int],
    expected_status_code: int,
):
    # 먼저 기준 타임슬롯 생성 (월,화,수 10:00-11:00) - 이 때는 모두 201
    base_payload = {
        "start_time": time(10, 0).isoformat(),
        "end_time": time(11, 0).isoformat(),
        "weekdays": [calendar.MONDAY, calendar.TUESDAY, calendar.WEDNESDAY],
    }
    response = client_with_auth.post("/time-slots", json=base_payload)
    assert response.status_code == status.HTTP_201_CREATED
    
    # 테스트할 타임슬롯 생성 시도 - 여기서 안 겹치면 201, 겹치면 422
    payload = {
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "weekdays": weekdays,
    }
    response = client_with_auth.post("/time-slots", json=payload)
    
    assert response.status_code == expected_status_code
