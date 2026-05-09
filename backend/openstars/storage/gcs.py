"""Google Cloud Storage implementation."""

from openstars.storage.base import GameStorage
from openstars.storage.compression import decode_json, encode_json

try:
    from google.api_core.exceptions import NotFound, PreconditionFailed
    from google.cloud import storage as gcs_storage
except ImportError:  # pragma: no cover - exercised via configuration tests instead
    gcs_storage = None

    class NotFound(Exception):
        """Fallback exception used when google-cloud-storage is unavailable."""

    class PreconditionFailed(Exception):
        """Fallback exception used when google-cloud-storage is unavailable."""


class GCSStorage(GameStorage):
    """Store game data as gzipped JSON blobs in a Google Cloud Storage bucket."""

    def __init__(self, bucket_name: str) -> None:
        if not bucket_name:
            raise ValueError("GCS bucket name is required")
        if gcs_storage is None:
            raise RuntimeError("google-cloud-storage is not installed")
        self.bucket_name = bucket_name
        self.client = gcs_storage.Client()
        self.bucket = self.client.bucket(bucket_name)

    def _create_json_blob(self, name: str, data: str) -> None:
        try:
            self._upload(name, data, if_generation_match=0)
        except PreconditionFailed as exc:
            raise FileExistsError(f"Object already exists: {name}") from exc

    def _update_json_blob(self, name: str, data: str) -> None:
        self._upload(name, data)

    def _load_json_blob(self, name: str) -> str:
        try:
            # GCS can transparently decode objects with Content-Encoding: gzip.
            # Request the stored bytes so the adapter owns decompression.
            return decode_json(self.bucket.blob(name).download_as_bytes(raw_download=True))
        except NotFound as exc:
            raise FileNotFoundError(f"Object not found: {name}") from exc

    def _blob_exists(self, name: str) -> bool:
        return self.bucket.blob(name).exists()

    def _list_blob_names(self) -> list[str]:
        return sorted(blob.name for blob in self.client.list_blobs(self.bucket_name))

    def _upload(self, name: str, data: str, *, if_generation_match: int | None = None) -> None:
        blob = self.bucket.blob(name)
        blob.upload_from_string(
            encode_json(data),
            content_type="application/gzip",
            if_generation_match=if_generation_match,
        )
