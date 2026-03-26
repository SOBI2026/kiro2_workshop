"""Quick test data insertion for dashboard"""
import boto3
import json
from datetime import datetime, timedelta
import random
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')

# Wait for tables to be active
print("테이블 상태 확인 중...")
dynamodb_client = boto3.client('dynamodb')

for table_name in ['SeniorCare-SensorData', 'SeniorCare-UserSettings', 'SeniorCare-AlertHistory']:
    waiter = dynamodb_client.get_waiter('table_exists')
    waiter.wait(TableName=table_name)
    print(f"✅ {table_name} 준비 완료")

# Create test user
print("\n테스트 사용자 생성 중...")
settings_table = dynamodb.Table('SeniorCare-UserSettings')
settings_table.put_item(Item={
    'userId': 'test-user-001',
    'name': '김영희',
    'age': 75,
    'phone': '010-1234-5678',
    'inactivityThreshold': 120,
    'voiceResponseTimeout': 30,
    'lastActivityTime': datetime.utcnow().isoformat(),
    'status': 'active',
    'createdAt': datetime.utcnow().isoformat(),
    'updatedAt': datetime.utcnow().isoformat()
})
print("✅ 사용자 생성 완료: test-user-001 (김영희)")

# Generate sensor data
print("\n센서 데이터 생성 중...")
sensor_table = dynamodb.Table('SeniorCare-SensorData')
sensor_types = ['accelerometer', 'motion', 'door', 'temperature']
device_types = ['mobile', 'iot']

for i in range(30):
    timestamp = datetime.utcnow() - timedelta(hours=random.randint(0, 23), minutes=random.randint(0, 59))
    ttl = int((datetime.utcnow() + timedelta(days=30)).timestamp())
    
    sensor_table.put_item(Item={
        'userId': 'test-user-001',
        'timestamp': int(timestamp.timestamp()),
        'deviceId': 'device-001',
        'deviceType': random.choice(device_types),
        'sensorType': random.choice(sensor_types),
        'value': Decimal(str(round(random.uniform(0.5, 5.0), 2))),
        'ttl': ttl
    })
    
    if (i + 1) % 10 == 0:
        print(f"  {i + 1}/30 완료")

print("✅ 센서 데이터 30개 생성 완료")

# Create sample alert
print("\n샘플 알림 생성 중...")
alert_table = dynamodb.Table('SeniorCare-AlertHistory')
alert_table.put_item(Item={
    'userId': 'test-user-001',
    'alertId': 'alert-001',
    'alertType': 'no_response',
    'status': 'voice_confirmation_pending',
    'createdAt': datetime.utcnow().isoformat(),
    'lastActivityTime': (datetime.utcnow() - timedelta(hours=3)).isoformat(),
    'retryCount': 0,
    'ttl': int((datetime.utcnow() + timedelta(days=90)).timestamp())
})
print("✅ 샘플 알림 생성 완료")

print("\n" + "="*50)
print("✅ 모든 테스트 데이터 생성 완료!")
print("="*50)
print("\n대시보드를 실행하세요:")
print("  streamlit run dashboard/app.py")
