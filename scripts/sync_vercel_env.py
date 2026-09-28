import os
import json
import secrets
import subprocess
import sys
from pathlib import Path
from dotenv import dotenv_values

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

env_path = Path(".env")
if not env_path.exists():
    print("Local .env not found!")
    sys.exit(1)

local_env = dotenv_values(".env")

# Generate new SECRET_KEY
prod_secret_key = secrets.token_hex(32)

env_vars_to_set = {
    "APP_ENV": "production",
    "SECRET_KEY": prod_secret_key,
    "VERTEX_MODEL": local_env.get("VERTEX_MODEL", "gemini-2.5-flash") or "gemini-2.5-flash",
    "GEMINI_MODEL": local_env.get("GEMINI_MODEL", "gemini-2.5-flash") or "gemini-2.5-flash",
    "GEMINI_TIMEOUT_MS": local_env.get("GEMINI_TIMEOUT_MS", "30000") or "30000",
}

# Check Google Cloud / Gemini configs
if local_env.get("GOOGLE_CLOUD_PROJECT"):
    env_vars_to_set["GOOGLE_CLOUD_PROJECT"] = local_env["GOOGLE_CLOUD_PROJECT"]

if local_env.get("GOOGLE_CLOUD_LOCATION"):
    env_vars_to_set["GOOGLE_CLOUD_LOCATION"] = local_env["GOOGLE_CLOUD_LOCATION"]

# Check for Service Account JSON file path
gac_path = local_env.get("GOOGLE_APPLICATION_CREDENTIALS")
if gac_path and os.path.exists(gac_path):
    try:
        with open(gac_path, "r", encoding="utf-8") as f:
            creds_data = json.load(f)
            env_vars_to_set["GOOGLE_CREDENTIALS_JSON"] = json.dumps(creds_data)
            if not env_vars_to_set.get("GOOGLE_CLOUD_PROJECT") and creds_data.get("project_id"):
                env_vars_to_set["GOOGLE_CLOUD_PROJECT"] = creds_data["project_id"]
        print("Found local service account JSON and prepared GOOGLE_CREDENTIALS_JSON (in-memory)")
    except Exception as e:
        print(f"Warning reading service account file: {e}")

if local_env.get("GEMINI_API_KEY"):
    env_vars_to_set["GEMINI_API_KEY"] = local_env["GEMINI_API_KEY"]

print(f"Total environment variables prepared: {len(env_vars_to_set)}")
for k in env_vars_to_set.keys():
    print(f"  - {k}: PREPARED")

# Function to add env var using npx vercel env add
for k, v in env_vars_to_set.items():
    if not v:
        continue
    # Add to production and preview
    for env_target in ["production", "preview"]:
        # We can echo value into npx vercel env add <name> <target>
        # Note: vercel env add <name> <target> reads from stdin
        cmd = ["npx.cmd" if os.name == "nt" else "npx", "vercel", "env", "add", k, env_target, "--force"]
        try:
            p = subprocess.run(cmd, input=v.encode("utf-8"), capture_output=True, check=False, shell=False)
            if p.returncode == 0:
                print(f"Successfully added/updated {k} ({env_target})")
            else:
                print(f"Note setting {k} ({env_target}): {p.stderr.decode('utf-8', errors='ignore').strip()}")
        except Exception as err:
            print(f"Error setting {k}: {err}")

print("All environment variables synced to Vercel!")
