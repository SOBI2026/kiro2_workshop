import requests
import json
from datetime import datetime

API_BASE_URL = "https://cl4yut77le.execute-api.us-east-1.amazonaws.com/prod"

print("=" * 60)
print("API Gateway 엔드포인트 테스트")
print("=" * 60)
print(f"Base URL: {API_BASE_URL}\n")

# Test 1: POST /sensor-data - 센서 데이터 전송
print("[Test 1] POST /sensor-data - 센서 데이터 전송")
print("-" * 60)

payload = {
    'userId': 'test-user-001',
    'deviceId': 'device-api-test',
    'deviceType': 'mobile',
    'sensorType': 'motion',
    'value': 4.2,
    'timestamp': datetime.utcnow().isoformat()
}

try:
    response = requests.post(
        f"{API_BASE_URL}/sensor-data",
        json=payload,
        headers={'Content-Type': 'application/json'},
        timeout=10
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        print("✅ 센서 데이터 전송 성공!")
    else:
        print(f"❌ 실패: {response.status_code}")
        
except Exception as e:
    print(f"❌ 에러: {e}")

# Test 2: GET /activity-history - 활동 이력 조회
print("\n[Test 2] GET /activity-history - 활동 이력 조회")
print("-" * 60)

params = {
    'userId': 'test-user-001',
    'startTime': int((datetime.utcnow().timestamp() - 86400)),  # 24시간 전
    'endTime': int(datetime.utcnow().timestamp())
}

try:
    response = requests.get(
        f"{API_BASE_URL}/activity-history",
        params=params,
        timeout=10
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 활동 이력 조회 성공!")
        print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
    else:
        print(f"❌ 실패: {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    print(f"❌ 에러: {e}")

# Test 3: GET /settings - 사용자 설정 조회
print("\n[Test 3] GET /settings - 사용자 설정 조회")
print("-" * 60)

params = {'userId': 'test-user-001'}

try:
    response = requests.get(
        f"{API_BASE_URL}/settings",
        params=params,
        timeout=10
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 사용자 설정 조회 성공!")
        print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
    else:
        print(f"❌ 실패: {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    print(f"❌ 에러: {e}")

# Test 4: PUT /settings - 사용자 설정 업데이트
print("\n[Test 4] PUT /settings - 사용자 설정 업데이트")
print("-" * 60)

payload = {
    'userId': 'test-user-001',
    'inactivityThreshold': 180
}

try:
    response = requests.put(
        f"{API_BASE_URL}/settings",
        json=payload,
        headers={'Content-Type': 'application/json'},
        timeout=10
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        print("✅ 사용자 설정 업데이트 성공!")
    else:
        print(f"❌ 실패: {response.status_code}")
        
except Exception as e:
    print(f"❌ 에러: {e}")

# Summary
print("\n" + "=" * 60)
print("API 테스트 완료!")
print("=" * 60)
