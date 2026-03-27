import boto3
import os
from datetime import datetime

print("=" * 70)
print("🗣️ AWS Polly 음성 생성 테스트")
print("=" * 70)

# Polly 클라이언트 생성
polly_client = boto3.client('polly', region_name='us-east-1')

# 음성 메시지 목록
messages = [
    {
        "id": "greeting",
        "text": "안녕하세요, 김영희님. 괜찮으신가요?",
        "description": "일반 안부 확인"
    },
    {
        "id": "fall_detected",
        "text": "김영희님, 넘어지신 것 같습니다. 괜찮으신가요? 응답해주세요.",
        "description": "낙상 감지 시"
    },
    {
        "id": "no_movement",
        "text": "김영희님, 2시간 동안 움직임이 감지되지 않았습니다. 안전하신가요?",
        "description": "활동 부재 감지 시"
    },
    {
        "id": "emergency",
        "text": "긴급 상황이 감지되었습니다. 즉시 응답해주세요. 응답이 없으면 보호자에게 연락하겠습니다.",
        "description": "긴급 상황"
    },
    {
        "id": "confirmation",
        "text": "네, 알겠습니다. 안전하시다니 다행입니다. 계속 모니터링하겠습니다.",
        "description": "정상 응답 확인"
    }
]

# 출력 디렉토리 생성
output_dir = "voice_outputs"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)
    print(f"✅ 출력 디렉토리 생성: {output_dir}/")

print("\n" + "=" * 70)
print("음성 생성 중...")
print("=" * 70)

# 각 메시지에 대해 음성 생성
for msg in messages:
    print(f"\n[{msg['id']}] {msg['description']}")
    print(f"텍스트: {msg['text']}")
    
    try:
        # Polly로 음성 생성
        response = polly_client.synthesize_speech(
            Text=msg['text'],
            OutputFormat='mp3',
            VoiceId='Seoyeon',  # 한국어 여성 음성
            Engine='neural',     # Neural TTS (더 자연스러운 음성)
            LanguageCode='ko-KR'
        )
        
        # 음성 파일 저장
        output_file = f"{output_dir}/{msg['id']}.mp3"
        with open(output_file, 'wb') as file:
            file.write(response['AudioStream'].read())
        
        print(f"✅ 음성 파일 생성: {output_file}")
        
        # 파일 크기 확인
        file_size = os.path.getsize(output_file)
        print(f"   파일 크기: {file_size:,} bytes ({file_size/1024:.2f} KB)")
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")

print("\n" + "=" * 70)
print("✨ 음성 생성 완료!")
print("=" * 70)

print(f"\n📁 생성된 파일 위치: {os.path.abspath(output_dir)}/")
print("\n💡 사용 가능한 한국어 음성:")
print("   - Seoyeon (여성, Neural)")
print("   - Seoyeon (여성, Standard)")

print("\n🎵 음성 재생 방법:")
print("   1. Windows Media Player로 재생")
print("   2. 대시보드에서 재생 (다음 단계에서 구현)")

print("\n📊 Polly 요금:")
print("   - Neural TTS: $16 per 1M characters")
print("   - Standard TTS: $4 per 1M characters")
print("   - 이 테스트: 약 $0.001 (매우 저렴)")

print("\n" + "=" * 70)
