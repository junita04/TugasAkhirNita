"""
COMPLETE SUPERSET REBUILD FROM SCRATCH
Delete everything and rebuild Dashboard 4 from zero.
"""
import sys
sys.path.insert(0, '/app')
from superset.app import create_app
from superset import db
from datetime import datetime
import json

app = create_app()
app.app_context().push()

from superset.models.dashboard import Dashboard
from superset.models.slice import Slice
from superset.connectors.sqla.models import SqlaTable

# ============================================================
# STEP 1: FULL AUDIT
# ============================================================
print("=" * 70)
print("STEP 1: FULL DATABASE AUDIT")
print("=" * 70)

# Check all datasets
datasets = db.session.query(SqlaTable).all()
print(f"\nAll datasets: {len(datasets)}")
for ds in datasets:
    print(f"  ID={ds.id} Table={ds.table_name} Schema={ds.schema}")

# Check dataset 27 columns
ds27 = db.session.query(SqlaTable).get(27)
if ds27:
    print(f"\nDataset 27 ({ds27.table_name}):")
    print(f"  Columns: {len(ds27.columns)}")
    for c in ds27.columns:
        print(f"    {c.column_name} ({c.type})")

# Check dataset 34 and 35 (fix versions)
ds34 = db.session.query(SqlaTable).get(34)
ds35 = db.session.query(SqlaTable).get(35)
print(f"\nDataset 34: {ds34.table_name if ds34 else 'NOT FOUND'}")
print(f"Dataset 35: {ds35.table_name if ds35 else 'NOT FOUND'}")

# Check all slices
slices = db.session.query(Slice).all()
print(f"\nAll slices: {len(slices)}")

# Check dashboard 4
dash4 = db.session.query(Dashboard).get(4)
if dash4:
    pos = json.loads(dash4.position_json) if dash4.position_json else {}
    chart_refs = [v.get("meta", {}).get("chartId") for k, v in pos.items() if k.startswith("CHART-")]
    print(f"\nDashboard 4: {dash4.dashboard_title}")
    print(f"  Chart references: {len(chart_refs)}")
    for cid in chart_refs:
        s = db.session.query(Slice).get(cid)
        print(f"    Chart {cid}: {s.slice_name if s else 'MISSING'}")

print("\nAudit complete.")
