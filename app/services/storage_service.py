import io
import logging
import os
import secrets
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from fastapi import HTTPException, UploadFile, status

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

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


def optimize_image_to_webp(content: bytes, max_dimension: int = 2400, quality: int = 85) -> tuple[bytes, str, int, int]:
    """Validate image bytes with Pillow, preserve aspect ratio, and convert to WebP."""
    if not HAS_PILLOW:
        if content.startswith(b"\xff\xd8\xff"):
            return content, "jpg", 1200, 900
        elif content.startswith(b"\x89PNG\r\n\x1a\n"):
            return content, "png", 1200, 900
        elif content.startswith(b"RIFF") and b"WEBP" in content[:16]:
            return content, "webp", 1200, 900
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

    w, h = image.size
    output = io.BytesIO()
    image.save(output, format="WEBP", quality=quality, method=6)
    return output.getvalue(), "webp", w, h


def optimize_chat_image(content: bytes, max_dimension: int = 2048, quality: int = 85) -> tuple[bytes, str, int, int]:
    """
    Validate, auto-orient EXIF, resize if needed, and optimize chat image to WebP.
    Returns: (optimized_bytes, 'webp', width, height)
    """
    return optimize_image_to_webp(content, max_dimension=max_dimension, quality=quality)


class StorageProvider:
    async def upload(self, file: UploadFile, prefix: str = "site", db: "Session | None" = None) -> StoredFile:
        raise NotImplementedError

    def upload_bytes(
        self,
        content: bytes,
        original_filename: str = "",
        prefix: str = "site",
        db: "Session | None" = None,
    ) -> StoredFile:
        raise NotImplementedError

    def get_bytes(self, key_or_url: str, db: "Session | None" = None) -> bytes | None:
        raise NotImplementedError

    def delete(self, url: str, db: "Session | None" = None) -> None:
        raise NotImplementedError

    def get_url(self, filename: str) -> str:
        raise NotImplementedError


class DatabaseStorageProvider(StorageProvider):
    """
    Production-ready persistent storage provider that stores media in Neon PostgreSQL (or SQLite).
    Resilient to serverless cold starts, container recycles, git pushes, and Vercel redeployments.
    """

    def __init__(self, db: "Session | None" = None) -> None:
        self.settings = get_settings()
        self.max_bytes = self.settings.upload_max_bytes
        self._db = db

    def _get_db(self, db: "Session | None" = None) -> tuple["Session", bool]:
        if db is not None:
            return db, False
        if self._db is not None:
            return self._db, False
        from app.database import SessionLocal

        return SessionLocal(), True

    async def upload(self, file: UploadFile, prefix: str = "site", db: "Session | None" = None) -> StoredFile:
        content = await file.read()
        return self.upload_bytes(
            content=content,
            original_filename=file.filename or "",
            prefix=prefix,
            db=db,
        )

    def upload_bytes(
        self,
        content: bytes,
        original_filename: str = "",
        prefix: str = "site",
        db: "Session | None" = None,
    ) -> StoredFile:
        if len(content) > self.max_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Ảnh vượt quá giới hạn 5MB.",
            )

        optimized_bytes, extension, w, h = optimize_image_to_webp(content)
        clean_prefix = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in prefix)[:40]
        filename = f"{clean_prefix}-{secrets.token_hex(8)}.{extension}"

        from app.models import StoredMedia
        from sqlalchemy import select

        session, should_close = self._get_db(db)
        try:
            # Check if key already exists, update or insert
            existing = session.scalars(select(StoredMedia).where(StoredMedia.key == filename)).first()
            if existing:
                existing.filename = original_filename or filename
                existing.mime_type = f"image/{extension}"
                existing.file_size = len(optimized_bytes)
                existing.width = w
                existing.height = h
                existing.data = optimized_bytes
            else:
                media = StoredMedia(
                    key=filename,
                    filename=original_filename or filename,
                    mime_type=f"image/{extension}",
                    file_size=len(optimized_bytes),
                    width=w,
                    height=h,
                    data=optimized_bytes,
                )
                session.add(media)
            session.commit()
        finally:
            if should_close:
                session.close()

        url = self.get_url(filename)
        return StoredFile(filename=filename, url=url, path=None)

    def delete(self, url: str, db: "Session | None" = None) -> None:
        if not url:
            return
        filename = Path(url.split("?")[0]).name
        from app.models import StoredMedia
        from sqlalchemy import select

        session, should_close = self._get_db(db)
        try:
            media = session.scalars(select(StoredMedia).where(StoredMedia.key == filename)).first()
            if media:
                session.delete(media)
                session.commit()
        except Exception as exc:
            logger.warning("Không thể xóa media DB %s: %s", filename, exc)
        finally:
            if should_close:
                session.close()

    def get_bytes(self, key_or_url: str, db: "Session | None" = None) -> bytes | None:
        if not key_or_url:
            return None
        filename = Path(key_or_url.split("?")[0]).name
        from app.models import StoredMedia
        from sqlalchemy import select

        session, should_close = self._get_db(db)
        try:
            media = session.scalars(select(StoredMedia).where(StoredMedia.key == filename)).first()
            if media:
                return media.data
            return None
        finally:
            if should_close:
                session.close()

    def get_url(self, filename: str) -> str:
        return f"/api/media/{filename}"


