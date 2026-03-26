# 시니어 안심 케어 애플리케이션

AWS 서버리스 아키텍처 기반 독거 노인 안전 모니터링 시스템

## 프로젝트 구조

```
senior-care-monitoring/
├── template.yaml                 # SAM CloudFormation template
├── requirements.txt              # Python dependencies
├── README.md
└── src/
    ├── common/                   # Shared utilities
    │   ├── __init__.py
    │   ├── logger.py            # Logging utilities
    │   ├── error_handler.py     # Error handling and retry logic
    │   ├── dynamodb_helper.py   # DynamoDB operations
    │   └── rds_helper.py        # RDS PostgreSQL operations
    ├── sensor_data_processor/   # Lambda: Process sensor data
    │   ├── __init__.py
    │   ├── app.py
    │   └── requirements.txt
    ├── inactivity_detector/     # Lambda: Detect inactivity
    ├── voice_response_handler/  # Lambda: Handle AI speaker responses
    ├── notification_manager/    # Lambda: Send guardian notifications
    ├── report_generator/        # Lambda: Generate reports
    ├── settings_manager/        # Lambda: Manage user settings
    └── activity_history_query/  # Lambda: Query activity history
```

## 주요 기능

1. **센서 데이터 수집**: 휴대폰 및 IoT 기기로부터 실시간 데이터 수집
2. **활동 부재 감지**: 설정 가능한 임계값 기반 자동 감지
3. **AI 스피커 음성 확인**: 활동 부재 시 음성 프롬프트를 통한 안전 확인
4. **보호자 긴급 알림**: 최대 5명의 보호자에게 3초 이내 푸시 알림
5. **활동 이력 관리**: 30일간 데이터 저장 및 조회
6. **리포트 생성**: 일일 요약 및 월간 PDF 리포트

## 기술 스택

- **컴퓨팅**: AWS Lambda (Python 3.11)
- **데이터베이스**: DynamoDB (실시간), RDS PostgreSQL (구조화)
- **스토리지**: S3 (리포트 및 백업)
- **메시징**: SNS (알림), SQS (비동기 처리)
- **스케줄링**: EventBridge
- **보안**: KMS (암호화), Secrets Manager (자격증명)
- **모니터링**: CloudWatch (로그, 메트릭, 알람)

## 배포 방법

### 사전 요구사항

- AWS CLI 설정 완료
- AWS SAM CLI 설치
- Python 3.11 설치

### 배포 단계

1. 프로젝트 빌드:
```bash
sam build
```

2. 배포:
```bash
sam deploy --guided
```

3. 배포 후 API Gateway 엔드포인트 확인:
```bash
aws cloudformation describe-stacks --stack-name senior-care-monitoring --query 'Stacks[0].Outputs'
```

## API 엔드포인트

- `POST /sensor-data` - 센서 데이터 수집
- `POST /voice-response` - AI 스피커 응답 수신
- `POST /emergency` - 수동 긴급 호출
- `GET /activity-history` - 활동 이력 조회
- `PUT /settings` - 사용자 설정 업데이트

## 환경 변수

Lambda 함수는 다음 환경 변수를 사용합니다:

- `DYNAMODB_SENSOR_DATA_TABLE` - SensorData 테이블 이름
- `DYNAMODB_USER_SETTINGS_TABLE` - UserSettings 테이블 이름
- `DYNAMODB_ALERT_HISTORY_TABLE` - AlertHistory 테이블 이름
- `RDS_SECRET_ARN` - RDS 자격증명 Secrets Manager ARN
- `SNS_ALERT_TOPIC_ARN` - 알림 SNS 토픽 ARN
- `SNS_REPORT_TOPIC_ARN` - 리포트 SNS 토픽 ARN
- `SQS_NOTIFICATION_QUEUE_URL` - 알림 SQS 큐 URL
- `REPORTS_BUCKET_NAME` - 리포트 S3 버킷 이름

## 테스트

속성 기반 테스트 (Hypothesis) 실행:
```bash
pytest tests/ -v
```

## 보안

- 모든 데이터는 KMS를 사용하여 암호화
- TLS 1.2 이상을 사용한 전송 암호화
- IAM 기반 API 인증
- Secrets Manager를 통한 자격증명 관리 (90일 자동 로테이션)

## 모니터링

CloudWatch 대시보드에서 다음 메트릭 확인:
- Lambda 실행 시간 및 에러율
- DynamoDB 읽기/쓰기 용량
- RDS CPU 및 메모리 사용률
- API Gateway 요청 수 및 지연 시간

## 라이선스

MIT License
