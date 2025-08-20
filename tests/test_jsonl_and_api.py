from fastapi.testclient import TestClient
import os
from tempfile import NamedTemporaryFile

import sys
from pathlib import Path

# Ensure repo root is on sys.path so imports like `import main` work under pytest
repo_root = str(Path(__file__).resolve().parents[1])
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from main import app
from models import PipelineInfo
from utils import read_jsonl, write_jsonl_append

client = TestClient(app)

SAMPLE = {
    "start_local": "2025-08-14 22:49:07",
    "end_local": "2025-08-14 23:17:19",
    "start_utc": "2025-08-15T05:49:07Z",
    "end_utc": "2025-08-15T06:17:19Z",
    "elapsed_seconds": 1692.8,
    "elapsed_human": "28m 12s",
    "output_file": "/tmp/out.subcon",
    "rowcount": 8543,
    "log_file": "/tmp/log.log",
    "pid": 53452,
    "date_code": "2025-08-12_2025-08-12",
    "pipeline_name": "get_subcon_lot_ref_data_LOTGDB_rc10.py",
    "script_name": "get_subcon_lot_ref_data_LOTGDB_rc10.py",
    "pipeline_type": "batch",
    "environment": "prod"
}


def test_jsonl_append_and_read():
    rec = PipelineInfo(**SAMPLE)
    ntf = NamedTemporaryFile(delete=False)
    path = ntf.name
    ntf.close()

    # Write using util
    write_jsonl_append(path, rec)

    loaded = read_jsonl(path)
    assert len(loaded) == 1
    assert loaded[0].rowcount == rec.rowcount

    os.remove(path)


def test_post_pipeline_inserts_jsonl(monkeypatch):
    # Force repository to be JsonlPipelineRepository with a temp file
    from repository import JsonlPipelineRepository
    import main as main_module

    repo = JsonlPipelineRepository()
    ntf = NamedTemporaryFile(delete=False)
    repo.filepath = ntf.name
    ntf.close()

    # Monkeypatch global REPO in main
    monkeypatch.setattr(main_module, 'REPO', repo)

    resp = client.post('/pipelines', json=SAMPLE)
    assert resp.status_code == 201
    data = resp.json()
    assert data['rowcount'] == SAMPLE['rowcount']

    # Ensure the file contains the record
    loaded = read_jsonl(repo.filepath)
    assert len(loaded) == 1
    os.remove(repo.filepath)
