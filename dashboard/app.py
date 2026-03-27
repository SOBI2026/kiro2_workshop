import streamlit as st
import boto3
import json
import pandas as pd
from datetime import datetime, timedelta
from decimal import Decimal
import plotly.express as px
import plotly.graph_objects as go
from zoneinfo import ZoneInfo

# 한국 시간대 설정
KST = ZoneInfo("Asia/Seoul")

def to_kst(utc_time_str):
    """UTC 시간 문자열을 한국 시간으로 변환"""
    try:
        if isinstance(utc_time_str, str):
            dt = datetime.fromisoformat(utc_time_str.replace('Z', '+00:00'))
            return dt.astimezone(KST).strftime('%Y-%m-%d %H:%M:%S')
        return utc_time_str
    except:
        return utc_time_str

def now_kst():
    """현재 한국 시간 반환"""
    return datetime.now(KST)

# Page configuration
st.set_page_config(
    page_title="개발자 모니터링 대시보드",
    page_icon="🔧",
    layout="wide"
)

# AWS clients
@st.cache_resource
def get_aws_clients():
    return {
        'dynamodb': boto3.resource('dynamodb'),
        'lambda': boto3.client('lambda'),
        'sns': boto3.client('sns'),
        'cloudwatch': boto3.client('cloudwatch')
    }

clients = get_aws_clients()

# Title
st.title("🔧 개발자 모니터링 대시보드")
st.caption("시니어 안심 케어 시스템 - 백엔드 관리 및 모니터링")

# Sidebar
st.sidebar.header("설정")

# 사용자 선택 드롭다운
user_options = {
    "test-user-001": "👵 김영희 (75세)",
    "test-user-002": "👴 박철수 (66세)"
}
user_id = st.sidebar.selectbox(
    "사용자 선택",
    options=list(user_options.keys()),
    format_func=lambda x: user_options[x],
    help="모니터링할 사용자를 선택하세요"
)

refresh_interval = st.sidebar.slider("새로고침 간격 (초)", 5, 60, 10)

# 박철수 사용자 데이터 자동 생성 (없으면)
def ensure_user_exists(user_id, user_data):
    """사용자 데이터가 없으면 생성"""
    try:
        user_settings_table = clients['dynamodb'].Table('SeniorCare-UserSettings')
        response = user_settings_table.get_item(Key={'userId': user_id})
        if 'Item' not in response:
            user_settings_table.put_item(Item=user_data)
            return True
    except:
        pass
    return False

# 박철수 사용자 데이터 확인 및 생성
if user_id == 'test-user-002':
    created = ensure_user_exists('test-user-002', {
        'userId': 'test-user-002',
        'name': '박철수',
        'age': 66,
        'status': 'active',
        'inactivityThreshold': 60,
        'voiceResponseTimeout': 30,
        'guardianPhone': '010-3328-4472',
        'guardianName': '보호자',
        'guardianEmail': 'guardian@example.com',
        'guardianRelation': '자녀',
        'lastActivityTime': datetime.utcnow().isoformat() + 'Z'
    })
    if created:
        st.sidebar.success("✅ 박철수 사용자 데이터 생성됨")

# 김영희 사용자 데이터 확인 및 생성
if user_id == 'test-user-001':
    ensure_user_exists('test-user-001', {
        'userId': 'test-user-001',
        'name': '김영희',
        'age': 75,
        'status': 'active',
        'inactivityThreshold': 120,
        'voiceResponseTimeout': 30,
        'guardianPhone': '010-3328-4472',
        'guardianName': '보호자',
        'guardianEmail': 'guardian@example.com',
        'guardianRelation': '자녀',
        'lastActivityTime': datetime.utcnow().isoformat() + 'Z'
    })

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 실시간 모니터링", 
    "🎬 시나리오 실행",
    "📱 센서 데이터 전송", 
    "🔔 알림 이력", 
    "⚙️ 설정 관리",
    "📈 통계"
])

