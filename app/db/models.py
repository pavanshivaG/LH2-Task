from sqlalchemy import Column, Integer, String, Text, DateTime, Float
from sqlalchemy.orm import declarative_base
from datetime import datetime, timezone

Base = declarative_base()

class CompanyRecord(Base):
    __tablename__ = "company_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_name = Column(String(255), nullable=False)
    domain = Column(String(255), nullable=True)

    # Raw enrichment signals (stored as text/JSON strings)
    signal_browser = Column(Text, nullable=True)      # from Playwright browser automation
    signal_http = Column(Text, nullable=True)          # from a plain HTTP/API call
    signal_secondary = Column(Text, nullable=True)     # third independent signal

    # LLM judgment
    fit_verdict = Column(String(50), nullable=True)        # e.g. "Strong Fit" / "Weak Fit" / "No Fit"
    confidence = Column(Float, nullable=True)               # e.g. 0.0 - 1.0
    follow_up_question = Column(Text, nullable=True)
    reasoning = Column(Text, nullable=True)                 # the LLM's reasoning trail

    processed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))