import os
from urllib.parse import quote_plus

from flask_caching.backends.rediscache import RedisCache


SECRET_KEY = os.environ["SUPERSET_SECRET_KEY"]
SQLALCHEMY_DATABASE_URI = (
    "postgresql+psycopg2://"
    f"{quote_plus(os.environ['POSTGRES_USER'])}:{quote_plus(os.environ['POSTGRES_PASSWORD'])}"
    f"@postgres:5432/{os.environ.get('SUPERSET_DB', 'superset')}"
)

REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))
RESULTS_BACKEND = RedisCache(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=1,
    key_prefix="superset_results",
    default_timeout=86400,
)

CELERY_CONFIG = {
    "broker_url": f"redis://{REDIS_HOST}:{REDIS_PORT}/0",
    "result_backend": f"redis://{REDIS_HOST}:{REDIS_PORT}/1",
    "imports": ("superset.sql_lab", "superset.tasks",),
}

FEATURE_FLAGS = {"DASHBOARD_NATIVE_FILTERS": True}
