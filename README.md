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

## 참고사항
- 가상환경은 `.venv` 디렉토리에 위치
- Poetry로 패키지 관리
- 가상환경 활성화 시 프롬프트 앞에 `(.venv)` 표시됨