#!/usr/bin/env python3
"""

It includes proper error handling, logging, and exit codes for monitoring.

Usage:
    # Daily full ingestion at 2 AM
    0 2 * * * /path/to/run_cron_ingestion.py --mode=full
    
    # Test ingestion every 4 hours
    0 */4 * * * /path/to/run_cron_ingestion.py --mode=test
    
    # Weekly deep analysis on Sundays at 1 AM  
    0 1 * * 0 /path/to/run_cron_ingestion.py --mode=deep
"""

import sys
import os
import argparse
import logging
import traceback
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.dialects.postgresql import insert
from api.models import SessionLocal, Workflow, Base, engine
from scripts.ingest_discourse import fetch_discourse_workflows
from scripts.ingest_youtube import fetch_youtube_workflows
from scripts.ingest_google import fetch_google_trends


def setup_logging(log_level=logging.INFO):
    """Configure logging for cron job execution."""
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f"ingestion_{datetime.now().strftime('%Y%m%d')}.log"
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)


def upsert_workflows(db_session, workflow_data, logger):
    """Upsert workflows with detailed logging."""
    if not workflow_data:
        logger.warning("No workflow data to upsert.")
        return 0
    
    # Remove duplicates
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
    
    logger.info(f"Removed {duplicates_count} duplicate workflows. Processing {len(unique_workflows)} unique workflows.")
    
    try:
        stmt = insert(Workflow).values(unique_workflows)
        update_stmt = stmt.on_conflict_do_update(
            index_elements=['workflow_name', 'platform', 'country'],
            set_=dict(
                popularity_metrics=stmt.excluded.popularity_metrics,
                source_url=stmt.excluded.source_url
            )
        )
        db_session.execute(update_stmt)
        db_session.commit()
        logger.info(f"Successfully upserted {len(unique_workflows)} workflows to database.")
        return len(unique_workflows)
        
    except Exception as e:
        logger.error(f"Database upsert failed: {str(e)}")
        db_session.rollback()
        raise


def run_full_ingestion(logger):
    """Run full ingestion from all platforms."""
    logger.info("Starting FULL ingestion mode - targeting ~20,000 workflows")
    
    all_workflows = []
    
    try:
        # Discourse ingestion
        logger.info("=== PHASE 1: Discourse Ingestion ===")
        discourse_workflows = fetch_discourse_workflows()
        logger.info(f"Discourse collected: {len(discourse_workflows)} workflows")
        all_workflows.extend(discourse_workflows)
        
        # YouTube ingestion
        logger.info("=== PHASE 2: YouTube Ingestion ===")
        youtube_workflows = fetch_youtube_workflows()
        logger.info(f"YouTube collected: {len(youtube_workflows)} workflows")
        all_workflows.extend(youtube_workflows)
        
        # Google Trends ingestion
        logger.info("=== PHASE 3: Google Trends Ingestion ===")
        google_workflows = fetch_google_trends()
        logger.info(f"Google Trends collected: {len(google_workflows)} workflows")
        all_workflows.extend(google_workflows)
        
        return all_workflows
        
    except Exception as e:
        logger.error(f"Ingestion failed during data collection: {str(e)}")
        raise


def run_test_ingestion(logger):
    """Run limited test ingestion for validation."""
    logger.info("Starting TEST ingestion mode - targeting ~400 workflows")
    
    # Import test script functionality
    sys.path.append(str(project_root / "scripts"))
    from run_ingestion_test import main as test_main
    
    # Redirect test script output to our logger
    import io
    from contextlib import redirect_stdout, redirect_stderr
    
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    
    try:
        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            test_main()
        
        # Log captured output
        stdout_content = stdout_capture.getvalue()
        stderr_content = stderr_capture.getvalue()
        
        if stdout_content:
            logger.info(f"Test ingestion output:\n{stdout_content}")
        if stderr_content:
            logger.warning(f"Test ingestion warnings:\n{stderr_content}")
            
        return []  # Test script handles its own database operations
        
    except Exception as e:
        logger.error(f"Test ingestion failed: {str(e)}")
        raise


def run_deep_analysis(logger):
    """Run deep analysis mode with extended metrics."""
    logger.info("Starting DEEP ANALYSIS mode - comprehensive data collection")
    
    # This could include:
    # - Historical trend analysis
    # - Cross-platform correlation analysis  
    # - Advanced engagement metrics
    # - Keyword performance analysis
    
    all_workflows = run_full_ingestion(logger)
    
    # Add deep analysis logic here in the future
    logger.info("Deep analysis completed - additional metrics would be calculated here")
    
    return all_workflows


def main():
    """Main cron job entry point."""
    parser = argparse.ArgumentParser(description="Popularity Vision Cron Job Runner")
    parser.add_argument(
        '--mode', 
        choices=['full', 'test', 'deep'], 
        default='full',
        help='Ingestion mode: full (production), test (validation), deep (analysis)'
    )
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run without writing to database'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = getattr(logging, args.log_level.upper())
    logger = setup_logging(log_level)
    
    start_time = datetime.now()
    logger.info(f"=== Popularity Vision Cron Job Started ===")
    logger.info(f"Mode: {args.mode.upper()}")
    logger.info(f"Start time: {start_time}")
    logger.info(f"Dry run: {args.dry_run}")
    
    exit_code = 0
    workflows_processed = 0
    
    try:
        # Ensure database tables exist
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        
        # Run ingestion based on mode
        if args.mode == 'full':
            workflows = run_full_ingestion(logger)
        elif args.mode == 'test':
            workflows = run_test_ingestion(logger)
        elif args.mode == 'deep':
            workflows = run_deep_analysis(logger)
        
        # Process workflows unless dry run
        if not args.dry_run and workflows:
            workflows_processed = upsert_workflows(db, workflows, logger)
        elif args.dry_run:
            logger.info(f"DRY RUN: Would have processed {len(workflows)} workflows")
            workflows_processed = len(workflows)
        
        db.close()
        
        # Success summary
        end_time = datetime.now()
        duration = end_time - start_time
        
        logger.info(f"=== Cron Job Completed Successfully ===")
        logger.info(f"Workflows processed: {workflows_processed}")
        logger.info(f"Duration: {duration}")
        logger.info(f"End time: {end_time}")
        
    except Exception as e:
        logger.error(f"=== Cron Job Failed ===")
        logger.error(f"Error: {str(e)}")
        logger.error(f"Traceback:\n{traceback.format_exc()}")
        exit_code = 1
        
    finally:
        try:
            if 'db' in locals():
                db.close()
        except:
            pass
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
