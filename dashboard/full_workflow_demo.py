import boto3
from datetime import datetime
from decimal import Decimal
import time
import os

print("=" * 80)
print("🏥 시니어 안심 케어 - 전체 워크플로우 데모")
print("=" * 80)
print("시나리오: 김영희씨(75세) 낙상 감지 → AI 음성 확인 → 보호자 알림")
print("=" * 80)

# AWS 클라이언트
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
polly_client = boto3.client('polly', region_name='us-east-1')

sensor_table = dynamodb.Table('SeniorCare-SensorData')
user_settings_table = dynamodb.Table('SeniorCare-UserSettings')
alert_table = dynamodb.Table('SeniorCare-AlertHistory')

user_id = 'test-user-001'

# ============================================================================
# STEP 1: 센서 데이터 수집 (정상 활동)
# ============================================================================
print("\n" + "=" * 80)
print("1️⃣ 센서 데이터 수집 - 정상 활동")
print("=" * 80)

activities = [
    ("motion", "motion-sensor-001", "iot", 2.5, "거실에서 TV 시청"),
    ("door", "door-sensor-001", "iot", 1.0, "방문 열림"),
    ("temperature", "temp-sensor-001", "iot", 22.5, "실내 온도 정상"),
    ("motion", "motion-sensor-002", "iot", 1.8, "침실 이동")
]

for sensor_type, device_id, device_type, value, description in activities:
    item = {
        'userId': user_id,
        'timestamp': int(datetime.utcnow().timestamp()),
        'deviceId': device_id,
        'deviceType': device_type,
        'sensorType': sensor_type,
        'value': Decimal(str(value))
    }
    sensor_table.put_item(Item=item)
    user_settings_table.update_item(
        Key={'userId': user_id},
        UpdateExpression='SET lastActivityTime = :lat',
        ExpressionAttributeValues={':lat': datetime.utcnow().isoformat() + 'Z'}
    )
    print(f"✅ {description}: {sensor_type} = {value}")
    time.sleep(0.5)

print("\n✨ 정상 활동 데이터 수집 완료!")

# ============================================================================
# STEP 2: 활동 부재 감지 (낙상 발생)
# ============================================================================
print("\n" + "=" * 80)
print("2️⃣ 활동 부재 감지 - 낙상 발생!")
print("=" * 80)

print("\n🚶 화장실로 이동...")
item = {
    'userId': user_id,
    'timestamp': int(datetime.utcnow().timestamp()),
    'deviceId': 'door-sensor-bathroom',
    'deviceType': 'iot',
    'sensorType': 'door',
    'value': Decimal('1.0')
}
sensor_table.put_item(Item=item)
print("✅ 화장실 문 열림 감지")
time.sleep(1)

print("\n🚨 낙상 발생!")
item = {
    'userId': user_id,
    'timestamp': int(datetime.utcnow().timestamp()),
    'deviceId': 'phone-001',
    'deviceType': 'mobile',
    'sensorType': 'accelerometer',
    'value': Decimal('15.8')
}
sensor_table.put_item(Item=item)
print("⚠️  가속도 센서: 15.8 (임계값 10.0 초과)")
print("⚠️  급격한 충격 감지 - 낙상 의심!")
time.sleep(1)

print("\n⏰ 활동 부재 시뮬레이션 (3분간 움직임 없음)...")
for i in range(3):
    item = {
        'userId': user_id,
        'timestamp': int(datetime.utcnow().timestamp()),
        'deviceId': 'motion-sensor-bathroom',
        'deviceType': 'iot',
        'sensorType': 'motion',
        'value': Decimal('0.05')
    }
    sensor_table.put_item(Item=item)
    print(f"   {i+1}분: motion = 0.05 (움직임 거의 없음)")
    time.sleep(1)

print("\n✨ 이상 징후 감지 완료!")

# ============================================================================
# STEP 3: AI 스피커 음성 확인 (AWS Polly)
# ============================================================================
print("\n" + "=" * 80)
print("3️⃣ AI 스피커 음성 확인 - AWS Polly")
print("=" * 80)

