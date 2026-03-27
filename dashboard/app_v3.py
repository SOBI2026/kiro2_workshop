import streamlit as st
import boto3
import json
import time
from datetime import datetime
from decimal import Decimal
import os
import uuid
from zoneinfo import ZoneInfo

# 한국 시간대 설정
KST = ZoneInfo("Asia/Seoul")

def now_kst():
    """현재 한국 시간 반환"""
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
    .step-inactive {
        background: #f5f5f5;
        color: #999;
    }
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
        height: 400px;
        overflow-y: auto;
        margin-top: 1rem;
    }
    .big-button {
        font-size: 1.5rem !important;
        padding: 1rem 2rem !important;
        width: 100% !important;
    }
    .trigger-detected {
        background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 1rem;
        animation: pulse 1s infinite;
    }
</style>
""", unsafe_allow_html=True)

# AWS clients
try:
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    polly_client = boto3.client('polly', region_name='us-east-1')
    sns_client = boto3.client('sns', region_name='us-east-1')
    trigger_table = dynamodb.Table('SeniorCare-WorkflowTrigger')
except Exception as e:
    st.error(f"AWS 클라이언트 초기화 오류: {str(e)}")
    st.stop()

# 트리거 확인 함수
def check_pending_trigger(user_id=None):
    """pending 상태의 트리거 확인 (모든 사용자 또는 특정 사용자)"""
    try:
        # 먼저 test-user-001 확인
        response = trigger_table.get_item(Key={'userId': 'test-user-001', 'triggerId': 'latest'})
        item = response.get('Item')
        if item and item.get('status') == 'pending':
            return item
        
        # test-user-002 확인 (박철수)
        response = trigger_table.get_item(Key={'userId': 'test-user-002', 'triggerId': 'latest'})
        item = response.get('Item')
        if item and item.get('status') == 'pending':
            return item
    except:
        pass
    return None

# 음성 나레이터 에이전트
import edge_tts
import asyncio
import base64

class VoiceNarrator:
    """워크플로우 진행 상황을 음성으로 안내하는 나레이터 에이전트 (edge-tts 사용)"""
    
    def __init__(self, voice='ko-KR-InJoonNeural'):
        self.voice = voice  # 인준 (남성)
        self.audio_placeholder = None
        self.audio_counter = 0
        # 절대 경로로 voice_outputs 폴더 생성
        self.output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'voice_outputs')
        os.makedirs(self.output_dir, exist_ok=True)
    
    def set_placeholder(self, placeholder):
        """Streamlit audio placeholder 설정"""
        self.audio_placeholder = placeholder
    
    def speak(self, text, rate="+0%"):
        """텍스트를 음성으로 변환하고 재생"""
        try:
            filename = os.path.join(self.output_dir, f'narrator_{now_kst().strftime("%H%M%S%f")}.mp3')
            
            # edge-tts는 async이므로 동기적으로 실행
            async def generate():
                communicate = edge_tts.Communicate(text, self.voice, rate=rate)
                await communicate.save(filename)
            
            # 새 이벤트 루프 생성
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(generate())
            finally:
                loop.close()
            
            if self.audio_placeholder and os.path.exists(filename):
                # 파일 읽기
                with open(filename, 'rb') as f:
                    audio_bytes = f.read()
                
                # Base64 인코딩으로 자동 재생 HTML 생성
                audio_b64 = base64.b64encode(audio_bytes).decode()
                
                # 자동 재생 HTML (JavaScript 사용)
                autoplay_html = f'''
                <div style="background: #2d2d2d; padding: 10px; border-radius: 8px; margin: 5px 0;">
                    <p style="color: #00ff00; margin: 0 0 8px 0;">🎙️ <b>나레이터 (인준):</b> {text}</p>
                    <audio id="narrator_audio_{self.audio_counter}" controls autoplay style="width: 100%;">
                        <source src="data:audio/mp3;base64,{audio_b64}" type="audio/mp3">
                    </audio>
                </div>
                <script>
                    var audio = document.getElementById("narrator_audio_{self.audio_counter}");
                    if (audio) {{
                        audio.volume = 1.0;
                        audio.play().catch(function(e) {{ console.log("Autoplay blocked:", e); }});
                    }}
                </script>
                '''
                self.audio_counter += 1
                self.audio_placeholder.markdown(autoplay_html, unsafe_allow_html=True)
            
            return filename
        except Exception as e:
            print(f"나레이터 오류: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def narrate_emergency_start(self, user_name, scenario):
        """응급상황 시작 안내"""
        if scenario == 'heat_inactivity':
            text = f"비상! 비상! {user_name}님 댁에서 폭염 위험 상황이 감지되었습니다. 워크플로우를 시작합니다."
        else:
            text = f"비상! 비상! {user_name}님 댁에서 이상 징후가 감지되었습니다. 워크플로우를 시작합니다."
        return self.speak(text, rate="+10%")
    
    def narrate_step1(self, scenario):
        """Step 1: 센서 데이터 수집"""
        if scenario == 'heat_inactivity':
            text = "1단계. 실내 온도 센서 데이터를 수집하고 있어요. 폭염으로 온도가 많이 올랐네요."
        else:
            text = "1단계. 센서 데이터를 수집하고 있어요. 정상 활동 데이터를 확인 중입니다."
        return self.speak(text)
    
    def narrate_step2(self, user_name, scenario):
        """Step 2: 이상 감지"""
        if scenario == 'heat_inactivity':
            text = f"2단계. 큰일이에요! {user_name}님의 활동이 전혀 감지되지 않아요. 모션 센서도 조용하고, 문도 안 열리고, 웨어러블 활동량도 없어요."
        else:
            text = f"2단계. 큰일이에요! 낙상이에요! {user_name}님이 넘어지신 것 같아요. 가속도 센서에서 급격한 변화가 감지됐어요."
        return self.speak(text, rate="+10%")
    
    def narrate_step3_start(self, user_name):
        """Step 3: AI 스피커 음성 확인 시작"""
        text = f"3단계. AI 스피커로 음성 확인을 해볼게요. 폴리야, {user_name}님 불러봐봐."
        return self.speak(text)
    
    def narrate_step3_waiting(self):
        """Step 3: 응답 대기 중"""
        text = "응답을 기다리고 있어요..."
        return self.speak(text)
    
    def narrate_step3_no_response(self):
        """Step 3: 응답 없음"""
        text = "아무런 응답이 없어요. 30초를 기다렸는데 대답이 없네요. 위험한 상황일 수 있어요!"
        return self.speak(text, rate="+10%")
    
    def narrate_step4(self, guardian_name):
        """Step 4: 보호자 알림 발송"""
        text = f"4단계. 보호자에게 알림을 발송할게요. {guardian_name}님에게 긴급 SMS를 보내고 있어요."
        return self.speak(text)
    
    def narrate_step4_sent(self):
        """Step 4: 발송 완료"""
        text = "SMS 발송 완료! 보호자님이 곧 확인하실 거예요."
        return self.speak(text)
    
    def narrate_step5(self, user_name):
        """Step 5: 완료"""
        text = f"5단계. 완료했어요! {user_name}님에 대한 조치가 취해질 거예요. 보호자님이 곧 연락하실 겁니다. 안심하세요."
        return self.speak(text)

def update_trigger_status(user_id, status):
    """트리거 상태 업데이트"""
    try:
        trigger_table.update_item(
            Key={'userId': user_id, 'triggerId': 'latest'},
            UpdateExpression='SET #s = :s',
            ExpressionAttributeNames={'#s': 'status'},
            ExpressionAttributeValues={':s': status}
        )
    except:
        pass

# Header
st.markdown("""
<div class="main-header">
    <h1>📊 시니어 안심 케어 - 실시간 현황</h1>
    <p>실시간 모니터링 및 워크플로우 진행 상황</p>
