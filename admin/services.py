import sqlite3
from datetime import date, timedelta
import logging

DB_PATH = "orders.db"


def block_date(excursion_id: str, date_str: str, admin_id: int, reason: str = ""):
    """Блокировка одной даты"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO blocked_dates (excursion_id, date, blocked_by, reason)
            VALUES (?, ?, ?, ?)
        """, (excursion_id, date_str, admin_id, reason))

        conn.commit()
        logging.info(f"✅ Дата {date_str} заблокирована для {excursion_id}")
        return True
    except sqlite3.IntegrityError:
        logging.warning(f"⚠️ Дата {date_str} уже заблокирована")
        return False
    finally:
        conn.close()


def block_date_range(excursion_id: str, start_date: date, end_date: date, admin_id: int, reason: str = ""):
    """Блокировка диапазона дат"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    current = start_date
    blocked_count = 0

    while current <= end_date:
        try:
            cursor.execute("""
                INSERT INTO blocked_dates (excursion_id, date, blocked_by, reason)
                VALUES (?, ?, ?, ?)
            """, (excursion_id, current.isoformat(), admin_id, reason))
            blocked_count += 1
        except sqlite3.IntegrityError:
            logging.warning(f"⚠️ Дата {current} уже заблокирована")

        current += timedelta(days=1)

    conn.commit()
    conn.close()

    logging.info(f"✅ Заблокировано {blocked_count} дат для {excursion_id}")
    return blocked_count


def unblock_date(excursion_id: str, date_str: str):
    """Разблокировка одной даты"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM blocked_dates
        WHERE excursion_id = ? AND date = ?
    """, (excursion_id, date_str))

    deleted = cursor.rowcount
    conn.commit()
    conn.close()

    if deleted > 0:
        logging.info(f"✅ Дата {date_str} разблокирована для {excursion_id}")
        return True
    else:
        logging.warning(f"⚠️ Дата {date_str} не была заблокирована")
        return False