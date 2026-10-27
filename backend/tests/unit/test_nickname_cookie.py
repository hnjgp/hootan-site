import uuid

import pytest

from app.config import Settings
from app.game.nickname import nickname_error
from app.security.cookie import sign, unsign

SETTINGS = Settings(database_url="postgresql+asyncpg://x/y", secret_key="k")


@pytest.mark.parametrize(
    "name", ["bob", "Trader_9", "a.b.c", "هوشنگ", "کسری", "اکنون", "x" * 20]
)
def test_good_nicknames(name):
    assert nickname_error(name) is None


@pytest.mark.parametrize("name", ["ab", "x" * 21, "has space", "dash-name", "<b>"])
def test_bad_shapes(name):
    assert nickname_error(name) is not None


@pytest.mark.parametrize("name", ["Admin", "hoo.tan", "FUCK_you", "AI_Team"])
def test_blocked_words(name):
    assert nickname_error(name) == "Please choose another nickname"


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
