# 🔥 Popularity Vision

**Multi-Platform Workflow Popularity Analysis System**

A comprehensive data ingestion and analysis platform that tracks workflow popularity across YouTube, n8n Community (Discourse), and Google Trends/Ads. Built with FastAPI, PostgreSQL, and Docker for scalable workflow analytics.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Data Sources](#data-sources)
- [Configuration](#configuration)
- [Development](#development)
- [Contributing](#contributing)

## 🌟 Overview

Popularity Vision is designed to analyze and track the popularity of n8n automation workflows across multiple platforms. It aggregates data from various sources to provide insights into trending workflows, engagement metrics, and cross-platform popularity analysis.

### Key Capabilities

- **Multi-Platform Data Ingestion**: Scrapes workflow data from YouTube, Discourse forums, and Google Ads
- **Comprehensive Analytics**: Tracks engagement metrics, popularity scores, and trend analysis
- **RESTful API**: Provides structured endpoints for accessing workflow data
- **Scalable Architecture**: Docker-based deployment with PostgreSQL for data persistence
- **Real-time Updates**: Configurable ingestion schedules for fresh data


## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Data Sources  │    │   Ingestion      │    │   API Layer     │
│                 │    │   Scripts        │    │                 │
│ • YouTube API   │───▶│ • ingest_youtube │───▶│ • FastAPI       │
│ • Discourse     │    │ • ingest_discourse│    │ • Pydantic      │
│ • Google Ads    │    │ • ingest_google   │    │ • JSON Response │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        │
                       ┌──────────────────┐              │
                       │   PostgreSQL     │◀─────────────┘
                       │   Database       │
                       │ • Workflows      │
                       │ • Metrics        │
                       │ • Metadata       │
                       └──────────────────┘
```

### Tech Stack
- **Backend**: Python 3.9+, FastAPI
- **Database**: PostgreSQL with SQLAlchemy ORM
- **APIs**: YouTube Data API v3, Google Ads Keyword Planner
- **Containerization**: Docker & Docker Compose
- **Data Processing**: Pandas, NumPy for analytics

## 🚀 Installation

### Prerequisites
- Docker & Docker Compose
- Python 3.9+ (for local development)
- API Keys:
  - YouTube Data API v3 key
  - Google Ads API credentials (optional)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/popularity-vision.git
   cd popularity-vision
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Start with Docker Compose**
   ```bash
   docker-compose up -d
   ```

4. **Access the API**
   - API: http://localhost:8000
   - Workflows: http://localhost:8000/workflows
   - Documentation: http://localhost:8000/docs
   - Database: localhost:5432

## 📖 Usage

1. **Install dependencies**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. **Set up database**
    ```bash
    # Initialize the database schema
    docker compose exec api python database/init_db.py
    ```

3. **initialization**
    ```bash
    # Full ingestion (~20,000 workflows)
    docker compose exec api python scripts/run_ingestion.py
    
    # Test ingestion (~350 workflows for testing)
    docker compose exec api python scripts/run_ingestion_test.py
   ```

### API Usage Examples

#### Get All Workflows
```bash
curl "http://localhost:8000/workflows"
```

#### Filter by Platform
```bash
curl "http://localhost:8000/workflows?platform=YouTube"
curl "http://localhost:8000/workflows?platform=Discourse"
curl "http://localhost:8000/workflows?platform=Google%20Trends"
```

#### Filter by Engagement
```bash
curl "http://localhost:8000/workflows/high-engagement?min_engagement=1000"
```

#### Get Workflow Details
```bash
curl "http://localhost:8000/workflows/1/detailed"
```

## 📚 API Documentation

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/workflows` | List all workflows with summary info |
| GET | `/workflows/{id}` | Get specific workflow summary |
| GET | `/workflows/{id}/detailed` | Get detailed workflow information |
| GET | `/workflows/high-engagement` | Get workflows above engagement threshold |
| GET | `/workflows/platform/{platform}` | Get workflows by platform |


## 🗂️ Data Sources

### YouTube (YouTube Data API v3)
- **Data Type**: Video tutorials, demos, guides
- **Metrics**: Views, likes, comments, engagement ratios
- **Coverage**: Global content with engagement analysis

### Discourse (n8n Community Forum)
- **Data Type**: Community discussions, solutions, Q&A
- **Metrics**: Views, replies, likes, solution status
- **Coverage**: Community-driven workflow discussions

### Google Trends/Ads
- **Data Type**: Search trends, keyword popularity
- **Metrics**: Search volume, competition, CPC, trend direction
- **Coverage**: US and India markets


### Keywords Configuration
Edit `keywords.txt` to customize the workflows being tracked:


### Ingestion Parameters
- **YouTube**: Configurable pages per keyword, batch size
- **Discourse**: Timeout settings, pages per keyword, rate limiting
- **Google Ads**: Keyword limits, country targeting

## 👩‍💻 Development


### Database Schema
```sql
CREATE TABLE workflows (
    id SERIAL PRIMARY KEY,
    workflow_name VARCHAR NOT NULL,
    platform VARCHAR NOT NULL,
    country VARCHAR NOT NULL,
    popularity_metrics JSONB,
    source_url VARCHAR,
    last_updated TIMESTAMP DEFAULT NOW(),
    UNIQUE(workflow_name, platform, country)
);
```

### Contribution Areas
- Additional data sources (Zapier, Make.com, etc.)
- Enhanced analytics and metrics
- Performance optimizations
- Test coverage improvements

## 🔗 Links

- [n8n Official Website](https://n8n.io)
- [n8n Community Forum](https://community.n8n.io)
- [YouTube Data API](https://developers.google.com/youtube/v3)
- [Google Ads API](https://developers.google.com/google-ads/api)

---

**Built with ❤️ for the n8n automation community**