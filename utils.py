import os
import json
from typing import List, Optional
from datetime import datetime
from models import PipelineInfo

def read_jsonl(filepath: str) -> List[PipelineInfo]:
    """Read a JSONL file and return a list of PipelineInfo objects."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    data = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                obj = json.loads(line)
                # Let Pydantic parse datetime strings into datetime objects
                data.append(PipelineInfo(**obj))
    return data


def write_jsonl_append(filepath: str, record: PipelineInfo) -> None:
    """Append a PipelineInfo record to a JSONL file.

    Serializes datetimes to ISO format using the Pydantic model_dump helper.
    """
    dirpath = os.path.dirname(filepath)
    if dirpath and not os.path.exists(dirpath):
        os.makedirs(dirpath, exist_ok=True)

    data = record.model_dump()
    # Turn datetimes into ISO strings
    for k, v in list(data.items()):
        if hasattr(v, 'isoformat'):
            data[k] = v.isoformat()

    with open(filepath, 'a', encoding='utf-8') as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")


def filter_pipeline_info(
    records: List[PipelineInfo],
    start_utc: Optional[datetime] = None,
    end_utc: Optional[datetime] = None,
    min_rowcount: Optional[int] = None,
    max_rowcount: Optional[int] = None,
) -> List[PipelineInfo]:
    """Apply filters to the pipeline info records."""
    filtered = []
    for rec in records:
        # rec.start_utc and rec.end_utc are datetimes (Pydantic will parse strings)
        if start_utc and rec.start_utc < start_utc:
            continue
        if end_utc and rec.end_utc > end_utc:
            continue
        if min_rowcount is not None and rec.rowcount < min_rowcount:
            continue
        if max_rowcount is not None and rec.rowcount > max_rowcount:
            continue
        filtered.append(rec)
    return filtered


def sort_pipeline_info(
    records: List[PipelineInfo], key: str = "start_utc", reverse: bool = True
) -> List[PipelineInfo]:
    """Sort pipeline info records by key (default: start_utc descending)."""
    return sorted(records, key=lambda x: getattr(x, key, ""), reverse=reverse)