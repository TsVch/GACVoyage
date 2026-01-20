import calendar
from datetime import date, timedelta
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from db import get_free_places_for_date
print("📁 calendar_utils path:", __file__)

MONTHS_RU = [
    "", "Январь", "Февраль", "Март", "Апрель",
    "Май", "Июнь", "Июль", "Август",
    "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
]

WEEKDAYS_RU = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

MAX_DAYS_AHEAD = 14
MAX_SEATS = 5


def month_title(year: int, month: int) -> str:
    return f"{MONTHS_RU[month]} {year}"


def load_free_seats_callback(date_str, dates_dict: dict):
    """
    dates_dict: { 'YYYY-MM-DD': free_places }
    """
    return dates_dict.get(date_str)

def seat_indicator(free: int) -> str:
    if free == 0:
        return "❌"
    elif free == 1:
        return "🔴"
    elif free <= 3:
        return "🟡"
    elif free > 3:
        return "🟢"
    return ""

def build_calendar(
    year: int,
    month: int,
    dates: dict,                 # {date_str: free_seats}
    blocked_dates: set[str] | None = None,
    mode: str = "user"            # "user" или "admin"
):
    if blocked_dates is None:
        blocked_dates = set()

    kb = InlineKeyboardBuilder()
    today = date.today()
    last_allowed = today + timedelta(days=MAX_DAYS_AHEAD)

    # ===== Заголовок дней недели =====
    for wd in WEEKDAYS_RU:
        kb.button(text=wd, callback_data="ignore")
    kb.adjust(7)

    cal = calendar.monthcalendar(year, month)

    for week in cal:
        row = []

        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(text=" ", callback_data="ignore"))
                continue

            current_date = date(year, month, day)
            date_str = current_date.strftime("%Y-%m-%d")

            # ❌ вне допустимого диапазона
            if current_date < today or current_date > last_allowed:
                row.append(InlineKeyboardButton(text=" ", callback_data="ignore"))
                continue

            # ❌ админ-блокировка
            if date_str in blocked_dates:
                callback = f"admin_blocked:{date_str}" if mode == "admin" else "ignore"
                row.append(InlineKeyboardButton(text=f"{day}❌", callback_data=callback))
                continue

            # 🔍 свободные места
            free_seats = dates.get(date_str, 0)

            # ❌ мест нет
            if free_seats <= 0:
                callback = f"admin_full:{date_str}" if mode == "admin" else "ignore"
                row.append(InlineKeyboardButton(text=f"{day}❌", callback_data=callback))
                continue

            # ✅ есть места
            indicator = seat_indicator(free_seats)
            callback = f"admin_date:{date_str}" if mode == "admin" else f"date:{date_str}"

            row.append(InlineKeyboardButton(text=f"{day}{indicator}", callback_data=callback))

        kb.row(*row)

    return kb.as_markup()