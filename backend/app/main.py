"""FastAPI application entry point."""

from fastapi import FastAPI

from app.admin.api import router as admin_router
from app.game.accounts import router as accounts_router
from app.game.api import router as game_router
from app.game.password import router as password_router
from app.jobfit.api import router as jobfit_router
from app.market.api import router as market_router
from app.trading.api import router as trading_router
from app.twin.api import router as twin_router

app = FastAPI(title="hootanseifi.com API")
app.include_router(twin_router)
app.include_router(jobfit_router)
app.include_router(market_router)
app.include_router(trading_router)
app.include_router(game_router)
app.include_router(accounts_router)
app.include_router(password_router)
app.include_router(admin_router)


@app.get("/api/health")
def health() -> dict[str, str]:
    """Liveness check: the process is up and answering."""
    return {"status": "ok"}
