"""
Debug: Find the actual big_number_total plugin source and its parameters.
"""
import sys, json, os
sys.path.insert(0, '/app')
from superset.app import create_app
app = create_app()
app.app_context().push()

# Search for big_number in the Superset installation
import subprocess
result = subprocess.run(
    ['find', '/app', '-type', 'f', '-name', '*.js'],
    capture_output=True, text=True
)
js_files = result.stdout.strip().split('\n')
bn_files = [f for f in js_files if 'big_number' in f.lower() or 'BigNumber' in f]
print(f"JS files with big_number: {len(bn_files)}")
for f in bn_files[:10]:
    print(f"  {f}")

# Also check Python files
result = subprocess.run(
    ['find', '/app', '-type', 'f', '-name', '*.py'],
    capture_output=True, text=True
)
py_files = result.stdout.strip().split('\n')
bn_py = [f for f in py_files if 'big_number' in f.lower()]
print(f"\nPython files with big_number: {len(bn_py)}")
for f in bn_py:
    print(f"  {f}")
    # Read first 50 lines
    with open(f) as fh:
        content = fh.read()
        # Look for font_size or header references
        for line in content.split('\n'):
            if 'font' in line.lower() or 'header' in line.lower() or 'size' in line.lower():
                print(f"    {line.strip()}")
