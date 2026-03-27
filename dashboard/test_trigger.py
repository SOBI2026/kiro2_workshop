"""
트리거 테스트 스크립트
개발자 대시보드에서 트리거가 제대로 생성되는지 확인
"""
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
trigger_table = dynamodb.Table('SeniorCare-WorkflowTrigger')

def check_trigger():
    """현재 트리거 상태 확인"""
    try:
        response = trigger_table.get_item(
            Key={'userId': 'test-user-001', 'triggerId': 'latest'}
        )
        item = response.get('Item')
        if item:
            print(f"✅ 트리거 발견:")
            print(f"   - 상태: {item.get('status')}")
            print(f"   - 음성: {item.get('voice')}")
            print(f"   - 생성 시간: {item.get('triggeredAt')}")
            print(f"   - 생성자: {item.get('triggeredBy')}")
            return item
        else:
            print("❌ 트리거 없음")
            return None
    except Exception as e:
        print(f"❌ 오류: {e}")
        return None

def create_test_trigger(voice='Seoyeon'):
    """테스트 트리거 생성"""
    try:
        trigger_table.put_item(Item={
            'userId': 'test-user-001',
            'triggerId': 'latest',
            'status': 'pending',
            'voice': voice,
            'triggeredAt': datetime.utcnow().isoformat(),
            'triggeredBy': 'test-script'
        })
        print(f"✅ 테스트 트리거 생성 완료 (음성: {voice})")
        return True
    except Exception as e:
        print(f"❌ 오류: {e}")
        return False

def reset_trigger():
    """트리거 상태 초기화 (completed로 변경)"""
    try:
        trigger_table.update_item(
            Key={'userId': 'test-user-001', 'triggerId': 'latest'},
            UpdateExpression='SET #status = :status',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={':status': 'completed'}
        )
        print("✅ 트리거 상태 초기화 완료 (completed)")
        return True
    except Exception as e:
        print(f"❌ 오류: {e}")
        return False

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == 'check':
            check_trigger()
        elif cmd == 'create':
            voice = sys.argv[2] if len(sys.argv) > 2 else 'Seoyeon'
            create_test_trigger(voice)
        elif cmd == 'reset':
            reset_trigger()
        else:
            print("사용법: python test_trigger.py [check|create|reset]")
    else:
        print("=== 트리거 상태 확인 ===")
        check_trigger()
