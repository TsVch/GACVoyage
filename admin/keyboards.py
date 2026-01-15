from aiogram.utils.keyboard import InlineKeyboardBuilder

def admin_main_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="📅 Управление датами", callback_data="admin_dates")
    kb.button(text="❌ Выйти", callback_data="admin_exit")
    kb.adjust(1)
    return kb.as_markup()


def admin_dates_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="🔒 Заблокировать дату", callback_data="admin_block_date")
    kb.button(text="📆 Заблокировать диапазон", callback_data="admin_block_range")
    kb.button(text="🟢 Разблокировать дату", callback_data="admin_unblock_date")
    kb.button(text="⬅ Назад", callback_data="admin_back")
    kb.adjust(1)
    return kb.as_markup()
