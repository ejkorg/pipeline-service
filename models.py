from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class PipelineInfo(BaseModel):
    # Use datetime for timestamps so Pydantic/ FastAPI will parse and validate them
    start_local: datetime = Field(..., description="Start time in local timezone")
    end_local: datetime = Field(..., description="End time in local timezone")
    start_utc: datetime = Field(..., description="Start time in UTC (ISO format)")
    end_utc: datetime = Field(..., description="End time in UTC (ISO format)")
    elapsed_seconds: float = Field(..., description="Duration in seconds")
    elapsed_human: str = Field(..., description="Human readable duration (e.g., '22m 5s')")
    output_file: str = Field(..., description="Path to output data file")
    rowcount: int = Field(..., description="Number of rows processed")
    log_file: str = Field(..., description="Path to log file")
    pid: int = Field(..., description="Process ID")
    date_code: str = Field(..., description="Unique date code identifier")
    
    # New pipeline identification fields
    pipeline_name: Optional[str] = Field(None, description="Name of the pipeline (e.g., 'data_ingestion', 'etl_transform')")
    script_name: Optional[str] = Field(None, description="Name of the script file (e.g., 'process_sales.py')")
    pipeline_type: Optional[str] = Field(None, description="Type of pipeline (e.g., 'batch', 'streaming', 'ml')")
    environment: Optional[str] = Field(None, description="Environment (e.g., 'prod', 'dev', 'test')")

    # Pydantic v2 model config
    model_config = {
        # allow building models from ORM objects/attribute-accessible objects
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "start_local": "2025-08-08 05:07:01",
                "end_local": "2025-08-08 05:29:07",
                "start_utc": "2025-08-08T12:07:01Z",
                "end_utc": "2025-08-08T12:29:07Z",
                "elapsed_seconds": 1325.571,
                "elapsed_human": "22m 5s",
                "output_file": "/apps/data/pipeline/output-20250808_050701.data",
                "rowcount": 4342,
                "log_file": "/apps/data/pipeline/logs/job-20250808_050701.log",
                "pid": 38298,
                "date_code": "20250808_050701",
                "pipeline_name": "sales_etl",
                "script_name": "process_sales_data.py",
                "pipeline_type": "batch",
                "environment": "prod"
            }
        }
    }

class PipelineInfoResponse(BaseModel):
    total: int = Field(..., description="Total number of matching records")
    count: int = Field(..., description="Number of records in this response")
    results: List[PipelineInfo] = Field(..., description="List of pipeline records")
    pipelines: List[str] = Field(default_factory=list, description="List of unique pipeline names in results")

class PipelineSummary(BaseModel):
    pipeline_name: Optional[str] = Field(..., description="Pipeline name")
    script_name: Optional[str] = Field(None, description="Script name")
    pipeline_type: Optional[str] = Field(None, description="Pipeline type")
    environment: Optional[str] = Field(None, description="Environment")
    total_runs: int = Field(..., description="Total number of runs")
    # last_run is a datetime so it can be sorted/compared programmatically
    last_run: Optional[datetime] = Field(None, description="Last run timestamp (UTC)")
    avg_duration: Optional[float] = Field(None, description="Average duration in seconds")
    avg_rowcount: Optional[float] = Field(None, description="Average rows processed")

class PipelineListResponse(BaseModel):
    pipelines: List[PipelineSummary] = Field(..., description="List of pipeline summaries")

# from pydantic import BaseModel, Field
# from typing import List

# class PipelineInfo(BaseModel):
#     start_local: str = Field(..., description="Start time in local timezone")
#     end_local: str = Field(..., description="End time in local timezone")
#     start_utc: str = Field(..., description="Start time in UTC (ISO format)")
#     end_utc: str = Field(..., description="End time in UTC (ISO format)")
#     elapsed_seconds: float = Field(..., description="Duration in seconds")
#     elapsed_human: str = Field(..., description="Human readable duration (e.g., '22m 5s')")
#     output_file: str = Field(..., description="Path to output data file")
#     rowcount: int = Field(..., description="Number of rows processed")
#     log_file: str = Field(..., description="Path to log file")
#     pid: int = Field(..., description="Process ID")
#     date_code: str = Field(..., description="Unique date code identifier")

#     model_config = {
#         "json_schema_extra": {
#             "example": {
#                 "start_local": "2025-08-08 05:07:01",
#                 "end_local": "2025-08-08 05:29:07",
#                 "start_utc": "2025-08-08T12:07:01Z",
#                 "end_utc": "2025-08-08T12:29:07Z",
#                 "elapsed_seconds": 1325.571,
#                 "elapsed_human": "22m 5s",
#                 "output_file": "/apps/data/pipeline/output-20250808_050701.data",
#                 "rowcount": 4342,
#                 "log_file": "/apps/data/pipeline/logs/job-20250808_050701.log",
#                 "pid": 38298,
#                 "date_code": "20250808_050701"
#             }
#         }
#     }

# class PipelineInfoResponse(BaseModel):
#     total: int = Field(..., description="Total number of matching records")
#     count: int = Field(..., description="Number of records in this response")
#     results: List[PipelineInfo] = Field(..., description="List of pipeline records")
    
# from pydantic import BaseModel, Field
# from typing import List

# class PipelineInfo(BaseModel):
#     start_local: str = Field(..., description="Start time in local timezone")
#     end_local: str = Field(..., description="End time in local timezone")
#     start_utc: str = Field(..., description="Start time in UTC (ISO format)")
#     end_utc: str = Field(..., description="End time in UTC (ISO format)")
#     elapsed_seconds: float = Field(..., description="Duration in seconds")
#     elapsed_human: str = Field(..., description="Human readable duration (e.g., '22m 5s')")
#     output_file: str = Field(..., description="Path to output data file")
#     rowcount: int = Field(..., description="Number of rows processed")
#     log_file: str = Field(..., description="Path to log file")
#     pid: int = Field(..., description="Process ID")
#     date_code: str = Field(..., description="Unique date code identifier")

#     class Config:
#         schema_extra = {
#             "example": {
#                 "start_local": "2025-08-08 05:07:01",
#                 "end_local": "2025-08-08 05:29:07",
#                 "start_utc": "2025-08-08T12:07:01Z",
#                 "end_utc": "2025-08-08T12:29:07Z",
#                 "elapsed_seconds": 1325.571,
#                 "elapsed_human": "22m 5s",
#                 "output_file": "/apps/data/pipeline/output-20250808_050701.data",
#                 "rowcount": 4342,
#                 "log_file": "/apps/data/pipeline/logs/job-20250808_050701.log",
#                 "pid": 38298,
#                 "date_code": "20250808_050701"
#             }
#         }

# class PipelineInfoResponse(BaseModel):
#     total: int = Field(..., description="Total number of matching records")
#     count: int = Field(..., description="Number of records in this response")
#     results: List[PipelineInfo] = Field(..., description="List of pipeline records")