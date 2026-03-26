# 시니어 안심 케어 시스템 - 가상 시나리오 예시

이 문서는 시스템이 실제로 어떻게 동작하는지 가상 시나리오를 통해 설명합니다.

---

## 📋 목차

1. [정상 활동 시나리오](#시나리오-1-정상-활동)
2. [활동 부재 감지 시나리오](#시나리오-2-활동-부재-감지)
3. [음성 확인 성공 시나리오](#시나리오-3-음성-확인-성공)
4. [음성 확인 실패 및 보호자 알림 시나리오](#시나리오-4-음성-확인-실패-보호자-알림)
5. [센서 데이터 검증 실패 시나리오](#시나리오-5-센서-데이터-검증-실패)
6. [설정 변경 시나리오](#시나리오-6-설정-변경)

---

## 시나리오 1: 정상 활동

### 상황
김영희 할머니(75세)가 아침에 일어나서 정상적으로 활동하는 경우

### 시간대별 이벤트

#### 07:00 - 기상 및 움직임 감지
```json
// 센서 데이터 전송 (모바일 앱)
{
  "userId": "user-001",
  "deviceId": "mobile-001",
  "deviceType": "mobile",
  "sensorType": "accelerometer",
  "value": 2.5,
  "timestamp": "2026-03-26T07:00:00Z"
}
```

**시스템 처리:**
1. SensorDataProcessor Lambda 실행
2. 데이터 검증 통과 (value > 0, 유효한 sensorType)
3. DynamoDB SensorData 테이블에 저장
4. UserSettings 테이블의 lastActivityTime 업데이트
5. 상태를 'active'로 유지

```python
# SensorDataProcessor 내부 처리 (주석)
# 1. 입력 데이터 검증
# 2. timestamp를 Unix epoch로 변환
# 3. TTL 설정 (30일 후 자동 삭제)
# 4. DynamoDB에 저장
# 5. 사용자 설정 업데이트 (lastActivityTime)
```

#### 07:30 - 화장실 문 열림 감지
```json
// 센서 데이터 전송 (IoT 센서)
{
  "userId": "user-001",
  "deviceId": "door-sensor-001",
  "deviceType": "iot",
  "sensorType": "door",
  "value": 1.0,
  "timestamp": "2026-03-26T07:30:00Z"
}
```

**시스템 처리:**
- 동일하게 SensorDataProcessor 처리
- lastActivityTime이 07:30으로 업데이트

#### 08:00 - InactivityDetector 정기 실행 (EventBridge)
```python
# InactivityDetector Lambda 실행 (매 1분마다)
# 1. 모든 사용자의 lastActivityTime 조회
# 2. 현재 시간과 비교
# 3. 김영희: 마지막 활동 30분 전 (임계값 120분 미만)
# 4. 정상 상태 유지, 아무 조치 없음
```

**결과:** ✅ 정상 활동 중, 알림 없음

---

## 시나리오 2: 활동 부재 감지

### 상황
김영희 할머니가 오후에 낮잠을 자다가 2시간 이상 움직임이 없는 경우

### 시간대별 이벤트

#### 13:00 - 마지막 활동
```json
{
  "userId": "user-001",
  "deviceId": "mobile-001",
  "deviceType": "mobile",
  "sensorType": "motion",
  "value": 1.2,
  "timestamp": "2026-03-26T13:00:00Z"
}
```

#### 13:01 ~ 15:00 - 활동 없음
```python
# InactivityDetector가 매 1분마다 실행되지만
# 아직 임계값(120분) 미만이므로 알림 없음
```

#### 15:01 - 임계값 초과 감지
```python
# InactivityDetector Lambda 실행
# 1. lastActivityTime: 13:00
# 2. 현재 시간: 15:01
# 3. 경과 시간: 121분 > 임계값(120분)
# 4. 활동 부재 감지!
```

**시스템 처리:**
1. AlertHistory 테이블에 새 알림 생성
```json
{
  "userId": "user-001",
  "alertId": "alert-20260326-001",
  "alertType": "inactivity_detected",
  "status": "voice_confirmation_pending",
  "createdAt": "2026-03-26T15:01:00Z",
  "lastActivityTime": "2026-03-26T13:00:00Z",
  "retryCount": 0
}
```

2. VoiceResponseHandler Lambda 호출 (SQS 메시지)
```python
# VoiceResponseHandler 실행
# 1. AI 스피커 API 호출 (가상)
# 2. "김영희님, 괜찮으신가요? 응답해주세요" 음성 재생
# 3. 응답 대기 (30초 타임아웃)
```

**결과:** ⏳ 음성 확인 대기 중

---

## 시나리오 3: 음성 확인 성공

### 상황
할머니가 AI 스피커의 질문에 "네, 괜찮아요"라고 응답

#### 15:01:15 - 음성 응답 수신
```json
// VoiceResponseHandler 수신 데이터 (가상)
{
  "userId": "user-001",
  "alertId": "alert-20260326-001",
  "voiceResponse": "네, 괜찮아요",
  "responseTime": "2026-03-26T15:01:15Z",
  "confidence": 0.95
}
```

**시스템 처리:**
```python
# VoiceResponseHandler Lambda
# 1. 음성 인식 결과 분석
# 2. 긍정 응답 확인 (confidence > 0.8)
# 3. AlertHistory 상태 업데이트
```

```json
// AlertHistory 업데이트
{
  "alertId": "alert-20260326-001",
  "status": "confirmed_safe",  // 상태 변경
  "voiceResponse": "네, 괜찮아요",
  "responseTime": "2026-03-26T15:01:15Z",
  "resolvedAt": "2026-03-26T15:01:15Z"
}
```

**결과:** ✅ 안전 확인 완료, 보호자 알림 없음

---

## 시나리오 4: 음성 확인 실패 → 보호자 알림

### 상황
할머니가 AI 스피커에 응답하지 않음 (30초 타임아웃)

#### 15:01:30 - 음성 응답 타임아웃
```python
# VoiceResponseHandler Lambda
# 1. 30초 대기 후 응답 없음
# 2. 재시도 카운트 확인 (0회)
# 3. 재시도 (최대 3회)
```

#### 15:02:00 - 2차 시도 실패
```python
# 2차 음성 확인 시도
# "김영희님, 응답이 없습니다. 괜찮으신가요?"
# 30초 대기 → 응답 없음
```

#### 15:02:30 - 3차 시도 실패
```python
# 3차 음성 확인 시도
# "김영희님, 마지막 확인입니다. 응답해주세요"
# 30초 대기 → 응답 없음
# 재시도 횟수 초과 (3회)
```

**시스템 처리:**
```python
# VoiceResponseHandler Lambda
# 1. 재시도 횟수 초과 확인
# 2. AlertHistory 상태 업데이트: 'no_response'
# 3. NotificationManager Lambda 호출 (SQS 메시지)
```

```json
// AlertHistory 업데이트
{
  "alertId": "alert-20260326-001",
  "status": "no_response",
  "retryCount": 3,
  "lastRetryTime": "2026-03-26T15:02:30Z"
}
```

#### 15:02:35 - 보호자 알림 전송
```python
# NotificationManager Lambda 실행
# 1. 사용자의 보호자 목록 조회 (RDS)
# 2. 각 보호자에게 SNS 알림 전송
```

```json
// 보호자 1 (딸) - SMS 전송
{
  "phoneNumber": "+82-10-1234-5678",
  "message": "[긴급] 김영희님이 2시간 이상 활동이 없으며, 음성 확인에 응답하지 않습니다. 확인이 필요합니다.",
  "priority": "high"
}

// 보호자 2 (아들) - 푸시 알림
{
  "deviceToken": "fcm-token-xxx",
  "title": "긴급 알림",
  "body": "어머니(김영희)의 활동이 감지되지 않습니다",
  "data": {
    "alertId": "alert-20260326-001",
    "userId": "user-001",
    "type": "no_response"
  }
}
```

**CloudWatch 로그:**
```
[INFO] NotificationManager: Sending alerts to 2 guardians
[INFO] SNS: SMS sent to +82-10-1234-5678 (MessageId: xxx)
[INFO] SNS: Push notification sent (MessageId: yyy)
[INFO] AlertHistory updated: notification_sent
```

**결과:** 🚨 보호자에게 긴급 알림 전송 완료

---

## 시나리오 5: 센서 데이터 검증 실패

### 상황
잘못된 센서 데이터가 전송된 경우

#### 케이스 1: 음수 값
```json
{
  "userId": "user-001",
  "deviceId": "mobile-001",
  "deviceType": "mobile",
  "sensorType": "accelerometer",
  "value": -1.5,  // ❌ 음수 값
  "timestamp": "2026-03-26T10:00:00Z"
}
```

**시스템 처리:**
```python
# SensorDataProcessor Lambda
# 1. 데이터 검증 실패: value < 0
# 2. 에러 응답 반환
```

```json
// 응답
{
  "statusCode": 400,
  "error": "ValidationError",
  "message": "Sensor value must be non-negative",
  "details": {
    "field": "value",
    "received": -1.5,
    "expected": ">= 0"
  }
}
```

**CloudWatch 로그:**
```
[ERROR] SensorDataProcessor: Validation failed
[ERROR] Field: value, Value: -1.5, Reason: negative value
[METRIC] ValidationErrors: 1
```

#### 케이스 2: 잘못된 센서 타입
```json
{
  "userId": "user-001",
  "deviceId": "mobile-001",
  "deviceType": "mobile",
  "sensorType": "invalid_sensor",  // ❌ 지원하지 않는 타입
  "value": 1.5,
  "timestamp": "2026-03-26T10:00:00Z"
}
```

**시스템 처리:**
```python
# SensorDataProcessor Lambda
# 1. 센서 타입 검증 실패
# 2. 허용된 타입: accelerometer, motion, door, temperature
```

```json
// 응답
{
  "statusCode": 400,
  "error": "ValidationError",
  "message": "Invalid sensor type",
  "details": {
    "field": "sensorType",
    "received": "invalid_sensor",
    "allowed": ["accelerometer", "motion", "door", "temperature"]
  }
}
```

**결과:** ❌ 데이터 저장 실패, 에러 로그 기록

---

## 시나리오 6: 설정 변경

### 상황
보호자가 활동 부재 임계값을 120분에서 180분으로 변경

#### 요청
```json
// SettingsManager Lambda 호출
{
  "userId": "user-001",
  "action": "update_settings",
  "inactivityThreshold": 180
}
```

**시스템 처리:**
```python
# SettingsManager Lambda
# 1. 사용자 존재 확인
# 2. 임계값 범위 검증 (30 ~ 480분)
# 3. UserSettings 테이블 업데이트
```

```json
// UserSettings 업데이트 전
{
  "userId": "user-001",
  "name": "김영희",
  "inactivityThreshold": 120,
  "updatedAt": "2026-03-26T08:00:00Z"
}

// UserSettings 업데이트 후
{
  "userId": "user-001",
  "name": "김영희",
  "inactivityThreshold": 180,  // 변경됨
  "updatedAt": "2026-03-26T16:00:00Z"  // 업데이트 시간
}
```

**CloudWatch 로그:**
```
[INFO] SettingsManager: Updating settings for user-001
[INFO] Field: inactivityThreshold, Old: 120, New: 180
[INFO] UserSettings updated successfully
[METRIC] SettingsUpdates: 1
```

**결과:** ✅ 설정 변경 완료, 다음 InactivityDetector 실행부터 새 임계값 적용

---

## 📊 시스템 흐름도

### 정상 활동 흐름
```
센서 데이터 발생
    ↓
SensorDataProcessor (검증 & 저장)
    ↓
DynamoDB 저장
    ↓
lastActivityTime 업데이트
    ↓
InactivityDetector (정기 체크)
    ↓
임계값 미만 → 정상 상태 유지
```

### 비상 상황 흐름
```
활동 부재 감지 (InactivityDetector)
    ↓
AlertHistory 생성
    ↓
VoiceResponseHandler 호출
    ↓
AI 스피커 음성 확인 (3회 재시도)
    ↓
    ├─ 응답 있음 → 안전 확인 완료
    └─ 응답 없음 → NotificationManager 호출
                      ↓
                  보호자 알림 전송 (SMS/푸시)
```

---

## 🔍 데이터 흐름 예시

### DynamoDB 테이블 상태 변화

#### SensorData 테이블
```
시간: 07:00
┌──────────┬───────────┬────────────┬──────────┐
│ userId   │ timestamp │ sensorType │ value    │
├──────────┼───────────┼────────────┼──────────┤
│ user-001 │ 1711436400│ accelero.. │ 2.5      │
└──────────┴───────────┴────────────┴──────────┘

시간: 07:30
┌──────────┬───────────┬────────────┬──────────┐
│ userId   │ timestamp │ sensorType │ value    │
├──────────┼───────────┼────────────┼──────────┤
│ user-001 │ 1711436400│ accelero.. │ 2.5      │
│ user-001 │ 1711438200│ door       │ 1.0      │ ← 추가
└──────────┴───────────┴────────────┴──────────┘
```

#### UserSettings 테이블
```
시간: 07:00 (업데이트 전)
┌──────────┬──────┬────────────────────┬────────┐
│ userId   │ name │ lastActivityTime   │ status │
├──────────┼──────┼────────────────────┼────────┤
│ user-001 │ 김영희│ 2026-03-26T06:00:00│ active │
└──────────┴──────┴────────────────────┴────────┘

시간: 07:00 (업데이트 후)
┌──────────┬──────┬────────────────────┬────────┐
│ userId   │ name │ lastActivityTime   │ status │
├──────────┼──────┼────────────────────┼────────┤
│ user-001 │ 김영희│ 2026-03-26T07:00:00│ active │ ← 변경
└──────────┴──────┴────────────────────┴────────┘
```

#### AlertHistory 테이블
```
시간: 15:01 (알림 생성)
┌──────────┬─────────────────┬──────────────┬────────────────────┐
│ userId   │ alertId         │ status       │ createdAt          │
├──────────┼─────────────────┼──────────────┼────────────────────┤
│ user-001 │ alert-...-001   │ voice_conf.. │ 2026-03-26T15:01:00│
└──────────┴─────────────────┴──────────────┴────────────────────┘

시간: 15:02:35 (응답 없음)
┌──────────┬─────────────────┬──────────────┬────────────────────┐
│ userId   │ alertId         │ status       │ createdAt          │
├──────────┼─────────────────┼──────────────┼────────────────────┤
│ user-001 │ alert-...-001   │ no_response  │ 2026-03-26T15:01:00│ ← 변경
└──────────┴─────────────────┴──────────────┴────────────────────┘
```

---

## 💡 주요 포인트

### 1. 자동 재시도 메커니즘
- 음성 확인: 최대 3회 재시도 (각 30초 간격)
- 보호자 알림: 실패 시 exponential backoff으로 재시도

### 2. 데이터 보존 정책
- 센서 데이터: 30일 후 자동 삭제 (TTL)
- 알림 이력: 90일 후 자동 삭제 (TTL)
- 일일 리포트: RDS에 영구 보관

### 3. 에러 처리
- 모든 Lambda 함수에 try-catch 구현
- CloudWatch Logs에 상세 로그 기록
- CloudWatch Metrics로 에러율 모니터링

### 4. 보안
- DynamoDB 테이블 KMS 암호화
- Lambda 함수 IAM 역할 최소 권한 원칙
- API Gateway 인증/인가 (향후 구현)

---

이 문서는 시스템의 동작을 이해하기 위한 가상 시나리오입니다.
실제 배포 후에는 CloudWatch Logs와 X-Ray를 통해 실시간 추적이 가능합니다.
