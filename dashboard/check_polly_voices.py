"""
AWS Polly 한국어 음성 목록 확인
"""
import boto3

print("=" * 60)
print("AWS Polly 한국어 음성 목록")
print("=" * 60)
print()

try:
    polly_client = boto3.client('polly', region_name='us-east-1')
    
    # 모든 음성 가져오기
    response = polly_client.describe_voices(LanguageCode='ko-KR')
    
    print(f"총 {len(response['Voices'])}개의 한국어 음성 사용 가능:")
    print()
    
    for voice in response['Voices']:
        print(f"이름: {voice['Id']}")
        print(f"  성별: {voice['Gender']}")
        print(f"  엔진: {', '.join(voice.get('SupportedEngines', []))}")
        print(f"  설명: {voice.get('Name', 'N/A')}")
        print()
    
except Exception as e:
    print(f"❌ 오류: {str(e)}")

print("=" * 60)
