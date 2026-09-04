import sys
sys.path.insert(0, '/app')
import superset
from superset.app import create_app

app = create_app()
with app.app_context():
    from superset import db
    from superset.models.core import Database
    from superset.connectors.sqla.models import SqlaTable, TableColumn
    from sqlalchemy import inspect as sa_inspect

    for name in ['dim_mahasiswa_fix', 'fact_khs_fix']:
        ds = db.session.query(SqlaTable).filter(SqlaTable.table_name == name).first()
        if not ds:
            print(f'{name} not found')
            continue
        
        print(f'\n=== {name} id={ds.id} ===')
        
        # Get database and engine properly
        database = ds.database
        engine = database.get_sqla_engine()  # This is a context manager
        
        # Use the engine's raw connection
        with engine.connect() as conn:
            inspector = sa_inspect(conn)
            columns = inspector.get_columns(ds.table_name, schema=ds.schema)
            print(f'  Found {len(columns)} columns in Trino')
            
            # Clear existing columns
            ds.columns.clear()
            db.session.flush()
            
            # Add columns
            for col_info in columns:
                col = TableColumn(
                    column_name=col_info['name'],
                    type=str(col_info['type']),
                    table_id=ds.id,
                    is_dttm=False,
                )
                ds.columns.append(col)
            
            db.session.commit()
            print(f'  Added {len(columns)} columns to Superset')
        
        # Verify
        ds2 = db.session.query(SqlaTable).filter(SqlaTable.table_name == name).first()
        print(f'  Verified: {len(ds2.columns)} columns')
        for c in ds2.columns[:5]:
            print(f'    {c.column_name} ({c.type})')
