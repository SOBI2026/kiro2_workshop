import json
import os
import sys
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from common.logger import get_logger
from common.error_handler import handle_lambda_error, ValidationError
from common.dynamodb_helper import DynamoDBHelper
from common.rds_helper import RDSHelper

logger = get_logger(__name__)

@handle_lambda_error
def lambda_handler(event, context):
    """
    Manage user settings and guardians
    
    Expected input:
    {
        "userId": "string",
        "action": "update_settings" | "add_guardian" | "remove_guardian",
        "inactivityThreshold": number (optional, 30-480 minutes),
        "voiceResponseTimeout": number (optional, 10-60 seconds),
        "guardian": {
            "name": "string",
            "phone": "string",
            "email": "string",
            "relationship": "string"
        }
    }
    """
    logger.info(f"Processing settings request: {json.dumps(event)}")
    
    # Parse body if from API Gateway
    if 'body' in event:
        body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
    else:
        body = event
    
    # Validate required fields
    if 'userId' not in body or 'action' not in body:
        raise ValidationError("Missing required fields: userId, action")
    
    user_id = body['userId']
    action = body['action']
    
    dynamodb = DynamoDBHelper()
    rds = RDSHelper()
    
    if action == 'update_settings':
        # Validate and update settings
        updates = {}
        
        if 'inactivityThreshold' in body:
            threshold = body['inactivityThreshold']
            if not (30 <= threshold <= 480):
                raise ValidationError(f"inactivityThreshold must be between 30 and 480 minutes, got {threshold}")
            updates['inactivityThreshold'] = threshold
        
        if 'voiceResponseTimeout' in body:
            timeout = body['voiceResponseTimeout']
            if not (10 <= timeout <= 60):
                raise ValidationError(f"voiceResponseTimeout must be between 10 and 60 seconds, got {timeout}")
            updates['voiceResponseTimeout'] = timeout
        
        if not updates:
            raise ValidationError("No settings to update")
        
        # Update DynamoDB
        update_expr = 'SET ' + ', '.join([f'{k} = :{k}' for k in updates.keys()])
        update_expr += ', updatedAt = :ua'
        
        expr_values = {f':{k}': v for k, v in updates.items()}
        expr_values[':ua'] = datetime.utcnow().isoformat()
        
        dynamodb.user_settings_table.update_item(
            Key={'userId': user_id},
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_values
        )
        
        logger.info(f"Updated settings for user {user_id}: {updates}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Settings updated successfully',
                'updates': updates
            })
        }
    
    elif action == 'add_guardian':
        # Add guardian
        if 'guardian' not in body:
            raise ValidationError("Missing guardian information")
        
        guardian = body['guardian']
        required_guardian_fields = ['name', 'phone']
        for field in required_guardian_fields:
            if field not in guardian:
                raise ValidationError(f"Missing guardian field: {field}")
        
        # Check guardian count (will be enforced by DB trigger)
        try:
            with rds.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO guardians (user_id, name, phone, email, relationship)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING guardian_id
                """, (
                    user_id,
                    guardian['name'],
                    guardian['phone'],
                    guardian.get('email'),
                    guardian.get('relationship', '보호자')
                ))
                guardian_id = cursor.fetchone()[0]
                
            logger.info(f"Added guardian {guardian_id} for user {user_id}")
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'Guardian added successfully',
                    'guardianId': str(guardian_id)
                })
            }
        except Exception as e:
            if 'Maximum 5 guardians' in str(e):
                raise ValidationError("Maximum 5 guardians allowed per user")
            raise
    
    elif action == 'remove_guardian':
        # Remove guardian
        if 'guardianId' not in body:
            raise ValidationError("Missing guardianId")
        
        guardian_id = body['guardianId']
        
        with rds.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM guardians
                WHERE guardian_id = %s AND user_id = %s
            """, (guardian_id, user_id))
        
        logger.info(f"Removed guardian {guardian_id} for user {user_id}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Guardian removed successfully'
            })
        }
    
    else:
        raise ValidationError(f"Invalid action: {action}")
