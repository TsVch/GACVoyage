from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def admin_main_kb():
    """Главное меню админ-панели"""
    kb = InlineKeyboardBuilder()
    kb.button(text="📅 Управление датами", callback_data="admin_dates")
    kb.button(text="📊 Статистика", callback_data="admin_stats")
    kb.button(text="❌ Закрыть", callback_data="admin_exit")
    kb.adjust(1)
    return kb.as_markup()


def admin_dates_kb():
    """Меню управления датами"""
    kb = InlineKeyboardBuilder()

    # 🔒 Блокировка одной даты
    kb.button(
        text="🔒 Заблокировать дату",
        callback_data="admin_mode:single"  # ✅ ИСПРАВЛЕНО
    )

    # 📆 Блокировка диапазона
    kb.button(
        text="📆 Заблокировать диапазон",
        callback_data="admin_mode:range"  # ✅ ИСПРАВЛЕНО
    )

    # 🟢 Разблокировка
    kb.button(
        text="🟢 Разблокировать дату",
        callback_data="admin_mode:unblock"
    )

    kb.button(text="⬅️ Назад", callback_data="admin_back")
    kb.adjust(1)
    return kb.as_markup()


def admin_excursions_kb(excursions: list):
    """
    Клавиатура выбора экскурсии
    excursions: список кортежей [(id, title), ...]
    """
    kb = InlineKeyboardBuilder()

    for exc_id, title in excursions:
        kb.button(
            text=title,
            callback_data=f"admin_exc:{exc_id}"
        )

    # ✅ ДОБАВЛЯЕМ кнопку "Назад"
    kb.button(text="⬅️ Назад", callback_data="admin_dates")

    kb.adjust(1)  # по 1 кнопке в ряд
    return kb.as_markup()