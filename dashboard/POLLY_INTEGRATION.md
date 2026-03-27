# 🗣️ AWS Polly 음성 통합 가이드

## 📋 개요

AWS Polly Neural TTS를 사용하여 자연스러운 한국어 음성으로 AI 스피커 안부 확인 기능을 구현했습니다.

---

## 🎵 생성된 음성 파일

### 1. greeting.mp3 (일반 안부 확인)
- **텍스트**: "안녕하세요, 김영희님. 괜찮으신가요?"
- **시나리오**: 정기 안부 확인
- **크기**: 21 KB

### 2. fall_detected.mp3 (낙상 감지)
- **텍스트**: "김영희님, 넘어지신 것 같습니다. 괜찮으신가요? 응답해주세요."
- **시나리오**: 가속도 센서가 급격한 충격 감지 (accelerometer > 10.0)
- **크기**: 33 KB

### 3. no_movement.mp3 (활동 부재)
- **텍스트**: "김영희님, 2시간 동안 움직임이 감지되지 않았습니다. 안전하신가요?"
- **시나리오**: 임계값 초과 (120분 이상 활동 없음)
- **크기**: 31 KB

### 4. emergency.mp3 (긴급 상황)
- **텍스트**: "긴급 상황이 감지되었습니다. 즉시 응답해주세요. 응답이 없으면 보호자에게 연락하겠습니다."
- **시나리오**: 낙상 + 활동 부재 복합 상황
- **크기**: 45 KB

### 5. confirmation.mp3 (정상 응답 확인)
- **텍스트**: "네, 알겠습니다. 안전하시다니 다행입니다. 계속 모니터링하겠습니다."
- **시나리오**: 사용자 정상 응답 후
- **크기**: 37 KB

---

## 🔧 Polly 설정

### 음성 설정
```python
polly_client.synthesize_speech(
    Text="안녕하세요, 김영희님. 괜찮으신가요?",
    OutputFormat='mp3',
    VoiceId='Seoyeon',      # 한국어 여성 음성
    Engine='neural',         # Neural TTS (더 자연스러운 음성)
    LanguageCode='ko-KR'
)
```

### 사용 가능한 한국어 음성
- **Seoyeon** (여성, Neural) - 추천 ⭐
- **Seoyeon** (여성, Standard)

### Neural vs Standard
| 특징 | Neural TTS | Standard TTS |
|------|-----------|--------------|
| 자연스러움 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| 억양 | 사람과 유사 | 기계적 |
| 가격 | $16/1M chars | $4/1M chars |
| 권장 | 프로덕션 | 테스트 |

---

## 💰 비용 분석

### 이 프로젝트 비용
- **총 문자 수**: 약 150자 (5개 메시지)
- **Neural TTS 비용**: $0.0024 (약 3원)
- **Standard TTS 비용**: $0.0006 (약 1원)

### 월간 예상 비용 (사용자 1명)
**시나리오**: 하루 10회 음성 확인
- 일일 문자 수: 30자 × 10회 = 300자
- 월간 문자 수: 300자 × 30일 = 9,000자
- **Neural TTS**: $0.14/월 (약 200원)
- **Standard TTS**: $0.04/월 (약 50원)

### 대규모 서비스 (사용자 1,000명)
- 월간 문자 수: 9,000자 × 1,000명 = 9M자
- **Neural TTS**: $144/월
- **Standard TTS**: $36/월

---

## 🎮 대시보드 사용법

### 버전 2 대시보드 (http://localhost:8504)

1. **음성 메시지 선택**
   - 드롭다운에서 원하는 시나리오 선택
   - 5가지 시나리오 중 선택 가능

2. **음성 재생**
   - 자동으로 오디오 플레이어 표시
   - 재생 버튼 클릭하여 음성 확인

3. **음성 재생성**
   - "🔄 음성 재생성" 버튼 클릭
   - Polly API 호출하여 새로운 음성 생성
   - 실시간으로 음성 파일 업데이트

---

## 🔄 워크플로우 통합

### 1단계: 이상 징후 감지
```
InactivityDetector → 낙상 감지 or 활동 부재
```

### 2단계: 음성 메시지 생성
```python
# VoiceResponseHandler Lambda
audio_stream = polly_client.synthesize_speech(
    Text=f"{user_name}님, 넘어지신 것 같습니다. 괜찮으신가요?",
    VoiceId='Seoyeon',
    Engine='neural'
)
```

### 3단계: AI 스피커로 전송
```
Audio Stream → S3 Upload → AI Speaker API
(Alexa / Google Home / Clova)
```

### 4단계: 응답 대기
```
30초 타임아웃
- 응답 있음 → confirmed_safe
- 응답 없음 → no_response → NotificationManager
```

