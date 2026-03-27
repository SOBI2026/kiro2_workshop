import json
import os
import sys
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from common.logger import get_logger
from common.error_handler import handle_lambda_error, ValidationError
from common.dynamodb_helper import DynamoDBHelper
from common.rds_helper import RDSHelper

logger = get_logger(__name__)

@handle_lambda_error
def lambda_handler(event, context):
    """
    Process sensor data from mobile phones and IoT devices
    
    Expected input:
    {
        "userId": "string",
        "deviceId": "string",
        "deviceType": "mobile" | "iot",
        "sensorType": "accelerometer" | "motion" | "door" | "temperature",
        "value": number,
        "timestamp": "ISO8601 string"
    }
    
    예시 시나리오:
    1. 정상 케이스: value=2.5, sensorType="accelerometer" → 저장 성공
    2. 검증 실패: value=-1.5 → 400 에러 (음수 불가)
    3. 검증 실패: sensorType="invalid" → 400 에러 (지원하지 않는 타입)
    """
    logger.info(f"Processing sensor data: {json.dumps(event)}")
    
    # Parse body if from API Gateway
    if 'body' in event:
        body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
    else:
        body = event
    
    # STEP 1: 필수 필드 검증
    # 예시: userId가 없으면 → ValidationError 발생
    required_fields = ['userId', 'deviceId', 'deviceType', 'sensorType', 'value', 'timestamp']
    for field in required_fields:
        if field not in body:
            raise ValidationError(f"Missing required field: {field}")
    
    user_id = body['userId']
    device_id = body['deviceId']
    device_type = body['deviceType']
    sensor_type = body['sensorType']
    value = body['value']
    timestamp_str = body['timestamp']
    
    # STEP 2: 디바이스 타입 검증
    # 예시: deviceType="invalid" → ValidationError
    if device_type not in ['mobile', 'iot']:
        raise ValidationError(f"Invalid deviceType: {device_type}")
    
    # STEP 3: 센서 타입 검증
    # 예시: sensorType="gps" → ValidationError (지원하지 않음)
    valid_sensor_types = ['accelerometer', 'motion', 'door', 'temperature']
    if sensor_type not in valid_sensor_types:
        raise ValidationError(f"Invalid sensorType: {sensor_type}")
    
    # STEP 3.5: 센서 값 검증 (음수 값 거부)
    # 예시: value=-1.0 → ValidationError
    if not isinstance(value, (int, float)):
        raise ValidationError(f"Invalid value type: {type(value)}")
    if value < 0:
        raise ValidationError(f"Sensor value cannot be negative: {value}")
    
    # STEP 4: 타임스탬프 파싱 및 정규화
    # 예시: "2026-03-26T07:00:00Z" → Unix timestamp (1711436400)
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        timestamp = int(dt.timestamp())
    except Exception as e:
        raise ValidationError(f"Invalid timestamp format: {timestamp_str}")
    
    # Initialize helpers
    dynamodb = DynamoDBHelper()
    rds = RDSHelper()
    
    # STEP 5: DynamoDB에 센서 데이터 저장
    # 테이블: SeniorCare-SensorData
    # TTL: 30일 후 자동 삭제
    # 예시: userId="user-001", timestamp=1711436400, value=2.5
    dynamodb.put_sensor_data(user_id, timestamp, device_id, device_type, sensor_type, value)
    
    # STEP 6: RDS에 활동 로그 저장 (장기 보관용) - 선택적
    # 테이블: activity_logs
    # 예시: 일일/월간 리포트 생성 시 사용
    try:
        rds.insert_activity_log(user_id, 'sensor_data', device_type, device_id, sensor_type, value, dt)
    except Exception as e:
        logger.warning(f"Failed to insert activity log to RDS (non-critical): {e}")
    
    # STEP 7: 사용자의 마지막 활동 시간 업데이트
    # 테이블: SeniorCare-UserSettings
    # 필드: lastActivityTime
    # 예시: "2026-03-26T07:00:00Z" → InactivityDetector가 이 값을 체크
    dynamodb.update_last_activity_time(user_id, timestamp)
    
    logger.info(f"Successfully processed sensor data for user {user_id}")
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Sensor data processed successfully',
            'lastActivityTime': dt.isoformat()
        })
    }