# 알림 생성 (수동으로 생성 - InactivityDetector는 1분마다 실행)
import uuid
alert_id = str(uuid.uuid4())

alert_item = {
    'userId': user_id,
    'alertId': alert_id,
    'alertType': 'fall_detected',
    'status': 'voice_confirmation_pending',
    'createdAt': datetime.utcnow().isoformat(),
    'lastActivityTime': datetime.utcnow().isoformat(),
    'retryCount': 0
}
alert_table.put_item(Item=alert_item)
print(f"✅ 알림 생성: {alert_id}")
print(f"   유형: fall_detected")
print(f"   상태: voice_confirmation_pending")

# Polly로 음성 생성
print("\n🗣️ AWS Polly로 음성 메시지 생성 중...")
message_text = "김영희님, 넘어지신 것 같습니다. 괜찮으신가요? 응답해주세요."

try:
    response = polly_client.synthesize_speech(
        Text=message_text,
        OutputFormat='mp3',
        VoiceId='Seoyeon',
        Engine='neural',
        LanguageCode='ko-KR'
    )
    
    # 음성 파일 저장
    os.makedirs('voice_outputs', exist_ok=True)
    voice_file = f'voice_outputs/demo_fall_detected_{datetime.now().strftime("%H%M%S")}.mp3'
    
    with open(voice_file, 'wb') as file:
        file.write(response['AudioStream'].read())
    
    file_size = os.path.getsize(voice_file)
    print(f"✅ 음성 생성 완료!")
    print(f"   텍스트: {message_text}")
    print(f"   파일: {voice_file}")
    print(f"   크기: {file_size:,} bytes ({file_size/1024:.2f} KB)")
    print(f"   음성: Seoyeon (Neural TTS)")
    
    print("\n🔊 음성 재생 중...")
    print("   (실제 환경에서는 AI 스피커로 전송됨)")
    print("   → Alexa: 'Alexa, 안부 확인'")
    print("   → Google Home: 'OK Google, 안부 확인'")
    print("   → Clova: 'Clova, 안부 확인'")
    
except Exception as e:
    print(f"❌ Polly 오류: {str(e)}")

# ============================================================================
# STEP 4: 응답 시나리오 시뮬레이션
# ============================================================================
print("\n" + "=" * 80)
print("4️⃣ 응답 시나리오")
print("=" * 80)

print("\n⏳ 30초 동안 응답 대기 중...")
print("   (시뮬레이션을 위해 3초로 단축)")

for i in range(3):
    print(f"   {i+1}초...")
    time.sleep(1)

print("\n❓ 응답 시나리오 선택:")
print("   A. 정상 응답: '네, 괜찮아요'")
print("   B. 응답 없음: (타임아웃)")

# 시뮬레이션: 응답 없음 시나리오
print("\n⚠️  응답 없음! (30초 타임아웃)")
print("   → 보호자 알림 단계로 진행")

# 알림 상태 업데이트
alert_table.update_item(
    Key={'userId': user_id, 'alertId': alert_id},
    UpdateExpression='SET #status = :status',
    ExpressionAttributeNames={'#status': 'status'},
    ExpressionAttributeValues={':status': 'no_response'}
)

print("✅ 알림 상태 업데이트: no_response")

# ============================================================================
# STEP 5: 보호자 알림 발송
# ============================================================================
print("\n" + "=" * 80)
print("5️⃣ 보호자 알림 발송")
print("=" * 80)

notification_message = f"""
🚨 긴급 알림

김영희님(75세)에게 이상 징후가 감지되었습니다.

⚠️  낙상 의심 (가속도: 15.8)
⚠️  음성 응답 없음 (30초 타임아웃)
⚠️  즉시 확인이 필요합니다

📍 위치: 서울시 강남구 (자택)
🕐 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
📞 연락처: 010-1234-5678

[지금 확인하기] [위치 보기] [119 신고]
"""

print(notification_message)

print("📱 알림 채널:")
print("   ✅ SMS 발송 완료 (010-1234-5678)")
print("   ✅ 푸시 알림 발송 완료 (모바일 앱)")
print("   ✅ 이메일 발송 완료 (family@example.com)")

