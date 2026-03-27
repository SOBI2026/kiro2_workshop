import boto3
import json
from datetime import datetime

lambda_client = boto3.client('lambda', region_name='us-east-1')

payload = {
    'userId': 'test-user-001',
    'deviceId': 'device-001',
    'deviceType': 'mobile',
    'sensorType': 'motion',
    'value': 1.5,
    'timestamp': datetime.utcnow().isoformat()
}

print(f"Sending payload: {json.dumps(payload, indent=2)}")

try:
    response = lambda_client.invoke(
        FunctionName='SeniorCare-SensorDataProcessor',
        InvocationType='RequestResponse',
        Payload=json.dumps(payload)
    )
    
    result = json.loads(response['Payload'].read())
    print(f"\nResponse: {json.dumps(result, indent=2)}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
