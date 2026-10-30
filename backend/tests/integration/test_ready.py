import httpx2

from app.db.session import get_session
from app.main import app


async def test_ready_reports_database_and_ai(session):
    app.dependency_overrides[get_session] = lambda: session
    transport = httpx2.ASGITransport(app=app)
    async with httpx2.AsyncClient(transport=transport, base_url="https://t") as c:
        response = await c.get("/api/ready")
    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["db"] == "ok"
    assert response.json()["ai"] in ("on", "off")
