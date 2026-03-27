import streamlit as st
import boto3
import json
import time
from datetime import datetime
from decimal import Decimal
import os
import uuid

# Page configuration
st.set_page_config(
    page_title="시니어 안심 케어 - 실시간 자동 데모",
    page_icon="🎬",
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
    .step-inactive {
        background: #f5f5f5;
        color: #999;
    }
    .step-active {
        background: linear-gradient(135deg, #ffa500 0%, #ff8c00 100%);
        color: white;
        border-color: #ff6600;
        box-shadow: 0 0 20px rgba(255, 165, 0, 0.5);
    }
    .step-success {
        background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);
        color: white;
    }
    .step-warning {
        background: linear-gradient(135deg, #f44336 0%, #e53935 100%);
        color: white;
    }
    .log-container {
        background: #1e1e1e;
        color: #00ff00;
        padding: 1rem;
        border-radius: 5px;
        font-family: 'Courier New', monospace;
        height: 300px;
        overflow-y: auto;
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'workflow_running' not in st.session_state:
    st.session_state.workflow_running = False
if 'current_step' not in st.session_state:
    st.session_state.current_step = 0
if 'logs' not in st.session_state:
    st.session_state.logs = []
if 'speed' not in st.session_state:
    st.session_state.speed = 3

# AWS clients
try:
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    polly_client = boto3.client('polly', region_name='us-east-1')
    sns_client = boto3.client('sns', region_name='us-east-1')
except Exception as e:
    st.error(f"AWS 클라이언트 초기화 오류: {str(e)}")
    st.stop()

def add_log(message, level="INFO"):
    """Add log message"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.logs.append(f"[{timestamp}] [{level}] {message}")

# Header
st.markdown("""
<div class="main-header">
    <h1>🎬 시니어 안심 케어 - 실시간 자동 데모</h1>
    <p>버튼 하나로 전체 워크플로우를 자동으로 실행합니다</p>
</div>
""", unsafe_allow_html=True)

# Control Panel
st.markdown("## 🎮 제어판")

col1, col2, col3 = st.columns(3)

with col1:
    speed_option = st.selectbox(
        "속도 선택",
        options=["빠르게 (1초)", "보통 (3초)", "느리게 (5초)"],
        index=1
    )
    if "빠르게" in speed_option:
        st.session_state.speed = 1
    elif "느리게" in speed_option:
        st.session_state.speed = 5
    else:
        st.session_state.speed = 3

with col2:
    st.write("")
    st.write("")
    if st.button("▶️ 시나리오 자동 실행", type="primary", disabled=st.session_state.workflow_running):
        st.session_state.workflow_running = True
        st.session_state.current_step = 0
        st.session_state.logs = []
        add_log("🎬 워크플로우 시작!", "INFO")

with col3:
    st.write("")
    st.write("")
    if st.button("⏹️ 중지 및 초기화", disabled=not st.session_state.workflow_running):
        st.session_state.workflow_running = False
        st.session_state.current_step = 0
        st.session_state.logs = []
        add_log("⏹️ 워크플로우 중지됨", "WARNING")

# Workflow execution
if st.session_state.workflow_running:
    user_id = 'test-user-001'
    sensor_table = dynamodb.Table('SeniorCare-SensorData')
    user_settings_table = dynamodb.Table('SeniorCare-UserSettings')
    alert_table = dynamodb.Table('SeniorCare-AlertHistory')
    
    speed = st.session_state.speed
    
    # Step 1: 센서 데이터 수집
    if st.session_state.current_step == 0:
        st.session_state.current_step = 1
        add_log("=== STEP 1: 센서 데이터 수집 시작 ===")
        
        activities = [
            ("motion", 2.5, "거실에서 TV 시청"),
            ("door", 1.0, "방문 열림"),
            ("temperature", 22.5, "실내 온도 정상")
        ]
        
        for sensor_type, value, desc in activities:
            try:
                item = {
                    'userId': user_id,
                    'timestamp': int(datetime.utcnow().timestamp()),
                    'deviceId': f'{sensor_type}-sensor-001',
                    'deviceType': 'iot',
                    'sensorType': sensor_type,
                    'value': Decimal(str(value))
                }
                sensor_table.put_item(Item=item)
                user_settings_table.update_item(
                    Key={'userId': user_id},
                    UpdateExpression='SET lastActivityTime = :lat',
                    ExpressionAttributeValues={':lat': datetime.utcnow().isoformat() + 'Z'}
                )
                add_log(f"✅ {desc}: {sensor_type} = {value}")
            except Exception as e:
                add_log(f"❌ 오류: {str(e)}", "ERROR")
        
        add_log("✨ 정상 활동 데이터 수집 완료", "SUCCESS")
        time.sleep(speed)
        st.session_state.current_step = 2
        st.experimental_rerun()
    
    # Step 2: 낙상 감지
    elif st.session_state.current_step == 2:
        add_log("=== STEP 2: 낙상 감지 ===", "WARNING")
        
        try:
            # 화장실 이동
            item = {
                'userId': user_id,
                'timestamp': int(datetime.utcnow().timestamp()),
                'deviceId': 'door-sensor-bathroom',
                'deviceType': 'iot',
                'sensorType': 'door',
                'value': Decimal('1.0')
            }
            sensor_table.put_item(Item=item)
            add_log("🚶 화장실로 이동...")
            time.sleep(1)
            
            # 낙상 발생
            item = {
                'userId': user_id,
                'timestamp': int(datetime.utcnow().timestamp()),
                'deviceId': 'phone-001',
                'deviceType': 'mobile',
                'sensorType': 'accelerometer',
                'value': Decimal('15.8')
            }
            sensor_table.put_item(Item=item)
            add_log("🚨 낙상 발생! 가속도: 15.8 (임계값 10.0 초과)", "ERROR")
            time.sleep(2)
            
            # 활동 부재
            for i in range(3):
                item = {
                    'userId': user_id,
                    'timestamp': int(datetime.utcnow().timestamp()),
                    'deviceId': 'motion-sensor-bathroom',
                    'deviceType': 'iot',
                    'sensorType': 'motion',
                    'value': Decimal('0.05')
                }
                sensor_table.put_item(Item=item)
                add_log(f"⏰ {i+1}분: 움직임 거의 없음 (motion = 0.05)")
                time.sleep(1)
            
            # 알림 생성
            alert_id = str(uuid.uuid4())
            alert_item = {
                'userId': user_id,
                'alertId': alert_id,
                'alertType': 'fall_detected',
                'status': 'voice_confirmation_pending',
                'createdAt': datetime.utcnow().isoformat(),
                'lastActivityTime': datetime.utcnow().isoformat(),
                'retryCount': 0
            }
            alert_table.put_item(Item=alert_item)
            add_log(f"✅ 알림 생성: {alert_id[:8]}...", "WARNING")
            st.session_state.alert_id = alert_id
            
        except Exception as e:
            add_log(f"❌ 오류: {str(e)}", "ERROR")
        
        time.sleep(speed)
        st.session_state.current_step = 3
        st.experimental_rerun()
    
    # Step 3: AI 스피커 음성 확인
    elif st.session_state.current_step == 3:
        add_log("=== STEP 3: AI 스피커 음성 확인 ===")
        
        message_text = "김영희님, 넘어지신 것 같습니다. 괜찮으신가요? 응답해주세요."
        add_log(f"🗣️ Polly 음성 생성 중...")
        add_log(f"   텍스트: {message_text}")
        
        try:
            response = polly_client.synthesize_speech(
                Text=message_text,
                OutputFormat='mp3',
                VoiceId='Seoyeon',
                Engine='neural',
                LanguageCode='ko-KR'
            )
            
            os.makedirs('voice_outputs', exist_ok=True)
            voice_file = f'voice_outputs/auto_demo_{datetime.now().strftime("%H%M%S")}.mp3'
            with open(voice_file, 'wb') as file:
                file.write(response['AudioStream'].read())
            
            add_log(f"✅ 음성 생성 완료: {voice_file}", "SUCCESS")
            add_log("🔊 AI 스피커로 음성 전송 중...")
            st.session_state.current_voice_file = voice_file
            
        except Exception as e:
            add_log(f"❌ Polly 오류: {str(e)}", "ERROR")
        
        time.sleep(2)
        
        # 응답 대기
        add_log("⏳ 30초 동안 응답 대기 중... (시뮬레이션: 3초)")
        for i in range(3):
            add_log(f"   {i+1}초...")
            time.sleep(1)
        
        # 응답 없음
        add_log("⚠️ 응답 없음! (30초 타임아웃)", "WARNING")
        
        try:
            alert_table.update_item(
                Key={'userId': user_id, 'alertId': st.session_state.alert_id},
                UpdateExpression='SET #status = :status',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={':status': 'no_response'}
            )
            add_log("✅ 알림 상태 업데이트: no_response")
        except Exception as e:
            add_log(f"❌ 오류: {str(e)}", "ERROR")
        
        time.sleep(speed)
        st.session_state.current_step = 4
        st.experimental_rerun()
    
    # Step 4: 보호자 알림 발송
    elif st.session_state.current_step == 4:
        add_log("=== STEP 4: 보호자 알림 발송 ===", "ERROR")
        
        notification_message = f"""🚨 긴급 알림

김영희님(75세)에게 이상 징후가 감지되었습니다.

⚠️ 낙상 의심 (가속도: 15.8)
⚠️ 음성 응답 없음
⚠️ 즉시 확인이 필요합니다

📍 위치: 서울시 강남구 (자택)
🕐 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

[지금 확인하기]"""
        
        add_log("📱 긴급 알림 메시지 생성 완료")
        
        # 실제 SMS 발송
        try:
            add_log("📤 SMS 발송 중... (010-3328-4472)")
            
            response = sns_client.publish(
                PhoneNumber='+821033284472',
                Message=notification_message,
                MessageAttributes={
                    'AWS.SNS.SMS.SMSType': {
                        'DataType': 'String',
                        'StringValue': 'Transactional'
                    }
                }
            )
            
            add_log(f"✅ SMS 발송 완료! MessageId: {response['MessageId'][:20]}...", "SUCCESS")
            
        except Exception as e:
            add_log(f"❌ SMS 발송 오류: {str(e)}", "ERROR")
            add_log("   (AWS SNS 권한 또는 설정을 확인하세요)")
        
        add_log("✅ 푸시 알림 발송 완료 (시뮬레이션)", "SUCCESS")
        add_log("✅ 이메일 발송 완료 (시뮬레이션)", "SUCCESS")
        
        time.sleep(speed)
        st.session_state.current_step = 5
        st.experimental_rerun()
    
    # Step 5: 완료
    elif st.session_state.current_step == 5:
        add_log("=== 워크플로우 완료 ===", "SUCCESS")
        add_log("✨ 모든 단계가 성공적으로 완료되었습니다!")
        add_log("🔄 대시보드를 새로고침하여 최신 상태를 확인하세요.")
        
        st.session_state.workflow_running = False
        st.experimental_rerun()

# Workflow Steps Visualization
st.markdown("## 🔄 워크플로우 진행 상황")

steps = [
    {"num": 1, "title": "센서 데이터 수집", "icon": "📊", "desc": "정상 활동 데이터 수집 중"},
    {"num": 2, "title": "낙상 감지", "icon": "🚨", "desc": "가속도 센서 이상 징후 감지"},
    {"num": 3, "title": "AI 스피커 음성 확인", "icon": "🗣️", "desc": "Polly 음성 생성 및 응답 대기"},
    {"num": 4, "title": "보호자 알림 발송", "icon": "📱", "desc": "SMS/푸시 알림 발송"},
    {"num": 5, "title": "완료", "icon": "✅", "desc": "모든 단계 완료"}
]

for step in steps:
    if st.session_state.current_step == step["num"]:
        step_class = "step-active"
    elif st.session_state.current_step > step["num"]:
        step_class = "step-success" if step["num"] != 2 else "step-warning"
    else:
        step_class = "step-inactive"
    
    st.markdown(f"""
    <div class="workflow-step {step_class}">
        <div style="font-size: 2rem; text-align: center;">{step["icon"]}</div>
        <div style="font-size: 1.5rem; font-weight: bold; text-align: center; margin-top: 0.5rem;">
            {step["num"]}. {step["title"]}
        </div>
        <div style="text-align: center; margin-top: 0.5rem; font-size: 0.9rem;">
            {step["desc"]}
        </div>
    </div>
    """, unsafe_allow_html=True)

# Voice Player
if st.session_state.current_step == 3 and 'current_voice_file' in st.session_state:
    st.markdown("### 🔊 AI 스피커 음성")
    voice_file = st.session_state.current_voice_file
    if os.path.exists(voice_file):
        with open(voice_file, 'rb') as audio_file:
            audio_bytes = audio_file.read()
        st.audio(audio_bytes, format='audio/mp3')

# Real-time Logs
st.markdown("## 📋 실시간 로그")

log_html = "<div class='log-container'>"
for log in st.session_state.logs[-20:]:
    log_html += f"{log}<br>"
log_html += "</div>"

st.markdown(log_html, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p><b>버전 3:</b> 실시간 자동 데모 대시보드</p>
    <p><b>SMS 발송:</b> 010-3328-4472 (실제 발송)</p>
    <p style="font-size: 0.9rem;">포트: 8505 | AWS Polly + SNS 통합</p>
</div>
""", unsafe_allow_html=True)
