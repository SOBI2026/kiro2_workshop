# 요구사항 문서

## 소개

시니어 안심 케어 애플리케이션은 독거 노인의 안전을 실시간으로 모니터링하는 AWS 서버리스 기반 시스템입니다. 휴대폰 센서, IoT 기기, AI 스피커를 통합하여 노인의 일상 활동을 자동으로 감지하고, 활동 부재 시 보호자에게 즉각적인 알림을 전송합니다.

## 용어 정의

- **Senior_User**: 65세 이상의 독거 노인으로, 시스템의 주요 모니터링 대상
- **Guardian**: Senior_User의 보호자 (자녀, 친척, 사회복지사 등)
- **Activity_Signal**: 휴대폰 센서 또는 IoT 기기로부터 수집되는 활동 데이터
- **Inactivity_Threshold**: 활동 부재로 판단하는 시간 임계값 (분 단위)
- **Voice_Response_Timeout**: AI 스피커 음성 확인 시 응답 대기 시간 (초 단위)
- **System**: 시니어 안심 케어 애플리케이션 전체 시스템
- **SensorDataProcessor**: 센서 데이터를 처리하는 Lambda 함수
- **InactivityDetector**: 활동 부재를 감지하는 Lambda 함수
- **VoiceResponseHandler**: AI 스피커 음성 확인을 처리하는 Lambda 함수
- **NotificationManager**: 보호자 알림을 전송하는 Lambda 함수
- **ReportGenerator**: 활동 리포트를 생성하는 Lambda 함수
- **DynamoDB_SensorData**: 센서 데이터를 저장하는 DynamoDB 테이블
- **DynamoDB_UserSettings**: 사용자 설정을 저장하는 DynamoDB 테이블
- **DynamoDB_AlertHistory**: 알림 이력을 저장하는 DynamoDB 테이블
- **RDS_ActivityLog**: 활동 로그를 저장하는 RDS PostgreSQL 테이블
- **RDS_Guardians**: 보호자 정보를 저장하는 RDS PostgreSQL 테이블
- **AI_Speaker**: Amazon Alexa, Google Assistant, Naver Clova 등의 AI 스피커
- **EventBridge**: AWS EventBridge 스케줄러
- **SNS**: AWS Simple Notification Service
- **SQS**: AWS Simple Queue Service
- **DLQ**: Dead Letter Queue (처리 실패한 메시지를 저장하는 큐)

## 요구사항

### 요구사항 1: 센서 데이터 수집

**사용자 스토리:** Senior_User로서, 나의 일상 활동이 자동으로 감지되기를 원합니다. 그래야 별도의 조작 없이도 안전이 모니터링됩니다.

#### 인수 기준

1. WHEN Activity_Signal이 휴대폰 가속도센서로부터 수신되면, THE SensorDataProcessor SHALL 1초 간격으로 데이터를 수집한다
2. WHEN Activity_Signal이 IoT 기기로부터 수신되면, THE SensorDataProcessor SHALL 5분 간격으로 데이터를 수집한다
3. WHEN Activity_Signal이 수신되면, THE SensorDataProcessor SHALL 데이터를 DynamoDB_SensorData에 저장하고 RDS_ActivityLog에 기록한다
4. WHEN Activity_Signal이 처리되면, THE SensorDataProcessor SHALL DynamoDB_UserSettings의 마지막 활동 시간을 업데이트한다
5. WHEN 센서 데이터 처리가 완료되면, THE SensorDataProcessor SHALL 2초 이내에 응답을 반환한다

#### 정확성 속성

**Property 1: 센서 데이터 처리 완전성**
- *For all* Activity_Signal inputs received by the System, each signal SHALL be processed and stored exactly once in DynamoDB_SensorData with a corresponding timestamp

**Property 2: 타임스탬프 순서 보존**
- *For all* consecutive Activity_Signal records for a given Senior_User, the timestamp of record(n+1) SHALL be greater than or equal to the timestamp of record(n)

**Property 3: 센서 데이터 처리 멱등성**
- *For all* Activity_Signal with identical userId and timestamp, processing the signal multiple times SHALL produce the same final state as processing it once

---

### 요구사항 2: 활동 부재 감지

