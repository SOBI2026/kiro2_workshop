# Property-Based Testing (PBT) - 시니어 안심 케어

이 디렉토리는 Hypothesis를 사용한 Property-Based Testing 코드를 포함합니다.

---

## 📚 기준값 레퍼런스 체인

모든 테스트 기준값은 다음 문서 체인에서 유래합니다:

```
1. senior-care-monitoring-presentation.md (원본 소스)
   ↓
2. .kiro/specs/senior-care-monitoring/requirements.md (요구사항)
   ↓
3. .kiro/specs/senior-care-monitoring/design.md (설계 및 Properties)
   ↓
4. tests/property/*.py (테스트 코드)
```

### 주요 기준값 매핑

| 기준값 | 출처 문서 | 섹션 | 테스트 파일 |
|--------|-----------|------|-------------|
| 임계값: 30~480분 | presentation.md | "임계값: 30~480분 (설정 가능)" | test_settings_properties.py |
| 음성 타임아웃: 10~60초 | presentation.md | "응답 대기: 10~60초 (설정 가능)" | test_settings_properties.py |
| 알림 전송: ≤3초 | presentation.md | "푸시 알림 (3초 이내 전송)" | test_notification_properties.py |
| 재시도: 3회, 5분 간격 | presentation.md | "실패 시 5분 간격 최대 3회 재시도" | test_notification_properties.py |
| 보호자: 최대 5명 | presentation.md | "최대 5명의 보호자 동시 알림" | test_notification_properties.py |
| 센서 타입 | design.md | Component Interfaces | test_sensor_data_properties.py |
| 기본 임계값: 120분 | requirements.md | 요구사항 2.4 | test_inactivity_detection_properties.py |
| 기본 타임아웃: 30초 | requirements.md | 요구사항 3.3 | test_settings_properties.py |

---

## 🧪 테스트 파일 구조

```
tests/property/
├── conftest.py                              # Pytest 설정 및 fixtures
├── test_sensor_data_properties.py           # 센서 데이터 처리 (Property 1-9)
├── test_inactivity_detection_properties.py  # 활동 부재 감지 (Property 10-16)
├── test_notification_properties.py          # 보호자 알림 (Property 17-21)
├── test_settings_properties.py              # 설정 관리 (Property 22-25)
└── README.md                                # 이 파일
```

---

## 🎯 Correctness Properties 커버리지

### 센서 데이터 수집 (9개 Properties)

| Property | 설명 | 테스트 파일 | 출처 |
|----------|------|-------------|------|
| Property 1 | 센서 데이터 처리 완전성 | test_sensor_data_properties.py | design.md |
| Property 2 | 센서 값 음수 불가 | test_sensor_data_properties.py | design.md (암묵적) |
| Property 3 | 유효하지 않은 센서 타입 거부 | test_sensor_data_properties.py | design.md |
| Property 4 | 멱등성 | test_sensor_data_properties.py | design.md Property 3 |
| Property 5 | 마지막 활동 시간 업데이트 | test_sensor_data_properties.py | requirements.md 1.4 |
| Property 6 | 필수 필드 검증 | test_sensor_data_properties.py | design.md |
| Property 7 | 디바이스 타입 검증 | test_sensor_data_properties.py | design.md |
| Property 8 | 타임스탬프 형식 검증 | test_sensor_data_properties.py | design.md |
| Property 9 | 센서 값 범위 검증 | test_sensor_data_properties.py | design.md (암묵적) |

### 활동 부재 감지 (7개 Properties)

| Property | 설명 | 테스트 파일 | 출처 |
|----------|------|-------------|------|
| Property 10 | 임계값 기반 감지 정확성 | test_inactivity_detection_properties.py | requirements.md Property 4 |
| Property 11 | 임계값 범위 검증 | test_inactivity_detection_properties.py | requirements.md Property 14 |
| Property 12 | 중복 알림 방지 | test_inactivity_detection_properties.py | requirements.md Property 5 |
| Property 13 | 기본 임계값 적용 | test_inactivity_detection_properties.py | requirements.md 2.4 |
| Property 14 | 전체 사용자 검사 | test_inactivity_detection_properties.py | requirements.md Property 6 |
| Property 15 | 비활성 사용자 제외 | test_inactivity_detection_properties.py | design.md |
| Property 16 | 알림 상태 초기값 | test_inactivity_detection_properties.py | requirements.md 2.5 |

