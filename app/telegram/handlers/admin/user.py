from datetime import datetime
import re
from aiogram import F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.types.reply_keyboard_remove import ReplyKeyboardRemove
from dateutil.relativedelta import relativedelta
from app.db import GetDB
from app.models.user import UserCreate
from app.operation import OperatorType
from app.operation.user import UserOperator
from app.operation.group import GroupOperation
from app.telegram.keyboards.group import DoneAction, GroupsSelector
from app.telegram.utils.forms import CreateUser
from app.models.admin import AdminDetails
from app.telegram.keyboards.admin import AdminPanel, AdminPanelAction
from app.telegram.keyboards.base import Cancelkeyboard
from app.telegram.utils.filters import IsAdminfilter
from . import router

user_operations = UserOperator(OperatorType.TELEGRAM)
group_operations = GroupOperation(OperatorType.TELEGRAM)

USERNAME_PATTERN = re.compile(r"^(?=\w{3,32}\b)[a-zA-Z0-9-_@.]+(?:_[a-zA-Z0-9-_@.]+)*$")


@router.callback_query(
    AdminPanel.Callback.filter(F.action == AdminPanelAction.create_user),
    IsAdminfilter(),
)
async def create_user(query: CallbackQuery, admin: AdminDetails | None, state: FSMContext):
    await state.set_state(CreateUser.username)
    await query.message.reply(
        "please enter the username",
        reply_markup=Cancelkeyboard().as_markup(one_time_keyboard=True, resize_keyboard=True),
    )


@router.message(CreateUser.username)
async def process_username(message: Message, state: FSMContext):
    username = message.text
    if not USERNAME_PATTERN.match(username):
        return await message.reply(
            "❌ Username only can be 3 to 32 characters and contain a-z, A-Z, 0-9, and underscores in between.",
            reply_markup=Cancelkeyboard().as_markup(one_time_keyboard=True, resize_keyboard=True),
        )
    await state.update_data(username=username)
    await state.set_state(CreateUser.data_limit)
    await message.reply(
        "⬆️ Enter Data Limit (GB):\n⚠️ Send 0 for unlimited.",
        reply_markup=Cancelkeyboard().as_markup(one_time_keyboard=True, resize_keyboard=True),
    )


@router.message(CreateUser.data_limit)
async def process_data_limit(message: Message, state: FSMContext):
    try:
        data_limit = float(message.text)
        if data_limit < 0:
            return await message.reply(
                "❌ Data limit must be greater or equal to 0.",
                reply_markup=Cancelkeyboard().as_markup(one_time_keyboard=True, resize_keyboard=True),
            )
    except ValueError:
        return await message.reply(
            "❌ Data limit must be a number.",
            reply_markup=Cancelkeyboard().as_markup(one_time_keyboard=True, resize_keyboard=True),
        )
    await state.update_data(data_limit=data_limit)
    await state.set_state(CreateUser.expire)
    await message.reply(
        "⬆️ Enter Expire Date (YYYY-MM-DD)\nOr You Can Use Regex Symbol: ^[0-9]{1,3}(M|D) :\n⚠️ Send 0 for never expire.",
        reply_markup=Cancelkeyboard().as_markup(one_time_keyboard=True, resize_keyboard=True),
    )


@router.message(CreateUser.expire)
async def process_expire(message: Message, state: FSMContext):
    try:
        now = datetime.now()
        today = datetime(year=now.year, month=now.month, day=now.day, hour=23, minute=59, second=59)
        if re.match(r"^[0-9]{1,3}([MmDd])$", message.text):
            number_pattern = r"^[0-9]{1,3}"
            number = int(re.findall(number_pattern, message.text)[0])
            symbol_pattern = r"([MmDd])$"
            symbol = re.findall(symbol_pattern, message.text)[0].upper()

            if symbol == "M":
                expire_date = today + relativedelta(months=number)
            else:
                expire_date = today + relativedelta(days=number)
        elif message.text == "0":
            expire_date = None
            expire_date = datetime.strptime(message.text, "%Y-%m-%d")
            if expire_date < today:
                raise ValueError("Expire date must be greater than today.")
        else:
            raise ValueError("Invalid input for onhold status.")
    except ValueError as err:
        error_message = (
            str(err) if str(err) != "Invalid input for onhold status." else "Invalid input. Please try again."
        )
        await state.set_state(CreateUser.expire)
        return await message.reply(f"❌ {error_message}")
    await state.update_data(expire=expire_date)
    await state.set_state(CreateUser.groups)
    async with GetDB() as db:
        groups = await group_operations.get_all_groups(db)
    await message.reply(
        "Select Groups:",
        reply_markup=GroupsSelector(groups).as_markup(),
    )


@router.callback_query(GroupsSelector.SelectorCallback.filter(), CreateUser.groups)
async def process_groups(query: CallbackQuery, state: FSMContext, callback_data: GroupsSelector.SelectorCallback):
    groups = await state.get_value("groups")
    if isinstance(groups, dict):
        if callback_data.group_id in groups["ids"]:
            groups["ids"].remove(callback_data.group_id)
            groups["names"].remove(callback_data.group_name)
        else:
            groups["ids"].append(callback_data.group_id)
            groups["names"].append(callback_data.group_name)
    else:
        groups = {"ids": [callback_data.group_id], "names": [callback_data.group_name]}

    await state.update_data(groups=groups)

    async with GetDB() as db:
        all_groups = await group_operations.get_all_groups(db)

    await query.message.edit_reply_markup(
        reply_markup=GroupsSelector(groups=all_groups, selected_groups=groups).as_markup()
    )


@router.callback_query(GroupsSelector.DoneCallback.filter(F.action == DoneAction.done))
async def process_done(
    query: CallbackQuery, admin: AdminDetails, state: FSMContext, callback_data: GroupsSelector.DoneCallback
):
    data = await state.get_data()
    if not data.get("groups", {}).get("ids"):
        return await query.answer("you have to select at least one groups", True)

    await state.clear()
    new_user = UserCreate(
        data_limit=data["data_limit"],
        expire=data["expire"],
        username=data["username"],
        group_ids=data["groups"]["ids"],
    )
    async with GetDB() as db:
        try:
            await user_operations.add_user(db, new_user, admin)
            await query.message.answer("user created successfully")
        except Exception:
            pass


@router.callback_query(GroupsSelector.DoneCallback.filter(F.action == DoneAction.cancel))
async def process_cancel(query: CallbackQuery, state: FSMContext):
    await state.clear()
    await query.message.answer("opration canceled", reply_markup=ReplyKeyboardRemove())


@router.message(Command(commands=("user")))
async def admin_panel(message: Message):
    """search user"""
    await message.reply("hello admin from user")
