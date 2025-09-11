# ⚡ Quick Start for Popularity Vision

**Ready-to-deploy workflow popularity analysis system with automated data ingestion.**

## 🎯 Choose Your Deployment

### **Option 1: Fully Automated (Docker + Cron)**
```bash
git clone <repository-url>
cd popularity-vision
cp .env.cron.example .env
# Add your YOUTUBE_API_KEY to .env
docker-compose -f docker-compose.yml -f docker-compose.cron.yml up -d
```
✅ **Done!** API + automatic daily data collection at 2 AM

### **Option 2: Manual Control (Docker API + System Cron)**  
```bash
git clone <repository-url>
cd popularity-vision
cp .env.example .env
# Add your YOUTUBE_API_KEY to .env
docker-compose up -d
./setup_cron.sh --install-daily
```
✅ **Done!** API in Docker + flexible cron scheduling

## ⚙️ Quick Configuration

### **Change Ingestion Schedule**
Edit `.env`:
```bash
CRON_SCHEDULE="0 2 * * *"     # Daily at 2 AM (default)
CRON_SCHEDULE="0 */6 * * *"   # Every 6 hours
CRON_SCHEDULE="0 1 * * 0"     # Weekly on Sundays
```

### **Change Data Volume**
```bash
INGESTION_MODE="full"         # ~20k workflows (production)
INGESTION_MODE="test"         # ~400 workflows (development)
```

## 🔧 Essential Commands

```bash
# Check status
./setup_cron.sh --status
python3 scripts/monitor_cron.py --generate-report

# View data
curl http://localhost:8000/workflows

# Check logs  
docker-compose logs -f cron-ingestion
tail -f logs/ingestion_$(date +%Y%m%d).log
```

## 📋 Requirements

- **Docker & Docker Compose** (for containerized deployment)
- **YouTube Data API v3 key** (required for data collection)
- **2-4 GB RAM** (for full ingestion)
- **10+ GB storage** (for database and logs)

---

**🚀 Your system will automatically collect workflow data from YouTube, Discourse, and Google Trends!**

For detailed configuration options, see [DEPLOYMENT.md](DEPLOYMENT.md).
