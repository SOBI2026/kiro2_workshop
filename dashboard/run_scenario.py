import boto3
import json
from datetime import datetime
import time
from decimal import Decimal

print("=" * 70)
print("🚨 낙상 감지 시나리오 시뮬레이션")
print("=" * 70)
print("시나리오: 김영희씨(75세)가 화장실에서 넘어짐")
print("=" * 70)

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
sensor_table = dynamodb.Table('SeniorCare-SensorData')
user_settings_table = dynamodb.Table('SeniorCare-UserSettings')

user_id = 'test-user-001'

# Step 1: 낙상 전 정상 활동
print("\n[Step 1] 낙상 전 정상 활동")
print("-" * 70)
print("김영희씨가 거실에서 TV를 시청 중...")

item = {
    'userId': user_id,
    'timestamp': int(datetime.utcnow().timestamp()),
    'deviceId': 'phone-001',
    'deviceType': 'mobile',
    'sensorType': 'motion',
    'value': Decimal('1.2')
}
sensor_table.put_item(Item=item)
user_settings_table.update_item(
    Key={'userId': user_id},
    UpdateExpression='SET lastActivityTime = :lat',
    ExpressionAttributeValues={':lat': datetime.utcnow().isoformat() + 'Z'}
)
print(f"✅ 정상 활동 기록: motion sensor = 1.2")
time.sleep(2)

# Step 2: 화장실로 이동
print("\n[Step 2] 화장실로 이동")
print("-" * 70)
print("김영희씨가 화장실로 이동 중...")

item = {
    'userId': user_id,
    'timestamp': int(datetime.utcnow().timestamp()),
    'deviceId': 'door-sensor-001',
    'deviceType': 'iot',
    'sensorType': 'door',
    'value': Decimal('1.0')
}
sensor_table.put_item(Item=item)
user_settings_table.update_item(
    Key={'userId': user_id},
    UpdateExpression='SET lastActivityTime = :lat',
    ExpressionAttributeValues={':lat': datetime.utcnow().isoformat() + 'Z'}
)
print(f"✅ 화장실 문 열림 감지")
time.sleep(2)

# Step 3: 낙상 발생!
print("\n[Step 3] 🚨 낙상 발생!")
print("-" * 70)
print("김영희씨가 화장실에서 미끄러져 넘어짐!")
print("가속도 센서가 급격한 충격을 감지...")

item = {
    'userId': user_id,
    'timestamp': int(datetime.utcnow().timestamp()),
    'deviceId': 'phone-001',
    'deviceType': 'mobile',
    'sensorType': 'accelerometer',
    'value': Decimal('15.8')
}
sensor_table.put_item(Item=item)
user_settings_table.update_item(
    Key={'userId': user_id},
    UpdateExpression='SET lastActivityTime = :lat',
    ExpressionAttributeValues={':lat': datetime.utcnow().isoformat() + 'Z'}
)
print(f"🚨 낙상 감지! accelerometer = 15.8 (임계값 10.0 초과)")
print(f"   → 시스템이 이상 징후를 감지했습니다!")
time.sleep(2)

# Step 4: 활동 부재
print("\n[Step 4] 활동 부재 감지")
print("-" * 70)
print("2분 동안 움직임이 감지되지 않음...")

for i in range(3):
    item = {
        'userId': user_id,
        'timestamp': int(datetime.utcnow().timestamp()),
        'deviceId': 'motion-sensor-001',
        'deviceType': 'iot',
        'sensorType': 'motion',
        'value': Decimal('0.1')
    }
    sensor_table.put_item(Item=item)
    print(f"   {i+1}분 경과: motion = 0.1 (움직임 거의 없음)")
    time.sleep(1)

print("\n⚠️  활동 부재 임계값 초과 가능!")

# Step 5: 알림 확인
print("\n[Step 5] 알림 이력 확인")
print("-" * 70)

alert_table = dynamodb.Table('SeniorCare-AlertHistory')
alert_response = alert_table.query(
    KeyConditionExpression='userId = :uid',
    ExpressionAttributeValues={':uid': user_id},
    ScanIndexForward=False,
    Limit=5
)

if alert_response['Items']:
    print(f"✅ 총 {len(alert_response['Items'])}개의 알림 발견:")
    for i, alert in enumerate(alert_response['Items'][:3], 1):
        alert_type = alert.get('alertType', 'unknown')
        status = alert.get('status', 'unknown')
        created_at = alert.get('createdAt', 'N/A')
        print(f"\n   알림 {i}:")
        print(f"   - 유형: {alert_type}")
        print(f"   - 상태: {status}")
        print(f"   - 생성 시간: {created_at}")
else:
    print("⚠️  아직 알림이 생성되지 않았습니다.")
    print("   (InactivityDetector는 EventBridge로 1분마다 실행됩니다)")

# Step 6: 센서 데이터 확인
print("\n[Step 6] 센서 데이터 확인")
print("-" * 70)

sensor_response = sensor_table.query(
    KeyConditionExpression='userId = :uid',
    ExpressionAttributeValues={':uid': user_id},
    ScanIndexForward=False,
    Limit=10
)

print(f"✅ 최근 {len(sensor_response['Items'])}개의 센서 데이터:")
for i, item in enumerate(sensor_response['Items'][:5], 1):
    sensor_type = item.get('sensorType', 'unknown')
    value = float(item.get('value', 0))
    device_id = item.get('deviceId', 'unknown')
    ts = datetime.fromtimestamp(int(item.get('timestamp', 0)))
    print(f"   {i}. {sensor_type}: {value} (device: {device_id}, time: {ts.strftime('%H:%M:%S')})")

print("\n" + "=" * 70)
print("📋 시스템 대응 프로세스")
print("=" * 70)
print("""
1. ✅ 낙상 감지 완료 (accelerometer = 15.8)
2. ✅ 활동 부재 시뮬레이션 (움직임 거의 없음)
3. 🔄 다음 단계: InactivityDetector 실행 대기
   → EventBridge가 1분마다 자동 실행
   → 임계값(120분) 초과 시 알림 생성
   
4. 💡 대시보드에서 확인:
   - 버전 1 (http://localhost:8503): 
     * 실시간 모니터링 탭: 최근 활동 타임라인에서 낙상 데이터 확인
     * 알림 이력 탭: 새 알림 확인 (생성 시)
     * 통계 탭: 센서 데이터 분포 확인
   
   - 버전 2 (http://localhost:8504): 
     * 실시간 시스템 현황: 센서 데이터 수 증가 확인
     * 마지막 활동 시간 업데이트 확인
""")

print("\n✨ 시나리오 실행 완료!")
print("   대시보드를 새로고침하여 변화를 확인하세요.")
print("=" * 70)
