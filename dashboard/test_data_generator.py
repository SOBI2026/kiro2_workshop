"""
Generate test data for Senior Care Monitoring System
"""
import boto3
import json
import random
from datetime import datetime, timedelta
import time

# AWS clients
dynamodb = boto3.resource('dynamodb')
sensor_table = dynamodb.Table('SeniorCare-SensorData')
settings_table = dynamodb.Table('SeniorCare-UserSettings')

def create_test_user(user_id, name):
    """Create test user in UserSettings"""
    settings_table.put_item(Item={
        'userId': user_id,
        'name': name,
        'age': 75,
        'phone': '010-1234-5678',
        'inactivityThreshold': 120,
        'voiceResponseTimeout': 30,
        'lastActivityTime': datetime.utcnow().isoformat(),
        'status': 'active',
        'createdAt': datetime.utcnow().isoformat(),
        'updatedAt': datetime.utcnow().isoformat()
    })
    print(f"Created test user: {user_id}")

def generate_sensor_data(user_id, device_id, count=50):
    """Generate random sensor data"""
    sensor_types = ['accelerometer', 'motion', 'door', 'temperature']
    device_types = ['mobile', 'iot']
    
    print(f"Generating {count} sensor data points...")
    
    for i in range(count):
        timestamp = datetime.utcnow() - timedelta(hours=random.randint(0, 24))
        ttl = int((datetime.utcnow() + timedelta(days=30)).timestamp())
        
        sensor_table.put_item(Item={
            'userId': user_id,
            'timestamp': int(timestamp.timestamp()),
            'deviceId': device_id,
            'deviceType': random.choice(device_types),
            'sensorType': random.choice(sensor_types),
            'value': round(random.uniform(0.5, 5.0), 2),
            'ttl': ttl
        })
        
        if (i + 1) % 10 == 0:
            print(f"  Generated {i + 1}/{count}")
        
        time.sleep(0.1)  # Avoid throttling
    
    print(f"✅ Generated {count} sensor data points")

if __name__ == '__main__':
    user_id = 'test-user-001'
    device_id = 'device-001'
    
    print("=== Test Data Generator ===\n")
    
    # Create test user
    create_test_user(user_id, '김영희')
    
    # Generate sensor data
    generate_sensor_data(user_id, device_id, count=50)
    
    print("\n✅ Test data generation complete!")
    print(f"User ID: {user_id}")
    print(f"Device ID: {device_id}")
