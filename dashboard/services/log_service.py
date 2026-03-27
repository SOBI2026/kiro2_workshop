"""
LogService - 워크플로우 로그 관리 서비스
KST 타임스탬프 포함, 로그 레벨 지원, 최대 30개 유지
"""

from datetime import datetime
from zoneinfo import ZoneInfo
from dataclasses import dataclass
from typing import List


@dataclass
class LogEntry:
    """로그 항목"""
    timestamp: str  # KST format "HH:MM:SS"
    level: str      # INFO | SUCCESS | WARNING | ERROR
    message: str


class LogService:
    """워크플로우 로그 관리"""
    
    LOG_LEVELS = ['INFO', 'SUCCESS', 'WARNING', 'ERROR']
    MAX_ENTRIES = 30
    
    def __init__(self):
        self.logs: List[LogEntry] = []
    
    def add(self, message: str, level: str = 'INFO') -> None:
        """로그 추가 (KST 타임스탬프 포함)"""
        if level not in self.LOG_LEVELS:
            level = 'INFO'
        
        kst = ZoneInfo("Asia/Seoul")
        timestamp = datetime.now(kst).strftime("%H:%M:%S")
        
        entry = LogEntry(timestamp=timestamp, level=level, message=message)
        self.logs.append(entry)
        
        # 최대 30개 유지
        if len(self.logs) > self.MAX_ENTRIES:
            self.logs = self.logs[-self.MAX_ENTRIES:]
    
    def get_recent(self, count: int = 30) -> List[LogEntry]:
        """최근 로그 반환"""
        return self.logs[-count:] if count < len(self.logs) else self.logs
    
    def clear(self) -> None:
        """로그 초기화"""
        self.logs = []
    
    def format_for_display(self) -> str:
        """Streamlit 표시용 포맷"""
        lines = []
        for entry in self.logs:
            icon = self._get_level_icon(entry.level)
            lines.append(f"[{entry.timestamp}] {icon} {entry.message}")
        return "\n".join(lines)
    
    def _get_level_icon(self, level: str) -> str:
        """로그 레벨별 아이콘"""
        icons = {
            'INFO': 'ℹ️',
            'SUCCESS': '✅',
            'WARNING': '⚠️',
            'ERROR': '❌'
        }
        return icons.get(level, 'ℹ️')
