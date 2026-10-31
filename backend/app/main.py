"""FastAPI application entry point."""

from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.api import router as admin_router
from app.config import get_settings
from app.db.session import get_session
from app.game.accounts import router as accounts_router
from app.game.api import router as game_router
from app.game.password import router as password_router
from app.jobfit.api import router as jobfit_router
from app.logs import RequestLogMiddleware, setup_logging
from app.market.api import router as market_router
from app.trading.api import router as trading_router
from app.twin.api import router as twin_router

setup_logging()
app = FastAPI(title="hootanseifi.pro API")
app.add_middleware(RequestLogMiddleware)
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


@app.get("/api/ready")
async def ready(session: Annotated[AsyncSession, Depends(get_session)]) -> JSONResponse:
    """Readiness: 200 when the database answers, else 503; also says whether AI is on.

    AI is "on" when AI_ENABLED is true and a key is set; no paid call is made.
    """
    settings = get_settings()
    ai = "on" if settings.ai_enabled and settings.llm_api_key else "off"
    try:
        await session.execute(text("SELECT 1"))
    except (SQLAlchemyError, OSError):
        return JSONResponse({"db": "down", "ai": ai}, status_code=503)
    return JSONResponse({"db": "ok", "ai": ai})
