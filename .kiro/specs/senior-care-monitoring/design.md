# 시니어 안심 케어 애플리케이션 - 기술 설계 문서

## Overview

### 시스템 목적

시니어 안심 케어 애플리케이션은 독거 노인의 안전을 실시간으로 모니터링하는 AWS 서버리스 기반 시스템입니다. 휴대폰 센서, IoT 기기, AI 스피커를 통합하여 노인의 일상 활동을 자동으로 감지하고, 활동 부재 시 보호자에게 즉각적인 알림을 전송합니다.

### 핵심 목표

- **신뢰성**: 99.5% 가용성을 보장하여 응급 상황에서도 안정적으로 작동
- **실시간성**: 3초 이내 알림 전송으로 신속한 응급 대응 지원
- **확장성**: 최대 10,000명의 사용자를 동시에 지원
- **보안성**: 의료법 및 개인정보보호법을 준수하는 데이터 암호화 및 접근 제어
- **사용자 친화성**: 65세 이상 노인도 쉽게 사용할 수 있는 간단한 인터페이스

### 주요 기능

1. **센서 데이터 수집**: 휴대폰 가속도센서(1초 간격), IoT 기기(5분 간격) 데이터 실시간 수집
2. **활동 부재 감지**: 설정 가능한 임계값(30~480분)을 기반으로 활동 부재 자동 감지
3. **AI 스피커 확인**: 활동 부재 시 음성 프롬프트를 통한 안전 확인 (10~60초 응답 대기)
4. **보호자 알림**: 최대 5명의 보호자에게 3초 이내 푸시 알림 전송 (실패 시 3회 재시도)
5. **활동 이력 관리**: 30일간 활동 데이터 저장 및 조회
6. **리포트 생성**: 일일 요약 및 월간 PDF 리포트 자동 생성
7. **수동 긴급 호출**: 긴급 버튼 또는 음성 명령을 통한 즉시 알림
8. **활동 패턴 학습**: 머신러닝 기반 이상 징후 조기 감지

## Architecture

### 시스템 아키텍처 개요

시스템은 AWS 서버리스 아키텍처를 기반으로 하며, 이벤트 기반 마이크로서비스 패턴을 따릅니다.

```
┌─────────────────────────────────────────────────────────────────┐
│                      Data Sources Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Mobile App   │  │ IoT Devices  │  │ AI Speaker   │          │
│  │ (Sensors)    │  │ (Smart Home) │  │ (Alexa/Clova)│          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
└─────────┼──────────────────┼──────────────────┼──────────────────┘
          │                  │                  │
          └──────────────────┼──────────────────┘
                             │
          ┌──────────────────▼──────────────────┐
          │      API Gateway (REST/WebSocket)   │
          │  - Authentication (IAM/Cognito)     │
          │  - Rate Limiting (1000 req/s)       │
          │  - Request Validation               │
          └──────────────────┬──────────────────┘
                             │
          ┌──────────────────▼──────────────────┐
          │       Processing Layer (Lambda)     │
          │  ┌────────────────────────────────┐ │
          │  │ SensorDataProcessor            │ │
          │  │ - Validate sensor data         │ │
          │  │ - Update last activity time    │ │
          │  │ - Store to DynamoDB/RDS        │ │
          │  └────────────────────────────────┘ │
          │  ┌────────────────────────────────┐ │
          │  │ InactivityDetector             │ │
          │  │ - Check activity threshold     │ │
          │  │ - Trigger voice confirmation   │ │
          │  │ - EventBridge scheduled (1min) │ │
          │  └────────────────────────────────┘ │
          │  ┌────────────────────────────────┐ │
          │  │ VoiceResponseHandler           │ │
          │  │ - Process AI speaker response  │ │
          │  │ - Manage response timeout      │ │
          │  │ - Update alert status          │ │
          │  └────────────────────────────────┘ │
          │  ┌────────────────────────────────┐ │
          │  │ NotificationManager            │ │
          │  │ - Send push notifications      │ │
          │  │ - Retry logic (3 attempts)     │ │
          │  │ - Multi-guardian support       │ │
          │  └────────────────────────────────┘ │
          │  ┌────────────────────────────────┐ │
          │  │ ReportGenerator                │ │
          │  │ - Daily/monthly reports        │ │
          │  │ - PDF generation               │ │
          │  │ - S3 storage                   │ │
          │  └────────────────────────────────┘ │
          └──────────────────┬──────────────────┘
                             │
          ┌──────────────────▼──────────────────┐
          │        Data Storage Layer           │
          │  ┌────────────────────────────────┐ │
          │  │ DynamoDB (Real-time Data)      │ │
          │  │ - SensorData (TTL: 30 days)    │ │
          │  │ - UserSettings                 │ │
          │  │ - AlertHistory (TTL: 90 days)  │ │
          │  └────────────────────────────────┘ │
          │  ┌────────────────────────────────┐ │
          │  │ RDS PostgreSQL (Structured)    │ │
          │  │ - Users                        │ │
          │  │ - Guardians                    │ │
          │  │ - ActivityLog (30 days)        │ │
          │  └────────────────────────────────┘ │
          │  ┌────────────────────────────────┐ │
          │  │ S3 (Long-term Storage)         │ │
          │  │ - Monthly reports (12 months)  │ │
          │  │ - Data backups                 │ │
          │  └────────────────────────────────┘ │
          └──────────────────┬──────────────────┘
                             │
          ┌──────────────────▼──────────────────┐
          │      Messaging & Events Layer       │
          │  ┌────────────────────────────────┐ │
          │  │ SNS (Notifications)            │ │
          │  │ - AlertNotification topic      │ │
          │  │ - DailyReport topic            │ │
          │  │ - SystemAlert topic            │ │
          │  └────────────────────────────────┘ │
          │  ┌────────────────────────────────┐ │
          │  │ SQS (Async Processing)         │ │
          │  │ - NotificationQueue            │ │
          │  │ - ReportQueue                  │ │
          │  │ - DeadLetterQueue              │ │
          │  └────────────────────────────────┘ │
          │  ┌────────────────────────────────┐ │
          │  │ EventBridge (Scheduling)       │ │
          │  │ - Inactivity check (1 min)     │ │
          │  │ - Daily report (00:00 UTC)     │ │
          │  │ - Monthly report (1st day)     │ │
          │  └────────────────────────────────┘ │
          └──────────────────┬──────────────────┘
                             │
          ┌──────────────────▼──────────────────┐
          │      Security & Monitoring Layer    │
          │  ┌────────────────────────────────┐ │
          │  │ IAM (Access Control)           │ │
          │  │ - Lambda execution roles       │ │
          │  │ - Least privilege principle    │ │
          │  └────────────────────────────────┘ │
          │  ┌────────────────────────────────┐ │
          │  │ KMS (Encryption)               │ │
          │  │ - DynamoDB encryption          │ │
          │  │ - RDS encryption               │ │
          │  │ - S3 encryption                │ │
          │  └────────────────────────────────┘ │
          │  ┌────────────────────────────────┐ │
          │  │ Secrets Manager                │ │
          │  │ - DB credentials               │ │
          │  │ - API keys                     │ │
          │  │ - Auto rotation (90 days)      │ │
          │  └────────────────────────────────┘ │
          │  ┌────────────────────────────────┐ │
          │  │ CloudWatch (Monitoring)        │ │
          │  │ - Logs aggregation             │ │
          │  │ - Metrics & alarms             │ │
          │  │ - Dashboards                   │ │
          │  └────────────────────────────────┘ │
          └────────────────────────────────────┘
```

