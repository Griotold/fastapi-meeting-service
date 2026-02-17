from datetime import date, timedelta
import pytest

from fastapi import status
from fastapi.testclient import TestClient
from pytest_lazy_fixtures import lf

from appserver.apps.account.models import User
from appserver.apps.calendar.models import TimeSlot, Booking
from appserver.apps.calendar.schemas import BookingOut
from tests.conftest import FIXED_TEST_DATE

def get_next_weekday(weekday: int, weeks_ahead: int = 1, base_date: date = FIXED_TEST_DATE) -> date:
    """지정한 요일의 미래 날짜를 반환 (0=월요일, 1=화요일, ...)"""
    days_ahead = weekday - base_date.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return base_date + timedelta(days=days_ahead + (weeks_ahead - 1) * 7)


def get_past_weekday(weekday: int, weeks_ago: int = 1, base_date: date = FIXED_TEST_DATE) -> date:
    """지정한 요일의 과거 날짜를 반환 (0=월요일, 1=화요일, ...)"""
    days_ago = base_date.weekday() - weekday
    if days_ago <= 0:
        days_ago += 7
    return base_date - timedelta(days=days_ago + (weeks_ago - 1) * 7)

@pytest.mark.usefixtures("host_user_calendar")
async def test_유효한_예약_신청_내용으로_예약_생성을_요청하면_예약_내용을_담아_HTTP_201_응답을_한다(
    host_user: User,
    client_with_guest_auth: TestClient,
    time_slot_tuesday: TimeSlot,
):
    target_date = get_next_weekday(1)  # 다음 화요일
    payload = {
        "when": target_date.isoformat(),
        "topic": "test",
        "description": "test",
        "time_slot_id": time_slot_tuesday.id,
    }

    response = client_with_guest_auth.post(f"/bookings/{host_user.username}", json=payload)

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()

    assert data["when"] == target_date.isoformat()
    assert data["topic"] == "test"
    assert data["description"] == "test"
    assert data["time_slot"]["start_time"] == time_slot_tuesday.start_time.isoformat()
    assert data["time_slot"]["end_time"] == time_slot_tuesday.end_time.isoformat()
    assert data["time_slot"]["weekdays"] == time_slot_tuesday.weekdays

async def test_호스트가_아닌_사용자에게_예약을_생성하면_HTTP_404_응답을_한다(
        cute_guest_user: User,
        client_with_guest_auth: TestClient,
        time_slot_tuesday: TimeSlot,
):
    target_date = get_next_weekday(1)  # 다음 화요일
    payload = {
        "when": target_date.isoformat(),
        "topic": "test",        
        "description": "test",
        "time_slot_id": time_slot_tuesday.id,
    }

    response = client_with_guest_auth.post(f"/bookings/{cute_guest_user.username}", json=payload)

    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.parametrize(
        "time_slot_id_add, weekday",
        [
            (100, 1),  # 존재하지 않는 time_slot_id, 화요일
            (0, 2),    # 수요일 (화요일 아님)
            (0, 3),    # 목요일 (화요일 아님)
        ],
)
@pytest.mark.usefixtures("host_user_calendar")
async def test_존재하지_않는_시간대에_예약을_생성하면_HTTP_404_응답을_한다(
        host_user: User,
        client_with_guest_auth: TestClient,
        time_slot_tuesday: TimeSlot,
        time_slot_id_add: int,
        weekday: int,
):
    target_date = get_next_weekday(weekday)
    payload = {
        "when": target_date.isoformat(),
        "topic": "test",
        "description": "test",
        "time_slot_id": time_slot_tuesday.id + time_slot_id_add,
    }

    response = client_with_guest_auth.post(f"/bookings/{host_user.username}", json=payload)

    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.usefixtures("host_user_calendar")
