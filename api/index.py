import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.main import app as _app  # noqa: E402

async def app(scope, receive, send):
    if scope.get("type") == "http":
        headers = dict(scope.get("headers", []))
        # Vercel supplies the original requested URI in x-matched-path
        matched_path = headers.get(b"x-matched-path", b"").decode("latin-1")
        if matched_path:
            clean_path = matched_path.split("?")[0].split("#")[0]
            scope["path"] = clean_path
            scope["raw_path"] = clean_path.encode("latin-1")
        elif scope.get("path", "").startswith("/api/index.py"):
            new_path = scope["path"][len("/api/index.py"):]
            scope["path"] = new_path if new_path.startswith("/") else ("/" + new_path if new_path else "/")
            scope["raw_path"] = scope["path"].encode("latin-1")
    await _app(scope, receive, send)
