import io
import json
import logging
from pathlib import Path
import pandas as pd
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from src import DatasetInfo, DatasetStorage, HealthResponse, setup_logging

setup_logging(verbose=True)
logger = logging.getLogger(__name__)

app = FastAPI(title="Data Processing API", version="1.0.0")
storage = DatasetStorage()

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
        logger.warning(f"Uploaded file is unreadable: {file.filename}")
        raise HTTPException(status_code=400, detail="Uploaded file is unreadable.")
    except pd.errors.ParserError:
        logger.warning(f"Uploaded file is unreadable: {file.filename}")
        raise HTTPException(status_code=400, detail="Uploaded file is unreadable.")
    except UnicodeDecodeError:
        logger.warning(f"Uploaded file is unreadable: {file.filename}")
        raise HTTPException(status_code=400, detail="Uploaded file is unreadable.")
    
    dataset_id = storage.save(df, file.filename)
    metadata = storage.get_metadata(dataset_id)
    logger.info(f"Uploaded dataset: id={dataset_id}, filename={file.filename}, rows={metadata.rows}")
    return metadata

@app.get("/datasets/{dataset_id}")
def get_dataset(dataset_id: int, limit: int = Query(default=100, ge=1)):
    """Return up to limit rows from a stored dataset."""
    df = storage.get(dataset_id)
    if df is None:
        logger.warning(f"Dataset {dataset_id} not found.")  
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    records = json.loads(df.head(limit).to_json(orient="records"))
    response = {
        "id": dataset_id,
        "data": records, 
        "total_rows": df.shape[0],
    }
    logger.info(f"Retrieved dataset: id={dataset_id}, returned_rows={len(records)}")
    return response
