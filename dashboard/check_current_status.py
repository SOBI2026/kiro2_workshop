import boto3
from datetime import datetime

print("=" * 70)
print("📊 현재 시스템 상태 확인")
print("=" * 70)

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

user_id = 'test-user-001'

# 1. 사용자 설정 확인
print("\n[1] 사용자 설정")
print("-" * 70)
user_settings_table = dynamodb.Table('SeniorCare-UserSettings')
response = user_settings_table.get_item(Key={'userId': user_id})

if 'Item' in response:
    user_data = response['Item']
    print(f"✅ 사용자: {user_data.get('name', 'N/A')}")
    print(f"   나이: {user_data.get('age', 'N/A')}세")
    print(f"   상태: {user_data.get('status', 'N/A')}")
    print(f"   마지막 활동: {user_data.get('lastActivityTime', 'N/A')}")
    print(f"   활동 부재 임계값: {user_data.get('inactivityThreshold', 'N/A')}분")
    print(f"   음성 응답 타임아웃: {user_data.get('voiceResponseTimeout', 'N/A')}초")

# 2. 센서 데이터 통계
print("\n[2] 센서 데이터 통계")
print("-" * 70)
sensor_table = dynamodb.Table('SeniorCare-SensorData')
sensor_response = sensor_table.query(
    KeyConditionExpression='userId = :uid',
    ExpressionAttributeValues={':uid': user_id},
    ScanIndexForward=False,
    Limit=200
)

total_count = len(sensor_response['Items'])
print(f"✅ 총 센서 데이터: {total_count}개 (최근 200개 조회)")

# 센서 타입별 분포
sensor_types = {}
device_types = {}
for item in sensor_response['Items']:
    sensor_type = item.get('sensorType', 'unknown')
    device_type = item.get('deviceType', 'unknown')
    sensor_types[sensor_type] = sensor_types.get(sensor_type, 0) + 1
    device_types[device_type] = device_types.get(device_type, 0) + 1

print("\n   센서 타입별 분포:")
for sensor_type, count in sorted(sensor_types.items(), key=lambda x: x[1], reverse=True):
    percentage = (count / total_count) * 100
    print(f"   - {sensor_type}: {count}개 ({percentage:.1f}%)")

print("\n   디바이스 타입별 분포:")
for device_type, count in sorted(device_types.items(), key=lambda x: x[1], reverse=True):
    percentage = (count / total_count) * 100
    print(f"   - {device_type}: {count}개 ({percentage:.1f}%)")

# 3. 최근 센서 데이터 (최근 5개)
print("\n[3] 최근 센서 데이터 (최근 5개)")
print("-" * 70)
for i, item in enumerate(sensor_response['Items'][:5], 1):
    sensor_type = item.get('sensorType', 'unknown')
    value = float(item.get('value', 0))
    device_id = item.get('deviceId', 'unknown')
    timestamp = int(item.get('timestamp', 0))
    dt = datetime.fromtimestamp(timestamp)
    
    emoji = {
        'motion': '🚶',
        'door': '🚪',
        'accelerometer': '📱',
        'temperature': '🌡️'
    }.get(sensor_type, '📊')
    
    print(f"{i}. {emoji} {sensor_type}: {value}")
    print(f"   Device: {device_id} | Time: {dt.strftime('%Y-%m-%d %H:%M:%S')}")

# 4. 알림 이력
print("\n[4] 알림 이력")
print("-" * 70)
alert_table = dynamodb.Table('SeniorCare-AlertHistory')
alert_response = alert_table.query(
    KeyConditionExpression='userId = :uid',
    ExpressionAttributeValues={':uid': user_id},
    ScanIndexForward=False,
    Limit=10
)

alert_count = len(alert_response['Items'])
print(f"✅ 총 알림: {alert_count}개")

if alert_response['Items']:
    print("\n   최근 알림:")
    for i, alert in enumerate(alert_response['Items'][:3], 1):
        alert_type = alert.get('alertType', 'unknown')
        status = alert.get('status', 'unknown')
        created_at = alert.get('createdAt', 'N/A')
        
        status_emoji = {
            'voice_confirmation_pending': '⏳',
            'confirmed_safe': '✅',
            'no_response': '⚠️',
            'resolved': '✔️'
        }.get(status, '❓')
        
        print(f"\n   {i}. {status_emoji} {alert_type}")
        print(f"      상태: {status}")
        print(f"      생성: {created_at}")

# 5. 낙상 감지 데이터 확인
print("\n[5] 낙상 감지 데이터 확인")
print("-" * 70)
fall_detected = False
for item in sensor_response['Items']:
    if item.get('sensorType') == 'accelerometer':
        value = float(item.get('value', 0))
        if value > 10.0:  # 낙상 임계값
            timestamp = int(item.get('timestamp', 0))
            dt = datetime.fromtimestamp(timestamp)
            print(f"🚨 낙상 감지!")
            print(f"   가속도: {value} (임계값 10.0 초과)")
            print(f"   시간: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
            fall_detected = True
            break

if not fall_detected:
    print("   낙상 감지 데이터 없음")

print("\n" + "=" * 70)
print("✨ 시스템 상태 확인 완료!")
print("\n💡 대시보드 확인:")
print("   - 버전 1: http://localhost:8503")
print("   - 버전 2: http://localhost:8504")
print("\n   브라우저에서 새로고침(F5 또는 Ctrl+R)하여 최신 데이터를 확인하세요!")
print("=" * 70)
