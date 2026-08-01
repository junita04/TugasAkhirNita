# Spark Environment-Driven and Superset via Trino Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Spark runtime configuration switchable between local and Docker cluster environments and make Superset query Iceberg Gold tables through Trino while preserving the existing PostgreSQL sink.

**Architecture:** `backend.config.settings` will derive explicit runtime defaults from `SPARK_MODE`, while `backend.spark.session` applies the selected master and Iceberg catalog without starting Spark during configuration tests. Superset will keep PostgreSQL for its metadata database but register a stable Trino database connection (`trino://trino@trino:8082/iceberg`) and three datasets in schema `gold`; the existing PostgreSQL publish step remains unchanged for compatibility.

**Tech Stack:** Python 3, PySpark 3.5, Apache Iceberg 1.5.2, Docker Compose, Apache Superset 6.0.0, SQLAlchemy Trino dialect, Trino 462, Hive Metastore, MinIO, PostgreSQL, Redis.

## Global Constraints

- Iceberg remains the pipeline source of truth; PostgreSQL is only a compatibility serving snapshot and Superset metadata store.
- `SPARK_MODE=local` defaults to `local[*]`, catalog `local`, and the repository `iceberg/` filesystem warehouse.
- `SPARK_MODE=cluster` defaults to `spark://spark-master:7077`, catalog `iceberg`, Hive Metastore, and `s3a://warehouse/iceberg`.
- Explicit environment variables override profile defaults; invalid `SPARK_MODE` values fail clearly before Spark starts.
- Superset dataset queries must use Trino catalog `iceberg`, schema `gold`, and the fixed tables `gold_mahasiswa`, `gold_program_studi`, and `gold_kurikulum`.
- Superset metadata continues to use PostgreSQL database `superset`; PostgreSQL serving tables and `publish_gold_tables()` are not removed.
- No real secrets may be committed; `.env.example` contains development placeholders only.
- Every implementation change must have a focused test or an explicit Compose/documentation validation command.

---

## File Map

- Modify `backend/config/settings.py`: normalize Spark mode and derive environment-driven master, catalog, and warehouse defaults while retaining PostgreSQL and S3 settings.
- Modify `backend/spark/session.py`: consume the normalized settings and apply local/cluster driver and Iceberg builder configuration.
- Modify `scripts/test_spark_session.py`: replace the manual-only smoke script with unit tests for environment-derived Spark configuration; retain an optional `main()` smoke entry point if useful.
- Modify `docker/superset/Dockerfile`: install the Trino SQLAlchemy driver alongside `psycopg2-binary`.
- Modify `docker/superset/register_datasets.py`: create/update the stable Trino database connection and register fixed `gold` datasets idempotently.
- Modify `scripts/test_superset_config.py`: test Trino URI and fixed dataset metadata without importing Superset runtime modules.
- Modify `docker-compose.yml`: pass Trino/catalog environment consistently, keep Superset waiting for healthy Trino, and preserve PostgreSQL metadata dependencies.
- Modify `.env.example`: document local/cluster Spark values and Trino connection variables without changing development-safe defaults.
- Modify `README.md`: document the new Iceberg → Trino → Superset flow, compatibility PostgreSQL role, operation commands, and validation commands.
- Do not modify `backend/services/pipeline_service.py` unless a regression test proves the existing PostgreSQL publish ordering changed; the current call order is already correct.

---

### Task 1: Make Spark settings environment-driven

**Files:**
- Modify: `backend/config/settings.py`
- Modify: `backend/spark/session.py`
- Modify: `scripts/test_spark_session.py`

**Interfaces:**
- `backend.config.settings.SPARK_MODE: str` is always `local` or `cluster`.
- `backend.config.settings.MASTER: str` is the selected Spark master URL.
- `backend.config.settings.ICEBERG_CATALOG: str` is `local` in local mode and `iceberg` in cluster mode unless explicitly overridden.
- `backend.config.settings.ICEBERG_WAREHOUSE: str` is the local repository path in local mode and `s3a://warehouse/iceberg` in cluster mode unless explicitly overridden.
- `backend.spark.session._iceberg_configs(builder)` applies the selected catalog without creating a Spark session.

- [ ] **Step 1: Write failing settings tests**

Replace the current manual smoke-only script with a test module that reloads `backend.config.settings` under patched environment values. Use a helper that removes `backend.config.settings` from `sys.modules`, imports it, then restores the original module after each test so the repository `.env` cannot override the test case.