**사용자 스토리:** Guardian으로서, Senior_User의 활동이 일정 시간 동안 감지되지 않으면 자동으로 알림을 받고 싶습니다. 그래야 응급 상황에 신속하게 대응할 수 있습니다.

#### 인수 기준

1. THE EventBridge SHALL 매 1분마다 InactivityDetector를 실행한다
2. WHEN InactivityDetector가 실행되면, THE InactivityDetector SHALL 모든 활성 Senior_User의 활동 상태를 검사한다
3. WHEN 현재 시간과 마지막 활동 시간의 차이가 Inactivity_Threshold 이상이면, THE InactivityDetector SHALL 음성 확인 프로세스를 트리거한다
4. WHERE Inactivity_Threshold가 설정되지 않은 경우, THE System SHALL 기본값 120분을 사용한다
5. WHEN 활동 부재가 감지되면, THE InactivityDetector SHALL DynamoDB_AlertHistory에 상태 "voice_confirmation_pending"으로 기록한다
6. WHEN 동일한 Senior_User에 대해 이미 "voice_confirmation_pending" 상태의 알림이 존재하면, THE InactivityDetector SHALL 새로운 알림을 생성하지 않는다

#### 정확성 속성

**Property 4: 임계값 기반 감지 정확성**
- *For all* Senior_User records, voice confirmation SHALL be triggered if and only if (current_time - last_activity_time) >= Inactivity_Threshold

**Property 5: 중복 감지 방지**
- *For all* inactivity events, only one voice confirmation request SHALL be created per continuous inactivity period until the status changes to "confirmed_safe" or "resolved"

**Property 6: 전체 사용자 검사**
- *For all* active Senior_User records in DynamoDB_UserSettings, the InactivityDetector SHALL evaluate the inactivity status in each execution cycle

---

### 요구사항 3: AI 스피커 음성 확인

**사용자 스토리:** Senior_User로서, 활동이 감지되지 않을 때 AI 스피커가 나의 안전을 확인하기를 원합니다. 그래야 실제 응급 상황과 단순 휴식을 구분할 수 있습니다.

#### 인수 기준

1. WHEN 활동 부재가 감지되면, THE VoiceResponseHandler SHALL AI_Speaker를 통해 "안녕하세요, 괜찮으신가요?"라는 음성 프롬프트를 전송한다
2. WHEN 음성 프롬프트가 전송되면, THE VoiceResponseHandler SHALL DynamoDB_UserSettings에서 Voice_Response_Timeout을 조회한다
3. WHEN Voice_Response_Timeout이 설정되지 않은 경우, THE System SHALL 기본값 30초를 사용한다
4. WHEN Voice_Response_Timeout 내에 Senior_User의 응답이 수신되면, THE VoiceResponseHandler SHALL DynamoDB_AlertHistory의 상태를 "confirmed_safe"로 업데이트한다
5. WHEN Voice_Response_Timeout 내에 응답이 수신되지 않으면, THE VoiceResponseHandler SHALL DynamoDB_AlertHistory의 상태를 "no_response"로 업데이트하고 NotificationManager를 트리거한다
6. WHEN AI_Speaker API 호출이 실패하면, THE VoiceResponseHandler SHALL 즉시 NotificationManager를 트리거한다

#### 정확성 속성

**Property 7: 타임아웃 정확성**
- *For all* voice confirmation requests, the wait duration SHALL be within ±2 seconds of the configured Voice_Response_Timeout value

**Property 8: 상태 전이 일관성**
- *For all* voice confirmation requests, the alert status SHALL transition from "voice_confirmation_pending" to either "confirmed_safe" (if response received) or "no_response" (if timeout), and never to any other intermediate state

**Property 9: 유효한 응답 인식**
- *For all* valid voice responses received within Voice_Response_Timeout, the VoiceResponseHandler SHALL recognize and process the response, updating the alert status to "confirmed_safe"

---

### 요구사항 4: 보호자 긴급 알림

**사용자 스토리:** Guardian으로서, Senior_User가 음성 확인에 응답하지 않으면 즉시 알림을 받고 싶습니다. 그래야 신속하게 안전을 확인할 수 있습니다.

#### 인수 기준

