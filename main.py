from fastapi import FastAPI, HTTPException, Query, status
from fastapi.responses import JSONResponse
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
import os
from datetime import datetime

from models import PipelineInfo, PipelineInfoResponse, PipelineListResponse
from repository import get_repository

app = FastAPI(
    title="Pipeline Info API",
    description="Production-grade FastAPI app for serving pipeline information with multi-pipeline support.",
    version="1.1.0"
)

# CORS configuration
origins = [
    "http://usaz15ls088:5173",
    "http://usaz15ls088:3000",
    "http://localhost:5173",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
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

@app.get("/pipelines", response_model=PipelineListResponse)
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

@app.get("/get_pipeline_info", response_model=PipelineInfoResponse, response_class=JSONResponse)
def get_pipeline_info(
    start_utc: Optional[datetime] = Query(None, description="Filter by start UTC (>=). Format: YYYY-MM-DDTHH:MM:SSZ"),
    end_utc: Optional[datetime] = Query(None, description="Filter by end UTC (<=). Format: YYYY-MM-DDTHH:MM:SSZ"),
    min_rowcount: Optional[int] = Query(None, description="Filter by minimum row count"),
    max_rowcount: Optional[int] = Query(None, description="Filter by maximum row count"),
    pipeline_name: Optional[str] = Query(None, description="Filter by pipeline name"),
    script_name: Optional[str] = Query(None, description="Filter by script name"),
    pipeline_type: Optional[str] = Query(None, description="Filter by pipeline type (batch, streaming, ml)"),
    environment: Optional[str] = Query(None, description="Filter by environment (prod, dev, test)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return (1-1000)"),
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

@app.get("/", include_in_schema=False)
def root():
    return {
        "message": "Welcome to the Pipeline Info API with multi-pipeline support. See /docs for usage.",
        "version": "1.1.0",
        "backend": DATA_BACKEND,
        "features": ["multi-pipeline", "filtering", "pagination", "statistics"]
    }

@app.get("/health")
def health():
    """Simple health check endpoint"""
    return {"status": "healthy", "backend": DATA_BACKEND, "version": "1.1.0"}


@app.post("/pipelines", response_model=PipelineInfo, status_code=status.HTTP_201_CREATED)
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
# from fastapi import FastAPI, HTTPException, Query
# from fastapi.responses import JSONResponse
# from typing import Optional
# from fastapi.middleware.cors import CORSMiddleware
# import os

# from models import PipelineInfo, PipelineInfoResponse
# from repository import get_repository

# app = FastAPI(
#     title="Pipeline Info API",
#     description="FastAPI app for serving pipeline information from a .jsonl file or Oracle database.",
#     version="1.0.0"
# )

# # CORS configuration
# origins = [
#     "http://usaz15ls088:5173",
#     "http://usaz15ls088:3000",
#     "http://localhost:5173",  # Common local dev
#     "http://localhost:3000",  # Common local dev
# ]

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=True,
#     allow_methods=["GET", "POST", "OPTIONS"],
#     allow_headers=["*"],
# )

# # Choose data source via env var: 'jsonl' or 'oracle'
# DATA_BACKEND = os.environ.get("PIPELINE_BACKEND", "jsonl").lower()

# try:
#     REPO = get_repository(DATA_BACKEND)
#     print(f"[INFO] Initialized {DATA_BACKEND} repository successfully")
# except Exception as e:
#     print(f"[ERROR] Failed to initialize {DATA_BACKEND} repository: {e}")
#     raise

# @app.get("/get_pipeline_info", response_model=PipelineInfoResponse, response_class=JSONResponse)
# def get_pipeline_info(
#     start_utc: Optional[str] = Query(None, description="Filter by start UTC (>=). Format: YYYY-MM-DDTHH:MM:SSZ"),
#     end_utc: Optional[str] = Query(None, description="Filter by end UTC (<=). Format: YYYY-MM-DDTHH:MM:SSZ"),
#     min_rowcount: Optional[int] = Query(None, description="Filter by minimum row count"),
#     max_rowcount: Optional[int] = Query(None, description="Filter by maximum row count"),
#     limit: int = Query(100, ge=1, le=1000, description="Maximum records to return (1-1000)"),
#     offset: int = Query(0, ge=0, description="Records to skip for pagination"),
#     all_data: bool = Query(False, description="Return all matching data (ignores limit/offset)")
# ):
#     """
#     Get pipeline information with filtering and pagination.
    
#     Returns pipeline job execution data with support for:
#     - Time range filtering (start_utc, end_utc)
#     - Row count filtering (min_rowcount, max_rowcount) 
#     - Pagination (limit, offset)
#     - Full data export (all_data=true)
#     """
#     try:
#         data = REPO.get_pipeline_info(
#             start_utc=start_utc,
#             end_utc=end_utc,
#             min_rowcount=min_rowcount,
#             max_rowcount=max_rowcount,
#             limit=None if all_data else limit,
#             offset=0 if all_data else offset
#         )
        
#         total = REPO.count_pipeline_info(
#             start_utc=start_utc,
#             end_utc=end_utc,
#             min_rowcount=min_rowcount,
#             max_rowcount=max_rowcount
#         ) if not all_data else len(data)
        
#         return PipelineInfoResponse(
#             total=total,
#             count=len(data),
#             results=data
#         )
#     except ValueError as e:
#         raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")
#     except FileNotFoundError as e:
#         raise HTTPException(status_code=404, detail=f"Data file not found: {str(e)}")
#     except Exception as e:
#         print(f"[ERROR] Unexpected error in get_pipeline_info: {e}")
#         raise HTTPException(status_code=500, detail="Internal server error")

# @app.get("/", include_in_schema=False)
# def root():
#     return {
#         "message": "Welcome to the Pipeline Info API. See /docs for usage.",
#         "version": "2.0.0",
#         "backend": DATA_BACKEND
#     }

# @app.get("/health")
# def health():
#     """Simple health check endpoint"""
#     return {"status": "healthy", "backend": DATA_BACKEND}