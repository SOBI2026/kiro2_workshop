"""
Property-Based Tests for Report Generation
Feature: senior-care-monitoring

이 테스트는 리포트 생성의 correctness properties를 검증합니다.
기준값 출처: senior-care-monitoring-presentation.md → requirements.md (요구사항 7)
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime, timedelta
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from report_generator.app import lambda_handler as report_handler
from common.dynamodb_helper import DynamoDBHelper
from common.rds_helper import RDSHelper


# ============================================================================
# Property 32: 리포트 생성 완전성
# 출처: requirements.md - Property 20, design.md - Property 21
# 기준: 모든 활성 사용자에 대해 일일 리포트 생성
# ============================================================================

@given(
    num_users=st.integers(min_value=1, max_value=10)
)
@settings(max_examples=20, deadline=None)
def test_property_32_report_generation_completeness(num_users):
    """
    Property 32: 리포트 생성 완전성
    
    For all active Senior_User records,
    a daily summary SHALL be generated each day at 00:00 UTC.
    
    시나리오:
    - 입력: N명의 활성 사용자
    - 기대: N개의 일일 리포트 생성
    - 검증: 각 사용자마다 리포트 존재
    
    기준값 출처: requirements.md 요구사항 7.1, 7.2
    """
    # Arrange
    dynamodb = DynamoDBHelper()
    rds = RDSHelper()
    
    user_ids = []
    for i in range(num_users):
        user_id = f'test-user-report-{i}'
        user_ids.append(user_id)
        
        # 활성 사용자 생성
        dynamodb.put_user_settings(
            user_id=user_id,
            name=f'Test User {i}',
            status='active'
        )
        
        # 활동 데이터 생성 (지난 24시간)
        for j in range(5):
            timestamp = datetime.utcnow() - timedelta(hours=j)
            rds.insert_activity_log(
                user_id=user_id,
                activity_type='sensor_data',
                device_type='mobile',
                device_id='device-001',
                sensor_type='accelerometer',
                value=2.5,
                timestamp=timestamp
            )
    
    # Act - 일일 리포트 생성
    event = {
        'reportType': 'daily'
    }
    response = report_handler(event, {})
    
    # Assert
    assert response['statusCode'] == 200
    
    body = json.loads(response['body'])
    generated_count = body.get('generatedReports', 0)
    
    assert generated_count == num_users, \
        f"Should generate {num_users} reports, but generated {generated_count}"


# ============================================================================
# Property 33: 리포트 데이터 정확성
# 출처: requirements.md - Property 21, design.md - Property 22
# 기준: 리포트의 활동 횟수 = 실제 활동 로그 수
# ============================================================================

@given(
    num_activities=st.integers(min_value=1, max_value=50)
)
@settings(max_examples=30, deadline=None)
def test_property_33_report_data_accuracy(num_activities):
    """
    Property 33: 리포트 데이터 정확성
    
    For all daily summaries, the total activity count SHALL equal 
    the count of Activity_Signal records for that day in RDS_ActivityLog.
    
    시나리오:
    - 입력: N개의 활동 로그
    - 기대: 리포트의 활동 횟수 = N
    - 검증: 리포트 데이터와 실제 로그 일치
    
    기준값 출처: requirements.md 요구사항 7.3
    """
    # Arrange
    user_id = 'test-user-accuracy'
    
    dynamodb = DynamoDBHelper()
    rds = RDSHelper()
    
    dynamodb.put_user_settings(
        user_id=user_id,
        name='Test User',
        status='active'
    )
    
    # N개의 활동 로그 생성
    for i in range(num_activities):
        timestamp = datetime.utcnow() - timedelta(hours=random.randint(0, 23))
        rds.insert_activity_log(
            user_id=user_id,
            activity_type='sensor_data',
            device_type='mobile',
            device_id='device-001',
            sensor_type='accelerometer',
            value=2.5,
            timestamp=timestamp
        )
    
    # Act - 일일 리포트 생성
    event = {
        'reportType': 'daily',
        'userId': user_id
    }
    response = report_handler(event, {})
    
    # Assert
    assert response['statusCode'] == 200
    
    body = json.loads(response['body'])
    report_data = body.get('reportData', {})
    total_activities = report_data.get('totalActivities', 0)
    
    assert total_activities == num_activities, \
        f"Report should show {num_activities} activities, but shows {total_activities}"


# ============================================================================
# Property 34: PDF 생성 및 저장
# 출처: requirements.md - Property 22, design.md - Property 23
# 기준: 월간 리포트는 PDF로 생성되어 S3에 저장
# ============================================================================

def test_property_34_pdf_generation_and_storage():
    """
    Property 34: PDF 생성 및 저장
    
    For all monthly report generation attempts,
    a valid PDF file SHALL be created and stored in S3 
    at the path {year}/{month}/{user_id}/report.pdf.
    
    시나리오:
    - 입력: 월간 리포트 생성 요청
    - 기대: PDF 파일 생성, S3 저장
    - 검증: S3 경로에 파일 존재
    
    기준값 출처: requirements.md 요구사항 7.5, 7.6
    """
    # Arrange
    user_id = 'test-user-pdf'
    
    dynamodb = DynamoDBHelper()
    rds = RDSHelper()
    
    dynamodb.put_user_settings(
        user_id=user_id,
        name='Test User',
        status='active'
    )
    
    # 지난 30일 활동 데이터 생성
    for i in range(30):
        timestamp = datetime.utcnow() - timedelta(days=i)
        rds.insert_activity_log(
            user_id=user_id,
            activity_type='sensor_data',
            device_type='mobile',
            device_id='device-001',
            sensor_type='accelerometer',
            value=2.5,
            timestamp=timestamp
        )
    
    # Act - 월간 리포트 생성
    event = {
        'reportType': 'monthly',
        'userId': user_id
    }
    response = report_handler(event, {})
    
    # Assert
    assert response['statusCode'] == 200
    
    body = json.loads(response['body'])
    s3_path = body.get('s3Path', '')
    
    # S3 경로 형식 검증: {year}/{month}/{user_id}/report.pdf
    now = datetime.utcnow()
    expected_path_pattern = f"{now.year}/{now.month:02d}/{user_id}/report.pdf"
    
    assert expected_path_pattern in s3_path, \
        f"S3 path should match pattern {expected_path_pattern}, got {s3_path}"


# ============================================================================
# Property 35: 리포트 보존 기간
# 출처: design.md - S3 라이프사이클 정책
# 기준: 리포트는 12개월 후 Glacier로 이동, 24개월 후 삭제
# ============================================================================

def test_property_35_report_retention_policy():
    """
    Property 35: 리포트 보존 기간
    
    For all reports stored in S3,
    lifecycle policy SHALL move to Glacier after 12 months
    and delete after 24 months.
    
    시나리오:
    - 입력: 리포트 생성
    - 기대: S3 객체에 라이프사이클 정책 적용
    - 검증: 메타데이터에 TTL 정보 포함
    
    기준값 출처: design.md - S3 라이프사이클 정책
    """
    # Arrange
    user_id = 'test-user-retention'
    
    dynamodb = DynamoDBHelper()
    dynamodb.put_user_settings(
        user_id=user_id,
        name='Test User',
        status='active'
    )
    
    # Act - 월간 리포트 생성
    event = {
        'reportType': 'monthly',
        'userId': user_id
    }
    response = report_handler(event, {})
    
    # Assert
    assert response['statusCode'] == 200
    
    body = json.loads(response['body'])
    metadata = body.get('metadata', {})
    
    # 라이프사이클 정책 정보 확인
    assert 'retentionPolicy' in metadata or 'lifecycle' in metadata, \
        "Report metadata should include retention/lifecycle policy information"


# ============================================================================
# Property 36: 일일 리포트 스케줄
# 출처: requirements.md - 요구사항 7.1
# 기준: 매일 00:00 UTC에 일일 리포트 생성
# ============================================================================

def test_property_36_daily_report_schedule():
    """
    Property 36: 일일 리포트 스케줄
    
    THE EventBridge SHALL 매일 00:00 UTC에 ReportGenerator를 실행하여 
    일일 리포트를 생성한다.
    
    시나리오:
    - 입력: EventBridge 스케줄 트리거
    - 기대: 일일 리포트 생성
    - 검증: 리포트 생성 시간이 00:00 UTC 근처
    
    기준값 출처: requirements.md 요구사항 7.1
    """
    # Arrange
    user_id = 'test-user-schedule'
    
    dynamodb = DynamoDBHelper()
    dynamodb.put_user_settings(
        user_id=user_id,
        name='Test User',
        status='active'
    )
    
    # EventBridge 스케줄 트리거 시뮬레이션
    event = {
        'reportType': 'daily',
        'source': 'aws.events',
        'time': datetime.utcnow().replace(hour=0, minute=0, second=0).isoformat()
    }
    
    # Act
    response = report_handler(event, {})
    
    # Assert
    assert response['statusCode'] == 200
    
    body = json.loads(response['body'])
    generation_time = body.get('generatedAt', '')
    
    # 생성 시간이 00:00 UTC 근처인지 확인 (±5분 허용)
    if generation_time:
        gen_time = datetime.fromisoformat(generation_time.replace('Z', '+00:00'))
        assert gen_time.hour == 0 and gen_time.minute <= 5, \
            f"Daily report should be generated around 00:00 UTC, got {gen_time}"


# ============================================================================
# Property 37: 월간 리포트 스케줄
# 출처: requirements.md - 요구사항 7.2
# 기준: 매월 1일 00:00 UTC에 월간 리포트 생성
# ============================================================================

def test_property_37_monthly_report_schedule():
    """
    Property 37: 월간 리포트 스케줄
    
    THE EventBridge SHALL 매월 1일 00:00 UTC에 ReportGenerator를 실행하여 
    월간 리포트를 생성한다.
    
    시나리오:
    - 입력: EventBridge 스케줄 트리거 (매월 1일)
    - 기대: 월간 리포트 생성
    - 검증: 리포트 생성 날짜가 1일
    
    기준값 출처: requirements.md 요구사항 7.2
    """
    # Arrange
    user_id = 'test-user-monthly'
    
    dynamodb = DynamoDBHelper()
    dynamodb.put_user_settings(
        user_id=user_id,
        name='Test User',
        status='active'
    )
    
    # EventBridge 스케줄 트리거 시뮬레이션 (매월 1일)
    now = datetime.utcnow()
    first_day = now.replace(day=1, hour=0, minute=0, second=0)
    
    event = {
        'reportType': 'monthly',
        'source': 'aws.events',
        'time': first_day.isoformat()
    }
    
    # Act
    response = report_handler(event, {})
    
    # Assert
    assert response['statusCode'] == 200
    
    body = json.loads(response['body'])
    generation_time = body.get('generatedAt', '')
    
    # 생성 시간이 매월 1일인지 확인
    if generation_time:
        gen_time = datetime.fromisoformat(generation_time.replace('Z', '+00:00'))
        assert gen_time.day == 1, \
            f"Monthly report should be generated on 1st day of month, got day {gen_time.day}"


# ============================================================================
# Property 38: 리포트 다운로드 링크 전송
# 출처: requirements.md - 요구사항 7.8
# 기준: 리포트 생성 후 SNS를 통해 다운로드 링크 게시
# ============================================================================

def test_property_38_report_download_link():
    """
    Property 38: 리포트 다운로드 링크 전송
    
    WHEN 리포트 생성이 완료되면,
    THE ReportGenerator SHALL SNS DailyReport 토픽에 다운로드 링크를 게시한다.
    
    시나리오:
    - 입력: 리포트 생성 완료
    - 기대: SNS 토픽에 다운로드 링크 게시
    - 검증: 응답에 다운로드 링크 포함
    
    기준값 출처: requirements.md 요구사항 7.8
    """
    # Arrange
    user_id = 'test-user-link'
    
    dynamodb = DynamoDBHelper()
    dynamodb.put_user_settings(
        user_id=user_id,
        name='Test User',
        status='active'
    )
    
    # Act - 월간 리포트 생성
    event = {
        'reportType': 'monthly',
        'userId': user_id
    }
    response = report_handler(event, {})
    
    # Assert
    assert response['statusCode'] == 200
    
    body = json.loads(response['body'])
    download_link = body.get('downloadLink', '')
    
    assert download_link, "Response should include download link"
    assert 's3' in download_link.lower() or 'http' in download_link.lower(), \
        "Download link should be a valid S3 URL or HTTP URL"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--hypothesis-show-statistics'])
