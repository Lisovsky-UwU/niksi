"""Telegram: linking people to their accounts, the shared chat, and chat notifications.

A person links Telegram with a one-time code from the web settings (sent to the bot as
/link CODE), so no password is ever typed into a chat. The couple's chat is bound with
/bind; the bot answers there and posts notifications and the evening summary.
"""

import secrets
from datetime import date, datetime, timedelta
from decimal import Decimal

from app.domain.exceptions import NotFoundError, ValidationError
from app.domain.models import Expense, Month, TelegramChat, TelegramLinkCode, User
from app.domain.text import expense_card
from app.interfaces.repositories import (
    CategoryRepository,
    ExpenseRepository,
    MonthRepository,
    TelegramChatRepository,
    UserRepository,
)

LINK_CODE_LIFETIME = timedelta(minutes=15)


class CreateTelegramLinkCodeUseCase:
    def __init__(self, user_repo: UserRepository) -> None:
        self._user_repo = user_repo

    def execute(self, user_id: int, now: datetime) -> TelegramLinkCode:
        code = f"{secrets.randbelow(1_000_000):06d}"
        expires_at = now + LINK_CODE_LIFETIME
        self._user_repo.set_link_code(user_id, code, expires_at)
        return TelegramLinkCode(code=code, expires_at=expires_at)


class LinkTelegramUseCase:
    def __init__(self, user_repo: UserRepository) -> None:
        self._user_repo = user_repo

    def execute(self, code: str, telegram_user_id: int, now: datetime) -> User:
        found = self._user_repo.find_link_code(code.strip())
        if found is None:
            raise ValidationError("Unknown link code")
        user, expires_at = found
        if expires_at.tzinfo is None:  # SQLite hands timestamps back without a zone
            expires_at = expires_at.replace(tzinfo=now.tzinfo)
        if expires_at < now:
            raise ValidationError("The link code has expired")
        # One Telegram account belongs to one person: move it if it was linked to the other.
        previous = self._user_repo.get_by_telegram_id(telegram_user_id)
        if previous is not None and previous.id != user.id:
            self._user_repo.set_telegram_id(previous.id, None)
        return self._user_repo.set_telegram_id(user.id, telegram_user_id)


class UnlinkTelegramUseCase:
    def __init__(self, user_repo: UserRepository) -> None:
        self._user_repo = user_repo

    def execute(self, user_id: int) -> User:
        return self._user_repo.set_telegram_id(user_id, None)


class BindChatUseCase:
    def __init__(self, chat_repo: TelegramChatRepository) -> None:
        self._chat_repo = chat_repo

    def execute(self, chat_id: int, user_id: int) -> TelegramChat:
        return self._chat_repo.bind(chat_id, user_id)


class SetChatFlagsUseCase:
    def __init__(self, chat_repo: TelegramChatRepository) -> None:
        self._chat_repo = chat_repo

    def execute(self, notify_enabled: bool | None, daily_summary_enabled: bool | None) -> TelegramChat:
        if self._chat_repo.get() is None:
            raise NotFoundError("No chat is bound yet")
        return self._chat_repo.set_flags(notify_enabled, daily_summary_enabled)


class GetCurrentMonthUseCase:
    """The month whose budget period is running: the latest one that has already started."""

    def __init__(self, month_repo: MonthRepository) -> None:
        self._month_repo = month_repo

    def execute(self, today: date) -> Month | None:
        started = [m for m in self._month_repo.list_all() if m.start_date <= today]
        return max(started, key=lambda m: m.start_date, default=None)


class WebExpenseNotificationUseCase:
    """Builds the chat message about an expense entered in the web app. Expenses entered in
    the chat itself are not echoed: the bot has already answered there."""

    def __init__(
        self,
        chat_repo: TelegramChatRepository,
        category_repo: CategoryRepository,
        expense_repo: ExpenseRepository,
        user_repo: UserRepository,
    ) -> None:
        self._chat_repo = chat_repo
        self._category_repo = category_repo
        self._expense_repo = expense_repo
        self._user_repo = user_repo

    def execute(self, expense: Expense) -> tuple[int, str] | None:
        chat = self._chat_repo.get()
        if chat is None or not chat.notify_enabled:
            return None
        category = self._category_repo.get_by_id(expense.category_id)
        if category is None:
            return None
        spender = self._user_repo.get_by_id(expense.spent_by_user_id)
        spent_after = self._expense_repo.sum_by_category_for_month(category.month_id).get(category.id, Decimal(0))
        text = expense_card(
            "📱",
            "Трата из приложения",
            expense.amount,
            category.name,
            spender.display_name if spender else None,
            expense.description,
            category.limit_amount,
            spent_after,
        )
        return chat.chat_id, text
