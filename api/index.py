import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.main import app as _app  # noqa: E402

async def app(scope, receive, send):
    if scope.get("type") == "http":
        path = scope.get("path", "")
        if path.startswith("/api/index.py"):
            new_path = path[len("/api/index.py"):]
            scope["path"] = new_path if new_path.startswith("/") else ("/" + new_path if new_path else "/")
            scope["raw_path"] = scope["path"].encode("ascii")
    await _app(scope, receive, send)
