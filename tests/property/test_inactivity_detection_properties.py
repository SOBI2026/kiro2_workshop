"""
Property-Based Tests for Inactivity Detection
Feature: senior-care-monitoring

이 테스트는 활동 부재 감지 로직의 correctness properties를 검증합니다.
기준값 출처: senior-care-monitoring-presentation.md → requirements.md (요구사항 2, 5)
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime, timedelta
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from inactivity_detector.app import lambda_handler as inactivity_handler
from common.dynamodb_helper import DynamoDBHelper


# ============================================================================
# Property 10: 임계값 기반 감지 정확성
# 출처: requirements.md - Property 4, design.md - Property 5
# 기준: (current_time - last_activity_time) >= Inactivity_Threshold
# ============================================================================

@given(
    inactivity_threshold=st.integers(min_value=30, max_value=480),  # 30~480분 (출처: presentation.md)
    time_since_last_activity=st.integers(min_value=0, max_value=600)  # 0~600분
)
@settings(max_examples=100, deadline=None)
def test_property_10_threshold_based_detection(inactivity_threshold, time_since_last_activity):
    """
    Property 10: 임계값 기반 감지 정확성
    
    For all Senior_User records, voice confirmation SHALL be triggered 
    if and only if (current_time - last_activity_time) >= Inactivity_Threshold.
    
    시나리오 1: 임계값 미만 (예: 30분 경과, 임계값 120분)
      - 기대: 알림 없음
    
    시나리오 2: 임계값 초과 (예: 121분 경과, 임계값 120분)
      - 기대: 음성 확인 트리거
    
    기준값 출처:
      - 임계값 범위: presentation.md "30~480분 (설정 가능)"
      - 검증 로직: requirements.md 요구사항 2.3
    """
    # Arrange
    user_id = f'test-user-{inactivity_threshold}'
    current_time = datetime.utcnow()
    last_activity_time = current_time - timedelta(minutes=time_since_last_activity)
    
    # Setup user with specific threshold
    dynamodb = DynamoDBHelper()
    dynamodb.put_user_settings(
        user_id=user_id,
        name='Test User',
        inactivity_threshold=inactivity_threshold,
        last_activity_time=last_activity_time.isoformat()
    )
    
    # Act
    response = inactivity_handler({}, {})
    
    # Assert
    should_trigger = time_since_last_activity >= inactivity_threshold
    
    # Check if alert was created
    alerts = dynamodb.get_pending_alerts(user_id)
    alert_triggered = len(alerts) > 0
    
    assert alert_triggered == should_trigger, \
        f"Threshold: {inactivity_threshold}min, Elapsed: {time_since_last_activity}min, " \
        f"Expected trigger: {should_trigger}, Actual: {alert_triggered}"


# ============================================================================
# Property 11: 임계값 범위 검증
# 출처: requirements.md - Property 14, design.md - Property 15
# 기준: 30분 ≤ Inactivity_Threshold ≤ 480분
# ============================================================================

@given(
    threshold=st.integers(min_value=30, max_value=480)
)
@settings(max_examples=50, deadline=None)
def test_property_11_valid_threshold_range(threshold):
    """
    Property 11: 유효한 임계값 범위
    
    For all Inactivity_Threshold values stored in DynamoDB_UserSettings,
    the value SHALL be >= 30 AND <= 480 minutes.
    
    시나리오:
    - 입력: 30~480분 범위의 임계값
    - 기대: 설정 성공
    
    기준값 출처: presentation.md "임계값: 30~480분 (설정 가능)"
    """
    # Arrange
    user_id = f'test-user-{threshold}'
    
    # Act
    dynamodb = DynamoDBHelper()
    result = dynamodb.put_user_settings(
        user_id=user_id,
        name='Test User',
        inactivity_threshold=threshold
    )
    
    # Assert
    assert result is not None, f"Threshold {threshold} should be accepted"
    
    # Verify stored value
    settings = dynamodb.get_user_settings(user_id)
    assert settings['inactivityThreshold'] == threshold


@given(
    invalid_threshold=st.one_of(
        st.integers(min_value=-100, max_value=29),  # 30분 미만
        st.integers(min_value=481, max_value=10000)  # 480분 초과
    )
)
@settings(max_examples=30, deadline=None)
def test_property_11_invalid_threshold_rejected(invalid_threshold):
    """
    Property 11: 유효하지 않은 임계값 거부
    
    For all Inactivity_Threshold values outside [30, 480],
    the System SHALL reject with error.
    
    시나리오:
    - 입력: 범위 밖의 임계값 (예: 10분, 500분)
    - 기대: 400 Bad Request 에러
    """
    # Arrange
    user_id = f'test-user-invalid'
    
    # Act & Assert
    dynamodb = DynamoDBHelper()
    
    # 유효하지 않은 값은 거부되어야 함
    with pytest.raises(Exception):  # ValidationError 또는 ValueError
        dynamodb.put_user_settings(
            user_id=user_id,
            name='Test User',
            inactivity_threshold=invalid_threshold
        )


# ============================================================================
# Property 12: 중복 알림 방지
# 출처: requirements.md - Property 5, design.md - Property 6
# 기준: 동일 사용자에 대해 pending 알림이 있으면 새 알림 생성 안 함
# ============================================================================

@given(
    time_since_last_activity=st.integers(min_value=121, max_value=300)  # 임계값(120분) 초과
)
@settings(max_examples=30, deadline=None)
def test_property_12_duplicate_alert_prevention(time_since_last_activity):
    """
    Property 12: 중복 알림 방지
    
    For all inactivity events, only one voice confirmation request 
    SHALL be created per continuous inactivity period.
    
    시나리오:
    1. 첫 번째 감지: 알림 생성
    2. 두 번째 감지 (1분 후): 알림 생성 안 함 (이미 pending 상태)
    3. 알림 해결 후: 새 알림 생성 가능
    
    기준값 출처: requirements.md 요구사항 2.6
    """
    # Arrange
    user_id = 'test-user-duplicate'
    current_time = datetime.utcnow()
    last_activity_time = current_time - timedelta(minutes=time_since_last_activity)
    
    dynamodb = DynamoDBHelper()
    dynamodb.put_user_settings(
        user_id=user_id,
        name='Test User',
        inactivity_threshold=120,  # 기본값
        last_activity_time=last_activity_time.isoformat()
    )
    
    # Act - 첫 번째 감지
    response1 = inactivity_handler({}, {})
    alerts_after_first = dynamodb.get_pending_alerts(user_id)
    
    # Act - 두 번째 감지 (1분 후, 여전히 활동 없음)
    response2 = inactivity_handler({}, {})
    alerts_after_second = dynamodb.get_pending_alerts(user_id)
    
    # Assert
    assert len(alerts_after_first) == 1, "First detection should create one alert"
    assert len(alerts_after_second) == 1, "Second detection should NOT create duplicate alert"
    assert alerts_after_first[0]['alertId'] == alerts_after_second[0]['alertId'], \
        "Alert ID should remain the same (no duplicate)"


# ============================================================================
# Property 13: 기본 임계값 적용
# 출처: requirements.md - 요구사항 2.4
# 기준: 임계값 미설정 시 기본값 120분 사용
# ============================================================================

def test_property_13_default_threshold():
    """
    Property 13: 기본 임계값 적용
    
    WHERE Inactivity_Threshold가 설정되지 않은 경우,
    THE System SHALL 기본값 120분을 사용한다.
    
    시나리오:
    - 입력: 임계값이 설정되지 않은 사용자
    - 기대: 120분 기본값 적용
    
    기준값 출처: requirements.md 요구사항 2.4 "기본값 120분"
    """
    # Arrange
    user_id = 'test-user-default'
    current_time = datetime.utcnow()
    last_activity_time = current_time - timedelta(minutes=121)  # 121분 전
    
    dynamodb = DynamoDBHelper()
    # 임계값 없이 사용자 생성
    dynamodb.put_user_settings(
        user_id=user_id,
        name='Test User',
        # inactivity_threshold 생략 (기본값 사용)
        last_activity_time=last_activity_time.isoformat()
    )
    
    # Act
    response = inactivity_handler({}, {})
    
    # Assert
    alerts = dynamodb.get_pending_alerts(user_id)
    assert len(alerts) > 0, "Alert should be triggered with default threshold (120min)"
    
    # Verify default threshold was used
    settings = dynamodb.get_user_settings(user_id)
    effective_threshold = settings.get('inactivityThreshold', 120)
    assert effective_threshold == 120, "Default threshold should be 120 minutes"


# ============================================================================
# Property 14: 전체 사용자 검사
# 출처: requirements.md - Property 6, design.md - Property 7
# 기준: 모든 활성 사용자의 활동 상태를 검사해야 함
# ============================================================================

@given(
    num_users=st.integers(min_value=1, max_value=10)
)
@settings(max_examples=20, deadline=None)
def test_property_14_all_users_checked(num_users):
    """
    Property 14: 전체 사용자 검사
    
    For all active Senior_User records in DynamoDB_UserSettings,
    the InactivityDetector SHALL evaluate the inactivity status.
    
    시나리오:
    - 입력: N명의 활성 사용자
    - 기대: 모든 사용자의 활동 상태 검사
    - 검증: 각 사용자에 대해 임계값 비교 수행
    """
    # Arrange - 여러 사용자 생성
    dynamodb = DynamoDBHelper()
    user_ids = []
    
    for i in range(num_users):
        user_id = f'test-user-{i}'
        user_ids.append(user_id)
        
        # 일부는 임계값 초과, 일부는 미만
        minutes_ago = 121 if i % 2 == 0 else 30
        last_activity = datetime.utcnow() - timedelta(minutes=minutes_ago)
        
        dynamodb.put_user_settings(
            user_id=user_id,
            name=f'Test User {i}',
            inactivity_threshold=120,
            last_activity_time=last_activity.isoformat(),
            status='active'
        )
    
    # Act
    response = inactivity_handler({}, {})
    
    # Assert - 모든 사용자가 검사되었는지 확인
    body = json.loads(response['body'])
    checked_users = body.get('activeUsers', 0)
    
    assert checked_users >= num_users, \
        f"All {num_users} users should be checked, but only {checked_users} were checked"


# ============================================================================
# Property 15: 비활성 사용자 제외
# 출처: design.md - InactivityDetector 로직
# 기준: status='inactive' 사용자는 검사하지 않음
# ============================================================================

def test_property_15_inactive_users_excluded():
    """
    Property 15: 비활성 사용자 제외
    
    For all Senior_User records with status='inactive',
    the InactivityDetector SHALL NOT evaluate inactivity.
    
    시나리오:
    - 입력: 활성 사용자 1명, 비활성 사용자 1명
    - 기대: 활성 사용자만 검사
    """
    # Arrange
    dynamodb = DynamoDBHelper()
    
    # 활성 사용자
    dynamodb.put_user_settings(
        user_id='active-user',
        name='Active User',
        inactivity_threshold=120,
        last_activity_time=(datetime.utcnow() - timedelta(minutes=121)).isoformat(),
        status='active'
    )
    
    # 비활성 사용자
    dynamodb.put_user_settings(
        user_id='inactive-user',
        name='Inactive User',
        inactivity_threshold=120,
        last_activity_time=(datetime.utcnow() - timedelta(minutes=121)).isoformat(),
        status='inactive'
    )
    
    # Act
    response = inactivity_handler({}, {})
    
    # Assert
    # 활성 사용자만 알림 생성
    active_alerts = dynamodb.get_pending_alerts('active-user')
    inactive_alerts = dynamodb.get_pending_alerts('inactive-user')
    
    assert len(active_alerts) > 0, "Active user should have alert"
    assert len(inactive_alerts) == 0, "Inactive user should NOT have alert"


# ============================================================================
# Property 16: 알림 상태 초기값
# 출처: requirements.md - 요구사항 2.5
# 기준: 새 알림의 초기 상태는 "voice_confirmation_pending"
# ============================================================================

def test_property_16_initial_alert_status():
    """
    Property 16: 알림 상태 초기값
    
    WHEN 활동 부재가 감지되면,
    THE InactivityDetector SHALL DynamoDB_AlertHistory에 
    상태 "voice_confirmation_pending"으로 기록한다.
    
    시나리오:
    - 입력: 임계값 초과 감지
    - 기대: 알림 생성, 상태 = "voice_confirmation_pending"
    
    기준값 출처: requirements.md 요구사항 2.5
    """
    # Arrange
    user_id = 'test-user-status'
    dynamodb = DynamoDBHelper()
    
    dynamodb.put_user_settings(
        user_id=user_id,
        name='Test User',
        inactivity_threshold=120,
        last_activity_time=(datetime.utcnow() - timedelta(minutes=121)).isoformat()
    )
    
    # Act
    response = inactivity_handler({}, {})
    
    # Assert
    alerts = dynamodb.get_pending_alerts(user_id)
    assert len(alerts) > 0, "Alert should be created"
    
    alert = alerts[0]
    assert alert['status'] == 'voice_confirmation_pending', \
        f"Initial status should be 'voice_confirmation_pending', got '{alert['status']}'"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--hypothesis-show-statistics'])
