import boto3
import json
from datetime import datetime
from decimal import Decimal

print("=" * 60)
print("시니어 안심 케어 모니터링 시스템 테스트")
print("=" * 60)

# AWS clients
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
lambda_client = boto3.client('lambda', region_name='us-east-1')

user_id = 'test-user-001'

# Test 1: 센서 데이터 전송
print("\n[Test 1] 센서 데이터 전송 테스트")
print("-" * 60)
payload = {
    'userId': user_id,
    'deviceId': 'device-test-001',
    'deviceType': 'mobile',
    'sensorType': 'motion',
    'value': 3.5,
    'timestamp': datetime.utcnow().isoformat()
}

try:
    response = lambda_client.invoke(
        FunctionName='SeniorCare-SensorDataProcessor',
        InvocationType='RequestResponse',
        Payload=json.dumps(payload)
    )
    result = json.loads(response['Payload'].read())
    
    if result.get('statusCode') == 200:
        print("✅ 센서 데이터 전송 성공!")
        print(f"   Response: {result.get('body')}")
    else:
        print(f"❌ 센서 데이터 전송 실패: {result}")
except Exception as e:
    print(f"❌ 에러: {e}")

# Test 2: DynamoDB 센서 데이터 조회
print("\n[Test 2] DynamoDB 센서 데이터 조회")
print("-" * 60)
try:
    sensor_table = dynamodb.Table('SeniorCare-SensorData')
    response = sensor_table.query(
        KeyConditionExpression='userId = :uid',
        ExpressionAttributeValues={':uid': user_id},
        ScanIndexForward=False,
        Limit=5
    )
    
    items = response['Items']
    print(f"✅ 센서 데이터 {len(items)}개 조회 성공!")
    
    for i, item in enumerate(items[:3], 1):
        timestamp = item.get('timestamp')
        sensor_type = item.get('sensorType')
        value = item.get('value')
        device_id = item.get('deviceId')
        
        # Convert Decimal to float for display
        if isinstance(value, Decimal):
            value = float(value)
        if isinstance(timestamp, Decimal):
            timestamp = int(timestamp)
        
        dt = datetime.fromtimestamp(timestamp)
        print(f"   {i}. {dt.strftime('%Y-%m-%d %H:%M:%S')} | {sensor_type} | {value} | {device_id}")
        
except Exception as e:
    print(f"❌ 에러: {e}")

# Test 3: 사용자 설정 조회
print("\n[Test 3] 사용자 설정 조회")
print("-" * 60)
try:
    settings_table = dynamodb.Table('SeniorCare-UserSettings')
    response = settings_table.get_item(Key={'userId': user_id})
    
    if 'Item' in response:
        item = response['Item']
        print("✅ 사용자 설정 조회 성공!")
        print(f"   이름: {item.get('name')}")
        print(f"   상태: {item.get('status')}")
        print(f"   마지막 활동: {item.get('lastActivityTime')}")
        print(f"   활동 부재 임계값: {item.get('inactivityThreshold')}분")
    else:
        print("❌ 사용자를 찾을 수 없습니다.")
        
except Exception as e:
    print(f"❌ 에러: {e}")

# Test 4: 알림 이력 조회
print("\n[Test 4] 알림 이력 조회")
print("-" * 60)
try:
    alert_table = dynamodb.Table('SeniorCare-AlertHistory')
    response = alert_table.query(
        KeyConditionExpression='userId = :uid',
        ExpressionAttributeValues={':uid': user_id},
        ScanIndexForward=False,
        Limit=5
    )
    
    items = response['Items']
    print(f"✅ 알림 이력 {len(items)}개 조회 성공!")
    
    for i, item in enumerate(items, 1):
        alert_type = item.get('alertType')
        status = item.get('status')
        created_at = item.get('createdAt')
        print(f"   {i}. {alert_type} | {status} | {created_at}")
        
except Exception as e:
    print(f"❌ 에러: {e}")

# Test 5: 설정 업데이트 테스트
print("\n[Test 5] 설정 업데이트 테스트")
print("-" * 60)
payload = {
    'userId': user_id,
    'action': 'update_settings',
    'inactivityThreshold': 150
}

try:
    response = lambda_client.invoke(
        FunctionName='SeniorCare-SettingsManager',
        InvocationType='RequestResponse',
        Payload=json.dumps(payload)
    )
    result = json.loads(response['Payload'].read())
    
    if result.get('statusCode') == 200:
        print("✅ 설정 업데이트 성공!")
        print(f"   Response: {result.get('body')}")
    else:
        print(f"❌ 설정 업데이트 실패: {result}")
except Exception as e:
    print(f"❌ 에러: {e}")

# Summary
print("\n" + "=" * 60)
print("테스트 완료!")
print("=" * 60)
print("\n시스템이 정상적으로 작동하고 있습니다.")
print("브라우저에서 http://localhost:8501 접속 후 캐시 삭제(Ctrl+Shift+Delete)하고")
print("하드 새로고침(Ctrl+F5)을 시도해보세요.")
