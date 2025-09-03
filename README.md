# Pipeline Service

Production-grade FastAPI application for storing and serving pipeline run metadata. Supports pluggable storage backends (JSONL for lightweight/local use, Oracle for production) using a clean repository abstraction.

## Quick Start
- Install dependencies and run the API:

```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```

Open `http://localhost:8001/docs` for interactive API docs.

For production deployment behind NGINX proxy, access via `http://usaz15ls088:8080/pipeline-service/docs`.

## Features
- Multi-backend storage: JSONL file or Oracle (`python-oracledb`).
- Rich filtering (time range, row counts, pipeline/script/type/env).
- Pagination with limit/offset and full export toggle.
- Aggregated summaries per pipeline.
- Ingestion via POST (validates with Pydantic v2 models).
- Health endpoint for orchestration.

## Configuration
Set environment variables to select and configure the backend.

+- `PIPELINE_BACKEND`: `jsonl` (default) or `oracle`.
+
+When `jsonl` backend:
+- `PIPELINE_JSONL_PATH`: path to JSON Lines file (default: `pipeline_data.jsonl`).
+
+When `oracle` backend:
+- `ORACLE_DSN`: e.g., `host:port/service`.
+- `ORACLE_USER`: database username.
+- `ORACLE_PASSWORD`: database password.
+- `ORACLE_TABLE`: table name (default `PIPELINE_RUNS`).
+- `ORACLE_COLUMN_MAP`: optional JSON mapping of model field -> DB column.
+
+CORS Configuration:
+- `CORS_ORIGINS`: Comma-separated list of allowed origins (default: `http://localhost:3000,http://localhost:5173,http://localhost:8080,http://usaz15ls088:8080`).
+- `CORS_ALLOW_ALL`: Set to `true` to allow all origins (useful for development, default: `false`).
+
+Example:
+```bash
+export PIPELINE_BACKEND=oracle
+export ORACLE_DSN=host:1521/ORCLPDB1
+export ORACLE_USER=app
+export ORACLE_PASSWORD=secret
+export ORACLE_TABLE=PIPELINE_RUNS
+export ORACLE_COLUMN_MAP='{"start_utc":"START_UTC","rowcount":"ROW_COUNT"}'
+export CORS_ORIGINS='http://localhost:3000,http://myfrontend.com'
+export CORS_ALLOW_ALL=false
+uvicorn main:app --reload
+```

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
		- `limit` (1–10000), `offset` (>=0)
		- `all_data` (bool) — if true, ignores pagination
- `POST /pipelines`: insert a run (body must match `PipelineInfo`).
- `GET /health`: health check.

Example POST:
```bash
curl -X POST http://127.0.0.1:8001/pipelines \
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
uvicorn main:app --reload --port 8001
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

## NGINX Proxy Configuration
When deploying behind NGINX, use a configuration like this:

```nginx
location /pipeline-service/ {
  proxy_pass http://usaz15ls088:8001/;   # note trailing slash
  proxy_http_version 1.1;
  proxy_set_header Connection "";
  proxy_set_header Host $host;
  proxy_set_header X-Real-IP $remote_addr;
  proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  proxy_set_header X-Forwarded-Proto $scheme;
  proxy_set_header X-Forwarded-Prefix /pipeline-service;

  # CORS headers are handled by the FastAPI app, not NGINX
  # This allows the app to control CORS policy dynamically

  proxy_connect_timeout 5s;
  proxy_send_timeout 30s;
  proxy_read_timeout 30s;
}
```

The FastAPI app handles CORS headers automatically. If you need cross-origin requests, configure `CORS_ORIGINS` or set `CORS_ALLOW_ALL=true`.

**Access URLs:**
- API: `http://usaz15ls088:8080/pipeline-service/`
- Dashboard: `http://usaz15ls088:8080/pipeline-dashboard/`
- Docs: `http://usaz15ls088:8080/pipeline-service/docs`

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