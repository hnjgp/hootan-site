"""Persian (Jalali) calendar: the leaderboard season is one Persian month."""

from datetime import date, timedelta

# Days before each Gregorian month in a common year.
MONTH_OFFSETS = (0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334)


def to_jalali(d: date) -> tuple[int, int, int]:
    """Jalali (year, month, day) of a Gregorian date (arithmetic 33-year cycle)."""
    gy = d.year + 1 if d.month > 2 else d.year
    days = (
        355666
        + 365 * d.year
        + (gy + 3) // 4
        - (gy + 99) // 100
        + (gy + 399) // 400
        + d.day
        + MONTH_OFFSETS[d.month - 1]
    )
    jy = -1595 + 33 * (days // 12053)
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365
    if days < 186:
        return jy, 1 + days // 31, 1 + days % 31
    return jy, 7 + (days - 186) // 30, 1 + (days - 186) % 30


def month_start(d: date) -> date:
    """Gregorian date of the first day of d's Persian month."""
    return d - timedelta(days=to_jalali(d)[2] - 1)
