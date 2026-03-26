import psycopg2
import json
import os
import boto3
from contextlib import contextmanager
from .error_handler import exponential_backoff_retry
from .logger import get_logger

logger = get_logger(__name__)

class RDSHelper:
    def __init__(self):
        self.secret_arn = os.environ['RDS_SECRET_ARN']
        self._connection = None
    
    def _get_credentials(self):
        """Get RDS credentials from Secrets Manager"""
        client = boto3.client('secretsmanager')
        response = client.get_secret_value(SecretId=self.secret_arn)
        return json.loads(response['SecretString'])
    
    @exponential_backoff_retry(max_retries=3)
    def _connect(self):
        """Establish RDS connection with retry"""
        if self._connection is None or self._connection.closed:
            creds = self._get_credentials()
            self._connection = psycopg2.connect(
                host=creds['host'],
                port=creds.get('port', 5432),
                database=creds.get('dbname', 'seniorcare'),
                user=creds['username'],
                password=creds['password'],
                connect_timeout=10
            )
            logger.info("Connected to RDS")
        return self._connection
    
    @contextmanager
    def get_connection(self):
        """Context manager for RDS connection"""
        conn = self._connect()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"RDS transaction failed: {str(e)}")
            raise
    
    def insert_activity_log(self, user_id, activity_type, device_type, device_id, sensor_type, value, timestamp):
        """Insert activity log record"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO activity_log 
                (user_id, activity_type, device_type, device_id, sensor_type, value, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (user_id, activity_type, device_type, device_id, sensor_type, value, timestamp))
            logger.info(f"Inserted activity log for user {user_id}")
    
    def get_guardians(self, user_id):
        """Get all guardians for a user (max 5)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT guardian_id, name, phone, email, push_token, device_type
                FROM guardians
                WHERE user_id = %s AND notification_enabled = true
                LIMIT 5
            """, (user_id,))
            
            columns = [desc[0] for desc in cursor.description]
            results = cursor.fetchall()
            return [dict(zip(columns, row)) for row in results]
    
    def check_guardian_permission(self, guardian_phone, user_id):
        """Check if guardian has permission to access user data"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM guardians
                WHERE user_id = %s AND phone = %s
            """, (user_id, guardian_phone))
            count = cursor.fetchone()[0]
            return count > 0
    
    def get_activity_history(self, user_id, start_date, end_date):
        """Get activity history for date range"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT log_id, activity_type, device_type, device_id, 
                       sensor_type, value, timestamp, created_at
                FROM activity_log
                WHERE user_id = %s AND timestamp BETWEEN %s AND %s
                ORDER BY timestamp DESC
            """, (user_id, start_date, end_date))
            
            columns = [desc[0] for desc in cursor.description]
            results = cursor.fetchall()
            return [dict(zip(columns, row)) for row in results]
