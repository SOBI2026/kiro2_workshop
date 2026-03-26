"""
Property-Based Tests for Voice Response Handling
Feature: senior-care-monitoring

이 테스트는 AI 스피커 음성 확인의 correctness properties를 검증합니다.
기준값 출처: senior-care-monitoring-presentation.md → requirements.md (요구사항 3)
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime, timedelta
import json
import time
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from voice_response_handler.app import lambda_handler as voice_handler
from common.dynamodb_helper import DynamoDBHelper


# ============================================================================
# Property 26: 타임아웃 정확성
# 출처: requirements.md - Property 7, design.md - Property 8
# 기준: 대기 시간이 설정된 Voice_Response_Timeout의 ±2초 이내
# ============================================================================

@given(
    timeout=st.integers(min_value=10, max_value=60)
)
@settings(max_examples=30, deadline=None)
def test_property_26_timeout_accuracy(timeout):
    """
    Property 26: 타임아웃 정확성
    
    For all voice confirmation requests, the wait duration 
    SHALL be within ±2 seconds of the configured Voice_Response_Timeout value.
    
    시나리오:
    - 입력: Voice_Response_Timeout = N초
    - 기대: 실제 대기 시간 = N ± 2초
    - 검증: 타임아웃 시간 측정
    
    기준값 출처:
      - presentation.md "응답 대기: 10~60초 (설정 가능)"
      - requirements.md 요구사항 3.2, 3.3
    """
    # Arrange
    user_id = f'test-user-timeout-{timeout}'
    alert_id = f'alert-{int(time.time())}'
    
    dynamodb = DynamoDBHelper()
    dynamodb.put_user_settings(
        user_id=user_id,
        name='Test User',
        voice_response_timeout=timeout
    )
    
    dynamodb.create_alert(
        user_id=user_id,
        alert_id=alert_id,
        alert_type='no_response',
        last_activity_time=datetime.utcnow().isoformat()
    )
    
    event = {
        'userId': user_id,
        'alertId': alert_id
    }
    
    # Act - 시간 측정
    start_time = time.time()
    response = voice_handler(event, {})
    elapsed_time = time.time() - start_time
    
    # Assert
    # 타임아웃 시간이 설정값의 ±2초 이내
    assert abs(elapsed_time - timeout) <= 2.0, \
        f"Timeout should be {timeout}±2s, but was {elapsed_time:.2f}s"


# ============================================================================
# Property 27: 상태 전이 일관성
# 출처: requirements.md - Property 8, design.md - Property 9
# 기준: voice_confirmation_pending → confirmed_safe 또는 no_response
# ============================================================================

@given(
    response_received=st.booleans()
)
@settings(max_examples=50, deadline=None)
def test_property_27_state_transition_consistency(response_received):
    """
    Property 27: 상태 전이 일관성
    
    For all voice confirmation requests, the alert status SHALL transition 
    from "voice_confirmation_pending" to either "confirmed_safe" (if response) 
    or "no_response" (if timeout).
    
    시나리오 1: 응답 수신
      - 초기 상태: voice_confirmation_pending
      - 최종 상태: confirmed_safe
    
    시나리오 2: 응답 없음 (타임아웃)
      - 초기 상태: voice_confirmation_pending
      - 최종 상태: no_response
    
    기준값 출처: requirements.md 요구사항 3.4, 3.5
    """
    # Arrange
    user_id = 'test-user-transition'
    alert_id = f'alert-{int(time.time())}'
    
    dynamodb = DynamoDBHelper()
    
    # 초기 상태: voice_confirmation_pending
    dynamodb.create_alert(
        user_id=user_id,
        alert_id=alert_id,
        alert_type='no_response',
        last_activity_time=datetime.utcnow().isoformat(),
        status='voice_confirmation_pending'
    )
    
    event = {
        'userId': user_id,
        'alertId': alert_id
    }
    
    if response_received:
        # 응답 수신 시뮬레이션
        event['response'] = '네, 괜찮아요'
        event['timestamp'] = datetime.utcnow().isoformat()
    
    # Act
    response = voice_handler(event, {})
    
    # Assert
    alert = dynamodb.get_alert(user_id, alert_id)
    
    if response_received:
        assert alert['status'] == 'confirmed_safe', \
            f"Status should be 'confirmed_safe' when response received, got '{alert['status']}'"
    else:
        assert alert['status'] == 'no_response', \
            f"Status should be 'no_response' when timeout, got '{alert['status']}'"


# ============================================================================
# Property 28: 유효한 응답 인식
# 출처: requirements.md - Property 9, design.md - Property 10
# 기준: 타임아웃 내 유효한 응답은 인식되어야 함
# ============================================================================

@given(
    response_text=st.sampled_from([
        '네', '괜찮아요', '네, 괜찮아요', '예', '좋아요',
        'yes', 'ok', 'fine', 'I am okay'
    ]),
    response_delay=st.integers(min_value=1, max_value=25)  # 타임아웃(30초) 내
)
@settings(max_examples=30, deadline=None)
def test_property_28_valid_response_recognition(response_text, response_delay):
    """
    Property 28: 유효한 응답 인식
    
    For all valid voice responses received within Voice_Response_Timeout,
    the VoiceResponseHandler SHALL recognize and process the response.
    
    시나리오:
    - 입력: 타임아웃(30초) 내 유효한 응답
    - 기대: 응답 인식, 상태 = confirmed_safe
    - 검증: voiceResponse 필드에 응답 저장
    
    기준값 출처: requirements.md 요구사항 3.4
    """
    # Arrange
    user_id = 'test-user-response'
    alert_id = f'alert-{int(time.time())}'
    
    dynamodb = DynamoDBHelper()
    dynamodb.put_user_settings(
        user_id=user_id,
        name='Test User',
        voice_response_timeout=30
    )
    
    dynamodb.create_alert(
        user_id=user_id,
        alert_id=alert_id,
        alert_type='no_response',
        last_activity_time=datetime.utcnow().isoformat()
    )
    
    # 응답 시간 시뮬레이션
    response_time = datetime.utcnow() + timedelta(seconds=response_delay)
    
    event = {
        'userId': user_id,
        'alertId': alert_id,
        'response': response_text,
        'timestamp': response_time.isoformat()
    }
    
    # Act
    response = voice_handler(event, {})
    
    # Assert
    assert response['statusCode'] == 200
    
    alert = dynamodb.get_alert(user_id, alert_id)
    assert alert['status'] == 'confirmed_safe'
    assert alert.get('voiceResponse') == response_text


# ============================================================================
# Property 29: 타임아웃 후 응답 무시
# 출처: design.md - VoiceResponseHandler 로직
# 기준: 타임아웃 이후 응답은 무시되어야 함
# ============================================================================

@given(
    response_delay=st.integers(min_value=31, max_value=120)  # 타임아웃(30초) 초과
)
@settings(max_examples=20, deadline=None)
def test_property_29_late_response_ignored(response_delay):
    """
    Property 29: 타임아웃 후 응답 무시
    
    For all voice responses received after Voice_Response_Timeout,
    the response SHALL be ignored and status remains "no_response".
    
    시나리오:
    - 입력: 타임아웃(30초) 이후 응답 (예: 35초 후)
    - 기대: 응답 무시, 상태 = no_response
    - 검증: 상태가 변경되지 않음
    
    기준값 출처: design.md - VoiceResponseHandler 타임아웃 관리
    """
    # Arrange
    user_id = 'test-user-late'
    alert_id = f'alert-{int(time.time())}'
    
    dynamodb = DynamoDBHelper()
    dynamodb.put_user_settings(
        user_id=user_id,
        name='Test User',
        voice_response_timeout=30
    )
    
    # 이미 타임아웃된 알림
    dynamodb.create_alert(
        user_id=user_id,
        alert_id=alert_id,
        alert_type='no_response',
        last_activity_time=datetime.utcnow().isoformat(),
        status='no_response'  # 이미 타임아웃됨
    )
    
    # 늦은 응답
    response_time = datetime.utcnow() + timedelta(seconds=response_delay)
    
    event = {
        'userId': user_id,
        'alertId': alert_id,
        'response': '네, 괜찮아요',
        'timestamp': response_time.isoformat()
    }
    
    # Act
    response = voice_handler(event, {})
    
    # Assert
    # 늦은 응답은 무시되어야 함
    alert = dynamodb.get_alert(user_id, alert_id)
    assert alert['status'] == 'no_response', \
        "Late response should be ignored, status should remain 'no_response'"


# ============================================================================
# Property 30: AI 스피커 API 실패 시 즉시 알림
# 출처: requirements.md - 요구사항 3.6
# 기준: API 호출 실패 시 음성 확인 건너뛰고 즉시 NotificationManager 트리거
# ============================================================================

def test_property_30_api_failure_immediate_notification():
    """
    Property 30: AI 스피커 API 실패 시 즉시 알림
    
    WHEN AI_Speaker API 호출이 실패하면,
    THE VoiceResponseHandler SHALL 즉시 NotificationManager를 트리거한다.
    
    시나리오:
    - 입력: AI 스피커 API 호출 실패
    - 기대: 음성 확인 건너뛰기, 즉시 보호자 알림
    - 검증: 상태 = no_response, NotificationManager 호출됨
    
    기준값 출처: requirements.md 요구사항 3.6
    """
    # Arrange
    user_id = 'test-user-api-fail'
    alert_id = f'alert-{int(time.time())}'
    
    dynamodb = DynamoDBHelper()
    dynamodb.create_alert(
        user_id=user_id,
        alert_id=alert_id,
        alert_type='no_response',
        last_activity_time=datetime.utcnow().isoformat()
    )
    
    # AI 스피커 API 실패 시뮬레이션
    event = {
        'userId': user_id,
        'alertId': alert_id,
        'apiFailure': True  # API 실패 플래그
    }
    
    # Act
    response = voice_handler(event, {})
    
    # Assert
    # API 실패 시 즉시 no_response 상태로 전환
    alert = dynamodb.get_alert(user_id, alert_id)
    assert alert['status'] == 'no_response', \
        "API failure should immediately set status to 'no_response'"
    
    # NotificationManager가 트리거되었는지 확인 (통합 테스트에서 검증)
    assert response['statusCode'] == 200


# ============================================================================
# Property 31: 기본 타임아웃 적용
# 출처: requirements.md - 요구사항 3.3
# 기준: Voice_Response_Timeout 미설정 시 기본값 30초 사용
# ============================================================================

def test_property_31_default_voice_timeout():
    """
    Property 31: 기본 음성 응답 타임아웃
    
    WHEN Voice_Response_Timeout이 설정되지 않은 경우,
    THE System SHALL 기본값 30초를 사용한다.
    
    시나리오:
    - 입력: 타임아웃 미설정 사용자
    - 기대: 30초 기본값 적용
    - 검증: 실제 대기 시간 = 30 ± 2초
    
    기준값 출처: requirements.md 요구사항 3.3 "기본값 30초"
    """
    # Arrange
    user_id = 'test-user-default-timeout'
    alert_id = f'alert-{int(time.time())}'
    
    dynamodb = DynamoDBHelper()
    # voice_response_timeout 없이 사용자 생성
    dynamodb.put_user_settings(
        user_id=user_id,
        name='Test User'
        # voice_response_timeout 생략
    )
    
    dynamodb.create_alert(
        user_id=user_id,
        alert_id=alert_id,
        alert_type='no_response',
        last_activity_time=datetime.utcnow().isoformat()
    )
    
    event = {
        'userId': user_id,
        'alertId': alert_id
    }
    
    # Act
    start_time = time.time()
    response = voice_handler(event, {})
    elapsed_time = time.time() - start_time
    
    # Assert
    # 기본값 30초가 적용되어야 함
    assert abs(elapsed_time - 30) <= 2.0, \
        f"Default timeout should be 30±2s, but was {elapsed_time:.2f}s"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--hypothesis-show-statistics'])
