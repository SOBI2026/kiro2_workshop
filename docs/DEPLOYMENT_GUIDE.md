# 시니어 안심 케어 시스템 - 배포 가이드

이 문서는 AWS SAM을 사용하여 시스템을 배포하는 방법을 설명합니다.

---

## 📋 사전 요구사항

### 1. 필수 도구 설치
- ✅ AWS CLI (버전 2.x 이상)
- ✅ SAM CLI (버전 1.x 이상)
- ✅ Python 3.12
- ✅ Docker (SAM 로컬 테스트용, 선택사항)

### 2. AWS 자격 증명 설정
```bash
# AWS CLI 설정 확인
aws sts get-caller-identity

# 출력 예시:
# {
#     "UserId": "AIDAXXXXXXXXXXXXXXXXX",
#     "Account": "098042404538",
#     "Arn": "arn:aws:sts::098042404538:assumed-role/WSParticipantRole/Participant"
# }
```

### 3. 필요한 권한
- Lambda 함수 생성/업데이트
- DynamoDB 테이블 생성
- IAM 역할 생성
- CloudFormation 스택 생성
- S3 버킷 접근 (배포 아티팩트 저장용)

---

## 🚀 배포 단계

### Step 1: 프로젝트 빌드

```bash
# 프로젝트 루트 디렉토리에서 실행
sam build

# 출력 예시:
# Building codeuri: src/sensor_data_processor runtime: python3.12 ...
# Building codeuri: src/inactivity_detector runtime: python3.12 ...
# ...
# Build Succeeded
```

**빌드 과정:**
1. 각 Lambda 함수의 의존성 설치 (requirements.txt)
2. 공통 모듈 (common/) 복사
3. `.aws-sam/build/` 디렉토리에 배포 패키지 생성

### Step 2: 배포 (첫 배포)

```bash
# 대화형 배포 (첫 배포 시 권장)
sam deploy --guided

# 질문에 답변:
# Stack Name [sam-app]: SeniorCare-Stack
# AWS Region [us-east-1]: us-east-1
# Confirm changes before deploy [Y/n]: Y
# Allow SAM CLI IAM role creation [Y/n]: Y
# Disable rollback [y/N]: N
# Save arguments to configuration file [Y/n]: Y
# SAM configuration file [samconfig.toml]: samconfig.toml
# SAM configuration environment [default]: default
```

**배포 과정:**
1. CloudFormation 변경 세트 생성
2. 변경 사항 미리보기 표시
3. 사용자 확인 후 배포 시작
4. 리소스 생성:
   - DynamoDB 테이블 3개
   - Lambda 함수 7개
   - IAM 역할 및 정책
   - EventBridge 규칙 (InactivityDetector용)
   - CloudWatch 로그 그룹

### Step 3: 배포 확인

```bash
# CloudFormation 스택 상태 확인
aws cloudformation describe-stacks --stack-name SeniorCare-Stack

# Lambda 함수 목록 확인
aws lambda list-functions --query 'Functions[?starts_with(FunctionName, `SeniorCare`)].FunctionName'

# DynamoDB 테이블 확인
aws dynamodb list-tables --query 'TableNames[?starts_with(@, `SeniorCare`)]'
```

**예상 출력:**
```json
// Lambda 함수
[
  "SeniorCare-SensorDataProcessor",
  "SeniorCare-InactivityDetector",
  "SeniorCare-VoiceResponseHandler",
  "SeniorCare-NotificationManager",
  "SeniorCare-ReportGenerator",
  "SeniorCare-SettingsManager",
  "SeniorCare-ActivityHistoryQuery"
]

// DynamoDB 테이블
[
  "SeniorCare-SensorData",
  "SeniorCare-UserSettings",
  "SeniorCare-AlertHistory"
]
```

---

## 🔄 업데이트 배포

코드 변경 후 재배포:

```bash
# 빌드
sam build

# 배포 (설정 파일 사용)
sam deploy

# 또는 특정 함수만 업데이트
sam deploy --parameter-overrides ParameterKey=FunctionName,ParameterValue=SensorDataProcessor
```

---

## 🧪 배포 후 테스트

### 1. DynamoDB 테이블 생성 확인

```bash
# 테이블 상세 정보 확인
aws dynamodb describe-table --table-name SeniorCare-UserSettings

# 예상 출력:
# {
#   "Table": {
#     "TableName": "SeniorCare-UserSettings",
#     "TableStatus": "ACTIVE",
#     "KeySchema": [
#       { "AttributeName": "userId", "KeyType": "HASH" }
#     ],
#     ...
#   }
# }
```

### 2. 테스트 데이터 삽입

