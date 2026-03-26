"""
Pytest configuration for property-based tests
"""

import pytest
from hypothesis import settings, Verbosity
import boto3
from moto import mock_aws
import os
from datetime import datetime
from unittest.mock import Mock, patch
import json


# Hypothesis 프로필 설정
settings.register_profile("default", max_examples=100, deadline=None)
settings.register_profile("ci", max_examples=50, deadline=5000)  # CI 환경용
settings.register_profile("dev", max_examples=20, deadline=None, verbosity=Verbosity.verbose)
settings.register_profile("thorough", max_examples=1000, deadline=None)  # 철저한 테스트

# 환경 변수에서 프로필 선택
profile = os.getenv('HYPOTHESIS_PROFILE', 'default')
settings.load_profile(profile)


@pytest.fixture(scope='function')
def aws_credentials():
    """AWS 자격증명 모킹"""
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'


@pytest.fixture(scope='function')
def dynamodb_mock(aws_credentials):
    """DynamoDB 모킹"""
    with mock_aws():
        # Secrets Manager 모킹 - RDS 자격증명
        secrets_client = boto3.client('secretsmanager', region_name='us-east-1')
        secrets_client.create_secret(
            Name='test-secret',
            SecretString=json.dumps({
                'host': 'localhost',
                'port': 5432,
                'dbname': 'seniorcare_test',
                'username': 'test_user',
                'password': 'test_password'
            })
        )
        
        # 테이블 생성
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        
        # SensorData 테이블
        dynamodb.create_table(
            TableName='SeniorCare-SensorData',
            KeySchema=[
                {'AttributeName': 'userId', 'KeyType': 'HASH'},
                {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'userId', 'AttributeType': 'S'},
                {'AttributeName': 'timestamp', 'AttributeType': 'N'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # UserSettings 테이블
        dynamodb.create_table(
            TableName='SeniorCare-UserSettings',
            KeySchema=[
                {'AttributeName': 'userId', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'userId', 'AttributeType': 'S'},
                {'AttributeName': 'status', 'AttributeType': 'S'},
                {'AttributeName': 'lastActivityTime', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'status-lastActivityTime-index',
                    'KeySchema': [
                        {'AttributeName': 'status', 'KeyType': 'HASH'},
                        {'AttributeName': 'lastActivityTime', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # AlertHistory 테이블
        dynamodb.create_table(
            TableName='SeniorCare-AlertHistory',
            KeySchema=[
                {'AttributeName': 'userId', 'KeyType': 'HASH'},
                {'AttributeName': 'alertId', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'userId', 'AttributeType': 'S'},
                {'AttributeName': 'alertId', 'AttributeType': 'S'},
                {'AttributeName': 'status', 'AttributeType': 'S'},
                {'AttributeName': 'createdAt', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'status-createdAt-index',
                    'KeySchema': [
                        {'AttributeName': 'status', 'KeyType': 'HASH'},
                        {'AttributeName': 'createdAt', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        yield dynamodb


@pytest.fixture(scope='function', autouse=True)
def setup_test_environment(dynamodb_mock, mock_rds_connection):
    """각 테스트 전에 환경 설정"""
    # 환경 변수 설정
    os.environ['DYNAMODB_SENSOR_DATA_TABLE'] = 'SeniorCare-SensorData'
    os.environ['DYNAMODB_USER_SETTINGS_TABLE'] = 'SeniorCare-UserSettings'
    os.environ['DYNAMODB_ALERT_HISTORY_TABLE'] = 'SeniorCare-AlertHistory'
    os.environ['RDS_SECRET_ARN'] = 'test-secret'
    os.environ['SNS_ALERT_TOPIC_ARN'] = 'arn:aws:sns:us-east-1:123456789012:test-alert-topic'
    os.environ['SNS_REPORT_TOPIC_ARN'] = 'arn:aws:sns:us-east-1:123456789012:test-report-topic'
    os.environ['SQS_NOTIFICATION_QUEUE_URL'] = 'https://sqs.us-east-1.amazonaws.com/123456789012/test-queue'
    os.environ['REPORTS_BUCKET_NAME'] = 'test-reports-bucket'
    
    yield
    
    # 테스트 후 정리 (필요시)


@pytest.fixture
def sample_user_data():
    """샘플 사용자 데이터"""
    return {
        'userId': 'test-user-001',
        'name': '김영희',
        'age': 75,
        'phone': '010-1234-5678',
        'inactivityThreshold': 120,
        'voiceResponseTimeout': 30,
        'status': 'active'
    }


@pytest.fixture
def sample_sensor_data():
    """샘플 센서 데이터"""
    return {
        'userId': 'test-user-001',
        'deviceId': 'device-001',
        'deviceType': 'mobile',
        'sensorType': 'accelerometer',
        'value': 2.5,
        'timestamp': datetime.utcnow().isoformat()
    }


@pytest.fixture(scope='function')
def mock_rds_connection():
    """RDS 연결 모킹 - PostgreSQL 연결 없이 테스트"""
    mock_conn = Mock()
    mock_cursor = Mock()
    
    # 기본 동작 설정
    mock_conn.cursor.return_value = mock_cursor
    mock_conn.commit.return_value = None
    mock_conn.rollback.return_value = None
    mock_conn.closed = False
    
    # cursor 동작 설정
    mock_cursor.execute.return_value = None
    mock_cursor.fetchone.return_value = (0,)
    mock_cursor.fetchall.return_value = []
    mock_cursor.description = []
    
    with patch('psycopg2.connect', return_value=mock_conn):
        yield mock_conn
