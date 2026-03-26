import json
import os
import sys
import uuid
from datetime import datetime, timedelta
import boto3

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from common.logger import get_logger
from common.error_handler import handle_lambda_error
from common.dynamodb_helper import DynamoDBHelper

logger = get_logger(__name__)
lambda_client = boto3.client('lambda')

@handle_lambda_error
def lambda_handler(event, context):
    """
    Detect user inactivity and trigger voice confirmation
    Runs every 1 minute via EventBridge schedule
    
    예시 시나리오:
    1. 정상 활동: lastActivity=30분 전, threshold=120분 → 알림 없음
    2. 임계값 초과: lastActivity=121분 전, threshold=120분 → 음성 확인 시작
    3. 중복 방지: 이미 pending alert 있음 → 새 알림 생성 안 함
    """
    logger.info("Starting inactivity detection")
    
    dynamodb = DynamoDBHelper()
    
    # STEP 1: 모든 활성 사용자 조회
    # 테이블: SeniorCare-UserSettings
    # 조건: status = 'active'
    # 예시: 10명의 활성 사용자 조회
    active_users = dynamodb.query_active_users()
    logger.info(f"Found {len(active_users)} active users")
    
    triggered_count = 0
    current_time = datetime.utcnow()
    
    for user in active_users:
        user_id = user['userId']
        last_activity_str = user.get('lastActivityTime')
        inactivity_threshold = user.get('inactivityThreshold', 120)  # Default 120 minutes
        
        if not last_activity_str:
            logger.warning(f"User {user_id} has no lastActivityTime")
            continue
        
        # Parse last activity time
        try:
            last_activity = datetime.fromisoformat(last_activity_str.replace('Z', '+00:00'))
        except Exception as e:
            logger.error(f"Error parsing lastActivityTime for user {user_id}: {str(e)}")
            continue
        
        # Calculate inactivity duration
        inactivity_minutes = (current_time - last_activity.replace(tzinfo=None)).total_seconds() / 60
        
        logger.info(f"User {user_id}: inactive for {inactivity_minutes:.1f} minutes (threshold: {inactivity_threshold})")
        
        # STEP 2: 임계값 초과 여부 확인
        # 예시 1: 30분 경과, 임계값 120분 → 정상 (알림 없음)
        # 예시 2: 121분 경과, 임계값 120분 → 임계값 초과 (알림 생성)
        if inactivity_minutes >= inactivity_threshold:
            # STEP 3: 중복 알림 방지 - 이미 pending 상태 알림이 있는지 확인
            # 예시: 이미 voice_confirmation_pending 알림 있음 → 새 알림 생성 안 함
            pending_alerts = dynamodb.get_pending_alerts(user_id)
            
            if pending_alerts:
                logger.info(f"User {user_id} already has pending alert, skipping")
                continue
            
            # STEP 4: 새 알림 생성
            # 테이블: SeniorCare-AlertHistory
            # 상태: voice_confirmation_pending
            # 예시: alertId="550e8400-e29b-41d4-a716-446655440000"
            alert_id = str(uuid.uuid4())
            dynamodb.create_alert(
                user_id=user_id,
                alert_id=alert_id,
                alert_type='no_response',
                last_activity_time=last_activity_str
            )
            
            # STEP 5: VoiceResponseHandler Lambda 비동기 호출
            # 음성 확인 프로세스 시작
            # 예시: AI 스피커가 "김영희님, 괜찮으신가요?" 질문
            try:
                lambda_client.invoke(
                    FunctionName=os.environ.get('VOICE_RESPONSE_HANDLER_FUNCTION', 'SeniorCare-VoiceResponseHandler'),
                    InvocationType='Event',  # Async (비동기)
                    Payload=json.dumps({
                        'userId': user_id,
                        'alertId': alert_id
                    })
                )
                logger.info(f"Triggered voice confirmation for user {user_id}, alert {alert_id}")
                triggered_count += 1
            except Exception as e:
                logger.error(f"Error invoking VoiceResponseHandler: {str(e)}")
    
    logger.info(f"Inactivity detection complete. Triggered {triggered_count} voice confirmations")
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Inactivity detection complete',
            'activeUsers': len(active_users),
            'triggeredAlerts': triggered_count
        })
    }
