# FastAPI Meeting Service

## 개발 환경 설정

### 1. Python 버전 확인
```bash
python --version  # Python 3.12 이상 필요
```

### 2. 가상환경 활성화
```bash
source .venv/bin/activate
```

### 3. 의존성 설치
```bash
poetry install
```

### 4. 개발 서버 실행
```bash
fastapi dev appserver/app.py
```

서버 주소:
- API: http://127.0.0.1:8000
- 문서: http://127.0.0.1:8000/docs

### 5. 가상환경 비활성화
```bash
deactivate
```

## 테스트

### 전체 테스트 실행
```bash
poetry run pytest
```

### 상세 출력으로 테스트 실행
```bash
poetry run pytest -v
```

### 특정 파일만 테스트
```bash
poetry run pytest tests/appserver/apps/account/test_login_api.py
```

### 특정 테스트 함수만 실행
```bash
poetry run pytest tests/appserver/apps/account/test_login_api.py::test_로그인_성공
```

### 테스트 커버리지 확인 (선택사항)
```bash
poetry run pytest --cov=appserver --cov-report=html
```

### 테스트 옵션 설명
- `-v`: 상세 출력
- `-s`: print 출력 표시
- `-x`: 첫 실패 시 중단
- `-k EXPRESSION`: 특정 패턴의 테스트만 실행 (예: `-k login`)

## 데이터베이스 마이그레이션 (Alembic)

### 마이그레이션 생성
모델을 수정한 후 마이그레이션 파일 생성:
```bash
alembic revision --autogenerate -m "마이그레이션 설명"
```

### 마이그레이션 적용
```bash
alembic upgrade head
```

### 마이그레이션 되돌리기
```bash
# 한 단계 되돌리기
alembic downgrade -1

# 특정 버전으로 되돌리기
alembic downgrade <revision_id>
```

### 마이그레이션 상태 확인
```bash
# 현재 버전 확인
alembic current

# 마이그레이션 히스토리 확인
alembic history
```

### 초기 설정 (최초 1회만)
```bash
# Alembic 초기화 (이미 완료됨)
alembic init alembic

# 첫 마이그레이션 생성 및 적용 (이미 완료됨)
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

## 개발 워크플로우 (TDD)

1. **테스트 작성** (Red)
   - 실패하는 테스트 먼저 작성

2. **최소 구현** (Green)
   - 테스트를 통과하는 최소한의 코드 작성

3. **리팩토링** (Refactor)
   - 코드 개선 및 최적화

4. **테스트 실행**
```bash
   poetry run pytest
```

## ⚠️ 모바일 앱 배포 시 주의사항

현재 프로젝트는 웹 브라우저 기반으로 구현되어 있습니다.  
모바일 앱으로 배포 시 JWT 쿠키 설정 제거 등의 수정이 필요합니다.

**자세한 내용:** [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) 참고

## DTO 네이밍 관례 (schemas.py)

프로젝트의 일관된 DTO 네이밍 패턴을 따릅니다.

### 요청(Request) DTO

#### 1. `Payload` 접미사
인증 및 사용자 관련 요청에 사용
```python
SignupPayload       # 회원가입 요청
LoginPayload        # 로그인 요청
UpdateUserPayload   # 사용자 정보 수정 요청
```

#### 2. `CreateIn` 접미사
리소스 생성 요청에 사용
```python
CalendarCreateIn    # 캘린더 생성
TimeSlotCreateIn    # 타임슬롯 생성
BookingCreateIn     # 예약 생성
```

#### 3. `UpdateIn` 접미사
리소스 수정 요청에 사용
```python
CalendarUpdateIn       # 캘린더 수정
HostBookingUpdateIn    # 예약 수정 (호스트용)
```

### 응답(Response) DTO

#### 1. `Out` 접미사
기본 응답 스키마
```python
UserOut         # 사용자 기본 정보
CalendarOut     # 캘린더 기본 정보
TimeSlotOut     # 타임슬롯 정보
BookingOut      # 예약 정보
```

#### 2. `DetailOut` 접미사
상세 정보 응답 (기본 정보 + 추가 필드)
```python
UserDetailOut       # 사용자 상세 정보 (email, 생성일, 수정일 포함)
CalendarDetailOut   # 캘린더 상세 정보 (host_id, 생성일, 수정일 포함)
```

#### 3. `Simple` 접두사
간소화된 응답 (필수 필드만 포함)
```python
SimpleBookingOut    # 예약 간소 정보 (날짜, 타임슬롯만)
```

### 네이밍 규칙 요약

| 용도 | 패턴 | 예시 |
|------|------|------|
| 인증/사용자 요청 | `XxxPayload` | `SignupPayload` |
| 생성 요청 | `XxxCreateIn` | `BookingCreateIn` |
| 수정 요청 | `XxxUpdateIn` | `CalendarUpdateIn` |
| 기본 응답 | `XxxOut` | `UserOut` |
| 상세 응답 | `XxxDetailOut` | `UserDetailOut` |
| 간소 응답 | `SimpleXxxOut` | `SimpleBookingOut` |

### 장점
- **명확한 데이터 흐름**: `In`/`Out`으로 요청/응답 구분
- **일관성**: 도메인별로 동일한 패턴 적용
- **확장성**: 새로운 DTO 추가 시 패턴 재사용 가능
- **가독성**: 클래스명만으로 용도 파악 가능

## 참고사항
- 가상환경은 `.venv` 디렉토리에 위치
- Poetry로 패키지 관리
- 가상환경 활성화 시 프롬프트 앞에 `(.venv)` 표시됨
- 개발 DB: SQLite (`local.db`)
- 테스트 설정: `pyproject.toml`의 `[tool.pytest.ini_options]` 참고
- 테스트 경로: `./tests`, `./appserver`