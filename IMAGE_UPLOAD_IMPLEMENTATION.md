# Organization Image Upload Implementation

## Overview

Added functionality for organizations to upload logo/images to their profiles. Images are automatically processed, resized, and stored in S3, then displayed on both the organization profile page and the Tinder-ish page.

---

## Features Implemented

### 1. **Automatic Image Processing**
- Images are automatically resized to fit within 800x600px while maintaining aspect ratio
- Converts all formats (PNG, JPG, GIF) to optimized JPEG
- Handles transparency in PNGs by adding white background
- High-quality resampling for best visual results
- Reduced file size for faster loading

### 2. **S3 Storage**
- Images stored in S3 at `organization_images/{org_id}.jpg`
- Organized folder structure for easy management
- Secure storage with proper content types

### 3. **Database Integration**
- New `image_path` column in `proposal_submissions` table
- Stores S3 key for each organization's image
- Nullable column (organizations can exist without images)

### 4. **User Interface**
- Image upload widget on Organization Profile page
- Preview of current image before uploading new one
- Automatic display on Tinder-ish page
- Responsive image sizing with CSS

---

## Files Modified

### Backend

#### 1. `helpers/db.py`
**Added:**
- `image_path` column to `ProposalSubmission` model

```python
image_path = Column(String(500), nullable=True)
```

#### 2. `helpers/storage.py`
**Added:**
- `process_image()` - Resizes and converts images
- `upload_organization_image()` - Handles organization image upload

**Features:**
- Maintains aspect ratio
- Converts to JPEG for consistency
- Handles transparency
- High-quality resampling
- Optimized compression (85% quality)

### Frontend

#### 3. `views/proposal_filler.py`
**Added:**
- Image upload widget after form fields
- Display of current image (if exists)
- Image processing and upload logic in save function
- Success/error messages for image upload

**Import added:**
```python
from helpers.storage import upload_organization_image, get_s3_url
```

#### 4. `views/tinderish.py`
**Added:**
- Image display at top of each organization card
- Centered, responsive image layout
- Error handling for missing images

**Import added:**
```python
from helpers.storage import get_s3_url
```

#### 5. `requirements.txt`
**Added:**
```
Pillow>=10.0.0
```

---

## Database Migration

### For Supabase:

Run this SQL command in your Supabase SQL Editor:

```sql
ALTER TABLE proposal_submissions 
ADD COLUMN image_path VARCHAR(500);

COMMENT ON COLUMN proposal_submissions.image_path IS 'S3 key/path for organization logo or image';
```

See `SUPABASE_ADD_IMAGE_COLUMN.sql` for the complete migration script.

---

## How It Works

### Upload Process:

1. **Organization Profile Page**:
   - Representative uploads image via file uploader
   - Image is stored in session state temporarily
   - Message confirms image is ready to upload

2. **Save Process**:
   - When "Save to Database" is clicked:
     - Profile data is saved first
     - Image is processed (resize, convert to JPEG)
     - Processed image uploaded to S3
     - S3 path saved to database
   - Success message confirms upload

3. **Display on Tinder-ish**:
   - Image URL generated from S3 path
   - Displayed at top of organization card
   - Centered with responsive width
   - Graceful fallback if image missing

### Image Processing Details:

**Input:** Any image file (JPG, PNG, GIF)

**Processing:**
1. Open image with PIL
2. Convert RGBA/transparent to RGB (white background)
3. Calculate new dimensions (max 800x600, maintain ratio)
4. Resize with high-quality LANCZOS resampling
5. Save as JPEG with 85% quality
6. Upload to S3 as `organization_images/{org_id}.jpg`

**Output:** Optimized JPEG stored in S3

---

## Image Display Specifications

### Organization Profile Page:
- Shows current image (if exists) at 300px width
- Upload widget below current image
- Accepts JPG, PNG, GIF formats

### Tinder-ish Page:
- Displayed at top of each card
- Centered in middle column (3:5 ratio)
- Responsive width (scales with page)
- Maintains aspect ratio
- Clean, professional presentation

---

## Error Handling

### Image Processing Errors:
- Invalid image format → Error message, upload skipped
- Corrupted file → Error message, upload skipped

### S3 Upload Errors:
- No S3 credentials → Warning message
- Upload failure → Warning message, profile saves without image

### Display Errors:
- Missing image file → No image shown (graceful degradation)
- Invalid S3 path → Info message shown

---

## Supported Image Formats

**Upload:** JPG, JPEG, PNG, GIF

**Storage:** JPEG (all converted)

**Recommended:**
- Aspect ratio: 4:3 or similar
- Size: 800x600px or larger
- File size: Under 5MB

---

## Testing Checklist

- [ ] Upload image on Organization Profile page
- [ ] Verify image appears on profile page after save
- [ ] Navigate to Tinder-ish page
- [ ] Verify image displays on organization card
- [ ] Test with different image formats (JPG, PNG, GIF)
- [ ] Test with transparent PNG
- [ ] Test with very large image (should resize)
- [ ] Test with very small image (should not upscale)
- [ ] Test organization without image (should work fine)
- [ ] Test replacing existing image

---

## S3 Bucket Requirements

### Permissions Needed:
- `s3:PutObject` - Upload images
- `s3:GetObject` - Retrieve images
- Public read access for display (or signed URLs)

### Folder Structure:
```
bucket-name/
├── uploads/           (existing - proposal documents)
└── organization_images/  (new - organization logos/images)
    ├── 1.jpg
    ├── 2.jpg
    └── ...
```

---

## Future Enhancements

**Potential improvements:**
1. Image cropping tool (let users crop before upload)
2. Multiple images per organization (gallery)
3. Image compression options
4. Thumbnail generation
5. CDN integration for faster loading
6. Image moderation/approval workflow
7. Default placeholder images

---

## Notes

- Images are automatically overwritten when organization uploads new one
- Original filenames not preserved (uses org ID)
- All images converted to JPEG for consistency
- Processing happens client-side before upload
- No storage quota implemented yet
- Images are permanent (no auto-deletion)

---

## Installation

1. Update database schema (run SQL migration)
2. Install new dependencies: `pip install Pillow>=10.0.0`
3. Ensure S3 credentials are configured
4. Restart Streamlit application
5. Test image upload on organization profile

---

All features are complete and ready for use! 🎉

