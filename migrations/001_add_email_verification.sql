-- Migration: Add email verification columns to app_users table
-- Date: 2025-12-10
-- Description: Adds columns for email verification with token-based verification and resend support

-- Add is_verified column (defaults to false for new users)
ALTER TABLE app_users 
ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT FALSE;

-- Add email verification token storage
ALTER TABLE app_users 
ADD COLUMN IF NOT EXISTS email_verification_token TEXT;

-- Add token expiry timestamp
ALTER TABLE app_users 
ADD COLUMN IF NOT EXISTS email_verification_expires TIMESTAMPTZ;

-- Add timestamp for when verification email was last sent
ALTER TABLE app_users 
ADD COLUMN IF NOT EXISTS verification_sent_at TIMESTAMPTZ;

-- Add counter for verification attempts (for rate limiting resends)
ALTER TABLE app_users 
ADD COLUMN IF NOT EXISTS verification_attempts INT DEFAULT 0;

-- Add max attempts configuration (allows per-user customization if needed)
ALTER TABLE app_users 
ADD COLUMN IF NOT EXISTS verification_max_attempts INT DEFAULT 5;

-- Create index on verification token for faster lookups
CREATE INDEX IF NOT EXISTS idx_app_users_verification_token 
ON app_users(email_verification_token) 
WHERE email_verification_token IS NOT NULL;

-- Optional: Update existing users to be verified (if you want existing users to bypass verification)
-- Uncomment the following line if you want all existing users to be marked as verified:
-- UPDATE app_users SET is_verified = TRUE WHERE is_verified IS NULL OR is_verified = FALSE;

-- Verify the migration was successful
SELECT column_name, data_type, column_default, is_nullable
FROM information_schema.columns
WHERE table_name = 'app_users' 
  AND column_name IN (
    'is_verified', 
    'email_verification_token', 
    'email_verification_expires',
    'verification_sent_at',
    'verification_attempts',
    'verification_max_attempts'
  )
ORDER BY column_name;

