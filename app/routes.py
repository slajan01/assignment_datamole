from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db, GitHubEvent

router = APIRouter()

@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    stats = db.query(
        GitHubEvent.repo_name,
        GitHubEvent.event_type,
        (func.avg(GitHubEvent.created_at - func.lag(GitHubEvent.created_at).over(partition_by=[GitHubEvent.repo_name, GitHubEvent.event_type]))).label("average_time_between_events")
    ).group_by(GitHubEvent.repo_name, GitHubEvent.event_type).all()
    return {"stats": stats}