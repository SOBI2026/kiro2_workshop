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
polly_client = boto3.client('polly')

def generate_voice_message(user_name, alert_type):
    """
    Generate voice message using AWS Polly
    
    Args:
        user_name: User's name
        alert_type: Type of alert (inactivity, fall_detected, etc.)
    
    Returns:
        Audio stream from Polly
    """
    # Message templates
    messages = {
        'inactivity': f"안녕하세요, {user_name}님. 2시간 동안 움직임이 감지되지 않았습니다. 안전하신가요?",
        'fall_detected': f"{user_name}님, 넘어지신 것 같습니다. 괜찮으신가요? 응답해주세요.",
        'emergency': f"긴급 상황이 감지되었습니다. 즉시 응답해주세요. 응답이 없으면 보호자에게 연락하겠습니다.",
        'default': f"안녕하세요, {user_name}님. 괜찮으신가요?"
    }
    
    text = messages.get(alert_type, messages['default'])
    
    try:
        response = polly_client.synthesize_speech(
            Text=text,
            OutputFormat='mp3',
            VoiceId='Seoyeon',  # Korean female voice
            Engine='neural',     # Neural TTS for more natural voice
            LanguageCode='ko-KR'
        )
        
        logger.info(f"Generated voice message for {alert_type}: {text}")
        return response['AudioStream']
    
    except Exception as e:
        logger.error(f"Error generating voice with Polly: {str(e)}")
        return None

@handle_lambda_error
def lambda_handler(event, context):
    """
    Handle AI speaker voice confirmation with AWS Polly
    
    Two modes:
    1. Initiate voice confirmation (from InactivityDetector) - Generate voice with Polly
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
        
        # Generate confirmation voice message
        user_settings = dynamodb.get_user_settings(user_id)
        user_name = user_settings.get('name', '사용자') if user_settings else '사용자'
        
        confirmation_text = f"네, 알겠습니다. {user_name}님이 안전하시다니 다행입니다. 계속 모니터링하겠습니다."
        
        try:
            confirmation_audio = polly_client.synthesize_speech(
                Text=confirmation_text,
                OutputFormat='mp3',
                VoiceId='Seoyeon',
                Engine='neural',
                LanguageCode='ko-KR'
            )
            logger.info("Generated confirmation voice message")
        except Exception as e:
            logger.error(f"Error generating confirmation voice: {str(e)}")
        
        logger.info(f"Alert {alert_id} marked as confirmed_safe")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Voice confirmation processed',
                'status': 'confirmed_safe',
                'confirmationText': confirmation_text
            })
        }
    else:
        # Initiate voice confirmation with Polly
        logger.info(f"Initiating voice confirmation for alert {alert_id}")
        
        # Get user settings
        user_settings = dynamodb.get_user_settings(user_id)
        voice_timeout = user_settings.get('voiceResponseTimeout', 30) if user_settings else 30
        user_name = user_settings.get('name', '사용자') if user_settings else '사용자'
        
        # Get alert type
        alert_type = body.get('alertType', 'default')
        
        # Generate voice message with Polly
        audio_stream = generate_voice_message(user_name, alert_type)
        
        if audio_stream:
            # In production, this audio would be sent to AI speaker (Alexa/Google/Clova)
            # For now, we log that voice was generated
            logger.info(f"Voice message generated for alert {alert_id}, type: {alert_type}")
        
        # Update alert with voice confirmation sent timestamp
        dynamodb.update_alert_status(
            user_id=user_id,
            alert_id=alert_id,
            status='voice_confirmation_pending',
            voiceConfirmationSentAt=datetime.utcnow().isoformat()
        )
        
        # TODO: Send audio to AI Speaker
        # In production:
        # 1. Upload audio to S3
        # 2. Call AI speaker API with audio URL
        # 3. Wait for response or timeout
        # 4. If response received, update status to confirmed_safe
        # 5. If timeout or no response, trigger NotificationManager
        
        logger.warning(f"AI Speaker integration not complete - simulating timeout for alert {alert_id}")
        
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
                'message': 'Voice confirmation initiated with Polly',
                'status': 'no_response',
                'timeout': voice_timeout,
                'voiceGenerated': audio_stream is not None,
                'alertType': alert_type
            })
        }
