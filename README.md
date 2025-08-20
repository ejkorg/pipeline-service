# Pipeline Info FastAPI Service (Pluggable Backend)

FastAPI service for pipeline/job info, with simple backend switching (`.jsonl` file or Oracle DB).

## Backend Selection

Set environment variable:

- `PIPELINE_BACKEND=jsonl` (default, reads from .jsonl file)
- `PIPELINE_BACKEND=oracle` (reads from Oracle database table)

### For `.jsonl`:

- Set `PIPELINE_JSONL_PATH` to your file (default: `benchmark.jsonl`)

### For Oracle:

Set all of:
- `ORACLE_DSN` (e.g. `host:port/service`)
- `ORACLE_USER`
- `ORACLE_PASSWORD`
- `ORACLE_TABLE` (default: `PIPELINE_RUNS`)

## Usage

```bash
pip install fastapi uvicorn pydantic cx_Oracle
uvicorn main:app --reload
```

See `/docs` for endpoint documentation.

## Extending

To add more data sources, simply implement another repository class in `repository.py` and update `get_repository`.

## Inserting records (POST endpoint)

The service now exposes a POST endpoint to insert pipeline records:

- POST /pipelines
	- Body: JSON matching the `PipelineInfo` model (see `/openapi.json` or `/docs` for fields).
	- Returns: 201 Created with the validated record in the response body.

Example:

```bash
curl -X POST http://127.0.0.1:8000/pipelines \
	-H "Content-Type: application/json" \
	-d @sample_record.json
```

When using the default `jsonl` backend the POST will append a JSON line to the file configured by `PIPELINE_JSONL_PATH`.

## Oracle column mapping

If your Oracle table uses column names that differ from the model field names, set the `ORACLE_COLUMN_MAP` environment
variable to a JSON mapping of model_field -> column_name. For example:

```bash
export ORACLE_COLUMN_MAP='{"start_utc":"START_UTC","rowcount":"ROW_COUNT","pipeline_name":"PIPE_NAME"}'
```

The mapping is used for WHERE clauses, SELECT aliases (when returning rows from Oracle) and INSERT column names. If not
provided the repository will assume the DB column names match the model field names.

## Quick install & run

Install dependencies from the provided `requirements.txt` and run the app with uvicorn:

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

## Tests & CI

- Run unit and integration tests locally:

```bash
pip install -r requirements.txt
pytest -q
```

- CI (GitHub Actions) will:
	- Run unit tests on push/PR for Python 3.11 and 3.12.
	- Cache pip downloads for faster runs.
	- Run a linter (`ruff`) as part of the job.
	- Run integration tests only when the branch is `integration` or when a PR has the `run-integration` label.

- CI secrets: For Oracle integration tests provide `ORACLE_DSN`, `ORACLE_USER`, `ORACLE_PASSWORD`, `ORACLE_TABLE`, and optional `ORACLE_COLUMN_MAP` as GitHub Secrets (Settings → Secrets) — do not commit credentials to the repo.

## CI secrets (explicit names)

If you plan to run Oracle integration tests in CI, add the following GitHub repository secrets (Settings → Secrets → Actions):

- ORACLE_DSN (example: host:1521/ORCLPDB1)
- ORACLE_USER
- ORACLE_PASSWORD
- ORACLE_TABLE (default: PIPELINE_RUNS)
- ORACLE_COLUMN_MAP (optional JSON mapping, e.g. '{"start_utc":"START_UTC","rowcount":"ROW_COUNT"}')

Optional pipeline/runtime config you may want to set as secrets or repository variables:

- PIPELINE_JSONL_PATH (if you want CI to write/read a specific path)
- PIPELINE_BACKEND (set to `oracle` in CI to exercise Oracle-backed flows)

Once added, these secrets will be available to Actions jobs as environment variables; the workflow can consume them automatically. Do not store credentials in the repository.

## Oracle datetime binding (recommended)

When using the Oracle backend prefer binding Python `datetime.datetime` objects directly instead of converting them to strings. Modern Oracle drivers (cx_Oracle or `python-oracledb`) will convert Python datetimes to native `TIMESTAMP` / `TIMESTAMP WITH TIME ZONE` values which enables correct range queries, indexing and partition pruning.

Short example using `python-oracledb`:

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

In this repo the Oracle repository now preserves Python datetimes when inserting so they are stored as native TIMESTAMP types (see `repository.py`). Continue to serialize datetimes to ISO strings for JSON/JSONL output.