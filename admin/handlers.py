from datetime import date, datetime, timedelta

from aiogram import Router
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from admin.permissions import is_admin
from admin.keyboards import admin_main_kb, admin_dates_kb

from admin.fsm import AdminBlockFSM
from admin.services import block_date, block_date_range
from calendar_utils import build_calendar
from db import get_blocked_dates

router = Router()


@router.message(Command("admin"))
async def admin_entry(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ У вас нет доступа")
        return

    await message.answer(
        "🎛 <b>Админ-панель</b>",
        parse_mode="HTML",
        reply_markup=admin_main_kb()
    )


@router.callback_query(lambda c: c.data == "admin_dates")
async def admin_dates(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return

    await callback.message.edit_text(
        "📅 <b>Управление датами</b>",
        parse_mode="HTML",
        reply_markup=admin_dates_kb()
    )


@router.callback_query(lambda c: c.data == "admin_back")
async def admin_back(callback: CallbackQuery):
    await callback.message.edit_text(
        "🎛 <b>Админ-панель</b>",
        parse_mode="HTML",
        reply_markup=admin_main_kb()
    )

@router.callback_query(lambda c: c.data == "admin_block_date")
async def admin_block_single(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(AdminBlockFSM.picking_start)

    today = date.today()

    await callback.message.edit_text(
        "🔒 <b>Выберите дату для блокировки</b>",
        parse_mode="HTML",
        reply_markup=build_calendar(
            today.year,
            today.month,
            dates={},
            blocked_dates=get_blocked_dates(),
            mode="admin_block"
        )
    )

@router.callback_query(lambda c: c.data == "admin_block_range")
async def admin_block_range_start(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(AdminBlockFSM.picking_start)

    today = date.today()

    await callback.message.edit_text(
        "📆 <b>Выберите НАЧАЛЬНУЮ дату</b>",
        parse_mode="HTML",
        reply_markup=build_calendar(
            today.year,
            today.month,
            dates={},
            blocked_dates=get_blocked_dates(),
            mode="admin_block"
        )
    )

@router.callback_query(lambda c: c.data.startswith("admin_pick:"))
async def admin_pick_date(callback: CallbackQuery, state: FSMContext):
    picked = callback.data.split(":")[1]
    picked_date = date.fromisoformat(picked)

    current_state = await state.get_state()

    # Одна дата
    if current_state == AdminBlockFSM.picking_start.state:
        data = await state.get_data()

        if "range" not in data:
            block_date(
                picked,
                callback.from_user.id,
                reason="Admin block"
            )
            await state.clear()
            await callback.answer("🔒 Дата заблокирована")

            await callback.message.edit_text(
                "✅ <b>Дата успешно заблокирована</b>",
                parse_mode="HTML",
                reply_markup=admin_dates_kb()
            )
            return

        # начало диапазона
        await state.update_data(start_date=picked_date)
        await state.set_state(AdminBlockFSM.picking_end)

        await callback.message.edit_text(
            "📆 <b>Выберите КОНЕЧНУЮ дату</b>",
            parse_mode="HTML",
            reply_markup=build_calendar(
                picked_date.year,
                picked_date.month,
                dates={},
                blocked_dates=get_blocked_dates(),
                mode="admin_block"
            )
        )

@router.callback_query(AdminBlockFSM.picking_end, lambda c: c.data.startswith("admin_pick:"))
async def admin_pick_range_end(callback: CallbackQuery, state: FSMContext):
    picked = callback.data.split(":")[1]
    end_date = date.fromisoformat(picked)

    data = await state.get_data()
    start_date = data["start_date"]

    if end_date < start_date:
        await callback.answer("❗ Конец раньше начала", show_alert=True)
        return

    block_date_range(
        start=start_date,
        end=end_date,
        admin_id=callback.from_user.id,
        reason="Admin range block"
    )

    await state.clear()
    await callback.answer("🔒 Диапазон заблокирован")

    await callback.message.edit_text(
        "✅ <b>Диапазон дат заблокирован</b>",
        parse_mode="HTML",
        reply_markup=admin_dates_kb()
    )