1. WHEN 음성 확인에 응답이 없으면, THE NotificationManager SHALL 3초 이내에 첫 번째 알림 전송을 시도한다
2. WHEN 알림이 생성되면, THE NotificationManager SHALL Senior_User의 이름, 알림 유형, 마지막 활동 시간, 현재 시간을 포함한다
3. WHEN 알림이 전송되면, THE NotificationManager SHALL RDS_Guardians 테이블에서 모든 등록된 Guardian을 조회한다
4. WHEN Guardian 목록이 조회되면, THE NotificationManager SHALL 최대 5명의 Guardian에게 푸시 알림을 전송한다
5. WHEN 알림 전송이 실패하면, THE NotificationManager SHALL 해당 알림을 SQS NotificationQueue에 추가한다
6. WHEN 알림이 SQS NotificationQueue에 추가되면, THE System SHALL 5분 간격으로 재시도한다
7. WHEN 알림 재시도가 3회 실패하면, THE System SHALL 해당 메시지를 DLQ로 이동하고 CloudWatch 알람을 트리거한다

#### 정확성 속성

**Property 10: 알림 전송 시간 제약**
- *For all* alert triggers, the time between trigger and first notification attempt SHALL be less than or equal to 3 seconds

**Property 11: 모든 보호자 알림**
- *For all* alert events, notification attempts SHALL be made to all registered Guardians (up to 5) associated with the Senior_User

**Property 12: 재시도 로직 정확성**
- *For all* failed notification attempts, the System SHALL retry exactly 3 times with 5-minute intervals between attempts

**Property 13: 알림 메시지 완전성**
- *For all* notifications sent, the message SHALL include Senior_User name, alert type, last activity time, and current timestamp

---

### 요구사항 5: 사용자 설정 관리

**사용자 스토리:** Senior_User 또는 Guardian으로서, 활동 부재 임계값과 음성 응답 타임아웃을 조정하고 싶습니다. 그래야 개인의 생활 패턴에 맞게 시스템을 설정할 수 있습니다.

#### 인수 기준

1. WHEN Inactivity_Threshold가 설정되면, THE System SHALL 30분 이상 480분 이하의 값만 허용한다
2. WHEN Voice_Response_Timeout이 설정되면, THE System SHALL 10초 이상 60초 이하의 값만 허용한다
3. WHEN 설정 값이 유효 범위를 벗어나면, THE System SHALL 400 Bad Request 에러를 반환한다
4. WHEN 설정이 업데이트되면, THE System SHALL DynamoDB_UserSettings에 새로운 값을 저장한다
5. WHEN 설정이 업데이트되면, THE System SHALL 2분 이내에 모니터링 작업에 새로운 값을 적용한다
6. WHEN Guardian이 추가되면, THE System SHALL RDS_Guardians 테이블에 최대 5명까지만 허용한다
7. WHEN 6번째 Guardian 추가가 시도되면, THE System SHALL 400 Bad Request 에러를 반환한다

#### 정확성 속성

**Property 14: 설정 범위 검증**
- *For all* Inactivity_Threshold values stored in DynamoDB_UserSettings, the value SHALL be >= 30 AND <= 480 minutes
- *For all* Voice_Response_Timeout values stored in DynamoDB_UserSettings, the value SHALL be >= 10 AND <= 60 seconds

**Property 15: 설정 적용 시간**
- *For all* setting updates, the new value SHALL be used in monitoring operations within 2 minutes of the update timestamp

**Property 16: 보호자 수 제한**
- *For all* Senior_User records, the count of associated Guardians in RDS_Guardians table SHALL be <= 5

---

### 요구사항 6: 활동 이력 저장 및 조회

**사용자 스토리:** Guardian으로서, Senior_User의 과거 활동 이력을 조회하고 싶습니다. 그래야 활동 패턴을 파악하고 건강 상태를 모니터링할 수 있습니다.

#### 인수 기준

1. WHEN Activity_Signal이 처리되면, THE System SHALL 데이터를 DynamoDB_SensorData와 RDS_ActivityLog에 저장한다
2. WHEN 데이터가 DynamoDB_SensorData에 저장되면, THE System SHALL TTL을 30일로 설정한다
3. WHEN 데이터가 RDS_ActivityLog에 저장되면, THE System SHALL 30일 후 자동으로 삭제한다
4. WHEN Guardian이 활동 이력을 요청하면, THE System SHALL 요청한 날짜 범위의 모든 활동 데이터를 반환한다
5. WHEN 활동 이력 조회 요청이 수신되면, THE System SHALL Guardian이 해당 Senior_User의 보호자인지 확인한다
6. WHEN 활동 이력 조회가 실행되면, THE System SHALL 5초 이내에 결과를 반환한다

