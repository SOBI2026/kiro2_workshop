# 시니어 안심 케어 애플리케이션
## 독거 노인 안전 모니터링 시스템

---

## 📋 목차
1. 서비스 개요
2. 핵심 기능
3. 시스템 아키텍처
4. AWS 인프라 구성
5. 기술 스택
6. 비즈니스 가치

---

## 1️⃣ 서비스 개요

### 문제 정의
- 독거 노인 응급 상황 대응 지연
- 일상적 안녕 상태 파악의 어려움
- 보호자의 지속적 모니터링 부담

### 솔루션
**스마트 센서 기반 자동 모니터링 시스템**
- 휴대폰 센서 + IoT 기기 + AI 스피커 연동
- 실시간 활동 감지 및 응급 알림
- 보호자에게 즉각적인 알림 전송

### 타겟 사용자
- Senior User: 65세 이상 독거 노인
- Guardian: 자녀 및 보호자

---

## 2️⃣ 핵심 기능

### 🔍 활동 감지 (Activity Detection)
```
휴대폰 가속도센서 (1초 간격)
        ↓
IoT 기기 상태 (5분 간격)
        ↓
생체 반응 데이터 통합
```

### ⏰ 활동 부재 감지 (Inactivity Detection)
- 임계값: 30~480분 (설정 가능)
- 활동 신호 없음 → AI 스피커 질문 발동

### 🎤 AI 스피커 확인 (Voice Confirmation)
- 질문: "안녕하세요, 괜찮으신가요?"
- 응답 대기: 10~60초 (설정 가능)
- 응답 있음 → 정상 상태 유지
- 응답 없음 → 보호자 긴급 알림

### 📲 보호자 알림 (Guardian Notification)
- 푸시 알림 (3초 이내 전송)
- 마지막 활동 시간 포함
- 최대 5명의 보호자 동시 알림
- 실패 시 5분 간격 최대 3회 재시도

### 📊 활동 이력 및 리포팅
- 30일 활동 데이터 저장
- 일일 활동 요약 생성
- 월간 PDF 리포트 다운로드
- 활동 패턴 시각화

---

## 3️⃣ 시스템 아키텍처

### 전체 시스템 흐름

```
┌─────────────────────────────────────────────────────────────┐
│                    Senior User (노인)                        │
│  ┌──────────────┐         ┌──────────────┐                  │
│  │ Mobile Phone │         │  IoT Devices │                  │
│  │ (Sensor)     │         │  (Smart Home)│                  │
│  └──────┬───────┘         └──────┬───────┘                  │
└─────────┼──────────────────────────┼──────────────────────────┘
          │                          │
          └──────────────┬───────────┘
                         │
                    [Data Collection]
                         │
          ┌──────────────▼───────────────┐
          │   AWS Cloud Platform         │
          │  ┌────────────────────────┐  │
          │  │  API Gateway           │  │
          │  │  (REST/WebSocket)      │  │
          │  └────────────┬───────────┘  │
          │               │              │
          │  ┌────────────▼───────────┐  │
          │  │  Lambda Functions      │  │
          │  │  (Data Processing)     │  │
          │  └────────────┬───────────┘  │
          │               │              │
          │  ┌────────────▼───────────┐  │
          │  │  DynamoDB / RDS        │  │
          │  │  (Data Storage)        │  │
          │  └────────────┬───────────┘  │
          │               │              │
          │  ┌────────────▼───────────┐  │
          │  │  SNS / SQS             │  │
          │  │  (Notification Queue)  │  │
          │  └────────────┬───────────┘  │
          │               │              │
          └───────────────┼──────────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
    [Guardian App]  [AI Speaker]   [Analytics]
          │               │               │
    ┌─────▼─────┐   ┌─────▼─────┐   ┌────▼────┐
    │ Push Notif│   │ Voice API  │   │ Reports │
    └───────────┘   └────────────┘   └─────────┘
```

---

## 4️⃣ AWS 인프라 구성

