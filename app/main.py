"""
FastAPI app exposing the pipeline:
- POST /trigger  -> run the pipeline on demand
- GET  /status   -> recent pipeline run results from DB
- GET  /companies -> list all processed companies
- Background scheduler runs the pipeline automatically every N minutes
"""
import os
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler

from app.pipeline import run_pipeline
from app.db.database import init_db, get_session
from app.db.models import CompanyRecord

SCHEDULE_MINUTES = int(os.getenv("SCHEDULE_MINUTES", "30"))

scheduler = BackgroundScheduler()

# Keep track of the last run for /status
last_run_summary = {"last_run_at": None, "results": []}


def scheduled_job():
    global last_run_summary
    print(f"[scheduler] Running pipeline at {datetime.now(timezone.utc).isoformat()}")
    results = run_pipeline()
    last_run_summary = {
        "last_run_at": datetime.now(timezone.utc).isoformat(),
        "results": results,
    }


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    scheduler.add_job(scheduled_job, "interval", minutes=SCHEDULE_MINUTES, id="pipeline_job")
    scheduler.start()
    print(f"Scheduler started - pipeline runs every {SCHEDULE_MINUTES} minutes.")
    yield
    scheduler.shutdown()


app = FastAPI(title="Company Intelligence Agent", lifespan=lifespan)


@app.get("/")
def root():
    return {
        "service": "Company Intelligence Agent",
        "status": "running",
        "schedule_minutes": SCHEDULE_MINUTES,
    }


@app.post("/trigger")
def trigger_pipeline():
    """Run the pipeline immediately, on demand."""
    global last_run_summary
    results = run_pipeline()
    last_run_summary = {
        "last_run_at": datetime.now(timezone.utc).isoformat(),
        "results": results,
    }
    return {"triggered": True, "results": results}


@app.get("/status")
def get_status():
    """Return the summary of the most recent pipeline run."""
    return last_run_summary


@app.get("/companies")
def list_companies():
    """Return all processed company records from the database."""
    session = get_session()
    try:
        records = session.query(CompanyRecord).all()
        return [
            {
                "id": r.id,
                "company_name": r.company_name,
                "domain": r.domain,
                "fit_verdict": r.fit_verdict,
                "confidence": r.confidence,
                "follow_up_question": r.follow_up_question,
                "reasoning": r.reasoning,
                "processed_at": r.processed_at.isoformat() if r.processed_at else None,
            }
            for r in records
        ]
    finally:
        session.close()


@app.get("/companies/{company_id}")
def get_company(company_id: int):
    """Return full detail for one company record, including raw signals."""
    session = get_session()
    try:
        record = session.query(CompanyRecord).filter(CompanyRecord.id == company_id).first()
        if not record:
            return {"error": "not found"}
        return {
            "id": record.id,
            "company_name": record.company_name,
            "domain": record.domain,
            "signal_http": record.signal_http,
            "signal_browser": record.signal_browser,
            "signal_secondary": record.signal_secondary,
            "fit_verdict": record.fit_verdict,
            "confidence": record.confidence,
            "follow_up_question": record.follow_up_question,
            "reasoning": record.reasoning,
            "processed_at": record.processed_at.isoformat() if record.processed_at else None,
        }
    finally:
        session.close()