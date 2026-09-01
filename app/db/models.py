from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean
from sqlalchemy.orm import declarative_base
from datetime import datetime, timezone

Base = declarative_base()

class CompanyRecord(Base):
    __tablename__ = "company_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sheet_row_number = Column(Integer, nullable=True, unique=True)
    company_name = Column(String(255), nullable=False)
    domain = Column(String(255), nullable=True)

    # Raw enrichment signals
    signal_http = Column(Text, nullable=True)
    signal_browser = Column(Text, nullable=True)
    signal_secondary = Column(Text, nullable=True)

    # LLM judgment
    fit_verdict = Column(String(50), nullable=True)
    confidence = Column(Float, nullable=True)
    follow_up_question = Column(Text, nullable=True)
    reasoning = Column(Text, nullable=True)

    processed = Column(Boolean, default=False)
    processed_at = Column(DateTime, nullable=True)