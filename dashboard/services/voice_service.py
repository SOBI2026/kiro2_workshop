"""
VoiceService - Amazon Polly 기반 음성 합성 서비스
한국어 음성 (Seoyeon/Jihye) 지원
"""

import os
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional
import boto3
from botocore.exceptions import ClientError


class VoiceService:
    """Amazon Polly 음성 합성 서비스"""
    
    SUPPORTED_VOICES = ['Seoyeon', 'Jihye']
    DEFAULT_VOICE = 'Seoyeon'
    
    # 단계별 음성 메시지 템플릿
    STEP_MESSAGES = {
        1: "{name}님의 센서 데이터를 수집하고 있습니다.",
        2: "낙상이 감지되었습니다! {name}님의 상태를 확인합니다.",
        3: "{name}님, 괜찮으세요? 응답해 주세요.",
        4: "보호자에게 긴급 알림을 발송합니다.",
        5: "워크플로우가 완료되었습니다. {name}님의 상태가 정상으로 복구되었습니다."
    }
    
    def __init__(self, polly_client=None, output_dir: str = 'dashboard/voice_outputs'):
        if polly_client is None:
            polly_client = boto3.client('polly', region_name='us-east-1')
        self.polly = polly_client
        self.output_dir = output_dir
        self._ensure_output_dir()
    
    def _ensure_output_dir(self) -> None:
        """voice_outputs 디렉토리 생성"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def synthesize(self, text: str, voice_id: str = 'Seoyeon') -> Optional[str]:
        """텍스트를 음성으로 변환하고 파일 경로 반환"""
        if voice_id not in self.SUPPORTED_VOICES:
            voice_id = self.DEFAULT_VOICE
        
        try:
            response = self.polly.synthesize_speech(
                Text=text,
                OutputFormat='mp3',
                VoiceId=voice_id,
                LanguageCode='ko-KR'
            )
            
            # 파일명 생성: auto_demo_HHMMSS.mp3
            kst = ZoneInfo("Asia/Seoul")
            timestamp = datetime.now(kst).strftime("%H%M%S")
            filename = f"auto_demo_{timestamp}.mp3"
            filepath = os.path.join(self.output_dir, filename)
            
            # 파일 저장
            with open(filepath, 'wb') as f:
                f.write(response['AudioStream'].read())
            
            return filepath
        except ClientError as e:
            print(f"Polly 오류: {e}")
            return None
        except Exception as e:
            print(f"음성 파일 저장 오류: {e}")
            return None
    
    def get_step_message(self, step: int, user_name: str = "김영희") -> str:
        """워크플로우 단계별 음성 메시지 반환"""
        template = self.STEP_MESSAGES.get(step, "")
        return template.format(name=user_name)
    
    def synthesize_step(self, step: int, user_name: str = "김영희", voice_id: str = 'Seoyeon') -> Optional[str]:
        """단계별 음성 합성 (편의 메서드)"""
        message = self.get_step_message(step, user_name)
        if message:
            return self.synthesize(message, voice_id)
        return None
