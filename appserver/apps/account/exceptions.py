# exceptions.py에 추가
from fastapi import HTTPException, status

class DuplicatedUsernameError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,  # 오타 수정
            detail="중복된 계정 ID입니다."
        )

class DuplicatedEmailError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="중복된 이메일입니다."
        )

class UserNotFoundError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자가 없습니다."
        )

class PasswordMismatchError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="틀린 비밀번호입니다.",
        )

# headers={"WWW-Authenticate": "Bearer"}의 의미
# 🔐 HTTP 표준 준수 - RFC 7235 (401 시 필수 권장)
# 📱 클라이언트 안내 - "Bearer 토큰으로 인증하세요"
# 🌐 브라우저 호환 - 자동 인증 처리 가능
# 🎯 명확한 의도 - 인증 방식 명시

class InvalidTokenError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 인증 토큰입니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

class ExpiredTokenError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="만료된 인증 토큰입니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )