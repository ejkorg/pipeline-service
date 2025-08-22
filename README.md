# Pipeline Service

Production-grade FastAPI application for storing and serving pipeline run metadata. Supports pluggable storage backends (JSONL for lightweight/local use, Oracle for production) using a clean repository abstraction.

## Quick Start
- Install dependencies and run the API:

```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Open `http://localhost:8000/docs` for interactive API docs.

## Features
- Multi-backend storage: JSONL file or Oracle (`python-oracledb`).
- Rich filtering (time range, row counts, pipeline/script/type/env).
- Pagination with limit/offset and full export toggle.
- Aggregated summaries per pipeline.
- Ingestion via POST (validates with Pydantic v2 models).
- Health endpoint for orchestration.

## Configuration
Set environment variables to select and configure the backend.

- `PIPELINE_BACKEND`: `jsonl` (default) or `oracle`.

When `jsonl` backend:
- `PIPELINE_JSONL_PATH`: path to JSON Lines file (default: `pipeline_data.jsonl`).

When `oracle` backend:
- `ORACLE_DSN`: e.g., `host:port/service`.
- `ORACLE_USER`: database username.
- `ORACLE_PASSWORD`: database password.
- `ORACLE_TABLE`: table name (default `PIPELINE_RUNS`).
- `ORACLE_COLUMN_MAP`: optional JSON mapping of model field -> DB column.

Example:
```bash
export PIPELINE_BACKEND=oracle
export ORACLE_DSN=host:1521/ORCLPDB1
export ORACLE_USER=app
export ORACLE_PASSWORD=secret
export ORACLE_TABLE=PIPELINE_RUNS
export ORACLE_COLUMN_MAP='{"start_utc":"START_UTC","rowcount":"ROW_COUNT"}'
uvicorn main:app --reload
```

## Data Model
Defined in `models.py`.

- `PipelineInfo`: single run with timestamps, metrics, artifacts, identifiers, and classification fields (`pipeline_name`, `script_name`, `pipeline_type`, `environment`).
- `PipelineSummary`: aggregated view per pipeline signature with totals, last run, averages.
- Response wrappers: `PipelineInfoResponse`, `PipelineListResponse`.

## Endpoints
- `GET /pipelines`: list `PipelineSummary` objects (aggregated stats).
- `GET /get_pipeline_info`: filtered pipeline runs with pagination.
	- Query params:
		- `start_utc`, `end_utc` (ISO datetimes)
		- `min_rowcount`, `max_rowcount` (ints)
		- `pipeline_name`, `script_name`, `pipeline_type`, `environment`
		- `limit` (1–1000), `offset` (>=0)
		- `all_data` (bool) — if true, ignores pagination
- `POST /pipelines`: insert a run (body must match `PipelineInfo`).
- `GET /health`: health check.

Example POST:
```bash
curl -X POST http://127.0.0.1:8000/pipelines \
	-H "Content-Type: application/json" \
	-d @sample_record.json
```

## Storage Backends
### JSONL (default)
- Appends newline-delimited JSON to `PIPELINE_JSONL_PATH`.
- All queries read file and filter in-memory (suitable for small files; rotate if large).

### Oracle (python-oracledb)
- Uses `python-oracledb` Thin mode by default.
- Parameterized queries prevent SQL injection; dynamic WHERE assembly based on provided filters.
- ROWNUM-based pagination; can be upgraded to keyset pagination.
- Optional `ORACLE_COLUMN_MAP` lets you adapt to existing column names.

See `sql/create_pipeline_runs.sql` for a reference table definition and indexes.

## Development & Testing
- Run tests:
```bash
pytest -q
```

- Useful commands:
```bash
uvicorn main:app --reload --port 8000
pip install python-oracledb
```

### Notes for Oracle Testing
- Provide env vars (`ORACLE_DSN`, `ORACLE_USER`, `ORACLE_PASSWORD`, `ORACLE_TABLE`).
- Consider using Oracle XE for local tests or mock the repository for unit tests.

## Oracle Datetime Binding (Recommended)
Bind Python `datetime` objects directly; `python-oracledb` converts them to native Oracle `TIMESTAMP`/`TIMESTAMP WITH TIME ZONE` types enabling correct range queries and indexing.

```python
import oracledb
from datetime import timezone

conn = oracledb.connect(user=ORACLE_USER, password=ORACLE_PASSWORD, dsn=ORACLE_DSN)
sql = "INSERT INTO pipeline_runs (start_utc, end_utc, rowcount, date_code) VALUES (:start_utc, :end_utc, :rowcount, :date_code)"
params = {
	"start_utc": my_record.start_utc.astimezone(timezone.utc),
	"end_utc": my_record.end_utc.astimezone(timezone.utc),
	"rowcount": my_record.rowcount,
	"date_code": my_record.date_code,
}
with conn.cursor() as cur:
	cur.execute(sql, params)
	conn.commit()
```

## Extending the Project
- Add a new backend: subclass `PipelineInfoRepository` in `repository.py` and implement the four methods.
- Add fields: extend `PipelineInfo`; ensure DB schema/column map updated accordingly.
- Add endpoints: keep validation in FastAPI and business/data access in the repo layer.

## Operations
- Configure via env vars; never commit secrets.
- Monitor via logs; consider metrics/tracing for production.
- Health probe at `/health` for container orchestration.

## Additional Documentation
- See `STUDY_GUIDE.md` for a comprehensive deep-dive: architecture, testing, security, scaling, runbook, and roadmap.