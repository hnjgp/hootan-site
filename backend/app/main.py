"""FastAPI application entry point."""

from fastapi import FastAPI

app = FastAPI(title="hootanseifi.com API")


@app.get("/api/health")
def health() -> dict[str, str]:
    """Liveness check: the process is up and answering."""
    return {"status": "ok"}
