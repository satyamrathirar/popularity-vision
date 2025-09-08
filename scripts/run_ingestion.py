import sys
sys.path.append('.')

from sqlalchemy.dialects.postgresql import insert
from api.models import SessionLocal, Workflow, Base, engine
from scripts.ingest_discourse import fetch_discourse_workflows
from scripts.ingest_youtube import fetch_youtube_workflows
from scripts.ingest_google import fetch_google_trends

def upsert_workflows(db_session, workflow_data):
    if not workflow_data:
        print("No workflow data to upsert.")
        return
        
    # The 'insert' function from SQLAlchemy's dialect provides the 'on_conflict_do_update' method
    stmt = insert(Workflow).values(workflow_data)
    
    # Define what to do on conflict (when unique constraint is violated)
    update_stmt = stmt.on_conflict_do_update(
        index_elements=['workflow_name', 'platform', 'country'], # The columns of our unique constraint
        set_=dict(
            popularity_metrics=stmt.excluded.popularity_metrics,
            source_url=stmt.excluded.source_url
            # We can also update the 'last_updated' column automatically
        )
    )
    db_session.execute(update_stmt)
    db_session.commit()
    print(f"Upserted {len(workflow_data)} records into the database.")

def main():
    # This ensures the table exists before we try to insert data
    Base.metadata.create_all(bind=engine) 
    db = SessionLocal()
    
    all_workflows = []
    all_workflows.extend(fetch_discourse_workflows())
    all_workflows.extend(fetch_youtube_workflows())
    all_workflows.extend(fetch_google_trends())

    print(f"Total workflows to process: {len(all_workflows)}")
    
    upsert_workflows(db, all_workflows)
    
    db.close()
    print("Ingestion process finished.")

if __name__ == "__main__":
    main()