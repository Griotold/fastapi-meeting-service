from datetime import date
from fastapi import APIRouter, status
from sqlmodel import select, and_, func, true
from sqlalchemy.exc import IntegrityError
from appserver.apps.account.models import User
from appserver.apps.calendar.models import Calendar, TimeSlot
from appserver.db import DbSessionDep
from appserver.apps.account.deps import CurrentUserOptionalDep, CurrentUserDep
from .models import Booking
from .exceptions import CalendarNotFoundError, HostNotFoundError, CalendarAlreadyExistsError, GuestPermissionError, TimeSlotOverlapError, TimeSlotNotFoundError, SelfBookingError, PastDateBookingError, DuplicateBookingError
from .schemas import CalendarDetailOut, CalendarOut, CalendarCreateIn, CalendarUpdateIn, TimeSlotCreateIn, TimeSlotOut, BookingCreateIn, BookingOut

router = APIRouter(tags=["calendar"])

@router.get("/calendar/{host_username}", status_code=status.HTTP_200_OK)
async def host_calendar_detail(
        host_username: str, 
        user: CurrentUserOptionalDep,
        session: DbSessionDep
) -> CalendarOut | CalendarDetailOut:
    # username으로 호스트 유저 찾기
    stmt = select(User).where(User.username == host_username)
    result = await session.execute(stmt)
    host = result.scalar_one_or_none()
    if host is None:
        raise HostNotFoundError()
        
    # 해당 호스트의 캘린더 찾기
    stmt = select(Calendar).where(Calendar.host_id == host.id)
    result = await session.execute(stmt)
    calendar = result.scalar_one_or_none()
    if calendar is None:
        raise CalendarNotFoundError()

    # 권한에 따른 분기 처리
    if user is not None and user.id == host.id:
        return CalendarDetailOut.model_validate(calendar) # 본인 -> 상세 정보
        
    return CalendarOut.model_validate(calendar) # 타인 -> 일반 정보

@router.post(
    "/calendar", 
    status_code=status.HTTP_201_CREATED,
    response_model=CalendarDetailOut,
)
async def create_calendar(
    user: CurrentUserDep,
    session: DbSessionDep,
    payload: CalendarCreateIn,
) -> CalendarDetailOut:
    if not user.is_host:
        raise GuestPermissionError()

    calendar = Calendar(
        host_id=user.id,
        topics=payload.topics,
        description=payload.description,
        google_calendar_id=payload.google_calendar_id,
        )
    session.add(calendar)
    try:
        await session.commit()
    except IntegrityError as exc:
        raise CalendarAlreadyExistsError() from exc
    return calendar

@router.patch(
    "/calendar",
    status_code=status.HTTP_200_OK,
    response_model=CalendarDetailOut,
)
async def update_calendar(
    user: CurrentUserDep,
    session: DbSessionDep,
    payload: CalendarUpdateIn,
) -> CalendarDetailOut:
    # 호스트가 아니면 캘린더를 수정할 수 없다.
    if not user.is_host:
        raise GuestPermissionError()
    
    # 사용자에게 캘린더가 없으면 HTTP 404 응답을 한다.
    if user.calendar is None:
        raise CalendarNotFoundError()
    
    # topics 값이 있으면 변경하고
    if payload.topics is not None:
        user.calendar.topics = payload.topics

    # description 값이 있으면 변경하고
    if payload.description is not None:
        user.calendar.description = payload.description

    # google_calendar_id 값이 있으면 변경하고
    if payload.google_calendar_id is not None:
        user.calendar.google_calendar_id = payload.google_calendar_id

    # 데이터베이스에 반영한다.
    await session.commit()

    return user.calendar

@router.post(
    "/time-slots",
    status_code=status.HTTP_201_CREATED,
    response_model=TimeSlotOut,
)
async def create_time_slot(
    user: CurrentUserDep,
    session: DbSessionDep,
    payload: TimeSlotCreateIn,
) -> TimeSlotOut:
    if not user.is_host:
        raise GuestPermissionError()
    
    # 이미 존재하는 타임슬롯과 겹치는지 확인
    stmt = select(TimeSlot).where(
        and_(
            TimeSlot.calendar_id == user.calendar.id,
            TimeSlot.start_time < payload.end_time,
            TimeSlot.end_time > payload.start_time,
        )
    )

    result = await session.execute(stmt)
    existing_time_slots = result.scalars().all()

    for existing_time_slot in existing_time_slots:
        if any(day in existing_time_slot.weekdays for day in payload.weekdays):
            raise TimeSlotOverlapError()
    
    time_slot = TimeSlot(
        calendar_id = user.calendar.id,
        start_time=payload.start_time,
        end_time=payload.end_time,
        weekdays=payload.weekdays,
    )
    session.add(time_slot)
    await session.commit()
    return time_slot

@router.post(
    "/bookings/{host_username}",
    status_code=status.HTTP_201_CREATED,
    response_model=BookingOut,
)
async def create_booking(
    host_username: str,
    user: CurrentUserDep,
    session: DbSessionDep,
    payload: BookingCreateIn
) -> BookingOut:
    stmt = (
        select(User)
        .where(User.username == host_username)
        .where(User.is_host.is_(true()))
    )
    result = await session.execute(stmt)
    host = result.scalar_one_or_none()
    if host is None:
        raise HostNotFoundError()

    if user.id == host.id:
        raise SelfBookingError()

    stmt = (
        select(TimeSlot)
        .where(TimeSlot.id == payload.time_slot_id)
        .where(TimeSlot.calendar_id == host.calendar.id)
    )
    result = await session.execute(stmt)
    time_slot = result.scalar_one_or_none()
    if time_slot is None:
        raise TimeSlotNotFoundError()
    if payload.when.weekday() not in time_slot.weekdays:
        raise TimeSlotNotFoundError()

    if payload.when < date.today():
        raise PastDateBookingError()

    # 중복 예약 체크
    stmt = (
        select(Booking)
        .where(Booking.guest_id == user.id)
        .where(Booking.when == payload.when)
        .where(Booking.time_slot_id == payload.time_slot_id)
    )
    result = await session.execute(stmt)
    existing_booking = result.scalar_one_or_none()
    if existing_booking is not None:
        raise DuplicateBookingError()

    booking = Booking(
        guest_id=user.id,
        when=payload.when,
        topic=payload.topic,
        description=payload.description,
        time_slot_id=payload.time_slot_id,
    )
    session.add(booking)
    await session.commit()
    await session.refresh(booking)
    return booking


