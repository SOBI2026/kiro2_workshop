import boto3
import json
from datetime import datetime
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
import requests

# AWS 자격증명
session = boto3.Session()
credentials = session.get_credentials()

API_BASE_URL = "https://cl4yut77le.execute-api.us-east-1.amazonaws.com/prod"
REGION = "us-east-1"

def sign_request(method, url, data=None):
    """AWS SigV4로 요청 서명"""
    request = AWSRequest(method=method, url=url, data=data, headers={'Content-Type': 'application/json'})
    SigV4Auth(credentials, 'execute-api', REGION).add_auth(request)
    return dict(request.headers)

print("=" * 60)
print("API Gateway 엔드포인트 테스트 (AWS IAM 인증)")
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
    url = f"{API_BASE_URL}/sensor-data"
    data = json.dumps(payload)
    headers = sign_request('POST', url, data)
    
    response = requests.post(url, data=data, headers=headers, timeout=10)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        print("✅ 센서 데이터 전송 성공!")
    else:
        print(f"❌ 실패: {response.status_code}")
        
except Exception as e:
    print(f"❌ 에러: {e}")
    import traceback
    traceback.print_exc()

# Test 2: GET /activity-history - 활동 이력 조회
print("\n[Test 2] GET /activity-history - 활동 이력 조회")
print("-" * 60)

try:
    params = {
        'userId': 'test-user-001',
        'guardianPhone': '+821012345678',
        'startTime': str(int((datetime.utcnow().timestamp() - 86400))),
        'endTime': str(int(datetime.utcnow().timestamp()))
    }
    
    url = f"{API_BASE_URL}/activity-history?userId={params['userId']}&guardianPhone={params['guardianPhone']}&startTime={params['startTime']}&endTime={params['endTime']}"
    headers = sign_request('GET', url)
    
    response = requests.get(url, headers=headers, timeout=10)
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 활동 이력 조회 성공!")
        print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}")
    else:
        print(f"❌ 실패: {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    print(f"❌ 에러: {e}")
    import traceback
    traceback.print_exc()

# Test 3: PUT /settings - 사용자 설정 업데이트
print("\n[Test 3] PUT /settings - 사용자 설정 업데이트")
print("-" * 60)

payload = {
    'userId': 'test-user-001',
    'action': 'update_settings',
    'inactivityThreshold': 200
}

try:
    url = f"{API_BASE_URL}/settings"
    data = json.dumps(payload)
    headers = sign_request('PUT', url, data)
    
    response = requests.put(url, data=data, headers=headers, timeout=10)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        print("✅ 사용자 설정 업데이트 성공!")
    else:
        print(f"❌ 실패: {response.status_code}")
        
except Exception as e:
    print(f"❌ 에러: {e}")
    import traceback
    traceback.print_exc()

# Summary
print("\n" + "=" * 60)
print("API 테스트 완료!")
print("=" * 60)
print("\n참고: API Gateway는 AWS IAM 인증을 사용하고 있습니다.")
print("외부에서 접근하려면 AWS 자격증명이 필요합니다.")
