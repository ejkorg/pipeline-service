from tempfile import NamedTemporaryFile
import os

from models import PipelineInfo
from utils import read_jsonl, write_jsonl_append

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
