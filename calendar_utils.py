from datetime import date, timedelta
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

MONTHS_RU = [
    "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
]


def month_title(year: int, month: int) -> str:
    """Возвращает название месяца и год"""
    return f"{MONTHS_RU[month - 1]} {year}"


def build_calendar(
        year: int,
        month: int,
        dates: dict,
        blocked_dates: set,
        mode: str = "user"
) -> InlineKeyboardMarkup:
    """
    Строит календарь с датами
    dates: [(date_str, free_places), ...]
    blocked_dates: {"2026-01-20", ...}
    mode: "user" или "admin"
    """
    # Создаём словарь дат для быстрого доступа
    dates_dict = dates

    # Определяем границы месяца
    first_day = date(year, month, 1)
    if month == 12:
        last_day = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = date(year, month + 1, 1) - timedelta(days=1)

    # Текущая дата и лимиты бронирования
    today = date.today()
    max_booking_date = today + timedelta(days=14)

    # Начинаем строить клавиатуру
    keyboard = []

    # ========== РЯД 1: ЗАГОЛОВОК С ПЕРЕКЛЮЧЕНИЕМ ==========
    if mode == "admin":
        prev_cb = f"admin_cal_prev:{year}:{month}"
        next_cb = f"admin_cal_next:{year}:{month}"
    else:
        prev_cb = f"cal_prev:{year}:{month}"
        next_cb = f"cal_next:{year}:{month}"
    header_row = [
        InlineKeyboardButton(text="◀️", callback_data=prev_cb),
        InlineKeyboardButton(text = month_title(year, month), callback_data="ignore"),
        InlineKeyboardButton(text="▶️", callback_data=next_cb),
    ]
    keyboard.append(header_row)

    # ========== РЯД 2: ДНИ НЕДЕЛИ ==========
    weekdays_row = [
        InlineKeyboardButton(text="Пн", callback_data="ignore"),
        InlineKeyboardButton(text="Вт", callback_data="ignore"),
        InlineKeyboardButton(text="Ср", callback_data="ignore"),
        InlineKeyboardButton(text="Чт", callback_data="ignore"),
        InlineKeyboardButton(text="Пт", callback_data="ignore"),
        InlineKeyboardButton(text="Сб", callback_data="ignore"),
        InlineKeyboardButton(text="Вс", callback_data="ignore")
    ]
    keyboard.append(weekdays_row)

    # ========== РЯДЫ 3+: КАЛЕНДАРНАЯ СЕТКА ==========
    current_row = []

    # Пустые ячейки до первого дня месяца
    weekday = first_day.weekday()  # 0=Пн, 6=Вс
    for _ in range(weekday):
        current_row.append(InlineKeyboardButton(text=" ", callback_data="ignore"))

    # Заполняем даты месяца
    current_day = first_day
    while current_day <= last_day:
        date_str = current_day.isoformat()
        day_num = current_day.day

        # Проверяем условия
        is_blocked = date_str in blocked_dates
        is_past = current_day < today
        is_too_far = current_day > max_booking_date
        free_places = dates_dict.get(date_str, 0)

        # ========== РЕЖИМ ПОЛЬЗОВАТЕЛЯ ==========
        if mode == "user":
            if is_past or is_too_far:
                text = f"{day_num}⚪️"
                callback = "ignore"
            elif is_blocked:
                text = f"{day_num}❌"
                callback = "ignore"
            elif free_places == 0:
                text = f"{day_num}🚫"
                callback = "ignore"
            elif free_places == 1:
                text = f"{day_num}🔴"
                callback = f"date:{date_str}"
            elif free_places <= 3:
                text = f"{day_num}🟡"
                callback = f"date:{date_str}"
            else:
                text = f"{day_num}🟢"
                callback = f"date:{date_str}"


        # ========== РЕЖИМ АДМИНА ==========
        else:
            # 🔥 ВАЖНО: админ НЕ ограничен MAX_DAYS_AHEAD
            if is_past or is_too_far:
                text = f"{day_num}⚪️"
                callback = "ignore"

            elif is_blocked:
                text = f"{day_num}❌"
                callback = f"admin_date:{date_str}"

            elif free_places <= 0:
                # ❗ теперь админ видит, что день "полный"
                text = f"{day_num}🚫"
                callback = f"admin_date:{date_str}"

            elif free_places == 1:
                text = f"{day_num}🔴"
                callback = f"admin_date:{date_str}"

            elif free_places <= 3:
                text = f"{day_num}🟡"
                callback = f"admin_date:{date_str}"

            else:
                text = f"{day_num}🟢"
                callback = f"admin_date:{date_str}"

        current_row.append(InlineKeyboardButton(text=text, callback_data=callback))

        # Если ряд заполнен (7 дней) - добавляем в клавиатуру
        if len(current_row) == 7:
            keyboard.append(current_row)
            current_row = []

        current_day += timedelta(days=1)

    # Добавляем последний неполный ряд, если есть
    if current_row:
        # Дополняем пустыми ячейками до 7
        while len(current_row) < 7:
            current_row.append(InlineKeyboardButton(text=" ", callback_data="ignore"))
        keyboard.append(current_row)

    # ========== КНОПКА "НАЗАД" ДЛЯ АДМИНА ==========
    if mode == "admin":
        keyboard.append([
            InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back_to_excursions")
        ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)