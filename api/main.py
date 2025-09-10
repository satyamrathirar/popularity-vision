import sys
sys.path.append('.')

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from api import models

app = FastAPI(title="n8n Workflow Popularity API")

# Dependency to get DB session
def get_db():
    db = models.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/workflows")
def get_workflows(platform: Optional[str] = None, country: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(models.Workflow)
    if platform:
        query = query.filter(models.Workflow.platform == platform)
    if country:
        query = query.filter(models.Workflow.country == country)

    results = query.all()
    if not results:
        raise HTTPException(status_code=404, detail="No workflows found for the given criteria")

    return results

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