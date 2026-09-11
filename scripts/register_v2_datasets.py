"""
Register v2 datasets in Superset via SQLAlchemy inspector.
"""
import sys
sys.path.insert(0, '/app')

from superset.app import create_app
from superset import db
import json

app = create_app()
app.app_context().push()

from superset.connectors.sqla.models import SqlaTable, TableColumn, Database
from sqlalchemy import inspect, create_engine

# Find Trino database
trino_db = db.session.query(Database).filter_by(database_name="Academic Trino").first()
print(f"Database: {trino_db.database_name} (ID={trino_db.id})")

# Create engine directly from Trino connection params
trino_url = "trino://trino@trino:8082/iceberg"
engine = create_engine(trino_url)
insp = inspect(engine)

new_datasets = [
    ("model_predictions_v2", "gold"),
    ("prediction_by_angkatan_v2", "gold"),
    ("training_dataset_v2", "feature_store"),
    ("inference_dataset_v2", "feature_store"),
]

TYPE_MAP = {
    "VARCHAR": "STRING",
    "BIGINT": "BIGINT",
    "INTEGER": "INT",
    "DOUBLE": "FLOAT",
    "BOOLEAN": "BOOLEAN",
}

created_datasets = {}
for table_name, schema in new_datasets:
    existing = db.session.query(SqlaTable).filter_by(
        table_name=table_name, schema=schema, database_id=trino_db.id
    ).first()
    
    if existing:
        print(f"  Dataset exists: {table_name} (ID={existing.id}, {len(existing.columns)} cols)")
        created_datasets[table_name] = existing.id
        continue
    
    try:
        cols = insp.get_columns(table_name, schema=schema)
        print(f"  Columns for {schema}.{table_name}: {len(cols)}")
    except Exception as e:
        print(f"  ERROR getting columns for {schema}.{table_name}: {e}")
        continue
    
    ds = SqlaTable(
        table_name=table_name,
        schema=schema,
        database_id=trino_db.id,
    )
    db.session.add(ds)
    db.session.flush()
    
    for col in cols:
        col_type_str = str(col["type"]).upper()
        col_type = TYPE_MAP.get(col_type_str, "STRING")
        tc = TableColumn(
            column_name=col["name"],
            type=col_type,
            table_id=ds.id,
            is_dttm=False,
        )
        db.session.add(tc)
    
    db.session.commit()
    created_datasets[table_name] = ds.id
    print(f"  Created: {table_name} (ID={ds.id}, {len(cols)} cols)")

print(f"\nDataset IDs: {created_datasets}")
