$env:PYTHONIOENCODING="utf-8"
$env:AWS_DEFAULT_REGION="us-east-1"
$env:AWS_ACCESS_KEY_ID="ASIARNU6IL25ONWEARER"
$env:AWS_SECRET_ACCESS_KEY="5hZBTQ5ITnnpYpo5p3Jo7ZEVcyegTV0Fb2UsBnRu"
$env:AWS_SESSION_TOKEN="IQoJb3JpZ2luX2VjEA4aCXVzLWVhc3QtMSJHMEUCIQDKBflsDI3cHKzMJi/tzWUWa58uPuphOlBpsb1js6q1ZAIgWi5OWp9dMVsbU7xYN0pMnkuCYP0ZLglfaK0HzaRL7HoqogII1v//////////ARAAGgwwOTgwNDI0MDQ1MzgiDHuoa2/+xbHybAQshCr2ASAPvLmbmoPvBQNAgC6bTUKyh1kElpEeWFI51qvXqYLSJx6p2XnZvzCaBIX7IqNeLUUbu4rakmyfRwPJFMN7i3nCU/M12yEb4RuLKijt7eRwlWFTJapn2RkDYEIXFlG2GHZWXv/SoYt5hTwiIXzhHy+mL5i4VfaequSrUFOQwr12hNjhSha3WFkTVvMDH444YQ9rhc4Gw+r+J/RhXloTOoJM/sCuxTtMM1f2+1pMxgbmsFH8EfZ0xp7OmcJy8peZ6KjWih85a5zXrWE7c/YsdQljC+0rSQq7mGrbLVAsjSvXmnCUoDBoY2SlOBy59U12hs6ytZ8tlzCno5jOBjqdAWB3pWXS7JyIalDpW4wMPEmq81H+X/Rz9YZ3LYz6v/DTvmcaxLxn4K0xhyvQs7ApO/wEafsHSKksTYfhGF/QKtgLPW7ZJYJZo0NE1/2UTN2RD8ixDQQXD4ECzHeGSy9uTO5n7LmjIUKPr8DBrEHFeHhX1VbPiD2F/jRopSL99j7zyhioGrHl7algQdVnjT30wDpFm5PMuMWJwYtu9JI="

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  개발자 모니터링 대시보드" -ForegroundColor Yellow
Write-Host "  시니어 안심 케어 - 백엔드 관리" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "URL: " -NoNewline
Write-Host "http://localhost:8503" -ForegroundColor Green
Write-Host ""
Write-Host "주요 기능:" -ForegroundColor Cyan
Write-Host "  ✅ 실시간 사용자 상태 모니터링"
Write-Host "  ✅ 보호자 연락처 설정"
Write-Host "  ✅ 센서 데이터 전송 (테스트)"
Write-Host "  ✅ 알림 이력 조회"
Write-Host "  ✅ 통계 및 분석"
Write-Host ""
Write-Host "시작 중..." -ForegroundColor Yellow
Write-Host ""

Set-Location $PSScriptRoot
& ..\.venv\Scripts\python.exe -m streamlit run app.py --server.port 8503
