import os
import re
import subprocess
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# List all files that git would track
cmd = ["git", "status", "--porcelain"]
proc = subprocess.run(cmd, capture_output=True, text=True, check=True)

untracked_or_changed = []
for line in proc.stdout.splitlines():
    status = line[:2]
    path = line[3:].strip()
    untracked_or_changed.append(path)

print("Files to be included/tracked by Git:")
for p in untracked_or_changed:
    print(f"  - {p}")

# Secret scanning on these paths
PATTERNS = {
    'PRIVATE_KEY': r'-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----',
    'GOOGLE_SERVICE_ACCOUNT': r'\"type\":\s*\"service_account\"',
    'HARDCODED_API_KEY': r'(?i)(AIza[0-9A-Za-z-_]{35})',
}

found_secrets = []
for root, dirs, files in os.walk('.'):
    # Skip ignored
    if any(x in root for x in ['.git', '.python', 'venv', '.venv', '__pycache__', 'scratch', '.tmp-chrome', '.tmp-admin-tests']):
        continue
    for f in files:
        if f.endswith(('.db', '.sqlite', '.webp', '.jpg', '.png', '.tmp')):
            continue
        if f == '.env':
            continue
        fp = os.path.join(root, f)
        try:
            with open(fp, 'r', encoding='utf-8', errors='ignore') as s:
                content = s.read()
                for s_name, pat in PATTERNS.items():
                    if re.search(pat, content):
                        found_secrets.append((fp, s_name))
        except Exception:
            pass

print("\n=== STAGED FILES SECRET SCAN RESULT ===")
if not found_secrets:
    print("SECRETS IN SOURCE: SAFE ✅ (No private keys, no API keys, no service account JSONs found)")
else:
    print("ACTION REQUIRED! Secrets found in:")
    for fp, st in found_secrets:
        print(f"  - {fp} ({st})")
