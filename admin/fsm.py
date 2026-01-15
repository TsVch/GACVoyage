from aiogram.fsm.state import StatesGroup, State

class AdminBlockFSM(StatesGroup):
    picking_start = State()
    picking_end = State()