import os
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile
import importlib

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


def test_post_pipeline_inserts_jsonl(monkeypatch):
    # Ensure repo root is importable, then import main and TestClient inside the test
    repo_root = str(Path(__file__).resolve().parents[2])
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)

    main_module = importlib.import_module('main')
    from fastapi.testclient import TestClient
    from repository import JsonlPipelineRepository

    # Import utils after repo root is on sys.path
    utils = importlib.import_module('utils')
    read_jsonl = utils.read_jsonl

    client = TestClient(main_module.app)

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
