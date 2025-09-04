from fastapi import FastAPI, HTTPException, Query, status
from fastapi.responses import JSONResponse, StreamingResponse
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
import os
import mimetypes
from datetime import datetime
from pathlib import Path

from models import PipelineInfo, PipelineInfoResponse, PipelineListResponse
from repository import get_repository

api_app = FastAPI(
    title="Pipeline Info API",
    description="Production-grade FastAPI app for serving pipeline information with multi-pipeline support.",
    version="1.1.0"
)

# CORS configuration - configurable via environment
cors_origins = os.environ.get("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173,http://localhost:8080,http://usaz15ls088:8080")
origins = [origin.strip() for origin in cors_origins.split(",") if origin.strip()]

# Allow all origins if CORS_ALLOW_ALL is set (for development)
allow_all_origins = os.environ.get("CORS_ALLOW_ALL", "false").lower() == "true"

api_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if allow_all_origins else origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Initialize repository
DATA_BACKEND = os.environ.get("PIPELINE_BACKEND", "jsonl").lower()

try:
    REPO = get_repository(DATA_BACKEND)
    print(f"[INFO] Initialized {DATA_BACKEND} repository successfully")
except Exception as e:
    print(f"[ERROR] Failed to initialize {DATA_BACKEND} repository: {e}")
    raise

# Configurable max file size for viewing/download (in MB)
MAX_FILE_SIZE_MB = int(os.environ.get("MAX_FILE_SIZE_MB", 50))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

