# Apache Superset Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish the Iceberg Gold tables to PostgreSQL and provide a Dockerized Apache Superset stack that exposes those tables as datasets.

**Architecture:** FastAPI keeps Iceberg as the system of record. After Gold processing, a focused JDBC sink writes three fixed Gold tables to PostgreSQL; Superset reads PostgreSQL through an internal Docker network. Superset metadata uses a separate PostgreSQL database, while the serving database is exposed to the host for the locally running FastAPI process.

**Tech Stack:** Python, FastAPI, PySpark JDBC, PostgreSQL 16, Apache Superset 4.x, Redis, Docker Compose, Bash/Python initialization scripts.

## Global Constraints

- Iceberg remains the pipeline source of truth; PostgreSQL is only a serving snapshot for Superset.
- Publish occurs after all Gold tables are created and before Feature Store execution.
- PostgreSQL table names are fixed: `gold_mahasiswa`, `gold_program_studi`, and `gold_kurikulum`.
- Secrets come from `.env`; commit only `.env.example` and never real passwords.
- Docker Compose must provide PostgreSQL, Redis, Superset web, Superset worker, and Superset initialization.
- Publish failures must be explicit and must not delete already-created Iceberg data.

---

### Task 1: Add serving configuration and PostgreSQL sink

**Files:**
- Create: `backend/serving/__init__.py`
- Create: `backend/serving/postgres_sink.py`
- Modify: `backend/config/settings.py`
- Modify: `backend/spark/session.py`
- Create: `scripts/test_postgres_sink.py`
- Modify: `requirements.txt` only if the implementation uses a new Python database client; prefer Spark JDBC and do not add one unnecessarily.

**Interfaces:**
- Produces `GoldTableSpec` with `source_table` and `target_table` string fields.
- Produces `publish_gold_tables(spark: SparkSession) -> None`.
- Consumes `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `POSTGRES_SCHEMA` environment variables.

- [ ] **Step 1: Write failing tests for configuration and fixed table mapping**

```python
import os
import unittest
from unittest.mock import patch

from backend.serving.postgres_sink import GOLD_TABLES, postgres_jdbc_url, postgres_properties


class PostgresSinkTests(unittest.TestCase):
    def test_jdbc_url_uses_environment_values(self):
        with patch.dict(os.environ, {
            "POSTGRES_HOST": "localhost",
            "POSTGRES_PORT": "5433",
            "POSTGRES_DB": "analytics",
        }, clear=False):
            self.assertEqual(
                postgres_jdbc_url(),
                "jdbc:postgresql://localhost:5433/analytics",
            )

    def test_table_mapping_is_fixed(self):
        self.assertEqual(
            [item.target_table for item in GOLD_TABLES],
            ["gold_mahasiswa", "gold_program_studi", "gold_kurikulum"],
        )

    def test_properties_do_not_return_an_empty_password(self):
        with patch.dict(os.environ, {"POSTGRES_PASSWORD": "secret"}, clear=False):
            self.assertEqual(postgres_properties()["password"], "secret")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the focused test and verify it fails**

Run: `python -m unittest scripts.test_postgres_sink -v`

Expected: FAIL because `backend.serving.postgres_sink` does not exist yet.

- [ ] **Step 3: Add environment-backed configuration and JDBC sink**

Implement `GoldTableSpec` and a fixed tuple:

```python
GOLD_TABLES = (
    GoldTableSpec("local.gold.gold_mahasiswa", "gold_mahasiswa"),
    GoldTableSpec("local.gold.gold_program_studi", "gold_program_studi"),
    GoldTableSpec("local.gold.gold_kurikulum", "gold_kurikulum"),
)
```

`publish_gold_tables(spark)` must read each source with `spark.table`, write with `df.write.jdbc(url, f"{schema}.{target_table}", mode="overwrite", properties=properties)`, and raise a `RuntimeError` that includes the target table if a write fails. Validate required values before the first write and never log the password.

Add `org.postgresql:postgresql:42.7.4` to `spark.jars.packages` in `backend/spark/session.py` alongside the existing packages.

