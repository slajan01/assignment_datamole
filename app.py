from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, String, Integer, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from contextlib import asynccontextmanager
import httpx
import datetime
import asyncio


DATABASE_URL = "sqlite:///./github_events.db"
GITHUB_API_URL = "https://api.github.com/repos/{owner}/{repo}/events"
REPOSITORIES = ["name/name"]  # Vlož sem repo, které chceš sledovat, nejvíce 5
ROLLING_WINDOW_DAYS = 7
MAX_EVENTS = 500

Base = declarative_base()
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@asynccontextmanager
def lifespan(app: FastAPI):
    task = asyncio.create_task(fetch_github_events())
    yield
    task.cancel()

app = FastAPI(lifespan=lifespan)

class GitHubEvent(Base):
    __tablename__ = "github_events"
    id = Column(String, primary_key=True)
    repo_name = Column(String, index=True)
    event_type = Column(String, index=True)
    created_at = Column(DateTime, index=True)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def fetch_github_events():
    async with httpx.AsyncClient() as client:
        while True:
            for repo in REPOSITORIES:
                owner, repo_name = repo.split("/")
                response = await client.get(GITHUB_API_URL.format(owner=owner, repo=repo_name))
                if response.status_code == 200:
                    events = response.json()
                    store_events(repo, events)
                await asyncio.sleep(10)  # Vyhnout se překročení API limitu


def store_events(repo, events):
    db = SessionLocal()
    for event in events[:MAX_EVENTS]:  # Zachovej pouze posledních MAX_EVENTS
        if not db.query(GitHubEvent).filter(GitHubEvent.id == event["id"]).first():
            db_event = GitHubEvent(
                id=event["id"],
                repo_name=repo,
                event_type=event["type"],
                created_at=datetime.datetime.strptime(event["created_at"], "%Y-%m-%dT%H:%M:%SZ")
            )
            db.add(db_event)
    db.commit()
    enforce_rolling_window(db)
    db.close()

def enforce_rolling_window(db: Session):
    cutoff_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=ROLLING_WINDOW_DAYS)
    db.query(GitHubEvent).filter(GitHubEvent.created_at < cutoff_date).delete()
    db.commit()

@app.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    stats = db.query(
        GitHubEvent.repo_name,
        GitHubEvent.event_type,
        (func.avg(GitHubEvent.created_at - func.lag(GitHubEvent.created_at).over(partition_by=[GitHubEvent.repo_name, GitHubEvent.event_type]))).label("average_time_between_events")
    ).group_by(GitHubEvent.repo_name, GitHubEvent.event_type).all()
    return {"stats": stats}

