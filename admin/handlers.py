import logging
from datetime import date
from aiogram import Router
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from admin.permissions import is_admin
from admin.keyboards import admin_main_kb, admin_dates_kb, admin_excursions_kb
from admin.fsm import AdminBlockFSM
from admin.services import block_date, block_date_range, unblock_date  # ✅ добавлен unblock_date
from calendar_utils import build_calendar
from db import get_blocked_dates, get_excursions, get_available_dates_range

router = Router()

MAX_DAYS_AHEAD = 14


# ====== Вход в админ-панель ======
@router.message(Command("admin"))
async def admin_entry(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ У вас нет доступа")
        return

    await state.clear()
    await message.answer(
        "🎛 <b>Админ-панель</b>",
        parse_mode="HTML",
        reply_markup=admin_main_kb()
    )


# ====== Управление датами ======
@router.callback_query(lambda c: c.data == "admin_dates")
async def admin_dates(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return

    await state.clear()
    await callback.message.edit_text(
        "📅 <b>Управление датами</b>",
        parse_mode="HTML",
        reply_markup=admin_dates_kb()
    )
    await callback.answer()


# ====== Выбор режима блокировки ======
@router.callback_query(lambda c: c.data.startswith("admin_mode:"))
async def admin_choose_excursion(callback: CallbackQuery, state: FSMContext):
    mode = callback.data.split(":")[1]

    logging.info(f"Выбран режим: {mode}")

    await state.clear()
    await state.update_data(mode=mode)

    excursions = get_excursions()

    logging.info(f"Загружено экскурсий: {excursions}")

    if not excursions:
        await callback.answer("❌ Экскурсии не найдены", show_alert=True)
        return

    await callback.message.edit_text(
        "🧭 <b>Выберите экскурсию</b>",
        parse_mode="HTML",
        reply_markup=admin_excursions_kb(excursions)
    )
    await callback.answer()


# ====== Выбор экскурсии ======
@router.callback_query(lambda c: c.data.startswith("admin_exc:"))
async def admin_excursion_selected(callback: CallbackQuery, state: FSMContext):
    excursion_id = callback.data.split(":")[1]

    logging.info(f"Выбрана экскурсия: {excursion_id}")

    await state.update_data(excursion_id=excursion_id)
    await state.set_state(AdminBlockFSM.picking_start)

    today = date.today()
    data = await state.get_data()
    mode = data.get("mode")

    dates = get_available_dates_range(excursion_id, today, MAX_DAYS_AHEAD)
    blocked = get_blocked_dates(excursion_id)

    if mode == "single":
        prompt = "🔒 <b>Выберите дату для блокировки</b>"
    elif mode == "range":
        prompt = "📆 <b>Выберите НАЧАЛЬНУЮ дату диапазона</b>"
    elif mode == "unblock":
        prompt = (
            "🟢 <b>Выберите дату для разблокировки</b>\n\n"
            "❌ — заблокированные даты"
        )
    else:
        prompt = "📅 <b>Выберите дату</b>"

    await callback.message.edit_text(
        prompt,
        parse_mode="HTML",
        reply_markup=build_calendar(
            today.year,
            today.month,
            dates=dates,
            blocked_dates=blocked,
            mode="admin"
        )
    )
    await callback.answer()


# ====== Назад в админ-панель ======
@router.callback_query(lambda c: c.data == "admin_back")
async def admin_back(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "🎛 <b>Админ-панель</b>",
        parse_mode="HTML",
        reply_markup=admin_main_kb()
    )
    await callback.answer()


# ==== Переключение месяцев в админ-календаре ======
@router.callback_query(lambda c: c.data.startswith("cal_prev"))
async def admin_calendar_prev(callback: CallbackQuery, state: FSMContext):
    _, year, month = callback.data.split(":")
    year, month = int(year), int(month)

    month -= 1
    if month == 0:
        month = 12
        year -= 1

    data = await state.get_data()
    excursion_id = data.get("excursion_id")
    mode = data.get("mode")

    today = date.today()
    dates = get_available_dates_range(excursion_id, today, MAX_DAYS_AHEAD)
    blocked = get_blocked_dates(excursion_id)

    if mode == "single":
        prompt = "🔒 <b>Выберите дату для блокировки</b>"
    elif mode == "range":
        prompt = "📆 <b>Выберите НАЧАЛЬНУЮ дату диапазона</b>"
    elif mode == "unblock":
        prompt = "🟢 <b>Выберите дату для разблокировки</b>\n\n❌ — заблокированные даты"
    else:
        prompt = "📅 <b>Выберите дату</b>"

    await callback.message.edit_text(
        prompt,
        parse_mode="HTML",
        reply_markup=build_calendar(
            year, month, dates, blocked, mode="admin"
        )
    )
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("cal_next"))
async def admin_calendar_next(callback: CallbackQuery, state: FSMContext):
    _, year, month = callback.data.split(":")
    year, month = int(year), int(month)

    month += 1
    if month == 13:
        month = 1
        year += 1

    data = await state.get_data()
    excursion_id = data.get("excursion_id")
    mode = data.get("mode")

    today = date.today()
    dates = get_available_dates_range(excursion_id, today, MAX_DAYS_AHEAD)
    blocked = get_blocked_dates(excursion_id)

    if mode == "single":
        prompt = "🔒 <b>Выберите дату для блокировки</b>"
    elif mode == "range":
        prompt = "📆 <b>Выберите НАЧАЛЬНУЮ дату диапазона</b>"
    elif mode == "unblock":
        prompt = "🟢 <b>Выберите дату для разблокировки</b>\n\n❌ — заблокированные даты"
    else:
        prompt = "📅 <b>Выберите дату</b>"

    await callback.message.edit_text(
        prompt,
        parse_mode="HTML",
        reply_markup=build_calendar(
            year, month, dates, blocked, mode="admin"
        )
    )
    await callback.answer()

# ====== Закрыть админ-панель ======
@router.callback_query(lambda c: c.data == "admin_exit")
async def admin_exit(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.answer("Админ-панель закрыта")


# ====== Выбор даты для блокировки/разблокировки ======
@router.callback_query(
    AdminBlockFSM.picking_start,
    lambda c: c.data.startswith("admin_date:")
)
async def admin_pick_start(callback: CallbackQuery, state: FSMContext):
    picked = callback.data.split(":")[1]
    picked_date = date.fromisoformat(picked)

    data = await state.get_data()
    mode = data.get("mode")
    excursion_id = data.get("excursion_id")

    logging.info(f"Режим: {mode}, Дата: {picked}, Экскурсия: {excursion_id}")

    # 🔒 одиночная блокировка
    if mode == "single":
        block_date(excursion_id, picked, callback.from_user.id, reason="Admin block")
        await state.clear()
        await callback.answer("🔒 Дата заблокирована")
        await callback.message.edit_text(
            "✅ <b>Дата успешно заблокирована</b>",
            parse_mode="HTML",
            reply_markup=admin_dates_kb()
        )
        return

    # 🟢 разблокировка даты
    if mode == "unblock":
        success = unblock_date(excursion_id, picked)

        if success:
            # ✅ Обновляем календарь после разблокировки
            dates = get_available_dates_range(excursion_id, picked_date, MAX_DAYS_AHEAD)
            blocked = get_blocked_dates(excursion_id)

            await callback.answer("🟢 Дата разблокирована")
            await callback.message.edit_text(
                "🟢 <b>Выберите дату для разблокировки</b>\n\n"
                "❌ — заблокированные даты\n\n"
                f"✅ Дата {picked} успешно разблокирована",
                parse_mode="HTML",
                reply_markup=build_calendar(
                    picked_date.year,
                    picked_date.month,
                    dates=dates,
                    blocked_dates=blocked,
                    mode="admin"
                )
            )
        else:
            await callback.answer("⚠️ Дата не была заблокирована", show_alert=True)

        return  # ✅ НЕ очищаем state, чтобы можно было разблокировать ещё даты

    # 📆 начало диапазона
    if mode == "range":
        await state.update_data(start_date=picked_date)
        await state.set_state(AdminBlockFSM.picking_end)

        dates = get_available_dates_range(excursion_id, picked_date, MAX_DAYS_AHEAD)
        blocked = get_blocked_dates(excursion_id)

        await callback.message.edit_text(
            "📆 <b>Выберите КОНЕЧНУЮ дату диапазона</b>",
            parse_mode="HTML",
            reply_markup=build_calendar(
                picked_date.year,
                picked_date.month,
                dates=dates,
                blocked_dates=blocked,
                mode="admin"
            )
        )
        await callback.answer()


# ====== Выбор конечной даты диапазона ======
@router.callback_query(
    AdminBlockFSM.picking_end,
    lambda c: c.data.startswith("admin_date:")
)
async def admin_pick_range_end(callback: CallbackQuery, state: FSMContext):
    picked = callback.data.split(":")[1]
    end_date = date.fromisoformat(picked)

    data = await state.get_data()
    start_date = data.get("start_date")
    excursion_id = data.get("excursion_id")

    if end_date < start_date:
        await callback.answer("❗ Конец раньше начала", show_alert=True)
        return

    block_date_range(excursion_id, start_date, end_date, callback.from_user.id, reason="Admin range block")

    await state.clear()
    await callback.answer("🔒 Диапазон заблокирован")
    await callback.message.edit_text(
        "✅ <b>Диапазон дат заблокирован</b>",
        parse_mode="HTML",
        reply_markup=admin_dates_kb()
    )