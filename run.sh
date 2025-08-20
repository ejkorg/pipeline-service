#!/bin/bash

# Pipeline Info API Runner Script
# FastAPI application startup script

set -e  # Exit on any error

# Configuration
DEFAULT_HOST="10.253.112.87"
DEFAULT_PORT="8001"
DEFAULT_BACKEND="jsonl"
DEFAULT_JSONL_PATH="/apps/exensio_data/reference_data/benchmark/benchmark.jsonl"

# Get configuration from environment or use defaults
HOST=${HOST:-$DEFAULT_HOST}
PORT=${PORT:-$DEFAULT_PORT}
PIPELINE_BACKEND=${PIPELINE_BACKEND:-$DEFAULT_BACKEND}
PIPELINE_JSONL_PATH=${PIPELINE_JSONL_PATH:-$DEFAULT_JSONL_PATH}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if required files exist
check_dependencies() {
    print_status "Checking dependencies..."
    
    # Check Python files
    for file in "main.py" "models.py" "repository.py"; do
        if [ ! -f "$file" ]; then
            print_error "Required file $file not found!"
            exit 1
        fi
    done
    
    # Check JSONL file if using JSONL backend
    if [ "$PIPELINE_BACKEND" = "jsonl" ]; then
        if [ ! -f "$PIPELINE_JSONL_PATH" ]; then
            print_warning "JSONL file $PIPELINE_JSONL_PATH not found. Will create sample data."
            create_sample_data
        fi
    fi
    
    print_status "Dependencies check passed ✓"
}

# Function to create sample JSONL data for testing
# create_sample_data() {
#     print_status "Creating sample pipeline data..."
    
#     # Create directory if it doesn't exist
#     mkdir -p "$(dirname "$PIPELINE_JSONL_PATH")"
    
#     cat > "$PIPELINE_JSONL_PATH" << 'EOF'
# {"start_local": "2025-08-08 05:07:01", "end_local": "2025-08-08 05:29:07", "start_utc": "2025-08-08T12:07:01Z", "end_utc": "2025-08-08T12:29:07Z", "elapsed_seconds": 1325.571, "elapsed_human": "22m 5s", "output_file": "/apps/data/pipeline/output-20250808_050701.data", "rowcount": 4342, "log_file": "/apps/data/pipeline/logs/job-20250808_050701.log", "pid": 38298, "date_code": "20250808_050701"}
# {"start_local": "2025-08-08 06:07:01", "end_local": "2025-08-08 06:29:25", "start_utc": "2025-08-08T13:07:01Z", "end_utc": "2025-08-08T13:29:25Z", "elapsed_seconds": 1343.854, "elapsed_human": "22m 23s", "output_file": "/apps/data/pipeline/output-20250808_060701.data", "rowcount": 4387, "log_file": "/apps/data/pipeline/logs/job-20250808_060701.log", "pid": 117881, "date_code": "20250808_060701"}
# {"start_local": "2025-08-08 07:07:01", "end_local": "2025-08-08 07:28:15", "start_utc": "2025-08-08T14:07:01Z", "end_utc": "2025-08-08T14:28:15Z", "elapsed_seconds": 1274.123, "elapsed_human": "21m 14s", "output_file": "/apps/data/pipeline/output-20250808_070701.data", "rowcount": 4156, "log_file": "/apps/data/pipeline/logs/job-20250808_070701.log", "pid": 125432, "date_code": "20250808_070701"}
# EOF
#     print_status "Sample data created at $PIPELINE_JSONL_PATH"
# }
create_sample_data() {
    print_status "Creating sample pipeline data..."
    
    # Create directory if it doesn't exist
    mkdir -p "$(dirname "$PIPELINE_JSONL_PATH")"
    
    cat > "$PIPELINE_JSONL_PATH" << 'EOF'
{"start_local": "2025-08-08 05:07:01", "end_local": "2025-08-08 05:29:07", "start_utc": "2025-08-08T12:07:01Z", "end_utc": "2025-08-08T12:29:07Z", "elapsed_seconds": 1325.571, "elapsed_human": "22m 5s", "output_file": "/apps/data/pipeline/sales_etl/output-20250808_050701.data", "rowcount": 4342, "log_file": "/apps/data/pipeline/logs/sales_etl-20250808_050701.log", "pid": 38298, "date_code": "20250808_050701", "pipeline_name": "sales_etl", "script_name": "process_sales_data.py", "pipeline_type": "batch", "environment": "prod"}
{"start_local": "2025-08-08 06:07:01", "end_local": "2025-08-08 06:29:25", "start_utc": "2025-08-08T13:07:01Z", "end_utc": "2025-08-08T13:29:25Z", "elapsed_seconds": 1343.854, "elapsed_human": "22m 23s", "output_file": "/apps/data/pipeline/user_analytics/output-20250808_060701.data", "rowcount": 4387, "log_file": "/apps/data/pipeline/logs/user_analytics-20250808_060701.log", "pid": 117881, "date_code": "20250808_060701", "pipeline_name": "user_analytics", "script_name": "analyze_user_behavior.py", "pipeline_type": "batch", "environment": "prod"}
{"start_local": "2025-08-08 07:07:01", "end_local": "2025-08-08 07:28:15", "start_utc": "2025-08-08T14:07:01Z", "end_utc": "2025-08-08T14:28:15Z", "elapsed_seconds": 1274.123, "elapsed_human": "21m 14s", "output_file": "/apps/data/pipeline/ml_training/output-20250808_070701.data", "rowcount": 4156, "log_file": "/apps/data/pipeline/logs/ml_training-20250808_070701.log", "pid": 125432, "date_code": "20250808_070701", "pipeline_name": "ml_training", "script_name": "train_recommendation_model.py", "pipeline_type": "ml", "environment": "prod"}
EOF
    print_status "Sample data created at $PIPELINE_JSONL_PATH"
}

