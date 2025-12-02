import boto3
import streamlit as st
from botocore.exceptions import ClientError, NoCredentialsError
import os
from io import BytesIO
from PIL import Image


def get_s3_client():
    """
    Initialize and return an S3 client using credentials from secrets.toml or environment variables.
    Returns None if credentials are not available.
    """
    try:
        # Try to get credentials from Streamlit secrets first
        try:
            if hasattr(st, 'secrets') and st.secrets is not None and 'AWS_ACCESS_KEY_ID' in st.secrets:
                access_key = st.secrets['AWS_ACCESS_KEY_ID']
                secret_key = st.secrets['AWS_SECRET_ACCESS_KEY']
                region = st.secrets.get('AWS_DEFAULT_REGION', 'us-east-1')
                bucket_name = st.secrets.get('AWS_BUCKET', 'proposal-filler-bucket')
            # Fallback to environment variables
            elif 'AWS_ACCESS_KEY_ID' in os.environ:
                access_key = os.environ['AWS_ACCESS_KEY_ID']
                secret_key = os.environ['AWS_SECRET_ACCESS_KEY']
                region = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
                bucket_name = os.environ.get('AWS_BUCKET', 'proposal-filler-bucket')
            else:
                return None, None
        except (AttributeError, KeyError, TypeError):
            # If st.secrets is not available or doesn't have the keys, try environment variables
            if 'AWS_ACCESS_KEY_ID' in os.environ:
                access_key = os.environ['AWS_ACCESS_KEY_ID']
                secret_key = os.environ['AWS_SECRET_ACCESS_KEY']
                region = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
                bucket_name = os.environ.get('AWS_BUCKET', 'proposal-filler-bucket')
            else:
                return None, None
        
        # Create S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        
        return s3_client, bucket_name
    except Exception as e:
        print(f"⚠️ Error initializing S3 client: {str(e)}")
        return None, None


