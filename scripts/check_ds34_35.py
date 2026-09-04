"""
Check dataset 34 and 35 columns and data.
"""
import sys
sys.path.insert(0, '/app')
from superset.app import create_app
from superset import db
import json

app = create_app()
app.app_context().push()

from superset.connectors.sqla.models import SqlaTable

# Check dataset 34
ds34 = db.session.query(SqlaTable).get(34)
print(f"Dataset 34: {ds34.table_name}")
print(f"  Schema: {ds34.schema}")
print(f"  Database: {ds34.database.database_name}")
print(f"  Columns: {len(ds34.columns)}")
for c in ds34.columns:
    print(f"    {c.column_name} ({c.type})")

# Check dataset 35
ds35 = db.session.query(SqlaTable).get(35)
print(f"\nDataset 35: {ds35.table_name}")
print(f"  Schema: {ds35.schema}")
print(f"  Database: {ds35.database.database_name}")
print(f"  Columns: {len(ds35.columns)}")
for c in ds35.columns:
    print(f"    {c.column_name} ({c.type})")
