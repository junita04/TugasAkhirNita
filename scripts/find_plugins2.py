"""
Find the EXACT viz types registered in Superset 6.0.0 frontend.
Use the Superset app context to enumerate the plugin registry.
"""
import requests
import json

BASE = "http://localhost:8088"

def api():
    s = requests.Session()
    r = s.post(f"{BASE}/api/v1/security/login",
               json={"username": "admin", "password": "change-me", "provider": "db"})
    token = r.json()["access_token"]
    s.headers.update({"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    r0 = s.get(f"{BASE}/api/v1/security/csrf_token/")
    s.headers.update({"X-CSRFToken": r0.json()["result"], "Referer": BASE})
    return s

def main():
    s = api()
    
    # Try the Superset explore page which lists all viz types
    # The explore page loads the viz type picker
    r = s.get(f"{BASE}/explore/")
    html = r.text
    
    # Look for registered plugin keys in the HTML/JS
    import re
    
    # The Superset frontend uses webpack chunks. Let's search for "viz_type" patterns
    # in all accessible JS files
    
    # First, find all JS chunk files from the HTML
    js_refs = re.findall(r'"/static/assets/([^"]+\.js)"', html)
    print(f"JS files referenced in explore page: {len(js_refs)}")
    
    # Download the main bundle and search for viz type keys
    # The main bundle is usually the one with the most content
    
    # Alternative: Use the Superset REST API to check if a chart type is valid
    # by creating a chart with it and checking if the explore endpoint accepts it
    
    # Most reliable: Check what the Superset server-side viz registry has
    r2 = s.get(f"{BASE}/api/v1/chart/", params={"q": json.dumps({"page_size": 1})})
    
    # Try to find the viz type registry via the Superset config endpoint
    r3 = s.get(f"{BASE}/api/v1/async_event/")
    
    # Let's try creating charts and checking the explore endpoint for errors
    # The key insight: Superset frontend viz types are determined by the
    # @superset-ui/core ChartPlugin registry
    
    # In Superset 6.0.0, the registered chart plugins should include:
    # @superset-ui/core: BigNumber, BigNumberTotal, Pie, Table
    # @superset-ui/plugin-chart-echarts: EchartsTimeseries, EchartsPie, EchartsBoxPlot, etc.
    # plugin-chart-table: Table
    
    # Let's check by looking at the Python package
    import subprocess
    
    # Find superset-ui packages
    result = subprocess.run(
        ["docker", "exec", "academic-datalakehouse-superset-1", 
         "bash", "-c", 
         "find /app -name 'package.json' -path '*superset-ui*' 2>/dev/null | head -5"],
        capture_output=True, text=True, timeout=10
    )
    print(f"Superset UI packages: {result.stdout.strip()}")
    
    # Try to find the viz type registry from the installed packages
    result2 = subprocess.run(
        ["docker", "exec", "academic-datalakehouse-superset-1",
         "bash", "-c",
         "find /app -name 'index.js' -path '*plugin*chart*' 2>/dev/null | head -10"],
        capture_output=True, text=True, timeout=10
    )
    print(f"Chart plugin files: {result2.stdout.strip()}")
    
    # Most direct approach: read the Superset static assets manifest
    result3 = subprocess.run(
        ["docker", "exec", "academic-datalakehouse-superset-1",
         "bash", "-c",
         "find /app/superset/static -name '*.js' | xargs grep -l 'registerPlugin' 2>/dev/null | head -5"],
        capture_output=True, text=True, timeout=30
    )
    print(f"Files with registerPlugin: {result3.stdout.strip()}")
    
    # Let's search for the actual viz type keys in the JS bundles
    result4 = subprocess.run(
        ["docker", "exec", "academic-datalakehouse-superset-1",
         "bash", "-c",
         "find /app/superset/static -name '*.js' -exec grep -l 'echarts' {} + 2>/dev/null | head -10"],
        capture_output=True, text=True, timeout=30
    )
    print(f"Files with echarts: {result4.stdout.strip()}")

if __name__ == "__main__":
    main()
