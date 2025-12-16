-- Migration: Add proposal_files table for managing multiple proposal documents per organization
-- This allows organization representatives to upload and manage multiple proposals
-- and select which one to use for AI features

CREATE TABLE IF NOT EXISTS proposal_files (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES app_users(id) ON DELETE CASCADE,
    
    -- File information
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,  -- S3 key or local path
    file_type TEXT NOT NULL,  -- MIME type
    
    -- Display name for the dropdown (editable by user)
    display_name VARCHAR(255) NOT NULL,
    
    -- Extracted text from the proposal (for AI features)
    extracted_text TEXT,
    
    -- Soft delete flag
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_proposal_files_user_id ON proposal_files(user_id);
CREATE INDEX IF NOT EXISTS idx_proposal_files_is_deleted ON proposal_files(is_deleted);
CREATE INDEX IF NOT EXISTS idx_proposal_files_created_at ON proposal_files(created_at);

-- Add trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_proposal_files_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_proposal_files_updated_at
    BEFORE UPDATE ON proposal_files
    FOR EACH ROW
    EXECUTE FUNCTION update_proposal_files_updated_at();

