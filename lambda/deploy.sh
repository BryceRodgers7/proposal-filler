#!/bin/bash
# Script to create a Lambda deployment package with dependencies

# Create a temporary directory for the deployment package
mkdir -p lambda_deploy
cd lambda_deploy

# Copy the lambda function files
cp ../lambda_function.py .
cp ../secrets.toml . 2>/dev/null || echo "Note: secrets.toml not found (using environment variables)"

# Install dependencies into the current directory
pip install stripe requests -t .

# Create the zip file
zip -r ../lambda_deployment.zip .

# Clean up
cd ..
rm -rf lambda_deploy

echo "Deployment package created: lambda_deployment.zip"
echo "Upload this file to AWS Lambda"

