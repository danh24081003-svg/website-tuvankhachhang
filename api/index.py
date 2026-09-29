import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.main import app as fastapi_app


async def app(scope, receive, send):
    if scope.get("type") == "http":
        path = scope.get("path", "")
        headers = dict(scope.get("headers", []))
        
        # Check if Vercel provided original matched path
        matched = (
            headers.get(b"x-matched-path", b"").decode("latin-1")
            or headers.get(b"x-forwarded-uri", b"").decode("latin-1")
            or headers.get(b"x-invoke-path", b"").decode("latin-1")
        )
        if matched and not matched.startswith("/api/index"):
            scope["path"] = matched
            scope["raw_path"] = matched.encode("latin-1")
        elif path == "/api/index.py" or path == "/api/index" or path == "/api":
            scope["path"] = "/"
            scope["raw_path"] = b"/"
        elif path.startswith("/api/index.py/"):
            rest = path[len("/api/index.py"):]
            scope["path"] = rest
            scope["raw_path"] = rest.encode("latin-1")

    await fastapi_app(scope, receive, send)