### 보호자 알림 (5개 Properties)

| Property | 설명 | 테스트 파일 | 출처 |
|----------|------|-------------|------|
| Property 17 | 알림 전송 시간 제약 | test_notification_properties.py | requirements.md Property 10 |
| Property 18 | 보호자 수 제한 | test_notification_properties.py | requirements.md Property 16 |
| Property 19 | 재시도 로직 정확성 | test_notification_properties.py | requirements.md Property 12 |
| Property 20 | 알림 메시지 완전성 | test_notification_properties.py | requirements.md Property 13 |
| Property 21 | 모든 보호자에게 알림 | test_notification_properties.py | requirements.md Property 11 |

### 설정 관리 (4개 Properties)

| Property | 설명 | 테스트 파일 | 출처 |
|----------|------|-------------|------|
| Property 22 | 임계값 범위 검증 | test_settings_properties.py | requirements.md Property 14 |
| Property 23 | 음성 타임아웃 범위 검증 | test_settings_properties.py | requirements.md Property 14 |
| Property 24 | 설정 업데이트 원자성 | test_settings_properties.py | design.md |
| Property 25 | 기본 설정 값 | test_settings_properties.py | requirements.md 2.4, 3.3 |

**총 25개 Properties 테스트 (design.md의 47개 중 핵심 25개)**

---

## 🚀 테스트 실행 방법

### 1. 의존성 설치

```bash
pip install -r requirements-test.txt
```

### 2. 전체 Property 테스트 실행

```bash
# 기본 프로필 (100 examples)
pytest tests/property/ -v

# 통계 표시
pytest tests/property/ -v --hypothesis-show-statistics

# 상세 출력 (dev 프로필, 20 examples)
HYPOTHESIS_PROFILE=dev pytest tests/property/ -v

# CI 환경 (50 examples, 5초 deadline)
HYPOTHESIS_PROFILE=ci pytest tests/property/ -v

# 철저한 테스트 (1000 examples)
HYPOTHESIS_PROFILE=thorough pytest tests/property/ -v
```

### 3. 특정 파일만 실행

```bash
# 센서 데이터 Properties만
pytest tests/property/test_sensor_data_properties.py -v

# 활동 부재 감지 Properties만
pytest tests/property/test_inactivity_detection_properties.py -v

# 알림 Properties만
pytest tests/property/test_notification_properties.py -v

# 설정 Properties만
pytest tests/property/test_settings_properties.py -v
```

### 4. 특정 Property만 실행

```bash
# Property 1만 실행
pytest tests/property/test_sensor_data_properties.py::test_property_1_sensor_data_completeness -v

# Property 10만 실행
pytest tests/property/test_inactivity_detection_properties.py::test_property_10_threshold_based_detection -v
```

### 5. 커버리지 측정

```bash
pytest tests/property/ --cov=src --cov-report=html --cov-report=term
```

---

## 📊 Hypothesis 프로필 설명

| 프로필 | Examples | Deadline | 용도 |
|--------|----------|----------|------|
| default | 100 | None | 일반 개발 및 테스트 |
| ci | 50 | 5000ms | CI/CD 파이프라인 (빠른 피드백) |
| dev | 20 | None | 로컬 개발 (빠른 반복) |
| thorough | 1000 | None | 릴리스 전 철저한 검증 |

---

## 🔍 Property 테스트 작성 가이드

### 1. 테스트 구조

