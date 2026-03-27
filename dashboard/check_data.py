import boto3
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

# Check SensorData
print("=== SensorData 테이블 확인 ===")
sensor_table = dynamodb.Table('SeniorCare-SensorData')
try:
    response = sensor_table.query(
        KeyConditionExpression='userId = :uid',
        ExpressionAttributeValues={':uid': 'test-user-001'},
        Limit=5
    )
    print(f"Found {len(response['Items'])} sensor data items")
    for item in response['Items'][:2]:
        print(f"  - timestamp: {item.get('timestamp')}, sensorType: {item.get('sensorType')}, value: {item.get('value')}")
except Exception as e:
    print(f"Error: {e}")

# Check UserSettings
print("\n=== UserSettings 테이블 확인 ===")
settings_table = dynamodb.Table('SeniorCare-UserSettings')
try:
    response = settings_table.get_item(Key={'userId': 'test-user-001'})
    if 'Item' in response:
        item = response['Item']
        print(f"User: {item.get('name')}")
        print(f"Status: {item.get('status')}")
        print(f"Last Activity: {item.get('lastActivityTime')}")
    else:
        print("User not found")
except Exception as e:
    print(f"Error: {e}")
