import os
import re

found = []
for root, dirs, files in os.walk('.'):
    if any(p in root for p in ['.git', '__pycache__', '.pytest_cache', 'scratch', 'scratch_screenshots', 'scratch_hover', '.tmp-chrome', '.python', 'venv', '.venv']):
        continue
    for f in files:
        if f.endswith(('.py', '.js', '.html', '.json', '.css')):
            p = os.path.join(root, f)
            with open(p, 'r', encoding='utf-8', errors='ignore') as fp:
                txt = fp.read()
                # find D:\ or C:\ or \\ in non-regex
                if re.search(r'[A-Za-z]:\\', txt):
                    found.append((p, 'Windows drive path found'))

print("=== WINDOWS PATH CHECK ===")
if not found:
    print("NO WINDOWS-SPECIFIC ABSOLUTE PATHS FOUND IN CODEBASE! (Clean)")
else:
    for p, msg in found:
        print(f"{p}: {msg}")
