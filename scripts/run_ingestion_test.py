import sys
sys.path.append('.')

from sqlalchemy.dialects.postgresql import insert
from api.models import SessionLocal, Workflow, Base, engine
from scripts.ingest_discourse import fetch_discourse_workflows
from scripts.ingest_youtube import fetch_youtube_workflows
# from scripts.ingest_google import fetch_google_trends  # Disabled - API not working

def upsert_workflows(db_session, workflow_data):
    if not workflow_data:
        print("No workflow data to upsert.")
        return
    
    # Remove duplicates based on unique constraint (workflow_name, platform, country)
    seen = set()
    unique_workflows = []
    duplicates_count = 0
    
    for workflow in workflow_data:
        key = (workflow['workflow_name'], workflow['platform'], workflow['country'])
        if key not in seen:
            seen.add(key)
            unique_workflows.append(workflow)
        else:
            duplicates_count += 1
    
    print(f"Removed {duplicates_count} duplicate workflows. Processing {len(unique_workflows)} unique workflows.")
        
    # The 'insert' function from SQLAlchemy's dialect provides the 'on_conflict_do_update' method
    stmt = insert(Workflow).values(unique_workflows)
    
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
    print(f"Upserted {len(unique_workflows)} records into the database.")

def main():
    # This ensures the table exists before we try to insert data
    Base.metadata.create_all(bind=engine) 
    db = SessionLocal()
    
    all_workflows = []
    target_workflows = 200
    
    print("=== TESTING INGESTION: 200 WORKFLOWS TARGET ===")
    print("Distribution: ~100 Discourse + ~100 YouTube (Google Trends disabled)\n")
    
    # Phase 1: Discourse - Target ~100 workflows (limited keywords and pages)
    print("=== PHASE 1: Discourse Ingestion ===")
    print("Target: ~100 workflows")
    discourse_workflows = fetch_discourse_workflows(max_keywords=3, max_pages_per_keyword=2)  # 3 keywords, 2 pages each
    print(f"Discourse collected: {len(discourse_workflows)} workflows")
    all_workflows.extend(discourse_workflows)
    
    # Phase 2: YouTube - Target ~100 workflows (limited keywords and pages)
    print(f"\n=== PHASE 2: YouTube Ingestion ===")
    print("Target: ~100 workflows")
    # Load first 3 keywords manually for YouTube
    from scripts.ingest_discourse import load_keywords_from_file
    limited_keywords = load_keywords_from_file()[:3]
    youtube_workflows = fetch_youtube_workflows(keywords=limited_keywords, max_pages_per_keyword=2)  # 3 keywords, 2 pages each
    print(f"YouTube collected: {len(youtube_workflows)} workflows")
    all_workflows.extend(youtube_workflows)
    
    # Phase 3: Google Trends - DISABLED
    print(f"\n=== PHASE 3: Google Trends Ingestion ===")
    print("SKIPPED: Google Trends API currently disabled due to issues")
    print("Google Trends collected: 0 workflows")

    print(f"\n=== TESTING SUMMARY ===")
    print(f"Target workflows: {target_workflows}")
    print(f"Actual collected: {len(all_workflows)}")
    print(f"Target achieved: {'✓' if len(all_workflows) >= target_workflows else '✗'} ({len(all_workflows)}/{target_workflows})")
    
    # Platform breakdown
    discourse_count = len([w for w in all_workflows if w['platform'] == 'Discourse'])
    youtube_count = len([w for w in all_workflows if w['platform'] == 'YouTube'])
    google_count = 0  # Disabled
    
    print(f"\nPlatform Breakdown:")
    print(f"  - Discourse: {discourse_count} workflows")
    print(f"  - YouTube: {youtube_count} workflows") 
    print(f"  - Google Trends: {google_count} trends (disabled)")
    
    upsert_workflows(db, all_workflows)
    
    db.close()
    print("\nTest ingestion process finished successfully!")

if __name__ == "__main__":
    main()
