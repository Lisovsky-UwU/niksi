"""Runs the Niksi Telegram bot: `uv run python -m app.telegram` (long polling)."""

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.core.config import settings
from app.telegram.bot import COMMANDS, router, summary_loop

log = logging.getLogger("app.telegram")


async def main() -> None:
    if not settings.telegram_bot_token:
        raise SystemExit("TELEGRAM_BOT_TOKEN is not set in backend/.env (see 'Telegram-бот' in the root README.md)")
    bot = Bot(settings.telegram_bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    me = await bot.get_me()
    log.info("Running as @%s", me.username)
    if not me.can_read_all_group_messages:
        log.warning(
            "Privacy mode is on: in a group the bot only sees commands, not lines like '450 продукты'. "
            "Turn it off in @BotFather: /setprivacy -> @%s -> Disable, then re-add the bot to the chat.",
            me.username,
        )
    await bot.set_my_commands(COMMANDS)
    dispatcher = Dispatcher()
    dispatcher.include_router(router)
    summary = asyncio.create_task(summary_loop(bot))
    try:
        await dispatcher.start_polling(bot)
    finally:
        summary.cancel()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    asyncio.run(main())
