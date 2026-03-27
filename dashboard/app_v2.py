import streamlit as st
import boto3
import json
import pandas as pd
from datetime import datetime, timedelta
from decimal import Decimal
import plotly.express as px
import plotly.graph_objects as go
import os

# Page configuration
st.set_page_config(
    page_title="시니어 안심 케어 - 아키텍처 뷰",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for card-based layout
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
    .card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
        border-left: 4px solid #667eea;
    }
    .card-title {
        font-size: 1.2rem;
        font-weight: bold;
        color: #667eea;
        margin-bottom: 0.5rem;
    }
    .card-subtitle {
        font-size: 0.9rem;
        color: #666;
        margin-bottom: 1rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
    }
    .metric-label {
        font-size: 1rem;
        opacity: 0.9;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #667eea;
        margin: 2rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #667eea;
    }
</style>
""", unsafe_allow_html=True)

# AWS clients
@st.cache_resource
def get_aws_clients():
    return {
        'dynamodb': boto3.resource('dynamodb'),
        'lambda': boto3.client('lambda'),
        'cloudwatch': boto3.client('cloudwatch'),
        'polly': boto3.client('polly')
    }

clients = get_aws_clients()

# Header
st.markdown("""
<div class="main-header">
    <h1>🏥 시니어 안심 케어</h1>
    <p>AI 기반 독거 노인 안전 모니터링 시스템</p>
</div>
""", unsafe_allow_html=True)

# Architecture Overview
st.markdown('<div class="section-header">📋 시스템 아키텍처</div>', unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    <div class="card">
        <div class="card-title">1️⃣ 데이터 수집</div>
        <div class="card-subtitle">센서 데이터 수집</div>
        <p>📱 <b>Mobile App</b><br>가족용 앱</p>
        <p>🔌 <b>IoT Sensors</b><br>센서 수집</p>
        <p>☁️ <b>AWS IoT Core</b><br>안전 수집</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="card">
        <div class="card-title">2️⃣ 분석/저장</div>
        <div class="card-subtitle">데이터 처리</div>
        <p>🗄️ <b>DynamoDB</b><br>실시간 데이터</p>
        <p>⚡ <b>Lambda</b><br>실시간 분석</p>
        <p>⏰ <b>Trigger</b><br>이벤트 감지</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="card">
        <div class="card-title">3️⃣ AI 에이전트</div>
        <div class="card-subtitle">지능형 분석</div>
        <p>🤖 <b>Bedrock</b><br>Claude 3.5</p>
        <p>💬 <b>상황 분석</b><br>대화 생성</p>
        <p>🗣️ <b>Polly</b><br>음성 변환</p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div class="card">
        <div class="card-title">4️⃣ 대응</div>
        <div class="card-subtitle">알림 및 대응</div>
        <p>✅ <b>정상 응답</b><br>대화형 리포트</p>
        <p>📞 <b>무응답/위급</b><br>긴급 알림</p>
        <p>📍 <b>Pinpoint/SNS</b><br>보호자 알림</p>
    </div>
    """, unsafe_allow_html=True)

# Real-time Metrics
st.markdown('<div class="section-header">📊 실시간 시스템 현황</div>', unsafe_allow_html=True)

user_id = 'test-user-001'

