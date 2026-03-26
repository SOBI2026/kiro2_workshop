# Set AWS credentials for Senior Care Monitoring System

param(
    [Parameter(Mandatory=$true)]
    [string]$AccessKeyId,
    
    [Parameter(Mandatory=$true)]
    [string]$SecretAccessKey,
    
    [Parameter(Mandatory=$false)]
    [string]$SessionToken,
    
    [Parameter(Mandatory=$false)]
    [string]$Region = "us-east-1"
)

Write-Host "Setting AWS credentials..." -ForegroundColor Yellow

$env:AWS_DEFAULT_REGION = $Region
$env:AWS_ACCESS_KEY_ID = $AccessKeyId
$env:AWS_SECRET_ACCESS_KEY = $SecretAccessKey

if ($SessionToken) {
    $env:AWS_SESSION_TOKEN = $SessionToken
}

# Verify credentials
Write-Host "`nVerifying credentials..." -ForegroundColor Yellow
aws sts get-caller-identity

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nCredentials configured successfully!" -ForegroundColor Green
} else {
    Write-Host "`nError: Failed to verify credentials" -ForegroundColor Red
}
