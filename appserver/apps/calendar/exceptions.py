# appserver/apps/calendar/exceptions.py
from fastapi import HTTPException, status


class CalendarNotFoundError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calendar not found"
        )


class HostNotFoundError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Host not found"
        )