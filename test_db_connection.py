from app.db.database import init_db, get_session
from app.db.models import CompanyRecord

def main():
    print("Initializing database (creating tables if needed)...")
    init_db()
    print("Tables created successfully.")

    session = get_session()
    try:
        # Insert a test row
        test_record = CompanyRecord(
            company_name="TestCorp",
            domain="testcorp.com",
            fit_verdict="Pending",
            confidence=0.0,
        )
        session.add(test_record)
        session.commit()
        print(f"Inserted test record with id={test_record.id}")

        # Read it back
        rows = session.query(CompanyRecord).all()
        print(f"Total rows in table: {len(rows)}")
        for r in rows:
            print(r.id, r.company_name, r.domain, r.fit_verdict)
    finally:
        session.close()

if __name__ == "__main__":
    main()