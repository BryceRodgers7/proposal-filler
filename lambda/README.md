# Lambda Function Deployment Guide

## Handler Configuration

When deploying this Lambda function, make sure the **Handler** is set correctly in the AWS Lambda console:

- **If you zipped the CONTENTS of the `lambda/` folder** (lambda_function.py at root of zip):
  - Handler: `lambda_function.lambda_handler`

- **If you zipped the `lambda/` FOLDER itself** (lambda/ folder inside the zip):
  - Handler: `lambda.lambda_function.lambda_handler` ⚠️ **This is likely your issue!**

## Deployment Package Structure

### Option 1: Deploy just the function file (Recommended)
```
deployment.zip
├── lambda_function.py
├── secrets.toml (optional - use environment variables instead)
└── [dependencies]
```

### Option 2: Deploy the lambda folder
```
deployment.zip
├── lambda/
│   ├── lambda_function.py
│   └── secrets.toml (optional)
└── [dependencies]
```
In this case, handler should still be `lambda_function.lambda_handler` (AWS Lambda will look for the file in the root of the zip).

## Required Dependencies

You **must** include these Python packages in your deployment package:
- `stripe` (required - not included in Lambda runtime)
- `requests` (usually included in Lambda runtime, but include it to be safe)

### How to Create Deployment Package with Dependencies

**Option 1: Use the deployment script (Recommended)**

On Windows (PowerShell):
```powershell
cd lambda
.\deploy.ps1
```

On Mac/Linux:
```bash
cd lambda
chmod +x deploy.sh
./deploy.sh
```

This will create `lambda_deployment.zip` with all dependencies included.

**Option 2: Manual method**

1. Create a new folder (e.g., `lambda_deploy`)
2. Copy `lambda_function.py` (and optionally `secrets.toml`) into it
3. Install dependencies into that folder:
   ```bash
   pip install stripe requests -t lambda_deploy
   ```
4. Zip the contents of the folder (not the folder itself):
   ```bash
   cd lambda_deploy
   zip -r ../lambda_deployment.zip .
   ```
5. Upload `lambda_deployment.zip` to AWS Lambda

**Important**: When zipping, make sure the files are at the root of the zip, not in a subfolder. The structure should be:
```
lambda_deployment.zip
├── lambda_function.py
├── stripe/ (package)
├── requests/ (package)
└── [other dependencies]
```

## Environment Variables (Recommended for Production)

Instead of using `secrets.toml`, set these as environment variables in the Lambda function configuration:

- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`

## Testing

After deployment, test the function with a sample Stripe webhook event to ensure it's working correctly.

