# Package Lambda functions for deployment

Write-Host "Packaging Lambda functions..." -ForegroundColor Yellow

$functions = @(
    "sensor_data_processor",
    "inactivity_detector",
    "voice_response_handler",
    "notification_manager",
    "report_generator",
    "settings_manager",
    "activity_history_query"
)

# Create dist directory
New-Item -ItemType Directory -Force -Path "dist" | Out-Null

foreach ($func in $functions) {
    Write-Host "Packaging $func..." -ForegroundColor Cyan
    
    $srcDir = "src/$func"
    $zipFile = "dist/$func.zip"
    
    # Remove old zip
    if (Test-Path $zipFile) {
        Remove-Item $zipFile
    }
    
    # Create temp directory
    $tempDir = "temp_$func"
    New-Item -ItemType Directory -Force -Path $tempDir | Out-Null
    
    # Copy function code
    Copy-Item -Path "$srcDir/*" -Destination $tempDir -Recurse
    
    # Copy common modules
    Copy-Item -Path "src/common" -Destination $tempDir -Recurse
    
    # Create zip
    Compress-Archive -Path "$tempDir/*" -DestinationPath $zipFile
    
    # Cleanup
    Remove-Item -Path $tempDir -Recurse -Force
    
    Write-Host "  Created: $zipFile" -ForegroundColor Green
}

Write-Host "`nAll Lambda functions packaged successfully!" -ForegroundColor Green
