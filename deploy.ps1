# Senior Care Monitoring System - Deployment Script

Write-Host "=== Senior Care Monitoring System Deployment ===" -ForegroundColor Green

# Check AWS credentials
Write-Host "`nChecking AWS credentials..." -ForegroundColor Yellow
aws sts get-caller-identity
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: AWS credentials not configured" -ForegroundColor Red
    exit 1
}

# Create S3 bucket for SAM artifacts
$STACK_NAME = "senior-care-monitoring"
$REGION = "us-east-1"
$ACCOUNT_ID = (aws sts get-caller-identity --query Account --output text)
$SAM_BUCKET = "sam-artifacts-$ACCOUNT_ID-$REGION"

Write-Host "`nCreating SAM artifacts bucket: $SAM_BUCKET" -ForegroundColor Yellow
aws s3 mb s3://$SAM_BUCKET --region $REGION 2>$null

# Package Lambda functions
Write-Host "`nPackaging Lambda functions..." -ForegroundColor Yellow
aws cloudformation package `
    --template-file template.yaml `
    --s3-bucket $SAM_BUCKET `
    --output-template-file packaged.yaml `
    --region $REGION

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to package template" -ForegroundColor Red
    exit 1
}

# Deploy stack
Write-Host "`nDeploying CloudFormation stack..." -ForegroundColor Yellow
aws cloudformation deploy `
    --template-file packaged.yaml `
    --stack-name $STACK_NAME `
    --capabilities CAPABILITY_IAM `
    --region $REGION `
    --parameter-overrides `
        Environment=dev

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to deploy stack" -ForegroundColor Red
    exit 1
}

# Get stack outputs
Write-Host "`nStack outputs:" -ForegroundColor Green
aws cloudformation describe-stacks `
    --stack-name $STACK_NAME `
    --query 'Stacks[0].Outputs' `
    --output table `
    --region $REGION

Write-Host "`nDeployment complete!" -ForegroundColor Green
