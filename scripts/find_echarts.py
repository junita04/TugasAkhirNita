"""
Search for ECharts plugin registrations in Superset 6.0.0 JS bundles.
"""
import os
import re

assets_dir = "/app/superset/static/assets"

# Search for echarts-related viz type keys
echarts_types = set()
all_plugin_keys = set()

for fname in os.listdir(assets_dir):
    if not fname.endswith(".js"):
        continue
    fpath = os.path.join(assets_dir, fname)
    try:
        with open(fpath, "r", errors="ignore") as f:
            content = f.read()
            
            # Search for ECharts plugin key patterns
            # Pattern 1: EchartsTimeseriesChartPlugin, key:"echarts_timeseries"
            matches1 = re.findall(r'key\s*:\s*"(echarts[^"]*)"', content)
            echarts_types.update(matches1)
            
            # Pattern 2: key:"something" near "echarts" or "plugin"
            # Look for registerPlugin calls
            matches2 = re.findall(r'\.registerPlugin\s*\(\s*\{[^}]*key\s*:\s*"([^"]+)"', content)
            all_plugin_keys.update(matches2)
            
            # Pattern 3: Look for chart type strings
            matches3 = re.findall(r'"(echarts_[a-z_]+)"', content)
            echarts_types.update(matches3)
            
    except:
        pass

print(f"ECharts types found ({len(echarts_types)}):")
for vt in sorted(echarts_types):
    print(f"  {vt}")

print(f"\nAll registered plugin keys ({len(all_plugin_keys)}):")
for pk in sorted(all_plugin_keys):
    print(f"  {pk}")

# Check specific types
print("\n--- Checking specific types ---")
check = ["echarts_bar", "echarts_timeseries_bar", "echarts_timeseries", 
         "echarts_pie", "pie", "big_number_total", "table", "heatmap", "histogram"]
for ct in check:
    in_echarts = ct in echarts_types
    in_all = ct in all_plugin_keys
    print(f"  {ct}: echarts={in_echarts}, plugins={in_all}")