</div>
""", unsafe_allow_html=True)

# 트리거 감지 섹션
trigger = check_pending_trigger()

# 트리거가 감지되면 자동으로 워크플로우 실행
if trigger:
    user_id = trigger.get('userId', 'test-user-001')
    scenario = trigger.get('scenario', 'fall_detection')
    scenario_name = trigger.get('scenarioName', '낙상 감지')
    user_name = trigger.get('userName', '김영희')
    user_age = trigger.get('userAge', 75)
    selected_voice = trigger.get('voice', 'Seoyeon')
    
    # 시나리오별 색상
    if scenario == 'heat_inactivity':
        banner_color = "#ff9800"
        banner_icon = "🌡️"
    else:
        banner_color = "#4caf50"
        banner_icon = "🎯"
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, {banner_color} 0%, {banner_color}dd 100%); color: white; padding: 1rem; border-radius: 10px; text-align: center; margin-bottom: 1rem; animation: pulse 1s infinite;">
        <h2>{banner_icon} {scenario_name} 트리거 감지! 자동 실행 중...</h2>
        <p>👤 {user_name} ({user_age}세) | 🔊 음성: {selected_voice} | 🎙️ 나레이터: 인준</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 트리거 상태를 running으로 변경
    update_trigger_status(user_id, 'running')
    
    # 바로 워크플로우 실행
    with st.spinner("워크플로우 실행 중..."):
        status_placeholder = st.empty()
        log_placeholder = st.empty()
        narrator_placeholder = st.empty()  # 나레이터 음성용
        voice_placeholder = st.empty()  # Polly 음성용
        info_placeholder = st.empty()
        
        # 나레이터 초기화
        narrator = VoiceNarrator()
        narrator.set_placeholder(narrator_placeholder)
        
        logs = []
        
        def add_log(message, level="INFO"):
            timestamp = now_kst().strftime("%H:%M:%S")
            logs.append(f"[{timestamp}] [{level}] {message}")
            log_html = "<div class='log-container'>"
            for log in logs[-30:]:
                log_html += f"{log}<br>"
            log_html += "</div>"
            log_placeholder.markdown(log_html, unsafe_allow_html=True)
        
        def update_status(step_num, steps):
            status_html = ""
            for step in steps:
                if step_num == step["num"]:
                    step_class = "step-active"
                elif step_num > step["num"]:
                    step_class = "step-success" if step.get("success", True) else "step-warning"
                else:
                    step_class = "step-inactive"
                
                status_html += f"""
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
            status_placeholder.markdown(status_html, unsafe_allow_html=True)
        
        sensor_table = dynamodb.Table('SeniorCare-SensorData')
        user_settings_table = dynamodb.Table('SeniorCare-UserSettings')
        alert_table = dynamodb.Table('SeniorCare-AlertHistory')
        
        # 보호자 정보 로드
        add_log(f"=== {scenario_name} 시스템 초기화 ===")
        guardian_info = {'name': '보호자', 'phone': '010-3328-4472', 'email': 'guardian@example.com', 'relation': '자녀'}
        
        try:
            response = user_settings_table.get_item(Key={'userId': user_id})
            if 'Item' in response:
                settings = response['Item']
                guardian_info = {
                    'name': settings.get('guardianName', '보호자'),
                    'phone': settings.get('guardianPhone', '010-3328-4472'),
                    'email': settings.get('guardianEmail', 'guardian@example.com'),
                    'relation': settings.get('guardianRelation', '자녀')
                }
                user_name = settings.get('name', user_name)
                add_log(f"✅ 보호자: {guardian_info['name']} ({guardian_info['phone']})", "SUCCESS")
        except Exception as e:
            add_log(f"⚠️ 보호자 정보 로드 실패: {str(e)}", "WARNING")
        
        info_placeholder.info(f"👤 {user_name} ({user_age}세) | 📱 {guardian_info['phone']} | 🔊 Polly: {selected_voice} | 🎙️ 나레이터: 인준")
        
        # 🎙️ 나레이터: 응급상황 시작 안내
        add_log("🎙️ 나레이터: 응급상황 안내 시작", "INFO")
        narrator.narrate_emergency_start(user_name, scenario)
        time.sleep(4)
        
        # 낙상 감지 시나리오
        steps = [
            {"num": 1, "title": "센서 데이터 수집", "icon": "📊", "desc": "정상 활동 데이터 수집 중"},
            {"num": 2, "title": "낙상 감지" if scenario != 'heat_inactivity' else "활동 부재 감지", "icon": "🚨" if scenario != 'heat_inactivity' else "🚶", "desc": "이상 징후 감지", "success": False},
            {"num": 3, "title": "AI 스피커 음성 확인", "icon": "🗣️", "desc": "Polly 음성 생성 및 응답 대기"},
            {"num": 4, "title": "보호자 알림 발송", "icon": "📱", "desc": "SMS/푸시 알림 발송"},
            {"num": 5, "title": "완료", "icon": "✅", "desc": "모든 단계 완료"}
        ]
        
        # Step 1: 센서 데이터 수집
        update_status(1, steps)
        add_log("=== STEP 1: 센서 데이터 수집 ===")
        
        # 🎙️ 나레이터: Step 1 안내
        narrator.narrate_step1(scenario)
        time.sleep(3)
        
        if scenario == 'heat_inactivity':
            # 폭염 시나리오 - 온도 데이터
            for temp, desc in [(33.5, "오전 10시"), (35.2, "오후 1시"), (36.8, "오후 3시")]:
                sensor_table.put_item(Item={'userId': user_id, 'timestamp': int(now_kst().timestamp()), 'deviceId': 'temp-001', 'deviceType': 'iot', 'sensorType': 'temperature', 'value': Decimal(str(temp))})
                user_settings_table.update_item(Key={'userId': user_id}, UpdateExpression='SET lastActivityTime = :lat', ExpressionAttributeValues={':lat': now_kst().isoformat()})
                if temp >= 35:
                    add_log(f"🔥 {desc} 실내 온도: {temp}°C (위험!)", "WARNING")
                else:
                    add_log(f"🌡️ {desc} 실내 온도: {temp}°C")
                time.sleep(0.5)
        else:
            # 낙상 시나리오 - 정상 활동 데이터
            for st_type, val, desc in [("motion", 2.5, "거실"), ("door", 1.0, "방문"), ("temperature", 22.5, "온도")]:
                sensor_table.put_item(Item={'userId': user_id, 'timestamp': int(now_kst().timestamp()), 'deviceId': f'{st_type}-001', 'deviceType': 'iot', 'sensorType': st_type, 'value': Decimal(str(val))})
                user_settings_table.update_item(Key={'userId': user_id}, UpdateExpression='SET lastActivityTime = :lat', ExpressionAttributeValues={':lat': now_kst().isoformat()})
                add_log(f"✅ {desc}: {val}")
                time.sleep(0.3)
        time.sleep(1)
        
        # Step 2: 이상 감지
        update_status(2, steps)
        add_log("=== STEP 2: 이상 감지 ===", "WARNING")
        
        # 🎙️ 나레이터: Step 2 안내
        narrator.narrate_step2(user_name, scenario)
        time.sleep(4)
        
        if scenario == 'heat_inactivity':
            # 활동 부재 데이터
            for i in range(3):
                sensor_table.put_item(Item={'userId': user_id, 'timestamp': int(now_kst().timestamp()), 'deviceId': 'motion-001', 'deviceType': 'iot', 'sensorType': 'motion', 'value': Decimal('0.01')})
                add_log(f"🚶 모션 센서 {i+1}: 움직임 없음 (0.01)")
                time.sleep(0.3)
            sensor_table.put_item(Item={'userId': user_id, 'timestamp': int(now_kst().timestamp()), 'deviceId': 'door-001', 'deviceType': 'iot', 'sensorType': 'door', 'value': Decimal('0')})
            add_log("🚪 문 개폐 센서: 닫힘 상태 유지")
        else:
            # 낙상 데이터
            sensor_table.put_item(Item={'userId': user_id, 'timestamp': int(now_kst().timestamp()), 'deviceId': 'phone-001', 'deviceType': 'mobile', 'sensorType': 'accelerometer', 'value': Decimal('15.8')})
            user_settings_table.update_item(Key={'userId': user_id}, UpdateExpression='SET lastActivityTime = :lat', ExpressionAttributeValues={':lat': now_kst().isoformat()})
            add_log("🚨 낙상 발생! 가속도: 15.8", "ERROR")
        
        user_settings_table.update_item(Key={'userId': user_id}, UpdateExpression='SET #s = :s', ExpressionAttributeNames={'#s': 'status'}, ExpressionAttributeValues={':s': 'emergency'})
        add_log("⚠️ 상태: emergency", "ERROR")
        
        alert_id = str(uuid.uuid4())
        alert_table.put_item(Item={'userId': user_id, 'alertId': alert_id, 'alertType': scenario, 'status': 'voice_confirmation_pending', 'createdAt': now_kst().isoformat()})
        time.sleep(1)
        
        # Step 3: AI 스피커 음성 확인
        update_status(3, steps)
        add_log("=== STEP 3: 음성 확인 ===")
        
        # 🎙️ 나레이터: Step 3 시작 안내
        narrator.narrate_step3_start(user_name)
        time.sleep(3)
        
        # Polly 음성으로 사용자 호출
        try:
            if scenario == 'heat_inactivity':
                polly_text = f"{user_name}님, 오늘 날씨가 매우 덥습니다. 괜찮으세요? 물을 충분히 드시고 계신가요?"
            else:
                polly_text = f"{user_name}님, 괜찮으세요? 응답해 주세요."
            
            response = polly_client.synthesize_speech(Text=polly_text, OutputFormat='mp3', VoiceId=selected_voice, LanguageCode='ko-KR')
            vf = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'voice_outputs', f'polly_call_{now_kst().strftime("%H%M%S")}.mp3')
            with open(vf, 'wb') as f: f.write(response['AudioStream'].read())
            
            # Base64 인코딩으로 자동 재생
            with open(vf, 'rb') as f:
                polly_bytes = f.read()
            polly_b64 = base64.b64encode(polly_bytes).decode()
            polly_html = f'''
            <div style="background: #1a237e; padding: 10px; border-radius: 8px; margin: 5px 0;">
                <p style="color: #64b5f6; margin: 0 0 8px 0;">🔊 <b>Polly ({selected_voice}):</b> {polly_text}</p>
                <audio id="polly_audio" controls autoplay style="width: 100%;">
                    <source src="data:audio/mp3;base64,{polly_b64}" type="audio/mp3">
                </audio>
            </div>
            <script>
                var pollyAudio = document.getElementById("polly_audio");
                if (pollyAudio) {{
                    pollyAudio.volume = 1.0;
                    pollyAudio.play().catch(function(e) {{ console.log("Polly autoplay blocked:", e); }});
                }}
            </script>
            '''
            voice_placeholder.markdown(polly_html, unsafe_allow_html=True)
            add_log(f"🔊 Polly: {polly_text}")
        except Exception as e:
            add_log(f"⚠️ Polly 오류: {str(e)}", "WARNING")
        
        time.sleep(3)
        
        # 🎙️ 나레이터: 응답 대기
        narrator.narrate_step3_waiting()
        add_log("⏳ 응답 대기 중...")
        time.sleep(3)
        
        # 🎙️ 나레이터: 응답 없음
        narrator.narrate_step3_no_response()
        add_log("⚠️ 응답 없음!", "WARNING")
        time.sleep(3)
        
        # Step 4: 보호자 알림 발송
        update_status(4, steps)
        add_log("=== STEP 4: 알림 발송 ===", "ERROR")
        
        # 🎙️ 나레이터: Step 4 안내
        narrator.narrate_step4(guardian_info['name'])
        time.sleep(3)
        
        # SMS 발송
        try:
            phone = guardian_info['phone'].replace('-', '')
            if phone.startswith('010'): phone = '+82' + phone[1:]
            if scenario == 'heat_inactivity':
                msg = f"🌡️ 폭염 위험 알림\n{user_name}님 실내온도 36°C\n활동 없음, 응답 없음\n속히 확인 바람"
            else:
                msg = f"🚨 응급상황 발생\n{user_name}님 위험상황 발생\n낙상 의심, 응답 없음\n속히 연락 바람"
            result = sns_client.publish(PhoneNumber=phone, Message=msg, MessageAttributes={'AWS.SNS.SMS.SMSType': {'DataType': 'String', 'StringValue': 'Transactional'}})
            add_log(f"✅ SMS 발송: {result['MessageId'][:15]}...", "SUCCESS")
        except Exception as e:
            add_log(f"❌ SMS 실패: {str(e)}", "ERROR")
        
        # 🎙️ 나레이터: 발송 완료
        narrator.narrate_step4_sent()
        time.sleep(3)
        
        # Step 5: 완료
        update_status(5, steps)
        add_log("=== STEP 5: 완료 ===", "SUCCESS")
        
        # 🎙️ 나레이터: 완료 안내
        narrator.narrate_step5(user_name)
        time.sleep(4)
        
        user_settings_table.update_item(Key={'userId': user_id}, UpdateExpression='SET #s = :s', ExpressionAttributeNames={'#s': 'status'}, ExpressionAttributeValues={':s': 'active'})
        add_log("✅ 상태 복구: active", "SUCCESS")
        add_log("🎉 워크플로우 완료!", "SUCCESS")
        
        # 트리거 완료 처리
        update_trigger_status(user_id, 'completed')
    
    st.success("✅ 워크플로우 완료!")
    st.balloons()
    st.stop()

else:
    st.info("⏳ 트리거 대기 중... 개발자 대시보드(8503)에서 '시나리오 실행' 버튼을 클릭하세요")
    
    auto_refresh = st.checkbox("자동 새로고침 (3초)", value=True)
    
    if auto_refresh:
        time.sleep(3)
        st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p><b>버전 3:</b> 실시간 자동 데모 대시보드 + 🎙️ 인준 나레이터</p>
    <p><b>SMS 발송:</b> 010-3328-4472 (실제 발송)</p>
    <p style="font-size: 0.9rem;">포트: 8505 | AWS Polly + SNS + Edge-TTS 통합</p>
</div>
""", unsafe_allow_html=True)
