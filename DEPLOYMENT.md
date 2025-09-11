# 🚀 Deployment Guide for Popularity Vision
!! A lot of the cron-job section is written by Claude Sonnet 4, don't blame if your server gets nuked.
This guide is for system administrators and DevOps teams deploying Popularity Vision with automated data ingestion.

## 📋 Quick Deployment Overview

Your Popularity Vision codebase comes **cron-ready** with multiple deployment options:

### 🎯 **For End Users: Choose Your Deployment Style**

#### **Option 1: Docker + Automated Cron (Recommended)**
```bash
# Clone and start with automated ingestion
git clone <your-repo>
cd popularity-vision
cp .env.cron.example .env
# Edit .env with your API keys
docker-compose -f docker-compose.yml -f docker-compose.cron.yml up -d
```
✅ **Result**: API runs + automatic daily data ingestion at 2 AM

#### **Option 2: Docker API + System Cron Jobs**
```bash
# Start API only
docker-compose up -d

# Setup system cron jobs
./setup_cron.sh --install-daily
```
✅ **Result**: API runs in Docker + cron jobs run on host system

#### **Option 3: Full System Installation**
```bash
# Traditional server setup
./setup_cron.sh --install-daily
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```
✅ **Result**: Everything runs on host system

---

## ⚙️ Configuration Options

### 🕒 **Cron Schedule Configuration**
Edit `.env` or `.env.cron` file:

```bash
# Ingestion Frequency Options
CRON_SCHEDULE="0 2 * * *"        # Daily at 2 AM (default)
CRON_SCHEDULE="0 */6 * * *"      # Every 6 hours  
CRON_SCHEDULE="0 1 * * 0"        # Weekly on Sundays
CRON_SCHEDULE="0 3 * * 1,3,5"    # Mon/Wed/Fri at 3 AM

# Ingestion Scope Options  
INGESTION_MODE="full"            # ~20k workflows (45-90 min)
INGESTION_MODE="test"            # ~400 workflows (5-10 min)
INGESTION_MODE="deep"            # Full + analytics
```

### 🔑 **Required API Keys**
```bash
# YouTube Data API v3 (Required)
YOUTUBE_API_KEY=your_youtube_api_key_here

# Google Ads API (Optional - uses simulation if not provided)
GOOGLE_ADS_API_KEY=your_google_ads_key_optional

# Database (Auto-configured for Docker)
DATABASE_URL=postgresql://user:password@db:5432/workflows
```

### 📊 **Data Collection Targets**
- **YouTube**: Video tutorials, demos, engagement metrics
- **Discourse**: Community discussions from n8n forums  
- **Google Trends**: Search popularity and keyword analysis
- **Expected Volume**: 15,000-25,000 workflows per full ingestion

---

## 🛠️ **Setup Commands Reference**

### **Docker-Based Setup**
```bash
# Quick start with cron
docker-compose -f docker-compose.yml -f docker-compose.cron.yml up -d

# Check container status
docker-compose ps

# View cron logs
docker-compose logs -f cron-ingestion

# Stop everything
docker-compose -f docker-compose.yml -f docker-compose.cron.yml down
```

### **System Cron Setup**
```bash
# Install daily ingestion
./setup_cron.sh --install-daily

# Install custom schedule
./setup_cron.sh --install-custom "0 */4 * * *"

# Check current jobs
./setup_cron.sh --status

# Remove all jobs
./setup_cron.sh --remove

# Test before installing
./setup_cron.sh --test
```

---

## 📊 **Monitoring & Health Checks**

### **Built-in Monitoring Tools**
```bash
# Complete health report
python3 scripts/monitor_cron.py --generate-report

# Check if jobs are running on time
python3 scripts/monitor_cron.py --check-last-run

# Analyze errors in logs  
python3 scripts/monitor_cron.py --check-logs --hours=24

# Database connectivity check
python3 scripts/monitor_cron.py --check-database
```

### **Integration with Monitoring Systems**
```bash
# JSON output for Prometheus/Grafana
python3 scripts/monitor_cron.py --generate-report --json

# Exit with error code for alerting
python3 scripts/monitor_cron.py --generate-report --alert-on-error
```

---

## 🚨 **Common Deployment Scenarios**

### **Scenario 1: Small Team / Development**
```bash
# Test ingestion every 4 hours
CRON_SCHEDULE="0 */4 * * *"
INGESTION_MODE="test"
```

### **Scenario 2: Production Analytics**
```bash  
# Full ingestion daily at 2 AM
CRON_SCHEDULE="0 2 * * *"
INGESTION_MODE="full"
```

### **Scenario 3: High-Frequency Monitoring**
```bash
# Every 2 hours with test mode
CRON_SCHEDULE="0 */2 * * *" 
INGESTION_MODE="test"
```

### **Scenario 4: Weekly Batch Processing**
```bash
# Deep analysis weekly
CRON_SCHEDULE="0 1 * * 0"
INGESTION_MODE="deep"
```

---

## 📁 **File Structure for Deployment**

```
popularity-vision/
├── 🐳 docker-compose.cron.yml     # Automated cron service
├── 🐳 Dockerfile.cron            # Cron container definition  
├── 🔧 setup_cron.sh              # System cron installer
├── ⚙️ .env.cron.example          # Configuration template
├── scripts/
│   ├── 🤖 run_cron_ingestion.py  # Cron-optimized entry point
│   └── 📊 monitor_cron.py        # Health monitoring
└── logs/                         # Auto-created log directory
```

---

## ✅ **Post-Deployment Verification**

### **1. Check API is Running**
```bash
curl http://localhost:8000/workflows
```

### **2. Verify Cron Jobs**
```bash
# Docker method
docker-compose logs cron-ingestion

# System method  
./setup_cron.sh --status
```

### **3. Test Data Ingestion**
```bash
# Run test ingestion
python3 scripts/run_cron_ingestion.py --mode=test --dry-run
```

### **4. Monitor Health**
```bash
# Generate health report
python3 scripts/monitor_cron.py --generate-report
```

---

## 🆘 **Troubleshooting**

### **Cron Jobs Not Running**
```bash
# Check cron service
systemctl status cron          # Linux
service cron status            # Alternative

# Check job syntax
./setup_cron.sh --status
```

### **API Connection Issues**
```bash
# Check Docker containers
docker-compose ps

# Check logs
docker-compose logs api
docker-compose logs db
```

### **Database Connection Problems**
```bash
# Test database connectivity
python3 scripts/monitor_cron.py --check-database
```

### **Missing API Keys**
```bash
# Verify environment file
cat .env | grep -E "(YOUTUBE|GOOGLE)"
```

---

## 📈 **Scaling & Performance**

### **For High-Volume Deployments**
- **Database**: Consider PostgreSQL connection pooling
- **Storage**: Monitor log file growth (`logs/` directory)  
- **Memory**: Full ingestion uses ~500MB-1GB RAM
- **Network**: YouTube API has rate limits (10,000 requests/day)

### **Cost Optimization**
- Use `test` mode for development environments
- Schedule `full` ingestion during off-peak hours
- Monitor API quota usage

---

## 📞 **Support & Maintenance**

### **Log Locations**
- **Cron Logs**: `logs/ingestion_YYYYMMDD.log`
- **System Cron**: `logs/cron.log`  
- **Docker Logs**: `docker-compose logs cron-ingestion`

### **Regular Maintenance Tasks**
1. **Weekly**: Check `monitor_cron.py --generate-report`
2. **Monthly**: Review log file sizes in `logs/` directory
3. **Quarterly**: Update API keys if needed
4. **As Needed**: Adjust cron schedules based on data freshness requirements

---

