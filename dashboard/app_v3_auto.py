"""
시니어 안심 케어 - 실시간 현황 대시보드 (자동 활성화 버전)
DynamoDB 폴링 기반 워크플로우 자동 감지 및 음성 안내
"""

import streamlit as st
import boto3
import time
from datetime import datetime
from decimal import Decimal
import os
import sys
import uuid
from zoneinfo import ZoneInfo

# 서비스 모듈 import (경로 추가)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from services.log_service import LogService
from services.trigger_service import WorkflowTriggerService
from services.voice_service import VoiceService
from services.notification_service import NotificationService

# 한국 시간대 설정
KST = ZoneInfo("Asia/Seoul")

def now_kst():
    return datetime.now(KST)

# Page configuration
st.set_page_config(
    page_title="시니어 안심 케어 - 실시간 현황",
    page_icon="📊",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .workflow-step {
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
        border: 3px solid transparent;
    }
    .step-inactive { background: #f5f5f5; color: #999; }
    .step-active {
        background: linear-gradient(135deg, #ffa500 0%, #ff8c00 100%);
        color: white;
        border-color: #ff6600;
        box-shadow: 0 0 20px rgba(255, 165, 0, 0.5);
        animation: pulse 2s infinite;
    }
    .step-success {
        background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);
        color: white;
    }
    .step-warning {
        background: linear-gradient(135deg, #f44336 0%, #e53935 100%);
        color: white;
    }
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.02); }
    }
    .log-container {
        background: #1e1e1e;
        color: #00ff00;
        padding: 1rem;
        border-radius: 5px;
        font-family: 'Courier New', monospace;
        height: 300px;
        overflow-y: auto;
    }
</style>
""", unsafe_allow_html=True)

# AWS clients 초기화
@st.cache_resource
def init_aws():
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    polly = boto3.client('polly', region_name='us-east-1')
    sns = boto3.client('sns', region_name='us-east-1')
    return dynamodb, polly, sns

dynamodb, polly_client, sns_client = init_aws()

# 테이블
sensor_table = dynamodb.Table('SeniorCare-SensorData')
user_settings_table = dynamodb.Table('SeniorCare-UserSettings')
alert_table = dynamodb.Table('SeniorCare-AlertHistory')

# 서비스 초기화
trigger_service = WorkflowTriggerService(dynamodb)
voice_service = VoiceService(polly_client)
notification_service = NotificationService(sns_client)

# 워크플로우 단계
STEPS = [
    {"num": 1, "title": "센서 데이터 수집", "icon": "📊", "desc": "실시간 센서 데이터를 수집합니다"},
    {"num": 2, "title": "낙상 감지", "icon": "🚨", "desc": "낙상 패턴을 분석합니다"},
    {"num": 3, "title": "AI 스피커 음성 확인", "icon": "🗣️", "desc": "음성으로 상태를 확인합니다"},
    {"num": 4, "title": "보호자 알림 발송", "icon": "📱", "desc": "SMS 알림을 발송합니다"},
    {"num": 5, "title": "완료", "icon": "✅", "desc": "워크플로우가 완료되었습니다"}
]

# Header
st.markdown("""
<div class="main-header">
    <h1>📊 시니어 안심 케어 - 실시간 현황</h1>
    <p>개발자 대시보드에서 시나리오 실행 시 자동으로 워크플로우가 시작됩니다</p>
