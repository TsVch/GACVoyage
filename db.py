import sqlite3
from datetime import datetime, date, timedelta
import os
import calendar

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "orders.db")
print("DB PATH:", os.path.abspath(DB_NAME))


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # ===== Заказы =====
    cur.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        booking_id TEXT PRIMARY KEY,
        tg_id INTEGER,
        name TEXT,
        phone TEXT,
        excursion_id TEXT,
        excursion TEXT,
        date TEXT,
        start_time TEXT,
        count INTEGER,
        price INTEGER,
        prepayment INTEGER,
        pickup_address TEXT,
        route TEXT,
        order_status TEXT,
        contract_signed INTEGER DEFAULT 0,
        signed_at TEXT
    )
    """)

    # ===== Экскурсии =====
    cur.execute("""
    CREATE TABLE IF NOT EXISTS excursions (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL
    )
    """)

    # ===== Календарь экскурсий =====
    cur.execute("""
    CREATE TABLE IF NOT EXISTS excursion_calendar (
        excursion_id TEXT,
        date TEXT,
        total_places INTEGER DEFAULT 5,
        booked_places INTEGER DEFAULT 0,
        PRIMARY KEY (excursion_id, date)
    )
    """)

    # ===== Заблокированные даты =====
    cur.execute("""
    CREATE TABLE IF NOT EXISTS blocked_dates (
        excursion_id TEXT,
        date TEXT,
        reason TEXT,
        blocked_by INTEGER,
        blocked_at TEXT,
        PRIMARY KEY (excursion_id, date)
    )
    """)

    conn.commit()
    conn.close()


# ===== Инициализация календаря на месяц =====
def init_calendar_for_month(excursion_id: str, year: int, month: int):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    _, days_in_month = calendar.monthrange(year, month)

    for day in range(1, days_in_month + 1):
        date_str = f"{year}-{month:02d}-{day:02d}"
        cur.execute("""
        INSERT OR IGNORE INTO excursion_calendar (excursion_id, date)
        VALUES (?, ?)
        """, (excursion_id, date_str))

    conn.commit()
    conn.close()


# ===== Получить доступные даты =====
def get_available_dates_dict(excursion_id: str):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
    SELECT date, (total_places - booked_places) AS free
    FROM excursion_calendar
    WHERE excursion_id = ?
      AND booked_places < total_places
    """, (excursion_id,))

    rows = cur.fetchall()
    conn.close()

    return {date: free for date, free in rows}

# ===== Забронировать места =====
def book_places(excursion_id: str, date: str, count: int) -> bool:
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
    SELECT total_places, booked_places
    FROM excursion_calendar
    WHERE excursion_id = ? AND date = ?
    """, (excursion_id, date))

    row = cur.fetchone()
    if not row:
        conn.close()
        return False

    total, booked = row
    if booked + count > total:
        conn.close()
        return False

    cur.execute("""
    UPDATE excursion_calendar
    SET booked_places = booked_places + ?
    WHERE excursion_id = ? AND date = ?
    """, (count, excursion_id, date))

    conn.commit()
    conn.close()
    return True


# ===== Заказы =====
def save_order(data: dict):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO orders (
        booking_id, tg_id, name, phone,
        excursion_id, excursion,
        date, start_time, count,
        price, prepayment,
        pickup_address, route,
        order_status
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["booking_id"],
        data["tg_id"],
        data["name"],
        data["phone"],
        data["excursion_id"],
        data["excursion"],
        data["date"],
        data["start_time"],
        data["count"],
        data["price"],
        data.get("prepayment", 0),
        data["pickup_address"],
        data["route"],
        "Создан"
    ))

    conn.commit()
    conn.close()


def mark_paid(booking_id: str, amount: int):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
    UPDATE orders
    SET prepayment = ?
    WHERE booking_id = ?
    """, (amount, booking_id))

    conn.commit()
    conn.close()


def sign_contract(booking_id: str):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
    UPDATE orders
    SET contract_signed = 1,
        signed_at = ?,
        order_status = 'Подписан'
    WHERE booking_id = ?
    """, (datetime.now().isoformat(), booking_id))

    conn.commit()
    conn.close()


def get_last_booking_by_user(tg_id: int):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
    SELECT booking_id, tg_id, name, phone,
           excursion_id, excursion,
           date, start_time, count,
           price, prepayment,
           pickup_address, route
    FROM orders
    WHERE tg_id = ?
    ORDER BY rowid DESC
    LIMIT 1
    """, (tg_id,))

    row = cur.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "booking_id": row[0],
        "tg_id": row[1],
        "name": row[2],
        "phone": row[3],
        "excursion_id": row[4],
        "excursion": row[5],
        "date": row[6],
        "start_time": row[7],
        "count": row[8],
        "price": row[9],
        "prepayment": row[10],
        "pickup_address": row[11],
        "route": row[12]
    }
