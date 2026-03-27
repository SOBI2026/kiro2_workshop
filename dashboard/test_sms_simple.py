"""
간단한 SMS 발송 테스트
"""
import boto3
from datetime import datetime

print("=" * 60)
print("간단한 SMS 발송 테스트")
print("=" * 60)
print()

try:
    # SNS 클라이언트 초기화
    sns_client = boto3.client('sns', region_name='us-east-1')
    
    # 간단한 테스트 메시지
    test_message = """🚨 응급상황 발생
김영희님 위험상황 발생
낙상 의심, 응답 없음
속히 연락 바람"""

    print("📤 SMS 발송 중...")
    print(f"   수신 번호: 010-3328-4472")
    print(f"   메시지 길이: {len(test_message)} 자")
    print()
    print("메시지 내용:")
    print("-" * 40)
    print(test_message)
    print("-" * 40)
    print()
    
    # SMS 발송
    response = sns_client.publish(
        PhoneNumber='+821033284472',
        Message=test_message,
        MessageAttributes={
            'AWS.SNS.SMS.SMSType': {
                'DataType': 'String',
                'StringValue': 'Transactional'
            }
        }
    )
    
    print("✅ SMS 발송 성공!")
    print(f"   MessageId: {response['MessageId']}")
    print(f"   HTTP Status: {response['ResponseMetadata']['HTTPStatusCode']}")
    print()
    print("📱 휴대폰을 확인하세요!")
    print()
    print("⚠️ 참고: SMS 수신까지 최대 1-2분 소요될 수 있습니다.")
    
except Exception as e:
    print("❌ SMS 발송 실패!")
    print(f"   오류: {str(e)}")
    print()
    
    if "ExpiredToken" in str(e):
        print("⚠️ AWS 세션 토큰이 만료되었습니다.")
    elif "AccessDenied" in str(e) or "not authorized" in str(e):
        print("⚠️ AWS SNS 권한이 없습니다.")
    elif "InvalidParameter" in str(e):
        print("⚠️ 전화번호 형식이 잘못되었습니다.")
    else:
        print("⚠️ 기타 오류가 발생했습니다.")

print()
print("=" * 60)
