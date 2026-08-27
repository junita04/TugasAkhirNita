"""
Find registered viz types in Superset 6.0.0 frontend.
Run inside the Superset container.
"""
import os
import re

# Find JS files with "echarts" references
assets_dir = "/app/superset/static/assets"
if not os.path.exists(assets_dir):
    # Try alternative paths
    for path in ["/app/superset/static/assets", "/app/superset/static", "/app/static/assets"]:
        if os.path.exists(path):
            assets_dir = path
            break

print(f"Assets dir: {assets_dir}")

# Search for viz type registrations in JS bundles
viz_types_found = set()
for fname in os.listdir(assets_dir):
    if not fname.endswith(".js"):
        continue
    fpath = os.path.join(assets_dir, fname)
    try:
        with open(fpath, "r", errors="ignore") as f:
            content = f.read()
            # Look for viz type key registrations
            # Pattern: key:"viz_type_name" or "viz_type":"name"
            matches = re.findall(r'key:"([a-z][a-z_]+)"', content)
            for m in matches:
                if len(m) > 3 and "_" in m or "echarts" in m or "chart" in m:
                    viz_types_found.add(m)
    except:
        pass

print(f"\nPotential viz type keys found ({len(viz_types_found)}):")
for vt in sorted(viz_types_found):
    print(f"  {vt}")

# Also check for the specific error-causing types
print("\n--- Checking specific types ---")
check_types = ["echarts_bar", "echarts_timeseries_bar", "bar", "dist_bar", "bar_chart"]
for ct in check_types:
    if ct in viz_types_found:
        print(f"  {ct}: FOUND in JS bundles")
    else:
        print(f"  {ct}: NOT FOUND in JS bundles")
