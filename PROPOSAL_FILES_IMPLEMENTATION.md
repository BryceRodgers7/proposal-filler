# Proposal Files Management Implementation

## Overview
This implementation adds a new proposal files management system that allows organization representatives to upload multiple proposal documents and select which one to use for AI-powered features across different pages.

## Changes Made

### 1. Database Changes

#### New Table: `proposal_files`
Created a new table to store multiple proposal files per organization:
- `id`: Primary key
- `user_id`: Foreign key to app_users (organization representative)
- `file_name`: Original filename
- `file_path`: S3 key or local path
- `file_type`: MIME type
- `display_name`: User-friendly name shown in dropdowns (editable)
- `is_deleted`: Soft delete flag
- `created_at`, `updated_at`: Timestamps

**Migration File**: `migrations/004_add_proposal_files.sql`

#### New Table: `file_extractions` (Added in migration 005)
Created a separate table to store extracted text with metadata:
- `id`: Primary key
- `proposal_file_id`: Foreign key to proposal_files
- `extracted_text`: Text extracted from the proposal for AI features
- `char_count`: Automatically calculated character count (generated column)
- `extracted_at`: Timestamp when extraction was performed

**Migration File**: `migrations/005_add_file_extractions.sql`

#### Database Model Updates
- Added `ProposalFile` model to `helpers/db.py`
- Added `FileExtraction` model to `helpers/db.py` (migration 005)
- Added `proposal_files` relationship to the `User` model
- Added `file_extraction` relationship to the `ProposalFile` model

### 2. New Page: Proposal Manager

**File**: `views/proposal_manager.py`

A dedicated page for organization representatives to manage their proposal files:

**Features**:
- **View all proposals**: List of all uploaded proposals with details
- **Upload new proposals**: Form to upload PDF, DOCX, or TXT files
- **Edit proposals**: Update the display name
- **Delete proposals**: Soft delete proposals (with confirmation)
- **Text extraction**: Optional text extraction for AI features
- **Preview**: View extracted text from proposals

**Access**: Only visible to organization representatives

### 3. Routing and Navigation

#### Updated Files:
- `app.py`: Added import and routing for `render_proposal_manager()`
- `views/sidebar.py`: Added "📂 Proposal Manager" to representative navigation menu

### 4. Organization Profile Page Updates

**File**: `views/proposal_filler.py`

Added a new section before the file upload area:

**Features**:
- **Proposal selector dropdown**: Shows all available proposal files
- **Quick AI extraction**: One-click AI extraction from selected proposal
- **Backwards compatibility**: Still supports uploading new proposals directly
- **Info display**: Shows selected proposal details

**User Flow**:
1. Select a proposal from the dropdown
2. Click "Extract with AI" to populate the form
3. Review and edit the extracted data
4. Save to database

### 5. Card Creator Page Updates

**File**: `views/card_creator.py`

Enhanced the AI card generation feature:

**Features**:
- **Proposal selector dropdown**: Choose which proposal to use for generation
- **Legacy support**: Still supports the old organization profile proposal
- **Smart filtering**: Only shows proposals with extracted text
- **Clear labeling**: Shows upload date for easy identification

**User Flow**:
1. Select a proposal from the dropdown
2. Click "Generate Card with AI"
3. Review the generated card content
4. Edit and save

## How to Use

### For Organization Representatives:

#### Step 1: Upload Proposal Files
1. Navigate to **📂 Proposal Manager** from the sidebar
2. Use the upload form at the bottom of the page
3. Provide a descriptive display name (e.g., "Q4 2024 Grant Proposal")
4. Select your proposal file (PDF, DOCX, or TXT)
5. Check "Extract text for AI features" (recommended)
6. Click "Upload Proposal"

#### Step 2: Use Proposals for AI Features

**On Organization Profile Page**:
1. Go to **👤 Organization Profile**
2. In the "Select Proposal" section, choose your proposal from the dropdown
3. Click "Extract with AI" to auto-fill the form
4. Review and edit the extracted information
5. Save your profile

**On Card Creator Page**:
1. Go to **🎴 Card Creator**
2. Scroll to "Create New Card"
3. In the AI generation section, select a proposal
4. Click "Generate Card with AI"
5. Review the generated title and subtitle
6. Save the card

#### Step 3: Manage Proposals
1. Return to **📂 Proposal Manager** anytime
2. View all your uploaded proposals
3. Edit display names for better organization
4. Delete old or unused proposals
5. Upload new versions as needed

## Technical Details

### File Storage
- All proposal files are uploaded to S3
- Path format: `proposal_files/{user_id}/{uuid}.{extension}`
- Original filenames are preserved in the database

### Text Extraction
- PDF: Uses `pdfplumber` library
- DOCX: Uses `python-docx` library
- TXT: Direct UTF-8 decoding
- Extraction happens during upload for better performance

### AI Integration
- The `generate_organization_card()` function uses proposal extracted text
- A mock proposal object is created for compatibility with new proposal files
- Legacy `ProposalSubmission` records are still supported

### Security
- Only the proposal owner can access their files
- Soft delete prevents data loss
- S3 presigned URLs for secure file access

## Migration Instructions

### Running the Database Migration

The migration needs to be run manually on your Supabase/PostgreSQL database:

1. Connect to your database
2. Run the SQL in `migrations/004_add_proposal_files.sql`
3. Verify the `proposal_files` table was created
4. Verify indexes and triggers were created

### Backwards Compatibility

This implementation maintains full backwards compatibility:
- Existing `ProposalSubmission` records continue to work
- The old single-proposal workflow is still available
- Users can still upload proposals directly on the profile page
- Card creator falls back to legacy proposals if no new files exist

## Benefits

1. **Organization**: Manage multiple proposals for different purposes
2. **Flexibility**: Switch between proposals without re-uploading
3. **Efficiency**: Extract once, use everywhere
4. **Version Control**: Keep different versions of proposals
5. **Clear Selection**: Descriptive names make it easy to choose the right proposal

## Future Enhancements (Optional)

Potential improvements for future iterations:
- Download proposal files
- Proposal file preview (PDF viewer)
- Proposal templates
- Bulk upload multiple files
- Proposal sharing between team members
- Proposal versioning/history
- Analytics on which proposals perform best

