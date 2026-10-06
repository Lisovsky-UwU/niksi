"""What the bot says and does, without any Telegram library.

Handlers in `bot.py` only translate Telegram updates into calls here and replies back,
so everything below can be tested with a plain database session. The web API and the
bot share the same use cases; this module is the bot's counterpart of `app/api/routes`.

Every message has the same shape so the chat is easy to scan: an icon and a bold title
saying what happened, then the amounts, the person and the comment, then the balance.
"""

import secrets
import time
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal
from html import escape

from sqlalchemy.orm import Session

from app.domain.exceptions import DomainError
from app.domain.loans import final_payment
from app.domain.models import Expense, Loan, Month, User
from app.domain.periods import estimated_end
from app.domain.text import (
    MONTHS_NOMINATIVE,
    MONTHS_PREPOSITIONAL,
    card,
    day_month,
    expense_card,
    money,
    plural,
    quote,
)
from app.infrastructure.repositories.sqlalchemy_category_repository import SqlAlchemyCategoryRepository
from app.infrastructure.repositories.sqlalchemy_expense_repository import SqlAlchemyExpenseRepository
from app.infrastructure.repositories.sqlalchemy_grey_zone_repository import SqlAlchemyGreyZoneRepository
from app.infrastructure.repositories.sqlalchemy_income_repository import SqlAlchemyIncomeRepository
from app.infrastructure.repositories.sqlalchemy_loan_repository import SqlAlchemyLoanRepository
from app.infrastructure.repositories.sqlalchemy_month_repository import SqlAlchemyMonthRepository
from app.infrastructure.repositories.sqlalchemy_reconciliation_repository import SqlAlchemyReconciliationRepository
from app.infrastructure.repositories.sqlalchemy_savings_repository import SqlAlchemySavingsRepository
from app.infrastructure.repositories.sqlalchemy_telegram_chat_repository import SqlAlchemyTelegramChatRepository
from app.infrastructure.repositories.sqlalchemy_user_repository import SqlAlchemyUserRepository
from app.telegram.parsing import parse_amount, parse_expense, parse_income
from app.use_cases.expenses import AddExpenseUseCase, DeleteExpenseUseCase, ListExpensesUseCase, UpdateExpenseUseCase
from app.use_cases.grey_zone import TakeFromGreyZoneUseCase
from app.use_cases.income import AddIncomeEntryUseCase
from app.use_cases.loans import AddLoanPaymentUseCase
from app.use_cases.summary import GetMonthSummaryUseCase
from app.use_cases.telegram import (
    BindChatUseCase,
    GetCurrentMonthUseCase,
    LinkTelegramUseCase,
    SetChatFlagsUseCase,
    UnlinkTelegramUseCase,
)


@dataclass
class Button:
    text: str
    data: str


@dataclass
class Reply:
    text: str
    buttons: list[list[Button]] = field(default_factory=list)


@dataclass
class _Pending:
    """An expense waiting for its category to be picked with a button."""

    user_id: int
    month_id: int
    amount: Decimal
    comment: str | None
    expense_date: date
    created: float


# Kept in the bot process only; a restart simply makes old buttons expire.
_PENDING: dict[str, _Pending] = {}
_PENDING_TTL_SECONDS = 30 * 60

HELP = card(
    "📒",
    "Как пользоваться Niksi",
    "✍️ <b>Трата</b> одной строкой, в любом порядке: сумма, категория, комментарий\n"
    "<code>450 прод пятёрочка</code>\n"
    "<code>кафе 300</code>\n"
    "<code>1500 дом и быт за электричество</code>\n"
    "Категорию можно сократить или написать с опечаткой. Если я её не узнаю, пришлю кнопки.",
    "💰 <b>Доход:</b> <code>+40000 аванс</code>\n"
    "🫥 <b>Серая зона:</b> <code>/grey 3000</code>",
    "👀 <b>Посмотреть</b>\n"
    "/left сколько осталось на месяц\n"
    "/cats остаток по категориям\n"
    "/month итог месяца\n"
    "/last последние траты\n"
    "/undo удалить свою последнюю трату\n"
    "/credits кредиты: остаток и ближайшие платежи",
    "🏦 <b>Кредиты:</b> накануне платежа напомню в общей беседе, "
    "оплату можно отметить кнопкой под напоминанием.",
    "⚙️ <b>Настройка</b>\n"
    "/link КОД привязать Telegram (код в настройках приложения)\n"
    "/bind сделать эту беседу общей\n"
    "/notify on|off уведомления о тратах из приложения\n"
    "/summary on|off вечерняя сводка",
)


