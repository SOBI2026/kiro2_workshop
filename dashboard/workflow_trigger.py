"""
워크플로우 트리거 헬퍼 함수
개발자 대시보드와 실시간 현황 대시보드 간 상태 공유
"""
import boto3
from datetime import datetime
from decimal import Decimal

# 시나리오 정의
SCENARIOS = {
    'fall_detection': {
        'name': '김영희 75세 낙상 감지',
        'user_id': 'test-user-001',
        'user_name': '김영희',
        'user_age': 75,
        'description': '화장실에서 낙상 발생 → 음성 확인 → 보호자 알림'
    },
    'heat_inactivity': {
        'name': '박철수 66세 폭염 활동부재',
        'user_id': 'test-user-002',
        'user_name': '박철수',
        'user_age': 66,
        'description': '폭염으로 실내 온도 상승 → 활동 부재 감지 → 보호자 알림'
    }
}

def trigger_workflow(user_id='test-user-001', voice='Seoyeon', scenario='fall_detection'):
    """워크플로우 실행 트리거"""
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    trigger_table = dynamodb.Table('SeniorCare-WorkflowTrigger')
    
    # 시나리오 정보 가져오기
    scenario_info = SCENARIOS.get(scenario, SCENARIOS['fall_detection'])
    
    trigger_table.put_item(Item={
        'userId': user_id,
        'triggerId': 'latest',
        'status': 'pending',
        'voice': voice,
        'scenario': scenario,
        'scenarioName': scenario_info['name'],
        'userName': scenario_info['user_name'],
        'userAge': scenario_info['user_age'],
        'triggeredAt': datetime.utcnow().isoformat(),
        'triggeredBy': 'developer-dashboard'
    })
    
    return True

def get_workflow_status(user_id='test-user-001'):
    """워크플로우 상태 확인"""
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    trigger_table = dynamodb.Table('SeniorCare-WorkflowTrigger')
    
    try:
        response = trigger_table.get_item(Key={
            'userId': user_id,
            'triggerId': 'latest'
        })
        return response.get('Item', {})
    except:
        return {}

def update_workflow_status(user_id='test-user-001', status='running', current_step=0):
    """워크플로우 상태 업데이트"""
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    trigger_table = dynamodb.Table('SeniorCare-WorkflowTrigger')
    
    trigger_table.update_item(
        Key={'userId': user_id, 'triggerId': 'latest'},
        UpdateExpression='SET #status = :status, currentStep = :step, updatedAt = :updated',
        ExpressionAttributeNames={'#status': 'status'},
        ExpressionAttributeValues={
            ':status': status,
            ':step': current_step,
            ':updated': datetime.utcnow().isoformat()
        }
    )
    
    return True

def clear_workflow_trigger(user_id='test-user-001'):
    """워크플로우 트리거 초기화"""
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    trigger_table = dynamodb.Table('SeniorCare-WorkflowTrigger')
    
    trigger_table.update_item(
        Key={'userId': user_id, 'triggerId': 'latest'},
        UpdateExpression='SET #status = :status',
        ExpressionAttributeNames={'#status': 'status'},
        ExpressionAttributeValues={':status': 'completed'}
    )
    
    return True
