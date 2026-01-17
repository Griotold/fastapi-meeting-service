from fastapi import APIRouter, status
from sqlmodel import select
from appserver.apps.account.models import User
from appserver.apps.calendar.models import Calendar
from appserver.db import DbSessionDep
from appserver.apps.account.deps import CurrentUserOptionalDep
from .exceptions import CalendarNotFoundError, HostNotFoundError
from .schemas import CalendarDetailOut, CalendarOut

async def host_calendar_detail(
        host_username: str, 
        user: CurrentUserOptionalDep,
        session: DbSessionDep
) -> CalendarOut | CalendarDetailOut:
    # username으로 호스트 유저 찾기
    stmt = select(User).where(User.username == host_username)
    result = await session.execute(stmt)
    host = result.scalar_one_or_none()
        
    # 해당 호스트의 캘린더 찾기
    stmt = select(Calendar).where(Calendar.host_id == host.id)
    result = await session.execute(stmt)
    calendar = result.scalar_one_or_none()

    # 권한에 따른 분기 처리
    if user is not None and user.id == host.id:
        return CalendarDetailOut.model_validate(calendar) # 본인 -> 상세 정보
        
    return CalendarOut.model_validate(calendar) # 타인 -> 일반 정보