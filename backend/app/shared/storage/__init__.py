"""对象存储共享能力。"""

from app.shared.storage.client import (
    ObjectStream,
    StorageBucketMissingError,
    build_public_url,
    build_storage_key,
    check_storage_health,
    create_storage_client,
    ensure_storage_bucket_exists,
    fetch_object_bytes,
    open_object_stream,
    remove_object_best_effort,
    remove_objects_best_effort,
    upload_bytes,
)
from app.shared.storage.file_url import (
    build_public_file_url,
    build_signed_file_url,
    extract_storage_key_from_file_url,
    sign_file_request,
    sign_managed_file_url,
    sign_managed_file_urls_in_text,
    verify_signed_file_request,
)

__all__ = [
    "ObjectStream",
    "StorageBucketMissingError",
    "build_public_file_url",
    "build_public_url",
    "build_signed_file_url",
    "build_storage_key",
    "check_storage_health",
    "create_storage_client",
    "ensure_storage_bucket_exists",
    "extract_storage_key_from_file_url",
    "fetch_object_bytes",
    "open_object_stream",
    "remove_object_best_effort",
    "remove_objects_best_effort",
    "sign_file_request",
    "sign_managed_file_url",
    "sign_managed_file_urls_in_text",
    "upload_bytes",
    "verify_signed_file_request",
]