# Tab 1: Real-time Monitoring
with tab1:
    st.header("실시간 사용자 상태")
    
    # 응급상황 경고 배너 (상단에 표시)
    emergency_banner = st.empty()
    
    col1, col2, col3, col4 = st.columns(4)
    
    try:
        # Get user settings
        user_settings_table = clients['dynamodb'].Table('SeniorCare-UserSettings')
        response = user_settings_table.get_item(Key={'userId': user_id})
        
        if 'Item' in response:
            user_data = response['Item']
            
            with col1:
                st.metric("사용자 이름", user_data.get('name', 'N/A'))
            
            with col2:
                last_activity = user_data.get('lastActivityTime', 'N/A')
                if last_activity != 'N/A':
                    last_activity_kst = to_kst(last_activity)
                    last_activity_dt = datetime.fromisoformat(last_activity.replace('Z', '+00:00'))
                    minutes_ago = int((datetime.now(KST) - last_activity_dt.astimezone(KST)).total_seconds() / 60)
                    st.metric("마지막 활동", f"{minutes_ago}분 전")
                    st.caption(f"{last_activity_kst} KST")
                else:
                    st.metric("마지막 활동", "N/A")
            
            with col3:
                threshold = user_data.get('inactivityThreshold', 120)
                st.metric("활동 부재 임계값", f"{threshold}분")
            
            with col4:
                status = user_data.get('status', 'unknown')
                if status == 'active':
                    status_color = "🟢"
                    status_text = "정상"
                elif status == 'emergency':
                    status_color = "🔴"
                    status_text = "응급상황"
                elif status == 'alert':
                    status_color = "🟠"
                    status_text = "경고"
                else:
                    status_color = "⚪"
                    status_text = status
                
                st.metric("상태", f"{status_color} {status_text}")
            
            # 응급상황일 때 상단 배너 경고 표시
            if status == 'emergency':
                emergency_banner.markdown("""
                <div style="background: linear-gradient(135deg, #f44336 0%, #e53935 100%); 
                            color: white; padding: 1.5rem; border-radius: 10px; 
                            margin-bottom: 1rem; text-align: center;
                            animation: pulse 1s infinite;">
                    <h2 style="margin: 0;">⚠️ 응급상황 발생! 즉시 확인 필요</h2>
                    <p style="margin: 0.5rem 0 0 0;">실시간 현황 대시보드(http://localhost:8505)에서 상세 정보를 확인하세요</p>
                </div>
                <style>
                    @keyframes pulse {
                        0%, 100% { opacity: 1; }
                        50% { opacity: 0.8; }
                    }
                </style>
                """, unsafe_allow_html=True)
                st.error("⚠️ 응급상황 발생! 즉시 확인 필요")
            
            # Activity timeline
            st.subheader("최근 활동 타임라인")
            
            try:
                sensor_data_table = clients['dynamodb'].Table('SeniorCare-SensorData')
                sensor_response = sensor_data_table.query(
                    KeyConditionExpression='userId = :uid',
                    ExpressionAttributeValues={':uid': user_id},
                    ScanIndexForward=False,
                    Limit=50
                )
                
                if sensor_response['Items']:
                    # Convert Decimal to float for pandas
                    items = []
                    for item in sensor_response['Items']:
                        converted_item = {}
                        for key, value in item.items():
                            if isinstance(value, Decimal):
                                converted_item[key] = float(value)
                            else:
                                converted_item[key] = value
                        items.append(converted_item)
                    
                    df = pd.DataFrame(items)
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
                    df = df.sort_values('timestamp')
                    
                    # Use deviceId if deviceType is not available
                    color_col = 'deviceType' if 'deviceType' in df.columns else 'deviceId'
                    
                    fig = px.scatter(df, x='timestamp', y='sensorType', 
                                   color=color_col, size='value',
                                   title='센서 활동 타임라인')
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("센서 데이터가 없습니다.")
            except Exception as timeline_error:
                st.error(f"타임라인 데이터 로드 오류: {str(timeline_error)}")
        else:
            st.warning(f"사용자 {user_id}를 찾을 수 없습니다.")
    
    except Exception as e:
        st.error(f"데이터 로드 오류: {str(e)}")

