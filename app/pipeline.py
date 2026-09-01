"""
The full pipeline orchestrator:
Read unprocessed Sheet rows -> enrich (3 signals) -> persist to DB ->
judge with LLM -> sync verdict back to Sheet.
"""
import json
from datetime import datetime, timezone

from app.sheets import get_unprocessed_rows, write_verdict_to_row
from app.db.database import init_db, get_session
from app.db.models import CompanyRecord
from app.enrich.http_signal import get_http_signal
from app.enrich.browser_signal import get_browser_signal
from app.enrich.secondary_signal import get_secondary_signal
from app.judge import judge_company


def process_company(row: dict) -> dict:
    """
    Runs the full enrich -> persist -> judge -> sync pipeline for one company row.
    Returns a summary dict of what happened.
    """
    company_name = row["company_name"]
    domain = row["domain"]
    row_number = row["row_number"]

    print(f"[{company_name}] Enriching...")

    http_sig = get_http_signal(domain)
    browser_sig = get_browser_signal(company_name)
    secondary_sig = get_secondary_signal(company_name)

    print(f"[{company_name}] Judging...")
    verdict = judge_company(
        company_name=company_name,
        domain=domain,
        http_signal=http_sig,
        browser_signal=browser_sig,
        secondary_signal=secondary_sig,
    )

    timestamp = datetime.now(timezone.utc).isoformat()

    print(f"[{company_name}] Persisting to DB...")
    session = get_session()
    try:
        record = CompanyRecord(
            sheet_row_number=row_number,
            company_name=company_name,
            domain=domain,
            signal_http=json.dumps(http_sig),
            signal_browser=json.dumps(browser_sig),
            signal_secondary=json.dumps(secondary_sig),
            fit_verdict=verdict.get("fit_verdict"),
            confidence=verdict.get("confidence"),
            follow_up_question=verdict.get("follow_up_question"),
            reasoning=verdict.get("reasoning"),
            processed=True,
            processed_at=datetime.now(timezone.utc),
        )
        session.add(record)
        session.commit()
    finally:
        session.close()

    print(f"[{company_name}] Syncing verdict back to Sheet...")
    write_verdict_to_row(
        row_number=row_number,
        fit_verdict=verdict.get("fit_verdict", ""),
        confidence=verdict.get("confidence", 0.0),
        follow_up_question=verdict.get("follow_up_question", ""),
        timestamp=timestamp,
    )

    print(f"[{company_name}] Done -> {verdict.get('fit_verdict')} ({verdict.get('confidence')})")

    return {
        "company_name": company_name,
        "fit_verdict": verdict.get("fit_verdict"),
        "confidence": verdict.get("confidence"),
    }


def run_pipeline() -> list:
    """
    Finds all unprocessed rows in the Sheet and runs the full pipeline on each.
    Returns a list of result summaries.
    """
    init_db()
    rows = get_unprocessed_rows()
    print(f"Found {len(rows)} unprocessed compan(y/ies).")

    results = []
    for row in rows:
        try:
            result = process_company(row)
            results.append(result)
        except Exception as e:
            print(f"[{row['company_name']}] ERROR: {e}")
            results.append({"company_name": row["company_name"], "error": str(e)})

    return results


if __name__ == "__main__":
    summary = run_pipeline()
    print("\n--- Pipeline run summary ---")
    for s in summary:
        print(s)