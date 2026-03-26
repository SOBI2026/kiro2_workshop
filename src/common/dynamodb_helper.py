import boto3
import os
from datetime import datetime, timedelta
from decimal import Decimal
from .error_handler import exponential_backoff_retry
from .logger import get_logger

logger = get_logger(__name__)

class DynamoDBHelper:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.sensor_data_table = self.dynamodb.Table(os.environ['DYNAMODB_SENSOR_DATA_TABLE'])
        self.user_settings_table = self.dynamodb.Table(os.environ['DYNAMODB_USER_SETTINGS_TABLE'])
        self.alert_history_table = self.dynamodb.Table(os.environ['DYNAMODB_ALERT_HISTORY_TABLE'])
    
    @exponential_backoff_retry(max_retries=10)
    def put_sensor_data(self, user_id, timestamp, device_id, device_type, sensor_type, value):
        """Store sensor data with TTL"""
        ttl = int((datetime.utcnow() + timedelta(days=30)).timestamp())
        
        # Convert float to Decimal for DynamoDB
        # Handle very small/large values that cause Decimal underflow/overflow
        if isinstance(value, float):
            # Clamp to reasonable range to avoid Decimal issues
            if abs(value) < 1e-28:  # Too small, treat as 0
                value = Decimal('0')
            elif abs(value) > 1e28:  # Too large, clamp
                value = Decimal('1e28') if value > 0 else Decimal('-1e28')
            else:
                value = Decimal(str(value))
        
        item = {
            'userId': user_id,
            'timestamp': int(timestamp),
            'deviceId': device_id,
            'deviceType': device_type,
            'sensorType': sensor_type,
            'value': value,
            'ttl': ttl
        }
        
        self.sensor_data_table.put_item(Item=item)
        logger.info(f"Stored sensor data for user {user_id}")
        return item
    
    @exponential_backoff_retry(max_retries=10)
    def update_last_activity_time(self, user_id, timestamp):
        """Update user's last activity time"""
        iso_timestamp = datetime.fromtimestamp(timestamp).isoformat()
        
        self.user_settings_table.update_item(
            Key={'userId': user_id},
            UpdateExpression='SET lastActivityTime = :lat, updatedAt = :ua',
            ExpressionAttributeValues={
                ':lat': iso_timestamp,
                ':ua': datetime.utcnow().isoformat()
            }
        )
        logger.info(f"Updated last activity time for user {user_id}")
    
    @exponential_backoff_retry(max_retries=10)
    def get_user_settings(self, user_id):
        """Get user settings"""
        response = self.user_settings_table.get_item(Key={'userId': user_id})
        return response.get('Item')
    
    @exponential_backoff_retry(max_retries=10)
    def query_active_users(self):
        """Query all active users"""
        response = self.user_settings_table.query(
            IndexName='status-lastActivityTime-index',
            KeyConditionExpression='#status = :status',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={':status': 'active'}
        )
        return response.get('Items', [])
    
    @exponential_backoff_retry(max_retries=10)
    def create_alert(self, user_id, alert_id, alert_type, last_activity_time):
        """Create alert in history"""
        ttl = int((datetime.utcnow() + timedelta(days=90)).timestamp())
        
        item = {
            'userId': user_id,
            'alertId': alert_id,
            'alertType': alert_type,
            'status': 'voice_confirmation_pending',
            'createdAt': datetime.utcnow().isoformat(),
            'lastActivityTime': last_activity_time,
            'retryCount': 0,
            'ttl': ttl
        }
        
        self.alert_history_table.put_item(Item=item)
        logger.info(f"Created alert {alert_id} for user {user_id}")
        return item
    
    @exponential_backoff_retry(max_retries=10)
    def update_alert_status(self, user_id, alert_id, status, **kwargs):
        """Update alert status"""
        update_expr = 'SET #status = :status, updatedAt = :ua'
        expr_attr_names = {'#status': 'status'}
        expr_attr_values = {
            ':status': status,
            ':ua': datetime.utcnow().isoformat()
        }
        
        for key, value in kwargs.items():
            update_expr += f', {key} = :{key}'
            expr_attr_values[f':{key}'] = value
        
        self.alert_history_table.update_item(
            Key={'userId': user_id, 'alertId': alert_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_attr_names,
            ExpressionAttributeValues=expr_attr_values
        )
        logger.info(f"Updated alert {alert_id} status to {status}")
    
    @exponential_backoff_retry(max_retries=10)
    def get_pending_alerts(self, user_id):
        """Get pending alerts for user"""
        response = self.alert_history_table.query(
            IndexName='status-createdAt-index',
            KeyConditionExpression='#status = :status',
            FilterExpression='userId = :uid',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'voice_confirmation_pending',
                ':uid': user_id
            }
        )
        return response.get('Items', [])

    @exponential_backoff_retry(max_retries=10)
    def get_sensor_data(self, user_id, timestamp):
        """Get sensor data by userId and timestamp"""
        response = self.sensor_data_table.get_item(
            Key={
                'userId': user_id,
                'timestamp': int(timestamp)
            }
        )
        return response.get('Item')

    @exponential_backoff_retry(max_retries=10)
    def put_user_settings(self, user_id, **settings):
        """Create or update user settings"""
        item = {
            'userId': user_id,
            'status': 'active',  # Default to active
            'createdAt': datetime.utcnow().isoformat(),
            'updatedAt': datetime.utcnow().isoformat(),
            **settings
        }
        self.user_settings_table.put_item(Item=item)
        logger.info(f"Stored user settings for user {user_id}")
        return item
