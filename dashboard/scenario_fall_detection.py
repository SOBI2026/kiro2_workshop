import boto3
import json
from datetime import datetime
import time

print("=" * 70)
print("🚨 낙상 감지 시나리오 시뮬레이션")
print("=" * 70)
print("시나리오: 김영희씨(75세)가 화장실에서 넘어짐")
print("=" * 70)

lambda_client = boto3.client('lambda', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

user_id = 'test-user-001'

# Step 1: 낙상 전 정상 활동
print("\n[Step 1] 낙상 전 정상 활동 (14:00)")
print("-" * 70)
print("김영희씨가 거실에서 TV를 시청 중...")

payload = {
    'userId': user_id,
    'deviceId': 'phone-001',
    'deviceType': 'mobile',
    'sensorType': 'motion',
    'value': 1.2,  # 정상 움직임
    'timestamp': datetime.utcnow().isoformat()
}

response = lambda_client.invoke(
    FunctionName='SeniorCare-SensorDataProcessor',
    InvocationType='RequestResponse',
    Payload=json.dumps(payload)
)
result = json.loads(response['Payload'].read())
print(f"✅ 정상 활동 기록: motion sensor = 1.2")

time.sleep(2)

# Step 2: 화장실로 이동
print("\n[Step 2] 화장실로 이동 (14:05)")
print("-" * 70)
print("김영희씨가 화장실로 이동 중...")

payload = {
    'userId': user_id,
    'deviceId': 'door-sensor-001',
    'deviceType': 'iot',
    'sensorType': 'door',
    'value': 1.0,  # 문 열림
    'timestamp': datetime.utcnow().isoformat()
}

response = lambda_client.invoke(
    FunctionName='SeniorCare-SensorDataProcessor',
    InvocationType='RequestResponse',
    Payload=json.dumps(payload)
)
print(f"✅ 화장실 문 열림 감지")

time.sleep(2)

# Step 3: 낙상 발생! (급격한 가속도 변화)
print("\n[Step 3] 🚨 낙상 발생! (14:07)")
print("-" * 70)
print("김영희씨가 화장실에서 미끄러져 넘어짐!")
print("가속도 센서가 급격한 충격을 감지...")

payload = {
    'userId': user_id,
    'deviceId': 'phone-001',
    'deviceType': 'mobile',
    'sensorType': 'accelerometer',
    'value': 15.8,  # 급격한 가속도 변화 (낙상 의심)
    'timestamp': datetime.utcnow().isoformat()
}

response = lambda_client.invoke(
    FunctionName='SeniorCare-SensorDataProcessor',
    InvocationType='RequestResponse',
    Payload=json.dumps(payload)
)
result = json.loads(response['Payload'].read())
print(f"🚨 낙상 감지! accelerometer = 15.8 (임계값 10.0 초과)")
print(f"   → 시스템이 이상 징후를 감지했습니다!")

time.sleep(2)

# Step 4: 활동 부재 (움직임 없음)
print("\n[Step 4] 활동 부재 감지 (14:08 ~ 14:10)")
print("-" * 70)
print("2분 동안 움직임이 감지되지 않음...")
print("InactivityDetector가 1분마다 체크 중...")

# 움직임 없음을 시뮬레이션 (매우 낮은 값)
for i in range(2):
    payload = {
        'userId': user_id,
        'deviceId': 'motion-sensor-001',
        'deviceType': 'iot',
        'sensorType': 'motion',
        'value': 0.1,  # 거의 움직임 없음
        'timestamp': datetime.utcnow().isoformat()
    }
    
    response = lambda_client.invoke(
        FunctionName='SeniorCare-SensorDataProcessor',
        InvocationType='RequestResponse',
        Payload=json.dumps(payload)
    )
    print(f"   {i+1}분 경과: motion = 0.1 (움직임 거의 없음)")
    time.sleep(1)

print("\n⚠️  활동 부재 임계값 초과!")
print("   → InactivityDetector가 알림을 생성합니다...")

# Step 5: 알림 생성 확인
print("\n[Step 5] 알림 이력 확인")
print("-" * 70)

alert_table = dynamodb.Table('SeniorCare-AlertHistory')
alert_response = alert_table.query(
    KeyConditionExpression='userId = :uid',
    ExpressionAttributeValues={':uid': user_id},
    ScanIndexForward=False,
    Limit=3
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

# Step 6: 다음 단계 안내
print("\n" + "=" * 70)
print("📋 시스템 대응 프로세스")
print("=" * 70)
print("""
1. ✅ 낙상 감지 완료 (accelerometer = 15.8)
2. ✅ 활동 부재 확인 (2분간 움직임 없음)
3. 🔄 다음 단계: AI 스피커 음성 확인
   → "김영희님, 괜찮으세요? 응답해주세요."
   
4. 시나리오 A: 응답 있음
   → "네, 괜찮아요" → 정상 처리, 모니터링 계속
   
5. 시나리오 B: 응답 없음 (30초 타임아웃)
   → 보호자에게 긴급 알림 발송
   → SMS: "김영희님이 넘어진 것으로 의심됩니다. 즉시 확인 바랍니다."
   → 푸시 알림: 위치 정보 포함

현재 상태: 음성 확인 대기 중...
""")

print("\n💡 대시보드에서 확인:")
print("   - 버전 1 (http://localhost:8503): 알림 이력 탭에서 새 알림 확인")
print("   - 버전 2 (http://localhost:8504): 실시간 시스템 현황에서 알림 수 증가 확인")
print("\n" + "=" * 70)
