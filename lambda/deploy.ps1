# PowerShell script to create a Lambda deployment package with dependencies
# Run this from the lambda/ directory

# Create a temporary directory for the deployment package
$deployDir = "lambda_deploy"
if (Test-Path $deployDir) {
    Remove-Item -Recurse -Force $deployDir
}
New-Item -ItemType Directory -Path $deployDir | Out-Null

# Copy the lambda function files
Copy-Item "lambda_function.py" -Destination $deployDir
if (Test-Path "secrets.toml") {
    Copy-Item "secrets.toml" -Destination $deployDir
} else {
    Write-Host "Note: secrets.toml not found (using environment variables)"
}

# Install dependencies into the deployment directory
Write-Host "Installing dependencies..."
pip install stripe requests -t $deployDir

# Create the zip file
Write-Host "Creating deployment package..."
Compress-Archive -Path "$deployDir\*" -DestinationPath "lambda_deployment.zip" -Force

# Clean up
Remove-Item -Recurse -Force $deployDir

Write-Host "Deployment package created: lambda_deployment.zip"
Write-Host "Upload this file to AWS Lambda"

