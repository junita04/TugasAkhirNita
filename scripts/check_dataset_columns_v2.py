"""
Check column differences between dataset ID=5 and ID=27.
"""
import sys
sys.path.insert(0, '/app')

from superset.app import create_app
from superset import db
import json

app = create_app()
app.app_context().push()

from superset.connectors.sqla.models import SqlaTable
from superset.models.slice import Slice

print("=" * 70)
print("DATASET COLUMN COMPARISON")
print("=" * 70)

# Dataset ID=5 (data_referensi_mahasiswa)
ds5 = db.session.query(SqlaTable).get(5)
print(f"\nDataset ID=5: {ds5.table_name}")
print(f"  Schema: {ds5.schema}")
print(f"  Columns ({len(ds5.columns)}):")
for col in ds5.columns:
    print(f"    {col.column_name} ({col.type})")

# Dataset ID=27 (dim_mahasiswa)
ds27 = db.session.query(SqlaTable).get(27)
print(f"\nDataset ID=27: {ds27.table_name}")
print(f"  Schema: {ds27.schema}")
print(f"  Columns ({len(ds27.columns)}):")
for col in ds27.columns:
    print(f"    {col.column_name} ({col.type})")

# Check which charts use dataset ID=5
print(f"\n{'='*70}")
print(f"CHARTS USING DATASET ID=5 (data_referensi_mahasiswa)")
print(f"{'='*70}")

charts = db.session.query(Slice).filter(Slice.datasource_id == 5).all()
for c in charts:
    print(f"  ID={c.id} Name={c.slice_name} Type={c.viz_type}")

# Check which charts use dataset ID=27
print(f"\n{'='*70}")
print(f"CHARTS USING DATASET ID=27 (dim_mahasiswa)")
print(f"{'='*70}")

charts27 = db.session.query(Slice).filter(Slice.datasource_id == 27).all()
for c in charts27:
    print(f"  ID={c.id} Name={c.slice_name} Type={c.viz_type}")

# Identify charts that need dataset change
print(f"\n{'='*70}")
print(f"CHARTS THAT NEED DATASET CHANGE")
print(f"{'='*70}")

dashboard = db.session.query(Dashboard).get(4)
position = json.loads(dashboard.position_json) if dashboard.position_json else {}
chart_ids = [v.get("meta", {}).get("chartId") for k, v in position.items() if k.startswith("CHART-")]

for cid in chart_ids:
    chart = db.session.query(Slice).get(cid)
    if chart and chart.datasource_id == 5:
        # Check if required columns exist in dataset 5
        required_cols = ["angkatan", "status_mahasiswa", "status_kelulusan", "label", "ipk", "ip", "total_sks", "selisih_sks", "lama_studi", "jenis_kelamin"]
        missing = [col for col in required_cols if col not in [c.column_name for c in ds5.columns]]
        print(f"  Chart {cid} ({chart.slice_name}): MISSING COLUMNS in dataset 5: {missing}")
