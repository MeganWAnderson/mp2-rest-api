# MP2: Data Processing REST API

This project is a FastAPI application that lets users upload CSV files, store them in memory, and retrieve or clean them through HTTP endpoints. `GET /health` reports the API's status and version, `POST /upload` accepts a CSV file and returns its metadata, `GET /datasets/{dataset_id}` returns up to `limit` rows from a stored dataset, and `POST /datasets/{dataset_id}/process` validates and cleans a stored dataset (duplicate removal, missing-value handling, and optional outlier removal) using the reusable MP1 pipeline modules in `data_pipeline/`. Request-logging middleware assigns each request an ID, logs its status code and duration, and returns the ID in an `X-Request-ID` header. The API is tested with pytest and FastAPI's TestClient.

## Project Structure

- `main.py` — FastAPI app and endpoints
- `src/` — response/request models, in-memory storage, logging setup, and middleware
- `data_pipeline/` — validation, processing, and reporting modules reused from MP1
- `fixtures/sample_data.csv` — sample data for manual testing and tests
- `tests/` — API tests

## How to Run

Install dependencies:

    python -m pip install -r requirements.txt

Start the server:

    python -m uvicorn main:app --reload

Then open http://127.0.0.1:8000/docs to try the endpoints.

## Running Tests

    python -m pytest tests -v