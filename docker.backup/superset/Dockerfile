FROM apache/superset:6.0.0

USER root
RUN pip install --no-cache-dir --target=/app/.venv/lib/python3.10/site-packages \
    psycopg2-binary sqlalchemy-trino

COPY superset_config.py /app/pythonpath/superset_config.py
COPY entrypoint-init.sh /app/docker/entrypoint-init.sh
COPY register_datasets.py /app/docker/register_datasets.py
COPY trino_config.py /app/docker/trino_config.py
COPY create_admin.py /app/docker/create_admin.py
RUN chmod +x /app/docker/entrypoint-init.sh

USER superset