```bash
# 테스트 사용자 생성
python dashboard/quick_test.py

# 출력:
# ✅ SeniorCare-SensorData 준비 완료
# ✅ SeniorCare-UserSettings 준비 완료
# ✅ SeniorCare-AlertHistory 준비 완료
# ✅ 사용자 생성 완료: test-user-001 (김영희)
# ✅ 센서 데이터 30개 생성 완료
# ✅ 샘플 알림 생성 완료
```

### 3. Lambda 함수 직접 호출 테스트

```bash
# SensorDataProcessor 테스트
aws lambda invoke \
  --function-name SeniorCare-SensorDataProcessor \
  --payload '{"userId":"test-user-001","deviceId":"device-001","deviceType":"mobile","sensorType":"accelerometer","value":2.5,"timestamp":"2026-03-26T10:00:00Z"}' \
  response.json

# 응답 확인
cat response.json

# 예상 출력:
# {
#   "statusCode": 200,
#   "body": "{\"message\":\"Sensor data processed successfully\",\"lastActivityTime\":\"2026-03-26T10:00:00+00:00\"}"
# }
```

### 4. InactivityDetector 수동 실행

```bash
# EventBridge 규칙 확인
aws events list-rules --name-prefix SeniorCare

# Lambda 직접 호출 (테스트용)
aws lambda invoke \
  --function-name SeniorCare-InactivityDetector \
  --payload '{}' \
  response.json

# 응답 확인
cat response.json

# 예상 출력:
# {
#   "statusCode": 200,
#   "body": "{\"message\":\"Inactivity detection complete\",\"activeUsers\":1,\"triggeredAlerts\":0}"
# }
```

---

## 📊 모니터링

### CloudWatch Logs 확인

```bash
# 로그 그룹 목록
aws logs describe-log-groups --log-group-name-prefix /aws/lambda/SeniorCare

# 최근 로그 스트림 확인
aws logs describe-log-streams \
  --log-group-name /aws/lambda/SeniorCare-SensorDataProcessor \
  --order-by LastEventTime \
  --descending \
  --max-items 5

# 로그 이벤트 조회
aws logs tail /aws/lambda/SeniorCare-SensorDataProcessor --follow
```

**예시 로그 출력:**
```
2026-03-26T10:00:01.234Z [INFO] Processing sensor data: {"userId":"test-user-001",...}
2026-03-26T10:00:01.456Z [INFO] STEP 1: 필수 필드 검증
2026-03-26T10:00:01.567Z [INFO] STEP 2: 디바이스 타입 검증
2026-03-26T10:00:01.678Z [INFO] STEP 5: DynamoDB에 센서 데이터 저장
2026-03-26T10:00:01.789Z [INFO] Successfully processed sensor data for user test-user-001
```

### CloudWatch Metrics 확인

```bash
# Lambda 함수 호출 횟수
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=SeniorCare-SensorDataProcessor \
  --start-time 2026-03-26T00:00:00Z \
  --end-time 2026-03-26T23:59:59Z \
  --period 3600 \
  --statistics Sum

# Lambda 함수 에러율
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Errors \
  --dimensions Name=FunctionName,Value=SeniorCare-SensorDataProcessor \
  --start-time 2026-03-26T00:00:00Z \
  --end-time 2026-03-26T23:59:59Z \
  --period 3600 \
  --statistics Sum
```

---

## 🎯 시나리오별 동작 확인

### 시나리오 1: 센서 데이터 전송

```bash
# 1. 센서 데이터 전송
aws lambda invoke \
  --function-name SeniorCare-SensorDataProcessor \
  --payload '{"userId":"test-user-001","deviceId":"mobile-001","deviceType":"mobile","sensorType":"motion","value":1.5,"timestamp":"2026-03-26T15:00:00Z"}' \
  response.json

# 2. DynamoDB에서 데이터 확인
aws dynamodb query \
  --table-name SeniorCare-SensorData \
  --key-condition-expression "userId = :uid" \
  --expression-attribute-values '{":uid":{"S":"test-user-001"}}' \
  --limit 5

# 3. 사용자 설정에서 lastActivityTime 확인
aws dynamodb get-item \
  --table-name SeniorCare-UserSettings \
  --key '{"userId":{"S":"test-user-001"}}'
```

### 시나리오 2: 활동 부재 감지