try:
    # Get user data
    user_settings_table = clients['dynamodb'].Table('SeniorCare-UserSettings')
    response = user_settings_table.get_item(Key={'userId': user_id})
    
    if 'Item' in response:
        user_data = response['Item']
        
        # Get sensor data count
        sensor_data_table = clients['dynamodb'].Table('SeniorCare-SensorData')
        sensor_response = sensor_data_table.query(
            KeyConditionExpression='userId = :uid',
            ExpressionAttributeValues={':uid': user_id},
            ScanIndexForward=False,
            Limit=100
        )
        
        sensor_count = len(sensor_response['Items'])
        
        # Get alert count
        alert_table = clients['dynamodb'].Table('SeniorCare-AlertHistory')
        alert_response = alert_table.query(
            KeyConditionExpression='userId = :uid',
            ExpressionAttributeValues={':uid': user_id},
            ScanIndexForward=False
        )
        
        alert_count = len(alert_response['Items'])
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{user_data.get('name', 'N/A')}</div>
                <div class="metric-label">모니터링 대상</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            status = user_data.get('status', 'unknown')
            status_emoji = "🟢" if status == 'active' else "🔴"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{status_emoji} {status}</div>
                <div class="metric-label">현재 상태</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{sensor_count}</div>
                <div class="metric-label">센서 데이터 (최근 100개)</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{alert_count}</div>
                <div class="metric-label">총 알림 수</div>
            </div>
            """, unsafe_allow_html=True)

except Exception as e:
    st.error(f"데이터 로드 오류: {str(e)}")

# Real-time Workflow Status
st.markdown('<div class="section-header">🔄 실시간 워크플로우 상태</div>', unsafe_allow_html=True)

# Get latest alert to determine workflow status
try:
    alert_table = clients['dynamodb'].Table('SeniorCare-AlertHistory')
    alert_response = alert_table.query(
        KeyConditionExpression='userId = :uid',
        ExpressionAttributeValues={':uid': user_id},
        ScanIndexForward=False,
        Limit=1
    )
    
    latest_alert = alert_response['Items'][0] if alert_response['Items'] else None
    alert_status = latest_alert.get('status', 'none') if latest_alert else 'none'
    
    # Check for fall detection in recent sensor data
    sensor_data_table = clients['dynamodb'].Table('SeniorCare-SensorData')
    sensor_response = sensor_data_table.query(
        KeyConditionExpression='userId = :uid',
        ExpressionAttributeValues={':uid': user_id},
        ScanIndexForward=False,
        Limit=50
    )
    
    fall_detected = False
    for item in sensor_response['Items']:
        if item.get('sensorType') == 'accelerometer' and float(item.get('value', 0)) > 10.0:
            fall_detected = True
            break
    
    # Determine workflow step statuses
    step1_status = "active"  # Always active if we have data
    step2_status = "warning" if fall_detected else "active"
    step3_status = "pending" if alert_status == 'voice_confirmation_pending' else ("success" if alert_status == 'confirmed_safe' else "inactive")
    step4_status = "warning" if alert_status == 'no_response' else ("success" if alert_status == 'resolved' else "inactive")
    
    # Status colors and emojis
    status_config = {
        "active": {"color": "#667eea", "emoji": "✅", "text": "정상"},
        "warning": {"color": "#f5576c", "emoji": "⚠️", "text": "경고"},
        "pending": {"color": "#ffa500", "emoji": "⏳", "text": "진행중"},
        "success": {"color": "#4caf50", "emoji": "✔️", "text": "완료"},
        "inactive": {"color": "#cccccc", "emoji": "⏸️", "text": "대기"}
    }
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        config = status_config[step1_status]
        st.markdown(f"""
        <div class="card" style="background: {config['color']}; color: white; border: none;">
            <div style="text-align: center; font-size: 3rem;">{config['emoji']}</div>
            <div style="text-align: center; font-size: 1.2rem; font-weight: bold; margin-top: 1rem;">1. 센서 데이터 수집</div>
            <div style="text-align: center; margin-top: 0.5rem; font-size: 1rem; font-weight: bold;">{config['text']}</div>
            <div style="text-align: center; margin-top: 1rem; font-size: 0.9rem;">
                • 센서 데이터: {sensor_count}개<br>
                • 실시간 수집 중<br>
                • DynamoDB 저장 완료
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        config = status_config[step2_status]
        status_text = "낙상 감지!" if fall_detected else "정상 활동"
        st.markdown(f"""
        <div class="card" style="background: {config['color']}; color: white; border: none;">
            <div style="text-align: center; font-size: 3rem;">{config['emoji']}</div>
            <div style="text-align: center; font-size: 1.2rem; font-weight: bold; margin-top: 1rem;">2. 활동 부재 감지</div>
            <div style="text-align: center; margin-top: 0.5rem; font-size: 1rem; font-weight: bold;">{status_text}</div>
            <div style="text-align: center; margin-top: 1rem; font-size: 0.9rem;">
                • {"가속도: 15.8 초과" if fall_detected else "정상 범위"}<br>
                • {"이상 징후 탐지" if fall_detected else "패턴 분석 중"}<br>
                • {"알림 생성됨" if fall_detected else "모니터링 중"}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        config = status_config[step3_status]
        if alert_status == 'voice_confirmation_pending':
            status_text = "음성 확인 중"
            detail = "• AI 스피커 호출 중<br>• 안부 확인 질문<br>• 응답 대기 (30초)"
        elif alert_status == 'confirmed_safe':
            status_text = "응답 확인됨"
            detail = "• 정상 응답 수신<br>• 안전 확인 완료<br>• 모니터링 계속"
        else:
            status_text = "대기 중"
            detail = "• 알림 없음<br>• 정상 상태<br>• 대기 모드"
        
        st.markdown(f"""
        <div class="card" style="background: {config['color']}; color: white; border: none;">
            <div style="text-align: center; font-size: 3rem;">{config['emoji']}</div>
            <div style="text-align: center; font-size: 1.2rem; font-weight: bold; margin-top: 1rem;">3. AI 스피커 음성 확인</div>
            <div style="text-align: center; margin-top: 0.5rem; font-size: 1rem; font-weight: bold;">{status_text}</div>
            <div style="text-align: center; margin-top: 1rem; font-size: 0.9rem;">
                {detail}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        config = status_config[step4_status]
        if alert_status == 'no_response':
            status_text = "긴급 알림 발송"
            detail = "• 음성 응답 없음<br>• SMS 발송 완료<br>• 보호자 확인 필요"
        elif alert_status == 'resolved':
            status_text = "처리 완료"
            detail = "• 보호자 확인 완료<br>• 상황 종료<br>• 정상 모니터링"
        else:
            status_text = "대기 중"
            detail = "• 알림 대기<br>• 음성 확인 우선<br>• 자동 대기 모드"
        
        st.markdown(f"""
        <div class="card" style="background: {config['color']}; color: white; border: none;">
            <div style="text-align: center; font-size: 3rem;">{config['emoji']}</div>
            <div style="text-align: center; font-size: 1.2rem; font-weight: bold; margin-top: 1rem;">4. 보호자 알림</div>
            <div style="text-align: center; margin-top: 0.5rem; font-size: 1rem; font-weight: bold;">{status_text}</div>
            <div style="text-align: center; margin-top: 1rem; font-size: 0.9rem;">
                {detail}
            </div>
        </div>
        """, unsafe_allow_html=True)

except Exception as e:
    st.error(f"워크플로우 상태 로드 오류: {str(e)}")

# Workflow Details Section
st.markdown('<div class="section-header">📋 시스템 워크플로우 상세</div>', unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    <div class="card" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none;">
        <div style="text-align: center; font-size: 3rem;">📊</div>
        <div style="text-align: center; font-size: 1.2rem; font-weight: bold; margin-top: 1rem;">센서 데이터 수집</div>
        <div style="text-align: center; margin-top: 1rem; font-size: 0.9rem;">
            • 휴대폰 가속도센서 (1초 간격)<br>
            • IoT 센서 (5분 간격)<br>
            • 실시간 DynamoDB 저장<br>
            • 마지막 활동 시간 업데이트
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; border: none;">
        <div style="text-align: center; font-size: 3rem;">⏰</div>
        <div style="text-align: center; font-size: 1.2rem; font-weight: bold; margin-top: 1rem;">활동 부재 감지</div>
        <div style="text-align: center; margin-top: 1rem; font-size: 0.9rem;">
            • EventBridge 1분마다 실행<br>
            • 임계값 초과 시 알림 생성<br>
            • 활동 패턴 분석<br>
            • 이상 징후 탐지
        </div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: white; border: none;">
        <div style="text-align: center; font-size: 3rem;">🗣️</div>
        <div style="text-align: center; font-size: 1.2rem; font-weight: bold; margin-top: 1rem;">AI 스피커 음성 확인</div>
        <div style="text-align: center; margin-top: 1rem; font-size: 0.9rem;">
            • Alexa/Google/Clova 연동<br>
            • 자동 안부 확인 질문<br>
            • 음성 응답 대기 (30초)<br>
            • 응답 패턴 분석
        </div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div class="card" style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); color: white; border: none;">
        <div style="text-align: center; font-size: 3rem;">📱</div>
        <div style="text-align: center; font-size: 1.2rem; font-weight: bold; margin-top: 1rem;">보호자 알림</div>
        <div style="text-align: center; margin-top: 1rem; font-size: 0.9rem;">
            • 음성 응답 없을 시 발송<br>
            • SNS/SQS 통한 알림<br>
            • SMS/푸시 알림<br>
            • 재시도 로직 (최대 3회)
        </div>
    </div>
    """, unsafe_allow_html=True)

# Sensor Types
st.markdown('<div class="section-header">🔌 센서 타입 설명</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="card">
        <div class="card-title">🚶 motion (동작 감지 센서)</div>
        <p>• 실내에서 사람의 움직임을 감지</p>
        <p>• 거실, 침실, 화장실 등에 설치</p>
        <p>• 일정 시간 동안 움직임이 없으면 활동 부재로 판단</p>
    </div>
    
    <div class="card">
        <div class="card-title">🚪 door (문 개폐 센서)</div>
        <p>• 현관문, 방문, 화장실 문 등의 개폐 감지</p>
        <p>• 외출/귀가 패턴 파악</p>
        <p>• 화장실 사용 빈도 모니터링</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="card">
        <div class="card-title">📱 accelerometer (가속도 센서)</div>
        <p>• 스마트폰이나 웨어러블 기기에 내장</p>
        <p>• 걸음 수, 활동량 측정</p>
        <p>• 낙상 감지 (급격한 가속도 변화)</p>
    </div>
    
    <div class="card">
        <div class="card-title">🌡️ temperature (온도 센서)</div>
        <p>• 실내 온도 모니터링</p>
        <p>• 여름철 폭염, 겨울철 저체온증 예방</p>
        <p>• 난방/냉방 기기 작동 여부 확인</p>
    </div>
    """, unsafe_allow_html=True)

