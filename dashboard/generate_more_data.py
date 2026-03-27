import boto3
from datetime import datetime, timedelta
from decimal import Decimal
import random

print("=" * 70)
print("📊 추가 센서 데이터 생성")
print("=" * 70)

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
sensor_table = dynamodb.Table('SeniorCare-SensorData')
user_settings_table = dynamodb.Table('SeniorCare-UserSettings')

user_id = 'test-user-001'

# 지난 24시간 동안의 데이터 생성
print("\n지난 24시간 동안의 활동 데이터 생성 중...")

base_time = datetime.utcnow()
data_count = 0

# 시간대별로 다양한 활동 패턴 생성
for hour_offset in range(24, 0, -1):
    current_time = base_time - timedelta(hours=hour_offset)
    
    # 시간대별 활동 패턴
    if 0 <= current_time.hour < 6:  # 새벽 (수면)
        activity_level = 0.1
        frequency = 1  # 1개/시간
    elif 6 <= current_time.hour < 9:  # 아침 (활동 증가)
        activity_level = 2.5
        frequency = 6  # 6개/시간
    elif 9 <= current_time.hour < 12:  # 오전 (활발)
        activity_level = 3.0
        frequency = 8
    elif 12 <= current_time.hour < 14:  # 점심 (활발)
        activity_level = 2.8
        frequency = 7
    elif 14 <= current_time.hour < 18:  # 오후 (보통)
        activity_level = 2.0
        frequency = 5
    elif 18 <= current_time.hour < 22:  # 저녁 (활발)
        activity_level = 2.5
        frequency = 6
    else:  # 밤 (감소)
        activity_level = 1.0
        frequency = 2
    
    # 해당 시간대에 여러 센서 데이터 생성
    for i in range(frequency):
        timestamp = int((current_time + timedelta(minutes=i*10)).timestamp())
        
        # 다양한 센서 타입 랜덤 선택
        sensor_types = [
            ('motion', 'motion-sensor-001', 'iot', activity_level * random.uniform(0.8, 1.2)),
            ('door', 'door-sensor-001', 'iot', random.choice([0.0, 1.0])),
            ('accelerometer', 'phone-001', 'mobile', activity_level * random.uniform(0.5, 1.5)),
            ('temperature', 'temp-sensor-001', 'iot', random.uniform(20.0, 25.0))
        ]
        
        sensor_type, device_id, device_type, value = random.choice(sensor_types)
        
        item = {
            'userId': user_id,
            'timestamp': timestamp,
            'deviceId': device_id,
            'deviceType': device_type,
            'sensorType': sensor_type,
            'value': Decimal(str(round(value, 2)))
        }
        
        sensor_table.put_item(Item=item)
        data_count += 1
        
        if data_count % 20 == 0:
            print(f"   {data_count}개 데이터 생성 완료...")

# 마지막 활동 시간 업데이트
user_settings_table.update_item(
    Key={'userId': user_id},
    UpdateExpression='SET lastActivityTime = :lat',
    ExpressionAttributeValues={':lat': datetime.utcnow().isoformat() + 'Z'}
)

print(f"\n✅ 총 {data_count}개의 센서 데이터 생성 완료!")
print("\n📊 생성된 데이터 분포:")
print(f"   - 새벽 (00-06시): 낮은 활동 (수면)")
print(f"   - 아침 (06-09시): 증가하는 활동")
print(f"   - 오전 (09-12시): 높은 활동")
print(f"   - 점심 (12-14시): 높은 활동")
print(f"   - 오후 (14-18시): 보통 활동")
print(f"   - 저녁 (18-22시): 증가하는 활동")
print(f"   - 밤 (22-24시): 감소하는 활동")

print("\n💡 대시보드에서 확인:")
print("   - 버전 1 (http://localhost:8503):")
print("     * 통계 탭: 시간대별 활동 분포 그래프")
print("     * 통계 탭: 센서 타입별 분포 파이 차트")
print("     * 통계 탭: 24시간 활동 타임라인")
print("   - 버전 2 (http://localhost:8504):")
print("     * 실시간 시스템 현황: 센서 데이터 수 증가")

print("\n" + "=" * 70)
