import re

with open('static/js/app.js', 'r', encoding='utf-8') as f:
    c = f.read()
print('API endpoints in app.js:', sorted(set(re.findall(r'[\'"](/api/[^\'"]+)[\'"]', c))))

with open('static/js/admin.js', 'r', encoding='utf-8') as f:
    c = f.read()
print('API endpoints in admin.js:', sorted(set(re.findall(r'[\'"](/api/[^\'"]+)[\'"]', c))))