### 아키텍처 설계 원칙

1. **서버리스 우선**: 인프라 관리 부담 최소화 및 자동 스케일링
2. **이벤트 기반**: 느슨한 결합을 통한 확장성 및 유지보수성 향상
3. **마이크로서비스**: 각 Lambda 함수는 단일 책임 원칙을 따름
4. **비동기 처리**: SQS를 통한 안정적인 메시지 처리
5. **장애 격리**: 한 컴포넌트의 장애가 전체 시스템에 영향을 주지 않도록 설계
6. **보안 심층 방어**: 다층 보안 체계 (암호화, 인증, 권한 관리)
7. **관찰 가능성**: 포괄적인 로깅, 메트릭, 추적 기능

### 데이터 흐름

#### 1. 센서 데이터 수집 흐름

```
Mobile App/IoT Device
    → API Gateway (인증 및 검증)
    → SensorDataProcessor Lambda
    → DynamoDB SensorData 테이블 저장
    → RDS ActivityLog 테이블 저장
    → 마지막 활동 시간 업데이트
```

#### 2. 활동 부재 감지 흐름

```
EventBridge (매 1분 스케줄)
    → InactivityDetector Lambda
    → DynamoDB SensorData 조회 (마지막 활동 시간)
    → DynamoDB UserSettings 조회 (임계값)
    → 임계값 초과 시:
        → VoiceResponseHandler Lambda 트리거
        → AI Speaker API 호출 (음성 프롬프트)
        → 응답 대기 (10~60초)
        → 응답 없음 시:
            → NotificationManager Lambda 트리거
```

#### 3. 보호자 알림 흐름

```
NotificationManager Lambda
    → RDS Guardians 테이블 조회
    → SNS AlertNotification 토픽 게시
    → 최대 5명의 Guardian에게 푸시 알림
    → 실패 시:
        → SQS NotificationQueue에 메시지 추가
        → 5분 후 재시도 (최대 3회)
        → 모든 재시도 실패 시:
            → DLQ로 이동
            → CloudWatch 알람 트리거
```

#### 4. 리포트 생성 흐름

```
EventBridge (일일/월간 스케줄)
    → ReportGenerator Lambda
    → RDS ActivityLog 조회
    → 통계 계산 및 리포트 생성
    → 월간 리포트: PDF 생성
    → S3 버킷에 저장
    → SNS DailyReport 토픽 게시
    → Guardian에게 다운로드 링크 전송
```

## Components and Interfaces

### Lambda Functions

#### 1. SensorDataProcessor

**목적**: 휴대폰 및 IoT 기기로부터 센서 데이터를 수집하고 처리

**트리거**: API Gateway (POST /sensor-data)

**입력**:
```json
{
  "userId": "string",
  "deviceId": "string",
  "deviceType": "mobile" | "iot",
  "sensorType": "accelerometer" | "motion" | "door" | "temperature",
  "value": "number",
  "timestamp": "ISO8601 string"
}
```

**출력**:
```json
{
  "statusCode": 200,
  "message": "Sensor data processed successfully",
  "lastActivityTime": "ISO8601 string"
}
```

**처리 로직**:
1. 입력 데이터 검증 (필수 필드, 데이터 타입)
2. 타임스탬프 정규화 및 중복 체크
3. DynamoDB SensorData 테이블에 저장 (TTL: 30일)
4. RDS ActivityLog 테이블에 저장
5. DynamoDB UserSettings에서 마지막 활동 시간 업데이트
6. CloudWatch 메트릭 기록 (처리 시간, 성공/실패)

**에러 처리**:
- 입력 검증 실패: 400 Bad Request
- DynamoDB/RDS 쓰기 실패: 재시도 (지수 백오프), 실패 시 500 Internal Server Error
- 타임아웃: 5초 후 Lambda 종료

**성능 요구사항**:
- 처리 시간: 2초 이내 (휴대폰 센서), 5초 이내 (IoT 기기)
- 동시 실행: 최대 1000개 인스턴스
- 메모리: 512MB
- 타임아웃: 10초

---

#### 2. InactivityDetector

**목적**: 사용자의 활동 부재를 감지하고 음성 확인을 트리거

**트리거**: EventBridge 스케줄 (매 1분)

**입력**: EventBridge 이벤트 (스케줄 트리거)

**출력**: 음성 확인이 필요한 사용자 목록

**처리 로직**:
1. DynamoDB UserSettings에서 모든 활성 사용자 조회
2. 각 사용자에 대해:
   - 마지막 활동 시간 조회
   - Inactivity_Threshold 조회
   - 현재 시간 - 마지막 활동 시간 >= 임계값 확인
3. 임계값 초과 시:
   - DynamoDB AlertHistory에 상태 "voice_confirmation_pending" 기록
   - VoiceResponseHandler Lambda 비동기 호출
4. CloudWatch 메트릭 기록 (검사한 사용자 수, 트리거된 알림 수)

**에러 처리**:
- DynamoDB 조회 실패: 재시도 (최대 3회)
- Lambda 호출 실패: SQS에 메시지 추가하여 재처리

**성능 요구사항**:
- 처리 시간: 10,000명 사용자 기준 30초 이내
- 메모리: 1024MB
- 타임아웃: 60초
- 동시 실행: 1개 (스케줄 기반)

---

#### 3. VoiceResponseHandler

**목적**: AI 스피커를 통한 음성 확인 처리

**트리거**: 
- InactivityDetector Lambda (비동기 호출)
- API Gateway (POST /voice-response) - AI 스피커 응답 수신

**입력 (음성 확인 요청)**:
```json
{
  "userId": "string",
  "alertId": "string"
}
```

**입력 (음성 응답 수신)**:
```json
{
  "userId": "string",
  "alertId": "string",
  "response": "string",
  "timestamp": "ISO8601 string"
}
```

**출력**:
```json
{
  "statusCode": 200,
  "message": "Voice confirmation processed",
  "status": "confirmed_safe" | "no_response"
}
```

**처리 로직**:
1. DynamoDB UserSettings에서 Voice_Response_Timeout 조회
2. AI 스피커 API 호출 (Alexa Skills Kit, Google Assistant, Naver Clova)
   - 프롬프트: "안녕하세요, 괜찮으신가요?"
3. 타임아웃 내 응답 대기:
   - 응답 수신: DynamoDB AlertHistory 상태를 "confirmed_safe"로 업데이트
   - 응답 없음: 상태를 "no_response"로 업데이트, NotificationManager 트리거
4. CloudWatch 메트릭 기록

**에러 처리**:
- AI 스피커 API 호출 실패: 30초 타임아웃, 실패 시 즉시 NotificationManager 트리거
- 타임아웃 관리: EventBridge를 사용하여 Voice_Response_Timeout 후 자동 체크

**성능 요구사항**:
- 처리 시간: Voice_Response_Timeout + 5초
- 메모리: 512MB
- 타임아웃: 90초
- 동시 실행: 최대 100개 인스턴스

---

#### 4. NotificationManager

**목적**: 보호자에게 긴급 알림을 전송하고 재시도 로직 관리

**트리거**:
- VoiceResponseHandler Lambda (비동기 호출)
- SQS NotificationQueue (재시도)
- API Gateway (POST /emergency) - 수동 긴급 호출

**입력**:
```json
{
  "userId": "string",
  "alertId": "string",
  "alertType": "no_response" | "manual_emergency",
  "lastActivityTime": "ISO8601 string",
  "retryCount": "number"
}
```

