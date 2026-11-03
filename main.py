"""
Data Processing API
DS 3500 - MP2

FastAPI application that uploads CSV files, stores them in memory,
and validates, processes, and retrieves datasets using MP1 modules.
"""

# Imports
import io
import json
import logging
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, File, HTTPException, Query, UploadFile

# Local Imports
from data_pipeline import create_cleaning_report, process_data, validate_dataframe
from src import (
    DatasetInfo,
    DatasetStorage,
    HealthResponse,
    ProcessConfig,
    ProcessingReport,
    log_requests,
    setup_logging,
)

# Set up logging
setup_logging(verbose=True)
logger = logging.getLogger(__name__)

# Set up FastAPI app and dataset storage
app = FastAPI(title="Data Processing API", version="1.0.0")
app.middleware("http")(log_requests)
storage = DatasetStorage()

# API Endpoints
@app.get("/health", response_model=HealthResponse)
def health_check():
    """Return the application status and version."""
    return HealthResponse(status="ok", version="1.0.0")


@app.post("/upload", response_model=DatasetInfo)
async def upload_dataset(file: UploadFile = File(...)):
    """Read and store a CSV upload."""
    extension = Path(file.filename or "").suffix.lower()
    if extension != ".csv":
        logger.warning(f"Unsupported file format: {extension}")
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")

    contents = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(contents))
    except pd.errors.EmptyDataError:
        logger.warning(f"Uploaded CSV file is empty: {file.filename}")
        raise HTTPException(status_code=400, detail="Uploaded CSV file is empty.")
    except pd.errors.ParserError:
        logger.warning(f"Uploaded file could not be parsed as CSV: {file.filename}")
        raise HTTPException(status_code=400, detail="Uploaded file could not be parsed as CSV.")
    except UnicodeDecodeError:
        logger.warning(f"Uploaded file is not valid UTF-8 text: {file.filename}")
        raise HTTPException(status_code=400, detail="Uploaded file is not valid UTF-8 text.")

    dataset_id = storage.save(df, file.filename)
    metadata = storage.get_metadata(dataset_id)
    logger.info(f"Uploaded dataset: id={dataset_id}, filename={file.filename}, rows={metadata.rows}")
    return metadata


@app.get("/datasets/{dataset_id}")
def get_dataset(dataset_id: int, limit: int = Query(default=100, ge=1)):
    """Return up to limit rows from a stored dataset."""
    df = storage.get(dataset_id)
    if df is None:
        logger.warning(f"Dataset not found: {dataset_id}")
        raise HTTPException(status_code=404, detail="Dataset not found")

    records = json.loads(df.head(limit).to_json(orient="records"))
    response = {
        "id": dataset_id,
        "data": records,
        "total_rows": df.shape[0],
    }
    logger.info(f"Retrieved dataset: id={dataset_id}, returned_rows={len(records)}")
    return response


@app.post(
    "/datasets/{dataset_id}/process",
    response_model=ProcessingReport
)
def process_dataset(dataset_id: int, config: ProcessConfig):
    """Validate and process a stored dataset using MP1 functions."""
    # Retrieve a copy of the stored dataset.
    df = storage.get(dataset_id)
    if df is None:
        logger.warning(f"Dataset {dataset_id} not found for processing.")
        raise HTTPException(status_code=404, detail="Dataset not found")

    # Convert the request model to the dict format MP1 expects.
    config_dict = config.model_dump()
    required = config_dict["validation"]["required_columns"]
    numeric = config_dict["validation"]["numeric_columns"]

    # Check numeric columns exist
    missing_cols = [col for col in numeric if col not in df.columns]
    if missing_cols:
        logger.warning(f"Numeric columns not found: {missing_cols}")
        raise HTTPException(
            status_code=400,
            detail=f"Numeric columns not found: {missing_cols}",
        )

    # Validate, then process a copy of the validated data
    try:
        validated = validate_dataframe(
            df, required_columns=required, numeric_columns=numeric
        )
        validation_rows_removed = len(df) - len(validated)
        validated_copy = validated.copy()

        processed = process_data(validated_copy, config_dict)
        cleaning_report = create_cleaning_report(validated_copy, processed)
    except ValueError as error:
        logger.warning(f"Processing failed for dataset {dataset_id}: {error}")
        raise HTTPException(status_code=400, detail=str(error))

    # Save only after validation and processing both succeed.
    storage.update(dataset_id, processed)

    logger.info(
        f"Processed dataset: id={dataset_id}, "
        f"validation_rows_removed={validation_rows_removed}, "
        f"rows_before={cleaning_report['rows_before']}, "
        f"rows_after={cleaning_report['rows_after']}"
    )

    return {
        "id": dataset_id,
        "validation_rows_removed": validation_rows_removed,
        "cleaning_report": cleaning_report,
    }
