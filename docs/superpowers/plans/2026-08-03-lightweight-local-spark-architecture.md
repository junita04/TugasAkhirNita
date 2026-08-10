# Lightweight Local Spark Architecture Implementation Plan

> **For agentic workers:** Execute this plan task-by-task with verification checkpoints.

**Goal:** Keep MinIO, Hive Metastore, Trino, Airflow, Superset, PostgreSQL, and Redis in Docker while making Windows-local Spark and FastAPI the default execution path.

**Architecture:** Docker provides the persistent lakehouse/control-plane services. FastAPI on Windows owns the Spark process and calls Docker services through published localhost ports. Airflow remains in Docker and triggers the host FastAPI pipeline through `host.docker.internal`.

**Tech Stack:** Docker Compose profiles, FastAPI, Apache Spark 3.5, Apache Iceberg, Hive Metastore, MinIO S3A, Trino, Airflow, PostgreSQL, Redis, Superset.

## Global Constraints

- Do not delete volumes or use `docker compose down -v`.
- Do not remove research components; make Spark Docker optional instead.
- Docker-internal clients use service names; Windows-local clients use published localhost ports.
- The original Excel dataset remains under `data/` and is seeded into MinIO `raw`.
- Every behavior change requires a failing test before implementation.
- Context7 is unavailable in this session; no Context7 lookup is claimed.

### Task 1: Add tests for the lightweight runtime contract

**Files:**
- Modify: `scripts/test_data_lake_runtime.py`
- Modify: `scripts/test_compose_architecture.py`

- [ ] Add tests asserting Spark services have the `spark-docker` profile, the local FastAPI endpoint is reachable from Airflow through `host.docker.internal`, and no default Compose service depends on `spark-master`.
- [ ] Run the focused tests and verify they fail against the current Compose/DAG configuration.

### Task 2: Make Docker Spark optional

**Files:**
- Modify: `docker-compose.yml`
- Test: `scripts/test_compose_architecture.py`

- [ ] Add `profiles: [spark-docker]` to `spark-master`, `spark-worker`, and `spark-history`.
- [ ] Keep their definitions, images, ports, and volumes intact for optional cluster demonstrations.
- [ ] Ensure the default stack still includes MinIO, Hive Metastore, Trino, Airflow, Superset, PostgreSQL, and Redis.
- [ ] Run `docker compose config --quiet` and the focused tests.

### Task 3: Add a host pipeline trigger for Airflow

**Files:**
- Create: `backend/api/pipeline.py`
- Modify: `main.py`
- Modify: `docker/airflow/dags/prediction_pipeline.py`
- Test: `scripts/test_pipeline_trigger.py`

- [ ] Add `POST /pipeline/run` accepting an optional filename defaulting to `req_data_rut.xlsx`.
- [ ] Resolve the filename under the project `data/` directory and reject path traversal or non-Excel files.
- [ ] Call the existing `run_pipeline(Path)` function and return the filename plus pipeline status.
- [ ] Replace missing `SparkSubmitOperator` job paths in the Airflow DAG with an HTTP call to `http://host.docker.internal:8000/pipeline/run`.
- [ ] Keep the DAG schedule, task ordering, and notifications intact.
- [ ] Run API unit tests without starting Spark by patching the pipeline boundary.

### Task 4: Document local Spark and Docker service endpoints

**Files:**
- Modify: `.env.example`
- Modify: `README.md`

- [ ] Document local Spark settings using `ICEBERG_CATALOG=iceberg`, `ICEBERG_WAREHOUSE=s3a://warehouse/iceberg`, `S3_ENDPOINT=http://localhost:9000`, and `HIVE_METASTORE_URI=thrift://localhost:9083`.
- [ ] Document the lightweight startup command and the optional `--profile spark-docker` command.
- [ ] Document the Airflow-to-host trigger through `host.docker.internal`.
- [ ] Document that PostgreSQL and MinIO volumes are preserved by normal `down`.

### Task 5: Verify without destructive operations

**Files:**
- No source changes.

- [ ] Run all relevant unit tests and `docker compose config --quiet`.
- [ ] Start only the default Docker services with `docker compose up -d --build` if the current service state permits.
- [ ] Verify MinIO raw object, Hive Metastore health, Trino health, Superset health, and Airflow webserver health.
- [ ] Do not start the optional Spark Docker profile unless explicitly requested.
