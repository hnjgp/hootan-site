"""Nickname rules: 3 to 20 letters (Persian too), digits, `_` or `.`, and no bad words."""

import re

PATTERN = re.compile(r"[\w.]{3,20}")
# Lowercase fragments a nickname may not contain; also blocks impersonating the site.
BLOCKED = (
    "admin",
    "hootan",
    "aiteam",
    "fuck",
    "shit",
    "bitch",
    "dick",
    "porn",
    "nazi",
    "کیر",
    "جنده",
    "گاییدم",
    "هوتن",
)


def nickname_error(nickname: str) -> str | None:
    """Why the nickname is not allowed, or None when it is fine."""
    if not PATTERN.fullmatch(nickname):
        return "Use 3 to 20 letters, digits, _ or ."
    plain = nickname.lower().replace("_", "").replace(".", "")
    if any(word in plain for word in BLOCKED):
        return "Please choose another nickname"
    return None
