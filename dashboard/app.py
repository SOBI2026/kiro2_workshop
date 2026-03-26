import streamlit as st
import boto3
import json
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

# Page configuration
st.set_page_config(
    page_title="시니어 안심 케어 모니터링",
    page_icon="🏥",
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
st.title("🏥 시니어 안심 케어 모니터링 대시보드")

# Sidebar
st.sidebar.header("설정")
user_id = st.sidebar.text_input("사용자 ID", value="test-user-001")
refresh_interval = st.sidebar.slider("새로고침 간격 (초)", 5, 60, 10)

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 실시간 모니터링", 
    "📱 센서 데이터 전송", 
    "🔔 알림 이력", 
    "⚙️ 설정 관리",
    "📈 통계"
])

# Tab 1: Real-time Monitoring
with tab1:
    st.header("실시간 사용자 상태")
    
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
                    last_activity_dt = datetime.fromisoformat(last_activity.replace('Z', '+00:00'))
                    minutes_ago = int((datetime.utcnow() - last_activity_dt.replace(tzinfo=None)).total_seconds() / 60)
                    st.metric("마지막 활동", f"{minutes_ago}분 전")
                else:
                    st.metric("마지막 활동", "N/A")
            
            with col3:
                threshold = user_data.get('inactivityThreshold', 120)
                st.metric("활동 부재 임계값", f"{threshold}분")
            
            with col4:
                status = user_data.get('status', 'unknown')
                status_color = "🟢" if status == 'active' else "🔴"
                st.metric("상태", f"{status_color} {status}")
            
            # Activity timeline
            st.subheader("최근 활동 타임라인")
            
            sensor_data_table = clients['dynamodb'].Table('SeniorCare-SensorData')
            sensor_response = sensor_data_table.query(
                KeyConditionExpression='userId = :uid',
                ExpressionAttributeValues={':uid': user_id},
                ScanIndexForward=False,
                Limit=50
            )
            
            if sensor_response['Items']:
                df = pd.DataFrame(sensor_response['Items'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
                df = df.sort_values('timestamp')
                
                fig = px.scatter(df, x='timestamp', y='sensorType', 
                               color='deviceType', size='value',
                               title='센서 활동 타임라인')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("센서 데이터가 없습니다.")
        else:
            st.warning(f"사용자 {user_id}를 찾을 수 없습니다.")
    
    except Exception as e:
        st.error(f"데이터 로드 오류: {str(e)}")

# Tab 2: Send Sensor Data
with tab2:
    st.header("센서 데이터 전송 테스트")
    
    col1, col2 = st.columns(2)
    
    with col1:
        device_id = st.text_input("디바이스 ID", value="device-001")
        device_type = st.selectbox("디바이스 타입", ["mobile", "iot"])
        sensor_type = st.selectbox("센서 타입", 
                                   ["accelerometer", "motion", "door", "temperature"])
    
    with col2:
        sensor_value = st.number_input("센서 값", value=1.5, step=0.1)
        timestamp = st.text_input("타임스탬프", 
                                 value=datetime.utcnow().isoformat())
    
    if st.button("센서 데이터 전송", type="primary"):
        try:
            payload = {
                'userId': user_id,
                'deviceId': device_id,
                'deviceType': device_type,
                'sensorType': sensor_type,
                'value': sensor_value,
                'timestamp': timestamp
            }
            
            response = clients['lambda'].invoke(
                FunctionName='SeniorCare-SensorDataProcessor',
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            
            result = json.loads(response['Payload'].read())
            
            if result.get('statusCode') == 200:
                st.success("✅ 센서 데이터가 성공적으로 전송되었습니다!")
                st.json(result)
            else:
                st.error(f"❌ 전송 실패: {result}")
        
        except Exception as e:
            st.error(f"오류 발생: {str(e)}")

# Tab 3: Alert History
with tab3:
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
                
                status_emoji = {
                    'voice_confirmation_pending': '⏳',
                    'confirmed_safe': '✅',
                    'no_response': '⚠️',
                    'resolved': '✔️'
                }.get(status, '❓')
                
                with st.expander(f"{status_emoji} {alert_type} - {created_at}"):
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

# Tab 4: Settings Management
with tab4:
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

# Tab 5: Statistics
with tab5:
    st.header("통계 및 분석")
    
    try:
        # Get sensor data for statistics
        sensor_data_table = clients['dynamodb'].Table('SeniorCare-SensorData')
        
        # Last 24 hours
        start_time = int((datetime.utcnow() - timedelta(days=1)).timestamp())
        
        sensor_response = sensor_data_table.query(
            KeyConditionExpression='userId = :uid AND #ts >= :start',
            ExpressionAttributeNames={'#ts': 'timestamp'},
            ExpressionAttributeValues={
                ':uid': user_id,
                ':start': start_time
            }
        )
        
        if sensor_response['Items']:
            df = pd.DataFrame(sensor_response['Items'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
            df['hour'] = df['timestamp'].dt.hour
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Hourly activity distribution
                hourly_counts = df.groupby('hour').size().reset_index(name='count')
                fig1 = px.bar(hourly_counts, x='hour', y='count',
                            title='시간대별 활동 분포',
                            labels={'hour': '시간', 'count': '활동 횟수'})
                st.plotly_chart(fig1, use_container_width=True)
            
            with col2:
                # Sensor type distribution
                sensor_counts = df.groupby('sensorType').size().reset_index(name='count')
                fig2 = px.pie(sensor_counts, values='count', names='sensorType',
                            title='센서 타입별 분포')
                st.plotly_chart(fig2, use_container_width=True)
            
            # Activity timeline
            st.subheader("24시간 활동 타임라인")
            fig3 = px.line(df, x='timestamp', y='value', color='sensorType',
                          title='센서 값 변화')
            st.plotly_chart(fig3, use_container_width=True)
            
            # Summary metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("총 활동 횟수", len(df))
            with col2:
                st.metric("활성 센서 수", df['sensorType'].nunique())
            with col3:
                st.metric("활성 디바이스 수", df['deviceId'].nunique())
        else:
            st.info("지난 24시간 동안 센서 데이터가 없습니다.")
    
    except Exception as e:
        st.error(f"통계 로드 오류: {str(e)}")

# Auto-refresh
if st.sidebar.checkbox("자동 새로고침", value=False):
    import time
    time.sleep(refresh_interval)
    st.rerun()
