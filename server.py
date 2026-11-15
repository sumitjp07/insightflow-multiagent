"""
server.py – InsightFlow Enterprise FastAPI Backend
===================================================
High-performance REST API powering the modern InsightFlow Web App.
Connects directly to LangGraph agents, SQLite memory, and ReportLab PDF generator.
"""

import sys
import os
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import pandas as pd

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Ensure project root is on sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

import config
from tools.data_tools import load_dataset, get_data_summary, clean_dataset, get_column_stats
from tools.file_tools import save_uploaded_file, get_sample_files
from tools.pdf_generator import generate_pdf_report
from workflow.graph import run_insightflow_pipeline
from memory.session_store import SessionStore

app = FastAPI(
    title="InsightFlow Intelligence Platform API",
    version=config.APP_VERSION,
    description="Multi-Agent AI Data Research & Analysis Backend"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session tracking
CURRENT_STATE: Dict[str, Any] = {
    "df": None,
    "file_name": "sales_data.csv",
    "latest_result": None
}

# Auto-load sales_data.csv on startup
def _preload_default():
    p = BASE_DIR / "sample_data" / "sales_data.csv"
    if p.exists():
        res = load_dataset(str(p))
        if res["success"]:
            CURRENT_STATE["df"] = res["data"]
            CURRENT_STATE["file_name"] = "sales_data.csv"

_preload_default()


# ── Schemas ────────────────────────────────────────────────
class RunAgentRequest(BaseModel):
    query: str
    file_name: Optional[str] = "sales_data.csv"


# ── Endpoints ──────────────────────────────────────────────
@app.get("/api/datasets")
async def list_datasets():
    """Lists all available sample datasets and uploaded files."""
    samples = get_sample_files()
    return {
        "success": True,
        "active_dataset": CURRENT_STATE["file_name"],
        "datasets": samples
    }


@app.post("/api/switch-dataset")
async def switch_dataset(file_name: str = Form(...)):
    """Switches the active dataset to a sample or uploaded file."""
    path = BASE_DIR / "sample_data" / file_name
    if not path.exists():
        path = BASE_DIR / "uploads" / file_name
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"File {file_name} not found")

    res = load_dataset(str(path))
    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["message"])

    CURRENT_STATE["df"] = res["data"]
    CURRENT_STATE["file_name"] = file_name
    CURRENT_STATE["latest_result"] = None

    return {
        "success": True,
        "message": f"Switched to {file_name}",
        "file_name": file_name,
        "rows": len(res["data"]),
        "columns": len(res["data"].columns)
    }


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Uploads and ingests a custom CSV or Excel file."""
    save_res = save_uploaded_file(file)
    if not save_res["success"]:
        raise HTTPException(status_code=400, detail=save_res.get("error", "Upload failed"))

    load_res = load_dataset(save_res["file_path"])
    if not load_res["success"]:
        raise HTTPException(status_code=400, detail=load_res["message"])

    CURRENT_STATE["df"] = load_res["data"]
    CURRENT_STATE["file_name"] = file.filename
    CURRENT_STATE["latest_result"] = None

    return {
        "success": True,
        "message": f"Successfully ingested {file.filename}",
        "file_name": file.filename,
        "rows": len(load_res["data"]),
        "columns": len(load_res["data"].columns)
    }


@app.get("/api/data-preview")
async def data_preview():
    """Returns dataset summary, profiling KPIs, and sample rows."""
    df = CURRENT_STATE["df"]
    if df is None:
        return {"success": False, "message": "No dataset active"}

    summary_res = get_data_summary(df)
    summary = summary_res.get("summary", {})

    # Convert head 20 rows to clean records
    clean_records = df.head(20).fillna("").to_dict(orient="records")

    return {
        "success": True,
        "file_name": CURRENT_STATE["file_name"],
        "rows": len(df),
        "columns": list(df.columns),
        "numeric_columns": summary.get("numeric_columns", []),
        "categorical_columns": summary.get("categorical_columns", []),
        "missing_count": int(df.isnull().sum().sum()),
        "duplicate_count": int(df.duplicated().sum()),
        "memory_kb": round(df.memory_usage(deep=True).sum() / 1024, 1),
        "records": clean_records
    }


@app.post("/api/run-agent")
async def run_agent(payload: RunAgentRequest):
    """Executes the complete LangGraph Multi-Agent pipeline."""
    df = CURRENT_STATE["df"]
    if df is None:
        raise HTTPException(status_code=400, detail="Please select or upload a dataset first.")

    query = payload.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    t0 = time.time()
    result = run_insightflow_pipeline(query, df, file_name=CURRENT_STATE["file_name"])
    duration = round(time.time() - t0, 2)
    result["execution_time_seconds"] = duration
    CURRENT_STATE["latest_result"] = result

    # Persist in SQLite
    try:
        store = SessionStore()
        sess_id = f"api_{int(time.time())}"
        store.create_session(
            session_id=sess_id,
            dataset_name=CURRENT_STATE["file_name"],
            row_count=len(df),
            column_count=len(df.columns),
            user_query=query,
            status=result.get("status", "completed")
        )
        ev = result.get("evaluation_result", {})
        store.record_evaluation(
            session_id=sess_id,
            accuracy=ev.get("calculation_accuracy_pct", 100.0),
            coverage=ev.get("evidence_coverage_pct", 100.0),
            retries=result.get("retry_count", 0),
            status="approved" if result.get("is_approved") else "flagged"
        )
        store.save_report(sess_id, result.get("final_report_md", ""))
    except Exception as e:
        print(f"SQLite save warning: {e}")

    # Generate PDF in background
    pdf_res = generate_pdf_report(result)
    result["pdf_generated"] = pdf_res["success"]
    result["pdf_filename"] = pdf_res.get("file_name", "")

    return {
        "success": True,
        "query": query,
        "duration": duration,
        "status": result.get("status"),
        "subtasks": result.get("subtasks", []),
        "evaluation": result.get("evaluation_result", {}),
        "retry_count": result.get("retry_count", 0),
        "insights": result.get("insights", []),
        "key_drivers": result.get("key_drivers", []),
        "anomalies": result.get("anomalies_detected", []),
        "report_markdown": result.get("final_report_md", ""),
        "evaluation_logs": result.get("evaluation_logs", [])
    }


@app.get("/api/download-pdf")
async def download_pdf():
    """Serves the latest generated PDF report."""
    res = CURRENT_STATE.get("latest_result")
    if not res:
        raise HTTPException(status_code=404, detail="No report generated yet.")

    pdf_res = generate_pdf_report(res)
    if not pdf_res["success"]:
        raise HTTPException(status_code=500, detail="Failed to compile PDF.")

    p = Path(pdf_res["pdf_path"])
    return FileResponse(
        path=str(p),
        filename=p.name,
        media_type="application/pdf"
    )


@app.get("/api/history")
async def get_history():
    """Fetches persistent history from SQLite."""
    store = SessionStore()
    sessions = store.get_recent_sessions(limit=15)
    return {"success": True, "sessions": sessions}


# ── Mount Static Web Assets ────────────────────────────────
static_dir = BASE_DIR / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    """Serves the modern enterprise dashboard."""
    index_path = static_dir / "index.html"
    if index_path.exists():
        return HTMLResponse(content=index_path.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>InsightFlow Web App Loading...</h1>")


if __name__ == "__main__":
    import uvicorn
    print("\n⚡ Starting InsightFlow High-Standard Web Server on http://localhost:8000 ...\n")
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)

