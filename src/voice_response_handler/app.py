import json
import os
import sys
import boto3
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from common.logger import get_logger
from common.error_handler import handle_lambda_error, ValidationError
from common.dynamodb_helper import DynamoDBHelper

logger = get_logger(__name__)
lambda_client = boto3.client('lambda')

@handle_lambda_error
def lambda_handler(event, context):
    """
    Handle AI speaker voice confirmation
    
    Two modes:
    1. Initiate voice confirmation (from InactivityDetector)
    2. Process voice response (from AI speaker API)
    """
    logger.info(f"Voice response handler invoked: {json.dumps(event)}")
    
    # Parse body if from API Gateway
    if 'body' in event:
        body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
    else:
        body = event
    
    # Validate required fields
    if 'userId' not in body or 'alertId' not in body:
        raise ValidationError("Missing required fields: userId, alertId")
    
    user_id = body['userId']
    alert_id = body['alertId']
    
    dynamodb = DynamoDBHelper()
    
    # Check if this is a voice response or initiation
    if 'response' in body:
        # Process voice response
        response_text = body['response']
        timestamp = body.get('timestamp', datetime.utcnow().isoformat())
        
        logger.info(f"Processing voice response for alert {alert_id}: {response_text}")
        
        # Update alert status to confirmed_safe
        dynamodb.update_alert_status(
            user_id=user_id,
            alert_id=alert_id,
            status='confirmed_safe',
            voiceResponseReceivedAt=timestamp
        )
        
        logger.info(f"Alert {alert_id} marked as confirmed_safe")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Voice confirmation processed',
                'status': 'confirmed_safe'
            })
        }
    else:
        # Initiate voice confirmation
        logger.info(f"Initiating voice confirmation for alert {alert_id}")
        
        # Get user settings for timeout
        user_settings = dynamodb.get_user_settings(user_id)
        voice_timeout = user_settings.get('voiceResponseTimeout', 30) if user_settings else 30
        
        # Update alert with voice confirmation sent timestamp
        dynamodb.update_alert_status(
            user_id=user_id,
            alert_id=alert_id,
            status='voice_confirmation_pending',
            voiceConfirmationSentAt=datetime.utcnow().isoformat()
        )
        
        # TODO: Call AI Speaker API (Alexa/Google/Clova)
        # For now, simulate timeout scenario
        # In production, this would:
        # 1. Call AI speaker API with prompt: "안녕하세요, 괜찮으신가요?"
        # 2. Wait for response or timeout
        # 3. If response received, update status to confirmed_safe
        # 4. If timeout or no response, trigger NotificationManager
        
        logger.warning(f"AI Speaker API not implemented - simulating timeout for alert {alert_id}")
        
        # Simulate timeout - trigger NotificationManager
        try:
            # Update alert status to no_response
            dynamodb.update_alert_status(
                user_id=user_id,
                alert_id=alert_id,
                status='no_response'
            )
            
            # Trigger NotificationManager
            lambda_client.invoke(
                FunctionName=os.environ.get('NOTIFICATION_MANAGER_FUNCTION', 'SeniorCare-NotificationManager'),
                InvocationType='Event',  # Async
                Payload=json.dumps({
                    'userId': user_id,
                    'alertId': alert_id,
                    'alertType': 'no_response',
                    'lastActivityTime': user_settings.get('lastActivityTime') if user_settings else None,
                    'retryCount': 0
                })
            )
            
            logger.info(f"Triggered NotificationManager for alert {alert_id}")
        except Exception as e:
            logger.error(f"Error triggering NotificationManager: {str(e)}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Voice confirmation initiated',
                'status': 'no_response',
                'timeout': voice_timeout
            })
        }