async def test_자기_자신에게_예약을_생성하면_HTTP_422_응답을_한다(
        host_user: User,
        client_with_auth: TestClient,
        time_slot_tuesday: TimeSlot,
):
    target_date = get_next_weekday(1)  # 다음 화요일
    payload = {
        "when": target_date.isoformat(),
        "topic": "test",
        "description": "test",
        "time_slot_id": time_slot_tuesday.id,
    }

    response = client_with_auth.post(f"/bookings/{host_user.username}", json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

@pytest.mark.usefixtures("host_user_calendar")
async def test_과거_일자에_예약을_생성하면_HTTP_422_응답을_한다(
        host_user: User,
        client_with_guest_auth: TestClient,
        time_slot_tuesday: TimeSlot,
):
    past_date = get_past_weekday(1)  # 지난 화요일
    payload = {
        "when": past_date.isoformat(),
        "topic": "test",
        "description": "test",
        "time_slot_id": time_slot_tuesday.id,
    }

    response = client_with_guest_auth.post(f"/bookings/{host_user.username}", json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

@pytest.mark.usefixtures("host_user_calendar")
async def test_중복_예약을_생성하면_HTTP_422_응답을_한다(
        host_user: User,
        client_with_guest_auth: TestClient,
        time_slot_tuesday: TimeSlot,
):
    target_date = get_next_weekday(1)  # 다음 화요일
    payload = {
        "when": target_date.isoformat(),
        "topic": "test",
        "description": "test",
        "time_slot_id": time_slot_tuesday.id,
    }

    # 첫 번째 예약 생성 (성공)
    first_response = client_with_guest_auth.post(f"/bookings/{host_user.username}", json=payload)
    assert first_response.status_code == status.HTTP_201_CREATED

    # 동일한 내용으로 두 번째 예약 시도 (실패 - 중복)
    second_response = client_with_guest_auth.post(f"/bookings/{host_user.username}", json=payload)
    assert second_response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

@pytest.mark.usefixtures("charming_host_bookings")
async def test_호스트는_페이지_단위로_자신에게_예약된_부킹_목록을_받는다(
    client_with_auth: TestClient,
    host_bookings: list[Booking],
):
    response = client_with_auth.get("/bookings", params={"page": 1, "page_size": 10})

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == len(host_bookings)

@pytest.mark.parametrize(
    "year, month",
    [(2024, 12), (2025, 1)],
)
@pytest.mark.usefixtures("charming_host_bookings")
async def test_게스트는_호스트의_캘린더의_예약_내역을_월_단위로_받는다(
    client_with_guest_auth: TestClient,
    host_bookings: list[Booking],
    host_user: User,
    year: int,
    month: int,
):
    params = {
        "year": year,
        "month": month,
    }
    response = client_with_guest_auth.get(f"/calendar/{host_user.username}/bookings", params=params)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    booking_dates = frozenset([
        booking.when.isoformat() 
        for booking in host_bookings
        if booking.when.year == params["year"] and booking.when.month == params["month"]
    ])
    assert not not data
    assert len(data) == len(booking_dates)
    assert all([item["when"] in booking_dates for item in data])

async def test_게스트는_자신의_캘린더의_예약_내역을_페이지_단위로_받는다(
        client_with_guest_auth: TestClient,
        host_bookings: list[Booking],
        charming_host_bookings: list[Booking]
):
    response = client_with_guest_auth.get("/guest-calendar/bookings", params={"page": 1, "page_size": 50})

    assert response.status_code == status.HTTP_200_OK

    id_set = frozenset([booking.id for booking in host_bookings] + [booking.id for 
                        booking in charming_host_bookings])
    
    data = response.json()
    assert len(data) == len(id_set)
    assert all([item["id"] in id_set for item in data])

@pytest.mark.parametrize(
    "client, booking_fixture, expected_status_code",
    [
        # 게스트 케이스
        (lf("client_with_guest_auth"), lf("host_bookings"), status.HTTP_200_OK),
        (lf("client_with_smart_guest_auth"), lf("host_bookings"), status.HTTP_404_NOT_FOUND),

        # 호스트 케이스
        (lf("client_with_auth"), lf("host_bookings"), status.HTTP_200_OK),  # 자신의 캘린더 부킹
        (lf("client_with_auth"), lf("host_as_guest_booking"), status.HTTP_200_OK),  # 자신이 게스트로 참여
        (lf("client_with_auth"), lf("charming_host_bookings"), status.HTTP_404_NOT_FOUND),  # 관련 없는 부킹
    ],
)
async def test_사용자는_특정_예약_내역_데이터를_받는다(
    client: TestClient,
    booking_fixture,
    expected_status_code: int,
):
    # booking_fixture가 리스트인 경우 첫 번째 요소 사용, 아니면 그대로 사용
    booking = booking_fixture[0] if isinstance(booking_fixture, list) else booking_fixture

    response = client.get(f"/bookings/{booking.id}")

    assert response.status_code == expected_status_code

    if expected_status_code == status.HTTP_200_OK:
        data = response.json()
        assert data["id"] == booking.id


@pytest.mark.parametrize(
    "payload",
    [
        {"when": get_next_weekday(1).isoformat(), "time_slot": lf("time_slot_tuesday")},  # 다음 화요일
        {"when": get_next_weekday(0).isoformat(), "time_slot": lf("time_slot_monday")},  # 다음 월요일
    ],
)
@pytest.mark.usefixtures("host_user_calendar")
async def test_호스트는_자신에게_신청한_부킹에_대해_일자_타임슬롯을_변경할_수_있다(
    payload: dict,
    client_with_auth: TestClient,
    host_bookings: list[Booking],
):
    booking = host_bookings[0]
    time_slot: TimeSlot = payload["time_slot"]
    payload["time_slot_id"] = time_slot.id
    del payload["time_slot"]

    response = client_with_auth.patch(f"/bookings/{booking.id}", json=payload)

    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["when"] == payload["when"]
    assert data["time_slot"]["start_time"] == time_slot.start_time.isoformat()
    assert data["time_slot"]["end_time"] == time_slot.end_time.isoformat()
    assert data["time_slot"]["weekdays"] == time_slot.weekdays

@pytest.mark.parametrize(
    "time_slot, expected_status_code",
    [
        (lf("time_slot_friday"), status.HTTP_404_NOT_FOUND),
        (lf("time_slot_tuesday"), status.HTTP_200_OK),
    ],
)
async def test_호스트는_다른_호스트의_타임슬롯을_변경할_할_수_없다(
    client_with_auth: TestClient,
    host_bookings: list[Booking],
    time_slot: TimeSlot,
    expected_status_code: int,
):
    response = client_with_auth.patch(
        f"/bookings/{host_bookings[0].id}",
        json={"time_slot_id": time_slot.id},
    )
    assert response.status_code == expected_status_code

@pytest.mark.parametrize(
    "time_slot, expected_status_code",
    [
        (lf("time_slot_friday"), status.HTTP_404_NOT_FOUND),
        (lf("time_slot_tuesday"), status.HTTP_200_OK),
    ],
)
async def test_게스트는_다른_호스트의_타임슬롯을_변경할_할_수_없다(
    client_with_guest_auth: TestClient,
    host_bookings: list[Booking],
    time_slot: TimeSlot,
    expected_status_code: int,
):
    response = client_with_guest_auth.patch(
        f"/guest-bookings/{host_bookings[0].id}",
        json={"time_slot_id": time_slot.id},
    )
    assert response.status_code == expected_status_code

@pytest.mark.parametrize(
    "payload",
    [
        {"topic": "test", "description": "test", "when": get_next_weekday(1).isoformat(), "time_slot": lf("time_slot_tuesday")},  # 다음 화요일
        {"topic": "test", "description": "test", "when": get_next_weekday(0).isoformat(), "time_slot": lf("time_slot_monday")},  # 다음 월요일
        {"description": "test", "when": get_next_weekday(1).isoformat()},  # 다음 화요일 (time_slot 변경 없음)
    ],
)
async def test_게스트는_자신의_부킹에_대해_주제_설명_일자_타임슬롯을_변경할_수_있다(
    client_with_guest_auth: TestClient,
    host_bookings: list[Booking],
    payload: dict,
):
    booking = host_bookings[0]

    # 변경 전 데이터 추출
    before_booking = BookingOut.model_validate(
        booking,
        from_attributes=True,
    ).model_dump(mode="json")

    # 변경 가능한 필드 설정
    updatable_fields = set(["topic", "description", "when", "time_slot"])
    exceptable_fields = updatable_fields - set(payload.keys())

    # 타임슬롯 처리
    if time_slot := payload.pop("time_slot", None):
        time_slot: TimeSlot
        payload["time_slot_id"] = time_slot.id
    else:
        time_slot = None
        payload["time_slot_id"] = None
    
    # 요청 보내기
    response = client_with_guest_auth.patch(
        f"/guest-bookings/{booking.id}",
        json=payload
    )

    # 응답 검증
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # 변경된 필드 검증
    for field, value in payload.items():
        if field == "time_slot_id" and time_slot:
            assert data["time_slot"]["start_time"] == time_slot.start_time.isoformat()
            assert data["time_slot"]["end_time"] == time_slot.end_time.isoformat()
            assert data["time_slot"]["weekdays"] == time_slot.weekdays
        else:
            assert payload[field] == value
    
    # 변경되지 않은 필드 검증
    for field_name in exceptable_fields:
        if field_name == "time_slot":
            assert before_booking["time_slot"]["start_time"] == data["time_slot"]["start_time"]
            assert before_booking["time_slot"]["end_time"] == data["time_slot"]["end_time"]
            assert before_booking["time_slot"]["weekdays"] == data["time_slot"]["weekdays"]
        else:
            assert before_booking[field_name] == data[field_name]

@pytest.mark.parametrize(
    "when, expected_status_code",
    [
        (get_next_weekday(2), status.HTTP_422_UNPROCESSABLE_ENTITY),  # 수요일 - 실패
        (get_next_weekday(1), status.HTTP_200_OK),  # 화요일 - 성공
    ],
)
async def test_호스트는_타임슬롯_요일이_아닌_날짜로_변경할_수_없다(
    client_with_auth: TestClient,
    host_bookings: list[Booking],
    when: date,
    expected_status_code: int,
):
    response = client_with_auth.patch(
        f"/bookings/{host_bookings[0].id}",
        json={"when": when.isoformat()},
    )
    assert response.status_code == expected_status_code

@pytest.mark.parametrize(
    "when, expected_status_code",
    [
        (get_next_weekday(2), status.HTTP_422_UNPROCESSABLE_ENTITY),  # 수요일 - 실패
        (get_next_weekday(1), status.HTTP_200_OK),  # 화요일 - 성공
    ],
)
async def test_게스트는_타임슬롯_요일이_아닌_날짜로_변경할_수_없다(
    client_with_guest_auth: TestClient,
    host_bookings: list[Booking],
    when: date,
    expected_status_code: int,
):
    response = client_with_guest_auth.patch(
        f"/guest-bookings/{host_bookings[0].id}",
        json={"when": when.isoformat()},
    )
    assert response.status_code == expected_status_code