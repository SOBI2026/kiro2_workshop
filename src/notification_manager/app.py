import json
import os
import sys
import boto3
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from common.logger import get_logger
from common.error_handler import handle_lambda_error, ValidationError
from common.dynamodb_helper import DynamoDBHelper
from common.rds_helper import RDSHelper

logger = get_logger(__name__)
sns_client = boto3.client('sns')
sqs_client = boto3.client('sqs')

@handle_lambda_error
def lambda_handler(event, context):
    """
    Send emergency notifications to guardians
    
    Expected input:
    {
        "userId": "string",
        "alertId": "string",
        "alertType": "no_response" | "manual_emergency",
        "lastActivityTime": "ISO8601 string",
        "retryCount": number
    }
    """
    logger.info(f"Processing notification: {json.dumps(event)}")
    
    # Parse body if from API Gateway or SQS
    if 'body' in event:
        body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
    elif 'Records' in event:
        # SQS batch processing
        body = json.loads(event['Records'][0]['body'])
    else:
        body = event
    
    # Validate required fields
    required_fields = ['userId', 'alertId', 'alertType']
    for field in required_fields:
        if field not in body:
            raise ValidationError(f"Missing required field: {field}")
    
    user_id = body['userId']
    alert_id = body['alertId']
    alert_type = body['alertType']
    last_activity_time = body.get('lastActivityTime', 'Unknown')
    retry_count = body.get('retryCount', 0)
    
    dynamodb = DynamoDBHelper()
    rds = RDSHelper()
    
    # Get user info
    user_settings = dynamodb.get_user_settings(user_id)
    user_name = user_settings.get('name', 'Unknown User') if user_settings else 'Unknown User'
    
    # Get guardians from RDS
    guardians = rds.get_guardians(user_id)
    logger.info(f"Found {len(guardians)} guardians for user {user_id}")
    
    if not guardians:
        logger.warning(f"No guardians found for user {user_id}")
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'No guardians to notify',
                'sentCount': 0,
                'failedCount': 0
            })
        }
    
    # Create notification message
    message = {
        'userName': user_name,
        'userId': user_id,
        'alertType': alert_type,
        'lastActivityTime': last_activity_time,
        'currentTime': datetime.utcnow().isoformat(),
        'alertId': alert_id
    }
    
    message_text = f"""
[긴급 알림] {user_name}님의 안전 확인이 필요합니다.

알림 유형: {alert_type}
마지막 활동 시간: {last_activity_time}
현재 시간: {message['currentTime']}

즉시 확인해 주시기 바랍니다.
    """.strip()
    
    # Send notifications to all guardians
    sent_count = 0
    failed_count = 0
    
    try:
        # Publish to SNS topic
        sns_client.publish(
            TopicArn=os.environ['SNS_ALERT_TOPIC_ARN'],
            Subject=f'[긴급] {user_name}님 안전 확인 필요',
            Message=message_text,
            MessageAttributes={
                'userId': {'DataType': 'String', 'StringValue': user_id},
                'alertId': {'DataType': 'String', 'StringValue': alert_id},
                'alertType': {'DataType': 'String', 'StringValue': alert_type}
            }
        )
        
        sent_count = len(guardians)
        logger.info(f"Published notification to SNS topic for {sent_count} guardians")
        
        # Update alert history
        dynamodb.update_alert_status(
            user_id=user_id,
            alert_id=alert_id,
            status='no_response',
            notificationSentAt=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error sending notification: {str(e)}")
        failed_count = len(guardians)
        
        # Retry logic
        if retry_count < 3:
            # Add to SQS for retry
            try:
                retry_message = body.copy()
                retry_message['retryCount'] = retry_count + 1
                
                sqs_client.send_message(
                    QueueUrl=os.environ['SQS_NOTIFICATION_QUEUE_URL'],
                    MessageBody=json.dumps(retry_message),
                    DelaySeconds=300  # 5 minutes
                )
                logger.info(f"Added to SQS for retry (attempt {retry_count + 1}/3)")
            except Exception as sqs_error:
                logger.error(f"Error adding to SQS: {str(sqs_error)}")
        else:
            # Max retries exceeded - will go to DLQ automatically
            logger.error(f"Max retries exceeded for alert {alert_id}")
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Notifications processed',
            'sentCount': sent_count,
            'failedCount': failed_count,
            'retryCount': retry_count
        })
    }
