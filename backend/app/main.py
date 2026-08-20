from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.documents import router as documents_router
from app.api.projects import router as projects_router
from app.api.search import router as search_router
from app.api.runs import router as runs_router
from app.api.reviews import router as reviews_router

app = FastAPI(
    title="Project Delivery Intelligence Agent",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
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