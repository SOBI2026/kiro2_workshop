"""
SMS 발송 테스트 스크립트
"""
import boto3
from datetime import datetime

print("=" * 60)
print("SMS 발송 테스트")
print("=" * 60)
print()

try:
    # SNS 클라이언트 초기화
    sns_client = boto3.client('sns', region_name='us-east-1')
    
    # 테스트 메시지
    test_message = f"""🧪 SMS 테스트

시니어 안심 케어 시스템 SMS 발송 테스트입니다.

📱 발송 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

이 메시지를 받으셨다면 SMS 발송이 정상 작동합니다."""

    print("📤 SMS 발송 중...")
    print(f"   수신 번호: 010-3328-4472")
    print(f"   메시지 길이: {len(test_message)} 자")
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
    
except Exception as e:
    print("❌ SMS 발송 실패!")
    print(f"   오류: {str(e)}")
    print()
    
    if "ExpiredToken" in str(e):
        print("⚠️ AWS 세션 토큰이 만료되었습니다.")
        print("   새로운 AWS 자격증명을 받아서 환경변수를 업데이트하세요.")
    elif "AccessDenied" in str(e) or "not authorized" in str(e):
        print("⚠️ AWS SNS 권한이 없습니다.")
        print("   IAM 정책에서 SNS:Publish 권한을 확인하세요.")
    elif "InvalidParameter" in str(e):
        print("⚠️ 전화번호 형식이 잘못되었습니다.")
        print("   형식: +821012345678 (국가코드 포함)")
    else:
        print("⚠️ 기타 오류가 발생했습니다.")
        print("   AWS 콘솔에서 SNS 설정을 확인하세요.")

print()
print("=" * 60)