### 📡 데이터 수집 계층 (Ingestion Layer)

#### API Gateway
- **역할**: 모바일 앱, IoT 기기, AI 스피커의 진입점
- **기능**:
  - REST API 엔드포인트 제공
  - 요청 인증 및 검증
  - 요청 속도 제한 (Rate Limiting)
  - CORS 설정

#### IoT Core (선택사항)
- **역할**: IoT 기기 연결 관리
- **기능**:
  - MQTT 프로토콜 지원
  - 기기 인증서 관리
  - 메시지 라우팅

### ⚙️ 처리 계층 (Processing Layer)

#### Lambda Functions
```
1. SensorDataProcessor
   - 휴대폰 센서 데이터 처리
   - 활동 임계값 판단
   - 마지막 활동 시간 업데이트

2. InactivityDetector
   - 활동 부재 감지 (CloudWatch Events 트리거)
   - AI 스피커 호출 결정
   - 타임아웃 관리

3. VoiceResponseHandler
   - AI 스피커 응답 처리
   - 응답 인식 및 검증
   - 상태 업데이트

4. NotificationManager
   - 보호자 알림 생성
   - SNS를 통한 푸시 알림 전송
   - 재시도 로직 처리

5. ReportGenerator
   - 활동 이력 조회
   - 일일/월간 리포트 생성
   - PDF 생성 및 저장
```

#### EventBridge (CloudWatch Events)
- **역할**: 스케줄 기반 이벤트 트리거
- **사용**:
  - 주기적 활동 부재 감지 (매 1분)
  - 응답 타임아웃 체크
  - 일일 리포트 생성 스케줄

### 💾 데이터 저장 계층 (Storage Layer)

#### DynamoDB (실시간 데이터)
```
테이블 1: SensorData
- PK: UserId + Timestamp
- 속성: AccelerometerValue, LastActivityTime, Status
- TTL: 30일

테이블 2: UserSettings
- PK: UserId
- 속성: InactivityTimeout, ResponseTimeout, Guardians
- 글로벌 보조 인덱스: GuardianId

테이블 3: AlertHistory
- PK: UserId + AlertId
- 속성: AlertTime, Status, GuardianResponses
- TTL: 90일
```

#### RDS (PostgreSQL) - 구조화된 데이터
```
테이블: Users
- user_id (PK)
- name, age, phone
- created_at, updated_at

테이블: Guardians
- guardian_id (PK)
- user_id (FK)
- name, phone, email
- permission_level

테이블: ActivityLog
- log_id (PK)
- user_id (FK)
- activity_type, timestamp
- device_type (mobile/iot)
```

#### S3 (장기 저장소)
- **용도**: 월간 리포트 PDF, 활동 데이터 백업
- **구조**:
  ```
  s3://senior-care-reports/
  ├── {year}/{month}/{user_id}/
  │   ├── report.pdf
  │   └── data_backup.json
  ```

### 🔔 메시징 계층 (Messaging Layer)

#### SNS (Simple Notification Service)
- **역할**: 보호자 푸시 알림 전송
- **토픽**:
  - `AlertNotification`: 긴급 알림
  - `DailyReport`: 일일 리포트
  - `SystemAlert`: 시스템 알림

#### SQS (Simple Queue Service)
- **역할**: 비동기 작업 큐
- **큐**:
  - `NotificationQueue`: 알림 전송 대기
  - `ReportQueue`: 리포트 생성 대기
  - `DeadLetterQueue`: 실패한 메시지

### 🔐 보안 계층 (Security Layer)

#### IAM (Identity & Access Management)
- Lambda 실행 역할 정의
- 최소 권한 원칙 적용
- 리소스별 접근 제어

#### Secrets Manager
- 데이터베이스 자격증명 관리
- API 키 관리
- 자동 로테이션

#### KMS (Key Management Service)
- 데이터 암호화 키 관리
- DynamoDB, RDS 암호화
- S3 객체 암호화