```python
def test_local_profile_defaults_to_local_master_and_filesystem_catalog():
    settings = load_settings({"SPARK_MODE": "local"})
    assert settings.SPARK_MODE == "local"
    assert settings.MASTER == "local[*]"
    assert settings.ICEBERG_CATALOG == "local"
    assert settings.ICEBERG_WAREHOUSE.endswith("iceberg")

def test_cluster_profile_defaults_to_docker_master_and_hive_warehouse():
    settings = load_settings({"SPARK_MODE": "cluster"})
    assert settings.SPARK_MODE == "cluster"
    assert settings.MASTER == "spark://spark-master:7077"
    assert settings.ICEBERG_CATALOG == "iceberg"
    assert settings.ICEBERG_WAREHOUSE == "s3a://warehouse/iceberg"

def test_explicit_runtime_values_override_profile_defaults():
    settings = load_settings({
        "SPARK_MODE": "cluster",
        "SPARK_MASTER_URL": "spark://external-master:7077",
        "ICEBERG_CATALOG": "custom",
        "ICEBERG_WAREHOUSE": "s3a://custom/warehouse",
    })
    assert settings.MASTER == "spark://external-master:7077"
    assert settings.ICEBERG_CATALOG == "custom"
    assert settings.ICEBERG_WAREHOUSE == "s3a://custom/warehouse"

def test_invalid_spark_mode_fails_with_actionable_error():
    with pytest.raises(ValueError, match="SPARK_MODE"):
        load_settings({"SPARK_MODE": "standalone"})
```

- [ ] **Step 2: Run the tests and verify the expected red state**

Run:

```powershell
python -m pytest scripts/test_spark_session.py -q
```

Expected: failures for profile-derived catalog/warehouse values and invalid-mode validation because the current settings only defaults catalog to `local`, does not derive cluster warehouse values, and accepts arbitrary mode strings.

- [ ] **Step 3: Implement the smallest settings change**

Add a normalization helper in `backend/config/settings.py`:

```python
def _runtime_setting(name, default):
    return os.getenv(name, default)

def _spark_mode():
    value = os.getenv("SPARK_MODE", "local").strip().lower()
    if value not in {"local", "cluster"}:
        raise ValueError("SPARK_MODE must be either 'local' or 'cluster'")
    return value
```

Derive profile defaults before explicit overrides:

```python
SPARK_MODE = _spark_mode()
MASTER = os.getenv(
    "SPARK_MASTER_URL",
    "local[*]" if SPARK_MODE == "local" else "spark://spark-master:7077",
)
ICEBERG_CATALOG = os.getenv(
    "ICEBERG_CATALOG",
    "local" if SPARK_MODE == "local" else "iceberg",
)
ICEBERG_WAREHOUSE = os.getenv(
    "ICEBERG_WAREHOUSE",
    str(ICEBERG_DIR) if SPARK_MODE == "local" else "s3a://warehouse/iceberg",
)
```

Do not remove the existing PostgreSQL or S3 environment constants. Keep `.env` loading process-safe by retaining `os.environ.setdefault`.

- [ ] **Step 4: Run the settings tests and verify green**

Run:

```powershell
python -m pytest scripts/test_spark_session.py -q
```

Expected: all focused settings tests pass without starting Spark or downloading packages.

- [ ] **Step 5: Add failing builder tests for local/cluster behavior**

Create a small fake builder recording `.config(key, value)` calls, and test `_iceberg_configs`:

```python
def test_local_catalog_uses_hadoop_warehouse(fake_builder, monkeypatch):
    monkeypatch.setattr(session, "ICEBERG_CATALOG", "local")
    monkeypatch.setattr(session, "ICEBERG_WAREHOUSE", "D:/data/iceberg")
    session._iceberg_configs(fake_builder)
    assert fake_builder.values["spark.sql.catalog.local.type"] == "hadoop"
    assert fake_builder.values["spark.sql.catalog.local.warehouse"] == "D:/data/iceberg"

def test_cluster_catalog_uses_hive_and_s3a(fake_builder, monkeypatch):
    monkeypatch.setattr(session, "ICEBERG_CATALOG", "iceberg")
    monkeypatch.setattr(session, "ICEBERG_WAREHOUSE", "s3a://warehouse/iceberg")
    session._iceberg_configs(fake_builder)
    assert fake_builder.values["spark.sql.catalog.iceberg.type"] == "hive"
    assert fake_builder.values["spark.sql.catalog.iceberg.uri"] == session.HIVE_METASTORE_URI
    assert fake_builder.values["spark.hadoop.fs.s3a.endpoint"] == session.S3_ENDPOINT
```

