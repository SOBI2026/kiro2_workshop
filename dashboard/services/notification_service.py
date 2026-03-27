"""
NotificationService - SMS 알림 발송 서비스
AWS SNS 기반 SMS 발송
"""

import re
from typing import Optional
import boto3
from botocore.exceptions import ClientError


class NotificationService:
    """알림 발송 서비스"""
    
    def __init__(self, sns_client=None):
        if sns_client is None:
            sns_client = boto3.client('sns', region_name='us-east-1')
        self.sns = sns_client
    
    def format_phone_number(self, phone: str) -> str:
        """전화번호 포맷 변환 (010-XXXX-XXXX → +8210XXXXXXXX)"""
        # 숫자만 추출
        digits = re.sub(r'[^0-9]', '', phone)
        
        # 010으로 시작하면 0 제거하고 +82 추가
        if digits.startswith('010'):
            return f"+82{digits[1:]}"
        elif digits.startswith('82'):
            return f"+{digits}"
        else:
            return f"+82{digits}"
    
    def send_sms(self, phone: str, message: str) -> dict:
        """SMS 발송 및 결과 반환"""
        formatted_phone = self.format_phone_number(phone)
        
        try:
            response = self.sns.publish(
                PhoneNumber=formatted_phone,
                Message=message,
                MessageAttributes={
                    'AWS.SNS.SMS.SenderID': {
                        'DataType': 'String',
                        'StringValue': 'SeniorCare'
                    },
                    'AWS.SNS.SMS.SMSType': {
                        'DataType': 'String',
                        'StringValue': 'Transactional'
                    }
                }
            )
            return {
                'success': True,
                'message_id': response.get('MessageId'),
                'phone': formatted_phone
            }
        except ClientError as e:
            return {
                'success': False,
                'error': str(e),
                'phone': formatted_phone
            }
    
    def create_emergency_message(self, user_name: str, situation: str = "낙상 의심, 응답 없음") -> str:
        """응급상황 SMS 메시지 생성 (간단하게)"""
        return f"🚨 응급상황 발생\n{user_name}님 위험상황 발생\n{situation}\n속히 연락 바람"