# ============================================================================
# STEP 6: 최종 상태 확인
# ============================================================================
print("\n" + "=" * 80)
print("6️⃣ 최종 상태 확인")
print("=" * 80)

# 센서 데이터 통계
sensor_response = sensor_table.query(
    KeyConditionExpression='userId = :uid',
    ExpressionAttributeValues={':uid': user_id},
    ScanIndexForward=False,
    Limit=20
)

print(f"\n📊 센서 데이터: {len(sensor_response['Items'])}개 (최근 20개)")

sensor_types = {}
for item in sensor_response['Items']:
    sensor_type = item.get('sensorType', 'unknown')
    sensor_types[sensor_type] = sensor_types.get(sensor_type, 0) + 1

for sensor_type, count in sorted(sensor_types.items(), key=lambda x: x[1], reverse=True):
    print(f"   - {sensor_type}: {count}개")

# 알림 통계
alert_response = alert_table.query(
    KeyConditionExpression='userId = :uid',
    ExpressionAttributeValues={':uid': user_id},
    ScanIndexForward=False,
    Limit=5
)

print(f"\n🔔 알림 이력: {len(alert_response['Items'])}개")
if alert_response['Items']:
    latest_alert = alert_response['Items'][0]
    print(f"   최신 알림:")
    print(f"   - ID: {latest_alert['alertId']}")
    print(f"   - 유형: {latest_alert.get('alertType', 'N/A')}")
    print(f"   - 상태: {latest_alert.get('status', 'N/A')}")
    print(f"   - 생성: {latest_alert.get('createdAt', 'N/A')}")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print("✨ 전체 워크플로우 데모 완료!")
print("=" * 80)

print("\n📋 실행된 단계:")
print("   1️⃣ 센서 데이터 수집 ✅")
print("   2️⃣ 활동 부재 감지 ✅ (낙상 감지!)")
print("   3️⃣ AI 스피커 음성 확인 ✅ (Polly 음성 생성)")
print("   4️⃣ 응답 없음 확인 ✅ (30초 타임아웃)")
print("   5️⃣ 보호자 알림 발송 ✅ (SMS/푸시/이메일)")

print("\n💡 대시보드에서 확인:")
print("   🌐 버전 1: http://localhost:8503")
print("      - 실시간 모니터링: 최근 활동 타임라인")
print("      - 알림 이력: 새로 생성된 알림")
print("      - 통계: 센서 데이터 분포")
print("")
print("   🌐 버전 2: http://localhost:8504")
print("      - 실시간 워크플로우 상태:")
print("        * 1단계: ✅ 정상 (초록)")
print("        * 2단계: ⚠️ 경고 (빨강) - 낙상 감지!")
print("        * 3단계: ⏳ 진행중 (주황) - 음성 확인 중")
print("        * 4단계: ⚠️ 경고 (빨강) - 알림 발송 필요")
print("")
print("      - AI 스피커 음성 확인:")
print("        * 음성 메시지 선택 및 재생")
print("        * 5가지 시나리오 음성 파일")
print("")
print("      - 워크플로우 시뮬레이션:")
print("        * ✅ 정상 응답 버튼")
print("        * ⚠️ 응답 없음 버튼")
print("        * 📤 긴급 알림 발송 버튼")
print("        * ✔️ 상황 종료 버튼")

print("\n🎵 생성된 음성 파일:")
voice_dir = 'voice_outputs'
if os.path.exists(voice_dir):
    voice_files = [f for f in os.listdir(voice_dir) if f.endswith('.mp3')]
    for vf in voice_files:
        file_path = os.path.join(voice_dir, vf)
        file_size = os.path.getsize(file_path)
        print(f"   - {vf} ({file_size/1024:.2f} KB)")

print("\n🔄 다음 단계:")
print("   1. 대시보드 새로고침 (F5)")
print("   2. 버전 2에서 음성 재생 테스트")
print("   3. 워크플로우 버튼으로 시나리오 진행")
print("   4. 실시간 상태 변화 확인")

print("\n" + "=" * 80)
print("🎉 데모 완료! 맛있게 드세요! 🍚")
print("=" * 80)