#### 정확성 속성

**Property 17: 데이터 보존 기간**
- *For all* activity records in DynamoDB_SensorData, the record SHALL exist for 30 days ±1 day from creation before TTL deletion
- *For all* activity records in RDS_ActivityLog, the record SHALL exist for 30 days ±1 day from creation

**Property 18: 조회 완전성**
- *For all* activity history queries with a specified date range, the result set SHALL include all records where timestamp falls within the range

**Property 19: 조회 성능**
- *For all* activity history queries with date range <= 30 days, the query response time SHALL be <= 5 seconds

---

### 요구사항 7: 일일 및 월간 리포트 생성

**사용자 스토리:** Guardian으로서, Senior_User의 활동을 요약한 일일 및 월간 리포트를 받고 싶습니다. 그래야 장기적인 건강 추세를 파악할 수 있습니다.

#### 인수 기준

1. THE EventBridge SHALL 매일 00:00 UTC에 ReportGenerator를 실행하여 일일 리포트를 생성한다
2. THE EventBridge SHALL 매월 1일 00:00 UTC에 ReportGenerator를 실행하여 월간 리포트를 생성한다
3. WHEN 일일 리포트가 생성되면, THE ReportGenerator SHALL 지난 24시간의 활동 데이터를 RDS_ActivityLog에서 조회한다
4. WHEN 월간 리포트가 생성되면, THE ReportGenerator SHALL 지난 30일의 활동 데이터를 RDS_ActivityLog에서 조회한다
5. WHEN 월간 리포트가 생성되면, THE ReportGenerator SHALL PDF 형식으로 리포트를 생성한다
6. WHEN PDF 리포트가 생성되면, THE ReportGenerator SHALL S3 버킷의 `{year}/{month}/{user_id}/report.pdf` 경로에 저장한다
7. WHEN 리포트가 S3에 저장되면, THE System SHALL 12개월 후 자동으로 삭제한다
8. WHEN 리포트 생성이 완료되면, THE ReportGenerator SHALL SNS DailyReport 토픽에 다운로드 링크를 게시한다

#### 정확성 속성

**Property 20: 리포트 생성 완전성**
- *For all* active Senior_User records, a daily summary SHALL be generated each day at 00:00 UTC

**Property 21: 리포트 데이터 정확성**
- *For all* daily summaries, the total activity count SHALL equal the count of Activity_Signal records for that day in RDS_ActivityLog

**Property 22: PDF 생성 및 저장**
- *For all* monthly report generation attempts, a valid PDF file SHALL be created and stored in S3 at the path `{year}/{month}/{user_id}/report.pdf`

---

### 요구사항 8: 시스템 가용성 및 성능

**사용자 스토리:** 시스템 관리자로서, 시스템이 높은 가용성과 성능을 유지하기를 원합니다. 그래야 응급 상황에서도 안정적으로 작동합니다.

#### 인수 기준

1. THE System SHALL 30일 측정 기간 동안 99.5% 이상의 가용성을 유지한다
2. THE System SHALL 최대 10,000명의 동시 Senior_User를 지원한다
3. WHEN API 요청률이 초당 1000개를 초과하면, THE System SHALL 1분 이내에 Lambda 동시 실행 수를 증가시킨다
4. WHEN 센서 데이터 처리 요청이 수신되면, THE SensorDataProcessor SHALL 평균 2초 이내에 처리를 완료한다
5. WHEN 알림 전송 요청이 수신되면, THE NotificationManager SHALL 평균 3초 이내에 처리를 완료한다

#### 정확성 속성

**Property 23: 가용성 목표**
- *For all* 30-day measurement periods, the system uptime ratio (total_uptime / total_time) SHALL be >= 0.995

**Property 24: 동시 사용자 지원**
- *For all* time periods, the System SHALL successfully process requests from up to 10,000 concurrent Senior_User accounts without degradation

**Property 25: 자동 스케일링**
- *When* API request rate exceeds 1000 requests per second, Lambda concurrency SHALL increase to handle the load within 1 minute

