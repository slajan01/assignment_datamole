import httpx
import asyncio
import datetime
from app.database import SessionLocal, GitHubEvent
from dotenv import load_dotenv
import os

load_dotenv()

GITHUB_API_URL = os.getenv("GITHUB_API_URL", "https://api.github.com/repos/{owner}/{repo}/events")
REPOSITORIES = ["owner/repo1", "owner/repo2", "owner/repo3", "owner/repo4", "owner/repo5"]  
ROLLING_WINDOW_DAYS = 7
MAX_EVENTS = 500
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", 10))

async def fetch_github_events():
    async with httpx.AsyncClient() as client:
        while True:
            for repo in REPOSITORIES:
                owner, repo_name = repo.split("/")
                response = await client.get(GITHUB_API_URL.format(owner=owner, repo=repo_name))
                if response.status_code == 200:
                    events = response.json()
                    store_events(repo, events)
                await asyncio.sleep(POLL_INTERVAL)

def store_events(repo, events):
    db = SessionLocal()
    for event in events[:MAX_EVENTS]:
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

def enforce_rolling_window(db):
    cutoff_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=ROLLING_WINDOW_DAYS)
    db.query(GitHubEvent).filter(GitHubEvent.created_at < cutoff_date).delete()
    db.commit()