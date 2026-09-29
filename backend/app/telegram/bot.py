"""aiogram wiring: turns Telegram updates into BotService calls and replies back.

Each update gets its own database session. The use cases are synchronous (SQLAlchemy),
so they run in a worker thread to keep the bot's event loop free.
"""

import asyncio
import logging
from collections.abc import Callable
from datetime import datetime
from typing import TypeVar
from zoneinfo import ZoneInfo

from aiogram import Bot, F, Router
from aiogram.enums import ChatType
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import BotCommand, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.core.config import settings
from app.infrastructure.db.session import SessionLocal
from app.telegram.service import HELP, BotService, Reply

log = logging.getLogger(__name__)
T = TypeVar("T")

router = Router()

COMMANDS = [
    BotCommand(command="left", description="Сколько осталось на месяц"),
    BotCommand(command="cats", description="Остаток по категориям"),
    BotCommand(command="month", description="Итог месяца"),
    BotCommand(command="last", description="Последние траты"),
    BotCommand(command="undo", description="Удалить свою последнюю трату"),
    BotCommand(command="grey", description="Взять из серой зоны: /grey 3000"),
    BotCommand(command="add", description="Записать трату: /add 450 продукты"),
    BotCommand(command="help", description="Как пользоваться"),
    BotCommand(command="link", description="Привязать Telegram кодом из приложения"),
    BotCommand(command="bind", description="Сделать эту беседу общей"),
    BotCommand(command="notify", description="Уведомления о тратах из приложения: on/off"),
    BotCommand(command="summary", description="Вечерняя сводка: on/off"),
]


def now() -> datetime:
    return datetime.now(ZoneInfo(settings.telegram_timezone))


def _run(action: Callable[[BotService], T]) -> T:
    db = SessionLocal()
    try:
        return action(BotService(db, now()))
    finally:
        db.close()


async def call(action: Callable[[BotService], T]) -> T:
    return await asyncio.to_thread(_run, action)


def _markup(reply: Reply) -> InlineKeyboardMarkup | None:
    if not reply.buttons:
        return None
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=b.text, callback_data=b.data) for b in row] for row in reply.buttons]
    )


async def send(message: Message, reply: Reply | None) -> None:
    if reply is not None:
        await message.answer(reply.text, reply_markup=_markup(reply))


def _private(message: Message) -> bool:
    return message.chat.type == ChatType.PRIVATE


async def _allowed(message: Message) -> bool:
    """Outside the shared chat (and private chats) the bot stays silent."""
    return await call(lambda s: s.chat_allowed(message.chat.id, _private(message)))


# ---- linking and setup: work in any chat ----


@router.message(CommandStart())
async def start(message: Message, command: CommandObject) -> None:
    if command.args:  # t.me/<bot>?start=<code> from the web settings
        await send(message, await call(lambda s: s.link(message.from_user.id, command.args or "")))
    else:
        await message.answer(HELP)


@router.message(Command("link"))
async def link(message: Message, command: CommandObject) -> None:
    await send(message, await call(lambda s: s.link(message.from_user.id, command.args or "")))


@router.message(Command("unlink"))
async def unlink(message: Message) -> None:
    await send(message, await call(lambda s: s.unlink(message.from_user.id)))


@router.message(Command("bind"))
async def bind(message: Message) -> None:
    await send(message, await call(lambda s: s.bind(message.from_user.id, message.chat.id, _private(message))))


@router.message(Command("help"))
async def help_(message: Message) -> None:
    await message.answer(HELP)


# ---- everything else: only in the shared chat or in private ----

_VIEWS: dict[str, Callable[[BotService, int], Reply]] = {
    "left": lambda s, uid: s.left(uid),
    "cats": lambda s, uid: s.cats(uid),
    "month": lambda s, uid: s.month(uid),
    "last": lambda s, uid: s.last(uid),
    "undo": lambda s, uid: s.undo(uid),
}


@router.message(Command(*_VIEWS))
async def views(message: Message, command: CommandObject) -> None:
    if not await _allowed(message):
        return
    view = _VIEWS[command.command]
    await send(message, await call(lambda s: view(s, message.from_user.id)))


@router.message(Command("grey"))
async def grey(message: Message, command: CommandObject) -> None:
    if await _allowed(message):
        await send(message, await call(lambda s: s.grey(message.from_user.id, command.args or "")))


@router.message(Command("notify", "summary"))
async def flags(message: Message, command: CommandObject) -> None:
    if await _allowed(message):
        await send(message, await call(lambda s: s.set_flag(command.command, command.args or "")))


@router.message(Command("add"))
async def add(message: Message, command: CommandObject) -> None:
    if await _allowed(message):
        await send(message, await call(lambda s: s.message(message.from_user.id, command.args or "", forced=True)))


@router.message(F.text & ~F.text.startswith("/"))
async def text(message: Message) -> None:
    if message.from_user is None or not await _allowed(message):
        return
    await send(message, await call(lambda s: s.message(message.from_user.id, message.text or "")))


@router.callback_query()
async def button(query: CallbackQuery) -> None:
    reply = await call(lambda s: s.callback(query.from_user.id, query.data or ""))
    await query.answer()
    if reply is None or not isinstance(query.message, Message):
        return
    try:
        await query.message.edit_text(reply.text, reply_markup=_markup(reply))
    except TelegramBadRequest:  # the message did not change
        pass


# ---- evening summary ----


async def summary_loop(bot: Bot) -> None:
    """Once a minute: after TELEGRAM_SUMMARY_TIME, send the day's summary if not sent yet."""
    while True:
        try:
            if now().strftime("%H:%M") >= settings.telegram_summary_time:
                result = await call(lambda s: s.daily_summary())
                if result is not None:
                    await bot.send_message(*result)
        except Exception:  # a failed summary must not stop the bot
            log.exception("Evening summary failed")
        await asyncio.sleep(60)