def upload_file_to_s3(file_data: bytes, file_name: str, content_type: str = None) -> str:
    """
    Upload a file to S3 bucket.
    
    Args:
        file_data: The file data as bytes
        file_name: The name of the file (will be used as S3 key)
        content_type: Optional MIME type of the file
    
    Returns:
        S3 key (path) if successful, None otherwise
    """
    s3_client, bucket_name = get_s3_client()
    
    if s3_client is None or bucket_name is None:
        print("❌ S3 client not available. Cannot upload file.")
        return None
    
    print(f"📤 Uploading to S3 bucket: {bucket_name}, key: {file_name}, size: {len(file_data)} bytes")
    
    try:
        # Upload file to S3
        extra_args = {}
        if content_type:
            extra_args['ContentType'] = content_type
            print(f"📋 Content-Type: {content_type}")
        
        s3_client.put_object(
            Bucket=bucket_name,
            Key=file_name,
            Body=file_data,
            **extra_args
        )
        
        print(f"✅ Successfully uploaded to S3: {file_name}")
        # Return the S3 key (path)
        return file_name
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_msg = e.response['Error']['Message']
        print(f"❌ S3 ClientError ({error_code}): {error_msg}")
        print(f"   Bucket: {bucket_name}, Key: {file_name}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error uploading file to S3: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return None


def get_s3_url(s3_key: str, check_exists=True, use_presigned=True) -> tuple:
    """
    Generate a URL for an S3 object with detailed error reporting.
    
    Args:
        s3_key: The S3 key (path) of the object
        check_exists: Whether to check if object exists in S3 (default: True)
        use_presigned: Whether to use presigned URLs for private buckets (default: True)
    
    Returns:
        Tuple of (url: str or None, error_message: str or None)
    """
    s3_client, bucket_name = get_s3_client()
    
    if s3_client is None or bucket_name is None:
        error_msg = "❌ S3 client not configured. Check AWS credentials in secrets."
        print(error_msg)
        return None, error_msg
    
    if not s3_key:
        error_msg = "❌ No S3 key provided (image_path is empty)"
        print(error_msg)
        return None, error_msg
    
    try:
        # Check if object exists in S3 and get metadata
        if check_exists:
            try:
                print(f"🔍 Checking if S3 object exists: {s3_key} in bucket: {bucket_name}")
                response = s3_client.head_object(Bucket=bucket_name, Key=s3_key)
                print(f"✅ S3 object found: {s3_key}")
                print(f"   Content-Type: {response.get('ContentType', 'unknown')}")
                print(f"   Size: {response.get('ContentLength', 0)} bytes")
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == '404':
                    error_msg = f"❌ Image not found in S3: {s3_key} (bucket: {bucket_name})"
                    print(error_msg)
                    return None, error_msg
                elif error_code == '403':
                    error_msg = f"❌ Access denied to S3 object: {s3_key} (check IAM permissions)"
                    print(error_msg)
                    return None, error_msg
                else:
                    error_msg = f"❌ S3 error ({error_code}): {str(e)}"
                    print(error_msg)
                    return None, error_msg
        
        # Generate URL
        if use_presigned:
            # Use presigned URL for secure access (works with private buckets)
            try:
                print(f"🔐 Generating presigned URL (expires in 1 hour)")
                url = s3_client.generate_presigned_url(
                    'get_object',
                    Params={
                        'Bucket': bucket_name,
                        'Key': s3_key
                    },
                    ExpiresIn=3600  # 1 hour
                )
                print(f"✅ Generated presigned S3 URL: {url[:100]}...")
                return url, None
            except Exception as presign_error:
                print(f"⚠️ Presigned URL failed: {str(presign_error)}, falling back to public URL")
                # Fall through to public URL
        
        # Generate public URL (requires bucket to be publicly accessible)
        region = s3_client.meta.region_name
        url = f"https://{bucket_name}.s3.{region}.amazonaws.com/{s3_key}"
        print(f"✅ Generated public S3 URL: {url}")
        print(f"⚠️ Note: Public URLs require bucket to have public read permissions")
        return url, None
    except Exception as e:
        error_msg = f"❌ Unexpected error generating S3 URL: {str(e)}"
        print(error_msg)
        import traceback
        print(traceback.format_exc())
        return None, error_msg


def is_s3_available() -> bool:
    """
    Check if S3 is available and configured.
    
    Returns:
        True if S3 is available, False otherwise
    """
    s3_client, bucket_name = get_s3_client()
    return s3_client is not None and bucket_name is not None


def process_image(image_file, max_width=800, max_height=600, quality=85):
    """
    Process and resize an uploaded image to fit within specified dimensions.
    Maintains aspect ratio and converts to JPEG format.
    
    Args:
        image_file: Uploaded file object from Streamlit
        max_width: Maximum width in pixels (default 800)
        max_height: Maximum height in pixels (default 600)
        quality: JPEG quality (1-100, default 85)
    
    Returns:
        Tuple of (processed_image_bytes, content_type)
    """
    try:
        # Open the image
        image = Image.open(image_file)
        
        # Convert RGBA to RGB if necessary (for PNG with transparency)
        if image.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Calculate new dimensions maintaining aspect ratio
        original_width, original_height = image.size
        aspect_ratio = original_width / original_height
        
        if original_width > max_width or original_height > max_height:
            if aspect_ratio > (max_width / max_height):
                # Width is the limiting factor
                new_width = max_width
                new_height = int(max_width / aspect_ratio)
            else:
                # Height is the limiting factor
                new_height = max_height
                new_width = int(max_height * aspect_ratio)
            
            # Resize image with high-quality resampling
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Save to bytes buffer
        buffer = BytesIO()
        image.save(buffer, format='JPEG', quality=quality, optimize=True)
        buffer.seek(0)
        
        return buffer.getvalue(), 'image/jpeg'
    
    except Exception as e:
        print(f"⚠️ Error processing image: {str(e)}")
        return None, None


def upload_organization_image(image_file, org_id):
    """
    Process and upload an organization's logo/image to S3.
    
    Args:
        image_file: Uploaded file object from Streamlit
        org_id: Organization/proposal ID
    
    Returns:
        S3 key (path) if successful, None otherwise
    """
    print(f"📤 Starting image upload for org_id: {org_id}")
    
    # Process the image
    print(f"🖼️ Processing image: {image_file.name if hasattr(image_file, 'name') else 'unknown'}")
    processed_image, content_type = process_image(image_file)
    
    if processed_image is None:
        print(f"❌ Image processing failed for org_id: {org_id}")
        return None
    
    print(f"✅ Image processed successfully. Size: {len(processed_image)} bytes, Type: {content_type}")
    
    # Generate S3 key
    s3_key = f"organization_images/{org_id}.jpg"
    print(f"📍 S3 key: {s3_key}")
    
    # Upload to S3
    result = upload_file_to_s3(processed_image, s3_key, content_type)
    
    if result:
        print(f"✅ Successfully uploaded image to S3: {s3_key}")
    else:
        print(f"❌ Failed to upload image to S3: {s3_key}")
    
    return result

