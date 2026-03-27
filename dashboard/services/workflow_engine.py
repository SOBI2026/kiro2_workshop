"""
WorkflowEngine - 5단계 워크플로우 실행 엔진
센서 수집 → 낙상 감지 → 음성 확인 → 알림 발송 → 완료
"""

import time
from dataclasses import dataclass
from typing import Callable, Optional, Any
from .log_service import LogService
from .voice_service import VoiceService
from .notification_service import NotificationService


@dataclass
class WorkflowStep:
    """워크플로우 단계"""
    num: int
    title: str
    icon: str
    desc: str
    status: str = 'inactive'  # inactive | active | success | warning


class WorkflowEngine:
    """워크플로우 실행 엔진"""
    
    STEPS = [
        {'num': 1, 'title': '센서 데이터 수집', 'icon': '📊', 'desc': '실시간 센서 데이터를 수집합니다'},
        {'num': 2, 'title': '낙상 감지', 'icon': '🚨', 'desc': '낙상 패턴을 분석합니다'},
        {'num': 3, 'title': 'AI 스피커 음성 확인', 'icon': '🗣️', 'desc': '음성으로 상태를 확인합니다'},
        {'num': 4, 'title': '보호자 알림 발송', 'icon': '📱', 'desc': 'SMS 알림을 발송합니다'},
        {'num': 5, 'title': '완료', 'icon': '✅', 'desc': '워크플로우가 완료되었습니다'}
    ]
    
    def __init__(
        self,
        log_service: LogService,
        voice_service: VoiceService,
        notification_service: NotificationService,
        user_settings_table=None
    ):
        self.log = log_service
        self.voice = voice_service
        self.notification = notification_service
        self.user_settings_table = user_settings_table
        self.current_step = 0
        self.voice_id = 'Seoyeon'
        self.user_name = '김영희'
        self.guardian_phone = ''
    
    def get_step_status(self, step_num: int) -> str:
        """단계별 상태 반환"""
        if step_num < self.current_step:
            return 'success' if step_num != 2 else 'warning'
        elif step_num == self.current_step:
            return 'active'
        else:
            return 'inactive'
    
    def get_all_steps(self) -> list:
        """모든 단계 정보 반환 (상태 포함)"""
        steps = []
        for step in self.STEPS:
            status = self.get_step_status(step['num'])
            steps.append(WorkflowStep(
                num=step['num'],
                title=step['title'],
                icon=step['icon'],
                desc=step['desc'],
                status=status
            ))
        return steps
    
    def execute_step(
        self,
        step_num: int,
        on_voice_ready: Optional[Callable[[str], None]] = None,
        on_step_complete: Optional[Callable[[int], None]] = None
    ) -> bool:
        """개별 단계 실행"""
        self.current_step = step_num
        step_info = self.STEPS[step_num - 1]
        
        self.log.add(f"단계 {step_num} 시작: {step_info['title']}", "INFO")
        
        # 음성 생성 및 재생
        voice_file = self.voice.synthesize_step(step_num, self.user_name, self.voice_id)
        if voice_file and on_voice_ready:
            on_voice_ready(voice_file)
            self.log.add(f"음성 안내 재생: {step_info['title']}", "SUCCESS")
        elif not voice_file:
            self.log.add(f"음성 생성 실패 (단계 {step_num})", "ERROR")
        
        # 단계별 특수 처리
        if step_num == 2:  # 낙상 감지
            self.log.add("⚠️ 낙상이 감지되었습니다!", "WARNING")
        elif step_num == 4:  # 알림 발송
            if self.guardian_phone:
                message = self.notification.create_emergency_message(self.user_name)
                result = self.notification.send_sms(self.guardian_phone, message)
                if result['success']:
                    self.log.add(f"SMS 발송 성공: {result['message_id']}", "SUCCESS")
                else:
                    self.log.add(f"SMS 발송 실패: {result.get('error', 'Unknown')}", "ERROR")
            else:
                self.log.add("보호자 연락처가 없어 SMS를 발송하지 않았습니다", "WARNING")
        
        # 단계 완료 콜백
        if on_step_complete:
            on_step_complete(step_num)
        
        self.log.add(f"단계 {step_num} 완료: {step_info['title']}", "SUCCESS")
        return True
    
    def execute_all(
        self,
        voice_id: str = 'Seoyeon',
        user_name: str = '김영희',
        guardian_phone: str = '',
        step_delay: float = 2.0,
        on_voice_ready: Optional[Callable[[str], None]] = None,
        on_step_complete: Optional[Callable[[int], None]] = None,
        on_workflow_complete: Optional[Callable[[], None]] = None
    ) -> bool:
        """전체 워크플로우 실행"""
        self.voice_id = voice_id
        self.user_name = user_name
        self.guardian_phone = guardian_phone
        self.current_step = 0
        
        self.log.add(f"워크플로우 시작 - 사용자: {user_name}, 음성: {voice_id}", "INFO")
        
        for step in self.STEPS:
            self.execute_step(
                step['num'],
                on_voice_ready=on_voice_ready,
                on_step_complete=on_step_complete
            )
            time.sleep(step_delay)
        
        self.log.add("🎉 워크플로우가 완료되었습니다!", "SUCCESS")
        
        if on_workflow_complete:
            on_workflow_complete()
        
        return True
