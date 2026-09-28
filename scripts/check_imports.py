import os
import ast

imports = set()
for root, _, files in os.walk('app'):
    for f in files:
        if f.endswith('.py'):
            p = os.path.join(root, f)
            with open(p, 'r', encoding='utf-8') as fp:
                try:
                    tree = ast.parse(fp.read(), filename=p)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                imports.add(alias.name.split('.')[0])
                        elif isinstance(node, ast.ImportFrom):
                            if node.module and not node.module.startswith('.'):
                                imports.add(node.module.split('.')[0])
                except Exception as e:
                    print('Err:', p, e)

print('External/Standard library imports found in app:', sorted(imports))