---

## 🚀 Lambda 함수 업데이트

### VoiceResponseHandler 개선사항

#### Before (기존)
```python
# TODO: Call AI Speaker API
logger.warning("AI Speaker API not implemented")
```

#### After (Polly 통합)
```python
# Generate voice with Polly
audio_stream = polly_client.synthesize_speech(
    Text=message_text,
    VoiceId='Seoyeon',
    Engine='neural',
    LanguageCode='ko-KR'
)

logger.info("Voice message generated with Polly")
# TODO: Send to AI Speaker
```

### 메시지 템플릿
```python
messages = {
    'inactivity': f"{user_name}님, 2시간 동안 움직임이 감지되지 않았습니다.",
    'fall_detected': f"{user_name}님, 넘어지신 것 같습니다. 괜찮으신가요?",
    'emergency': "긴급 상황이 감지되었습니다. 즉시 응답해주세요.",
    'default': f"안녕하세요, {user_name}님. 괜찮으신가요?"
}
```

---

## 🧪 테스트 방법

### 1. 음성 파일 생성
```bash
cd dashboard
python polly_voice_test.py
```

### 2. 대시보드에서 재생
```bash
# 버전 2 대시보드 시작
.\start_v2.ps1

# 브라우저에서 http://localhost:8504 접속
# "AI 스피커 음성 확인" 섹션에서 음성 재생
```

### 3. Lambda 함수 테스트
```bash
# VoiceResponseHandler 직접 호출
python dashboard/test_lambda.py
```

---

## 📊 실제 AI 스피커 연동 (향후 구현)

### Alexa 연동
```python
# Alexa Skills Kit
alexa_client.send_audio(
    audio_url=s3_url,
    device_id=user_device_id
)
```

### Google Home 연동
```python
# Google Assistant SDK
google_client.play_audio(
    audio_stream=audio_stream,
    device_name=user_device_name
)
```

### Clova 연동
```python
# Naver Clova CEK
clova_client.send_directive(
    audio_url=s3_url,
    user_id=user_id
)
```

---

## 🎯 다음 단계

### Phase 1: 음성 생성 ✅ (완료)
- [x] Polly 통합
- [x] 한국어 Neural TTS
- [x] 5가지 시나리오 메시지
- [x] 대시보드 재생 기능

### Phase 2: AI 스피커 연동 (예정)
- [ ] S3에 음성 파일 업로드
- [ ] Alexa Skills Kit 연동
- [ ] Google Home 연동
- [ ] Clova CEK 연동

### Phase 3: 음성 인식 (예정)
- [ ] 사용자 응답 녹음
- [ ] Amazon Transcribe로 음성→텍스트
- [ ] 감정 분석 (긍정/부정/위급)
- [ ] 자동 대응 로직

### Phase 4: 고도화 (예정)
- [ ] 다국어 지원 (영어, 일본어)
- [ ] 사용자별 음성 커스터마이징
- [ ] 시간대별 음성 톤 조절
- [ ] 음성 히스토리 저장

---

## 💡 팁 & 트릭

### 1. 음성 품질 향상
```python
# SSML 사용으로 억양 조절
text = '<speak><prosody rate="slow">안녕하세요</prosody></speak>'
```

### 2. 비용 절감
```python
# 자주 사용하는 메시지는 S3에 캐싱
if cached_audio_exists(message_id):
    return get_from_s3(message_id)
else:
    audio = generate_with_polly(text)
    save_to_s3(message_id, audio)
    return audio
```

### 3. 응답 시간 단축
```python
# Lambda 함수에서 Polly 클라이언트 재사용
polly_client = boto3.client('polly')  # 전역 변수로 선언
```

---

## 📚 참고 자료

- [AWS Polly 문서](https://docs.aws.amazon.com/polly/)
- [Neural TTS 가이드](https://docs.aws.amazon.com/polly/latest/dg/ntts-main.html)
- [한국어 음성 지원](https://docs.aws.amazon.com/polly/latest/dg/SupportedLanguage.html)
- [SSML 태그](https://docs.aws.amazon.com/polly/latest/dg/supportedtags.html)

---

## ✨ 결론

AWS Polly Neural TTS를 사용하여 자연스러운 한국어 음성으로 AI 스피커 안부 확인 기능을 성공적으로 구현했습니다. 

**주요 성과**:
- ✅ 5가지 시나리오별 음성 메시지
- ✅ 대시보드 실시간 재생 기능
- ✅ Lambda 함수 Polly 통합
- ✅ 매우 저렴한 비용 (월 200원/사용자)

**다음 목표**:
- 실제 AI 스피커 연동 (Alexa/Google/Clova)
- 음성 인식 및 감정 분석
- 다국어 지원
