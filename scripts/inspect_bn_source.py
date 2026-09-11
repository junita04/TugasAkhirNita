"""
Inspect: Find the actual big_number_total JS source and understand font rendering.
"""
import sys, json, subprocess
sys.path.insert(0, '/app')
from superset.app import create_app
app = create_app()
app.app_context().push()

# Find the BigNumberTotal plugin JS file
result = subprocess.run(
    ['find', '/app', '-type', 'f', '-name', '*.js'],
    capture_output=True, text=True
)
js_files = result.stdout.strip().split('\n') if result.stdout.strip() else []

# Search for BigNumberTotal in JS files
for f in js_files:
    try:
        with open(f, 'r', errors='ignore') as fh:
            content = fh.read(50000)  # Read first 50KB
            if 'BigNumberTotal' in content or 'big_number_total' in content:
                print(f"Found in: {f}")
                # Look for font-related code
                for i, line in enumerate(content.split('\n')):
                    if 'font' in line.lower() and ('size' in line.lower() or 'header' in line.lower()):
                        print(f"  Line {i}: {line.strip()[:200]}")
    except:
        pass

# Also check the Python viz.py for big_number
print("\n--- Checking viz.py ---")
import os
viz_path = '/app/superset/viz.py'
if os.path.exists(viz_path):
    with open(viz_path) as fh:
        content = fh.read()
        # Find BigNumber related code
        in_big_number = False
        for i, line in enumerate(content.split('\n')):
            if 'class BigNumber' in line or 'big_number' in line:
                in_big_number = True
            if in_big_number:
                if 'font' in line.lower() or 'header' in line.lower() or 'size' in line.lower():
                    print(f"  Line {i}: {line.strip()[:200]}")
                if line.strip().startswith('class ') and 'BigNumber' not in line:
                    in_big_number = False
