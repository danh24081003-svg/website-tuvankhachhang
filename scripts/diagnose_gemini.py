import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from google import genai
from google.genai import types

from app.config import get_settings


PROMPT = "Chỉ trả lời đúng một từ: OK"


def safe_config() -> dict[str, Any]:
    settings = get_settings()
    uses_gemini_key = bool(settings.gemini_api_key and settings.gemini_api_key.strip())
    has_project = bool(
        settings.google_cloud_project
        and settings.google_cloud_project.strip()
        and settings.google_cloud_project.strip() != "your-project-id"
    )
    if uses_gemini_key:
        provider = "gemini-developer-api"
        vertex_ai = False
        auth = "GEMINI_API_KEY"
        model = settings.gemini_model
    elif has_project:
        provider = "vertex-ai"
        vertex_ai = True
        auth = "google-application-default-credentials"
        model = settings.vertex_model
    else:
        provider = "not-configured"
        vertex_ai = False
        auth = "missing"
        model = settings.gemini_model

    return {
        "provider": provider,
        "vertex_ai": vertex_ai,
        "auth_method": auth,
        "google_cloud_project_configured": has_project,
        "location": settings.google_cloud_location,
        "model": model,
        "fallback_model": settings.gemini_fallback_model or "",
        "timeout_ms": settings.gemini_timeout_ms,
    }


def create_client(config: dict[str, Any]):
    settings = get_settings()
    http_options = types.HttpOptions(timeout=settings.gemini_timeout_ms)
    if config["provider"] == "gemini-developer-api":
        return genai.Client(api_key=settings.gemini_api_key.strip(), http_options=http_options)
    if config["provider"] == "vertex-ai":
        return genai.Client(
            vertexai=True,
            project=settings.google_cloud_project.strip(),
            location=settings.google_cloud_location,
            http_options=http_options,
        )
    raise RuntimeError("AI provider is not configured")


def error_code(err: Exception) -> str:
    for attr in ("code", "status_code"):
        value = getattr(err, attr, None)
        if value:
            return str(value)
    response = getattr(err, "response", None)
    value = getattr(response, "status_code", None)
    if value:
        return str(value)
    text = str(err)
    for code in ["400", "401", "403", "404", "429", "500", "502", "503", "504"]:
        if code in text:
            return code
    return "UNKNOWN"


def sanitize_error(err: Exception) -> str:
    text = str(err)
    if len(text) > 900:
        return text[:900] + "..."
    return text


def test_model(client, model: str) -> dict[str, Any]:
    started = time.monotonic()
    try:
        response = client.models.generate_content(
            model=model,
            contents=[types.Content(role="user", parts=[types.Part(text=PROMPT)])],
            config=types.GenerateContentConfig(temperature=0, max_output_tokens=8),
        )
        return {
            "model": model,
            "result": "PASS",
            "http_error_code": "",
            "latency_ms": int((time.monotonic() - started) * 1000),
            "response": (getattr(response, "text", "") or "").strip(),
        }
    except Exception as err:
        return {
            "model": model,
            "result": "FAIL",
            "http_error_code": error_code(err),
            "latency_ms": int((time.monotonic() - started) * 1000),
            "error_type": err.__class__.__name__,
            "error_message": sanitize_error(err),
        }


def list_models(client) -> list[str]:
    names: list[str] = []
    try:
        for item in client.models.list():
            name = getattr(item, "name", "") or ""
            if name:
                names.append(name)
    except Exception as err:
        print(f"MODEL LIST: FAIL {error_code(err)} {err.__class__.__name__}")
        print(sanitize_error(err))
    return names


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--list-models", action="store_true")
    parser.add_argument("--candidate", action="append", default=[])
    args = parser.parse_args()

    config = safe_config()
    print(f"Provider: {config['provider']}")
    print(f"Vertex AI: {config['vertex_ai']}")
    print(f"Authentication method: {config['auth_method']}")
    print(f"Google Cloud Project: {'configured' if config['google_cloud_project_configured'] else 'missing'}")
    print(f"Location: {config['location']}")
    print(f"Model: {config['model']}")
    print(f"Fallback model configured: {bool(config['fallback_model'])}")

    try:
        client = create_client(config)
    except Exception as err:
        print("Result: FAIL")
        print(f"HTTP/error code: {error_code(err)}")
        print(f"Error type: {err.__class__.__name__}")
        print(sanitize_error(err))
        return 2

    models_to_test = [config["model"]]
    if config["fallback_model"]:
        models_to_test.append(config["fallback_model"])
    for candidate in args.candidate:
        if candidate not in models_to_test:
            models_to_test.append(candidate)

    if args.list_models:
        names = list_models(client)
        flash = [name for name in names if "flash" in name.lower()]
        print("Available Flash-like models:")
        print(json.dumps(flash[:50], ensure_ascii=False, indent=2))

    exit_code = 1
    for model in models_to_test:
        result = test_model(client, model)
        print("---")
        print(f"Provider: {config['provider']}")
        print(f"Location: {config['location']}")
        print(f"Model: {model}")
        print(f"Result: {result['result']}")
        print(f"HTTP/error code: {result.get('http_error_code', '')}")
        print(f"Latency ms: {result['latency_ms']}")
        if result["result"] == "PASS":
            print(f"Response: {result['response']}")
            exit_code = 0
        else:
            if result.get("http_error_code") == "503":
                print("PRIMARY MODEL: 503 UNAVAILABLE")
            print(f"Error type: {result.get('error_type')}")
            print(f"Google error message: {result.get('error_message')}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
