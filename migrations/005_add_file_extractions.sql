-- Migration: Add file_extractions table for storing extracted text from proposal files
-- This separates extracted text into its own table with metadata and removes extracted_text from proposal_files

-- Create file_extractions table
CREATE TABLE IF NOT EXISTS file_extractions (
    id SERIAL PRIMARY KEY,
    proposal_file_id INTEGER NOT NULL REFERENCES proposal_files(id) ON DELETE CASCADE,
    
    -- Extracted text content
    extracted_text TEXT NOT NULL,
    
    -- Character count (generated column)
    char_count INTEGER GENERATED ALWAYS AS (char_length(extracted_text)) STORED,
    
    -- Timestamp when extraction was performed
    extracted_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_file_extractions_proposal_file_id ON file_extractions(proposal_file_id);
CREATE INDEX IF NOT EXISTS idx_file_extractions_extracted_at ON file_extractions(extracted_at);

-- Migrate existing extracted_text data from proposal_files to file_extractions
INSERT INTO file_extractions (proposal_file_id, extracted_text, extracted_at)
SELECT id, extracted_text, created_at
FROM proposal_files
WHERE extracted_text IS NOT NULL AND extracted_text != '';

-- Remove extracted_text column from proposal_files
ALTER TABLE proposal_files DROP COLUMN IF EXISTS extracted_text;

