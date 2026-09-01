"""
Drops and recreates all tables - use only in development when the schema changes.
"""
from app.db.database import engine, init_db
from app.db.models import Base

print("Dropping all tables...")
Base.metadata.drop_all(bind=engine)
print("Recreating tables with current schema...")
init_db()
print("Done.")