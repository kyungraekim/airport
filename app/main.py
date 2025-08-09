from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from app.core.config import settings
from app.api.webhooks import router as webhook_router
from app.api.jobs import router as jobs_router
from app.api.commands import router as commands_router

logger = structlog.get_logger()

app = FastAPI(
    title="Model Validation Bot",
    description="GitHub PR-based Model Validation Bot with FastAPI",
    version="0.1.0",
    docs_url="/docs" if settings.DEBUG else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(webhook_router, prefix="/webhook", tags=["webhooks"])
app.include_router(jobs_router, prefix="/jobs", tags=["jobs"])
app.include_router(commands_router, prefix="/commands", tags=["commands"])

@app.get("/")
async def root():
    return {"message": "Model Validation Bot API", "version": "0.1.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

def main():
    """Entry point for the application."""
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_config=None,
    )

if __name__ == "__main__":
    main()