"""
대시보드 3 없이 자동 워크플로우를 실행하는 스크립트
백엔드 대시보드(8503)에서 알람을 확인할 수 있습니다
"""
import boto3
import time
from datetime import datetime
from decimal import Decimal
import uuid

print("=" * 60)
print("시니어 안심 케어 - 자동 워크플로우 실행")
print("=" * 60)
print()

# AWS 클라이언트 초기화
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
polly_client = boto3.client('polly', region_name='us-east-1')
sns_client = boto3.client('sns', region_name='us-east-1')

user_id = 'test-user-001'
sensor_table = dynamodb.Table('SeniorCare-SensorData')
user_settings_table = dynamodb.Table('SeniorCare-UserSettings')
alert_table = dynamodb.Table('SeniorCare-AlertHistory')

# Step 1: 센서 데이터 수집
print("📊 STEP 1: 센서 데이터 수집")
print("-" * 60)

activities = [
    ("motion", 2.5, "거실에서 TV 시청"),
    ("door", 1.0, "방문 열림"),
    ("temperature", 22.5, "실내 온도 정상")
]

for sensor_type, value, desc in activities:
    item = {
        'userId': user_id,
        'timestamp': int(datetime.utcnow().timestamp()),
        'deviceId': f'{sensor_type}-sensor-001',
        'deviceType': 'iot',
        'sensorType': sensor_type,
        'value': Decimal(str(value))
    }
    sensor_table.put_item(Item=item)
    user_settings_table.update_item(
        Key={'userId': user_id},
        UpdateExpression='SET lastActivityTime = :lat',
        ExpressionAttributeValues={':lat': datetime.utcnow().isoformat() + 'Z'}
    )
    print(f"✅ {desc}: {sensor_type} = {value}")
    time.sleep(0.5)

print("✨ 정상 활동 데이터 수집 완료")
print()
time.sleep(2)

# Step 2: 낙상 감지
print("🚨 STEP 2: 낙상 감지")
print("-" * 60)

# 화장실 이동
item = {
    'userId': user_id,
    'timestamp': int(datetime.utcnow().timestamp()),
    'deviceId': 'door-sensor-bathroom',
    'deviceType': 'iot',
    'sensorType': 'door',
    'value': Decimal('1.0')
}
sensor_table.put_item(Item=item)
print("🚶 화장실로 이동...")
time.sleep(1)

# 낙상 발생
item = {
    'userId': user_id,
    'timestamp': int(datetime.utcnow().timestamp()),
    'deviceId': 'phone-001',
    'deviceType': 'mobile',
    'sensorType': 'accelerometer',
    'value': Decimal('15.8')
}
sensor_table.put_item(Item=item)
print("🚨 낙상 발생! 가속도: 15.8 (임계값 10.0 초과)")
time.sleep(1)

# 활동 부재
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
    print(f"⏰ {i+1}분: 움직임 거의 없음 (motion = 0.05)")
    time.sleep(0.8)

# 알림 생성
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
print(f"✅ 알림 생성: {alert_id[:8]}...")
print()
time.sleep(2)

# Step 3: AI 스피커 음성 확인
print("🗣️ STEP 3: AI 스피커 음성 확인")
print("-" * 60)

message_text = "김영희님, 넘어지신 것 같습니다. 괜찮으신가요? 응답해주세요."
print(f"🗣️ Polly 음성 생성 중...")
print(f"   텍스트: {message_text}")

try:
    response = polly_client.synthesize_speech(
        Text=message_text,
        OutputFormat='mp3',
        VoiceId='Seoyeon',
        Engine='neural',
        LanguageCode='ko-KR'
    )
    
    import os
    os.makedirs('voice_outputs', exist_ok=True)
    voice_file = f'voice_outputs/auto_workflow_{datetime.now().strftime("%H%M%S")}.mp3'
    with open(voice_file, 'wb') as file:
        file.write(response['AudioStream'].read())
    
    print(f"✅ 음성 생성 완료: {voice_file}")
    print("🔊 AI 스피커로 음성 전송 중...")
except Exception as e:
    print(f"❌ Polly 오류: {str(e)}")

time.sleep(2)

# 응답 대기
print("⏳ 30초 동안 응답 대기 중... (시뮬레이션: 3초)")
for i in range(3):
    print(f"   {i+1}초...")
    time.sleep(1)

# 응답 없음
print("⚠️ 응답 없음! (30초 타임아웃)")

alert_table.update_item(
    Key={'userId': user_id, 'alertId': alert_id},
    UpdateExpression='SET #status = :status',
    ExpressionAttributeNames={'#status': 'status'},
    ExpressionAttributeValues={':status': 'no_response'}
)
print("✅ 알림 상태 업데이트: no_response")
print()
time.sleep(2)

# Step 4: 보호자 알림 발송
print("📱 STEP 4: 보호자 알림 발송")
print("-" * 60)

notification_message = f"""🚨 긴급 알림

김영희님(75세)에게 이상 징후가 감지되었습니다.

⚠️ 낙상 의심 (가속도: 15.8)
⚠️ 음성 응답 없음
⚠️ 즉시 확인이 필요합니다

📍 위치: 서울시 강남구 (자택)
🕐 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

[지금 확인하기]"""

print("📱 긴급 알림 메시지 생성 완료")

# 실제 SMS 발송
try:
    print("📤 SMS 발송 중... (010-3328-4472)")
    
    response = sns_client.publish(
        PhoneNumber='+821033284472',
        Message=notification_message,
        MessageAttributes={
            'AWS.SNS.SMS.SMSType': {
                'DataType': 'String',
                'StringValue': 'Transactional'
            }
        }
    )
    
    print(f"✅ SMS 발송 완료! MessageId: {response['MessageId'][:20]}...")
except Exception as e:
    print(f"❌ SMS 발송 오류: {str(e)}")
    print("   (AWS SNS 권한 또는 설정을 확인하세요)")

print("✅ 푸시 알림 발송 완료 (시뮬레이션)")
print("✅ 이메일 발송 완료 (시뮬레이션)")
print()
time.sleep(2)

# 완료
print("=" * 60)
print("✨ 워크플로우 완료!")
print("=" * 60)
print()
print("📊 백엔드 대시보드에서 확인:")
print("   1. http://localhost:8503 접속")
print("   2. '알림 이력' 탭 클릭")
print(f"   3. 알림 ID: {alert_id[:8]}... 확인")
print()
print("🔄 대시보드를 새로고침하여 최신 상태를 확인하세요.")
