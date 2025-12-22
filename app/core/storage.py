"""
Storage abstraction layer for file uploads.

Supports local filesystem storage (development) and AWS S3 (production).
"""

import os
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# Try to import boto3 for S3 support
try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError

    S3_AVAILABLE = True
except ImportError:
    S3_AVAILABLE = False
    logger.warning("boto3 not installed. S3 storage unavailable.")


class StorageBackend(ABC):
    """Abstract base class for storage backends"""

    @abstractmethod
    def upload(
        self, file_content: bytes, filename: str, content_type: str
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Upload a file.

        Args:
            file_content: File bytes
            filename: Destination filename
            content_type: MIME type

        Returns:
            Tuple of (success, file_url, error_message)
        """
        pass

    @abstractmethod
    def delete(self, filename: str) -> Tuple[bool, Optional[str]]:
        """
        Delete a file.

        Args:
            filename: File to delete

        Returns:
            Tuple of (success, error_message)
        """
        pass

    @abstractmethod
    def exists(self, filename: str) -> bool:
        """Check if file exists"""
        pass

    @abstractmethod
    def get_url(self, filename: str) -> str:
        """Get public URL for file"""
        pass


class LocalStorage(StorageBackend):
    """Local filesystem storage (for development)"""

    def __init__(self, base_dir: str = "uploads"):
        """
        Initialize local storage.

        Args:
            base_dir: Base directory for uploads
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)

        # Create subdirectories
        for subdir in ["videos", "images", "files"]:
            (self.base_dir / subdir).mkdir(exist_ok=True)

        logger.info(f"Local storage initialized at {self.base_dir.absolute()}")

    def upload(
        self, file_content: bytes, filename: str, content_type: str
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """Upload file to local filesystem"""
        try:
            # Determine subdirectory based on content type
            if content_type.startswith("image/"):
                subdir = "images"
            elif content_type.startswith("video/"):
                subdir = "videos"
            else:
                subdir = "files"

            file_path = self.base_dir / subdir / filename

            # Write file
            with open(file_path, "wb") as f:
                f.write(file_content)

            # Return relative URL
            file_url = f"/uploads/{subdir}/{filename}"
            logger.info(f"File uploaded to local storage: {file_url}")

            return True, file_url, None

        except Exception as e:
            logger.error(f"Failed to upload file to local storage: {e}")
            return False, None, str(e)

    def delete(self, filename: str) -> Tuple[bool, Optional[str]]:
        """Delete file from local filesystem"""
        try:
            # Try each subdirectory
            for subdir in ["videos", "images", "files"]:
                file_path = self.base_dir / subdir / filename
                if file_path.exists():
                    os.remove(file_path)
                    logger.info(f"File deleted from local storage: {filename}")
                    return True, None

            return False, "File not found"

        except Exception as e:
            logger.error(f"Failed to delete file: {e}")
            return False, str(e)

    def exists(self, filename: str) -> bool:
        """Check if file exists in any subdirectory"""
        for subdir in ["videos", "images", "files"]:
            if (self.base_dir / subdir / filename).exists():
                return True
        return False

    def get_url(self, filename: str) -> str:
        """Get URL for file"""
        # Try to find in subdirectories
        for subdir in ["videos", "images", "files"]:
            if (self.base_dir / subdir / filename).exists():
                return f"/uploads/{subdir}/{filename}"
        return f"/uploads/files/{filename}"


class S3Storage(StorageBackend):
    """AWS S3 storage (for production)"""

    def __init__(
        self,
        bucket_name: str,
        region: str = "us-east-1",
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
    ):
        """
        Initialize S3 storage.

        Args:
            bucket_name: S3 bucket name
            region: AWS region
            access_key: AWS access key (uses environment if not provided)
            secret_key: AWS secret key (uses environment if not provided)
        """
        if not S3_AVAILABLE:
            raise ImportError(
                "boto3 is required for S3 storage. Install with: pip install boto3"
            )

        self.bucket_name = bucket_name
        self.region = region

        # Initialize S3 client
        try:
            if access_key and secret_key:
                self.s3_client = boto3.client(
                    "s3",
                    region_name=region,
                    aws_access_key_id=access_key,
                    aws_secret_access_key=secret_key,
                )
            else:
                # Use environment variables or IAM role
                self.s3_client = boto3.client("s3", region_name=region)

            # Verify bucket exists and is accessible
            self.s3_client.head_bucket(Bucket=bucket_name)
            logger.info(f"S3 storage initialized: s3://{bucket_name}")

        except NoCredentialsError:
            raise ValueError(
                "AWS credentials not found. Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY."
            )
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "404":
                raise ValueError(f"S3 bucket '{bucket_name}' not found")
            elif error_code == "403":
                raise ValueError(f"Access denied to S3 bucket '{bucket_name}'")
            else:
                raise ValueError(f"S3 error: {e}")

    def upload(
        self, file_content: bytes, filename: str, content_type: str
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """Upload file to S3"""
        try:
            # Determine S3 key (path) based on content type
            if content_type.startswith("image/"):
                s3_key = f"images/{filename}"
            elif content_type.startswith("video/"):
                s3_key = f"videos/{filename}"
            else:
                s3_key = f"files/{filename}"

            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=content_type,
                # Make file publicly readable (adjust based on your security requirements)
                # ACL='public-read'  # Uncomment if you want public access
            )

            # Generate URL
            file_url = (
                f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{s3_key}"
            )
            logger.info(f"File uploaded to S3: {file_url}")

            return True, file_url, None

        except ClientError as e:
            logger.error(f"Failed to upload file to S3: {e}")
            return False, None, str(e)

    def delete(self, filename: str) -> Tuple[bool, Optional[str]]:
        """Delete file from S3"""
        try:
            # Try all possible prefixes
            for prefix in ["images/", "videos/", "files/"]:
                s3_key = f"{prefix}{filename}"

                try:
                    self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
                    logger.info(f"File deleted from S3: {s3_key}")
                    return True, None
                except ClientError:
                    continue

            return False, "File not found"

        except Exception as e:
            logger.error(f"Failed to delete file from S3: {e}")
            return False, str(e)

    def exists(self, filename: str) -> bool:
        """Check if file exists in S3"""
        for prefix in ["images/", "videos/", "files/"]:
            s3_key = f"{prefix}{filename}"
            try:
                self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
                return True
            except ClientError:
                continue
        return False

    def get_url(self, filename: str) -> str:
        """Get public URL for file"""
        # Try to find the file
        for prefix in ["images/", "videos/", "files/"]:
            s3_key = f"{prefix}{filename}"
            if self.exists(s3_key.split("/")[-1]):
                return f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{s3_key}"

        # Default to files prefix
        return f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/files/{filename}"

    def get_presigned_url(self, filename: str, expiration: int = 3600) -> Optional[str]:
        """
        Generate a presigned URL for secure file access.

        Args:
            filename: File to generate URL for
            expiration: URL validity in seconds (default 1 hour)

        Returns:
            Presigned URL or None if file not found
        """
        for prefix in ["images/", "videos/", "files/"]:
            s3_key = f"{prefix}{filename}"
            try:
                self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)

                # Generate presigned URL
                url = self.s3_client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": self.bucket_name, "Key": s3_key},
                    ExpiresIn=expiration,
                )
                return url
            except ClientError:
                continue

        return None


# Global storage instance
_storage: Optional[StorageBackend] = None


def init_storage(backend: str = "local", **kwargs) -> StorageBackend:
    """
    Initialize the global storage backend.

    Args:
        backend: Storage backend type ('local' or 's3')
        **kwargs: Backend-specific configuration

    Returns:
        StorageBackend instance
    """
    global _storage

    if backend == "local":
        _storage = LocalStorage(**kwargs)
    elif backend == "s3":
        _storage = S3Storage(**kwargs)
    else:
        raise ValueError(f"Unknown storage backend: {backend}")

    return _storage


def get_storage() -> StorageBackend:
    """
    Get the global storage backend instance.

    Returns:
        StorageBackend instance (creates local storage if not initialized)
    """
    global _storage
    if _storage is None:
        _storage = LocalStorage()
    return _storage
