"""
Enterprise Cloud Storage Service
Provides S3 / MinIO / Local filesystem storage abstractions with pre-signed URLs
and multi-tenant path isolation.
"""

import io
import os
import shutil
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO, Optional, Union

logger = logging.getLogger(__name__)

class StorageProvider(ABC):
    """Abstract base class for cloud/local storage backends."""

    @abstractmethod
    def save_file(
        self,
        file_obj: Union[BinaryIO, bytes],
        destination_path: str,
        content_type: Optional[str] = None,
        tenant_id: str = "default",
    ) -> str:
        """Save a file and return its storage key/URI."""
        pass

    @abstractmethod
    def get_file(self, storage_key: str, tenant_id: str = "default") -> bytes:
        """Retrieve file content as bytes."""
        pass

    @abstractmethod
    def generate_presigned_url(
        self,
        storage_key: str,
        tenant_id: str = "default",
        expires_in_seconds: int = 3600,
    ) -> str:
        """Generate a pre-signed temporary URL for secure access."""
        pass

    @abstractmethod
    def delete_file(self, storage_key: str, tenant_id: str = "default") -> bool:
        """Delete a file from storage."""
        pass


class LocalDiskStorageProvider(StorageProvider):
    """Storage provider saving files to local disk under a base upload directory."""

    def __init__(self, base_dir: Optional[Union[str, Path]] = None):
        self.base_dir = Path(base_dir or (Path(__file__).parent.parent / "uploads"))
        self.base_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"LocalDiskStorageProvider initialized at {self.base_dir}")

    def _resolve_path(self, storage_key: str, tenant_id: str) -> Path:
        clean_key = storage_key.lstrip("/\\")
        path = self.base_dir / "tenants" / tenant_id / clean_key
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def save_file(
        self,
        file_obj: Union[BinaryIO, bytes],
        destination_path: str,
        content_type: Optional[str] = None,
        tenant_id: str = "default",
    ) -> str:
        target_path = self._resolve_path(destination_path, tenant_id)
        if isinstance(file_obj, bytes):
            with open(target_path, "wb") as f:
                f.write(file_obj)
        else:
            with open(target_path, "wb") as f:
                shutil.copyfileobj(file_obj, f)
        logger.info(f"File stored locally: {target_path} (tenant: {tenant_id})")
        return f"tenants/{tenant_id}/{destination_path.lstrip('/\\')}"

    def get_file(self, storage_key: str, tenant_id: str = "default") -> bytes:
        # Check if already prefixed with tenants/{tenant_id}
        if storage_key.startswith("tenants/"):
            target_path = self.base_dir / storage_key
        else:
            target_path = self._resolve_path(storage_key, tenant_id)

        if not target_path.exists():
            raise FileNotFoundError(f"Storage object not found: {storage_key}")

        with open(target_path, "rb") as f:
            return f.read()

    def generate_presigned_url(
        self,
        storage_key: str,
        tenant_id: str = "default",
        expires_in_seconds: int = 3600,
    ) -> str:
        # For local dev, returns a relative API download endpoint
        key = storage_key.lstrip("/\\")
        return f"/api/v1/storage/download/{key}"

    def delete_file(self, storage_key: str, tenant_id: str = "default") -> bool:
        if storage_key.startswith("tenants/"):
            target_path = self.base_dir / storage_key
        else:
            target_path = self._resolve_path(storage_key, tenant_id)

        if target_path.exists():
            target_path.unlink()
            return True
        return False


class S3StorageProvider(StorageProvider):
    """S3-compatible storage provider (AWS S3, MinIO, Wasabi, Cloudflare R2)."""

    def __init__(
        self,
        bucket_name: str,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        region_name: Optional[str] = None,
        endpoint_url: Optional[str] = None,
    ):
        try:
            import boto3
            from botocore.config import Config
        except ImportError:
            raise ImportError("boto3 is required for S3StorageProvider. Install with pip install boto3")

        self.bucket_name = bucket_name
        self.endpoint_url = endpoint_url
        session = boto3.session.Session()
        self.s3_client = session.client(
            "s3",
            region_name=region_name or os.getenv("AWS_REGION", "us-east-1"),
            aws_access_key_id=aws_access_key_id or os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=aws_secret_access_key or os.getenv("AWS_SECRET_ACCESS_KEY"),
            endpoint_url=endpoint_url or os.getenv("S3_ENDPOINT_URL"),
            config=Config(signature_version="s3v4"),
        )
        logger.info(f"S3StorageProvider initialized for bucket: {bucket_name}")

    def _resolve_key(self, storage_key: str, tenant_id: str) -> str:
        clean_key = storage_key.lstrip("/\\")
        if clean_key.startswith("tenants/"):
            return clean_key
        return f"tenants/{tenant_id}/{clean_key}"

    def save_file(
        self,
        file_obj: Union[BinaryIO, bytes],
        destination_path: str,
        content_type: Optional[str] = None,
        tenant_id: str = "default",
    ) -> str:
        key = self._resolve_key(destination_path, tenant_id)
        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type

        if isinstance(file_obj, bytes):
            buffer = io.BytesIO(file_obj)
            self.s3_client.upload_fileobj(buffer, self.bucket_name, key, ExtraArgs=extra_args)
        else:
            self.s3_client.upload_fileobj(file_obj, self.bucket_name, key, ExtraArgs=extra_args)

        logger.info(f"Uploaded {key} to s3://{self.bucket_name}/ (tenant: {tenant_id})")
        return key

    def get_file(self, storage_key: str, tenant_id: str = "default") -> bytes:
        key = self._resolve_key(storage_key, tenant_id)
        buffer = io.BytesIO()
        self.s3_client.download_fileobj(self.bucket_name, key, buffer)
        buffer.seek(0)
        return buffer.read()

    def generate_presigned_url(
        self,
        storage_key: str,
        tenant_id: str = "default",
        expires_in_seconds: int = 3600,
    ) -> str:
        key = self._resolve_key(storage_key, tenant_id)
        return self.s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket_name, "Key": key},
            ExpiresIn=expires_in_seconds,
        )

    def delete_file(self, storage_key: str, tenant_id: str = "default") -> bool:
        key = self._resolve_key(storage_key, tenant_id)
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
            return True
        except Exception as e:
            logger.error(f"Error deleting S3 object {key}: {e}")
            return False


# Singleton Storage Manager Factory
_storage_instance: Optional[StorageProvider] = None

def get_storage_provider() -> StorageProvider:
    """Retrieve the configured storage provider singleton."""
    global _storage_instance
    if _storage_instance is not None:
        return _storage_instance

    backend = os.getenv("STORAGE_BACKEND", "local").lower()
    bucket = os.getenv("S3_BUCKET_NAME")

    if backend == "s3" or (backend == "auto" and bucket):
        if not bucket:
            logger.warning("STORAGE_BACKEND is s3 but S3_BUCKET_NAME is unset; falling back to local disk.")
            _storage_instance = LocalDiskStorageProvider()
        else:
            try:
                _storage_instance = S3StorageProvider(bucket_name=bucket)
            except Exception as e:
                logger.error(f"Failed to initialize S3 storage ({e}); falling back to local disk storage.")
                _storage_instance = LocalDiskStorageProvider()
    else:
        _storage_instance = LocalDiskStorageProvider()

    return _storage_instance