- [ ] **Step 6: Run builder tests, then align session branching**

Run:

```powershell
python -m pytest scripts/test_spark_session.py -q
```

Expected: the new cluster test fails against the current code because the implementation branches on `ICEBERG_CATALOG == "hive"`, while the agreed cluster catalog name is `iceberg`.

Update `_iceberg_configs` to treat `ICEBERG_CATALOG == "iceberg"` as the Hive catalog and use the configured catalog name consistently. Keep the local builder branch for `local`. In `get_spark`, apply loopback driver host/bind settings only for local mode; retain the existing dependency list including PostgreSQL JDBC.

- [ ] **Step 7: Run focused Spark tests and existing import checks**

Run:

```powershell
python -m pytest scripts/test_spark_session.py -q
python -c "from backend.spark.session import get_spark; print('spark session module import ok')"
```

Expected: focused tests pass and importing the module does not create a Spark session.

- [ ] **Step 8: Commit the Spark configuration unit**

```powershell
git add backend/config/settings.py backend/spark/session.py scripts/test_spark_session.py
git commit -m "feat: make Spark runtime configuration environment driven"
```

### Task 2: Point Superset datasets at Trino

**Files:**
- Modify: `docker/superset/Dockerfile`
- Modify: `docker/superset/register_datasets.py`
- Modify: `scripts/test_superset_config.py`

**Interfaces:**
- `TRINO_DATABASE_NAME = "Academic Trino"`.
- `TRINO_CATALOG = "iceberg"`.
- `TRINO_SCHEMA = "gold"`.
- `TRINO_TABLES = ("gold_mahasiswa", "gold_program_studi", "gold_kurikulum")`.
- `trino_uri()` returns `trino://trino@trino:8082/iceberg` by default and supports `TRINO_HOST`, `TRINO_PORT`, and `TRINO_USER` environment overrides.
- Registration finds/creates a Superset `Database` by stable name and finds/creates `SqlaTable` rows by database, schema, and table.

- [ ] **Step 1: Write failing pure configuration tests**

Extend `scripts/test_superset_config.py` without importing `superset.app`:

```python
def test_trino_uri_uses_internal_defaults(monkeypatch):
    monkeypatch.delenv("TRINO_HOST", raising=False)
    monkeypatch.delenv("TRINO_PORT", raising=False)
    monkeypatch.delenv("TRINO_USER", raising=False)
    assert trino_uri() == "trino://trino@trino:8082/iceberg"

def test_registered_tables_are_gold_tables():
    assert TRINO_SCHEMA == "gold"
    assert set(TRINO_TABLES) == {"gold_mahasiswa", "gold_program_studi", "gold_kurikulum"}

def test_postgres_serving_uri_is_not_the_dataset_uri():
    assert trino_uri().startswith("trino://")
```

- [ ] **Step 2: Run the tests and verify the expected red state**

Run:

```powershell
python -m pytest scripts/test_superset_config.py -q
```

Expected: failures because the current registration script only exposes `serving_uri()` and PostgreSQL constants.

- [ ] **Step 3: Implement pure Trino constants and URI construction**

Move constants and URI construction above the Superset imports so the test can load them without a Superset installation:

```python
TRINO_DATABASE_NAME = "Academic Trino"
TRINO_CATALOG = "iceberg"
TRINO_SCHEMA = "gold"
TRINO_TABLES = ("gold_mahasiswa", "gold_program_studi", "gold_kurikulum")

def trino_uri():
    user = quote_plus(os.getenv("TRINO_USER", "trino"))
    host = os.getenv("TRINO_HOST", "trino")
    port = os.getenv("TRINO_PORT", "8082")
    catalog = os.getenv("TRINO_CATALOG", TRINO_CATALOG)
    return f"trino://{user}@{host}:{port}/{catalog}"
```

Keep the PostgreSQL `serving_uri()` only if it is still used by another bootstrap path; do not register it as a Superset dataset database.

- [ ] **Step 4: Run pure tests and verify green**

Run:

```powershell
python -m pytest scripts/test_superset_config.py -q
```

Expected: pure Trino configuration tests pass without a running container.

- [ ] **Step 5: Write the idempotent registration behavior test**

Add a test using simple fake `Database`, `SqlaTable`, and session objects, or test the extracted pure `dataset_specs()` helper:

```python
def test_dataset_specs_target_trino_gold_tables():
    assert dataset_specs() == [
        ("gold", "gold_mahasiswa"),
        ("gold", "gold_program_studi"),
        ("gold", "gold_kurikulum"),
    ]
```

