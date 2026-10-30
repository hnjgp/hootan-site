import json
import logging

import httpx2

from app.logs import JsonFormatter, request_id
from app.main import app


def test_formatter_merges_fields_and_request_id():
    record = logging.LogRecord("llm", logging.INFO, "", 0, "llm call", None, None)
    record.fields = {"model": "gpt-5-nano", "tokens_in": 12}
    token = request_id.set("abc123")
    line = json.loads(JsonFormatter().format(record))
    request_id.reset(token)
    assert line["msg"] == "llm call"
    assert line["request_id"] == "abc123"
    assert line["model"] == "gpt-5-nano"
    assert line["tokens_in"] == 12


async def test_each_request_gets_an_id_and_one_log_line(caplog):
    # /api/health is not logged (Docker probes it), so ask for an unknown path.
    transport = httpx2.ASGITransport(app=app)
    with caplog.at_level(logging.INFO, logger="http"):
        async with httpx2.AsyncClient(transport=transport, base_url="https://t") as c:
            response = await c.get("/api/nope")
    rid = response.headers["x-request-id"]
    assert len(rid) == 12
    assert response.status_code == 404
    (record,) = [r for r in caplog.records if r.name == "http"]
    assert record.fields == {
        "method": "GET",
        "path": "/api/nope",
        "status": 404,
        "ms": record.fields["ms"],
    }