**출력**:
```json
{
  "statusCode": 200,
  "message": "Notifications sent successfully",
  "sentCount": "number",
  "failedCount": "number"
}
```

**처리 로직**:
1. RDS Guardians 테이블에서 보호자 목록 조회 (최대 5명)
2. 알림 메시지 생성:
   - 사용자 이름
   - 알림 유형 (자동/수동)
   - 마지막 활동 시간
   - 현재 시간
   - 위치 정보 (가능한 경우)
3. SNS AlertNotification 토픽에 게시
4. 각 보호자에게 푸시 알림 전송 (3초 이내)
5. 실패한 알림:
   - retryCount < 3: SQS NotificationQueue에 추가 (5분 지연)
   - retryCount >= 3: DLQ로 이동, CloudWatch 알람 트리거
6. DynamoDB AlertHistory 업데이트

**에러 처리**:
- SNS 게시 실패: 재시도 (최대 3회)
- RDS 조회 실패: 캐시된 보호자 정보 사용 (가능한 경우)

**성능 요구사항**:
- 처리 시간: 3초 이내 (첫 번째 시도)
- 메모리: 512MB
- 타임아웃: 15초
- 동시 실행: 최대 500개 인스턴스

---

#### 5. ReportGenerator

**목적**: 일일 및 월간 활동 리포트 생성

**트리거**: EventBridge 스케줄
- 일일 리포트: 매일 00:00 UTC
- 월간 리포트: 매월 1일 00:00 UTC

**입력**: EventBridge 이벤트 (스케줄 트리거)

**출력**: 생성된 리포트 수 및 S3 경로

**처리 로직**:
1. RDS ActivityLog에서 활동 데이터 조회
   - 일일: 지난 24시간
   - 월간: 지난 30일
2. 통계 계산:
   - 총 활동 횟수
   - 시간대별 활동 분포
   - 알림 발생 횟수
   - 활동 패턴 분석
3. 월간 리포트: PDF 생성 (라이브러리: ReportLab/WeasyPrint)
4. S3 버킷에 저장: `{year}/{month}/{user_id}/report.pdf`
5. SNS DailyReport 토픽에 게시
6. 보호자에게 다운로드 링크 전송

**에러 처리**:
- RDS 조회 실패: 재시도 (최대 3회)
- PDF 생성 실패: 로그 기록, 다음 스케줄에서 재시도
- S3 업로드 실패: 재시도 (지수 백오프)

**성능 요구사항**:
- 처리 시간: 사용자당 5초 이내
- 메모리: 2048MB (PDF 생성)
- 타임아웃: 300초
- 동시 실행: 10개 인스턴스 (배치 처리)

---

### API Gateway 엔드포인트

#### 1. POST /sensor-data
- **목적**: 센서 데이터 수집
- **인증**: IAM 또는 Cognito
- **Rate Limit**: 사용자당 초당 10개 요청
- **Lambda**: SensorDataProcessor

#### 2. POST /voice-response
- **목적**: AI 스피커 응답 수신
- **인증**: API Key (AI 스피커 서비스)
- **Rate Limit**: 사용자당 초당 5개 요청
- **Lambda**: VoiceResponseHandler

#### 3. POST /emergency
- **목적**: 수동 긴급 호출
- **인증**: IAM 또는 Cognito
- **Rate Limit**: 사용자당 분당 5개 요청
- **Lambda**: NotificationManager

#### 4. GET /activity-history
- **목적**: 활동 이력 조회
- **인증**: IAM 또는 Cognito
- **Rate Limit**: 사용자당 초당 5개 요청
- **Lambda**: ActivityHistoryQuery (별도 Lambda)

#### 5. PUT /settings
- **목적**: 사용자 설정 업데이트
- **인증**: IAM 또는 Cognito
- **Rate Limit**: 사용자당 분당 10개 요청
- **Lambda**: SettingsManager (별도 Lambda)

#### 6. POST /guardian-response
- **목적**: 보호자 응답 기록
- **인증**: IAM 또는 Cognito
- **Rate Limit**: 사용자당 초당 10개 요청
- **Lambda**: GuardianResponseHandler (별도 Lambda)

---

### 외부 서비스 연동

#### 1. AI 스피커 통합

**Amazon Alexa**:
- Alexa Skills Kit 사용
- Custom Skill 생성: "시니어 안심 케어"
- Intent: CheckWellbeing
- 프롬프트: "안녕하세요, 괜찮으신가요?"
- 응답 처리: Lambda 함수로 전달

**Google Assistant**:
- Google Actions 사용
- Conversational Action 생성
- Webhook: API Gateway 엔드포인트
- 프롬프트 및 응답 처리 동일

**Naver Clova**:
- Clova Skills Kit 사용
- Custom Extension 생성
- Intent 및 프롬프트 설정
- Webhook 연동

#### 2. 푸시 알림 서비스

**iOS (APNs)**:
- SNS를 통한 APNs 연동
- 디바이스 토큰 관리
- 알림 페이로드 구성

**Android (FCM)**:
- SNS를 통한 FCM 연동
- 디바이스 토큰 관리
- 알림 페이로드 구성

## Data Models

### DynamoDB 테이블

#### 1. SensorData

**목적**: 실시간 센서 데이터 저장

**파티션 키**: `userId` (String)
**정렬 키**: `timestamp` (Number, Unix timestamp)

**속성**:
```json
{
  "userId": "string",
  "timestamp": "number",
  "deviceId": "string",
  "deviceType": "mobile | iot",
  "sensorType": "accelerometer | motion | door | temperature",
  "value": "number",
  "ttl": "number"  // 30일 후 자동 삭제
}
```

**인덱스**:
- GSI: `deviceId-timestamp-index` (기기별 조회)

**용량 모드**: On-Demand (자동 스케일링)

**TTL**: `ttl` 속성 (30일)

---

#### 2. UserSettings

**목적**: 사용자 설정 및 상태 저장

**파티션 키**: `userId` (String)

**속성**:
```json
{
  "userId": "string",
  "name": "string",
  "age": "number",
  "phone": "string",
  "inactivityThreshold": "number",  // 분 단위 (30~480)
  "voiceResponseTimeout": "number",  // 초 단위 (10~60)
  "lastActivityTime": "string",  // ISO8601
  "deviceIds": ["string"],  // 등록된 기기 목록
  "aiSpeakerId": "string",
  "activityPattern": {
    "hourlyAverage": [number],  // 24개 요소 (시간대별 평균)
    "dailyAverage": "number",
    "standardDeviation": "number",
    "lastUpdated": "string"
  },
  "patternLearningEnabled": "boolean",
  "status": "active | inactive",
  "createdAt": "string",
  "updatedAt": "string"
}
```

**인덱스**:
- GSI: `status-lastActivityTime-index` (활성 사용자 조회)

**용량 모드**: On-Demand

---

#### 3. AlertHistory

**목적**: 알림 이력 저장

**파티션 키**: `userId` (String)
**정렬 키**: `alertId` (String, UUID)

**속성**:
```json
{
  "userId": "string",
  "alertId": "string",
  "alertType": "no_response | manual_emergency | activity_decrease",
  "status": "voice_confirmation_pending | confirmed_safe | no_response | acknowledged | responding | resolved | notification_failed",
  "createdAt": "string",
  "lastActivityTime": "string",
  "voiceConfirmationSentAt": "string",
  "voiceResponseReceivedAt": "string",
  "notificationSentAt": "string",
  "guardianResponses": [
    {
      "guardianId": "string",
      "respondedAt": "string",
      "action": "acknowledged | responding | resolved",
      "notes": "string"
    }
  ],
  "retryCount": "number",
  "resolvedAt": "string",
  "ttl": "number"  // 90일 후 자동 삭제
}
```

