import logging
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.main import app as _app  # noqa: E402

logger = logging.getLogger("uvicorn.error")

async def app(scope, receive, send):
    if scope.get("type") == "http":
        headers = dict(scope.get("headers", []))
        raw_headers = {k.decode('latin-1'): v.decode('latin-1') for k, v in headers.items()}
        logger.info("VERCEL_SCOPE_PATH: %s", scope.get("path"))
        logger.info("VERCEL_HEADERS: %s", raw_headers)

        # Check for original URL headers
        original_uri = (
            raw_headers.get("x-vercel-matched-path")
            or raw_headers.get("x-now-route-matches")
            or raw_headers.get("x-forwarded-uri")
            or raw_headers.get("x-forwarded-path")
            or scope.get("path", "")
        )

        # If path ends up as /api/index.py or starts with /api/index.py, strip it
        if original_uri.startswith("/api/index.py"):
            original_uri = original_uri[len("/api/index.py"):]

        clean_path = (original_uri.split("?")[0].split("#")[0]).strip()
        if not clean_path.startswith("/"):
            clean_path = "/" + clean_path

        logger.info("RESOLVED_PATH: %s", clean_path)
        scope["path"] = clean_path
        scope["raw_path"] = clean_path.encode("latin-1")

    await _app(scope, receive, send)
