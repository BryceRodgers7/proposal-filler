import boto3
import streamlit as st
from botocore.exceptions import ClientError, NoCredentialsError
import os


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
        print("⚠️ S3 client not available. Cannot upload file.")
        return None
    
    try:
        # Upload file to S3
        extra_args = {}
        if content_type:
            extra_args['ContentType'] = content_type
        
        s3_client.put_object(
            Bucket=bucket_name,
            Key=file_name,
            Body=file_data,
            **extra_args
        )
        
        # Return the S3 key (path)
        return file_name
    except ClientError as e:
        print(f"⚠️ Error uploading file to S3: {str(e)}")
        return None
    except Exception as e:
        print(f"⚠️ Unexpected error uploading file to S3: {str(e)}")
        return None


def get_s3_url(s3_key: str) -> str:
    """
    Generate a URL for an S3 object.
    
    Args:
        s3_key: The S3 key (path) of the object
    
    Returns:
        S3 URL string
    """
    s3_client, bucket_name = get_s3_client()
    
    if s3_client is None or bucket_name is None:
        return None
    
    try:
        # Get the region from the client
        region = s3_client.meta.region_name
        return f"https://{bucket_name}.s3.{region}.amazonaws.com/{s3_key}"
    except Exception as e:
        print(f"⚠️ Error generating S3 URL: {str(e)}")
        return None


def is_s3_available() -> bool:
    """
    Check if S3 is available and configured.
    
    Returns:
        True if S3 is available, False otherwise
    """
    s3_client, bucket_name = get_s3_client()
    return s3_client is not None and bucket_name is not None

