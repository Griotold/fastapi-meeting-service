# 배포 가이드

## 모바일 앱 배포 시 체크리스트

### 1. JWT 쿠키 설정 제거
**위치:** `appserver/apps/account/endpoints.py` - `login()` 함수

**현재 (웹 브라우저용):**
```python
res.set_cookie(
    key="auth_token",
    value=access_token,
    httponly=True,
    secure=True,
    samesite="strict"
)
return res
```

**변경 (모바일 앱용):**
```python
# 쿠키 설정 제거 - 모바일 앱은 토큰을 직접 관리
return JSONResponse(response_data, status_code=status.HTTP_200_OK)
```

**이유:**
- 모바일 앱은 브라우저가 아니므로 쿠키 불필요
- 앱은 SecureStorage에 토큰 저장 후 Authorization 헤더로 전송

### 2. 환경변수 설정
**위치:** `appserver/apps/account/utils.py`

**현재:**
```python
SECRET_KEY = "a4f...b5e8...c1d4...f7a2...b5e8..."
```

**변경:**
```python
SECRET_KEY = os.getenv("SECRET_KEY")
```

**.env 파일 생성:**
```env
SECRET_KEY=your-secret-key-here
ENVIRONMENT=production
```

### 3. HTTPS 강제
- 운영 서버는 반드시 HTTPS 사용
- HTTP는 앱스토어 심사 탈락 가능

## 개발 vs 운영 환경

| 항목 | 개발 (현재) | 운영 (배포 시) |
|------|------------|---------------|
| 쿠키 설정 | O (웹 테스트용) | X (앱용) |
| SECRET_KEY | 하드코딩 | 환경변수 |
| HTTPS | 선택 | 필수 |

## 참고사항
- 현재는 책의 React 웹 클라이언트 기준으로 구현됨
- 모바일 앱 출시 전에 위 체크리스트 필수 확인