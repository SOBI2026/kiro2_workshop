"""
워크플로우 트리거 테이블 생성
"""
import boto3

print("=" * 60)
print("워크플로우 트리거 테이블 생성")
print("=" * 60)
print()

try:
    dynamodb = boto3.client('dynamodb', region_name='us-east-1')
    
    # 테이블 생성
    table_name = 'SeniorCare-WorkflowTrigger'
    
    print(f"📊 테이블 생성 중: {table_name}")
    
    response = dynamodb.create_table(
        TableName=table_name,
        KeySchema=[
            {'AttributeName': 'userId', 'KeyType': 'HASH'},
            {'AttributeName': 'triggerId', 'KeyType': 'RANGE'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'userId', 'AttributeType': 'S'},
            {'AttributeName': 'triggerId', 'AttributeType': 'S'}
        ],
        BillingMode='PAY_PER_REQUEST'
    )
    
    print("✅ 테이블 생성 요청 완료!")
    print(f"   상태: {response['TableDescription']['TableStatus']}")
    print()
    print("⏳ 테이블이 활성화될 때까지 기다리는 중...")
    
    # 테이블 활성화 대기
    waiter = dynamodb.get_waiter('table_exists')
    waiter.wait(TableName=table_name)
    
    print("✅ 테이블 활성화 완료!")
    print()
    
except dynamodb.exceptions.ResourceInUseException:
    print("ℹ️ 테이블이 이미 존재합니다.")
    print()
    
except Exception as e:
    print(f"❌ 오류: {str(e)}")
    print()

print("=" * 60)
