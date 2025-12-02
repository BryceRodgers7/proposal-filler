-- =====================================================
-- SUPABASE MIGRATION SQL
-- Add Organization Image Support
-- =====================================================
-- Run this command in your Supabase SQL Editor to add image support

-- Add image_path column to proposal_submissions table
ALTER TABLE proposal_submissions 
ADD COLUMN image_path VARCHAR(500);

-- Add comment for documentation
COMMENT ON COLUMN proposal_submissions.image_path IS 'S3 key/path for organization logo or image';

-- =====================================================
-- VERIFICATION QUERY (Optional)
-- =====================================================
-- Run this to verify the column was added successfully

SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns 
WHERE table_name = 'proposal_submissions' AND column_name = 'image_path';