@api_app.get("/pipelines", response_model=PipelineListResponse)
def list_pipelines():
    """
    Get a summary of all pipelines with statistics.
    
    Returns overview information for each unique pipeline including:
    - Total number of runs
    - Last execution time
    - Average duration and row counts
    """
    try:
        summaries = REPO.get_pipelines_summary()
        return PipelineListResponse(pipelines=summaries)
    except Exception as e:
        print(f"[ERROR] Error getting pipeline summaries: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@api_app.get("/get_pipeline_info", response_model=PipelineInfoResponse, response_class=JSONResponse)
def get_pipeline_info(
    start_utc: Optional[datetime] = Query(None, description="Filter by start UTC (>=). Format: YYYY-MM-DDTHH:MM:SSZ"),
    end_utc: Optional[datetime] = Query(None, description="Filter by end UTC (<=). Format: YYYY-MM-DDTHH:MM:SSZ"),
    min_rowcount: Optional[int] = Query(None, description="Filter by minimum row count"),
    max_rowcount: Optional[int] = Query(None, description="Filter by maximum row count"),
    pipeline_name: Optional[str] = Query(None, description="Filter by pipeline name"),
    script_name: Optional[str] = Query(None, description="Filter by script name"),
    pipeline_type: Optional[str] = Query(None, description="Filter by pipeline type (batch, streaming, ml)"),
    environment: Optional[str] = Query(None, description="Filter by environment (prod, dev, test)"),
    limit: int = Query(100, ge=1, le=10000, description="Maximum records to return (1-10000)"),
    offset: int = Query(0, ge=0, description="Records to skip for pagination"),
    all_data: bool = Query(False, description="Return all matching data (ignores limit/offset)")
):
    """
    Get pipeline information with filtering and pagination.
    
    Enhanced with pipeline-specific filtering:
    - **pipeline_name**: Filter by specific pipeline (e.g., 'sales_etl', 'user_analytics')
    - **script_name**: Filter by script file name (e.g., 'process_sales.py')
    - **pipeline_type**: Filter by type (batch, streaming, ml)
    - **environment**: Filter by environment (prod, dev, test)
    
    Plus all existing filters:
    - Time range filtering (start_utc, end_utc)
    - Row count filtering (min_rowcount, max_rowcount) 
    - Pagination (limit, offset)
    - Full data export (all_data=true)
    """
    try:
        data = REPO.get_pipeline_info(
            start_utc=start_utc,
            end_utc=end_utc,
            min_rowcount=min_rowcount,
            max_rowcount=max_rowcount,
            limit=None if all_data else limit,
            offset=0 if all_data else offset,
            pipeline_name=pipeline_name,
            script_name=script_name,
            pipeline_type=pipeline_type,
            environment=environment
        )
        
        total = REPO.count_pipeline_info(
            start_utc=start_utc,
            end_utc=end_utc,
            min_rowcount=min_rowcount,
            max_rowcount=max_rowcount,
            pipeline_name=pipeline_name,
            script_name=script_name,
            pipeline_type=pipeline_type,
            environment=environment
        ) if not all_data else len(data)
        
        # Extract unique pipeline names from results
        unique_pipelines = list(set([r.pipeline_name for r in data if r.pipeline_name]))
        
        return PipelineInfoResponse(
            total=total,
            count=len(data),
            results=data,
            pipelines=unique_pipelines
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Data file not found: {str(e)}")
    except Exception as e:
        print(f"[ERROR] Unexpected error in get_pipeline_info: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@api_app.get("/", include_in_schema=False)
def root():
    return {
        "message": "Welcome to the Pipeline Info API with multi-pipeline support. See /docs for usage.",
        "version": "1.1.0",
        "backend": DATA_BACKEND,
        "features": ["multi-pipeline", "filtering", "pagination", "statistics"]
    }

@api_app.get("/health")
def health():
    """Simple health check endpoint"""
    return {"status": "healthy", "backend": DATA_BACKEND, "version": "1.1.0"}


@api_app.get("/pipelines/archived/{date_code}")
async def get_archived_file(date_code: str):
    """
    Stream the archived_file for a pipeline record by date_code.
    
    - Detects file type and sets appropriate MIME type
    - If file size <= MAX_FILE_SIZE_MB, allows inline viewing (if browser supports)
    - If file size > MAX_FILE_SIZE_MB, forces download
    - Returns 404 if record or file not found
    - Production-grade: streams in chunks for scalability
    """
    try:
        # Securely fetch record by date_code
        record = REPO.get_pipeline_info_by_date_code(date_code)
        if not record or not record.archived_file:
            raise HTTPException(status_code=404, detail="Pipeline record or archived file not found")
        
        # Store the original archived file path for filename extraction
        original_archived_path = Path(record.archived_file)
        
        # Use the actual file path for reading (might be different if file was moved/copied)
        file_path = Path(record.archived_file)
        if not file_path.is_file():
            raise HTTPException(status_code=404, detail="Archived file not found on disk")
        
        # Security: Prevent path traversal
        if ".." in str(file_path) or not file_path.is_absolute():
            raise HTTPException(status_code=403, detail="Invalid file path")
        
        file_size = file_path.stat().st_size
        
        # Extract filename from the original archived_file path in the database record
        # This ensures we use the original filename, not the filesystem name
        download_filename = original_archived_path.name
        
        # Clean up the filename - remove .tmp extension if present
        # This handles cases where files are processed and temporarily renamed
        if download_filename.endswith('.tmp'):
            download_filename = download_filename[:-4]  # Remove .tmp
        elif download_filename.endswith('.gz.tmp'):
            download_filename = download_filename[:-8] + '.gz'  # Remove .tmp but keep .gz
        
        # Detect MIME type based on the cleaned filename
        mime_type, encoding = mimetypes.guess_type(download_filename)
        if mime_type is None:
            # Handle compressed files that return None for mime_type
            if encoding == 'gzip':
                mime_type = "application/gzip"
            elif encoding == 'bzip2':
                mime_type = "application/x-bzip2"
            elif encoding == 'compress':
                mime_type = "application/x-compress"
            else:
                mime_type = "application/octet-stream"  # Default for unknown types
        
        # Determine disposition based on size and type
        if file_size > MAX_FILE_SIZE_BYTES:
            disposition = "attachment"
        else:
            # For known safe types, allow inline; otherwise force download
            safe_types = ["text/", "image/", "application/json", "application/xml"]
            if any(mime_type.startswith(safe) for safe in safe_types):
                disposition = "inline"
            else:
                disposition = "attachment"
        
        # Import aiofiles here to avoid import errors if not installed
        try:
            import aiofiles
        except ImportError:
            raise HTTPException(status_code=500, detail="aiofiles package required for file streaming")
        
        async def file_generator():
            async with aiofiles.open(file_path, "rb") as f:
                chunk_size = 64 * 1024  # 64KB chunks
                while chunk := await f.read(chunk_size):
                    yield chunk
        
        return StreamingResponse(
            file_generator(),
            media_type=mime_type,
            headers={
                "Content-Disposition": f'{disposition}; filename="{download_filename}"',
                "Content-Length": str(file_size),
                "Cache-Control": "private, max-age=300",  # Short cache for dynamic content
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to serve archived file for {date_code}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@api_app.post("/pipelines", response_model=PipelineInfo, status_code=status.HTTP_201_CREATED)
def create_pipeline(record: PipelineInfo):
    """Insert a single pipeline record into the configured backend.

    Returns the created record (as validated by the model).
    """
    try:
        REPO.insert_pipeline_info(record)
        return record
    except Exception as e:
        print(f"[ERROR] Failed to insert pipeline record: {e}")
        raise HTTPException(status_code=500, detail="Failed to insert record")

main_app = FastAPI()
main_app.mount("/pipeline-service", api_app)