import sys
sys.path.append('.')

from sqlalchemy.dialects.postgresql import insert
from api.models import SessionLocal, Workflow, Base, engine
from scripts.ingest_discourse import fetch_discourse_workflows
from scripts.ingest_youtube import fetch_youtube_workflows
from scripts.ingest_google import fetch_google_trends  # Re-enabled with Google Ads approach

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
    target_workflows = 350  # Target 300-400 workflows
    
    print("=== TESTING INGESTION: 300-400 WORKFLOWS TARGET ===")
    print("Distribution: ~100 Discourse + ~150 YouTube + ~100 Google Trends\n")
    
    # Phase 1: Discourse - Target ~100 workflows (limited keywords and pages)
    print("=== PHASE 1: Discourse Ingestion ===")
    print("Target: ~100 workflows")
    discourse_workflows = fetch_discourse_workflows(max_keywords=3, max_pages_per_keyword=2)  # 3 keywords, 2 pages each
    print(f"Discourse collected: {len(discourse_workflows)} workflows")
    all_workflows.extend(discourse_workflows)
    
    # Phase 2: YouTube - Target ~150 workflows (more keywords and pages)
    print(f"\n=== PHASE 2: YouTube Ingestion ===")
    print("Target: ~150 workflows")
    # Load first 5 keywords for YouTube with more pages
    from scripts.ingest_discourse import load_keywords_from_file
    limited_keywords = load_keywords_from_file()[:5]
    youtube_workflows = fetch_youtube_workflows(keywords=limited_keywords, max_pages_per_keyword=3)  # 5 keywords, 3 pages each
    print(f"YouTube collected: {len(youtube_workflows)} workflows")
    all_workflows.extend(youtube_workflows)
    
    # Phase 3: Google Trends - Target ~100 workflows (re-enabled with Google Ads)
    print(f"\n=== PHASE 3: Google Trends Ingestion ===")
    print("Target: ~100 workflows")
    # Use limited keywords for Google Trends
    google_workflows = fetch_google_trends(max_keywords=5)  # 5 keywords × 2 countries × avg 10 workflows = ~100
    print(f"Google Trends collected: {len(google_workflows)} workflows")
    all_workflows.extend(google_workflows)

    print(f"\n=== TESTING SUMMARY ===")
    print(f"Target workflows: {target_workflows}")
    print(f"Actual collected: {len(all_workflows)}")
    print(f"Target achieved: {'✓' if len(all_workflows) >= target_workflows else '✗'} ({len(all_workflows)}/{target_workflows})")
    
    # Platform breakdown
    discourse_count = len([w for w in all_workflows if w['platform'] == 'Discourse'])
    youtube_count = len([w for w in all_workflows if w['platform'] == 'YouTube'])
    google_count = len([w for w in all_workflows if w['platform'] == 'Google Trends'])
    
    print(f"\nPlatform Breakdown:")
    print(f"  - Discourse: {discourse_count} workflows")
    print(f"  - YouTube: {youtube_count} workflows") 
    print(f"  - Google Trends: {google_count} workflows")
    
    upsert_workflows(db, all_workflows)
    
    db.close()
    print("\nTest ingestion process finished successfully!")

if __name__ == "__main__":
    main()
