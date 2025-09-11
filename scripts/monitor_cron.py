#!/usr/bin/env python3
"""
It can be used for alerts, status dashboards, and troubleshooting.

Usage:
    python3 scripts/monitor_cron.py --check-last-run
    python3 scripts/monitor_cron.py --check-logs --hours=24
    python3 scripts/monitor_cron.py --generate-report
"""

import sys
import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.models import SessionLocal, Workflow


def check_last_run(hours_threshold: int = 25) -> Dict:
    """Check if cron job has run within the expected timeframe."""
    log_dir = project_root / "logs"
    log_files = list(log_dir.glob("ingestion_*.log"))
    
    if not log_files:
        return {
            "status": "error",
            "message": "No ingestion log files found",
            "last_run": None
        }
    
    # Find the most recent log file
    latest_log = max(log_files, key=lambda f: f.stat().st_mtime)
    last_modified = datetime.fromtimestamp(latest_log.stat().st_mtime)
    
    # Check if it's within threshold
    threshold_time = datetime.now() - timedelta(hours=hours_threshold)
    is_recent = last_modified > threshold_time
    
    return {
        "status": "healthy" if is_recent else "warning",
        "message": f"Last run: {last_modified.strftime('%Y-%m-%d %H:%M:%S')}",
        "last_run": last_modified.isoformat(),
        "hours_since_last_run": (datetime.now() - last_modified).total_seconds() / 3600
    }


def check_logs_for_errors(hours: int = 24) -> Dict:
    """Analyze recent logs for errors and warnings."""
    log_dir = project_root / "logs"
    log_files = list(log_dir.glob("*.log"))
    
    if not log_files:
        return {
            "status": "error", 
            "message": "No log files found",
            "errors": [],
            "warnings": []
        }
    
    cutoff_time = datetime.now() - timedelta(hours=hours)
    errors = []
    warnings = []
    
    for log_file in log_files:
        if datetime.fromtimestamp(log_file.stat().st_mtime) < cutoff_time:
            continue
            
        try:
            with open(log_file, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    if 'ERROR' in line:
                        errors.append(f"{log_file.name}:{line_num} - {line.strip()}")
                    elif 'WARNING' in line:
                        warnings.append(f"{log_file.name}:{line_num} - {line.strip()}")
        except Exception as e:
            errors.append(f"Failed to read {log_file}: {str(e)}")
    
    status = "healthy"
    if errors:
        status = "error"
    elif warnings:
        status = "warning"
    
    return {
        "status": status,
        "message": f"Found {len(errors)} errors and {len(warnings)} warnings in last {hours} hours",
        "errors": errors[-10:],  # Last 10 errors
        "warnings": warnings[-10:]  # Last 10 warnings
    }


def check_database_status() -> Dict:
    """Check database connectivity and recent data."""
    try:
        db = SessionLocal()
        
        # Check connection
        workflow_count = db.query(Workflow).count()
        
        # Check recent updates
        recent_cutoff = datetime.now() - timedelta(hours=48)
        recent_workflows = db.query(Workflow).filter(
            Workflow.last_updated >= recent_cutoff
        ).count()
        
        db.close()
        
        status = "healthy" if recent_workflows > 0 else "warning"
        message = f"Total workflows: {workflow_count}, Recent updates: {recent_workflows}"
        
        return {
            "status": status,
            "message": message,
            "total_workflows": workflow_count,
            "recent_updates": recent_workflows
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Database connection failed: {str(e)}",
            "total_workflows": 0,
            "recent_updates": 0
        }


def get_cron_job_status() -> Dict:
    """Check if cron jobs are properly configured."""
    import subprocess
    
    try:
        # Get current cron jobs
        result = subprocess.run(
            ['crontab', '-l'], 
            capture_output=True, 
            text=True, 
            check=False
        )
        
        if result.returncode != 0:
            return {
                "status": "warning",
                "message": "No cron jobs found or crontab access denied",
                "jobs": []
            }
        
        # Find popularity-vision related jobs
        cron_output = result.stdout
        project_jobs = [
            line.strip() for line in cron_output.split('\n')
            if 'popularity-vision' in line or 'run_cron_ingestion' in line
        ]
        
        status = "healthy" if project_jobs else "warning"
        message = f"Found {len(project_jobs)} active cron jobs"
        
        return {
            "status": status,
            "message": message,
            "jobs": project_jobs
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to check cron status: {str(e)}",
            "jobs": []
        }


def generate_health_report() -> Dict:
    """Generate comprehensive health report."""
    report = {
        "timestamp": datetime.now().isoformat(),
        "overall_status": "healthy",
        "checks": {
            "last_run": check_last_run(),
            "log_analysis": check_logs_for_errors(),
            "database": check_database_status(),
            "cron_jobs": get_cron_job_status()
        }
    }
    
    # Determine overall status
    statuses = [check["status"] for check in report["checks"].values()]
    if "error" in statuses:
        report["overall_status"] = "error"
    elif "warning" in statuses:
        report["overall_status"] = "warning"
    
    return report


def main():
    parser = argparse.ArgumentParser(description="Popularity Vision Cron Monitor")
    parser.add_argument('--check-last-run', action='store_true', help='Check last run time')
    parser.add_argument('--check-logs', action='store_true', help='Analyze logs for errors')
    parser.add_argument('--check-database', action='store_true', help='Check database status')
    parser.add_argument('--check-cron', action='store_true', help='Check cron job configuration')
    parser.add_argument('--generate-report', action='store_true', help='Generate full health report')
    parser.add_argument('--hours', type=int, default=24, help='Time window for analysis (default: 24)')
    parser.add_argument('--json', action='store_true', help='Output in JSON format')
    parser.add_argument('--alert-on-error', action='store_true', help='Exit with code 1 if errors found')
    
    args = parser.parse_args()
    
    result = {}
    
    if args.check_last_run:
        result = check_last_run(args.hours)
    elif args.check_logs:
        result = check_logs_for_errors(args.hours)
    elif args.check_database:
        result = check_database_status()
    elif args.check_cron:
        result = get_cron_job_status()
    elif args.generate_report:
        result = generate_health_report()
    else:
        result = generate_health_report()  # Default to full report
    
    # Output results
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Status: {result.get('status', 'unknown').upper()}")
        print(f"Message: {result.get('message', 'No message')}")
        
        if 'checks' in result:
            print("\nDetailed Checks:")
            for check_name, check_result in result['checks'].items():
                status_icon = {"healthy": "✅", "warning": "⚠️", "error": "❌"}.get(check_result['status'], "❓")
                print(f"  {status_icon} {check_name}: {check_result['message']}")
    
    # Exit with error code if requested and errors found
    if args.alert_on_error and result.get('status') == 'error':
        sys.exit(1)


if __name__ == "__main__":
    main()
