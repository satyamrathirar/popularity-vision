import sys
sys.path.append('.') # Allows importing from parent directory

from sqlalchemy.dialects.postgresql import insert
from api.models import SessionLocal, Workflow, Base, engine
from scripts.ingest_discourse import fetch_discourse_workflows
from scripts.ingest_youtube import fetch_youtube_workflows
from scripts.ingest_google import fetch_google_trends

def upsert_workflows(db_session, workflow_data):
    # Logic to perform an "upsert":
    # INSERT if new (based on unique constraint), UPDATE if exists.
    # This is critical for the cron job.
    stmt = insert(Workflow).values(workflow_data)
    # ... add on_conflict_do_update logic ...
    db_session.execute(stmt)
    db_session.commit()

def main():
    Base.metadata.create_all(bind=engine) # Create table if it doesn't exist
    db = SessionLocal()

    all_workflows = []
    all_workflows.extend(fetch_discourse_workflows())
    all_workflows.extend(fetch_youtube_workflows())
    all_workflows.extend(fetch_google_trends())

    print(f"Total workflows to process: {len(all_workflows)}")

    if all_workflows:
         # Logic to batch upsert data into the database
         pass # Use the upsert_workflows function

    db.close()
    print("Ingestion process finished.")

if __name__ == "__main__":
    main()