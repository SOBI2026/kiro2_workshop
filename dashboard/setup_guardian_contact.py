import boto3

print("=" * 70)
print("📞 보호자 연락처 설정")
print("=" * 70)

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
user_settings_table = dynamodb.Table('SeniorCare-UserSettings')

user_id = 'test-user-001'

# 보호자 연락처 정보
guardian_info = {
    'guardianName': '보호자',
    'guardianPhone': '010-3328-4472',
    'guardianEmail': 'guardian@example.com',
    'guardianRelation': '자녀'
}

print("\n보호자 정보:")
print(f"  - 이름: {guardian_info['guardianName']}")
print(f"  - 관계: {guardian_info['guardianRelation']}")
print(f"  - 휴대폰: {guardian_info['guardianPhone']}")
print(f"  - 이메일: {guardian_info['guardianEmail']}")

try:
    user_settings_table.update_item(
        Key={'userId': user_id},
        UpdateExpression='SET guardianPhone = :phone, guardianName = :name, guardianEmail = :email, guardianRelation = :relation',
        ExpressionAttributeValues={
            ':phone': guardian_info['guardianPhone'],
            ':name': guardian_info['guardianName'],
            ':email': guardian_info['guardianEmail'],
            ':relation': guardian_info['guardianRelation']
        }
    )
    
    print("\n✅ 보호자 연락처가 DynamoDB에 저장되었습니다!")
    
    # 확인
    response = user_settings_table.get_item(Key={'userId': user_id})
    if 'Item' in response:
        item = response['Item']
        print("\n📋 저장된 정보 확인:")
        print(f"  - 사용자: {item.get('name', 'N/A')} ({item.get('age', 'N/A')}세)")
        print(f"  - 보호자: {item.get('guardianName', 'N/A')} ({item.get('guardianRelation', 'N/A')})")
        print(f"  - 연락처: {item.get('guardianPhone', 'N/A')}")
        print(f"  - 이메일: {item.get('guardianEmail', 'N/A')}")

except Exception as e:
    print(f"\n❌ 오류 발생: {str(e)}")

print("\n" + "=" * 70)
print("💡 이제 대시보드 3에서 자동 실행 시 실제 SMS가 발송됩니다!")
print("   URL: http://localhost:8505")
print("=" * 70)