class LocalStorageProvider(StorageProvider):
    """
    Local filesystem storage provider for standalone offline local development.
    """

    def __init__(self) -> None:
        settings = get_settings()
        if os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
            self.upload_dir = Path("/tmp/static/uploads")
        else:
            self.upload_dir = Path(settings.upload_dir)
        self.url_prefix = settings.upload_url_prefix.rstrip("/")
        self.max_bytes = settings.upload_max_bytes
        try:
            self.upload_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            self.upload_dir = Path("/tmp/static/uploads")
            self.upload_dir.mkdir(parents=True, exist_ok=True)

    async def upload(self, file: UploadFile, prefix: str = "site", db: "Session | None" = None) -> StoredFile:
        content = await file.read()
        return self.upload_bytes(
            content=content,
            original_filename=file.filename or "",
            prefix=prefix,
            db=db,
        )

    def upload_bytes(
        self,
        content: bytes,
        original_filename: str = "",
        prefix: str = "site",
        db: "Session | None" = None,
    ) -> StoredFile:
        if len(content) > self.max_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Ảnh vượt quá giới hạn 5MB.",
            )

        optimized_bytes, extension, w, h = optimize_image_to_webp(content)
        clean_prefix = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in prefix)[:40]
        filename = f"{clean_prefix}-{secrets.token_hex(8)}.{extension}"
        target = self.upload_dir / filename
        target.write_bytes(optimized_bytes)
        return StoredFile(filename=filename, url=self.get_url(filename), path=target)

    def delete(self, url: str, db: "Session | None" = None) -> None:
        if not url:
            return
        filename = Path(url.split("?")[0]).name
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

    def get_bytes(self, key_or_url: str, db: "Session | None" = None) -> bytes | None:
        if not key_or_url:
            return None
        filename = Path(key_or_url.split("?")[0]).name
        target = self.upload_dir / filename
        if target.exists() and target.is_file():
            return target.read_bytes()
        return None

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

    async def upload(self, file: UploadFile, prefix: str = "site", db: "Session | None" = None) -> StoredFile:
        content = await file.read()
        return self.upload_bytes(
            content=content,
            original_filename=file.filename or "",
            prefix=prefix,
            db=db,
        )

    def upload_bytes(
        self,
        content: bytes,
        original_filename: str = "",
        prefix: str = "site",
        db: "Session | None" = None,
    ) -> StoredFile:
        if len(content) > self.max_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Ảnh vượt quá giới hạn 5MB.",
            )

        optimized_bytes, extension, w, h = optimize_image_to_webp(content)
        clean_prefix = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in prefix)[:40]
        filename = f"{clean_prefix}-{secrets.token_hex(8)}.{extension}"

        _, bucket = self._get_client_and_bucket()
        blob = bucket.blob(filename)
        blob.upload_from_string(optimized_bytes, content_type="image/webp")

        url = self.get_url(filename)
        return StoredFile(filename=filename, url=url, path=None)

    def delete(self, url: str, db: "Session | None" = None) -> None:
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

    def get_bytes(self, key_or_url: str, db: "Session | None" = None) -> bytes | None:
        if not key_or_url or not self.bucket_name:
            return None
        filename = key_or_url.split(f"/{self.bucket_name}/")[-1].split("?")[0]
        try:
            _, bucket = self._get_client_and_bucket()
            blob = bucket.blob(filename)
            if blob.exists():
                return blob.download_as_bytes()
        except Exception as exc:
            logger.warning("Không thể đọc file GCS %s: %s", filename, exc)
        return None

    def get_url(self, filename: str) -> str:
        return f"https://storage.googleapis.com/{self.bucket_name}/{filename}"


def get_storage_provider(db: "Session | None" = None) -> StorageProvider:
    settings = get_settings()
    # Check if explicitly configured for GCS
    if settings.upload_storage.lower() == "gcs" and settings.gcs_bucket_name:
        return GoogleCloudStorageProvider()
    # Check if explicitly configured for local filesystem
    if settings.upload_storage.lower() == "local" and not os.environ.get("VERCEL"):
        try:
            (BASE_DIR / "static" / "uploads").mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        return LocalStorageProvider()
    # Default: DatabaseStorageProvider (Neon PostgreSQL / SQLite persistent storage)
    return DatabaseStorageProvider(db=db)
