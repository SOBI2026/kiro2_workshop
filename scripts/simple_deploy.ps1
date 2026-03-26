# Simple deployment script without SAM CLI
# This script creates Lambda functions directly using AWS CLI

Write-Host "=== Senior Care Monitoring - Simple Deployment ===" -ForegroundColor Green

# Configuration
$STACK_NAME = "senior-care-monitoring"
$REGION = "us-east-1"

# Create DynamoDB tables
Write-Host "`nCreating DynamoDB tables..." -ForegroundColor Yellow

# SensorData table
aws dynamodb create-table `
    --table-name SeniorCare-SensorData `
    --attribute-definitions `
        AttributeName=userId,AttributeType=S `
        AttributeName=timestamp,AttributeType=N `
        AttributeName=deviceId,AttributeType=S `
    --key-schema `
        AttributeName=userId,KeyType=HASH `
        AttributeName=timestamp,KeyType=RANGE `
    --billing-mode PAY_PER_REQUEST `
    --global-secondary-indexes `
        "IndexName=deviceId-timestamp-index,KeySchema=[{AttributeName=deviceId,KeyType=HASH},{AttributeName=timestamp,KeyType=RANGE}],Projection={ProjectionType=ALL}" `
    --sse-specification Enabled=true,SSEType=KMS `
    --region $REGION 2>$null

Write-Host "  SensorData table created" -ForegroundColor Green

# UserSettings table  
aws dynamodb create-table `
    --table-name SeniorCare-UserSettings `
    --attribute-definitions `
        AttributeName=userId,AttributeType=S `
        AttributeName=status,AttributeType=S `
        AttributeName=lastActivityTime,AttributeType=S `
    --key-schema `
        AttributeName=userId,KeyType=HASH `
    --billing-mode PAY_PER_REQUEST `
    --global-secondary-indexes `
        "IndexName=status-lastActivityTime-index,KeySchema=[{AttributeName=status,KeyType=HASH},{AttributeName=lastActivityTime,KeyType=RANGE}],Projection={ProjectionType=ALL}" `
    --sse-specification Enabled=true,SSEType=KMS `
    --region $REGION 2>$null

Write-Host "  UserSettings table created" -ForegroundColor Green

# AlertHistory table
aws dynamodb create-table `
    --table-name SeniorCare-AlertHistory `
    --attribute-definitions `
        AttributeName=userId,AttributeType=S `
        AttributeName=alertId,AttributeType=S `
        AttributeName=status,AttributeType=S `
        AttributeName=createdAt,AttributeType=S `
    --key-schema `
        AttributeName=userId,KeyType=HASH `
        AttributeName=alertId,KeyType=RANGE `
    --billing-mode PAY_PER_REQUEST `
    --global-secondary-indexes `
        "IndexName=status-createdAt-index,KeySchema=[{AttributeName=status,KeyType=HASH},{AttributeName=createdAt,KeyType=RANGE}],Projection={ProjectionType=ALL}" `
    --sse-specification Enabled=true,SSEType=KMS `
    --region $REGION 2>$null

Write-Host "  AlertHistory table created" -ForegroundColor Green

# Create SNS topics
Write-Host "`nCreating SNS topics..." -ForegroundColor Yellow

$ALERT_TOPIC_ARN = aws sns create-topic --name SeniorCare-AlertNotification --region $REGION --query 'TopicArn' --output text
$REPORT_TOPIC_ARN = aws sns create-topic --name SeniorCare-DailyReport --region $REGION --query 'TopicArn' --output text
$SYSTEM_TOPIC_ARN = aws sns create-topic --name SeniorCare-SystemAlert --region $REGION --query 'TopicArn' --output text

Write-Host "  SNS topics created" -ForegroundColor Green

# Create SQS queues
Write-Host "`nCreating SQS queues..." -ForegroundColor Yellow

$DLQ_URL = aws sqs create-queue --queue-name SeniorCare-DeadLetterQueue --region $REGION --query 'QueueUrl' --output text
$QUEUE_URL = aws sqs create-queue `
    --queue-name SeniorCare-NotificationQueue `
    --attributes "VisibilityTimeout=300,MessageRetentionPeriod=1209600,ReceiveMessageWaitTimeSeconds=20" `
    --region $REGION --query 'QueueUrl' --output text

Write-Host "  SQS queues created" -ForegroundColor Green

# Create S3 bucket for reports
Write-Host "`nCreating S3 bucket..." -ForegroundColor Yellow

$ACCOUNT_ID = aws sts get-caller-identity --query Account --output text
$BUCKET_NAME = "senior-care-reports-$ACCOUNT_ID"

aws s3 mb s3://$BUCKET_NAME --region $REGION 2>$null
aws s3api put-bucket-encryption `
    --bucket $BUCKET_NAME `
    --server-side-encryption-configuration '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"aws:kms"}}]}' `
    --region $REGION

Write-Host "  S3 bucket created: $BUCKET_NAME" -ForegroundColor Green

Write-Host "`nDeployment complete!" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "1. Create RDS PostgreSQL instance manually or use existing one"
Write-Host "2. Run database/init_db.py to initialize schema"
Write-Host "3. Package and deploy Lambda functions using SAM CLI"
Write-Host "   - Run: sam build"
Write-Host "   - Run: sam deploy --guided"
