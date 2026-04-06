from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.database import get_active_clusters
import asyncio
from backend.manager import main_loop
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(main_loop())
    yield

app = FastAPI(title="Daystat API", lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For local development, be more specific in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/status")
async def get_status():
    return get_active_clusters()

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
