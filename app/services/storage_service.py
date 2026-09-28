import io
import logging
import secrets
from dataclasses import dataclass
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

try:
    from PIL import Image, ImageOps, UnidentifiedImageError
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False
    Image = None
    ImageOps = None
    UnidentifiedImageError = Exception

from app.config import BASE_DIR, get_settings


logger = logging.getLogger(__name__)

ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}


@dataclass(frozen=True)
class StoredFile:
    filename: str
    url: str
    path: Path | None = None


def optimize_image_to_webp(content: bytes, max_dimension: int = 2400, quality: int = 85) -> tuple[bytes, str]:
    """Validate image bytes with Pillow, preserve aspect ratio, and convert to WebP."""
    if not HAS_PILLOW:
        # Fallback if Pillow is ever uninstalled
        if content.startswith(b"\xff\xd8\xff"):
            return content, "jpg"
        elif content.startswith(b"\x89PNG\r\n\x1a\n"):
            return content, "png"
        elif content.startswith(b"RIFF") and b"WEBP" in content[:16]:
            return content, "webp"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Chỉ hỗ trợ file ảnh định dạng JPG, PNG hoặc WebP.",
        )

    try:
        image = Image.open(io.BytesIO(content))
        image.load()
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tập tin tải lên không phải là ảnh hợp lệ hoặc đã bị lỗi.",
        ) from exc

    if (image.format or "").upper() not in ALLOWED_IMAGE_FORMATS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Chỉ hỗ trợ file ảnh định dạng JPG, PNG hoặc WebP.",
        )

    # Correct orientation based on EXIF tags if present
    try:
        image = ImageOps.exif_transpose(image)
    except Exception:
        pass

    # Ensure color mode is compatible with WebP
    if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
        image = image.convert("RGBA")
    elif image.mode != "RGB":
        image = image.convert("RGB")

    # Resize while strictly preserving aspect ratio without distortion
    if max(image.size) > max_dimension:
        image.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)

    output = io.BytesIO()
    image.save(output, format="WEBP", quality=quality, method=6)
    return output.getvalue(), "webp"


class StorageProvider:
    async def upload(self, file: UploadFile, prefix: str = "site") -> StoredFile:
        raise NotImplementedError

    def delete(self, url: str) -> None:
        raise NotImplementedError

    def get_url(self, filename: str) -> str:
        raise NotImplementedError


class LocalStorageProvider(StorageProvider):
    def __init__(self) -> None:
        settings = get_settings()
        self.upload_dir = Path(settings.upload_dir)
        self.url_prefix = settings.upload_url_prefix.rstrip("/")
        self.max_bytes = settings.upload_max_bytes
        try:
            self.upload_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            self.upload_dir = Path("/tmp/static/uploads")
            self.upload_dir.mkdir(parents=True, exist_ok=True)

    async def upload(self, file: UploadFile, prefix: str = "site") -> StoredFile:
        content = await file.read()
        if len(content) > self.max_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Ảnh vượt quá giới hạn 5MB.",
            )

        optimized_bytes, extension = optimize_image_to_webp(content)

        clean_prefix = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in prefix)[:40]
        filename = f"{clean_prefix}-{secrets.token_hex(10)}.{extension}"
        target = self.upload_dir / filename
        target.write_bytes(optimized_bytes)
        return StoredFile(filename=filename, url=self.get_url(filename), path=target)

    def delete(self, url: str) -> None:
        if not url or not url.startswith(self.url_prefix):
            return
        filename = Path(url).name
        target = (self.upload_dir / filename).resolve()
        try:
            target.relative_to(self.upload_dir.resolve())
        except ValueError:
            return
        if target.exists() and target.is_file():
            try:
                target.unlink()
            except OSError as err:
                logger.warning("Không thể xóa file %s: %s", target, err)

    def get_url(self, filename: str) -> str:
        return f"{self.url_prefix}/{filename}"


class GoogleCloudStorageProvider(StorageProvider):
    def __init__(self) -> None:
        settings = get_settings()
        self.bucket_name = settings.gcs_bucket_name
        self.project = settings.google_cloud_project
        self.max_bytes = settings.upload_max_bytes

    def _get_client_and_bucket(self):
        if not self.bucket_name:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Google Cloud Storage chưa được cấu hình (thiếu GCS_BUCKET_NAME).",
            )
        try:
            from google.cloud import storage

            client = storage.Client(project=self.project)
            bucket = client.bucket(self.bucket_name)
            return client, bucket
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Lỗi khởi tạo Google Cloud Storage: {exc}",
            ) from exc

    async def upload(self, file: UploadFile, prefix: str = "site") -> StoredFile:
        content = await file.read()
        if len(content) > self.max_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Ảnh vượt quá giới hạn 5MB.",
            )

        optimized_bytes, extension = optimize_image_to_webp(content)
        clean_prefix = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in prefix)[:40]
        filename = f"{clean_prefix}-{secrets.token_hex(10)}.{extension}"

        _, bucket = self._get_client_and_bucket()
        blob = bucket.blob(filename)
        blob.upload_from_string(optimized_bytes, content_type="image/webp")

        url = self.get_url(filename)
        return StoredFile(filename=filename, url=url, path=None)

    def delete(self, url: str) -> None:
        if not url or not self.bucket_name or self.bucket_name not in url:
            return
        filename = url.split(f"/{self.bucket_name}/")[-1].split("?")[0]
        try:
            _, bucket = self._get_client_and_bucket()
            blob = bucket.blob(filename)
            if blob.exists():
                blob.delete()
        except Exception as exc:
            logger.warning("Không thể xóa file GCS %s: %s", filename, exc)

    def get_url(self, filename: str) -> str:
        return f"https://storage.googleapis.com/{self.bucket_name}/{filename}"


def get_storage_provider() -> StorageProvider:
    settings = get_settings()
    if settings.upload_storage.lower() == "gcs" and settings.gcs_bucket_name:
        return GoogleCloudStorageProvider()
    (BASE_DIR / "static" / "uploads").mkdir(parents=True, exist_ok=True)
    return LocalStorageProvider()


def optimize_chat_image(content: bytes, max_dimension: int = 2048, quality: int = 85) -> tuple[bytes, str, int, int]:
    """
    Validate, auto-orient EXIF, resize if needed, and optimize chat image to WebP.
    Returns: (optimized_bytes, 'webp', width, height)
    """
    if not HAS_PILLOW:
        raise HTTPException(status_code=500, detail="Thư viện xử lý ảnh chưa sẵn sàng.")
    try:
        image = Image.open(io.BytesIO(content))
        image.load()
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tập tin tải lên không phải là ảnh hợp lệ hoặc đã bị lỗi.",
        ) from exc

    if (image.format or "").upper() not in ALLOWED_IMAGE_FORMATS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Chỉ hỗ trợ file ảnh định dạng JPG, PNG hoặc WebP.",
        )

    try:
        image = ImageOps.exif_transpose(image)
    except Exception:
        pass

    if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
        image = image.convert("RGBA")
    elif image.mode != "RGB":
        image = image.convert("RGB")

    if max(image.size) > max_dimension:
        image.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)

    w, h = image.size
    output = io.BytesIO()
    image.save(output, format="WEBP", quality=quality, method=6)
    return output.getvalue(), "webp", w, h