# Tab 2: Scenario Execution
with tab2:
    st.header("🎬 시나리오 실행")
    st.markdown("실시간 현황 대시보드(포트 8505)에서 워크플로우를 자동으로 실행합니다.")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 시나리오 선택")
        
        # 시나리오 선택 드롭다운
        scenario_options = {
            "fall_detection": "👵 김영희 75세 - 낙상 감지",
            "heat_inactivity": "👴 박철수 66세 - 폭염 활동부재"
        }
        
        selected_scenario = st.selectbox(
            "시나리오",
            options=list(scenario_options.keys()),
            format_func=lambda x: scenario_options[x],
            help="실행할 시나리오를 선택하세요"
        )
        
        # 시나리오별 설명
        if selected_scenario == "fall_detection":
            st.info("""
            **👵 김영희 75세 낙상 감지 시나리오**
            1. 📊 센서 데이터 수집 (정상 활동)
            2. 🚨 낙상 감지 (가속도 센서 이상)
            3. 🗣️ AI 스피커 음성 확인 (Polly)
            4. 📱 보호자 알림 발송 (SMS)
            5. ✅ 완료
            """)
            scenario_user_id = 'test-user-001'
        else:
            st.warning("""
            **👴 박철수 66세 폭염 활동부재 시나리오**
            1. 🌡️ 실내 온도 상승 감지 (35°C 이상)
            2. 🚶 모션 센서 움직임 없음
            3. 🚪 문 개폐 센서 닫힘 상태 유지
            4. ⌚ 웨어러블 활동량 저조
            5. 🗣️ AI 스피커 음성 확인 (Polly)
            6. 📱 보호자 알림 발송 (SMS)
            7. ✅ 완료
            """)
            scenario_user_id = 'test-user-002'
        
        voice_choice = st.selectbox(
            "음성 선택",
            options=["Seoyeon (여성, 부드러움)", "Jihye (여성, 밝음)"],
            help="AI 스피커 음성을 선택하세요"
        )
        selected_voice = "Seoyeon" if "Seoyeon" in voice_choice else "Jihye"
        
        if st.button("▶️ 시나리오 실행", type="primary", key="trigger_workflow"):
            try:
                import sys
                sys.path.insert(0, '.')
                from workflow_trigger import trigger_workflow, SCENARIOS
                
                # 박철수 사용자 데이터 확인 및 생성
                if selected_scenario == 'heat_inactivity':
                    user_settings_table = clients['dynamodb'].Table('SeniorCare-UserSettings')
                    try:
                        response = user_settings_table.get_item(Key={'userId': 'test-user-002'})
                        if 'Item' not in response:
                            # 박철수 사용자 데이터 생성
                            user_settings_table.put_item(Item={
                                'userId': 'test-user-002',
                                'name': '박철수',
                                'age': 66,
                                'status': 'active',
                                'inactivityThreshold': 60,
                                'voiceResponseTimeout': 30,
                                'guardianPhone': '010-3328-4472',
                                'guardianName': '보호자',
                                'guardianEmail': 'guardian@example.com',
                                'guardianRelation': '자녀',
                                'lastActivityTime': datetime.utcnow().isoformat() + 'Z'
                            })
                            st.info("✅ 박철수 사용자 데이터가 생성되었습니다.")
                    except Exception as e:
                        st.warning(f"사용자 데이터 확인 중 오류: {str(e)}")
                
                with st.spinner("워크플로우 트리거 중..."):
                    trigger_workflow(user_id=scenario_user_id, voice=selected_voice, scenario=selected_scenario)
                
                scenario_name = SCENARIOS[selected_scenario]['name']
                st.success(f"✅ '{scenario_name}' 워크플로우가 트리거되었습니다!")
                st.info("📊 실시간 현황 대시보드(http://localhost:8505)에서 진행 상황을 확인하세요.")
                
            except Exception as e:
                st.error(f"❌ 오류: {str(e)}")
                st.write("상세:", e)
    
    with col2:
        st.markdown("### 📊 실시간 현황")
        st.markdown("""
        실시간 현황 대시보드를 열려면:
        
        ```powershell
        cd dashboard
        .\\start_v3.ps1
        ```
        
        또는 브라우저에서:
        
        http://localhost:8505
        """)

