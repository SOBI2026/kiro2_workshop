"""
WorkflowTriggerService - 워크플로우 트리거 관리 서비스
DynamoDB 기반 트리거 생성, 조회, 상태 업데이트
"""

from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional
import boto3
from botocore.exceptions import ClientError


class WorkflowTriggerService:
    """워크플로우 트리거 관리 서비스"""
    
    VALID_STATUSES = ['pending', 'running', 'completed']
    
    def __init__(self, dynamodb_resource=None, table_name: str = 'SeniorCare-WorkflowTrigger'):
        if dynamodb_resource is None:
            dynamodb_resource = boto3.resource('dynamodb', region_name='us-east-1')
        self.table = dynamodb_resource.Table(table_name)
        self.table_name = table_name
    
    def create_trigger(self, user_id: str, voice: str = 'Seoyeon') -> dict:
        """새 워크플로우 트리거 생성"""
        kst = ZoneInfo("Asia/Seoul")
        now = datetime.now(kst).isoformat()
        
        item = {
            'userId': user_id,
            'triggerId': 'latest',
            'status': 'pending',
            'voice': voice if voice in ['Seoyeon', 'Jihye'] else 'Seoyeon',
            'currentStep': 0,
            'triggeredAt': now,
            'triggeredBy': 'developer-dashboard',
            'updatedAt': now
        }
        
        try:
            self.table.put_item(Item=item)
            return item
        except ClientError as e:
            raise Exception(f"트리거 생성 실패: {e}")
    
    def get_pending_trigger(self, user_id: str) -> Optional[dict]:
        """pending 상태의 트리거 조회"""
        try:
            response = self.table.get_item(
                Key={'userId': user_id, 'triggerId': 'latest'}
            )
            item = response.get('Item')
            if item and item.get('status') == 'pending':
                return item
            return None
        except ClientError:
            return None
    
    def get_trigger(self, user_id: str) -> Optional[dict]:
        """트리거 조회 (상태 무관)"""
        try:
            response = self.table.get_item(
                Key={'userId': user_id, 'triggerId': 'latest'}
            )
            return response.get('Item')
        except ClientError:
            return None
    
    def update_status(self, user_id: str, status: str, current_step: int = 0) -> bool:
        """트리거 상태 업데이트 (pending → running → completed)"""
        if status not in self.VALID_STATUSES:
            return False
        
        kst = ZoneInfo("Asia/Seoul")
        now = datetime.now(kst).isoformat()
        
        try:
            self.table.update_item(
                Key={'userId': user_id, 'triggerId': 'latest'},
                UpdateExpression='SET #status = :status, currentStep = :step, updatedAt = :updated',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': status,
                    ':step': current_step,
                    ':updated': now
                }
            )
            return True
        except ClientError:
            return False
