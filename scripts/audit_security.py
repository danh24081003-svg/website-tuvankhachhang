import os
import re

PATTERNS = {
    'API_KEY': r'(?i)(api[_-]?key|gemini[_-]?api[_-]?key|secret[_-]?key)\s*[:=]\s*[\'"][A-Za-z0-9_\-\.]{8,}[\'"]',
    'PRIVATE_KEY': r'-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----',
    'GOOGLE_SERVICE_ACCOUNT': r'\"type\":\s*\"service_account\"',
    'PASSWORD_HARDCODED': r'(?i)(password|admin[_-]?pass|db[_-]?password)\s*[:=]\s*[\'"][A-Za-z0-9@#$%!^&*()_\-\.]{5,}[\'"]',
    'WINDOWS_PATH': r'[a-zA-Z]:\\(?:[a-zA-Z0-9_\- ]+\\)+',
    'HARDCODED_LOCALHOST': r'http://127\.0\.0\.1|http://localhost',
}

findings = []
for root, dirs, files in os.walk('.'):
    if any(p in root for p in ['.git', '__pycache__', '.pytest_cache', 'scratch', 'scratch_screenshots', 'scratch_hover', '.tmp-chrome']):
        continue
    for f in files:
        if f.endswith(('.py', '.json', '.html', '.js', '.css', '.md', '.env', '.txt', '.sh', '.bat')):
            fpath = os.path.join(root, f)
            try:
                with open(fpath, 'r', encoding='utf-8', errors='ignore') as fp:
                    content = fp.read()
                    for p_name, pat in PATTERNS.items():
                        matches = re.findall(pat, content)
                        if matches:
                            findings.append((fpath, p_name, len(matches)))
            except Exception:
                pass

print("=== AUDIT RESULTS ===")
for path, p_name, count in findings:
    print(f"PATTERN FOUND: {path} | Type: {p_name} | Count: {count}")
