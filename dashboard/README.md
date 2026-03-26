# 시니어 안심 케어 모니터링 대시보드

Streamlit 기반 실시간 모니터링 대시보드

## 설치

```bash
pip install -r requirements.txt
```

## 실행

```bash
streamlit run app.py
```

## 기능

### 1. 📊 실시간 모니터링
- 사용자 상태 실시간 확인
- 마지막 활동 시간 표시
- 센서 활동 타임라인 시각화

### 2. 📱 센서 데이터 전송
- 테스트용 센서 데이터 전송
- 다양한 센서 타입 지원 (가속도계, 모션, 도어, 온도)
- 실시간 응답 확인

### 3. 🔔 알림 이력
- 모든 알림 이력 조회
- 알림 상태별 필터링
- 상세 정보 확인

### 4. ⚙️ 설정 관리
- 활동 부재 임계값 조정 (30-480분)
- 음성 응답 타임아웃 조정 (10-60초)
- 실시간 설정 업데이트

### 5. 📈 통계
- 시간대별 활동 분포
- 센서 타입별 통계
- 24시간 활동 타임라인

## AWS 자격증명 설정

대시보드 실행 전 AWS 자격증명을 설정하세요:

```powershell
$env:AWS_DEFAULT_REGION="us-east-1"
$env:AWS_ACCESS_KEY_ID="your-access-key"
$env:AWS_SECRET_ACCESS_KEY="your-secret-key"
$env:AWS_SESSION_TOKEN="your-session-token"  # 임시 자격증명 사용 시
```

또는 AWS CLI 프로필 사용:

```bash
export AWS_PROFILE=your-profile-name
```
