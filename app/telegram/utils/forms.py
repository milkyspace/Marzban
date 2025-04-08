from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup


class CreateUser(StatesGroup):
    username = State()
    status = State()
    expire = State()
    data_limit = State()
    note = State()
    
    