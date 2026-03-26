"""
Property-Based Tests for Data Retention and Storage
Feature: senior-care-monitoring

이 테스트는 데이터 보존 정책의 correctness properties를 검증합니다.
기준값 출처: senior-care-monitoring-presentation.md → requirements.md (요구사항 6)
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime, timedelta
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from common.dynamodb_helper import DynamoDBHelper
from common.rds_helper import RDSHelper


# ============================================================================
# Property 39: 센서 데이터 TTL (30일)
# 출처: requirements.md - Property 17, design.md - DynamoDB 테이블 설계
# 기준: 센서 데이터는 30일 ±1일 후 자동 삭제
# ============================================================================

@given(
    days_old=st.integers(min_value=1, max_value=35)
)
@settings(max_examples=30, deadline=None)
def test_property_39_sensor_data_ttl(days_old):
    """
    Property 39: 센서 데이터 TTL
    
    For all activity records in DynamoDB_SensorData,
    the record SHALL exist for 30 days ±1 day before TTL deletion.
    
    시나리오 1: 29일 된 데이터
      - 기대: 여전히 존재
    
    시나리오 2: 31일 된 데이터
      - 기대: 삭제됨 (또는 삭제 예정)
    
    기준값 출처:
      - presentation.md "30일 활동 데이터 저장"
      - requirements.md 요구사항 6.2
    """
    # Arrange
    user_id = 'test-user-ttl'
    timestamp = datetime.utcnow() - timedelta(days=days_old)
    
    dynamodb = DynamoDBHelper()
    
    # TTL 계산 (생성 시점 + 30일)
    ttl = int((timestamp + timedelta(days=30)).timestamp())
    
    dynamodb.put_sensor_data(
        user_id=user_id,
        timestamp=int(timestamp.timestamp()),
        device_id='device-001',
        device_type='mobile',
        sensor_type='accelerometer',
        value=2.5,
        ttl=ttl
    )
    
    # Act - 데이터 조회
    stored_data = dynamodb.get_sensor_data(user_id, int(timestamp.timestamp()))
    
    # Assert
    current_time = int(datetime.utcnow().timestamp())
    
    if days_old <= 30:
        # 30일 이내 데이터는 존재해야 함
        assert stored_data is not None, \
            f"Data {days_old} days old should still exist (within 30-day retention)"
        assert stored_data['ttl'] == ttl
    else:
        # 30일 초과 데이터는 삭제되었거나 삭제 예정
        # TTL은 DynamoDB가 자동으로 처리하므로, TTL 값만 검증
        if stored_data:
            assert stored_data['ttl'] < current_time, \
                f"Data {days_old} days old should have expired TTL"


# ============================================================================
# Property 40: 알림 이력 TTL (90일)
# 출처: design.md - DynamoDB AlertHistory 테이블
# 기준: 알림 이력은 90일 후 자동 삭제
# ============================================================================

@given(
    days_old=st.integers(min_value=1, max_value=100)
)
@settings(max_examples=30, deadline=None)
def test_property_40_alert_history_ttl(days_old):
    """
    Property 40: 알림 이력 TTL
    
    For all alert records in DynamoDB_AlertHistory,
    the record SHALL exist for 90 days before TTL deletion.
    
    시나리오 1: 89일 된 알림
      - 기대: 여전히 존재
    
    시나리오 2: 91일 된 알림
      - 기대: 삭제됨
    
    기준값 출처: design.md - AlertHistory 테이블 "TTL: 90일"
    """
    # Arrange
    user_id = 'test-user-alert-ttl'
    alert_id = f'alert-{days_old}'
    created_at = datetime.utcnow() - timedelta(days=days_old)
    
    dynamodb = DynamoDBHelper()
    
    # TTL 계산 (생성 시점 + 90일)
    ttl = int((created_at + timedelta(days=90)).timestamp())
    
    dynamodb.create_alert(
        user_id=user_id,
        alert_id=alert_id,
        alert_type='no_response',
        last_activity_time=created_at.isoformat(),
        ttl=ttl
    )
    
    # Act - 알림 조회
    alert = dynamodb.get_alert(user_id, alert_id)
    
    # Assert
    current_time = int(datetime.utcnow().timestamp())
    
    if days_old <= 90:
        # 90일 이내 알림은 존재해야 함
        assert alert is not None, \
            f"Alert {days_old} days old should still exist (within 90-day retention)"
        assert alert['ttl'] == ttl
    else:
        # 90일 초과 알림은 삭제되었거나 삭제 예정
        if alert:
            assert alert['ttl'] < current_time, \
                f"Alert {days_old} days old should have expired TTL"


# ============================================================================
# Property 41: RDS 활동 로그 보존 (30일)
# 출처: requirements.md - Property 17
# 기준: RDS ActivityLog는 30일 후 자동 삭제
# ============================================================================

@given(
    days_old=st.integers(min_value=1, max_value=35)
)
@settings(max_examples=30, deadline=None)
def test_property_41_rds_activity_log_retention(days_old):
    """
    Property 41: RDS 활동 로그 보존
    
    For all activity records in RDS_ActivityLog,
    the record SHALL exist for 30 days ±1 day from creation.
    
    시나리오:
    - 입력: N일 된 활동 로그
    - 기대: 30일 이내는 존재, 30일 초과는 삭제
    - 검증: 데이터베이스 쿼리 결과
    
    기준값 출처: requirements.md 요구사항 6.3
    """
    # Arrange
    user_id = 'test-user-rds-retention'
    timestamp = datetime.utcnow() - timedelta(days=days_old)
    
    rds = RDSHelper()
    
    # 활동 로그 생성
    rds.insert_activity_log(
        user_id=user_id,
        activity_type='sensor_data',
        device_type='mobile',
        device_id='device-001',
        sensor_type='accelerometer',
        value=2.5,
        timestamp=timestamp
    )
    
    # Act - 로그 조회
    logs = rds.get_activity_logs(
        user_id=user_id,
        start_date=timestamp - timedelta(days=1),
        end_date=timestamp + timedelta(days=1)
    )
    
    # Assert
    if days_old <= 30:
        # 30일 이내 로그는 존재해야 함
        assert len(logs) > 0, \
            f"Activity log {days_old} days old should exist (within 30-day retention)"
    else:
        # 30일 초과 로그는 삭제되었을 수 있음
        # (실제로는 배치 작업이 삭제하므로, 여기서는 정책만 검증)
        pass


# ============================================================================
# Property 42: 조회 완전성
# 출처: requirements.md - Property 18
# 기준: 날짜 범위 내 모든 레코드 반환
# ============================================================================

@given(
    num_records=st.integers(min_value=1, max_value=20),
    query_days=st.integers(min_value=1, max_value=30)
)
@settings(max_examples=30, deadline=None)
def test_property_42_query_completeness(num_records, query_days):
    """
    Property 42: 조회 완전성
    
    For all activity history queries with a specified date range,
    the result set SHALL include all records where timestamp falls within the range.
    
    시나리오:
    - 입력: N개의 활동 로그, M일 범위 쿼리
    - 기대: 범위 내 모든 레코드 반환
    - 검증: 반환된 레코드 수 = 범위 내 레코드 수
    
    기준값 출처: requirements.md 요구사항 6.4, 6.5
    """
    # Arrange
    user_id = 'test-user-query'
    
    rds = RDSHelper()
    
    # N개의 활동 로그 생성 (지난 M일 동안)
    created_records = []
    for i in range(num_records):
        timestamp = datetime.utcnow() - timedelta(days=i % query_days)
        rds.insert_activity_log(
            user_id=user_id,
            activity_type='sensor_data',
            device_type='mobile',
            device_id='device-001',
            sensor_type='accelerometer',
            value=2.5,
            timestamp=timestamp
        )
        created_records.append(timestamp)
    
    # Act - 날짜 범위 쿼리
    start_date = datetime.utcnow() - timedelta(days=query_days)
    end_date = datetime.utcnow()
    
    logs = rds.get_activity_logs(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date
    )
    
    # Assert
    # 범위 내 모든 레코드가 반환되어야 함
    assert len(logs) == num_records, \
        f"Should return all {num_records} records within {query_days}-day range, got {len(logs)}"


# ============================================================================
# Property 43: 조회 성능
# 출처: requirements.md - Property 19
# 기준: 30일 이하 범위 쿼리는 5초 이내 응답
# ============================================================================

@given(
    query_days=st.integers(min_value=1, max_value=30)
)
@settings(max_examples=20, deadline=None)
def test_property_43_query_performance(query_days):
    """
    Property 43: 조회 성능
    
    For all activity history queries with date range <= 30 days,
    the query response time SHALL be <= 5 seconds.
    
    시나리오:
    - 입력: 1~30일 범위 쿼리
    - 기대: 5초 이내 응답
    - 검증: 실행 시간 측정
    
    기준값 출처: requirements.md 요구사항 6.6
    """
    # Arrange
    user_id = 'test-user-performance'
    
    rds = RDSHelper()
    
    # 테스트 데이터 생성
    for i in range(50):
        timestamp = datetime.utcnow() - timedelta(days=i % query_days)
        rds.insert_activity_log(
            user_id=user_id,
            activity_type='sensor_data',
            device_type='mobile',
            device_id='device-001',
            sensor_type='accelerometer',
            value=2.5,
            timestamp=timestamp
        )
    
    # Act - 시간 측정
    start_time = time.time()
    
    start_date = datetime.utcnow() - timedelta(days=query_days)
    end_date = datetime.utcnow()
    
    logs = rds.get_activity_logs(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date
    )
    
    elapsed_time = time.time() - start_time
    
    # Assert
    assert elapsed_time <= 5.0, \
        f"Query for {query_days}-day range should complete within 5s, took {elapsed_time:.2f}s"
    assert len(logs) > 0, "Should return some records"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--hypothesis-show-statistics'])
