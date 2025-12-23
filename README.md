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

## 참고사항
- 가상환경은 `.venv` 디렉토리에 위치
- Poetry로 패키지 관리
- 가상환경 활성화 시 프롬프트 앞에 `(.venv)` 표시됨
- 개발 DB: SQLite (`local.db`)