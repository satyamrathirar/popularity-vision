import sys
sys.path.append('.')

from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
from api import models

app = FastAPI(title="n8n Workflow Popularity API")

# Pydantic response models for better structure
class WorkflowSummary(BaseModel):
    id: int
    workflow_name: str
    platform: str
    country: str
    source_url: Optional[str] = None
    last_updated: datetime
    key_metrics: Dict[str, Any]  # Top 3-4 most important metrics per platform
    
    class Config:
        from_attributes = True

class WorkflowDetailed(BaseModel):
    id: int
    workflow_name: str
    platform: str
    country: str
    popularity_metrics: Dict[str, Any]
    source_url: Optional[str] = None
    last_updated: datetime
    
    class Config:
        from_attributes = True

def extract_key_metrics(platform: str, metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Extract key metrics based on platform for summary view"""
    if platform == "YouTube":
        return {
            "views": metrics.get("views", 0),
            "engagement_score": metrics.get("engagement_score", 0),
            "like_to_view_ratio": metrics.get("like_to_view_ratio", 0),
            "comments": metrics.get("comments", 0)
        }
    elif platform == "Discourse":
        return {
            "views": metrics.get("views", 0),
            "replies": metrics.get("replies", 0),
            "engagement_score": metrics.get("engagement_score", 0),
            "contributors": metrics.get("contributors", 0)
        }
    elif platform == "Google Trends":
        return {
            "relative_search_interest": metrics.get("relative_search_interest", 0),
            "momentum_score": metrics.get("momentum_score", 0),
            "trend_30d_direction": metrics.get("trend_30d", {}).get("trend_direction", "unknown"),
            "trend_30d_change": metrics.get("trend_30d", {}).get("change_percentage", 0)
        }
    else:
        # Fallback for unknown platforms
        return {k: v for k, v in list(metrics.items())[:4]}

# Dependency to get DB session
def get_db():
    db = models.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/workflows", response_model=List[WorkflowSummary])
def get_workflows(
    platform: Optional[str] = None, 
    country: Optional[str] = None, 
    view: str = Query("summary", description="View type: 'summary' or 'detailed'"),
    db: Session = Depends(get_db)
):
    """Get workflows with platform prominently displayed in collapsed view"""
    query = db.query(models.Workflow)
    if platform:
        query = query.filter(models.Workflow.platform == platform)
    if country:
        query = query.filter(models.Workflow.country == country)

    results = query.all()
    if not results:
        raise HTTPException(status_code=404, detail="No workflows found for the given criteria")

    # Convert to summary format with key metrics
    summary_results = []
    for workflow in results:
        key_metrics = extract_key_metrics(workflow.platform, workflow.popularity_metrics)
        summary_results.append(WorkflowSummary(
            id=workflow.id,
            workflow_name=workflow.workflow_name,
            platform=workflow.platform,
            country=workflow.country,
            source_url=workflow.source_url,
            last_updated=workflow.last_updated,
            key_metrics=key_metrics
        ))

    return summary_results

@app.get("/workflows/detailed", response_model=List[WorkflowDetailed])
def get_workflows_detailed(
    platform: Optional[str] = None, 
    country: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get workflows with full detailed metrics"""
    query = db.query(models.Workflow)
    if platform:
        query = query.filter(models.Workflow.platform == platform)
    if country:
        query = query.filter(models.Workflow.country == country)

    results = query.all()
    if not results:
        raise HTTPException(status_code=404, detail="No workflows found for the given criteria")

    return [WorkflowDetailed(
        id=workflow.id,
        workflow_name=workflow.workflow_name,
        platform=workflow.platform,
        country=workflow.country,
        popularity_metrics=workflow.popularity_metrics,
        source_url=workflow.source_url,
        last_updated=workflow.last_updated
    ) for workflow in results]

@app.get("/workflows/engagement")
def get_workflows_with_engagement(
    platform: Optional[str] = None, 
    country: Optional[str] = None,
    min_like_to_view_ratio: Optional[float] = None,
    min_comment_to_view_ratio: Optional[float] = None,
    min_engagement_score: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """Get workflows with engagement metrics filtering"""
    query = db.query(models.Workflow)
    if platform:
        query = query.filter(models.Workflow.platform == platform)
    if country:
        query = query.filter(models.Workflow.country == country)

    results = query.all()
    
    # Filter by engagement ratios if specified
    filtered_results = []
    for workflow in results:
        metrics = workflow.popularity_metrics
        
        # Skip if no engagement ratios available
        if not isinstance(metrics, dict):
            continue
            
        like_ratio = metrics.get('like_to_view_ratio', 0)
        comment_ratio = metrics.get('comment_to_view_ratio', 0)
        engagement_score = metrics.get('engagement_score', 0)
        
        # Apply filters
        if min_like_to_view_ratio is not None and like_ratio < min_like_to_view_ratio:
            continue
        if min_comment_to_view_ratio is not None and comment_ratio < min_comment_to_view_ratio:
            continue
        if min_engagement_score is not None and engagement_score < min_engagement_score:
            continue
            
        filtered_results.append(workflow)

    if not filtered_results:
        raise HTTPException(status_code=404, detail="No workflows found matching the engagement criteria")

    return filtered_results

@app.get("/workflows/top-engagement")
def get_top_engagement_workflows(
    platform: Optional[str] = None,
    country: Optional[str] = None,
    limit: int = 10,
    sort_by: str = "engagement_score",  # engagement_score, like_to_view_ratio, comment_to_view_ratio
    db: Session = Depends(get_db)
):
    """Get top workflows sorted by engagement metrics"""
    query = db.query(models.Workflow)
    if platform:
        query = query.filter(models.Workflow.platform == platform)
    if country:
        query = query.filter(models.Workflow.country == country)

    results = query.all()
    
    # Sort by the specified engagement metric
    valid_sort_options = ["engagement_score", "like_to_view_ratio", "comment_to_view_ratio"]
    if sort_by not in valid_sort_options:
        raise HTTPException(status_code=400, detail=f"sort_by must be one of {valid_sort_options}")
    
    # Filter out workflows without engagement metrics and sort
    workflows_with_metrics = []
    for workflow in results:
        metrics = workflow.popularity_metrics
        if isinstance(metrics, dict) and sort_by in metrics:
            workflows_with_metrics.append(workflow)
    
    # Sort by the specified metric (descending)
    sorted_workflows = sorted(
        workflows_with_metrics,
        key=lambda w: w.popularity_metrics.get(sort_by, 0),
        reverse=True
    )
    
    return sorted_workflows[:limit]

@app.get("/analytics/engagement-stats")
def get_engagement_statistics(
    platform: Optional[str] = None,
    country: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get statistical summary of engagement metrics"""
    query = db.query(models.Workflow)
    if platform:
        query = query.filter(models.Workflow.platform == platform)
    if country:
        query = query.filter(models.Workflow.country == country)

    results = query.all()
    
    # Collect engagement metrics
    like_ratios = []
    comment_ratios = []
    engagement_scores = []
    total_views = 0
    total_likes = 0
    total_comments = 0
    
    for workflow in results:
        metrics = workflow.popularity_metrics
        if isinstance(metrics, dict):
            if 'like_to_view_ratio' in metrics:
                like_ratios.append(metrics['like_to_view_ratio'])
            if 'comment_to_view_ratio' in metrics:
                comment_ratios.append(metrics['comment_to_view_ratio'])
            if 'engagement_score' in metrics:
                engagement_scores.append(metrics['engagement_score'])
            
            # Aggregate totals
            total_views += metrics.get('views', 0)
            total_likes += metrics.get('likes', 0)
            total_comments += metrics.get('comments', 0)
    
    def calculate_stats(values):
        if not values:
            return {"count": 0, "mean": 0, "min": 0, "max": 0}
        return {
            "count": len(values),
            "mean": round(sum(values) / len(values), 6),
            "min": round(min(values), 6),
            "max": round(max(values), 6)
        }
    
    return {
        "total_workflows": len(results),
        "total_views": total_views,
        "total_likes": total_likes,
        "total_comments": total_comments,
        "overall_like_to_view_ratio": round(total_likes / total_views, 6) if total_views > 0 else 0,
        "overall_comment_to_view_ratio": round(total_comments / total_views, 6) if total_views > 0 else 0,
        "like_to_view_ratio_stats": calculate_stats(like_ratios),
        "comment_to_view_ratio_stats": calculate_stats(comment_ratios),
        "engagement_score_stats": calculate_stats(engagement_scores),
        "platform": platform or "all",
        "country": country or "all"
    }

@app.get("/")
def read_root():
    return {"message": "Welcome to the n8n Workflow Popularity API. Visit /docs for documentation. visit /workflows to see workflows."}