- [ ] **Step 4: Run the focused test and verify it passes**

Run: `python -m unittest scripts.test_postgres_sink -v`

Expected: PASS.

- [ ] **Step 5: Commit the serving sink**

```bash
git add backend/serving backend/config/settings.py backend/spark/session.py scripts/test_postgres_sink.py
git commit -m "feat: add PostgreSQL Gold serving sink"
```

### Task 2: Publish Gold data from the pipeline

**Files:**
- Modify: `backend/services/pipeline_service.py`
- Create: `scripts/test_pipeline_publish.py`

**Interfaces:**
- `run_pipeline(file_path: Path)` continues to be the public pipeline entry point.
- It calls `publish_gold_tables(get_spark("Gold PostgreSQL Publish"))` after `process_gold()` and before `run_feature_store()`.

- [ ] **Step 1: Write a failing ordering test**

```python
import unittest
from pathlib import Path
from unittest.mock import patch

from backend.services.pipeline_service import run_pipeline


class PipelinePublishTests(unittest.TestCase):
    @patch("backend.services.pipeline_service.run_feature_store")
    @patch("backend.services.pipeline_service.publish_gold_tables")
    @patch("backend.services.pipeline_service.get_spark")
    @patch("backend.services.pipeline_service.process_gold")
    @patch("backend.services.pipeline_service.process_all_tables")
    @patch("backend.services.pipeline_service.load_all_sheets_to_bronze")
    def test_publish_runs_after_gold_before_feature_store(
        self, bronze, silver, gold, get_spark, publish, feature_store
    ):
        events = []
        gold.side_effect = lambda: events.append("gold")
        publish.side_effect = lambda spark: events.append("publish")
        feature_store.side_effect = lambda: events.append("feature_store")
        run_pipeline(Path("data/input.xlsx"))
        self.assertEqual(events, ["gold", "publish", "feature_store"])
        publish.assert_called_once_with(get_spark.return_value)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test and verify it fails**

Run: `python -m unittest scripts.test_pipeline_publish -v`

Expected: FAIL because `pipeline_service` does not call the sink.

- [ ] **Step 3: Integrate the sink without changing existing ETL behavior**

Import `get_spark` and `publish_gold_tables`, then add:

```python
process_gold()
publish_gold_tables(get_spark("Gold PostgreSQL Publish"))
run_feature_store()
```

Do not catch the sink exception in `run_pipeline`; the upload endpoint will return its existing HTTP 500 response while the Iceberg output remains intact.

- [ ] **Step 4: Run focused and existing pipeline tests**

Run: `python -m unittest scripts.test_pipeline_publish -v`

Expected: PASS.

Run: `python scripts/test_feature_store.py` and the existing relevant scripts that do not require a running PostgreSQL service.

Expected: Existing behavior remains passing or reports only pre-existing environment-dependent failures.

- [ ] **Step 5: Commit pipeline integration**

```bash
git add backend/services/pipeline_service.py scripts/test_pipeline_publish.py
git commit -m "feat: publish Gold tables during pipeline"
```

### Task 3: Create the Dockerized Superset stack

**Files:**
- Create: `docker-compose.yml`
- Create: `.env.example`
- Create: `docker/postgres/init.sql`
- Create: `docker/superset/Dockerfile`
- Create: `docker/superset/entrypoint-init.sh`
- Create: `docker/superset/superset_config.py`

**Interfaces:**
- Host FastAPI connects to `localhost:${POSTGRES_PORT}`.
- Superset connects to `postgresql://...@postgres:5432/${POSTGRES_SERVING_DB}` internally.
- Superset metadata connects to its dedicated metadata database.

- [ ] **Step 1: Add environment template**

Create `.env.example` with non-secret defaults:

```dotenv
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=academic_serving
POSTGRES_USER=academic
POSTGRES_PASSWORD=change-me
POSTGRES_SCHEMA=public
SUPERSET_DB=superset
SUPERSET_ADMIN_USERNAME=admin
SUPERSET_ADMIN_EMAIL=admin@example.com
SUPERSET_ADMIN_PASSWORD=change-me
SUPERSET_SECRET_KEY=change-this-secret-key
```

