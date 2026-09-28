import os
import re
from pathlib import Path

# Check static file references in templates, css, js
static_refs = set()
for root, _, files in os.walk('.'):
    if any(p in root for p in ['.git', '__pycache__', '.pytest_cache', 'scratch', 'scratch_screenshots', 'scratch_hover', '.tmp-chrome', '.python', 'venv', '.venv']):
        continue
    for f in files:
        if f.endswith(('.html', '.js', '.css', '.py')):
            p = os.path.join(root, f)
            with open(p, 'r', encoding='utf-8', errors='ignore') as fp:
                txt = fp.read()
                matches = re.findall(r'[\'"](/static/[^\'"]+)[\'"]', txt)
                for m in matches:
                    clean_m = m.split('?')[0].split('#')[0]
                    static_refs.add((p, clean_m))

print(f"Total static references found: {len(static_refs)}")

# Build case-sensitive file tree of static/
static_files_on_disk = {}
for root, dirs, files in os.walk('static'):
    for f in files:
        full = os.path.join(root, f).replace('\\', '/')
        static_files_on_disk['/' + full] = full

mismatches = []
missing = []
for src_file, ref in static_refs:
    # Ignore dynamic paths like /static/uploads/... that are generated or upload placeholders
    if ref.startswith('/static/uploads/'):
        continue
    if ref in static_files_on_disk:
        continue
    # Check if case-insensitive match exists
    lower_map = {k.lower(): k for k in static_files_on_disk.keys()}
    if ref.lower() in lower_map:
        mismatches.append((src_file, ref, lower_map[ref.lower()]))
    else:
        missing.append((src_file, ref))

print("=== CASE MISMATCHES ===")
for src, ref, actual in mismatches:
    print(f"File {src}: reference '{ref}' differs in case from disk '{actual}'")

print("=== MISSING STATIC FILES ===")
for src, ref in missing:
    print(f"File {src}: reference '{ref}' NOT found on disk!")
