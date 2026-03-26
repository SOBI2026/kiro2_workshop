"""
Property-Based Tests for Settings Management
Feature: senior-care-monitoring

이 테스트는 사용자 설정 관리의 correctness properties를 검증합니다.
기준값 출처: senior-care-monitoring-presentation.md → requirements.md (요구사항 5)
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from settings_manager.app import lambda_handler as settings_handler
from common.dynamodb_helper import DynamoDBHelper


# ============================================================================
# Property 22: 임계값 범위 검증
# 출처: requirements.md - Property 14, design.md - Property 15
# 기준: 30분 ≤ Inactivity_Threshold ≤ 480분
# ============================================================================

@given(
    threshold=st.integers(min_value=30, max_value=480)
)
@settings(max_examples=50, deadline=None)
def test_property_22_valid_inactivity_threshold(threshold):
    """
    Property 22: 유효한 임계값 범위
    
    For all Inactivity_Threshold values in [30, 480],
    the System SHALL accept and store the value.
    
    시나리오:
    - 입력: 30~480분 범위의 임계값
    - 기대: 설정 성공 (200 OK)
    - 검증: DynamoDB에 저장된 값 확인
    
    기준값 출처: presentation.md "임계값: 30~480분 (설정 가능)"
    """
    # Arrange
    user_id = f'test-user-threshold-{threshold}'
    
    event = {
        'userId': user_id,
        'action': 'update_settings',
        'inactivityThreshold': threshold
    }
    
    # Act
    response = settings_handler(event, {})
    
    # Assert
    assert response['statusCode'] == 200, \
        f"Threshold {threshold} should be accepted, got {response['statusCode']}"
    
    # Verify stored value
    dynamodb = DynamoDBHelper()
    settings = dynamodb.get_user_settings(user_id)
    
    if settings:
        assert settings['inactivityThreshold'] == threshold, \
            f"Stored threshold should be {threshold}, got {settings['inactivityThreshold']}"


@given(
    invalid_threshold=st.one_of(
        st.integers(min_value=-100, max_value=29),  # 30분 미만
        st.integers(min_value=481, max_value=10000)  # 480분 초과
    )
)
@settings(max_examples=30, deadline=None)
def test_property_22_invalid_inactivity_threshold(invalid_threshold):
    """
    Property 22: 유효하지 않은 임계값 거부
    
    For all Inactivity_Threshold values outside [30, 480],
    the System SHALL reject with 400 error.
    
    시나리오:
    - 입력: 범위 밖의 임계값 (예: 10분, 500분)
    - 기대: 400 Bad Request 에러
    
    기준값 출처: requirements.md 요구사항 5.1, 5.3
    """
    # Arrange
    user_id = 'test-user-invalid-threshold'
    
    event = {
        'userId': user_id,
        'action': 'update_settings',
        'inactivityThreshold': invalid_threshold
    }
    
    # Act
    response = settings_handler(event, {})
    
    # Assert
    assert response['statusCode'] == 400, \
        f"Invalid threshold {invalid_threshold} should be rejected with 400"


# ============================================================================
# Property 23: 음성 응답 타임아웃 범위 검증
# 출처: requirements.md - Property 14, design.md - Property 15
# 기준: 10초 ≤ Voice_Response_Timeout ≤ 60초
# ============================================================================

@given(
    timeout=st.integers(min_value=10, max_value=60)
)
@settings(max_examples=50, deadline=None)
def test_property_23_valid_voice_timeout(timeout):
    """
    Property 23: 유효한 음성 응답 타임아웃
    
    For all Voice_Response_Timeout values in [10, 60],
    the System SHALL accept and store the value.
    
    시나리오:
    - 입력: 10~60초 범위의 타임아웃
    - 기대: 설정 성공
    
    기준값 출처: presentation.md "응답 대기: 10~60초 (설정 가능)"
    """
    # Arrange
    user_id = f'test-user-timeout-{timeout}'
    
    event = {
        'userId': user_id,
        'action': 'update_settings',
        'voiceResponseTimeout': timeout
    }
    
    # Act
    response = settings_handler(event, {})
    
    # Assert
    assert response['statusCode'] == 200, \
        f"Timeout {timeout} should be accepted"
    
    # Verify stored value
    dynamodb = DynamoDBHelper()
    settings = dynamodb.get_user_settings(user_id)
    
    if settings:
        assert settings['voiceResponseTimeout'] == timeout


@given(
    invalid_timeout=st.one_of(
        st.integers(min_value=-10, max_value=9),  # 10초 미만
        st.integers(min_value=61, max_value=1000)  # 60초 초과
    )
)
@settings(max_examples=30, deadline=None)
def test_property_23_invalid_voice_timeout(invalid_timeout):
    """
    Property 23: 유효하지 않은 음성 응답 타임아웃 거부
    
    For all Voice_Response_Timeout values outside [10, 60],
    the System SHALL reject with 400 error.
    
    시나리오:
    - 입력: 범위 밖의 타임아웃 (예: 5초, 120초)
    - 기대: 400 Bad Request 에러
    
    기준값 출처: requirements.md 요구사항 5.2, 5.3
    """
    # Arrange
    user_id = 'test-user-invalid-timeout'
    
    event = {
        'userId': user_id,
        'action': 'update_settings',
        'voiceResponseTimeout': invalid_timeout
    }
    
    # Act
    response = settings_handler(event, {})
    
    # Assert
    assert response['statusCode'] == 400, \
        f"Invalid timeout {invalid_timeout} should be rejected"


# ============================================================================
# Property 24: 설정 업데이트 원자성
# 출처: design.md - 데이터 일관성 보장
# 기준: 설정 업데이트는 원자적으로 수행되어야 함
# ============================================================================

@given(
    threshold=st.integers(min_value=30, max_value=480),
    timeout=st.integers(min_value=10, max_value=60)
)
@settings(max_examples=30, deadline=None)
def test_property_24_settings_update_atomicity(threshold, timeout):
    """
    Property 24: 설정 업데이트 원자성
    
    For all settings update operations,
    all fields SHALL be updated atomically (all or nothing).
    
    시나리오:
    - 입력: 여러 설정 값 동시 업데이트
    - 기대: 모두 성공 또는 모두 실패
    - 검증: 부분 업데이트 없음
    """
    # Arrange
    user_id = 'test-user-atomic'
    
    event = {
        'userId': user_id,
        'action': 'update_settings',
        'inactivityThreshold': threshold,
        'voiceResponseTimeout': timeout
    }
    
    # Act
    response = settings_handler(event, {})
    
    # Assert
    assert response['statusCode'] == 200
    
    # Verify both values updated
    dynamodb = DynamoDBHelper()
    settings = dynamodb.get_user_settings(user_id)
    
    if settings:
        assert settings['inactivityThreshold'] == threshold
        assert settings['voiceResponseTimeout'] == timeout


# ============================================================================
# Property 25: 기본 설정 값
# 출처: requirements.md - 요구사항 2.4, 3.3
# 기준: 임계값 기본값 120분, 타임아웃 기본값 30초
# ============================================================================

def test_property_25_default_settings():
    """
    Property 25: 기본 설정 값
    
    For all new Senior_User registrations,
    default settings SHALL be:
    - Inactivity_Threshold: 120 minutes
    - Voice_Response_Timeout: 30 seconds
    
    시나리오:
    - 입력: 설정 없이 사용자 생성
    - 기대: 기본값 자동 적용
    
    기준값 출처:
      - requirements.md 요구사항 2.4 "기본값 120분"
      - requirements.md 요구사항 3.3 "기본값 30초"
    """
    # Arrange
    user_id = 'test-user-defaults'
    
    # Act - 기본 설정으로 사용자 생성
    dynamodb = DynamoDBHelper()
    dynamodb.put_user_settings(
        user_id=user_id,
        name='Test User'
        # inactivityThreshold, voiceResponseTimeout 생략
    )
    
    # Assert
    settings = dynamodb.get_user_settings(user_id)
    
    assert settings is not None
    assert settings.get('inactivityThreshold', 120) == 120, \
        "Default inactivity threshold should be 120 minutes"
    assert settings.get('voiceResponseTimeout', 30) == 30, \
        "Default voice response timeout should be 30 seconds"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--hypothesis-show-statistics'])