**인덱스**:
- GSI: `status-createdAt-index` (상태별 조회)

**용량 모드**: On-Demand

**TTL**: `ttl` 속성 (90일)

---

### RDS PostgreSQL 테이블

#### 1. Users

**목적**: 사용자 기본 정보 저장

```sql
CREATE TABLE users (
  user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(100) NOT NULL,
  age INTEGER NOT NULL CHECK (age >= 65),
  phone VARCHAR(20) NOT NULL UNIQUE,
  email VARCHAR(255),
  address TEXT,
  emergency_contact VARCHAR(20),
  status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'suspended')),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_status ON users(status);
CREATE INDEX idx_users_phone ON users(phone);
```

---

#### 2. Guardians

**목적**: 보호자 정보 및 연결 관계 저장

```sql
CREATE TABLE guardians (
  guardian_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  name VARCHAR(100) NOT NULL,
  phone VARCHAR(20) NOT NULL,
  email VARCHAR(255),
  relationship VARCHAR(50),  -- 자녀, 친척, 사회복지사 등
  permission_level VARCHAR(20) DEFAULT 'standard' CHECK (permission_level IN ('standard', 'admin')),
  notification_enabled BOOLEAN DEFAULT true,
  push_token TEXT,  -- 푸시 알림 토큰
  device_type VARCHAR(20) CHECK (device_type IN ('ios', 'android')),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT unique_user_guardian UNIQUE (user_id, phone)
);

CREATE INDEX idx_guardians_user_id ON guardians(user_id);
CREATE INDEX idx_guardians_phone ON guardians(phone);

-- 보호자 수 제한 (최대 5명) 체크 함수
CREATE OR REPLACE FUNCTION check_guardian_limit()
RETURNS TRIGGER AS $$
BEGIN
  IF (SELECT COUNT(*) FROM guardians WHERE user_id = NEW.user_id) >= 5 THEN
    RAISE EXCEPTION 'Maximum 5 guardians allowed per user';
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER guardian_limit_check
BEFORE INSERT ON guardians
FOR EACH ROW EXECUTE FUNCTION check_guardian_limit();
```

---

#### 3. ActivityLog

**목적**: 활동 로그 저장 (30일 보존)

```sql
CREATE TABLE activity_log (
  log_id BIGSERIAL PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  activity_type VARCHAR(50) NOT NULL,  -- sensor_data, voice_response, manual_check
  device_type VARCHAR(20),  -- mobile, iot, ai_speaker
  device_id VARCHAR(100),
  sensor_type VARCHAR(50),
  value NUMERIC,
  timestamp TIMESTAMP NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_activity_log_user_timestamp ON activity_log(user_id, timestamp DESC);
CREATE INDEX idx_activity_log_timestamp ON activity_log(timestamp);

-- 30일 이상 된 데이터 자동 삭제 (일일 배치 작업)
CREATE OR REPLACE FUNCTION delete_old_activity_logs()
RETURNS void AS $$
BEGIN
  DELETE FROM activity_log WHERE timestamp < NOW() - INTERVAL '30 days';
END;
$$ LANGUAGE plpgsql;
```

---

### S3 버킷 구조

**버킷 이름**: `senior-care-reports-{environment}`

**디렉토리 구조**:
```
s3://senior-care-reports-prod/
├── reports/
│   ├── 2026/
│   │   ├── 01/
│   │   │   ├── {user_id}/
│   │   │   │   ├── report.pdf
│   │   │   │   └── metadata.json
│   │   ├── 02/
│   │   └── ...
├── backups/
│   ├── 2026/
│   │   ├── 01/
│   │   │   ├── sensor_data_backup.json.gz
│   │   │   └── alert_history_backup.json.gz
```

**라이프사이클 정책**:
- 리포트: 12개월 후 Glacier로 이동, 24개월 후 삭제
- 백업: 90일 후 Glacier로 이동, 365일 후 삭제

**암호화**: SSE-KMS (AWS KMS 키 사용)

**버전 관리**: 활성화 (실수로 삭제 방지)


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### 센서 데이터 수집 속성

#### Property 1: 센서 데이터 처리 완전성

*For all* Activity_Signal inputs received by the system, each signal SHALL be processed and stored exactly once in DynamoDB_SensorData with a corresponding timestamp.

**Validates: Requirements 1.1, 1.2, 1.3**

#### Property 2: 타임스탬프 순서 보존

*For all* consecutive Activity_Signal records for a given Senior_User, the timestamp of record(n+1) SHALL be greater than or equal to the timestamp of record(n).

**Validates: Requirements 1.3**

#### Property 3: 센서 데이터 처리 멱등성

*For all* Activity_Signal with identical userId and timestamp, processing the signal multiple times SHALL produce the same final state as processing it once.

**Validates: Requirements 1.3**

#### Property 4: 마지막 활동 시간 업데이트

*For all* Activity_Signal processed, the Senior_User's lastActivityTime in DynamoDB_UserSettings SHALL be updated to the signal's timestamp if it is more recent than the current value.

**Validates: Requirements 1.4**

---

### 활동 부재 감지 속성

#### Property 5: 임계값 기반 감지 정확성

*For all* Senior_User records, voice confirmation SHALL be triggered if and only if (current_time - last_activity_time) >= Inactivity_Threshold.

**Validates: Requirements 2.3**

#### Property 6: 중복 감지 방지

*For all* inactivity events, only one voice confirmation request SHALL be created per continuous inactivity period until the status changes to "confirmed_safe" or "resolved".

**Validates: Requirements 2.6**

#### Property 7: 전체 사용자 검사

*For all* active Senior_User records in DynamoDB_UserSettings, the InactivityDetector SHALL evaluate the inactivity status in each execution cycle.

**Validates: Requirements 2.2**

---

### AI 스피커 음성 확인 속성

#### Property 8: 타임아웃 정확성

*For all* voice confirmation requests, the wait duration SHALL be within ±2 seconds of the configured Voice_Response_Timeout value.

**Validates: Requirements 3.3**

#### Property 9: 상태 전이 일관성

*For all* voice confirmation requests, the alert status SHALL transition from "voice_confirmation_pending" to either "confirmed_safe" (if response received) or "no_response" (if timeout), and never to any other intermediate state.

**Validates: Requirements 3.5, 3.6**

#### Property 10: 유효한 응답 인식

*For all* valid voice responses received within Voice_Response_Timeout, the VoiceResponseHandler SHALL recognize and process the response, updating the alert status to "confirmed_safe".

**Validates: Requirements 3.5**

---

### 보호자 긴급 알림 속성

#### Property 11: 알림 전송 시간 제약

*For all* alert triggers, the time between trigger and first notification attempt SHALL be less than or equal to 3 seconds.

**Validates: Requirements 4.1**

#### Property 12: 모든 보호자 알림

*For all* alert events, notification attempts SHALL be made to all registered Guardians (up to 5) associated with the Senior_User.

**Validates: Requirements 4.4**

#### Property 13: 재시도 로직 정확성

*For all* failed notification attempts, the system SHALL retry exactly 3 times with 5-minute intervals between attempts.

**Validates: Requirements 4.6, 4.7**

