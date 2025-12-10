-- Migration: Add user details fields and soft-delete functionality
-- Date: 2025-12-10
-- Description: Adds personal/address fields to app_users and is_deleted to multiple tables

-- =============================================
-- PART 1: Add user detail fields to app_users
-- =============================================

-- First name (required)
ALTER TABLE app_users 
ADD COLUMN IF NOT EXISTS first_name VARCHAR(100);

-- Last name (required)
ALTER TABLE app_users 
ADD COLUMN IF NOT EXISTS last_name VARCHAR(100);

-- Company (optional)
ALTER TABLE app_users 
ADD COLUMN IF NOT EXISTS company VARCHAR(255);

-- Street address (required)
ALTER TABLE app_users 
ADD COLUMN IF NOT EXISTS street_address VARCHAR(500);

-- City (required)
ALTER TABLE app_users 
ADD COLUMN IF NOT EXISTS city VARCHAR(100);

-- State (required)
ALTER TABLE app_users 
ADD COLUMN IF NOT EXISTS state VARCHAR(100);

-- ZIP code (required)
ALTER TABLE app_users 
ADD COLUMN IF NOT EXISTS zip_code VARCHAR(20);

-- Phone number (optional)
ALTER TABLE app_users 
ADD COLUMN IF NOT EXISTS phone_number VARCHAR(50);

-- =============================================
-- PART 2: Add soft-delete field to tables
-- =============================================

-- Add is_deleted to app_users
ALTER TABLE app_users 
ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN NOT NULL DEFAULT FALSE;

-- Add is_deleted to donor_profiles
ALTER TABLE donor_profiles 
ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN NOT NULL DEFAULT FALSE;

-- Add is_deleted to proposal_submissions
ALTER TABLE proposal_submissions 
ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN NOT NULL DEFAULT FALSE;

-- =============================================
-- PART 3: Populate existing rows with defaults
-- =============================================

-- Update existing users with placeholder data for required fields
UPDATE app_users 
SET 
    first_name = 'John',
    last_name = 'Smith',
    street_address = '555 Main Street',
    city = 'New York',
    state = 'NY',
    zip_code = '12345'
WHERE first_name IS NULL OR last_name IS NULL OR street_address IS NULL OR city IS NULL OR state IS NULL OR zip_code IS NULL;

-- Ensure is_deleted is false for all existing rows
UPDATE app_users SET is_deleted = FALSE WHERE is_deleted IS NULL;
UPDATE donor_profiles SET is_deleted = FALSE WHERE is_deleted IS NULL;
UPDATE proposal_submissions SET is_deleted = FALSE WHERE is_deleted IS NULL;

-- =============================================
-- PART 4: Add indexes for soft-delete queries
-- =============================================

-- Index on is_deleted for app_users (for filtering active users)
CREATE INDEX IF NOT EXISTS idx_app_users_is_deleted 
ON app_users(is_deleted);

-- Index on is_deleted for donor_profiles (for filtering active donor profiles)
CREATE INDEX IF NOT EXISTS idx_donor_profiles_is_deleted 
ON donor_profiles(is_deleted);

-- Index on is_deleted for proposal_submissions (for filtering active proposals)
CREATE INDEX IF NOT EXISTS idx_proposal_submissions_is_deleted 
ON proposal_submissions(is_deleted);

-- =============================================
-- PART 5: Verify the migration
-- =============================================

-- Check app_users columns
SELECT column_name, data_type, column_default, is_nullable
FROM information_schema.columns
WHERE table_name = 'app_users' 
  AND column_name IN (
    'first_name', 
    'last_name', 
    'company',
    'street_address',
    'city',
    'state',
    'zip_code',
    'phone_number',
    'is_deleted'
  )
ORDER BY column_name;

-- Check donor_profiles columns
SELECT column_name, data_type, column_default, is_nullable
FROM information_schema.columns
WHERE table_name = 'donor_profiles' 
  AND column_name = 'is_deleted';

-- Check proposal_submissions columns
SELECT column_name, data_type, column_default, is_nullable
FROM information_schema.columns
WHERE table_name = 'proposal_submissions' 
  AND column_name = 'is_deleted';

