import sys
sys.path.insert(0, '/app')
import superset
from superset.app import create_app

app = create_app()
with app.app_context():
    from superset import db
    from superset.models.core import Database
    from superset.connectors.sqla.models import SqlaTable

    for name in ['dim_mahasiswa_fix', 'fact_khs_fix']:
        ds = db.session.query(SqlaTable).filter(SqlaTable.table_name == name).first()
        if not ds:
            print(f'{name} not found')
            continue
        
        print(f'\n=== {name} id={ds.id} ===')
        print(f'  Methods: {[m for m in dir(ds) if "column" in m.lower() or "sync" in m.lower() or "refresh" in m.lower()]}')
        
        # Try the correct method
        try:
            # Use the SqlaTable's own method
            ds.sync_to_db_from_config(db.session)
            db.session.commit()
            print(f'  sync_to_db_from_config: OK')
        except Exception as e:
            print(f'  sync_to_db_from_config: {e}')
        
        # Try using database engine to get columns
        try:
            database = ds.database
            with database.get_sqla_engine() as engine:
                from sqlalchemy import inspect as sa_inspect
                inspector = sa_inspect(engine)
                columns = inspector.get_columns(ds.table_name, schema=ds.schema)
                print(f'  SQLAlchemy columns: {len(columns)}')
                for c in columns[:3]:
                    print(f'    {c["name"]} ({c["type"]})')
        except Exception as e:
            print(f'  SQLAlchemy error: {e}')
        
        # Try using database's get_columns with correct signature
        try:
            database = ds.database
            cols = database.get_columns(ds.table_name, ds.schema)
            print(f'  database.get_columns: {len(cols)} columns')
        except Exception as e:
            print(f'  database.get_columns error: {e}')
