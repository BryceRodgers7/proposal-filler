# lambda_function.py
import json
import os
import base64
from datetime import datetime, timezone
from pathlib import Path

import stripe
import requests

# Try to use tomllib (Python 3.11+), fall back to tomli if needed
try:
    import tomllib
except ImportError:
    import tomli as tomllib

# Read secrets from secrets.toml in the lambda folder
# In Lambda deployment, secrets.toml should be in the same directory as this file
secrets_path = Path(__file__).parent / "secrets.toml"

if secrets_path.exists():
    with open(secrets_path, "rb") as f:
        secrets = tomllib.load(f)
    STRIPE_SECRET_KEY = secrets["STRIPE_SECRET_KEY"]
    STRIPE_WEBHOOK_SECRET = secrets["STRIPE_WEBHOOK_SECRET"]
    SUPABASE_URL = secrets["SUPABASE_URL"].rstrip("/")
    SUPABASE_SERVICE_ROLE_KEY = secrets["SUPABASE_SERVICE_ROLE_KEY"]
else:
    # Fallback to environment variables if secrets.toml doesn't exist
    # (useful for local testing or if secrets are set via Lambda environment variables)
    STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
    STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
    SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
    SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

# Validate that required secrets are set
if not STRIPE_SECRET_KEY or not STRIPE_WEBHOOK_SECRET or not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise ValueError(
        "Missing required environment variables or secrets. "
        "Please set: STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY"
    )

stripe.api_key = STRIPE_SECRET_KEY


def supabase_update_user_account_tier(user_id: str, account_tier: str, stripe_customer_id: str = None):
    """
    Update the user's account_tier in the app_users table via Supabase REST API.
    Assumes an 'app_users' table with:
      - id (integer, primary key)
      - account_tier (text)
      - stripe_customer_id (text, nullable)
    """
    try:
        payload = {
            "account_tier": account_tier,
        }
        if stripe_customer_id:
            payload["stripe_customer_id"] = stripe_customer_id

        # Supabase REST endpoint for app_users table
        # Ensure URL doesn't have trailing slash
        base_url = SUPABASE_URL.rstrip("/")
        url = f"{base_url}/rest/v1/app_users?id=eq.{user_id}"

        print(f"Updating user {user_id} at URL: {url}")
        print(f"Payload: {json.dumps(payload)}")

        headers = {
            "apikey": SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        }

        resp = requests.patch(url, headers=headers, data=json.dumps(payload), timeout=10)
        
        # Log response details
        print(f"Response status: {resp.status_code}")
        print(f"Response text: {resp.text}")
        
        if resp.status_code not in (200, 204):
            error_msg = f"Supabase update failed: {resp.status_code} - {resp.text}"
            print(error_msg)
            raise Exception(error_msg)
        else:
            print(f"Successfully updated user {user_id} to account_tier: {account_tier}")
            return True
    except Exception as e:
        print(f"Error in supabase_update_user_account_tier: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise


def lambda_handler(event, context):
    """
    AWS Lambda entrypoint for Stripe webhook.
    Expects to be invoked via Lambda Function URL.
    """

    # Get raw body (handle base64-encoded case)
    body = event.get("body", "")
    if event.get("isBase64Encoded"):
        body = base64.b64decode(body)
    else:
        # If body is a string, encode it to bytes for Stripe webhook verification
        if isinstance(body, str):
            body = body.encode('utf-8')

    # Get Stripe signature header (header names can vary in case)
    headers = event.get("headers", {}) or {}
    sig_header = headers.get("stripe-signature") or headers.get("Stripe-Signature")
    if not sig_header:
        # Not a Stripe webhook, ignore
        return {
            "statusCode": 400,
            "body": "Missing Stripe-Signature header",
        }

    # Verify and construct the event
    try:
        stripe_event = stripe.Webhook.construct_event(
            payload=body,
            sig_header=sig_header,
            secret=STRIPE_WEBHOOK_SECRET,
        )
    except ValueError as e:
        # Invalid payload
        print("Invalid payload:", e)
        return {"statusCode": 400, "body": "Invalid payload"}
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        print("Invalid signature:", e)
        return {"statusCode": 400, "body": "Invalid signature"}

    event_type = stripe_event["type"]
    data_object = stripe_event["data"]["object"]

    print("Received event:", event_type)

    # --- When checkout session completes, upgrade user to premium ---
    if event_type == "checkout.session.completed":
        print("Processing checkout.session.completed event")
        print(f"Data object: {json.dumps(data_object, indent=2)}")
        
        # Get user ID from metadata (set when creating checkout session)
        metadata = data_object.get("metadata") or {}
        user_id = metadata.get("user_id")
        customer_id = data_object.get("customer")  # Stripe customer ID

        print(f"Extracted user_id: {user_id}, customer_id: {customer_id}")

        if user_id:
            try:
                # Update user's account tier to premium
                supabase_update_user_account_tier(
                    user_id=str(user_id),
                    account_tier="premium",
                    stripe_customer_id=customer_id if customer_id else None,
                )
                print(f"Successfully processed upgrade for user {user_id}")
            except Exception as e:
                print(f"Error processing upgrade for user {user_id}: {str(e)}")
                # Don't return error - we still want to return 200 to Stripe
                # to prevent retries, but log the error
        else:
            error_msg = "Warning: checkout.session.completed event missing user_id in metadata"
            print(error_msg)
            print(f"Available metadata keys: {list(metadata.keys())}")

    # TODO: later you can also handle:
    # - 'customer.subscription.updated' (downgrades, cancels)
    # - 'customer.subscription.deleted'

    return {
        "statusCode": 200,
        "body": json.dumps({"received": True}),
    }