# =========================
# 🔥 CALENDAR FUNCTIONS
# =========================

MAX_PLACES_PER_DAY = 5


def get_free_places_for_date(excursion_id: str, date_str: str) -> int:
    """
    Возвращает количество свободных мест на конкретную дату
    """
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
    SELECT total_places, booked_places
    FROM excursion_calendar
    WHERE excursion_id = ? AND date = ?
    """, (excursion_id, date_str))

    row = cur.fetchone()
    conn.close()

    if not row:
        return 0

    total, booked = row
    return max(total - booked, 0)


def get_calendar_load_level(excursion_id: str, date_str: str) -> str:
    """
    Используется ТОЛЬКО для UI календаря
    """
    free = get_free_places_for_date(excursion_id, date_str)

    if free >= 3:
        return "🟢"
    elif free == 2:
        return "🟡"
    elif free == 1:
        return "🟠"
    else:
        return "❌"


def is_date_blocked(excursion_id: str, date_str: str) -> bool:
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # ручная блокировка для конкретной экскурсии
    cur.execute(
        """
        SELECT 1
        FROM blocked_dates
        WHERE excursion_id = ? AND date = ?
        """,
        (excursion_id, date_str)
    )

    if cur.fetchone():
        conn.close()
        return True

    conn.close()

    # либо нет свободных мест
    return get_free_places_for_date(excursion_id, date_str) <= 0




def get_available_dates_range(
    excursion_id: str,
    start_date: date,
    days_ahead: int = 14
) -> dict:
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    end_date = start_date + timedelta(days=days_ahead)

    cur.execute("""
    SELECT date, total_places, booked_places
    FROM excursion_calendar
    WHERE excursion_id = ?
      AND date BETWEEN ? AND ?
    """, (
        excursion_id,
        start_date.isoformat(),
        end_date.isoformat()
    ))

    rows = cur.fetchall()

    # 🔒 блокировки ТОЛЬКО этой экскурсии
    cur.execute(
        """
        SELECT date
        FROM blocked_dates
        WHERE excursion_id = ?
        """,
        (excursion_id,)
    )
    blocked = {row[0] for row in cur.fetchall()}

    conn.close()

    result = {}
    for date_str, total, booked in rows:
        if date_str in blocked:
            continue  # ❌ админ-блок

        free = max(total - booked, 0)
        if free > 0:
            result[date_str] = free

    return result

def block_date(excursion_id: str, date_str: str, admin_id: int, reason: str = ""):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
    INSERT OR REPLACE INTO blocked_dates
    (excursion_id, date, reason, blocked_by, blocked_at)
    VALUES (?, ?, ?, ?, ?)
    """, (
        excursion_id,
        date_str,
        reason,
        admin_id,
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()


def block_date_range(
    excursion_id: str,
    start: date,
    end: date,
    admin_id: int,
    reason: str = ""
):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    current = start
    while current <= end:
        cur.execute("""
        INSERT OR REPLACE INTO blocked_dates
        (excursion_id, date, reason, blocked_by, blocked_at)
        VALUES (?, ?, ?, ?, ?)
        """, (
            excursion_id,
            current.isoformat(),
            reason,
            admin_id,
            datetime.now().isoformat()
        ))
        current += timedelta(days=1)

    conn.commit()
    conn.close()


def unblock_date(excursion_id: str, date_str: str):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute(
        """
        DELETE FROM blocked_dates
        WHERE excursion_id = ? AND date = ?
        """,
        (excursion_id, date_str)
    )

    conn.commit()
    conn.close()


def get_blocked_dates(excursion_id: str) -> set[str]:
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute(
        "SELECT date FROM blocked_dates WHERE excursion_id = ?",
        (excursion_id,)
    )

    rows = cur.fetchall()
    conn.close()

    return {row[0] for row in rows}

def get_excursions():
    """
    Возвращает список экскурсий из конфига
    НЕ из БД — экскурсии хранятся в коде!
    """
    from config import EXCURSIONS
    return [(ex["id"], ex["title"]) for ex in EXCURSIONS]