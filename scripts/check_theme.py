"""
Check the Superset theme to understand font size calculations.
"""
import sys, json
sys.path.insert(0, '/app')
from superset.app import create_app
app = create_app()
app.app_context().push()

# Check the Superset theme
from superset import theme
print("=== Superset Theme ===")
if hasattr(theme, 'SUPerset_theme'):
    t = theme.SUPerset_theme
    print(f"Font sizes: {json.dumps({k:v for k,v in t.items() if 'font' in k.lower()}, indent=2)}")
elif hasattr(theme, 'superset_theme'):
    t = theme.superset_theme
    print(f"Font sizes: {json.dumps({k:v for k,v in t.items() if 'font' in k.lower()}, indent=2)}")

# Check the default theme
from superset.utils.core import get_theme
try:
    t = get_theme()
    print(f"\nDefault theme font sizes: {json.dumps({k:v for k,v in t.items() if 'font' in k.lower()}, indent=2)}")
except:
    pass

# Check the JS source for the font size calculation
import subprocess
result = subprocess.run(
    ['grep', '-r', 'fontSize', '/app/superset/static/assets/3397.e50fe988a9ae924cbe1f.entry.js'],
    capture_output=True, text=True
)
lines = result.stdout.strip().split('\n')[:20]
print(f"\n--- JS fontSize references ---")
for l in lines:
    print(f"  {l[:200]}")

# Check for the header_font_size parameter handling
result = subprocess.run(
    ['grep', '-r', 'header_font_size', '/app/superset/static/assets/'],
    capture_output=True, text=True
)
lines = result.stdout.strip().split('\n')[:10]
print(f"\n--- header_font_size in JS ---")
for l in lines:
    print(f"  {l[:200]}")
