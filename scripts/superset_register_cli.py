"""
Register _fix datasets using Superset's internal API via flask shell
"""
import subprocess
import json

# Use superset CLI to create datasets
commands = [
    # First, let's try using superset shell to create datasets
    """
import sys
sys.path.insert(0, '/app')
from superset import db
from superset.models.core import Database
from superset.connectors.sqla.models import SqlaTable

# Get the Trino database
database = db.session.query(Database).filter(Database.database_name == 'Academic Trino').first()
if not database:
    print("ERROR: Database 'Academic Trino' not found")
else:
    print(f"Found database: {database.database_name} (id={database.id})")
    
    # Check if datasets already exist
    existing = db.session.query(SqlaTable).filter(
        SqlaTable.table_name.in_(['dim_mahasiswa_fix', 'fact_khs_fix'])
    ).all()
    print(f"Existing _fix datasets: {[t.table_name for t in existing]}")
    
    # Create dim_mahasiswa_fix
    if not any(t.table_name == 'dim_mahasiswa_fix' for t in existing):
        ds = SqlaTable(
            table_name='dim_mahasiswa_fix',
            database_id=database.id,
            schema='gold',
        )
        db.session.add(ds)
        db.session.commit()
        print(f"Created dim_mahasiswa_fix (id={ds.id})")
    else:
        ds = next(t for t in existing if t.table_name == 'dim_mahasiswa_fix')
        print(f"dim_mahasiswa_fix already exists (id={ds.id})")
    
    # Create fact_khs_fix
    if not any(t.table_name == 'fact_khs_fix' for t in existing):
        ds2 = SqlaTable(
            table_name='fact_khs_fix',
            database_id=database.id,
            schema='gold',
        )
        db.session.add(ds2)
        db.session.commit()
        print(f"Created fact_khs_fix (id={ds2.id})")
    else:
        ds2 = next(t for t in existing if t.table_name == 'fact_khs_fix')
        print(f"fact_khs_fix already exists (id={ds2.id})")
    
    # Refresh columns for both
    for ds_name in ['dim_mahasiswa_fix', 'fact_khs_fix']:
        ds = db.session.query(SqlaTable).filter(SqlaTable.table_name == ds_name).first()
        if ds:
            ds.get_columns(db.engine)
            db.session.commit()
            print(f"Refreshed columns for {ds_name}: {len(ds.columns)} columns")
    
    # List all _fix datasets
    all_fix = db.session.query(SqlaTable).filter(SqlaTable.table_name.like('%_fix%')).all()
    print(f"\\nAll _fix datasets:")
    for t in all_fix:
        print(f"  id={t.id} | {t.table_name} | schema={t.schema}")
"""
]

# Run via superset shell
for cmd in commands:
    result = subprocess.run(
        ["docker", "exec", "academic-datalakehouse-superset-1", "superset", "shell", "-c", cmd],
        capture_output=True, text=True, timeout=60
    )
    print("STDOUT:", result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr[:500])