If the live Superset model test is not importable on the host, keep it as a container smoke check and ensure the pure helper locks the database name, schema, and table mapping.

- [ ] **Step 6: Run the behavior test, then implement registration**

Run the focused test and confirm it fails until `dataset_specs()` exists. Then update the live registration block to:

```python
database = db.session.query(Database).filter_by(
    database_name=TRINO_DATABASE_NAME,
).one_or_none()
if database is None:
    database = Database(
        database_name=TRINO_DATABASE_NAME,
        sqlalchemy_uri=trino_uri(),
        expose_in_sqllab=True,
    )
    db.session.add(database)
    db.session.flush()
elif database.sqlalchemy_uri != trino_uri():
    database.sqlalchemy_uri = trino_uri()

for schema, table_name in dataset_specs():
    dataset = db.session.query(SqlaTable).filter_by(
        database_id=database.id,
        table_name=table_name,
        schema=schema,
    ).one_or_none()
    if dataset is None:
        db.session.add(SqlaTable(
            database=database,
            table_name=table_name,
            schema=schema,
        ))
```

Use `superset.app` and model imports only after pure definitions, so the host unit test remains dependency-light. The registration script must never print `trino_uri()` or any credential-bearing URI.

- [ ] **Step 7: Install the Trino driver in the Superset image**

Update `docker/superset/Dockerfile` to install the dialect used by the URI, alongside the existing PostgreSQL driver:

```dockerfile
RUN pip install --no-cache-dir --target=/app/.venv/lib/python3.10/site-packages \
    psycopg2-binary sqlalchemy-trino
```

Keep the target directory consistent with the existing image setup and do not alter the Superset metadata URI in `superset_config.py`.

- [ ] **Step 8: Run focused tests and commit Superset integration**

Run:

```powershell
python -m pytest scripts/test_superset_config.py -q
git diff --check
git add docker/superset/Dockerfile docker/superset/register_datasets.py scripts/test_superset_config.py
git commit -m "feat: register Superset datasets through Trino"
```

Expected: focused tests pass and the diff has no whitespace errors.

### Task 3: Align Compose and environment documentation

**Files:**
- Modify: `docker-compose.yml`
- Modify: `.env.example`
- Modify: `docker/superset/entrypoint-init.sh` only if init ordering or retry behavior needs to be made explicit.

**Interfaces:**
- Superset containers receive `TRINO_HOST=trino`, `TRINO_PORT=8082`, `TRINO_CATALOG=iceberg`, and `TRINO_USER=trino`.
- `superset-init` depends on healthy `postgres`, `redis`, and `trino`.
- Superset web and worker depend on successful `superset-init`.
- PostgreSQL remains available on the host for FastAPI compatibility.

- [ ] **Step 1: Add a Compose/env regression test or inspection assertions**

Add `scripts/test_compose_architecture.py` that reads `docker-compose.yml` and `.env.example` as text and asserts the required wiring without starting containers:

```python
def test_superset_waits_for_trino_and_receives_trino_settings():
    compose = Path("docker-compose.yml").read_text(encoding="utf-8")
    assert "trino:\n        condition: service_healthy" in compose
    assert "TRINO_HOST: trino" in compose

def test_env_example_declares_two_spark_profiles_and_trino():
    env = Path(".env.example").read_text(encoding="utf-8")
    assert "SPARK_MODE=local" in env
    assert "TRINO_URI=http://trino:8082" in env
```

- [ ] **Step 2: Run the inspection test and confirm any missing wiring fails**

Run:

```powershell
python -m pytest scripts/test_compose_architecture.py -q
```

Expected: failure if the current Compose environment does not explicitly pass Trino variables to Superset or if documentation values are inconsistent.

- [ ] **Step 3: Implement only the required Compose wiring**

Add explicit environment values to `superset-init`, `superset`, and `superset-worker`:

```yaml
TRINO_HOST: ${TRINO_HOST:-trino}
TRINO_PORT: ${TRINO_PORT:-8082}
TRINO_CATALOG: ${TRINO_CATALOG:-iceberg}
TRINO_USER: ${TRINO_USER:-trino}
```

Keep the existing `trino` health check and `superset-init` dependency. Do not make Superset depend on PostgreSQL serving tables; PostgreSQL is required only because `superset_config.py` stores Superset metadata there.

In `.env.example`, make `SPARK_MASTER_URL`, `ICEBERG_WAREHOUSE`, and `ICEBERG_CATALOG` explicit comments/examples for local versus cluster use, and keep the Trino variables adjacent to the existing Trino section. Do not put a real password in the file.

