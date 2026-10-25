"""FastAPI application entry point."""

from fastapi import FastAPI

from app.twin.api import router as twin_router

app = FastAPI(title="hootanseifi.com API")
app.include_router(twin_router)


@app.get("/api/health")
def health() -> dict[str, str]:
    """Liveness check: the process is up and answering."""
    return {"status": "ok"}
