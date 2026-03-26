# Run Streamlit Dashboard for Senior Care Monitoring

Write-Host "=== 시니어 안심 케어 모니터링 대시보드 ===" -ForegroundColor Green

# Check if virtual environment exists
if (-not (Test-Path "dashboard\venv")) {
    Write-Host "`n가상환경 생성 중..." -ForegroundColor Yellow
    python -m venv dashboard\venv
}

# Activate virtual environment
Write-Host "`n가상환경 활성화 중..." -ForegroundColor Yellow
& "dashboard\venv\Scripts\Activate.ps1"

# Install dependencies
Write-Host "`n의존성 설치 중..." -ForegroundColor Yellow
pip install -r dashboard\requirements.txt -q

# Set AWS credentials (if not already set)
if (-not $env:AWS_ACCESS_KEY_ID) {
    Write-Host "`n경고: AWS 자격증명이 설정되지 않았습니다." -ForegroundColor Red
    Write-Host "다음 명령으로 설정하세요:" -ForegroundColor Yellow
    Write-Host '$env:AWS_ACCESS_KEY_ID="your-key"' -ForegroundColor Cyan
    Write-Host '$env:AWS_SECRET_ACCESS_KEY="your-secret"' -ForegroundColor Cyan
    Write-Host '$env:AWS_SESSION_TOKEN="your-token"' -ForegroundColor Cyan
}

# Run Streamlit
Write-Host "`nStreamlit 대시보드 시작 중..." -ForegroundColor Green
streamlit run dashboard\app.py
