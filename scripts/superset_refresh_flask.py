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
        if ds:
            print(f'Found {name} id={ds.id}')
            # Try different methods to refresh columns
            try:
                ds.update_column_in_database(db.session)
                db.session.commit()
                print(f'  Updated columns via update_column_in_database')
            except Exception as e:
                print(f'  update_column_in_database failed: {e}')
            
            try:
                ds.sync_to_db_from_config(db.session)
                db.session.commit()
                print(f'  Synced via sync_to_db_from_config')
            except Exception as e:
                print(f'  sync_to_db_from_config failed: {e}')
            
            # Try using the database engine directly
            try:
                database = ds.database
                engine = database.get_sqla_engine()
                # Get columns via SQLAlchemy inspector
                from sqlalchemy import inspect
                inspector = inspect(engine)
                columns = inspector.get_columns(ds.table_name, schema=ds.schema)
                print(f'  Got {len(columns)} columns via SQLAlchemy inspector')
                for c in columns[:5]:
                    print(f'    {c["name"]} ({c["type"]})')
            except Exception as e:
                print(f'  SQLAlchemy inspector failed: {e}')
            
            # Try using the database's get_columns method
            try:
                cols = ds.database.get_columns(ds.table_name, ds.schema)
                print(f'  Got {len(cols)} columns via database.get_columns')
            except Exception as e:
                print(f'  database.get_columns failed: {e}')
        else:
            print(f'{name} not found')