```python
# Feature: senior-care-monitoring, Property X: 속성 이름
@given(
    param1=st.strategy1(),
    param2=st.strategy2()
)
@settings(max_examples=100, deadline=None)
def test_property_X_description(param1, param2):
    """
    Property X: 속성 이름
    
    For all ... (formal property statement)
    
    시나리오:
    - 입력: ...
    - 기대: ...
    - 검증: ...
    
    기준값 출처: [문서명] [섹션]
    """
    # Arrange
    ...
    
    # Act
    ...
    
    # Assert
    ...
```

### 2. 주석 규칙

모든 Property 테스트는 다음 정보를 포함해야 합니다:

1. **Feature 태그**: `# Feature: senior-care-monitoring, Property X`
2. **Formal statement**: `For all ... SHALL ...` 형식
3. **시나리오**: 구체적인 입력/기대/검증
4. **기준값 출처**: 어느 문서의 어느 섹션에서 왔는지

### 3. Hypothesis Strategies

```python
# 텍스트
st.text(min_size=5, max_size=50)

# 정수 (범위 지정)
st.integers(min_value=30, max_value=480)

# 실수 (NaN, Infinity 제외)
st.floats(min_value=0.0, max_value=1000.0, allow_nan=False, allow_infinity=False)

# 선택 (enum)
st.sampled_from(['mobile', 'iot'])

# 날짜/시간
st.datetimes(min_value=datetime(2020, 1, 1), max_value=datetime(2030, 12, 31))

# 조합
st.one_of(st.integers(min_value=0, max_value=29), st.integers(min_value=481, max_value=1000))
```

---

## ⚠️ 주의사항

### 1. AWS 서비스 모킹

- 실제 AWS 서비스 대신 `moto` 라이브러리 사용
- DynamoDB, Lambda, SNS, SQS 모킹 지원
- RDS는 SQLite 인메모리 DB로 대체

### 2. 테스트 격리

- 각 테스트는 독립적으로 실행
- `conftest.py`의 fixtures로 환경 초기화
- 테스트 간 데이터 공유 없음

### 3. 성능 고려

- Property 테스트는 많은 반복 실행 (100~1000회)
- CI 환경에서는 `ci` 프로필 사용 (50 examples)
- 로컬 개발 시 `dev` 프로필 사용 (20 examples)

### 4. 실패 시 디버깅

```bash
# 실패한 케이스 재현
pytest tests/property/ -v --hypothesis-seed=12345

# 상세 로그 출력
pytest tests/property/ -v -s

# 특정 Property만 디버깅
pytest tests/property/test_sensor_data_properties.py::test_property_1_sensor_data_completeness -v -s
```

---

## 📖 참고 자료

### Hypothesis 문서
- [Hypothesis 공식 문서](https://hypothesis.readthedocs.io/)
- [Strategies 가이드](https://hypothesis.readthedocs.io/en/latest/data.html)
- [Settings 설정](https://hypothesis.readthedocs.io/en/latest/settings.html)

### Property-Based Testing 개념
- [Property-Based Testing이란?](https://hypothesis.works/articles/what-is-property-based-testing/)
- [좋은 Property 작성법](https://hypothesis.works/articles/how-to-use-hypothesis-effectively/)

### 프로젝트 문서
- `senior-care-monitoring-presentation.md` - 원본 요구사항
- `.kiro/specs/senior-care-monitoring/requirements.md` - 상세 요구사항
- `.kiro/specs/senior-care-monitoring/design.md` - 기술 설계 및 47개 Properties
- `docs/SCENARIO_EXAMPLES.md` - 가상 시나리오 예시

---

## 🎯 다음 단계

1. **추가 Properties 구현**: 나머지 22개 Properties 테스트 작성
2. **통합 테스트**: 여러 컴포넌트 간 상호작용 테스트
3. **성능 테스트**: 부하 테스트 및 스트레스 테스트
4. **CI/CD 통합**: GitHub Actions 또는 AWS CodePipeline에 통합

---

이 테스트들은 시스템의 correctness를 보장하는 핵심 검증 도구입니다!