- [ ] **Step 4: Run Compose and inspection checks**

Run:

```powershell
python -m pytest scripts/test_compose_architecture.py -q
docker compose config
```

Expected: the inspection test passes and Compose renders successfully. If `.env` is absent, copy `.env.example` to `.env` only as a local uncommitted validation prerequisite; never commit it.

- [ ] **Step 5: Commit Compose configuration**

```powershell
git add docker-compose.yml .env.example scripts/test_compose_architecture.py
git commit -m "chore: align Compose with Trino-backed Superset"
```

### Task 4: Document and verify the complete architecture

**Files:**
- Modify: `README.md`
- Modify: `scripts/test_pipeline_publish.py` only if the existing test is missing or no longer covers publish ordering.

**Interfaces:**
- README commands must work from `D:\TugasAkhirNita` in PowerShell.
- README states that Superset queries Trino and PostgreSQL serving is retained only for compatibility.
- Pipeline order remains `Gold -> publish_gold_tables() -> Feature Store`.

- [ ] **Step 1: Add/confirm a pipeline ordering regression test**

Ensure `scripts/test_pipeline_publish.py` verifies the existing behavior:

```python
def test_publish_runs_after_gold_before_feature_store(...):
    events = []
    gold.side_effect = lambda: events.append("gold")
    publish.side_effect = lambda spark: events.append("publish")
    feature_store.side_effect = lambda: events.append("feature_store")
    run_pipeline(Path("data/input.xlsx"))
    assert events == ["gold", "publish", "feature_store"]
```

Do not change `pipeline_service.py` if this test passes; the compatibility sink must remain in place.

- [ ] **Step 2: Run the pipeline-order test and verify it passes**

Run:

```powershell
python -m pytest scripts/test_pipeline_publish.py -q
```

Expected: PASS. Any failure is a regression to investigate before editing documentation.

- [ ] **Step 3: Rewrite README for the new data flow**

Document these exact operational sections:

```text
1. Prerequisites and environment setup
2. Local pipeline mode (`SPARK_MODE=local`)
3. Docker cluster mode (`SPARK_MODE=cluster`)
4. Architecture and data flow
5. Superset/Trino datasets
6. Validation commands
7. Start/stop/restart/troubleshooting commands
```

Use this architecture description:

```text
Excel -> FastAPI -> Bronze -> Silver -> Gold Iceberg
                                -> Trino (catalog iceberg, schema gold)
                                -> Superset
Gold -> PostgreSQL serving snapshot (compatibility only)
```

State that Superset’s metadata is stored in PostgreSQL `superset`, while its three analytical datasets come from Trino. Include `docker compose config`, `python -m pytest scripts/test_spark_session.py scripts/test_superset_config.py scripts/test_compose_architecture.py scripts/test_pipeline_publish.py -q`, and the optional `python scripts/test_spark_session.py` Spark smoke command.

- [ ] **Step 4: Run documentation/configuration verification**

Run:

```powershell
git diff --check
docker compose config
python -m pytest scripts/test_spark_session.py scripts/test_superset_config.py scripts/test_compose_architecture.py scripts/test_pipeline_publish.py -q
```

Expected: all focused tests pass, Compose exits with code 0, and the diff has no whitespace errors. If a full Docker image build is feasible, run `docker compose build superset superset-init superset-worker` and record the result; otherwise report the external limitation explicitly.

- [ ] **Step 5: Commit documentation and verification helpers**

```powershell
git add README.md scripts/test_pipeline_publish.py
git commit -m "docs: describe Trino-backed Superset architecture"
```

## Final Verification Checklist

- [ ] `SPARK_MODE=local` defaults to `local[*]`, local catalog, and filesystem warehouse.
- [ ] `SPARK_MODE=cluster` defaults to Docker Spark Master, Hive catalog, and MinIO warehouse.
- [ ] Invalid `SPARK_MODE` fails with an actionable `ValueError`.
- [ ] Superset registration uses `Academic Trino`, `trino://.../iceberg`, schema `gold`, and exactly three fixed tables.
- [ ] Superset metadata still uses PostgreSQL and the pipeline PostgreSQL sink remains in place.
- [ ] Superset services receive Trino environment values and wait for healthy Trino.
- [ ] `docker compose config` succeeds.
- [ ] Focused Python tests pass.
- [ ] README documents local mode, cluster mode, Trino query path, PostgreSQL compatibility role, and validation commands.
