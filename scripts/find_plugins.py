"""
Find registered viz types from Superset frontend.
Strategy: Create a chart with each possible viz type, then check
if the frontend can render it by checking the explore endpoint.
"""
import requests
import json
import re

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
    
    # Strategy: Look at what the Superset explore page loads
    # Get the main page
    r = s.get(f"{BASE}/superset/sqllab/")
    
    # Find all JS bundle paths
    js_files = re.findall(r'src="([^"]+\.js)"', r.text)
    print(f"Found {len(js_files)} JS files in main page")
    
    # Also check the home page
    r2 = s.get(f"{BASE}/superset/dashboard/")
    js_files2 = re.findall(r'src="([^"]+\.js)"', r2.text)
    print(f"Found {len(js_files2)} JS files in dashboard page")
    
    # Check the static assets index
    r3 = s.get(f"{BASE}/static/assets/")
    print(f"Static assets status: {r3.status_code}")
    
    # Try to find the manifest.json
    r4 = s.get(f"{BASE}/static/assets/manifest.json")
    if r4.status_code == 200:
        manifest = r4.json()
        print(f"Manifest entries: {len(manifest)}")
        # Look for chart-related entries
        for key, val in manifest.items():
            if 'chart' in key.lower() or 'viz' in key.lower():
                print(f"  {key}: {val}")
    
    # Try to find the plugin registry by looking at the explore page
    r5 = s.get(f"{BASE}/explore/?slice_id=1")
    print(f"\nExplore page status: {r5.status_code}")
    
    # Look for viz type definitions in the explore page
    viz_matches = re.findall(r'"viz_type":\s*"([^"]+)"', r5.text)
    if viz_matches:
        print(f"Viz types found in explore page: {set(viz_matches)}")
    
    # Search for chart_type or viz_type in the explore page
    type_matches = re.findall(r'chartType["\s:]+["\']([^"\']+)', r5.text)
    if type_matches:
        print(f"Chart types found: {set(type_matches)}")
    
    # Try to get the available viz types from the Superset config
    r6 = s.get(f"{BASE}/api/v1/available_domains/")
    print(f"Available domains: {r6.status_code}")

if __name__ == "__main__":
    main()