# Additional Features
st.markdown('<div class="section-header">⚙️ 추가 기능</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="card">
        <div class="card-title">📈 리포트 생성</div>
        <p>• <b>일일 리포트:</b> 매일 오전 9시 자동 생성</p>
        <p>• <b>월간 리포트:</b> 매월 1일 자동 생성</p>
        <p>• PDF 형식으로 S3 저장</p>
        <p>• 활동 패턴 분석 및 통계</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="card">
        <div class="card-title">🔐 보안 및 암호화</div>
        <p>• <b>KMS 암호화:</b> DynamoDB 데이터 암호화</p>
        <p>• <b>Secrets Manager:</b> RDS 자격증명 관리</p>
        <p>• <b>TLS 1.2+:</b> 전송 중 데이터 암호화</p>
        <p>• IAM 역할 기반 접근 제어</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="card">
        <div class="card-title">🔄 에러 처리 및 복구</div>
        <p>• <b>재시도 로직:</b> 최대 3회 지수 백오프</p>
        <p>• <b>DLQ:</b> 실패한 메시지 저장</p>
        <p>• <b>CloudWatch 알람:</b> 에러율 모니터링</p>
        <p>• 자동 복구 메커니즘</p>
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("---")

# Workflow Simulation Controls
st.markdown('<div class="section-header">🎮 워크플로우 시뮬레이션</div>', unsafe_allow_html=True)

# Voice Player Section
st.markdown("""
<div class="card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: white; border: none; margin-bottom: 2rem;">
    <div style="text-align: center;">
        <div style="font-size: 2rem;">🗣️</div>
        <div style="font-size: 1.3rem; font-weight: bold; margin-top: 0.5rem;">AI 스피커 음성 확인 (AWS Polly)</div>
        <div style="font-size: 0.9rem; margin-top: 0.5rem;">Neural TTS로 생성된 자연스러운 한국어 음성</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Voice message selection
voice_messages = {
    "일반 안부 확인": {
        "file": "greeting.mp3",
        "text": "안녕하세요, 김영희님. 괜찮으신가요?",
        "scenario": "정기 안부 확인"
    },
    "낙상 감지": {
        "file": "fall_detected.mp3",
        "text": "김영희님, 넘어지신 것 같습니다. 괜찮으신가요? 응답해주세요.",
        "scenario": "가속도 센서가 급격한 충격 감지"
    },
    "활동 부재": {
        "file": "no_movement.mp3",
        "text": "김영희님, 2시간 동안 움직임이 감지되지 않았습니다. 안전하신가요?",
        "scenario": "임계값 초과 (120분 이상 활동 없음)"
    },
    "긴급 상황": {
        "file": "emergency.mp3",
        "text": "긴급 상황이 감지되었습니다. 즉시 응답해주세요. 응답이 없으면 보호자에게 연락하겠습니다.",
        "scenario": "낙상 + 활동 부재 복합 상황"
    },
    "정상 응답 확인": {
        "file": "confirmation.mp3",
        "text": "네, 알겠습니다. 안전하시다니 다행입니다. 계속 모니터링하겠습니다.",
        "scenario": "사용자 정상 응답 후"
    }
}

col_voice1, col_voice2 = st.columns([2, 1])

with col_voice1:
    selected_voice = st.selectbox(
        "🎵 음성 메시지 선택",
        list(voice_messages.keys()),
        key="voice_select"
    )
    
    voice_info = voice_messages[selected_voice]
    
    st.info(f"📝 **텍스트**: {voice_info['text']}")
    st.info(f"📋 **시나리오**: {voice_info['scenario']}")
    
    # Check if voice file exists
    voice_file_path = f"voice_outputs/{voice_info['file']}"
    if os.path.exists(voice_file_path):
        # Read audio file
        with open(voice_file_path, 'rb') as audio_file:
            audio_bytes = audio_file.read()
        
        st.audio(audio_bytes, format='audio/mp3')
        st.success(f"✅ 음성 파일 준비 완료 ({voice_info['file']})")
    else:
        st.warning(f"⚠️ 음성 파일이 없습니다. 생성 버튼을 클릭하세요.")

with col_voice2:
    st.markdown("### 🎙️ Polly 설정")
    st.write("**음성**: Seoyeon (여성)")
    st.write("**엔진**: Neural TTS")
    st.write("**언어**: 한국어")
    st.write("**품질**: 고품질")
    
    if st.button("🔄 음성 재생성", key="regenerate_voice"):
        with st.spinner("음성 생성 중..."):
            try:
                polly_client = clients.get('polly')
                if not polly_client:
                    polly_client = boto3.client('polly', region_name='us-east-1')
                
                # Generate voice for selected message
                response = polly_client.synthesize_speech(
                    Text=voice_info['text'],
                    OutputFormat='mp3',
                    VoiceId='Seoyeon',
                    Engine='neural',
                    LanguageCode='ko-KR'
                )
                
                # Save to file
                os.makedirs('voice_outputs', exist_ok=True)
                with open(voice_file_path, 'wb') as file:
                    file.write(response['AudioStream'].read())
                
                st.success("✅ 음성이 재생성되었습니다!")
                st.rerun()
            except Exception as e:
                st.error(f"오류: {str(e)}")

st.markdown("---")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="card">
        <div class="card-title">🗣️ 음성 응답 시뮬레이션</div>
        <p>AI 스피커 음성 확인 단계를 시뮬레이션합니다.</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("✅ 정상 응답 (안전)", key="voice_safe", type="primary"):
        try:
            alert_table = clients['dynamodb'].Table('SeniorCare-AlertHistory')
            alert_response = alert_table.query(
                KeyConditionExpression='userId = :uid',
                ExpressionAttributeValues={':uid': user_id},
                ScanIndexForward=False,
                Limit=1
            )
            
            if alert_response['Items']:
                alert_id = alert_response['Items'][0]['alertId']
                alert_table.update_item(
                    Key={'userId': user_id, 'alertId': alert_id},
                    UpdateExpression='SET #status = :status, voiceResponse = :response',
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={
                        ':status': 'confirmed_safe',
                        ':response': '네, 괜찮아요. 걱정 마세요.'
                    }
                )
                st.success("✅ 음성 응답 확인! 정상 상태로 업데이트되었습니다.")
                st.info("🔄 페이지를 새로고침하여 워크플로우 상태를 확인하세요.")
            else:
                st.warning("활성 알림이 없습니다.")
        except Exception as e:
            st.error(f"오류: {str(e)}")
    
    if st.button("⚠️ 응답 없음 (위급)", key="voice_no_response"):
        try:
            alert_table = clients['dynamodb'].Table('SeniorCare-AlertHistory')
            alert_response = alert_table.query(
                KeyConditionExpression='userId = :uid',
                ExpressionAttributeValues={':uid': user_id},
                ScanIndexForward=False,
                Limit=1
            )
            
            if alert_response['Items']:
                alert_id = alert_response['Items'][0]['alertId']
                alert_table.update_item(
                    Key={'userId': user_id, 'alertId': alert_id},
                    UpdateExpression='SET #status = :status',
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={':status': 'no_response'}
                )
                st.warning("⚠️ 음성 응답 없음! 보호자 알림 단계로 진행합니다.")
                st.info("🔄 페이지를 새로고침하여 워크플로우 상태를 확인하세요.")
            else:
                st.warning("활성 알림이 없습니다.")
        except Exception as e:
            st.error(f"오류: {str(e)}")

with col2:
    st.markdown("""
    <div class="card">
        <div class="card-title">📱 보호자 알림 시뮬레이션</div>
        <p>보호자에게 긴급 알림을 발송합니다.</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("📤 긴급 알림 발송", key="send_notification", type="primary"):
        try:
            alert_table = clients['dynamodb'].Table('SeniorCare-AlertHistory')
            alert_response = alert_table.query(
                KeyConditionExpression='userId = :uid',
                ExpressionAttributeValues={':uid': user_id},
                ScanIndexForward=False,
                Limit=1
            )
            
            if alert_response['Items'] and alert_response['Items'][0].get('status') == 'no_response':
                alert_id = alert_response['Items'][0]['alertId']
                
                # Simulate notification sent
                notification_message = """
                🚨 긴급 알림
                
                김영희님(75세)에게 이상 징후가 감지되었습니다.
                
                - 낙상 의심 (가속도: 15.8)
                - 음성 응답 없음
                - 즉시 확인이 필요합니다
                
                위치: 서울시 강남구 (자택)
                시간: 2026-03-27 12:23:36
                """
                
                st.error("🚨 긴급 알림 발송!")
                st.code(notification_message)
                st.success("✅ SMS 및 푸시 알림이 보호자에게 발송되었습니다.")
                st.info("📞 보호자: 010-1234-5678")
            else:
                st.warning("음성 응답 없음 상태가 아닙니다. 먼저 '응답 없음' 버튼을 클릭하세요.")
        except Exception as e:
            st.error(f"오류: {str(e)}")
    
    if st.button("✔️ 상황 종료", key="resolve"):
        try:
            alert_table = clients['dynamodb'].Table('SeniorCare-AlertHistory')
            alert_response = alert_table.query(
                KeyConditionExpression='userId = :uid',
                ExpressionAttributeValues={':uid': user_id},
                ScanIndexForward=False,
                Limit=1
            )
            
            if alert_response['Items']:
                alert_id = alert_response['Items'][0]['alertId']
                alert_table.update_item(
                    Key={'userId': user_id, 'alertId': alert_id},
                    UpdateExpression='SET #status = :status',
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={':status': 'resolved'}
                )
                st.success("✔️ 상황이 종료되었습니다. 정상 모니터링으로 돌아갑니다.")
                st.info("🔄 페이지를 새로고침하여 워크플로우 상태를 확인하세요.")
            else:
                st.warning("활성 알림이 없습니다.")
        except Exception as e:
            st.error(f"오류: {str(e)}")

with col3:
    st.markdown("""
    <div class="card">
        <div class="card-title">🔄 워크플로우 초기화</div>
        <p>새로운 시나리오를 테스트하기 위해 초기화합니다.</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🔄 워크플로우 초기화", key="reset"):
        try:
            # Delete all alerts
            alert_table = clients['dynamodb'].Table('SeniorCare-AlertHistory')
            alert_response = alert_table.query(
                KeyConditionExpression='userId = :uid',
                ExpressionAttributeValues={':uid': user_id}
            )
            
            for alert in alert_response['Items']:
                alert_table.delete_item(
                    Key={'userId': user_id, 'alertId': alert['alertId']}
                )
            
            st.success("✅ 모든 알림이 삭제되었습니다.")
            st.info("🔄 페이지를 새로고침하여 초기 상태를 확인하세요.")
        except Exception as e:
            st.error(f"오류: {str(e)}")
    
    st.markdown("---")
    
    if st.button("🚨 새 낙상 시나리오 실행", key="new_scenario"):
        st.info("💡 터미널에서 다음 명령어를 실행하세요:")
        st.code("python dashboard/run_scenario.py", language="bash")

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem;">
    <p><b>핵심 기능:</b> 센서 데이터 수집 → 활동 부재 감지 → AI 스피커 음성 확인 → 보호자 알림</p>
    <p><b>기술 스택:</b> AWS Lambda | DynamoDB | EventBridge | SNS/SQS | API Gateway</p>
    <p style="font-size: 0.9rem; margin-top: 1rem;">2026년 3월 | AWS SAM 기반 서버리스 아키텍처</p>
</div>
""", unsafe_allow_html=True)