- [ ] **Step 2: Add Compose services and health checks**

Define two PostgreSQL databases in one PostgreSQL service using `docker/postgres/init.sql`: `academic_serving` and `superset`. Add Redis, `superset-init`, `superset`, and `superset-worker`. `superset` and `superset-worker` must depend on `superset-init` completing successfully; PostgreSQL and Redis must have health checks. Mount `superset_config.py` and expose Superset on `8088`.

- [ ] **Step 3: Add idempotent Superset initialization**

The init script must run `superset db upgrade`, create the admin only when absent, run `superset init`, and create the PostgreSQL serving database connection if it is not already present. Use the Superset CLI/Python API available in the selected image; do not store credentials in the image.

- [ ] **Step 4: Validate Compose syntax and image configuration**

Run: `docker compose config`

Expected: Compose renders successfully using a copied `.env` file.

- [ ] **Step 5: Start the stack and verify health**

Run: `docker compose up -d`

Run: `docker compose ps`

Expected: PostgreSQL, Redis, Superset, worker, and init report healthy/completed states; Superset is reachable at `http://localhost:8088`.

- [ ] **Step 6: Commit the local stack**

```bash
git add docker-compose.yml docker .env.example
git commit -m "feat: add Dockerized Superset stack"
```

### Task 4: Register datasets, document operation, and run end-to-end verification

**Files:**
- Create: `docker/superset/register_datasets.py`
- Modify: `docker/superset/entrypoint-init.sh`
- Modify: `README.md`
- Create: `scripts/test_superset_config.py`

**Interfaces:**
- Registration is safe to run repeatedly and targets only the three fixed serving tables.
- README documents copying `.env.example` to `.env`, starting Compose, starting FastAPI, uploading Excel, and opening Superset.

- [ ] **Step 1: Write a failing registration/configuration test**

```python
import unittest

from backend.serving.postgres_sink import GOLD_TABLES


class SupersetConfigTests(unittest.TestCase):
    def test_all_published_tables_are_registered_targets(self):
        self.assertEqual(
            {spec.target_table for spec in GOLD_TABLES},
            {"gold_mahasiswa", "gold_program_studi", "gold_kurikulum"},
        )


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Implement idempotent dataset registration**

Create or update the Superset bootstrap code to find/create one dataset per fixed table in schema `public`, preserving existing datasets on rerun. Ensure the database connection name is stable and that no password is written to logs.

- [ ] **Step 3: Run configuration and full unit checks**

Run: `python -m unittest scripts.test_postgres_sink scripts.test_pipeline_publish scripts.test_superset_config -v`

Expected: PASS.

- [ ] **Step 4: Perform end-to-end smoke verification**

With Compose running and `.env` configured:

1. Start FastAPI with `uvicorn main:app --reload`.
2. Upload an Excel file through `POST /upload/`.
3. Query PostgreSQL and verify all three serving tables exist and have rows.
4. Open Superset, select the registered database, and verify the three datasets can be queried.

Expected: PostgreSQL row counts match the corresponding Gold DataFrame counts, and Superset can query each dataset.

- [ ] **Step 5: Document operations and troubleshooting**

README must include the required Docker commands, default URLs, credentials source, how to restart only Superset, how to stop the stack, and the fact that a new Excel upload overwrites the PostgreSQL serving snapshot.

- [ ] **Step 6: Commit documentation and verification helpers**

```bash
git add README.md docker/superset scripts/test_superset_config.py
git commit -m "docs: document Superset datasets and operations"
```

## Final Verification Checklist

- [ ] `docker compose config` succeeds.
- [ ] `docker compose ps` shows healthy PostgreSQL, Redis, Superset, and worker services.
- [ ] Focused Python tests pass.
- [ ] FastAPI upload completes with PostgreSQL running.
- [ ] All three fixed serving tables contain the latest Gold snapshot.
- [ ] Superset can query all three registered datasets.
- [ ] No real secrets or `.env` file are committed.
