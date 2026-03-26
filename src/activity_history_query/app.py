import json
import os
import sys
from datetime import datetime, timedelta

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from common.logger import get_logger
from common.error_handler import handle_lambda_error, ValidationError
from common.rds_helper import RDSHelper

logger = get_logger(__name__)

@handle_lambda_error
def lambda_handler(event, context):
    """
    Query activity history for a user
    
    Query parameters:
    - userId: User ID
    - guardianPhone: Guardian phone number (for authorization)
    - startDate: Start date (ISO8601)
    - endDate: End date (ISO8601)
    """
    logger.info(f"Processing activity history query: {json.dumps(event)}")
    
    # Parse query parameters
    params = event.get('queryStringParameters', {})
    
    if not params:
        raise ValidationError("Missing query parameters")
    
    user_id = params.get('userId')
    guardian_phone = params.get('guardianPhone')
    start_date = params.get('startDate')
    end_date = params.get('endDate')
    
    # Validate required fields
    if not user_id or not guardian_phone:
        raise ValidationError("Missing required parameters: userId, guardianPhone")
    
    rds = RDSHelper()
    
    # Check guardian permission
    has_permission = rds.check_guardian_permission(guardian_phone, user_id)
    
    if not has_permission:
        logger.warning(f"Guardian {guardian_phone} does not have permission for user {user_id}")
        return {
            'statusCode': 403,
            'body': json.dumps({
                'error': 'Forbidden: You do not have permission to access this user data'
            })
        }
    
    # Parse dates
    try:
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        else:
            start_dt = datetime.utcnow() - timedelta(days=30)
        
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        else:
            end_dt = datetime.utcnow()
    except Exception as e:
        raise ValidationError(f"Invalid date format: {str(e)}")
    
    # Query activity history
    activity_history = rds.get_activity_history(user_id, start_dt, end_dt)
    
    logger.info(f"Retrieved {len(activity_history)} activity records for user {user_id}")
    
    # Convert datetime objects to ISO strings for JSON serialization
    for record in activity_history:
        if 'timestamp' in record and isinstance(record['timestamp'], datetime):
            record['timestamp'] = record['timestamp'].isoformat()
        if 'created_at' in record and isinstance(record['created_at'], datetime):
            record['created_at'] = record['created_at'].isoformat()
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Activity history retrieved successfully',
            'count': len(activity_history),
            'data': activity_history
        })
    }
