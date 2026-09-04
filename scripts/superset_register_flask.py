import sys
sys.path.insert(0, '/app')
from superset import db
from superset.models.core import Database
from superset.connectors.sqla.models import SqlaTable

database = db.session.query(Database).filter(Database.database_name == 'Academic Trino').first()
print(f'Database: {database.database_name} id={database.id}')

existing = db.session.query(SqlaTable).filter(SqlaTable.table_name.in_(['dim_mahasiswa_fix', 'fact_khs_fix'])).all()
print(f'Existing: {[t.table_name for t in existing]}')

if not any(t.table_name == 'dim_mahasiswa_fix' for t in existing):
    ds = SqlaTable(table_name='dim_mahasiswa_fix', database_id=database.id, schema='gold')
    db.session.add(ds)
    db.session.commit()
    print(f'Created dim_mahasiswa_fix id={ds.id}')

if not any(t.table_name == 'fact_khs_fix' for t in existing):
    ds2 = SqlaTable(table_name='fact_khs_fix', database_id=database.id, schema='gold')
    db.session.add(ds2)
    db.session.commit()
    print(f'Created fact_khs_fix id={ds2.id}')

for name in ['dim_mahasiswa_fix', 'fact_khs_fix']:
    ds = db.session.query(SqlaTable).filter(SqlaTable.table_name == name).first()
    if ds:
        ds.get_columns(db.engine)
        db.session.commit()
        print(f'Refreshed {name}: {len(ds.columns)} columns')

all_fix = db.session.query(SqlaTable).filter(SqlaTable.table_name.like('%_fix%')).all()
print('All _fix datasets:')
for t in all_fix:
    print(f'  id={t.id} {t.table_name} schema={t.schema}')