```bash
# 1. 사용자의 lastActivityTime을 2시간 전으로 설정
aws dynamodb update-item \
  --table-name SeniorCare-UserSettings \
  --key '{"userId":{"S":"test-user-001"}}' \
  --update-expression "SET lastActivityTime = :time" \
  --expression-attribute-values '{":time":{"S":"2026-03-26T13:00:00Z"}}'

# 2. InactivityDetector 실행
aws lambda invoke \
  --function-name SeniorCare-InactivityDetector \
  --payload '{}' \
  response.json

# 3. 알림 생성 확인
aws dynamodb query \
  --table-name SeniorCare-AlertHistory \
  --key-condition-expression "userId = :uid" \
  --expression-attribute-values '{":uid":{"S":"test-user-001"}}' \
  --scan-index-forward false \
  --limit 1

# 예상 출력:
# {
#   "Items": [{
#     "userId": {"S": "test-user-001"},
#     "alertId": {"S": "550e8400-..."},
#     "status": {"S": "voice_confirmation_pending"},
#     "alertType": {"S": "no_response"},
#     ...
#   }]
# }
```

### 시나리오 3: 설정 변경

```bash
# 임계값 변경 (120분 → 180분)
aws lambda invoke \
  --function-name SeniorCare-SettingsManager \
  --payload '{"userId":"test-user-001","action":"update_settings","inactivityThreshold":180}' \
  response.json

# 변경 확인
aws dynamodb get-item \
  --table-name SeniorCare-UserSettings \
  --key '{"userId":{"S":"test-user-001"}}' \
  --projection-expression "inactivityThreshold,updatedAt"

# 예상 출력:
# {
#   "Item": {
#     "inactivityThreshold": {"N": "180"},
#     "updatedAt": {"S": "2026-03-26T16:00:00Z"}
#   }
# }
```

---

## 🗑️ 리소스 정리

배포된 리소스를 모두 삭제하려면:

```bash
# CloudFormation 스택 삭제
aws cloudformation delete-stack --stack-name SeniorCare-Stack

# 삭제 진행 상황 확인
aws cloudformation describe-stacks --stack-name SeniorCare-Stack

# DynamoDB 테이블 수동 삭제 (필요시)
aws dynamodb delete-table --table-name SeniorCare-SensorData
aws dynamodb delete-table --table-name SeniorCare-UserSettings
aws dynamodb delete-table --table-name SeniorCare-AlertHistory

# S3 배포 버킷 정리 (필요시)
aws s3 rm s3://aws-sam-cli-managed-default-samclisourcebucket-xxx --recursive
aws s3 rb s3://aws-sam-cli-managed-default-samclisourcebucket-xxx
```

---

## ⚠️ 주의사항

### 1. 비용 관리
- DynamoDB: On-Demand 모드 사용 (사용량에 따라 과금)
- Lambda: 호출 횟수 및 실행 시간에 따라 과금
- CloudWatch Logs: 로그 저장 용량에 따라 과금

**예상 비용 (월간, 사용자 100명 기준):**
- DynamoDB: ~$10-20
- Lambda: ~$5-10
- CloudWatch: ~$5
- 총: ~$20-35/월

### 2. 제한 사항
- Lambda 동시 실행: 계정당 1000개 (기본값)
- DynamoDB 읽기/쓰기: On-Demand 모드는 제한 없음
- CloudWatch Logs: 로그 그룹당 10,000개 로그 스트림

### 3. 보안
- IAM 역할은 최소 권한 원칙 적용
- DynamoDB 테이블은 KMS 암호화 활성화
- Lambda 함수는 VPC 내부에 배치 (선택사항)

---

## 📚 추가 리소스

- [AWS SAM 공식 문서](https://docs.aws.amazon.com/serverless-application-model/)
- [DynamoDB 모범 사례](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)
- [Lambda 모범 사례](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [시나리오 예시 문서](./SCENARIO_EXAMPLES.md)

---

## 🆘 문제 해결

### 문제 1: SAM 빌드 실패
```
Error: PythonPipBuilder:ResolveDependencies - {pip error}
```

**해결:**
```bash
# Python 버전 확인
python --version  # 3.12 이상 필요

# pip 업그레이드
python -m pip install --upgrade pip

# 의존성 수동 설치 테스트
cd src/sensor_data_processor
pip install -r requirements.txt
```

### 문제 2: 배포 권한 부족
```
Error: User is not authorized to perform: cloudformation:CreateStack
```

**해결:**
- AWS 관리자에게 필요한 권한 요청
- 필요한 권한: CloudFormation, Lambda, DynamoDB, IAM

### 문제 3: DynamoDB 테이블 이미 존재
```
Error: Table already exists: SeniorCare-UserSettings
```

**해결:**
```bash
# 기존 테이블 삭제 후 재배포
aws dynamodb delete-table --table-name SeniorCare-UserSettings

# 또는 스택 전체 삭제 후 재배포
aws cloudformation delete-stack --stack-name SeniorCare-Stack
```

---

이 가이드를 따라 시스템을 성공적으로 배포하고 테스트할 수 있습니다!
