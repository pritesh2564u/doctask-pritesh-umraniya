from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from app.api.documents import router as documents_router
from app.api.projects import router as projects_router
from app.api.search import router as search_router
from app.api.runs import router as runs_router
from app.api.reviews import router as reviews_router

app = FastAPI(
    title="Project Delivery Intelligence Agent",
    version="0.1.0",
)

# Read CORS origins from the environment variable CORS_ORIGINS as a
# comma-separated string. Fall back to the local dev origin if not set.
_cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173")
if isinstance(_cors_origins, str):
    _allow_origins = [o.strip() for o in _cors_origins.split(",") if o.strip()]
else:
    # In case someone passes a list-like value via the settings library
    _allow_origins = list(_cors_origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects_router)
app.include_router(documents_router)
app.include_router(search_router)
app.include_router(runs_router)
app.include_router(reviews_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