**Property 26: 센서 데이터 처리 지연**
- *For all* sensor data processing operations, the average latency SHALL be < 2 seconds

**Property 27: 알림 처리 지연**
- *For all* notification processing operations, the average latency SHALL be < 3 seconds

---

### 요구사항 9: 데이터 보안 및 개인정보 보호

**사용자 스토리:** Senior_User 및 Guardian으로서, 나의 개인정보와 건강 데이터가 안전하게 보호되기를 원합니다. 그래야 안심하고 서비스를 이용할 수 있습니다.

#### 인수 기준

1. THE System SHALL DynamoDB의 모든 데이터를 AWS KMS를 사용하여 암호화한다
2. THE System SHALL RDS의 모든 데이터를 AWS KMS를 사용하여 암호화한다
3. THE System SHALL S3의 모든 데이터를 AWS KMS를 사용하여 암호화한다
4. THE System SHALL 모든 데이터 전송에 TLS 1.2 이상을 사용한다
5. WHEN API 요청이 수신되면, THE System SHALL IAM 또는 Cognito를 사용하여 인증을 검증한다
6. WHEN 인증이 실패하면, THE System SHALL 401 Unauthorized 에러를 반환한다
7. WHEN Guardian이 데이터 접근을 요청하면, THE System SHALL RDS_Guardians 테이블에서 권한을 확인한다
8. WHEN 권한이 없으면, THE System SHALL 403 Forbidden 에러를 반환한다
9. THE System SHALL 데이터베이스 자격증명을 AWS Secrets Manager에 저장하고 90일마다 자동으로 로테이션한다

#### 정확성 속성

**Property 28: 저장 데이터 암호화**
- *For all* data stored in DynamoDB, RDS, and S3, encryption SHALL be enabled using AWS KMS

**Property 29: 전송 데이터 암호화**
- *For all* data transmitted between components, TLS 1.2 or higher SHALL be used

**Property 30: API 인증 필수**
- *For all* API requests to API Gateway, authentication SHALL be verified using IAM or Cognito tokens before processing

**Property 31: 권한 검증**
- *For all* Guardian data access requests, access SHALL be granted if and only if the Guardian is associated with the Senior_User in the RDS_Guardians table

---

### 요구사항 10: 에러 처리 및 복구

**사용자 스토리:** 시스템 관리자로서, 시스템이 에러 상황에서도 자동으로 복구되기를 원합니다. 그래야 수동 개입을 최소화하고 안정성을 유지할 수 있습니다.

#### 인수 기준

1. WHEN Lambda 함수 실행이 실패하면, THE System SHALL 자동으로 2회 재시도한다
2. WHEN 2회 재시도가 모두 실패하면, THE System SHALL 해당 이벤트를 DLQ로 이동한다
3. WHEN 이벤트가 DLQ로 이동하면, THE System SHALL SNS를 통해 시스템 관리자에게 알림을 전송한다
4. WHEN DynamoDB 스로틀링이 발생하면, THE System SHALL 지수 백오프를 사용하여 최대 10회 재시도한다
5. WHEN RDS 연결이 실패하면, THE System SHALL 최대 3회 재시도한다
6. WHEN AI_Speaker API 호출이 실패하면, THE VoiceResponseHandler SHALL 음성 확인 단계를 건너뛰고 즉시 NotificationManager를 트리거한다
7. WHEN SNS 알림 전송이 실패하면, THE NotificationManager SHALL 해당 알림을 SQS NotificationQueue에 추가한다
8. WHEN 에러율이 5분 동안 5%를 초과하면, THE System SHALL CloudWatch 알람을 트리거한다
9. THE System SHALL 모든 에러를 CloudWatch Logs에 기록한다

#### 정확성 속성

**Property 32: Lambda 재시도 로직**
- *For all* Lambda function execution failures, the System SHALL retry exactly 2 times before sending the event to the Dead Letter Queue

**Property 33: DLQ 알림**
- *For all* events sent to the Dead Letter Queue, an SNS notification SHALL be sent to system administrators

**Property 34: 에러율 모니터링**
- *When* (error_count / total_request_count) > 0.05 over a 5-minute window, a CloudWatch alarm SHALL be triggered