def _cleanup_pending() -> None:
    now = time.monotonic()
    for key in [k for k, p in _PENDING.items() if now - p.created > _PENDING_TTL_SECONDS]:
        del _PENDING[key]


def _rows(buttons: list[Button], per_row: int = 2) -> list[list[Button]]:
    return [buttons[i : i + per_row] for i in range(0, len(buttons), per_row)]


class BotService:
    def __init__(self, db: Session, now: datetime) -> None:
        self._now = now
        self._today = now.date()
        self._users = SqlAlchemyUserRepository(db)
        self._months = SqlAlchemyMonthRepository(db)
        self._categories = SqlAlchemyCategoryRepository(db)
        self._expenses = SqlAlchemyExpenseRepository(db)
        self._income = SqlAlchemyIncomeRepository(db)
        self._grey = SqlAlchemyGreyZoneRepository(db)
        self._chats = SqlAlchemyTelegramChatRepository(db)
        self._loans = SqlAlchemyLoanRepository(db)
        self._summary = GetMonthSummaryUseCase(
            self._months,
            self._categories,
            self._expenses,
            self._income,
            self._users,
            self._grey,
            SqlAlchemySavingsRepository(db),
            SqlAlchemyReconciliationRepository(db),
            self._loans,
        )

    # ---- who and where ----

    def user(self, telegram_user_id: int) -> User | None:
        return self._users.get_by_telegram_id(telegram_user_id)

    def chat_allowed(self, chat_id: int, is_private: bool) -> bool:
        """The bot works in the bound shared chat and in private chats. Before a chat is
        bound it answers anywhere, so that /link and /bind can be used."""
        chat = self._chats.get()
        return chat is None or is_private or chat.chat_id == chat_id

    def not_linked(self) -> Reply:
        return Reply(
            card(
                "🔗",
                "Я вас пока не знаю",
                "Откройте в приложении Настройки, блок Telegram, получите код и отправьте мне "
                "<code>/link КОД</code>.",
            )
        )

    def _current_month(self) -> Month | None:
        return GetCurrentMonthUseCase(self._months).execute(self._today)

    def _no_month(self) -> Reply:
        return Reply(card("📅", "Месяц не заведён", "Создайте текущий месяц в приложении, в разделе «Все месяцы»."))

    @staticmethod
    def _problem(text: str) -> Reply:
        return Reply(f"⚠️ {text}")

    # ---- linking ----

    def link(self, telegram_user_id: int, code: str) -> Reply:
        if not code.strip():
            return self._problem("Отправьте код из настроек приложения: <code>/link 123456</code>")
        try:
            user = LinkTelegramUseCase(self._users).execute(code, telegram_user_id, self._now)
        except DomainError:
            return self._problem(
                "Код не подошёл или устарел. Получите новый в настройках приложения, он действует 15 минут."
            )
        return Reply(
            card("🔗", f"Готово, {escape(user.display_name)}!", "Теперь можно записывать траты. Как, покажет /help.")
        )

    def unlink(self, telegram_user_id: int) -> Reply:
        user = self.user(telegram_user_id)
        if user is None:
            return self.not_linked()
        UnlinkTelegramUseCase(self._users).execute(user.id)
        return Reply(card("🔓", "Telegram отвязан", "Привязать снова можно кодом из настроек приложения."))

    def bind(self, telegram_user_id: int, chat_id: int, is_private: bool) -> Reply:
        user = self.user(telegram_user_id)
        if user is None:
            return self.not_linked()
        if is_private:
            return self._problem("Команду /bind нужно отправить в общей беседе, куда добавлен бот.")
        BindChatUseCase(self._chats).execute(chat_id, user.id)
        return Reply(
            card(
                "🏠",
                "Эта беседа теперь общая",
                "Здесь я отвечаю на траты, пишу о тратах из приложения и присылаю вечернюю сводку.",
            )
        )

    def set_flag(self, which: str, arg: str) -> Reply:
        chat = self._chats.get()
        if chat is None:
            return self._problem("Сначала сделайте беседу общей командой /bind.")
        value = {"on": True, "вкл": True, "off": False, "выкл": False}.get(arg.strip().lower())
        current = chat.notify_enabled if which == "notify" else chat.daily_summary_enabled
        feminine = which == "summary"
        label = "Вечерняя сводка" if feminine else "Уведомления о тратах из приложения"

        def state(on: bool) -> str:
            if feminine:
                return "включена" if on else "выключена"
            return "включены" if on else "выключены"

        if value is None:
            return Reply(
                card(
                    "🔔" if current else "🔕",
                    f"{label}: {state(current)}",
                    f"Изменить: <code>/{which} on</code> или <code>/{which} off</code>",
                )
            )
        SetChatFlagsUseCase(self._chats).execute(
            value if which == "notify" else None, value if which == "summary" else None
        )
        return Reply(card("🔔" if value else "🔕", f"{label} {state(value)}"))

    # ---- messages ----

    def message(self, telegram_user_id: int, text: str, forced: bool = False) -> Reply | None:
        """A plain chat message: income, an expense, or nothing (then the bot stays silent)."""
        user = self.user(telegram_user_id)
        if user is None:
            return self.not_linked() if forced else None
        income = parse_income(text)
        if income is not None:
            return self._add_income(user, *income)
        month = self._current_month()
        if month is None:
            return self._no_month() if forced else None
        categories = self._categories.list_by_month(month.id)
        parsed = parse_expense(text, [(c.id, c.name) for c in categories], forced=forced)
        if parsed is None:
            return self._problem("Не нашёл сумму. Пример: <code>/add 450 продукты</code>") if forced else None
        if parsed.category_id is not None:
            return self._record(user, parsed.category_id, parsed.amount, parsed.comment)
        if not categories:
            return self._problem("В этом месяце ещё нет категорий. Заведите их в приложении.")
        _cleanup_pending()
        key = secrets.token_hex(4)
        _PENDING[key] = _Pending(user.id, month.id, parsed.amount, parsed.comment, self._today, time.monotonic())
        by_id = {c.id: c for c in categories}
        choices = [by_id[i] for i in parsed.candidates if i in by_id]
        rows = _rows([Button(c.name, f"new:{key}:{c.id}") for c in choices])
        rows.append([Button("✖️ Это не трата", f"drop:{key}")])
        what = [f"💸 <b>{money(parsed.amount)}</b>", f"👤 {escape(user.display_name)}"]
        if parsed.comment:
            what.append(quote(parsed.comment))
        return Reply(card("❓", "В какую категорию записать?", "\n".join(what)), rows)

    def _add_income(self, user: User, amount: Decimal, comment: str | None) -> Reply:
        month = self._current_month()
        if month is None:
            return self._no_month()
        AddIncomeEntryUseCase(self._income, self._months, self._users).execute(
            month.id, user.id, amount, comment, self._today, user.id
        )
        summary = self._summary.execute(month.id)
        mine = next((u for u in summary.income.per_user if u.user_id == user.id), None)
        what = [f"➕ <b>{money(amount)}</b>", f"👤 {escape(user.display_name)}"]
        if comment:
            what.append(quote(comment))
        status = None
        if mine is not None and mine.forecast > 0:
            status = f"📈 Получено за месяц <b>{money(mine.actual)}</b> из ожидаемых {money(mine.forecast)}"
        return Reply(card("💰", "Доход записан", "\n".join(what), status))

    def _record(self, user: User, category_id: int, amount: Decimal, comment: str | None) -> Reply:
        expense = AddExpenseUseCase(self._expenses, self._categories, self._users).execute(
            category_id, amount, comment, self._today, user.id, user.id
        )
        return self._expense_reply(expense, "Трата записана")

    def _expense_reply(self, expense: Expense, title: str) -> Reply:
        category = self._categories.get_by_id(expense.category_id)
        spender = self._users.get_by_id(expense.spent_by_user_id)
        assert category is not None
        spent = self._expenses.sum_by_category_for_month(category.month_id).get(category.id, Decimal(0))
        text = expense_card(
            "✅",
            title,
            expense.amount,
            category.name,
            spender.display_name if spender else None,
            expense.description,
            category.limit_amount,
            spent,
        )
        buttons = [[Button("↩️ Отменить", f"undo:{expense.id}"), Button("🔀 Другая категория", f"recat:{expense.id}")]]
        return Reply(text, buttons)

    def _removed(self, expense: Expense, title: str) -> Reply:
        category = self._categories.get_by_id(expense.category_id)
        name = escape(category.name) if category else ""
        line = f"💸 <s>{money(expense.amount)}</s>, {name}"
        if expense.description:
            line += f"\n{quote(expense.description)}"
        return Reply(card("🗑", title, line))

    # ---- buttons ----

    def callback(self, telegram_user_id: int, data: str) -> Reply | None:
        """A pressed button. The returned reply replaces the message the button was on."""
        user = self.user(telegram_user_id)
        if user is None:
            return self.not_linked()
        kind, _, rest = data.partition(":")
        try:
            if kind == "new":
                key, _, category_id = rest.partition(":")
                pending = _PENDING.pop(key, None)
                if pending is None:
                    return self._problem("Эта кнопка устарела. Отправьте трату ещё раз.")
                expense = AddExpenseUseCase(self._expenses, self._categories, self._users).execute(
                    int(category_id), pending.amount, pending.comment, pending.expense_date, user.id, pending.user_id
                )
                return self._expense_reply(expense, "Трата записана")
            if kind == "drop":
                _PENDING.pop(rest, None)
                return Reply(card("👌", "Хорошо, не записываю"))
            if kind == "undo":
                expense = self._expenses.get_by_id(int(rest))
                if expense is None:
                    return self._problem("Эта трата уже удалена.")
                DeleteExpenseUseCase(self._expenses).execute(expense.id)
                return self._removed(expense, "Трата отменена")
            if kind == "recat":
                expense = self._expenses.get_by_id(int(rest))
                if expense is None:
                    return self._problem("Эта трата уже удалена.")
                category = self._categories.get_by_id(expense.category_id)
                assert category is not None
                choices = [c for c in self._categories.list_by_month(category.month_id) if c.id != category.id]
                rows = _rows([Button(c.name, f"cat:{expense.id}:{c.id}") for c in choices])
                return Reply(
                    card(
                        "🔀",
                        "В какую категорию перенести?",
                        f"💸 <b>{money(expense.amount)}</b>, сейчас в «{escape(category.name)}»",
                    ),
                    rows,
                )
            if kind == "cat":
                expense_id, _, category_id = rest.partition(":")
                updated = UpdateExpenseUseCase(self._expenses, self._categories, self._users).execute(
                    int(expense_id), None, None, None, int(category_id)
                )
                return self._expense_reply(updated, "Категория изменена")
            if kind == "loanpay":
                loan_id, _, due = rest.partition(":")
                return self._pay_loan(user, int(loan_id), date.fromisoformat(due))
        except DomainError:
            return self._problem("Не получилось: запись уже изменилась. Проверьте её в приложении.")
        return None

    # ---- looking at the month ----

    def _period(self, month: Month) -> tuple[str, str]:
        """("Сентябрь 2026", "с 27 августа примерно по 26 сентября")."""
        end = month.end_date or estimated_end(month.start_date)
        approx = "примерно " if month.end_date is None else ""
        title = f"{MONTHS_NOMINATIVE[month.month - 1]} {month.year}"
        return title, f"с {day_month(month.start_date)} {approx}по {day_month(end)}"

    def _left_lines(self, month: Month) -> list[str]:
        """What is left for the month by category limits, and per day until the period ends."""
        summary = self._summary.execute(month.id)
        limit, spent = summary.totals.total_limit, summary.totals.total_spent
        if limit <= 0:
            return [f"💸 Потрачено <b>{money(spent)}</b>. Лимиты категориям не заданы."]
        left = limit - spent
        lines = (
            [f"💰 Осталось <b>{money(left)}</b> из {money(limit)}"]
            if left >= 0
            else [f"🔴 Перерасход <b>{money(-left)}</b>, лимит был {money(limit)}"]
        )
        end = month.end_date or estimated_end(month.start_date)
        days = (end - self._today).days + 1
        if left > 0 and days > 0:
            per_day = (left / days).quantize(Decimal(1))
            lines.append(
                f"🗓 До конца месяца {days} {plural(days, 'день', 'дня', 'дней')}, "
                f"это примерно <b>{money(per_day)}</b> в день"
            )
        return lines

    def left(self, telegram_user_id: int) -> Reply:
        if self.user(telegram_user_id) is None:
            return self.not_linked()
        month = self._current_month()
        if month is None:
            return self._no_month()
        title, period = self._period(month)
        return Reply(card("📅", title, f"<i>{period}</i>", "\n".join(self._left_lines(month))))

    def cats(self, telegram_user_id: int) -> Reply:
        if self.user(telegram_user_id) is None:
            return self.not_linked()
        month = self._current_month()
        if month is None:
            return self._no_month()
        summary = self._summary.execute(month.id)
        if not summary.categories:
            return self._problem("В этом месяце ещё нет категорий.")
        lines = []
        for c in summary.categories:
            if c.remaining < 0:
                mark, tail = "🔴", f"перерасход <b>{money(-c.remaining)}</b>"
            elif c.percent_used >= 80:
                mark, tail = "🟡", f"осталось <b>{money(c.remaining)}</b>"
            else:
                mark, tail = "🟢", f"осталось <b>{money(c.remaining)}</b>"
            lines.append(f"{mark} <b>{escape(c.name)}</b>\n{money(c.spent)} из {money(c.limit_amount)}, {tail}")
        title, _ = self._period(month)
        return Reply(card("📊", f"Категории, {title.lower()}", "\n\n".join(lines)))

    def month(self, telegram_user_id: int) -> Reply:
        if self.user(telegram_user_id) is None:
            return self.not_linked()
        month = self._current_month()
        if month is None:
            return self._no_month()
        s = self._summary.execute(month.id)
        b = s.balance
        rows = [
            ("  С прошлого месяца", s.carryover.carried_over),
            ("+ Доходы", b.income_actual),
            ("− Траты", b.total_spent),
            ("− Серая зона", b.grey_zone_taken),
            ("− В накопления" if b.savings_net >= 0 else "+ Из накоплений", abs(b.savings_net)),
        ]
        if b.loan_payments:
            rows.append(("− Кредиты", b.loan_payments))
        if b.adjustments:
            rows.append(("± Сверка", b.adjustments))
        width = max(len(label) for label, _ in rows) + 2
        table = [f"{label.ljust(width)}{money(value).rjust(14)}" for label, value in rows]
        table.append("═" * (width + 14))
        table.append(f"{'= Остаток'.ljust(width)}{money(s.carryover.closing).rjust(14)}")
        title, period = self._period(month)
        return Reply(
            card("🧾", f"Итог месяца, {title.lower()}", f"<i>{period}</i>", f"<pre>{escape(chr(10).join(table))}</pre>")
        )

    def last(self, telegram_user_id: int, count: int = 10) -> Reply:
        if self.user(telegram_user_id) is None:
            return self.not_linked()
        month = self._current_month()
        if month is None:
            return self._no_month()
        expenses = ListExpensesUseCase(self._expenses).execute(month_id=month.id)[:count]
        if not expenses:
            return Reply(card("🕘", "Последние траты", "В этом месяце трат ещё нет."))
        names = {c.id: c.name for c in self._categories.list_by_month(month.id)}
        people = {u.id: u.display_name for u in self._users.list_all()}
        # Grouped by day, newest first, like the list in the app.
        days: list[str] = []
        current: date | None = None
        block: list[str] = []
        for e in expenses:
            if e.expense_date != current:
                if block:
                    days.append("\n".join(block))
                current = e.expense_date
                block = [f"<b>{day_month(e.expense_date)}</b>"]
            line = (
                f"💸 <b>{money(e.amount)}</b>, {escape(names.get(e.category_id, ''))}"
                f", 👤 {escape(people.get(e.spent_by_user_id, ''))}"
            )
            if e.description:
                line += f"\n      <i>{escape(e.description)}</i>"
            block.append(line)
        if block:
            days.append("\n".join(block))
        return Reply(card("🕘", "Последние траты", *days))

    def undo(self, telegram_user_id: int) -> Reply:
        user = self.user(telegram_user_id)
        if user is None:
            return self.not_linked()
        month = self._current_month()
        if month is None:
            return self._no_month()
        mine = [e for e in ListExpensesUseCase(self._expenses).execute(month_id=month.id) if e.created_by_user_id == user.id]
        if not mine:
            return self._problem("Удалять нечего: в этом месяце вы ещё ничего не записывали.")
        latest = max(mine, key=lambda e: e.id)
        DeleteExpenseUseCase(self._expenses).execute(latest.id)
        return self._removed(latest, "Последняя трата удалена")

    def grey(self, telegram_user_id: int, arg: str) -> Reply:
        user = self.user(telegram_user_id)
        if user is None:
            return self.not_linked()
        amount = parse_amount(arg)
        if amount is None:
            return self._problem("Сколько взяли? Например: <code>/grey 3000</code>")
        month = self._current_month()
        if month is None:
            return self._no_month()
        TakeFromGreyZoneUseCase(self._grey, self._months).execute(month.id, user.id, amount, self._today)
        summary = self._summary.execute(month.id)
        mine = next((u for u in summary.grey_zone.per_user if u.user_id == user.id), None)
        status = None
        if mine is not None and mine.limit > 0:
            status = f"📊 В лимите осталось <b>{money(mine.remaining)}</b> из {money(mine.limit)}"
        what = f"➖ <b>{money(amount)}</b> взято себе\n👤 {escape(user.display_name)}"
        return Reply(card("🫥", "Серая зона", what, status))

    # ---- loans ----

    def _due_line(self, loan: Loan) -> str:
        due = loan.next_payment_date
        if due is None:
            return "✅ Выплачен"
        amount = money(final_payment(loan.balance, loan.rate_percent, loan.monthly_payment))
        if due < self._today:
            return f"🔴 Платеж {amount} просрочен, был {day_month(due)}"
        if due == self._today:
            return f"📌 Платеж {amount} сегодня"
        if due == self._today + timedelta(days=1):
            return f"📌 Платеж {amount} завтра"
        return f"🗓 Платеж {amount}, {day_month(due)}"

    def _loan_lines(self, loan: Loan) -> list[str]:
        lines = [f"<b>{escape(loan.name)}</b>", f"💳 Остаток долга <b>{money(loan.balance)}</b>", self._due_line(loan)]
        if loan.payoff_date and loan.payments_left:
            left = loan.payments_left
            lines.append(
                f"🏁 Закроется примерно в {MONTHS_PREPOSITIONAL[loan.payoff_date.month - 1]} "
                f"{loan.payoff_date.year}, еще {left} {plural(left, 'платеж', 'платежа', 'платежей')}"
            )
        return lines

    def credits(self, telegram_user_id: int) -> Reply:
        if self.user(telegram_user_id) is None:
            return self.not_linked()
        loans = [loan for loan in self._loans.list_loans() if not loan.is_closed]
        if not loans:
            return Reply(card("🏦", "Кредиты", 'Кредитов нет. Завести их можно в приложении, раздел "Деньги".'))
        blocks = ["\n".join(self._loan_lines(loan)) for loan in loans]
        total = sum((loan.balance for loan in loans), Decimal(0))
        monthly = sum((loan.monthly_payment for loan in loans if loan.balance > 0), Decimal(0))
        blocks.append(f"Всего долг <b>{money(total)}</b>, платежи <b>{money(monthly)}</b> в месяц")
        return Reply(card("🏦", "Кредиты", *blocks))

    def loan_reminders(self) -> tuple[int, list[Reply]] | None:
        """For the shared chat: a payment due tomorrow, today or overdue, once per payment date."""
        chat = self._chats.get()
        if chat is None:
            return None
        tomorrow = self._today + timedelta(days=1)
        replies = []
        for loan in self._loans.list_loans():
            due = loan.next_payment_date
            if due is None or due > tomorrow or loan.last_reminded_due == due:
                continue
            self._loans.set_last_reminded_due(loan.id, due)
            amount = final_payment(loan.balance, loan.rate_percent, loan.monthly_payment)
            title = {tomorrow: "Завтра платеж по кредиту", self._today: "Сегодня платеж по кредиту"}.get(
                due, "Платеж по кредиту просрочен"
            )
            what = f"<b>{escape(loan.name)}</b>\n💸 <b>{money(amount)}</b>, {day_month(due)}"
            replies.append(
                Reply(
                    card("🏦", title, what, f"💳 Остаток долга {money(loan.balance)}"),
                    [[Button(f"✅ Оплачено {money(amount)}", f"loanpay:{loan.id}:{due.isoformat()}")]],
                )
            )
        return (chat.chat_id, replies) if replies else None

    def _pay_loan(self, user: User, loan_id: int, due: date) -> Reply:
        """The "Оплачено" button: records the regular payment the reminder was about, once."""
        loan = self._loans.get_loan(loan_id)
        if loan is None:
            return self._problem("Этого кредита уже нет.")
        if loan.next_payment_date != due:
            return Reply(card("👌", "Этот платеж уже записан", "\n".join(self._loan_lines(loan))))
        amount = final_payment(loan.balance, loan.rate_percent, loan.monthly_payment)
        payment = AddLoanPaymentUseCase(self._loans).execute(loan.id, "regular", amount, None, self._today, None, user.id)
        loan = self._loans.get_loan(loan_id)
        assert loan is not None
        what = (
            f"💸 <b>{money(payment.amount)}</b>: {money(payment.principal_part)} в счет долга, "
            f"{money(payment.interest_part)} проценты\n👤 {escape(user.display_name)}"
        )
        return Reply(card("✅", "Платеж записан", what, "\n".join(self._loan_lines(loan))))

    # ---- evening summary ----

    def daily_summary(self) -> tuple[int, str] | None:
        """The evening message for the shared chat, once a day, if it is switched on."""
        chat = self._chats.get()
        if chat is None or not chat.daily_summary_enabled or chat.last_summary_date == self._today:
            return None
        month = self._current_month()
        if month is None:
            return None
        today = [e for e in ListExpensesUseCase(self._expenses).execute(month_id=month.id) if e.expense_date == self._today]
        people = {u.id: u.display_name for u in self._users.list_all()}
        if today:
            total = sum((e.amount for e in today), Decimal(0))
            by_person: dict[int, Decimal] = {}
            for e in today:
                by_person[e.spent_by_user_id] = by_person.get(e.spent_by_user_id, Decimal(0)) + e.amount
            spent = [f"💸 Потрачено за день <b>{money(total)}</b>"]
            spent += [f"👤 {escape(people.get(uid, ''))}: {money(v)}" for uid, v in by_person.items()]
            day_block = "\n".join(spent)
        else:
            day_block = "💸 Сегодня трат не было"
        self._chats.mark_summary_sent(self._today)
        text = card("🌙", f"Итоги дня, {day_month(self._today)}", day_block, "\n".join(self._left_lines(month)))
        return chat.chat_id, text
