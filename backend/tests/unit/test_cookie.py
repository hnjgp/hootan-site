import uuid

from app.config import Settings
from app.security.cookie import sign, unsign

SETTINGS = Settings(database_url="postgresql+asyncpg://x/y", secret_key="k")


def test_signed_cookie_round_trip():
    player_id = uuid.uuid4()
    assert unsign(sign(player_id, SETTINGS), SETTINGS) == player_id


def test_tampered_or_foreign_cookie_is_rejected():
    value = sign(uuid.uuid4(), SETTINGS)
    other = str(uuid.uuid4()) + value[36:]
    assert unsign(other, SETTINGS) is None
    other_key = Settings(database_url="postgresql+asyncpg://x/y", secret_key="z")
    assert unsign(value, other_key) is None
    assert unsign("garbage", SETTINGS) is None
