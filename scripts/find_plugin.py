"""
Debug: Find the BigNumberTotal plugin in node_modules or superset-frontend.
"""
import sys, json, subprocess
sys.path.insert(0, '/app')
from superset.app import create_app
app = create_app()
app.app_context().push()

# Search for BigNumber in node_modules
result = subprocess.run(
    ['find', '/app', '-type', 'd', '-name', '*BigNumber*'],
    capture_output=True, text=True
)
dirs = result.stdout.strip().split('\n') if result.stdout.strip() else []
print(f"BigNumber directories: {len(dirs)}")
for d in dirs:
    print(f"  {d}")

# Search for big_number in Python packages
result = subprocess.run(
    ['find', '/app/.venv', '-type', 'f', '-name', '*.py', '-path', '*big_number*'],
    capture_output=True, text=True
)
py_files = result.stdout.strip().split('\n') if result.stdout.strip() else []
print(f"\nPython big_number files: {len(py_files)}")
for f in py_files:
    print(f"  {f}")

# Check the superset package for big_number plugin
result = subprocess.run(
    ['find', '/app/.venv', '-type', 'd', '-name', '*plugin*'],
    capture_output=True, text=True
)
plugin_dirs = result.stdout.strip().split('\n') if result.stdout.strip() else []
print(f"\nPlugin directories: {len(plugin_dirs)}")
for d in plugin_dirs[:20]:
    if 'big' in d.lower() or 'number' in d.lower():
        print(f"  {d}")

# Check the actual superset-frontend build
result = subprocess.run(
    ['find', '/app', '-type', 'f', '-name', '*.js.map', '-path', '*big*'],
    capture_output=True, text=True
)
maps = result.stdout.strip().split('\n') if result.stdout.strip() else []
print(f"\nJS map files: {len(maps)}")
for m in maps[:5]:
    print(f"  {m}")

# Try a different approach - check the chart registry
from superset.charts.schemas import ChartDataQueryContextSchema
print("\n--- Chart registry ---")
from superset import registry
print(f"Registry: {registry}")
