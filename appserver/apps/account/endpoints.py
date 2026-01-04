from fastapi import APIRouter, HTTPException, status
from sqlmodel import select, func, update, delete, true
from .models import User
from appserver.db import DbSessionDep
from sqlalchemy.exc import IntegrityError
from .exceptions import DuplicatedUsernameError, DuplicatedEmailError, PasswordMismatchError, UserNotFoundError
from .schemas import SignupPayload, UserOut, LoginPayload
from .utils import hash_password, verify_password

router = APIRouter(prefix="/account")

@router.get("/users/{username}")
async def user_detail(username: str, session: DbSessionDep) -> User:
    stmt = select(User).where(User.username == username)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if user is not None:
        return user
    
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


@router.post("/signup", status_code=status.HTTP_201_CREATED, response_model=UserOut)
async def signup(payload: SignupPayload, session: DbSessionDep) -> User:
    stmt = select(func.count()).select_from(User).where(User.username == payload.username)
    result = await session.execute(stmt)
    count = result.scalar_one()

    if count > 0:
        raise DuplicatedUsernameError()
    
    # SignupPayload → User 변환 시 password를 hashed_password로 변환
    user_data = payload.model_dump(exclude={"password", "password_again"})
    user_data["hashed_password"] = hash_password(payload.password)

    user = User.model_validate(user_data)
    session.add(user)
    try:
        await session.commit()
    except IntegrityError:
        raise DuplicatedEmailError()
    await session.refresh(user)
    return user

@router.post("/login", status_code=status.HTTP_200_OK, response_model=UserOut)
async def login(payload: LoginPayload, session: DbSessionDep) -> User:
    stmt = select(User).where(User.username == payload.username)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise UserNotFoundError()
    
    is_valid = verify_password(payload.password, user.hashed_password)
    if not is_valid:
        raise PasswordMismatchError()
    
    return user
    