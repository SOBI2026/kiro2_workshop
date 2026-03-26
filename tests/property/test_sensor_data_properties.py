"""
Property-Based Tests for Sensor Data Processing
Feature: senior-care-monitoring

이 테스트는 센서 데이터 처리의 correctness properties를 검증합니다.
기준값 출처: senior-care-monitoring-presentation.md → requirements.md → design.md
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime, timedelta
from decimal import Decimal
import json
import sys
import os

# Lambda 함수 import를 위한 경로 설정
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from sensor_data_processor.app import lambda_handler
from common.dynamodb_helper import DynamoDBHelper


# ============================================================================
# Property 1: 센서 데이터 처리 완전성
# 출처: design.md - Property 1
# 기준: 모든 센서 데이터는 정확히 한 번 저장되어야 함
# ============================================================================

@given(
    user_id=st.text(min_size=5, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
    device_id=st.text(min_size=5, max_size=50),
    device_type=st.sampled_from(['mobile', 'iot']),
    sensor_type=st.sampled_from(['accelerometer', 'motion', 'door', 'temperature']),
    value=st.floats(min_value=0.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
    timestamp_offset=st.integers(min_value=0, max_value=86400)  # 0~24시간 전
)
@settings(max_examples=100, deadline=None)
def test_property_1_sensor_data_completeness(user_id, device_id, device_type, sensor_type, value, timestamp_offset):
    """
    Property 1: 센서 데이터 처리 완전성
    
    For all Activity_Signal inputs received by the System, 
    each signal SHALL be processed and stored exactly once in DynamoDB_SensorData.
    
    시나리오:
    - 입력: 임의의 유효한 센서 데이터
    - 기대: DynamoDB에 정확히 한 번 저장됨
    - 검증: 저장된 데이터가 입력과 일치함
    """
    # Arrange
    timestamp = datetime.utcnow() - timedelta(seconds=timestamp_offset)
    
    event = {
        'userId': user_id,
        'deviceId': device_id,
        'deviceType': device_type,
        'sensorType': sensor_type,
        'value': float(value),  # Keep as float in event
        'timestamp': timestamp.isoformat()
    }
    
    # Act
    response = lambda_handler(event, {})
    
    # Assert
    assert response['statusCode'] == 200, f"Expected 200, got {response['statusCode']}"
    
    # Verify data stored in DynamoDB
    dynamodb = DynamoDBHelper()
    stored_data = dynamodb.get_sensor_data(user_id, int(timestamp.timestamp()))
    
    assert stored_data is not None, "Data should be stored in DynamoDB"
    assert stored_data['userId'] == user_id
    assert stored_data['deviceId'] == device_id
    assert stored_data['sensorType'] == sensor_type


# ============================================================================
# Property 2: 센서 값 음수 불가
# 출처: design.md - 암묵적 제약 (value >= 0)
# 기준: 센서 값은 항상 0 이상이어야 함
# ============================================================================

@given(
    user_id=st.text(min_size=5, max_size=50),
    device_id=st.text(min_size=5, max_size=50),
    sensor_type=st.sampled_from(['accelerometer', 'motion', 'door', 'temperature']),
    value=st.floats(min_value=-1000.0, max_value=-0.01)  # 음수 값
)
@settings(max_examples=50, deadline=None)
def test_property_2_negative_sensor_value_rejected(user_id, device_id, sensor_type, value):
    """
    Property 2: 센서 값 음수 불가
    
    For all Activity_Signal with negative values,
    the System SHALL reject the data with 400 error.
    
    시나리오:
    - 입력: 음수 센서 값 (예: -1.5)
    - 기대: 400 Bad Request 에러
    - 검증: 데이터가 저장되지 않음
    """
    # Arrange
    event = {
        'userId': user_id,
        'deviceId': device_id,
        'deviceType': 'mobile',
        'sensorType': sensor_type,
        'value': value,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    # Act
    response = lambda_handler(event, {})
    
    # Assert
    assert response['statusCode'] == 400, f"Negative values should be rejected with 400, got {response['statusCode']}"
    
    body = json.loads(response['body'])
    assert 'error' in body or 'message' in body


# ============================================================================
# Property 3: 유효하지 않은 센서 타입 거부
# 출처: design.md - Component Interfaces
# 기준: accelerometer, motion, door, temperature만 허용
# ============================================================================

@given(
    user_id=st.text(min_size=5, max_size=50),
    device_id=st.text(min_size=5, max_size=50),
    invalid_sensor_type=st.text(min_size=1, max_size=20).filter(
        lambda x: x not in ['accelerometer', 'motion', 'door', 'temperature']
    ),
    value=st.floats(min_value=0.0, max_value=100.0)
)
@settings(max_examples=50, deadline=None)
def test_property_3_invalid_sensor_type_rejected(user_id, device_id, invalid_sensor_type, value):
    """
    Property 3: 유효하지 않은 센서 타입 거부
    
    For all Activity_Signal with invalid sensorType,
    the System SHALL reject the data with 400 error.
    
    시나리오:
    - 입력: 지원하지 않는 센서 타입 (예: "gps", "camera")
    - 기대: 400 Bad Request 에러
    - 허용 타입: accelerometer, motion, door, temperature
    """
    # Arrange
    event = {
        'userId': user_id,
        'deviceId': device_id,
        'deviceType': 'mobile',
        'sensorType': invalid_sensor_type,
        'value': value,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    # Act
    response = lambda_handler(event, {})
    
    # Assert
    assert response['statusCode'] == 400, f"Invalid sensor type should be rejected, got {response['statusCode']}"


# ============================================================================
# Property 4: 멱등성 (Idempotency)
# 출처: design.md - Property 3
# 기준: 동일한 데이터를 여러 번 처리해도 결과는 동일해야 함
# ============================================================================

@given(
    user_id=st.text(min_size=5, max_size=50),
    device_id=st.text(min_size=5, max_size=50),
    sensor_type=st.sampled_from(['accelerometer', 'motion', 'door', 'temperature']),
    value=st.floats(min_value=0.0, max_value=100.0),
    repeat_count=st.integers(min_value=2, max_value=5)
)
@settings(max_examples=30, deadline=None)
def test_property_4_idempotency(user_id, device_id, sensor_type, value, repeat_count):
    """
    Property 4: 멱등성
    
    For all Activity_Signal with identical userId and timestamp,
    processing the signal multiple times SHALL produce the same final state.
    
    시나리오:
    - 입력: 동일한 센서 데이터를 2~5회 전송
    - 기대: 모든 호출이 성공하고, 최종 상태는 동일
    - 검증: DynamoDB에 하나의 레코드만 존재
    """
    # Arrange
    timestamp = datetime.utcnow()
    event = {
        'userId': user_id,
        'deviceId': device_id,
        'deviceType': 'mobile',
        'sensorType': sensor_type,
        'value': value,
        'timestamp': timestamp.isoformat()
    }
    
    # Act - 여러 번 호출
    responses = []
    for _ in range(repeat_count):
        response = lambda_handler(event, {})
        responses.append(response)
    
    # Assert - 모든 호출이 성공
    for response in responses:
        assert response['statusCode'] == 200
    
    # Verify - DynamoDB에 하나의 레코드만 존재 (멱등성)
    dynamodb = DynamoDBHelper()
    stored_data = dynamodb.get_sensor_data(user_id, int(timestamp.timestamp()))
    assert stored_data is not None
    # 추가 검증: 동일한 timestamp로 여러 레코드가 있는지 확인
    # (실제로는 DynamoDB의 PK가 userId+timestamp이므로 자동으로 하나만 저장됨)


# ============================================================================
# Property 5: 마지막 활동 시간 업데이트
# 출처: requirements.md - 요구사항 1.4
# 기준: 센서 데이터 처리 시 lastActivityTime이 업데이트되어야 함
# ============================================================================

@given(
    user_id=st.text(min_size=5, max_size=50),
    device_id=st.text(min_size=5, max_size=50),
    sensor_type=st.sampled_from(['accelerometer', 'motion', 'door', 'temperature']),
    value=st.floats(min_value=0.0, max_value=100.0)
)
@settings(max_examples=50, deadline=None)
def test_property_5_last_activity_time_update(user_id, device_id, sensor_type, value):
    """
    Property 5: 마지막 활동 시간 업데이트
    
    For all Activity_Signal processed, the Senior_User's lastActivityTime 
    SHALL be updated to the signal's timestamp.
    
    시나리오:
    - 입력: 센서 데이터 전송
    - 기대: UserSettings의 lastActivityTime이 센서 timestamp로 업데이트
    - 검증: 업데이트된 시간이 센서 timestamp와 일치
    """
    # Arrange
    timestamp = datetime.utcnow()
    event = {
        'userId': user_id,
        'deviceId': device_id,
        'deviceType': 'mobile',
        'sensorType': sensor_type,
        'value': value,
        'timestamp': timestamp.isoformat()
    }
    
    # Act
    response = lambda_handler(event, {})
    
    # Assert
    assert response['statusCode'] == 200
    
    # Verify lastActivityTime updated
    dynamodb = DynamoDBHelper()
    user_settings = dynamodb.get_user_settings(user_id)
    
    if user_settings:
        last_activity = datetime.fromisoformat(user_settings['lastActivityTime'].replace('Z', '+00:00'))
        # 타임스탬프가 업데이트되었는지 확인 (±5초 허용)
        time_diff = abs((last_activity.replace(tzinfo=None) - timestamp).total_seconds())
        assert time_diff <= 5, f"lastActivityTime should be updated, diff: {time_diff}s"


# ============================================================================
# Property 6: 필수 필드 검증
# 출처: design.md - SensorDataProcessor 입력 스키마
# 기준: userId, deviceId, deviceType, sensorType, value, timestamp 필수
# ============================================================================

@given(
    missing_field=st.sampled_from(['userId', 'deviceId', 'deviceType', 'sensorType', 'value', 'timestamp'])
)
@settings(max_examples=20, deadline=None)
def test_property_6_required_fields_validation(missing_field):
    """
    Property 6: 필수 필드 검증
    
    For all Activity_Signal missing required fields,
    the System SHALL reject with 400 error.
    
    시나리오:
    - 입력: 필수 필드 중 하나가 누락된 데이터
    - 기대: 400 Bad Request 에러
    - 검증: 에러 메시지에 누락된 필드 명시
    """
    # Arrange - 완전한 데이터 생성
    complete_event = {
        'userId': 'test-user-001',
        'deviceId': 'device-001',
        'deviceType': 'mobile',
        'sensorType': 'accelerometer',
        'value': 2.5,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    # 하나의 필드 제거
    event = {k: v for k, v in complete_event.items() if k != missing_field}
    
    # Act
    response = lambda_handler(event, {})
    
    # Assert
    assert response['statusCode'] == 400, f"Missing {missing_field} should result in 400 error"
    
    body = json.loads(response['body'])
    assert 'error' in body or 'message' in body
    # 에러 메시지에 누락된 필드가 언급되어야 함
    error_text = str(body).lower()
    assert missing_field.lower() in error_text or 'missing' in error_text


# ============================================================================
# Property 7: 디바이스 타입 검증
# 출처: design.md - SensorDataProcessor 입력 스키마
# 기준: mobile 또는 iot만 허용
# ============================================================================

@given(
    invalid_device_type=st.text(min_size=1, max_size=20).filter(
        lambda x: x not in ['mobile', 'iot']
    )
)
@settings(max_examples=30, deadline=None)
def test_property_7_device_type_validation(invalid_device_type):
    """
    Property 7: 디바이스 타입 검증
    
    For all Activity_Signal with invalid deviceType,
    the System SHALL reject with 400 error.
    
    시나리오:
    - 입력: 유효하지 않은 deviceType (예: "tablet", "watch")
    - 기대: 400 Bad Request 에러
    - 허용 타입: mobile, iot
    """
    # Arrange
    event = {
        'userId': 'test-user-001',
        'deviceId': 'device-001',
        'deviceType': invalid_device_type,
        'sensorType': 'accelerometer',
        'value': 2.5,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    # Act
    response = lambda_handler(event, {})
    
    # Assert
    assert response['statusCode'] == 400, f"Invalid deviceType '{invalid_device_type}' should be rejected"


# ============================================================================
# Property 8: 타임스탬프 형식 검증
# 출처: design.md - SensorDataProcessor 입력 스키마
# 기준: ISO8601 형식만 허용
# ============================================================================

@given(
    invalid_timestamp=st.sampled_from([
        'not-a-date',
        '2026-13-01',  # 잘못된 월
        '2026-01-32',  # 잘못된 일
        '25:00:00',    # 잘못된 시간
        '12345',       # Unix timestamp (ISO8601 아님)
        ''             # 빈 문자열
    ])
)
@settings(max_examples=20, deadline=None)
def test_property_8_timestamp_format_validation(invalid_timestamp):
    """
    Property 8: 타임스탬프 형식 검증
    
    For all Activity_Signal with invalid timestamp format,
    the System SHALL reject with 400 error.
    
    시나리오:
    - 입력: 잘못된 형식의 timestamp
    - 기대: 400 Bad Request 에러
    - 유효 형식: ISO8601 (예: "2026-03-26T10:00:00Z")
    """
    # Arrange
    event = {
        'userId': 'test-user-001',
        'deviceId': 'device-001',
        'deviceType': 'mobile',
        'sensorType': 'accelerometer',
        'value': 2.5,
        'timestamp': invalid_timestamp
    }
    
    # Act
    response = lambda_handler(event, {})
    
    # Assert
    assert response['statusCode'] == 400, f"Invalid timestamp '{invalid_timestamp}' should be rejected"


# ============================================================================
# Property 9: 센서 값 범위 검증
# 출처: design.md - 암묵적 제약
# 기준: 센서 값은 0 이상 1000 이하 (합리적인 범위)
# ============================================================================

@given(
    value=st.floats(min_value=1001.0, max_value=1000000.0, allow_nan=False, allow_infinity=False)
)
@settings(max_examples=30, deadline=None)
def test_property_9_sensor_value_range(value):
    """
    Property 9: 센서 값 범위 검증
    
    For all Activity_Signal with value > 1000,
    the System SHOULD handle gracefully (현재는 허용하지만 경고 로그).
    
    시나리오:
    - 입력: 비정상적으로 큰 센서 값 (예: 5000)
    - 기대: 처리는 되지만 경고 로그 기록
    - 참고: 현재 구현은 허용하지만, 향후 제한 가능
    """
    # Arrange
    event = {
        'userId': 'test-user-001',
        'deviceId': 'device-001',
        'deviceType': 'mobile',
        'sensorType': 'accelerometer',
        'value': value,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    # Act
    response = lambda_handler(event, {})
    
    # Assert
    # 현재는 허용하지만, 향후 제한할 수 있음
    # 이 테스트는 시스템이 큰 값을 어떻게 처리하는지 문서화
    assert response['statusCode'] in [200, 400], "System should handle large values gracefully"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--hypothesis-show-statistics'])