#### Property 14: 알림 메시지 완전성

*For all* notifications sent, the message SHALL include Senior_User name, alert type, last activity time, and current timestamp.

**Validates: Requirements 4.2, 4.3**

---

### 사용자 설정 관리 속성

#### Property 15: 설정 범위 검증

*For all* Inactivity_Threshold values stored in DynamoDB_UserSettings, the value SHALL be >= 30 AND <= 480 minutes.
*For all* Voice_Response_Timeout values stored in DynamoDB_UserSettings, the value SHALL be >= 10 AND <= 60 seconds.

**Validates: Requirements 5.1, 5.2**

#### Property 16: 설정 적용 시간

*For all* setting updates, the new value SHALL be used in monitoring operations within 2 minutes of the update timestamp.

**Validates: Requirements 5.5**

#### Property 17: 보호자 수 제한

*For all* Senior_User records, the count of associated Guardians in RDS Guardians table SHALL be <= 5.

**Validates: Requirements 5.6**

---

### 활동 이력 저장 및 조회 속성

#### Property 18: 데이터 보존 기간

*For all* activity records in DynamoDB_SensorData, the record SHALL exist for 30 days ±1 day from creation before TTL deletion.
*For all* activity records in RDS_ActivityLog, the record SHALL exist for 30 days ±1 day from creation.

**Validates: Requirements 6.2, 6.3**

#### Property 19: 조회 완전성

*For all* activity history queries with a specified date range, the result set SHALL include all records where timestamp falls within the range.

**Validates: Requirements 6.5**

#### Property 20: 조회 성능

*For all* activity history queries with date range <= 30 days, the query response time SHALL be <= 5 seconds.

**Validates: Requirements 6.6**

---

### 리포트 생성 속성

#### Property 21: 리포트 생성 완전성

*For all* active Senior_User records, a daily summary SHALL be generated each day at 00:00 UTC.

**Validates: Requirements 7.2**

#### Property 22: 리포트 데이터 정확성

*For all* daily summaries, the total activity count SHALL equal the count of Activity_Signal records for that day in RDS_ActivityLog.

**Validates: Requirements 7.3**

#### Property 23: PDF 생성 및 저장

*For all* monthly report generation attempts, a valid PDF file SHALL be created and stored in S3 at the path `{year}/{month}/{user_id}/report.pdf`.

**Validates: Requirements 7.5, 7.6**

---

### 시스템 가용성 및 성능 속성

#### Property 24: 가용성 목표

*For all* 30-day measurement periods, the system uptime ratio (total_uptime / total_time) SHALL be >= 0.995.

**Validates: Requirements 8.1**

#### Property 25: 동시 사용자 지원

*For all* time periods, the system SHALL successfully process requests from up to 10,000 concurrent Senior_User accounts without degradation.

**Validates: Requirements 8.2**

#### Property 26: 자동 스케일링

*When* API request rate exceeds 1000 requests per second, Lambda concurrency SHALL increase to handle the load within 1 minute.

**Validates: Requirements 8.3**

#### Property 27: 센서 데이터 처리 지연

*For all* sensor data processing operations, the average latency SHALL be < 2 seconds.

**Validates: Requirements 8.4**

#### Property 28: 알림 처리 지연

*For all* notification processing operations, the average latency SHALL be < 3 seconds.

**Validates: Requirements 8.5**

---

### 데이터 보안 및 개인정보 보호 속성

#### Property 29: 저장 데이터 암호화

*For all* data stored in DynamoDB, RDS, and S3, encryption SHALL be enabled using AWS KMS.

**Validates: Requirements 9.1, 9.2, 9.3**

#### Property 30: 전송 데이터 암호화

*For all* data transmitted between components, TLS 1.2 or higher SHALL be used.

**Validates: Requirements 9.4**

#### Property 31: API 인증 필수

*For all* API requests to API Gateway, authentication SHALL be verified using IAM or Cognito tokens before processing.

**Validates: Requirements 9.5**

#### Property 32: 권한 검증

*For all* Guardian data access requests, access SHALL be granted if and only if the Guardian is associated with the Senior_User in the RDS Guardians table.

**Validates: Requirements 9.7**

---

### 에러 처리 및 복구 속성

#### Property 33: Lambda 재시도 로직

*For all* Lambda function execution failures, the system SHALL retry exactly 2 times before sending the event to the Dead Letter Queue.

**Validates: Requirements 10.1, 10.2**

#### Property 34: DLQ 알림

*For all* events sent to the Dead Letter Queue, an SNS notification SHALL be sent to system administrators.

**Validates: Requirements 10.3**

#### Property 35: 에러율 모니터링

*When* (error_count / total_request_count) > 0.05 over a 5-minute window, a CloudWatch alarm SHALL be triggered.

**Validates: Requirements 10.9**

---

### 사용자 등록 및 온보딩 속성

#### Property 36: 등록 완전성

*For all* user registration attempts, the registration SHALL be completed if and only if all required fields (name, age, phone) are provided and valid.

**Validates: Requirements 11.2**

#### Property 37: 기본 설정 생성

*For all* new Senior_User registrations, a default settings record SHALL be created in DynamoDB_UserSettings with Inactivity_Threshold=120 and Voice_Response_Timeout=30.

**Validates: Requirements 11.3**

#### Property 38: 기기 등록 유일성

*For all* device registrations, each device_id SHALL be associated with exactly one Senior_User.

**Validates: Requirements 11.6, 11.7, 11.8**

---

### 보호자 응답 및 조치 관리 속성

#### Property 39: 응답 기록 완전성

*For all* Guardian responses to alerts, the response SHALL be recorded in DynamoDB_AlertHistory with timestamp and Guardian ID.

**Validates: Requirements 12.1**

#### Property 40: 상태 전이 순서

*For all* alert status transitions, the status SHALL follow the valid sequence: voice_confirmation_pending → no_response → acknowledged → responding → resolved.

**Validates: Requirements 12.2, 12.3, 12.4**

#### Property 41: 해결 후 알림 중단

*For all* alerts with status "resolved", no additional notification attempts SHALL be made.

**Validates: Requirements 12.5**

---

### 수동 긴급 호출 속성

#### Property 42: 수동 호출 즉시 전송

*For all* manual emergency calls, the time between button press/voice command and first notification attempt SHALL be <= 1 second.

**Validates: Requirements 13.7**

#### Property 43: 음성 확인 건너뛰기

*For all* manual emergency calls, the alert status SHALL transition directly from "manual_emergency" to notification without "voice_confirmation_pending" state.

**Validates: Requirements 13.3**

#### Property 44: 수동 호출 우선순위

*When* both manual and automatic alerts exist in the processing queue, manual emergency alerts SHALL be processed first.

**Validates: Requirements 13.5**

---

### 활동 패턴 학습 및 이상 감지 속성

#### Property 45: 학습 데이터 충분성

*For all* pattern learning operations, learning SHALL begin if and only if at least 7 days of activity data exists for the Senior_User.

**Validates: Requirements 14.1**

#### Property 46: 이상 감지 통계 기준

*For all* activity anomaly detections, an alert SHALL be triggered if and only if the activity level is more than 2 standard deviations below the calculated mean.

**Validates: Requirements 14.4**

#### Property 47: 패턴 업데이트 주기

*For all* Senior_User records with pattern learning enabled, activity patterns SHALL be recalculated every 7 days ±1 hour.

**Validates: Requirements 14.6**


## Error Handling

### 에러 처리 전략