</div>
""", unsafe_allow_html=True)

def render_steps(current_step):
    html = ""
    for step in STEPS:
        if current_step == step["num"]:
            step_class = "step-active"
        elif current_step > step["num"]:
            step_class = "step-success" if step["num"] != 2 else "step-warning"
        else:
            step_class = "step-inactive"
        
        html += f"""
        <div class="workflow-step {step_class}">
            <div style="font-size: 2rem; text-align: center;">{step["icon"]}</div>
            <div style="font-size: 1.5rem; font-weight: bold; text-align: center; margin-top: 0.5rem;">
                {step["num"]}. {step["title"]}
            </div>
            <div style="text-align: center; margin-top: 0.5rem; font-size: 0.9rem;">
                {step["desc"]}
            </div>
        </div>
        """
    return html

def load_guardian_info(user_id):
    try:
        response = user_settings_table.get_item(Key={'userId': user_id})
        if 'Item' in response:
            s = response['Item']
            return {
                'name': s.get('guardianName', '보호자'),
                'phone': s.get('guardianPhone', '010-3328-4472'),
                'user_name': s.get('name', '김영희'),
            }
    except:
        pass
    return {'name': '보호자', 'phone': '010-3328-4472', 'user_name': '김영희'}

def run_workflow(voice_id, status_ph, log_ph, voice_ph, info_ph):
    user_id = 'test-user-001'
    logs = []
    
    def add_log(msg, level="INFO"):
        ts = now_kst().strftime("%H:%M:%S")
        icon = {"INFO": "ℹ️", "SUCCESS": "✅", "WARNING": "⚠️", "ERROR": "❌"}.get(level, "ℹ️")
        logs.append(f"[{ts}] {icon} {msg}")
        log_html = "<div class='log-container'>" + "<br>".join(logs[-20:]) + "</div>"
        log_ph.markdown(log_html, unsafe_allow_html=True)
    
    # 트리거 상태 변경
    trigger_service.update_status(user_id, 'running', 0)
    
    # 보호자 정보
    guardian = load_guardian_info(user_id)
    add_log(f"보호자: {guardian['name']}, SMS: {guardian['phone']}", "INFO")
    info_ph.info(f"👤 {guardian['user_name']} | 📱 {guardian['phone']} | 🔊 {voice_id}")
    
    # Step 1
    status_ph.markdown(render_steps(1), unsafe_allow_html=True)
    add_log("=== STEP 1: 센서 데이터 수집 ===")
    vf = voice_service.synthesize_step(1, guardian['user_name'], voice_id)
    if vf and os.path.exists(vf):
        voice_ph.audio(open(vf, 'rb').read(), format='audio/mp3')
    
    for st_type, val, desc in [("motion", 2.5, "거실"), ("door", 1.0, "방문"), ("temperature", 22.5, "온도")]:
        sensor_table.put_item(Item={
            'userId': user_id, 'timestamp': int(now_kst().timestamp()),
            'deviceId': f'{st_type}-001', 'deviceType': 'iot',
            'sensorType': st_type, 'value': Decimal(str(val))
        })
        add_log(f"✅ {desc}: {val}")
        time.sleep(0.3)
    time.sleep(1)
    
    # Step 2
    status_ph.markdown(render_steps(2), unsafe_allow_html=True)
    add_log("=== STEP 2: 낙상 감지 ===", "WARNING")
    vf = voice_service.synthesize_step(2, guardian['user_name'], voice_id)
    if vf and os.path.exists(vf):
        voice_ph.audio(open(vf, 'rb').read(), format='audio/mp3')
    
    sensor_table.put_item(Item={
        'userId': user_id, 'timestamp': int(now_kst().timestamp()),
        'deviceId': 'phone-001', 'deviceType': 'mobile',
        'sensorType': 'accelerometer', 'value': Decimal('15.8')
    })
    add_log("🚨 낙상 발생! 가속도: 15.8", "ERROR")
    
    user_settings_table.update_item(
        Key={'userId': user_id},
        UpdateExpression='SET #s = :s',
        ExpressionAttributeNames={'#s': 'status'},
        ExpressionAttributeValues={':s': 'emergency'}
    )
    add_log("⚠️ 상태: emergency", "ERROR")
    time.sleep(1)
    
    # Step 3
    status_ph.markdown(render_steps(3), unsafe_allow_html=True)
    add_log("=== STEP 3: 음성 확인 ===")
    vf = voice_service.synthesize_step(3, guardian['user_name'], voice_id)
    if vf and os.path.exists(vf):
        voice_ph.audio(open(vf, 'rb').read(), format='audio/mp3')
    add_log("⏳ 응답 대기 중...")
    time.sleep(2)
    add_log("⚠️ 응답 없음!", "WARNING")
    time.sleep(1)
    
    # Step 4
    status_ph.markdown(render_steps(4), unsafe_allow_html=True)
    add_log("=== STEP 4: 알림 발송 ===", "ERROR")
    vf = voice_service.synthesize_step(4, guardian['user_name'], voice_id)
    if vf and os.path.exists(vf):
        voice_ph.audio(open(vf, 'rb').read(), format='audio/mp3')
    
    msg = notification_service.create_emergency_message(guardian['user_name'])
    result = notification_service.send_sms(guardian['phone'], msg)
    if result['success']:
        add_log(f"✅ SMS 발송: {result['message_id'][:15]}...", "SUCCESS")
    else:
        add_log(f"❌ SMS 실패: {result.get('error')}", "ERROR")
    time.sleep(1)
    
    # Step 5
    status_ph.markdown(render_steps(5), unsafe_allow_html=True)
    add_log("=== STEP 5: 완료 ===", "SUCCESS")
    vf = voice_service.synthesize_step(5, guardian['user_name'], voice_id)
    if vf and os.path.exists(vf):
        voice_ph.audio(open(vf, 'rb').read(), format='audio/mp3')
    
    user_settings_table.update_item(
        Key={'userId': user_id},
        UpdateExpression='SET #s = :s',
        ExpressionAttributeNames={'#s': 'status'},
        ExpressionAttributeValues={':s': 'active'}
    )
    add_log("✅ 상태 복구: active", "SUCCESS")
    add_log("🎉 워크플로우 완료!", "SUCCESS")
    
    trigger_service.update_status(user_id, 'completed', 5)

# 메인 UI
col1, col2 = st.columns([3, 1])

with col1:
    st.markdown("## 🔄 워크플로우 진행 상황")
    status_placeholder = st.empty()
    status_placeholder.markdown(render_steps(0), unsafe_allow_html=True)

with col2:
    st.markdown("## 📋 제어판")
    
    # 트리거 상태 확인
    user_id = 'test-user-001'
    trigger = trigger_service.get_pending_trigger(user_id)
    
    if trigger:
        st.success(f"🎯 트리거 감지됨! 음성: {trigger.get('voice', 'Seoyeon')}")
        if st.button("▶️ 워크플로우 시작", type="primary"):
            st.session_state.start_workflow = True
            st.session_state.voice_id = trigger.get('voice', 'Seoyeon')
    else:
        st.info("⏳ 트리거 대기 중...")
        st.caption("개발자 대시보드(8503)에서 '시나리오 실행' 버튼을 클릭하세요")
    
    if st.button("🔄 새로고침"):
        st.rerun()
    
    # 자동 새로고침 (5초)
    auto_refresh = st.checkbox("자동 새로고침 (5초)", value=True)

# 로그 및 음성
st.markdown("## 📝 실행 로그")
log_placeholder = st.empty()
log_placeholder.markdown("<div class='log-container'>대기 중...</div>", unsafe_allow_html=True)

st.markdown("## 🔊 음성 안내")
voice_placeholder = st.empty()

st.markdown("## 📋 시스템 정보")
info_placeholder = st.empty()

# 워크플로우 실행
if st.session_state.get('start_workflow'):
    st.session_state.start_workflow = False
    voice_id = st.session_state.get('voice_id', 'Seoyeon')
    run_workflow(voice_id, status_placeholder, log_placeholder, voice_placeholder, info_placeholder)
    st.success("✅ 워크플로우 완료!")
    st.balloons()

# 자동 새로고침
if auto_refresh and not trigger:
    time.sleep(5)
    st.rerun()

# Footer
st.markdown("---")
st.caption("실시간 현황 대시보드 | 포트: 8505")