# Tab 3: Send Sensor Data
with tab3:
    st.header("센서 데이터 전송 테스트")
    
    # 센서 타입 설명
    with st.expander("📖 센서 타입 설명", expanded=False):
        st.markdown("""
        ### 센서 타입별 용도
        
        **🚶 motion (동작 감지 센서)**
        - 실내에서 사람의 움직임을 감지
        - 거실, 침실, 화장실 등에 설치
        - 일정 시간 동안 움직임이 없으면 활동 부재로 판단
        
        **🚪 door (문 개폐 센서)**
        - 현관문, 방문, 화장실 문 등의 개폐 감지
        - 외출/귀가 패턴 파악
        - 화장실 사용 빈도 모니터링
        
        **📱 accelerometer (가속도 센서)**
        - 스마트폰이나 웨어러블 기기에 내장
        - 걸음 수, 활동량 측정
        - 낙상 감지 (급격한 가속도 변화)
        
        **🌡️ temperature (온도 센서)**
        - 실내 온도 모니터링
        - 여름철 폭염, 겨울철 저체온증 예방
        - 난방/냉방 기기 작동 여부 확인
        """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        device_id = st.text_input("디바이스 ID", value="device-001")
        device_type = st.selectbox("디바이스 타입", ["mobile", "iot"])
        sensor_type = st.selectbox("센서 타입", 
                                   ["motion", "door", "accelerometer", "temperature"],
                                   help="센서 타입 설명은 위의 '📖 센서 타입 설명'을 참고하세요")
    
    with col2:
        sensor_value = st.number_input("센서 값", value=1.5, step=0.1)
        timestamp = st.text_input("타임스탬프", 
                                 value=datetime.utcnow().isoformat())
    
    if st.button("센서 데이터 전송", type="primary"):
        try:
            # DynamoDB에 직접 저장
            sensor_data_table = clients['dynamodb'].Table('SeniorCare-SensorData')
            
            # 타임스탬프를 Unix timestamp로 변환
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    unix_timestamp = int(dt.timestamp())
                except:
                    unix_timestamp = int(datetime.utcnow().timestamp())
            else:
                unix_timestamp = int(datetime.utcnow().timestamp())
            
            item = {
                'userId': user_id,
                'timestamp': unix_timestamp,
                'deviceId': device_id,
                'deviceType': device_type,
                'sensorType': sensor_type,
                'value': Decimal(str(sensor_value))
            }
            
            sensor_data_table.put_item(Item=item)
            
            # 사용자 설정의 lastActivityTime 업데이트
            user_settings_table = clients['dynamodb'].Table('SeniorCare-UserSettings')
            user_settings_table.update_item(
                Key={'userId': user_id},
                UpdateExpression='SET lastActivityTime = :lat',
                ExpressionAttributeValues={
                    ':lat': datetime.utcnow().isoformat() + 'Z'
                }
            )
            
            st.success("✅ 센서 데이터가 성공적으로 전송되었습니다!")
            st.json({
                'userId': user_id,
                'timestamp': unix_timestamp,
                'deviceId': device_id,
                'sensorType': sensor_type,
                'value': float(sensor_value)
            })
        
        except Exception as e:
            st.error(f"오류 발생: {str(e)}")
            st.write("상세 오류:", e)

# Tab 4: Alert History
with tab4:
    st.header("알림 이력")
    
    try:
        alert_history_table = clients['dynamodb'].Table('SeniorCare-AlertHistory')
        alert_response = alert_history_table.query(
            KeyConditionExpression='userId = :uid',
            ExpressionAttributeValues={':uid': user_id},
            ScanIndexForward=False,
            Limit=20
        )
        
        if alert_response['Items']:
            alerts_df = pd.DataFrame(alert_response['Items'])
            
            # Display alerts
            for _, alert in alerts_df.iterrows():
                status = alert.get('status', 'unknown')
                alert_type = alert.get('alertType', 'unknown')
                created_at = alert.get('createdAt', 'N/A')
                created_at_kst = to_kst(created_at) if created_at != 'N/A' else 'N/A'
                
                status_emoji = {
                    'voice_confirmation_pending': '⏳',
                    'confirmed_safe': '✅',
                    'no_response': '⚠️',
                    'resolved': '✔️'
                }.get(status, '❓')
                
                with st.expander(f"{status_emoji} {alert_type} - {created_at_kst} KST"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Alert ID:** {alert.get('alertId', 'N/A')}")
                        st.write(f"**상태:** {status}")
                        st.write(f"**유형:** {alert_type}")
                    with col2:
                        st.write(f"**생성 시간:** {created_at}")
                        st.write(f"**마지막 활동:** {alert.get('lastActivityTime', 'N/A')}")
                        st.write(f"**재시도 횟수:** {alert.get('retryCount', 0)}")
        else:
            st.info("알림 이력이 없습니다.")
    
    except Exception as e:
        st.error(f"알림 이력 로드 오류: {str(e)}")

# Tab 5: Settings Management
with tab5:
    st.header("사용자 설정 관리")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("활동 부재 임계값")
        new_threshold = st.slider("임계값 (분)", 30, 480, 120, 10)
        
        if st.button("임계값 업데이트"):
            try:
                payload = {
                    'userId': user_id,
                    'action': 'update_settings',
                    'inactivityThreshold': new_threshold
                }
                
                response = clients['lambda'].invoke(
                    FunctionName='SeniorCare-SettingsManager',
                    InvocationType='RequestResponse',
                    Payload=json.dumps(payload)
                )
                
                result = json.loads(response['Payload'].read())
                
                if result.get('statusCode') == 200:
                    st.success("✅ 임계값이 업데이트되었습니다!")
                else:
                    st.error(f"❌ 업데이트 실패: {result}")
            
            except Exception as e:
                st.error(f"오류 발생: {str(e)}")
    
    with col2:
        st.subheader("음성 응답 타임아웃")
        new_timeout = st.slider("타임아웃 (초)", 10, 60, 30, 5)
        
        if st.button("타임아웃 업데이트"):
            try:
                payload = {
                    'userId': user_id,
                    'action': 'update_settings',
                    'voiceResponseTimeout': new_timeout
                }
                
                response = clients['lambda'].invoke(
                    FunctionName='SeniorCare-SettingsManager',
                    InvocationType='RequestResponse',
                    Payload=json.dumps(payload)
                )
                
                result = json.loads(response['Payload'].read())
                
                if result.get('statusCode') == 200:
                    st.success("✅ 타임아웃이 업데이트되었습니다!")
                else:
                    st.error(f"❌ 업데이트 실패: {result}")
            
            except Exception as e:
                st.error(f"오류 발생: {str(e)}")
    
    # 보호자 연락처 설정
    st.markdown("---")
    st.subheader("📞 보호자 연락처 설정")
    
    col1, col2 = st.columns(2)
    
    with col1:
        guardian_phone = st.text_input(
            "보호자 휴대폰 번호",
            value="010-3328-4472",
            help="긴급 알림을 받을 보호자의 휴대폰 번호"
        )
        
        guardian_name = st.text_input(
            "보호자 이름",
            value="보호자",
            help="보호자의 이름"
        )
    
    with col2:
        guardian_email = st.text_input(
            "보호자 이메일",
            value="guardian@example.com",
            help="상세 리포트를 받을 이메일 주소"
        )
        
        guardian_relation = st.selectbox(
            "관계",
            options=["자녀", "배우자", "형제/자매", "친척", "기타"],
            help="사용자와의 관계"
        )
    
    if st.button("📞 보호자 연락처 저장", type="primary"):
        try:
            # DynamoDB에 직접 저장
            user_settings_table = clients['dynamodb'].Table('SeniorCare-UserSettings')
            
            user_settings_table.update_item(
                Key={'userId': user_id},
                UpdateExpression='SET guardianPhone = :phone, guardianName = :name, guardianEmail = :email, guardianRelation = :relation',
                ExpressionAttributeValues={
                    ':phone': guardian_phone,
                    ':name': guardian_name,
                    ':email': guardian_email,
                    ':relation': guardian_relation
                }
            )
            
            st.success("✅ 보호자 연락처가 저장되었습니다!")
            st.info(f"📱 SMS 알림: {guardian_phone}")
            st.info(f"📧 이메일 알림: {guardian_email}")
            
        except Exception as e:
            st.error(f"오류 발생: {str(e)}")
            st.write("상세 오류:", e)
    
    # 현재 설정 확인
    st.markdown("---")
    st.subheader("📋 현재 설정")
    
    try:
        user_settings_table = clients['dynamodb'].Table('SeniorCare-UserSettings')
        response = user_settings_table.get_item(Key={'userId': user_id})
        
        if 'Item' in response:
            settings = response['Item']
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**사용자 정보**")
                st.write(f"- 이름: {settings.get('name', 'N/A')}")
                st.write(f"- 나이: {settings.get('age', 'N/A')}세")
                st.write(f"- 상태: {settings.get('status', 'N/A')}")
                st.write(f"- 활동 부재 임계값: {settings.get('inactivityThreshold', 'N/A')}분")
                st.write(f"- 음성 응답 타임아웃: {settings.get('voiceResponseTimeout', 'N/A')}초")
            
            with col2:
                st.write("**보호자 정보**")
                st.write(f"- 이름: {settings.get('guardianName', '미설정')}")
                st.write(f"- 관계: {settings.get('guardianRelation', '미설정')}")
                st.write(f"- 휴대폰: {settings.get('guardianPhone', '미설정')}")
                st.write(f"- 이메일: {settings.get('guardianEmail', '미설정')}")
        else:
            st.warning("사용자 설정을 찾을 수 없습니다.")
    
    except Exception as e:
        st.error(f"설정 로드 오류: {str(e)}")

# Tab 6: Statistics
with tab6:
    st.header("통계 및 분석")
    
    try:
        # Get sensor data for statistics
        sensor_data_table = clients['dynamodb'].Table('SeniorCare-SensorData')
        
        # Get all data for the user (without time filter first)
        sensor_response = sensor_data_table.query(
            KeyConditionExpression='userId = :uid',
            ExpressionAttributeValues={':uid': user_id},
            ScanIndexForward=False,
            Limit=200
        )
        
        if sensor_response['Items']:
            # Convert Decimal to float for pandas
            items = []
            for item in sensor_response['Items']:
                converted_item = {}
                for key, value in item.items():
                    if isinstance(value, Decimal):
                        converted_item[key] = float(value)
                    else:
                        converted_item[key] = value
                items.append(converted_item)
            
            df = pd.DataFrame(items)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
            
            # Filter last 24 hours
            last_24h = datetime.utcnow() - timedelta(days=1)
            df_24h = df[df['timestamp'] >= last_24h]
            
            if len(df_24h) > 0:
                df_24h['hour'] = df_24h['timestamp'].dt.hour
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Hourly activity distribution
                    hourly_counts = df_24h.groupby('hour').size().reset_index(name='count')
                    fig1 = px.bar(hourly_counts, x='hour', y='count',
                                title='시간대별 활동 분포 (24시간)',
                                labels={'hour': '시간', 'count': '활동 횟수'})
                    st.plotly_chart(fig1, use_container_width=True)
                
                with col2:
                    # Sensor type distribution
                    sensor_counts = df_24h.groupby('sensorType').size().reset_index(name='count')
                    fig2 = px.pie(sensor_counts, values='count', names='sensorType',
                                title='센서 타입별 분포')
                    st.plotly_chart(fig2, use_container_width=True)
                
                # Activity timeline
                st.subheader("24시간 활동 타임라인")
                fig3 = px.line(df_24h, x='timestamp', y='value', color='sensorType',
                              title='센서 값 변화')
                st.plotly_chart(fig3, use_container_width=True)
                
                # Summary metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("총 활동 횟수", len(df_24h))
                with col2:
                    st.metric("활성 센서 수", df_24h['sensorType'].nunique())
                with col3:
                    st.metric("활성 디바이스 수", df_24h['deviceId'].nunique())
            else:
                st.info("지난 24시간 동안 센서 데이터가 없습니다.")
        else:
            st.info("센서 데이터가 없습니다.")
    
    except Exception as e:
        st.error(f"통계 로드 오류: {str(e)}")
        st.write("상세 오류:", e)

# Auto-refresh
if st.sidebar.checkbox("자동 새로고침", value=False):
    import time
    time.sleep(refresh_interval)
    st.rerun()