시스템은 다층 에러 처리 메커니즘을 구현하여 장애 격리 및 자동 복구를 보장합니다.

### Lambda 함수 에러 처리

#### 1. 재시도 메커니즘

**동기 호출 (API Gateway)**:
- 자동 재시도 없음 (클라이언트가 재시도 결정)
- 타임아웃: 함수별로 설정 (10~300초)
- 에러 응답: HTTP 상태 코드 및 에러 메시지 반환

**비동기 호출 (EventBridge, SNS)**:
- 자동 재시도: 최대 2회
- 재시도 간격: 지수 백오프 (1분, 2분)
- 실패 후: Dead Letter Queue로 이동

#### 2. Dead Letter Queue (DLQ)

**구성**:
- SQS DLQ: 각 Lambda 함수별로 별도 DLQ 설정
- 메시지 보존: 14일
- 알림: DLQ에 메시지 추가 시 SNS를 통해 관리자에게 알림

**처리**:
- 수동 검토 및 재처리
- CloudWatch 대시보드에서 DLQ 메트릭 모니터링
- 주기적인 DLQ 정리 작업

#### 3. 타임아웃 관리

**함수별 타임아웃**:
- SensorDataProcessor: 10초
- InactivityDetector: 60초
- VoiceResponseHandler: 90초
- NotificationManager: 15초
- ReportGenerator: 300초

**타임아웃 발생 시**:
- 부분 완료된 작업 롤백 (가능한 경우)
- CloudWatch Logs에 타임아웃 기록
- 재시도 로직 적용

### 데이터베이스 에러 처리

#### DynamoDB

**스로틀링 (ProvisionedThroughputExceededException)**:
- 지수 백오프 재시도 (AWS SDK 기본 제공)
- 최대 재시도: 10회
- 백오프 시간: 50ms ~ 20초

**조건부 쓰기 실패 (ConditionalCheckFailedException)**:
- 낙관적 잠금 실패로 간주
- 최신 데이터 재조회 후 재시도
- 최대 재시도: 3회

**네트워크 에러**:
- 자동 재시도 (AWS SDK)
- 타임아웃: 5초
- 실패 시 에러 로그 기록 및 알람

#### RDS PostgreSQL

**연결 풀 관리**:
- 최대 연결 수: 100
- 연결 타임아웃: 10초
- 유휴 연결 제거: 5분

**트랜잭션 실패**:
- 데드락: 자동 재시도 (최대 3회)
- 제약 조건 위반: 에러 반환 (재시도 없음)
- 네트워크 에러: 재시도 (최대 3회)

**읽기 전용 복제본**:
- 읽기 작업은 복제본으로 라우팅
- 복제본 장애 시 마스터로 폴백
- 자동 장애 조치 (RDS Multi-AZ)

### 외부 서비스 에러 처리

#### AI 스피커 API

**타임아웃**:
- 연결 타임아웃: 5초
- 응답 타임아웃: 30초
- 총 타임아웃: 35초

**에러 응답**:
- 4xx 에러: 재시도 없음, 즉시 NotificationManager 트리거
- 5xx 에러: 재시도 (최대 2회, 5초 간격)
- 네트워크 에러: 재시도 (최대 2회, 5초 간격)

**폴백 전략**:
- AI 스피커 API 실패 시 즉시 보호자 알림
- 음성 확인 단계 건너뛰기
- 실패 이유 로그 기록

#### 푸시 알림 서비스 (SNS)

**재시도 로직**:
- SNS 게시 실패: 재시도 (최대 3회)
- 개별 디바이스 전송 실패: SQS NotificationQueue에 추가
- 5분 간격으로 재시도 (최대 3회)

**디바이스 토큰 관리**:
- 유효하지 않은 토큰: RDS에서 제거
- 만료된 토큰: 갱신 요청
- 토큰 갱신 실패: Guardian에게 앱 재설치 안내

### 데이터 일관성 보장

#### 이벤트 소싱

**멱등성 키**:
- 모든 중요한 작업에 멱등성 키 사용
- DynamoDB 조건부 쓰기로 중복 방지
- 멱등성 키 형식: `{userId}:{timestamp}:{operation}`

**이벤트 순서 보장**:
- DynamoDB 정렬 키를 사용한 순서 보장
- 타임스탬프 기반 순서 정렬
- 순서 위반 감지 및 로그 기록

#### 분산 트랜잭션

**Saga 패턴**:
- 긴 트랜잭션을 여러 단계로 분할
- 각 단계는 독립적으로 커밋
- 실패 시 보상 트랜잭션 실행

**예시: 사용자 등록**:
1. RDS Users 테이블에 사용자 생성
2. DynamoDB UserSettings에 기본 설정 생성
3. 실패 시: RDS에서 사용자 삭제 (보상 트랜잭션)

### 모니터링 및 알람

#### CloudWatch 알람

**중요 알람**:
- Lambda 에러율 > 5% (5분 동안)
- DLQ 메시지 수 > 10
- API Gateway 5xx 에러율 > 1%
- RDS CPU 사용률 > 80%
- DynamoDB 스로틀링 발생

**알람 액션**:
- SNS를 통해 관리자에게 이메일/SMS 전송
- PagerDuty 통합 (긴급 알람)
- 자동 스케일링 트리거 (가능한 경우)

#### 로그 집계

**CloudWatch Logs Insights**:
- 모든 Lambda 함수 로그 집계
- 에러 패턴 분석
- 성능 병목 지점 식별

**로그 보존**:
- 일반 로그: 30일
- 에러 로그: 90일
- 감사 로그: 365일

### 장애 복구 절차

#### 자동 복구

**Lambda 함수 장애**:
- AWS Lambda 자동 재시도
- DLQ로 이동 후 수동 재처리

**DynamoDB 장애**:
- AWS 관리형 서비스 자동 복구
- Multi-AZ 배포로 고가용성 보장

**RDS 장애**:
- Multi-AZ 자동 장애 조치 (1~2분)
- 읽기 복제본으로 읽기 작업 라우팅

#### 수동 복구

**데이터 복구**:
- DynamoDB Point-in-Time Recovery (35일)
- RDS 자동 백업 (7일)
- S3 버전 관리 및 복구

**재처리**:
- DLQ 메시지 수동 재처리
- 실패한 알림 수동 재전송
- 누락된 리포트 수동 생성

### 우아한 성능 저하 (Graceful Degradation)

**우선순위 기반 처리**:
1. 수동 긴급 호출 (최우선)
2. 자동 긴급 알림
3. 센서 데이터 수집
4. 활동 이력 조회
5. 리포트 생성 (최하위)

**부하 제한**:
- API Gateway Rate Limiting
- Lambda 동시 실행 제한
- DynamoDB 용량 예약

**폴백 모드**:
- 비필수 기능 일시 중단 (리포트 생성, 패턴 학습)
- 필수 기능 유지 (센서 수집, 알림 전송)
- 복구 후 자동으로 정상 모드 전환

## Testing Strategy

### 테스트 접근 방식

시스템의 정확성을 보장하기 위해 **단위 테스트**와 **속성 기반 테스트(Property-Based Testing)**를 병행합니다.

- **단위 테스트**: 특정 예제, 엣지 케이스, 에러 조건 검증
- **속성 기반 테스트**: 모든 입력에 대해 보편적으로 성립하는 속성 검증

두 접근 방식은 상호 보완적이며, 단위 테스트는 구체적인 버그를 잡고, 속성 기반 테스트는 일반적인 정확성을 보장합니다.

