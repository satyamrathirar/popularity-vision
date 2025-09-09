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

@app.get("/")
def read_root():
    return {"message": "Welcome to the n8n Workflow Popularity API. Visit /docs for documentation. visit /workflows to see workflows."}