### 📊 모니터링 및 로깅 계층

#### CloudWatch
- **로그**: Lambda, API Gateway 로그 수집
- **메트릭**: 
  - API 응답 시간
  - Lambda 실행 시간
  - 오류율
  - 알림 전송 성공률
- **대시보드**: 실시간 시스템 상태 모니터링

#### X-Ray
- 분산 추적 (Distributed Tracing)
- 성능 병목 지점 식별
- 요청 흐름 시각화

---

## 5️⃣ 기술 스택

### 백엔드
| 계층 | 기술 | 용도 |
|------|------|------|
| API | API Gateway | REST 엔드포인트 |
| 처리 | Lambda (Python/Node.js) | 비즈니스 로직 |
| 데이터 | DynamoDB + RDS | 데이터 저장 |
| 메시징 | SNS/SQS | 비동기 처리 |
| 저장소 | S3 | 파일 저장 |

### 모바일 앱
- **iOS**: Swift + AWS SDK
- **Android**: Kotlin + AWS SDK
- **기능**: 센서 데이터 수집, 알림 수신, 설정 관리

### AI 스피커 연동
- **Alexa Skills Kit**: Amazon Alexa 통합
- **Google Assistant**: Google Actions 통합
- **Naver Clova**: Clova Skills Kit 통합

### 프론트엔드 (보호자 대시보드)
- **Framework**: React.js / Vue.js
- **호스팅**: CloudFront + S3
- **기능**: 실시간 모니터링, 리포트 조회, 설정 관리

---

## 6️⃣ 비즈니스 가치

### 📈 주요 지표
| 지표 | 목표 | 효과 |
|------|------|------|
| 응급 대응 시간 | 3초 이내 | 생명 구조 확률 증대 |
| 시스템 가용성 | 99.5% | 지속적 모니터링 |
| 사용자 만족도 | 90% 이상 | 신뢰도 향상 |
| 오탐지율 | 5% 이하 | 보호자 신뢰 유지 |

### 💰 비용 효율성
- **초기 투자**: AWS 인프라 구축
- **운영 비용**: 사용량 기반 과금 (Pay-as-you-go)
- **확장성**: 사용자 증가에 따른 자동 스케일링

### 🎯 경쟁 우위
1. **실시간 모니터링**: 다중 센서 기반 정확한 감지
2. **사용자 친화적**: 65세 이상 고려한 UI/UX
3. **신뢰성**: 99.5% 가용성 보장
4. **확장성**: 최대 10,000명 동시 지원
5. **보안**: 의료법 및 개인정보보호법 준수

---

## 📊 배포 로드맵

### Phase 1 (3개월)
- ✅ 핵심 기능 개발 (센서 수집, 활동 감지)
- ✅ AWS 인프라 구축
- ✅ 보호자 알림 시스템 구현

### Phase 2 (3개월)
- 🔄 AI 스피커 연동 (Alexa, Google Assistant)
- 🔄 활동 이력 및 리포팅 기능
- 🔄 보호자 대시보드 개발

### Phase 3 (3개월)
- 📅 다중 보호자 지원 고도화
- 📅 머신러닝 기반 이상 탐지
- 📅 모바일 앱 최적화

---

## 🎓 결론

**시니어 안심 케어 애플리케이션**은 AWS 클라우드 기반의 확장 가능하고 신뢰할 수 있는 솔루션으로, 독거 노인의 안전을 보장하고 보호자의 부담을 경감시킵니다.

### 핵심 가치
✨ **안전**: 실시간 모니터링으로 응급 상황 신속 대응
✨ **편의**: 복잡한 조작 없이 음성으로 간단 확인
✨ **신뢰**: 99.5% 가용성으로 지속적 보호
✨ **확장**: AWS 기반으로 무제한 확장 가능

---

## 📞 문의사항

**프로젝트 팀**
- 개발: [팀명]
- 문의: [이메일]
- 웹사이트: [URL]

---

*Last Updated: 2026년 3월*
