$env:PYTHONIOENCODING='utf-8'

Write-Host "Building SAM application..." -ForegroundColor Green
& 'C:\Program Files\Amazon\AWSSAMCLI\bin\sam.cmd' build

if ($LASTEXITCODE -ne 0) {
    Write-Host "Build failed!" -ForegroundColor Red
    exit 1
}

Write-Host "`nDeploying to AWS..." -ForegroundColor Green
& 'C:\Program Files\Amazon\AWSSAMCLI\bin\sam.cmd' deploy `
    --stack-name senior-care-monitoring `
    --s3-bucket aws-sam-cli-managed-default-samclisourcebucket-098042404538 `
    --s3-prefix senior-care-monitoring `
    --region us-east-1 `
    --capabilities CAPABILITY_IAM `
    --no-confirm-changeset `
    --no-fail-on-empty-changeset

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nDeployment successful!" -ForegroundColor Green
    Write-Host "`nGetting stack outputs..." -ForegroundColor Cyan
    aws cloudformation describe-stacks --stack-name senior-care-monitoring --region us-east-1 --query "Stacks[0].Outputs" --output table
} else {
    Write-Host "`nDeployment failed!" -ForegroundColor Red
    exit 1
}