# Function to check Python packages
check_python_packages() {
    print_status "Checking Python packages..."
    
    python3.13 -c "import fastapi, uvicorn, pydantic" 2>/dev/null || {
        print_error "Required Python packages not found!"
        print_status "Please install with: pip install fastapi uvicorn pydantic"
        exit 1
    }
    
    # Check Oracle packages if using Oracle backend
    if [ "$PIPELINE_BACKEND" = "oracle" ]; then
        python3.13 -c "import oracledb" 2>/dev/null || {
            print_error "python-oracledb package not found (required for Oracle backend)!"
            print_status "Please install with: pip install python-oracledb"
            exit 1
        }
    fi
    
    print_status "Python packages check passed ✓"
}

# Function to validate Oracle configuration
check_oracle_config() {
    if [ "$PIPELINE_BACKEND" = "oracle" ]; then
        print_status "Validating Oracle configuration..."
        
        if [ -z "$ORACLE_DSN" ] || [ -z "$ORACLE_USER" ] || [ -z "$ORACLE_PASSWORD" ]; then
            print_error "Oracle backend selected but missing configuration!"
            echo "Required environment variables:"
            echo "  ORACLE_DSN=host:port/service"
            echo "  ORACLE_USER=username"
            echo "  ORACLE_PASSWORD=password"
            echo "  ORACLE_TABLE=table_name (optional, defaults to PIPELINE_RUNS)"
            exit 1
        fi
        
        print_status "Oracle configuration validated ✓"
    fi
}

# Function to start the application
start_app() {
    print_status "Starting Pipeline Info API..."
    print_status "Configuration:"
    echo "  Backend: $PIPELINE_BACKEND"
    echo "  Host: $HOST"
    echo "  Port: $PORT"
    
    if [ "$PIPELINE_BACKEND" = "jsonl" ]; then
        echo "  JSONL Path: $PIPELINE_JSONL_PATH"
    else
        echo "  Oracle DSN: $ORACLE_DSN"
        echo "  Oracle User: $ORACLE_USER"
        echo "  Oracle Table: ${ORACLE_TABLE:-PIPELINE_RUNS}"
    fi
    
    echo ""
    print_status "API will be available at:"
    echo "  Docs: http://$HOST:$PORT/docs"
    echo "  Health: http://$HOST:$PORT/health"
    echo "  API: http://$HOST:$PORT/get_pipeline_info"
    echo ""
    print_status "Starting server..."
    
    # Export environment variables
    export PIPELINE_BACKEND
    export PIPELINE_JSONL_PATH
    export ORACLE_DSN
    export ORACLE_USER
    export ORACLE_PASSWORD
    export ORACLE_TABLE
    
    # Start the server
    if command -v uvicorn >/dev/null 2>&1; then
        uvicorn main:app --host "$HOST" --port "$PORT" --reload
    else
        python3.13 -m uvicorn main:app --host "$HOST" --port "$PORT" --reload
    fi
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  -p, --port     Port to run on (default: 8001)"
    echo "  --host         Host to bind to (default: 10.253.112.87)"
    echo "  --backend      Backend type: jsonl|oracle (default: jsonl)"
    echo "  --jsonl-path   Path to JSONL file (default: /apps/exensio_data/reference_data/benchmark/benchmark.jsonl)"
    echo ""
    echo "Environment Variables:"
    echo "  HOST                  Host to bind to"
    echo "  PORT                  Port to run on"
    echo "  PIPELINE_BACKEND      Backend type (jsonl|oracle)"
    echo "  PIPELINE_JSONL_PATH   Path to JSONL file"
    echo "  ORACLE_DSN            Oracle connection string"
    echo "  ORACLE_USER           Oracle username"
    echo "  ORACLE_PASSWORD       Oracle password"
    echo "  ORACLE_TABLE          Oracle table name"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Run with defaults"
    echo "  $0 -p 9000                          # Run on port 9000"
    echo "  $0 --backend oracle                 # Use Oracle backend"
    echo "  PIPELINE_BACKEND=oracle $0          # Use Oracle via env var"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_usage
            exit 0
            ;;
        -p|--port)
            PORT="$2"
            shift 2
            ;;
        --host)
            HOST="$2"
            shift 2
            ;;
        --backend)
            PIPELINE_BACKEND="$2"
            shift 2
            ;;
        --jsonl-path)
            PIPELINE_JSONL_PATH="$2"
            shift 2
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Main execution
main() {
    print_status "Pipeline Info API Startup Script"
    print_status "Created by: ejkorg"
    print_status "Date: 2025-08-08 01:14:22 UTC"
    echo ""
    
    check_dependencies
    check_python_packages
    check_oracle_config
    start_app
}

# Run main function
main "$@"