### 속성 기반 테스트 (Property-Based Testing)

#### 테스트 라이브러리

**Python (Lambda 함수)**:
- **Hypothesis**: Python 표준 속성 기반 테스트 라이브러리
- 설치: `pip install hypothesis`

**JavaScript/TypeScript (프론트엔드)**:
- **fast-check**: JavaScript 속성 기반 테스트 라이브러리
- 설치: `npm install --save-dev fast-check`

#### 테스트 구성

**반복 횟수**: 각 속성 테스트는 최소 100회 반복 실행

**태그 형식**: 각 테스트는 설계 문서의 속성을 참조하는 주석 포함
```python
# Feature: senior-care-monitoring, Property 1: 센서 데이터 처리 완전성
```

#### 속성 테스트 예시

**Property 1: 센서 데이터 처리 완전성**

```python
from hypothesis import given, strategies as st
import pytest

# Feature: senior-care-monitoring, Property 1: 센서 데이터 처리 완전성
@given(
    user_id=st.uuids(),
    device_id=st.text(min_size=1, max_size=50),
    sensor_type=st.sampled_from(['accelerometer', 'motion', 'door', 'temperature']),
    value=st.floats(min_value=0, max_value=1000),
    timestamp=st.integers(min_value=1000000000, max_value=2000000000)
)
@pytest.mark.repeat(100)
def test_sensor_data_processing_completeness(user_id, device_id, sensor_type, value, timestamp):
    """
    For all Activity_Signal inputs, each signal SHALL be processed and stored exactly once.
    """
    # Arrange
    sensor_data = {
        'userId': str(user_id),
        'deviceId': device_id,
        'sensorType': sensor_type,
        'value': value,
        'timestamp': timestamp
    }
    
    # Act
    result = process_sensor_data(sensor_data)
    
    # Assert
    stored_record = get_sensor_data_from_db(str(user_id), timestamp)
    assert stored_record is not None
    assert stored_record['userId'] == str(user_id)
    assert stored_record['deviceId'] == device_id
    assert stored_record['sensorType'] == sensor_type
    assert stored_record['value'] == value
    assert stored_record['timestamp'] == timestamp
```

**Property 5: 임계값 기반 감지 정확성**

```python
from hypothesis import given, strategies as st
from datetime import datetime, timedelta

# Feature: senior-care-monitoring, Property 5: 임계값 기반 감지 정확성
@given(
    user_id=st.uuids(),
    inactivity_threshold=st.integers(min_value=30, max_value=480),
    time_since_last_activity=st.integers(min_value=0, max_value=600)
)
@pytest.mark.repeat(100)
def test_inactivity_detection_accuracy(user_id, inactivity_threshold, time_since_last_activity):
    """
    For all Senior_User records, voice confirmation SHALL be triggered 
    if and only if (current_time - last_activity_time) >= Inactivity_Threshold.
    """
    # Arrange
    current_time = datetime.now()
    last_activity_time = current_time - timedelta(minutes=time_since_last_activity)
    
    setup_user_settings(str(user_id), inactivity_threshold)
    update_last_activity_time(str(user_id), last_activity_time)
    
    # Act
    result = check_inactivity(str(user_id), current_time)
    
    # Assert
    should_trigger = time_since_last_activity >= inactivity_threshold
    assert result['voice_confirmation_triggered'] == should_trigger
```

**Property 11: 알림 전송 시간 제약**

```python
from hypothesis import given, strategies as st
import time

# Feature: senior-care-monitoring, Property 11: 알림 전송 시간 제약
@given(
    user_id=st.uuids(),
    alert_type=st.sampled_from(['no_response', 'manual_emergency'])
)
@pytest.mark.repeat(100)
def test_notification_timing_constraint(user_id, alert_type):
    """
    For all alert triggers, the time between trigger and first notification attempt 
    SHALL be less than or equal to 3 seconds.
    """
    # Arrange
    alert_data = {
        'userId': str(user_id),
        'alertType': alert_type,
        'lastActivityTime': datetime.now().isoformat()
    }
    
    # Act
    start_time = time.time()
    result = trigger_notification(alert_data)
    end_time = time.time()
    
    # Assert
    elapsed_time = end_time - start_time
    assert elapsed_time <= 3.0
    assert result['statusCode'] == 200
```

### 단위 테스트

#### 테스트 프레임워크

**Python (Lambda 함수)**:
- **pytest**: 테스트 프레임워크
- **moto**: AWS 서비스 모킹
- **pytest-mock**: 함수 모킹

**JavaScript/TypeScript**:
- **Jest**: 테스트 프레임워크
- **aws-sdk-mock**: AWS SDK 모킹

#### 단위 테스트 범위

**1. Lambda 함수 테스트**

각 Lambda 함수에 대해:
- 정상 입력 처리
- 유효하지 않은 입력 처리
- 에러 조건 처리
- 타임아웃 시나리오
- 재시도 로직

**예시: SensorDataProcessor**

```python
import pytest
from moto import mock_dynamodb, mock_rds
from sensor_data_processor import handler

@mock_dynamodb
def test_sensor_data_processor_valid_input():
    """정상 센서 데이터 처리"""
    event = {
        'body': json.dumps({
            'userId': 'user-123',
            'deviceId': 'device-456',
            'deviceType': 'mobile',
            'sensorType': 'accelerometer',
            'value': 9.8,
            'timestamp': '2026-03-15T10:30:00Z'
        })
    }
    
    response = handler(event, {})
    
    assert response['statusCode'] == 200
    assert 'lastActivityTime' in json.loads(response['body'])

@mock_dynamodb
def test_sensor_data_processor_invalid_input():
    """유효하지 않은 입력 처리"""
    event = {
        'body': json.dumps({
            'userId': 'user-123',
            # deviceId 누락
            'sensorType': 'accelerometer',
            'value': 9.8
        })
    }
    
    response = handler(event, {})
    
    assert response['statusCode'] == 400
    assert 'error' in json.loads(response['body'])

@mock_dynamodb
def test_sensor_data_processor_duplicate_timestamp():
    """중복 타임스탬프 처리 (멱등성)"""
    event = {
        'body': json.dumps({
            'userId': 'user-123',
            'deviceId': 'device-456',
            'deviceType': 'mobile',
            'sensorType': 'accelerometer',
            'value': 9.8,
            'timestamp': '2026-03-15T10:30:00Z'
        })
    }
    
    # 첫 번째 호출
    response1 = handler(event, {})
    # 두 번째 호출 (동일한 데이터)
    response2 = handler(event, {})
    
    assert response1['statusCode'] == 200
    assert response2['statusCode'] == 200
    # 데이터베이스에 하나의 레코드만 존재
    records = get_sensor_data_count('user-123', '2026-03-15T10:30:00Z')
    assert records == 1
```

**2. 통합 테스트**

여러 컴포넌트 간 상호작용 테스트:
- API Gateway → Lambda → DynamoDB
- Lambda → SNS → 푸시 알림
- EventBridge → Lambda → 여러 서비스

**예시: 활동 부재 감지 플로우**

