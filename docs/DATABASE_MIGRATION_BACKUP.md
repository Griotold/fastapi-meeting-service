# 데이터베이스 마이그레이션 & 백업 전략 가이드

## 📚 목차

1. [Enum 사용법](#1-enum-사용법)
2. [데이터베이스 마이그레이션 (Alembic)](#2-데이터베이스-마이그레이션-alembic)
3. [백업 전략](#3-백업-전략)
4. [프로덕션 환경 (AWS RDS)](#4-프로덕션-환경-aws-rds)
5. [실무 베스트 프랙티스](#5-실무-베스트-프랙티스)

---

## 1. Enum 사용법

### 1.1 Python Enum 기본

FastAPI와 SQLModel에서 Enum을 사용하면 타입 안정성과 가독성을 높일 수 있습니다.

#### StrEnum 정의

```python
# appserver/apps/calendar/enums.py
import enum

class AttendanceStatus(enum.StrEnum):
    """참석 상태 종류
    SCHEDULED: 예정
    ATTENDED: 출석
    NO_SHOW: 결석
    CANCELLED: 취소
    SAME_DAY_CANCEL: 당일 취소
    LATE: 지각
    """
    SCHEDULED = enum.auto()
    ATTENDED = enum.auto()
    NO_SHOW = enum.auto()
    CANCELLED = enum.auto()
    SAME_DAY_CANCEL = enum.auto()
    LATE = enum.auto()
```

#### 모델에서 사용

```python
# appserver/apps/calendar/models.py
from sqlalchemy import String
from sqlmodel import SQLModel, Field
from .enums import AttendanceStatus

class Booking(SQLModel, table=True):
    __tablename__ = "bookings"

    id: int = Field(default=None, primary_key=True)
    attendance_status: AttendanceStatus = Field(
        default=AttendanceStatus.SCHEDULED,
        description="참석 상태 종류",
        sa_type=String(50),  # VARCHAR(50)로 저장
    )
```

### 1.2 데이터베이스 저장 방식

#### 방법 1: String 타입 (유연함, 권장) ⭐

```python
attendance_status: AttendanceStatus = Field(
    sa_type=String(50),  # VARCHAR(50)로 저장
    default=AttendanceStatus.SCHEDULED,
)
```

**장점:**
- ✅ Enum 값 추가 시 마이그레이션 불필요 (코드만 수정)
- ✅ 유연한 확장성
- ✅ FastAPI Pydantic 검증으로 충분히 안전

**단점:**
- ⚠️ DB 레벨에서는 검증 안 함 (직접 SQL 입력 시)

#### 방법 2: SQLAlchemy Enum 타입 (엄격함)

```python
from sqlalchemy import Enum as SQLEnum

attendance_status: AttendanceStatus = Field(
    sa_type=SQLEnum(AttendanceStatus, native_enum=True),
    default=AttendanceStatus.SCHEDULED,
)
```

**장점:**
- ✅ DB 레벨에서 값 검증
- ✅ PostgreSQL ENUM 타입 사용 (타입 안전성)

**단점:**
- ❌ Enum 값 추가/삭제 시 마이그레이션 필수
- ❌ ALTER TYPE 명령 필요 (복잡)

### 1.3 비교표

| 방법 | FastAPI 검증 | DB 검증 | Enum 값 추가 시 | 권장 |
|------|-------------|---------|----------------|------|
| **String(50)** | ✅ | ❌ | 코드만 수정 | ⭐ 개발/유연성 중시 |
| **SQLEnum** | ✅ | ✅ | 마이그레이션 필요 | 프로덕션/엄격함 중시 |
| **String + CHECK** | ✅ | ✅ | 제약 조건 수정 | 균형잡힌 선택 |

---

## 2. 데이터베이스 마이그레이션 (Alembic)

### 2.1 마이그레이션 생성

```bash
# 모델 변경 후 마이그레이션 파일 자동 생성
alembic revision --autogenerate -m "Add attendance_status to bookings"
```

**생성되는 파일:** `alembic/versions/xxxxx_add_attendance_status_to_bookings.py`

### 2.2 마이그레이션 스크립트 검토 및 수정

⚠️ **중요:** 자동 생성된 마이그레이션은 반드시 검토하고 필요시 수정해야 합니다!

#### 문제 예시: default 값 누락

**자동 생성 (문제):**
```python
def upgrade() -> None:
    # nullable=False인데 server_default가 없음!
    op.add_column('bookings',
        sa.Column('attendance_status', sa.String(length=50), nullable=False)
    )
```

**수정 후 (안전):**
```python
def upgrade() -> None:
    # server_default 추가하여 기존 데이터 보호
    op.add_column('bookings',
        sa.Column('attendance_status', sa.String(length=50),
                  nullable=False,
                  server_default='SCHEDULED')  # 👈 추가!
    )
```

### 2.3 마이그레이션 작동 방식

**기존 데이터 보존 원칙:**

```
마이그레이션 전 (bookings 테이블):
┌────┬────────┬─────────────┬────────────┐
│ id │ topic  │ description │ when       │
├────┼────────┼─────────────┼────────────┤
│ 1  │ Python │ 파이썬 학습 │ 2024-01-10 │
│ 2  │ FastAPI│ API 개발    │ 2024-01-15 │
└────┴────────┴─────────────┴────────────┘

마이그레이션 후:
┌────┬────────┬─────────────┬────────────┬───────────────────┐
│ id │ topic  │ description │ when       │ attendance_status │
├────┼────────┼─────────────┼────────────┼───────────────────┤
│ 1  │ Python │ 파이썬 학습 │ 2024-01-10 │ SCHEDULED        │ ← default 값
│ 2  │ FastAPI│ API 개발    │ 2024-01-15 │ SCHEDULED        │ ← default 값
└────┴────────┴─────────────┴────────────┴───────────────────┘
```

✅ **기존 데이터 유지** + **새 컬럼 추가** + **default 값으로 채워짐**

### 2.4 마이그레이션 명령어

```bash
# 현재 버전 확인
alembic current

# 마이그레이션 히스토리 확인
alembic history --verbose

# 마이그레이션 적용
alembic upgrade head

# 한 단계 롤백
alembic downgrade -1

# 특정 버전으로 롤백
alembic downgrade <revision_id>
```

---

## 3. 백업 전략

### 3.1 SQLite (개발 환경)

SQLite는 **파일 기반** 데이터베이스로 백업이 매우 간단합니다.

#### 백업 방법

```bash
# 방법 1: 파일 복사 (가장 간단)
cp local.db local.db.backup.$(date +%Y%m%d_%H%M%S)

# 방법 2: sqlite3 명령어 (더 안전)
sqlite3 local.db ".backup local.db.backup"

# 방법 3: SQL 덤프
sqlite3 local.db .dump > local.db.sql
```

#### 복구 방법

```bash
# 백업 파일로 복구
cp local.db.backup local.db

# SQL 덤프로 복구
sqlite3 local.db < local.db.sql
```

#### 마이그레이션 워크플로우

```bash
# 1. 백업 (옵션, 데이터가 중요하면)
cp local.db local.db.backup

# 2. 마이그레이션 적용
alembic upgrade head

# 3. 문제 발생 시 복구
cp local.db.backup local.db
# 또는
alembic downgrade -1
```

### 3.2 PostgreSQL (프로덕션 환경)

PostgreSQL은 **서버 기반** 데이터베이스로 전용 백업 도구를 사용합니다.

#### pg_dump (논리적 백업) ⭐ 가장 많이 사용

**개념:**
- 데이터베이스를 SQL 명령어로 변환
- 텍스트 기반 (사람이 읽을 수 있음)
- 버전 간 호환성 좋음

**백업:**
```bash
# SQL 텍스트 파일
pg_dump -U username -d database_name > backup.sql

# 압축된 커스텀 포맷 (권장)
pg_dump -U username -d database_name -F c -f backup.dump

# 특정 테이블만 백업
pg_dump -U username -d database_name -t bookings > bookings_backup.sql
```

**복구:**
```bash
# SQL 파일로 복구
psql -U username -d database_name < backup.sql

# 커스텀 포맷 복구
pg_restore -U username -d database_name backup.dump
```

#### pg_basebackup (물리적 백업)

**개념:**
- PostgreSQL 데이터 디렉토리 전체를 복사
- 바이너리 형식
- 대용량 데이터베이스에 적합

**백업:**
```bash
pg_basebackup -U username \
  -D /backup/directory \
  -F tar \
  -z \
  -P
```

#### 비교표

| 구분 | pg_dump | pg_basebackup |
|------|---------|---------------|
| **형식** | SQL 텍스트 | 바이너리 |
| **사람이 읽기** | ✅ 가능 | ❌ 불가능 |
| **백업 속도** | 느림 | 빠름 |
| **복구 속도** | 느림 | 빠름 |
| **특정 테이블만** | ✅ 가능 | ❌ 불가능 |
| **버전 호환성** | ✅ 좋음 | ⚠️ 같은 버전만 |
| **일반적 용도** | 일반 백업 | 대용량 DB, 재해 복구 |

---

## 4. 프로덕션 환경 (AWS RDS)

### 4.1 AWS RDS 백업 기능

AWS RDS는 **자동 백업 기능**이 매우 잘 되어 있습니다.

#### 자동 백업 (Automated Backups) ⭐

**기본 제공:**
- ✅ 매일 자동 전체 스냅샷
- ✅ 트랜잭션 로그 연속 백업 (5분마다)
- ✅ Point-in-Time Recovery (PITR)

**설정:**
```yaml
백업 보관 기간: 7일 (기본) ~ 35일 (최대)
백업 시간: 서비스 부담 적은 시간 (예: 03:00-04:00 UTC)
PITR: 활성화 (권장)
```

**복구 가능 범위:**
- 최근 5분 전 ~ 보관 기간 내 **어느 시점으로든** 복구 가능
- 예: "어제 오후 3시 15분 30초" 상태로 복구 가능!

#### 수동 스냅샷 (Manual Snapshots)

**용도:**
- 마이그레이션 전 백업
- 중요 배포 전 백업
- 장기 보관 (무기한 가능)

**생성:**
```bash
# AWS CLI
aws rds create-db-snapshot \
  --db-instance-identifier puddingcamp-prod \
  --db-snapshot-identifier before-migration-20260218

# 또는 AWS 콘솔에서 클릭
```

**보관 기간:**
- ✅ **무기한 보관 가능** (삭제할 때까지)
- ✅ 1년, 2년, 그 이상도 가능
- ⚠️ 스토리지 비용 발생 (약 $0.095/GB/월)

#### Point-in-Time Recovery (PITR)

**강력한 복구 기능:**

```
시나리오: 2026-02-18 15:30에 실수로 중요 데이터 삭제

복구 절차:
1. AWS 콘솔 → "Restore to point in time"
2. 시간 지정: 2026-02-18 15:25 (삭제 5분 전)
3. 새 RDS 인스턴스로 복구
4. 확인 후 전환
```

### 4.2 백업 비용

```yaml
자동 백업:
  - DB 크기만큼 무료
  - 예: DB 100GB → 자동 백업 100GB까지 무료
  - 초과분: $0.095/GB/월

수동 스냅샷:
  - 모든 스토리지 유료
  - $0.095/GB/월

예시:
  DB: 100GB
  수동 스냅샷 3개 (각 100GB): 300GB
  비용: 300GB × $0.095 = $28.5/월 (약 38,000원/월)
```

### 4.3 장기 보관 전략

#### 전략 1: 주요 마일스톤만 보관 (권장)

```yaml
단기 (1-3개월):
  - 매주 배포 전 스냅샷
  - 주요 마이그레이션 전
  - 3개월 후 삭제

중기 (6개월-1년):
  - 월말 스냅샷
  - 분기별 중요 배포
  - 1년 후 삭제

장기 (1년 이상):
  - 연말 스냅샷
  - 주요 버전 릴리스
  - 법적 요구사항
```

#### 전략 2: S3로 Export (비용 절감)

```yaml
비용 비교:
  - RDS 스냅샷: $0.095/GB/월
  - S3 Standard: $0.025/GB/월 (약 4배 저렴!)
  - S3 Glacier: $0.004/GB/월 (약 24배 저렴!)

장기 보관:
  1. RDS 수동 스냅샷 생성
  2. S3로 Export
  3. RDS 스냅샷 삭제
  4. S3에서 장기 보관
```

### 4.4 DDL 스크립트 관리

⚠️ **중요:** AWS RDS는 **DDL 스크립트를 자동으로 관리하지 않습니다!**

**개발자가 관리해야 할 것:**
```
✅ Alembic 마이그레이션 스크립트 → Git으로 버전 관리
✅ models.py 등 스키마 정의 → Git으로 버전 관리
✅ 마이그레이션 실행 타이밍 → 수동 또는 CI/CD
✅ 마이그레이션 전 수동 스냅샷 생성 → AWS CLI/콘솔
```

**AWS RDS가 해주는 것:**
```
✅ 데이터 자동 백업
✅ Point-in-Time Recovery
✅ 수동 스냅샷 저장
✅ 모니터링 및 알림
```

---

## 5. 실무 베스트 프랙티스

### 5.1 3단계 백업 전략

```yaml
레벨 1 - 자동 백업 (AWS RDS):
  - 용도: 일상적인 복구
  - 보관: 7일
  - 관리: 자동

레벨 2 - 수동 스냅샷 (AWS RDS):
  - 용도: 마이그레이션/배포 전
  - 보관: 1-3개월
  - 관리: 수동

레벨 3 - Git (코드/스키마):
  - 용도: 완전한 재구성
  - 보관: 영구
  - 관리: Git
```

### 5.2 마이그레이션 체크리스트

#### 개발 환경

```bash
# 1. 모델 수정
# appserver/apps/calendar/models.py 수정

# 2. 마이그레이션 생성
alembic revision --autogenerate -m "Add attendance_status"

# 3. 마이그레이션 스크립트 검토 및 수정
# alembic/versions/xxxxx.py 확인

# 4. Git 커밋
git add alembic/versions/xxxxx.py appserver/apps/calendar/models.py
git commit -m "Add attendance_status to bookings"

# 5. 로컬 테스트
alembic upgrade head
pytest

# 6. Push
git push origin main
```

#### 프로덕션 환경 (AWS RDS)

```bash
# 1. 수동 스냅샷 생성 (필수!)
aws rds create-db-snapshot \
  --db-instance-identifier puddingcamp-prod \
  --db-snapshot-identifier before-migration-$(date +%Y%m%d)

# 2. 스냅샷 완료 대기
aws rds wait db-snapshot-completed \
  --db-snapshot-identifier before-migration-$(date +%Y%m%d)

# 3. 코드 배포
git pull origin main

# 4. 마이그레이션 적용
alembic upgrade head

# 5. 애플리케이션 재시작
systemctl restart fastapi-app

# 6. 모니터링 및 확인
# - 애플리케이션 로그 확인
# - DB 스키마 확인
# - 기능 테스트

# 7. 문제 발생 시
# 방법 1: Alembic 롤백
alembic downgrade -1

# 방법 2: RDS 스냅샷 복구 (심각한 경우)
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier puddingcamp-prod-restore \
  --db-snapshot-identifier before-migration-$(date +%Y%m%d)
```

### 5.3 환경별 설정

```python
# appserver/config.py
import os

class Config:
    """환경별 데이터베이스 설정"""

    # 개발 환경
    if os.getenv("ENV") == "development":
        DATABASE_URL = "sqlite:///./local.db"

    # 스테이징 환경
    elif os.getenv("ENV") == "staging":
        DATABASE_URL = os.getenv("STAGING_DATABASE_URL")
        # postgresql://user:pass@staging-rds.amazonaws.com/puddingcamp

    # 프로덕션 환경
    else:
        DATABASE_URL = os.getenv("DATABASE_URL")
        # postgresql://user:pass@prod-rds.amazonaws.com/puddingcamp
```

### 5.4 스냅샷 관리 자동화 (Lambda)

```python
# AWS Lambda 예시 (의사 코드)
import boto3
from datetime import datetime, timedelta

rds = boto3.client('rds')

def cleanup_old_snapshots(event, context):
    """오래된 스냅샷 자동 삭제"""

    snapshots = rds.describe_db_snapshots(
        DBInstanceIdentifier='puddingcamp-prod',
        SnapshotType='manual'
    )['DBSnapshots']

    for snapshot in snapshots:
        snapshot_date = snapshot['SnapshotCreateTime']
        snapshot_id = snapshot['DBSnapshotIdentifier']
        age = datetime.now() - snapshot_date

        # 정책별 삭제
        if 'weekly' in snapshot_id and age > timedelta(days=30):
            rds.delete_db_snapshot(DBSnapshotIdentifier=snapshot_id)

        elif 'monthly' in snapshot_id and age > timedelta(days=180):
            rds.delete_db_snapshot(DBSnapshotIdentifier=snapshot_id)

        # 연간 스냅샷은 유지 또는 S3로 Export
```

### 5.5 배포 파이프라인 예시

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Create RDS Snapshot
      run: |
        aws rds create-db-snapshot \
          --db-instance-identifier ${{ secrets.RDS_INSTANCE }} \
          --db-snapshot-identifier pre-deploy-$(date +%Y%m%d-%H%M%S)

    - name: Wait for Snapshot
      run: |
        aws rds wait db-snapshot-completed \
          --db-snapshot-identifier pre-deploy-$(date +%Y%m%d-%H%M%S)

    - name: Deploy Application
      run: |
        # 배포 스크립트 실행
        ./deploy.sh

    - name: Run Migrations
      run: |
        alembic upgrade head

    - name: Health Check
      run: |
        curl -f https://api.puddingcamp.com/health || exit 1
```

---

## 📝 요약

### 핵심 원칙

1. **마이그레이션 전 항상 백업**
   - 개발: 선택 (데이터 중요하면)
   - 프로덕션: 필수!

2. **자동 생성된 마이그레이션 스크립트 검토**
   - `server_default` 확인
   - 데이터 마이그레이션 로직 확인

3. **3단계 백업 전략**
   - 자동 백업 (일상)
   - 수동 스냅샷 (중요 시점)
   - Git (코드/스키마)

4. **테스트 환경에서 먼저 실행**
   - 로컬 → 스테이징 → 프로덕션

### 환경별 권장사항

| 환경 | 데이터베이스 | 백업 방법 | 보관 기간 |
|------|------------|----------|----------|
| **개발** | SQLite | 파일 복사 | 필요시 |
| **스테이징** | PostgreSQL | pg_dump | 7일 |
| **프로덕션** | AWS RDS | 자동 백업 + 수동 스냅샷 | 자동: 7일<br>수동: 정책별 |

---

## 📚 참고 자료

- [Alembic 공식 문서](https://alembic.sqlalchemy.org/)
- [AWS RDS 백업 및 복원](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_CommonTasks.BackupRestore.html)
- [PostgreSQL 백업 가이드](https://www.postgresql.org/docs/current/backup.html)
- [SQLModel 공식 문서](https://sqlmodel.tiangolo.com/)
