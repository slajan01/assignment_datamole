from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.database import Base, engine
from app.services import fetch_github_events
from app.routes import router
from dotenv import load_dotenv
import asyncio
import os

load_dotenv()

@asynccontextmanager
def lifespan(app: FastAPI):
    task = asyncio.create_task(fetch_github_events())
    yield
    task.cancel()

Base.metadata.create_all(bind=engine)

app = FastAPI(lifespan=lifespan)
app.include_router(router)