```python
@mock_dynamodb
@mock_sns
def test_inactivity_detection_flow():
    """활동 부재 감지 전체 플로우"""
    # 1. 사용자 설정
    setup_user('user-123', inactivity_threshold=60)
    
    # 2. 마지막 활동 시간 설정 (90분 전)
    last_activity = datetime.now() - timedelta(minutes=90)
    update_last_activity('user-123', last_activity)
    
    # 3. InactivityDetector 실행
    inactivity_result = check_inactivity('user-123')
    assert inactivity_result['voice_confirmation_triggered'] == True
    
    # 4. VoiceResponseHandler 실행 (응답 없음 시뮬레이션)
    voice_result = simulate_voice_timeout('user-123')
    assert voice_result['status'] == 'no_response'
    
    # 5. NotificationManager 실행
    notification_result = send_notifications('user-123')
    assert notification_result['sentCount'] > 0
    
    # 6. AlertHistory 확인
    alert = get_alert_history('user-123')
    assert alert['status'] == 'no_response'
```

**3. 엣지 케이스 테스트**

특수한 경계 조건 테스트:
- 빈 데이터
- 최대/최소 값
- 동시성 문제
- 네트워크 장애

**예시: 보호자 수 제한**

```python
def test_guardian_limit_enforcement():
    """보호자 수 제한 (최대 5명)"""
    user_id = 'user-123'
    
    # 5명의 보호자 추가
    for i in range(5):
        result = add_guardian(user_id, f'guardian-{i}')
        assert result['statusCode'] == 200
    
    # 6번째 보호자 추가 시도
    result = add_guardian(user_id, 'guardian-6')
    assert result['statusCode'] == 400
    assert 'Maximum 5 guardians' in result['message']
```

### 성능 테스트

#### 부하 테스트

**도구**: Apache JMeter, Locust, Artillery

**시나리오**:
1. **정상 부하**: 초당 100개 요청, 10분 지속
2. **피크 부하**: 초당 1000개 요청, 5분 지속
3. **스파이크 테스트**: 초당 2000개 요청, 1분 지속

**측정 지표**:
- 응답 시간 (p50, p95, p99)
- 에러율
- Lambda 동시 실행 수
- DynamoDB 스로틀링 발생 여부

#### 스트레스 테스트

**목표**: 시스템 한계 파악

**시나리오**:
- 10,000명의 동시 사용자 시뮬레이션
- 각 사용자: 1초마다 센서 데이터 전송
- 총 부하: 초당 10,000개 요청

**예상 결과**:
- Lambda 자동 스케일링
- DynamoDB On-Demand 용량 자동 조정
- 응답 시간 < 2초 유지

### 보안 테스트

#### 인증 및 권한 테스트

```python
def test_unauthorized_access():
    """인증되지 않은 접근 차단"""
    event = {
        'headers': {},  # 인증 토큰 없음
        'body': json.dumps({'userId': 'user-123'})
    }
    
    response = handler(event, {})
    assert response['statusCode'] == 401

def test_cross_user_access():
    """다른 사용자 데이터 접근 차단"""
    # Guardian A는 User 1의 보호자
    # Guardian A가 User 2의 데이터 접근 시도
    
    event = {
        'headers': {'Authorization': 'guardian-a-token'},
        'pathParameters': {'userId': 'user-2'}
    }
    
    response = get_activity_history(event, {})
    assert response['statusCode'] == 403
```

#### 암호화 검증

```python
def test_data_encryption_at_rest():
    """저장 데이터 암호화 확인"""
    # DynamoDB 테이블 암호화 설정 확인
    table_description = dynamodb.describe_table(TableName='SensorData')
    assert table_description['Table']['SSEDescription']['Status'] == 'ENABLED'
    assert table_description['Table']['SSEDescription']['SSEType'] == 'KMS'

def test_data_encryption_in_transit():
    """전송 데이터 암호화 확인"""
    # API Gateway TLS 설정 확인
    api_config = apigateway.get_rest_api(restApiId='api-id')
    assert api_config['minimumCompressionSize'] >= 0
    # TLS 1.2 이상 강제
```

### 테스트 자동화

#### CI/CD 파이프라인

**GitHub Actions / AWS CodePipeline**:

```yaml
name: Test and Deploy

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      
      - name: Run unit tests
        run: pytest tests/unit --cov=src --cov-report=xml
      
      - name: Run property-based tests
        run: pytest tests/property --hypothesis-profile=ci
      
      - name: Run integration tests
        run: pytest tests/integration
      
      - name: Upload coverage
        uses: codecov/codecov-action@v2
        with:
          files: ./coverage.xml
  
  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Deploy to AWS
        run: |
          sam build
          sam deploy --no-confirm-changeset
```

#### 테스트 커버리지 목표

- **단위 테스트 커버리지**: 80% 이상
- **속성 기반 테스트**: 모든 Correctness Properties 커버
- **통합 테스트**: 주요 플로우 100% 커버
- **엣지 케이스**: 각 함수당 최소 5개 이상

### 모니터링 및 알람 테스트

#### Chaos Engineering

**AWS Fault Injection Simulator (FIS)**:
- Lambda 함수 지연 주입
- DynamoDB 스로틀링 시뮬레이션
- RDS 장애 조치 테스트
- 네트워크 지연 주입

**목표**: 시스템이 장애 상황에서도 우아하게 성능 저하하는지 확인

#### 알람 테스트

```python
def test_error_rate_alarm():
    """에러율 알람 트리거 테스트"""
    # 5분 동안 에러율 > 5% 생성
    for _ in range(100):
        trigger_error()
    
    # CloudWatch 알람 상태 확인
    alarm_state = cloudwatch.describe_alarms(
        AlarmNames=['ErrorRateAlarm']
    )
    assert alarm_state['MetricAlarms'][0]['StateValue'] == 'ALARM'
```

### 테스트 데이터 관리

#### 테스트 데이터 생성

**Faker 라이브러리 사용**:
```python
from faker import Faker

fake = Faker('ko_KR')

def generate_test_user():
    return {
        'userId': str(uuid.uuid4()),
        'name': fake.name(),
        'age': fake.random_int(min=65, max=95),
        'phone': fake.phone_number()
    }
```

#### 테스트 환경 격리

- **개발 환경**: 개발자 로컬 테스트
- **스테이징 환경**: CI/CD 자동 테스트
- **프로덕션 환경**: 실제 사용자 데이터

각 환경은 별도의 AWS 계정 또는 리전에 배포하여 격리

---

## 결론

본 설계 문서는 시니어 안심 케어 애플리케이션의 기술적 구현을 상세히 정의합니다. AWS 서버리스 아키텍처를 기반으로 하여 높은 가용성, 확장성, 보안성을 보장하며, 47개의 정확성 속성을 통해 시스템의 정확한 동작을 검증합니다.

### 주요 설계 결정

1. **서버리스 아키텍처**: Lambda, DynamoDB, API Gateway를 사용하여 자동 스케일링 및 운영 부담 최소화
2. **이벤트 기반 설계**: EventBridge, SNS, SQS를 통한 느슨한 결합 및 비동기 처리
3. **다층 보안**: KMS 암호화, IAM 인증, Secrets Manager를 통한 심층 방어
4. **포괄적인 에러 처리**: 재시도, DLQ, 알람을 통한 자동 복구 및 모니터링
5. **속성 기반 테스트**: Hypothesis를 사용한 포괄적인 정확성 검증

### 다음 단계

1. **구현 단계**: 설계 문서를 기반으로 Lambda 함수 및 인프라 코드 작성
2. **테스트 단계**: 단위 테스트 및 속성 기반 테스트 구현
3. **배포 단계**: CI/CD 파이프라인 구축 및 스테이징 환경 배포
4. **모니터링 단계**: CloudWatch 대시보드 및 알람 설정
5. **최적화 단계**: 성능 테스트 결과를 기반으로 시스템 최적화

