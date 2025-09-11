#!/bin/bash
"""
Cron Job Setup Helper for Popularity Vision

This script helps you set up cron jobs for automated data ingestion.
It provides different scheduling options and handles environment setup.

Usage:
    ./setup_cron.sh --help
    ./setup_cron.sh --install-daily
    ./setup_cron.sh --install-custom "0 2 * * *"
    ./setup_cron.sh --remove
    ./setup_cron.sh --status
"""

set -e

# Configuration
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT_PATH="$PROJECT_DIR/scripts/run_cron_ingestion.py"
LOG_DIR="$PROJECT_DIR/logs"
ENV_FILE="$PROJECT_DIR/.env"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_help() {
    cat << EOF
Popularity Vision Cron Setup Helper

USAGE:
    $0 [OPTIONS]

OPTIONS:
    --install-daily     Install daily ingestion at 2 AM
    --install-hourly    Install test ingestion every 4 hours
    --install-weekly    Install deep analysis weekly (Sundays 1 AM)
    --install-custom    Install with custom schedule (provide cron expression)
    --remove           Remove all popularity-vision cron jobs
    --status           Show current cron job status
    --test             Test the ingestion script
    --help             Show this help message

EXAMPLES:
    # Install daily full ingestion
    $0 --install-daily

    # Install custom schedule (every Monday at 3 AM)
    $0 --install-custom "0 3 * * 1"
    
    # Remove all cron jobs
    $0 --remove
    
    # Check current status
    $0 --status

CRON SCHEDULE FORMATS:
    Daily at 2 AM:      0 2 * * *
    Every 4 hours:      0 */4 * * *
    Weekly (Sunday):    0 1 * * 0
    Twice daily:        0 2,14 * * *

EOF
}

log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check if script exists
    if [[ ! -f "$SCRIPT_PATH" ]]; then
        error "Ingestion script not found: $SCRIPT_PATH"
        exit 1
    fi
    
    # Check if Python environment is set up
    if [[ ! -f "$ENV_FILE" ]]; then
        warn "Environment file not found: $ENV_FILE"
        warn "Make sure to create .env with required API keys"
    fi
    
    # Create log directory
    mkdir -p "$LOG_DIR"
    
    # Make script executable
    chmod +x "$SCRIPT_PATH"
    
    log "Prerequisites check completed"
}

get_cron_comment() {
    echo "# Popularity Vision Automated Ingestion - $1"
}

install_cron_job() {
    local schedule="$1"
    local mode="$2"
    local description="$3"
    
    log "Installing cron job: $description"
    
    # Remove existing jobs first
    remove_cron_jobs
    
    # Create the cron job entry
    local cron_entry="$schedule cd $PROJECT_DIR && python3 $SCRIPT_PATH --mode=$mode >> $LOG_DIR/cron.log 2>&1"
    local cron_comment="$(get_cron_comment "$description")"
    
    # Add to crontab
    (crontab -l 2>/dev/null; echo "$cron_comment"; echo "$cron_entry") | crontab -
    
    log "Cron job installed successfully"
    info "Schedule: $schedule"
    info "Mode: $mode"
    info "Logs: $LOG_DIR/cron.log"
}

remove_cron_jobs() {
    log "Removing existing Popularity Vision cron jobs..."
    
    # Remove lines containing our project path
    crontab -l 2>/dev/null | grep -v "$PROJECT_DIR" | crontab - 2>/dev/null || true
    
    log "Existing cron jobs removed"
}

show_status() {
    log "Current cron job status:"
    
    local current_jobs=$(crontab -l 2>/dev/null | grep "$PROJECT_DIR" || echo "")
    
    if [[ -z "$current_jobs" ]]; then
        info "No Popularity Vision cron jobs found"
    else
        info "Active cron jobs:"
        echo "$current_jobs" | while read line; do
            if [[ "$line" =~ ^#.* ]]; then
                echo -e "  ${BLUE}$line${NC}"
            else
                echo -e "  ${GREEN}$line${NC}"
            fi
        done
    fi
    
    # Show recent log entries
    local log_file="$LOG_DIR/cron.log"
    if [[ -f "$log_file" ]]; then
        info "Recent log entries (last 10 lines):"
        tail -n 10 "$log_file" | sed 's/^/  /'
    else
        info "No log file found: $log_file"
    fi
}

test_ingestion() {
    log "Testing ingestion script..."
    
    cd "$PROJECT_DIR"
    python3 "$SCRIPT_PATH" --mode=test --dry-run
    
    if [[ $? -eq 0 ]]; then
        log "Test completed successfully"
    else
        error "Test failed - check the output above"
        exit 1
    fi
}

# Main execution
case "${1:-}" in
    --install-daily)
        check_prerequisites
        install_cron_job "0 2 * * *" "full" "Daily Full Ingestion"
        ;;
    --install-hourly)
        check_prerequisites  
        install_cron_job "0 */4 * * *" "test" "Test Ingestion Every 4 Hours"
        ;;
    --install-weekly)
        check_prerequisites
        install_cron_job "0 1 * * 0" "deep" "Weekly Deep Analysis"
        ;;
    --install-custom)
        if [[ -z "${2:-}" ]]; then
            error "Custom schedule required. Example: --install-custom '0 3 * * 1'"
            exit 1
        fi
        check_prerequisites
        install_cron_job "$2" "full" "Custom Schedule ($2)"
        ;;
    --remove)
        remove_cron_jobs
        ;;
    --status)
        show_status
        ;;
    --test)
        check_prerequisites
        test_ingestion
        ;;
    --help|-h)
        print_help
        ;;
    *)
        error "Invalid option: ${1:-}"
        echo
        print_help
        exit 1
        ;;
esac
